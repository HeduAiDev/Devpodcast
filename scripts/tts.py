"""TTS 抽象层：DialogueTTSProvider（MOSS-TTSD，原生对话）与 SegmentedTTSProvider
（CosyVoice3，逐句+拼接）两类，统一 Protocol。本地基类管理 GPU/batch/预热/显存。

CLI（MOSS-TTSD 已装时）：
    python3 scripts/tts.py synthesize <script.md> --voice-map S1=wav S2=wav --output <dir> [--target-minutes 35]
"""
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

# 需在 M0 环境任务（Task 17）安装 torch；本文件顶层不 import torch，避免无 GPU 环境崩溃。
# MOSS-TTSD 的 Windows 兼容 patch（torchaudio → soundfile 回退）在 synthesize 内导入。


@dataclass
class TTSOpts:
    sample_rate: int = 24000
    max_new_tokens: int | None = None
    temperature: float = 0.6
    top_k: int = 50
    top_p: float = 0.9
    output_dir: str = "audio"


@dataclass
class VoiceSpec:
    name: str
    ref_audio: Path | None = None


@dataclass
class AudioBundle:
    wav_path: Path
    segments: list[Path] = field(default_factory=list)
    duration_s: float = 0.0
    vram_gb: float = 0.0


@runtime_checkable
class TTSProvider(Protocol):
    native_dialogue: bool

    def synthesize(self, script, voice_map: dict, opts: TTSOpts) -> AudioBundle: ...
    def list_voices(self) -> list[VoiceSpec]: ...


class LocalTTSProvider:
    """本地基类：GPU 设备管理、模型预热、显存报告。子类实现 synthesize。"""

    def __init__(self, model_dir: str | Path, device: str = "cuda:0", dtype: str = "bfloat16"):
        self.model_dir = Path(model_dir)
        self.device = device
        self.dtype = dtype

    def warmup(self) -> None:
        """预热到稳态：子类实现（模型加载）。"""
        raise NotImplementedError

    def list_voices(self) -> list[VoiceSpec]:
        """列出可用音色：子类实现。"""
        raise NotImplementedError

    def vram_report(self) -> dict:
        try:
            import torch
        except ImportError:
            return {"error": "torch not installed"}
        if not torch.cuda.is_available():
            return {"error": "cuda not available"}
        props = torch.cuda.get_device_properties(0)
        return {"device": torch.cuda.get_device_name(0),
                "total_gb": round(props.total_memory / 1024 ** 3, 1),
                "used_gb": round((props.total_memory - torch.cuda.mem_get_info(0)[0]) / 1024 ** 3, 1)}


def _enable_sdpa_backends() -> None:
    """禁用 Blackwell 上损坏的 cuDNN SDPA，保留 flash/mem-efficient/math（官方 README 配方）。"""
    import torch
    torch.backends.cuda.enable_cudnn_sdp(False)
    torch.backends.cuda.enable_flash_sdp(True)
    torch.backends.cuda.enable_mem_efficient_sdp(True)
    torch.backends.cuda.enable_math_sdp(True)


class DialogueTTSProvider(LocalTTSProvider):
    """MOSS-TTSD：整段对话一次合成。Script → [S1]/[S2] 标签串 → 单次生成。

    已接入验证配方（2026-08-03 实测）：
    - SDPA attention（flash-attn 未装时可用；8B bf16 全卡 VRAM ~26GB）
    - device_map='auto' + low_cpu_mem_usage=True 流式加载（32GB RAM 直接 .to(cuda) 会 OOM）
    - 参考音频经 encode_audios_from_wav 编码为 codec tokens 后作 reference
    - 停顿由模型生成；production-notes 的停顿建议是软提示（改写文本节奏）
    """
    native_dialogue = True

    def __init__(self, model_dir: str | Path, device: str = "cuda:0", dtype: str = "bfloat16"):
        super().__init__(model_dir, device, dtype)
        self._processor = None
        self._model = None

    def _load(self):
        if self._processor is not None and self._model is not None:
            return
        _enable_sdpa_backends()
        import torch
        from transformers import AutoModel, AutoProcessor

        # Windows 无 FFmpeg 时 torchaudio.load 走 soundfile 回退（scripts/ta_compat）
        try:
            import scripts.ta_compat  # noqa: F401
        except ImportError:
            pass

        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.bfloat16 if device == "cuda" else torch.float32

        self._processor = AutoProcessor.from_pretrained(self.model_dir, trust_remote_code=True)
        self._processor.audio_tokenizer = self._processor.audio_tokenizer.to(device).eval()
        self._model = AutoModel.from_pretrained(
            self.model_dir,
            trust_remote_code=True,
            attn_implementation="sdpa",
            torch_dtype=dtype,
            device_map="auto",
            low_cpu_mem_usage=True,
        ).eval()

    def warmup(self) -> None:
        self._load()

    def _calibrated_decode(self, dedelayed, start_length, n_vq, pad_code, target_sr):
        """网格搜索最佳 (通道移位, 时间偏移) 解码组合，pitch 自相关评分。

        背景：MOSS-TTSD 的 de-delay 通道布局与 start_length 裁剪边界在本环境
        （Windows/torch 2.11/SDPA）与模型训练时存在偏差，固定常量会导致解码出
        噪声。pitch 自相关是「是否像语音」的强指标（浊音 >0.4，噪声 <0.25），
        网格搜索自动对齐。约 16×5=80 次短解码，<1 分钟，对长音频合成可接受。
        """
        import numpy as np
        import torch as _t

        def _pitch(wav):
            frame = wav[:min(len(wav), target_sr * 10)]
            if len(frame) < target_sr // 2:
                return 0.0
            lag_lo, lag_hi = target_sr // 400, target_sr // 80
            ac = np.correlate(
                frame[:target_sr] - frame[:target_sr].mean(),
                frame[:target_sr] - frame[:target_sr].mean(),
                "full",
            )[len(frame[:target_sr]) - 1:]
            return float((ac / (ac[0] + 1e-9))[lag_lo:lag_hi].max())

        best = (0.0, None)
        for shift in range(n_vq):
            for t_off in range(-2, 3):
                trim_from = max(0, start_length - n_vq + 1 + t_off)
                trimmed = dedelayed[trim_from:]
                valid = trimmed[~(trimmed == pad_code).all(dim=1)]
                if valid.shape[0] < 5:
                    continue
                shifted = _t.roll(valid, shift, dims=1)
                try:
                    wavs = self._processor.decode_audio_codes(shifted)
                    if not wavs:
                        continue
                    wav = _t.cat(wavs, dim=-1).numpy()
                    p = _pitch(wav)
                    if p > best[0]:
                        best = (p, wav)
                except Exception:
                    continue
        if best[1] is None:
            raise RuntimeError("自校准解码失败：无任何可解码组合")
        return [best[1]]

    def synthesize(self, script, voice_map: dict, opts: TTSOpts) -> AudioBundle:
        self._load()
        import torch

        processor = self._processor
        model = self._model
        target_sr = int(processor.model_config.sampling_rate)
        n_vq = getattr(processor.model_config, "n_vq", 16)

        # 1. 组装对话文本：turns → "[S1] ... [S2] ..." 标签串
        parts = []
        for turn in script.turns:
            text = (turn.text or "").strip()
            if text:
                parts.append(f"[{turn.speaker}] {text}")
        if not parts:
            raise ValueError("script 无任何发言内容，无法合成")
        full_text = " ".join(parts)

        # 分段生成（规避模型提前终止）：模型对长文本会过早输出 audio_end
        # （实测 300 字仅生成 ~53 步 vs 短文本可到 318 步）。按目标秒数分块，
        # 每段独立生成后拼接；每段 ≤60s 音频（750 步），提前终止风险低。
        # 音色一致性：每段用同一参考音频克隆，漂移可控。
        # 模型实测单段可完整朗读 ~889 字（英文 48.8s）。用 800 字 chunk：
        # 减少分段数、降低失败概率；每段 ~60s 语音，整期 ~13 段。
        chunk_seconds = 200.0
        chunk_chars = int(chunk_seconds * 4.0)  # 4 字/秒口播 = 800 字
        # 按 turn 边界切分（避免把单个 turn 劈开）
        chunks: list[str] = []
        cur: list[str] = []
        cur_chars = 0
        for part in parts:
            n = len(part)
            if cur and cur_chars + n > chunk_chars:
                chunks.append(" ".join(cur))
                cur, cur_chars = [], 0
            cur.append(part)
            cur_chars += n
        if cur:
            chunks.append(" ".join(cur))
        if len(chunks) > 1:
            print(f"  [tts] 分段生成：{len(chunks)} 段（每段 ≤{chunk_chars} 字）")

        # 2. 参考音频：voice_map {speaker: wav_path}，编码为 codec tokens
        #    官方 v0.7 中文示例证明：必须带参考文本前缀（prompt_text），否则
        #    模型缺少"谁在说话"锚定 → 生成质量差、提前终止。
        import torchaudio
        wavs, ref_names = [], []
        for spk in ("S1", "S2"):
            p = voice_map.get(spk)
            if not p:
                raise ValueError(f"voice_map 缺 {spk} 音色样本: {voice_map}")
            w, sr = torchaudio.load(str(p))
            if w.shape[0] > 1:
                w = w.mean(dim=0, keepdim=True)
            if sr != target_sr:
                w = torchaudio.functional.resample(w, sr, target_sr)
            wavs.append(w)
            ref_names.append(str(p))
        ref_codes = processor.encode_audios_from_wav(wavs, sampling_rate=target_sr)
        concat_wav = torch.cat(wavs, dim=-1)
        prompt_audio = processor.encode_audios_from_wav([concat_wav], sampling_rate=target_sr)[0]

        # 参考文本前缀（voice_map 里可选传 REF_TEXT_<spk> 键；缺省用占位）
        ref_texts = []
        for spk in ("S1", "S2"):
            rt = voice_map.get(f"REF_TEXT_{spk}", "")
            ref_texts.append(f"[{spk}] {rt}".strip() if rt else "")

        # 3-5. 分段生成 + 解码
        device = self._model.device
        pad_code = processor.model_config.audio_pad_code
        segments_dir = Path(opts.output_dir) / "segments"
        segments_dir.mkdir(parents=True, exist_ok=True)
        segments: list[Path] = []
        total_frames = 0
        import soundfile as sf

        # 参考文本前缀：官方 _build_prefixed_text 把 [S1]ref1[S2]ref2 拼在对话前
        ref_prefix = "".join(rt for rt in ref_texts if rt)

        # 批处理：一次生成 BATCH_SIZE 个 chunk，GPU 并行 → 3-4x 提速
        # （官方 generate 原生支持 batch；处理器按最长序列 padding）
        BATCH_SIZE = 4
        for g in range(0, len(chunks), BATCH_SIZE):
            group = chunks[g:g + BATCH_SIZE]
            conversations = [[
                processor.build_user_message(text=(ref_prefix + ct) if ref_prefix else ct, reference=ref_codes),
                processor.build_assistant_message(audio_codes_list=[prompt_audio]),
            ] for ct in group]
            batch = processor(conversations, mode="continuation")

            # max_new_tokens 取组内最大（短 chunk 靠 <|im_end|> 提前停）
            max_new_tokens = max(
                max(512, int(len(ct) / 4.0 * 12.5 * 1.3)) for ct in group
            )
            min_ok_steps = [
                max(60, int(len(ct) / 4.0 * 12.5 * 0.35)) for ct in group
            ]

            # 每样本独立重试评分：非静音占比 × 步数达标率
            import numpy as np

            best_wavs: list[list] = [[] for _ in group]
            best_scores = [-1.0] * len(group)
            for attempt in range(3):
                torch.manual_seed(42 + g * 101 + attempt * 17)
                with torch.no_grad():
                    outputs = model.generate(
                        input_ids=batch["input_ids"].to(device),
                        attention_mask=batch["attention_mask"].to(device),
                        max_new_tokens=max_new_tokens,
                        text_temperature=0.7, text_top_p=0.9, text_top_k=50,
                        audio_temperature=0.7, audio_top_p=0.9, audio_top_k=50,
                        audio_repetition_penalty=1.1,
                    )
                # outputs: list of (start_length, generation_ids)，每样本一个
                for i, (start_len, gen_ids) in enumerate(outputs):
                    new_steps = int(gen_ids.shape[0]) - int(start_len.item())
                    msgs = processor.decode([(start_len, gen_ids)])
                    att_wavs = []
                    for msg in msgs:
                        if msg is None:
                            continue
                        for wav in msg.audio_codes_list:
                            if not isinstance(wav, torch.Tensor) or wav.numel() == 0:
                                continue
                            att_wavs.append(wav.detach().float().cpu())
                    if not att_wavs:
                        continue
                    concat = torch.cat(att_wavs, dim=-1).numpy().reshape(-1)
                    if concat.size == 0:
                        continue
                    nonsil = float((np.abs(concat) >= 0.01).mean())
                    mok = min_ok_steps[i]
                    score = nonsil * min(new_steps / mok, 1.0) if mok > 0 else nonsil
                    if score > best_scores[i]:
                        best_scores[i] = score
                        best_wavs[i] = att_wavs
                # 全部达标才提前停
                if all(
                    best_scores[i] > 0.5 * min(1.0, 1.0)
                    for i in range(len(group))
                ):
                    break

            # 保存本组所有样本的分段
            for i, wavs_out in enumerate(best_wavs):
                ci = g + i
                for wav in wavs_out:
                    wav_np = wav.numpy()
                    if wav_np.ndim == 1:
                        wav_np = wav_np.reshape(-1, 1)
                    seg_path = segments_dir / f"chunk{ci:02d}_{len(segments):03d}.wav"
                    sf.write(str(seg_path), wav_np.astype("float32"), target_sr)
                    segments.append(seg_path)
                    total_frames += wav_np.shape[0]

        # 6. 拼接总音频
        bundle_path = Path(opts.output_dir) / "episode.wav"
        if len(segments) == 1:
            bundle_path.write_bytes(segments[0].read_bytes())
        else:
            import numpy as np
            frames = [sf.read(str(s), dtype="float32")[0] for s in segments]
            combined = np.concatenate(frames, axis=0)
            sf.write(str(bundle_path), combined.astype("float32"), target_sr)

        duration_s = total_frames / target_sr
        vram_gb = 0.0
        try:
            free0 = torch.cuda.mem_get_info(0)[0] / 1024 ** 3
            _ = free0  # 无法拿加载前基线；报告当前占用
            used = (torch.cuda.get_device_properties(0).total_memory - torch.cuda.mem_get_info(0)[0]) / 1024 ** 3
            vram_gb = round(used, 1)
        except Exception:
            pass

        return AudioBundle(wav_path=bundle_path, segments=segments, duration_s=round(duration_s, 2), vram_gb=vram_gb)


def _synthesize_turns(
    model_dir: str | Path,
    turns: list[tuple[int, str, str]],
    speaker_voice: dict[str, str],
) -> dict:
    """进程内合成指定 turns（multiprocessing worker）。返回 {turn_idx: (wav, sr)}。"""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    _enable_sdpa_backends()
    import numpy as np
    import torch
    from qwen_tts import Qwen3TTSModel

    model = Qwen3TTSModel.from_pretrained(
        str(model_dir),
        device_map="cuda:0",
        dtype=torch.bfloat16,
        attn_implementation="sdpa",
    )
    # 按说话人分组批量合成
    from collections import defaultdict
    by_speaker: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for idx, spk, text in turns:
        by_speaker[spk].append((idx, text))

    result: dict[int, tuple[np.ndarray, int]] = {}
    for spk, items in by_speaker.items():
        voice = speaker_voice.get(spk, "dylan")
        texts = [t for _, t in items]
        wavs, sr = model.generate_custom_voice(
            texts, speaker=voice, language="chinese", do_sample=True,
        )
        for (idx, _), wav in zip(items, wavs):
            result[idx] = (np.asarray(wav, dtype=np.float32), sr)
    return result


class SegmentedTTSProvider(LocalTTSProvider):
    """Qwen3-TTS（逐句合成 + 规则插静音拼接）。

    2026-08-05 调研选定：MOSS-TTSD 中文长文本生成不稳定（>200字退化），
    业界第一梯队调研结论主选 Qwen3-TTS-12Hz-1.7B-CustomVoice：
    - Apache-2.0 全开放，9 个内置音色免克隆（dylan 做老张 / aiden 做阿凯）
    - 逐句合成 + 拼接天然支持任意长度
    - RTF≈2.0（35 分钟一期约 70 分钟合成，可接受）

    voice_map 传音色名（如 S1=dylan,S2=aiden），不是 wav 路径。
    """
    native_dialogue = False
    PAUSE_SPEAKER_SWITCH_MS = (350, 500)
    PAUSE_SAME_SPEAKER_MS = (150, 250)

    def __init__(self, model_dir: str | Path, device: str = "cuda:0", dtype: str = "bfloat16"):
        super().__init__(model_dir, device, dtype)
        self._model = None

    def _load(self):
        if self._model is not None:
            return
        _enable_sdpa_backends()
        import torch
        from qwen_tts import Qwen3TTSModel

        self._model = Qwen3TTSModel.from_pretrained(
            self.model_dir,
            device_map=self.device,
            dtype=torch.bfloat16,
            attn_implementation="sdpa",
        )

    def warmup(self) -> None:
        """加载模型（Qwen3-TTS 无需预热，加载即就绪）。"""
        self._load()

    def synthesize(self, script, voice_map: dict, opts: TTSOpts) -> AudioBundle:
        """逐句合成 + 拼接。script.turns → 每 turn 一个音频，中间插停顿。

        GPU 利用率实测仅 20-39%（1.7B 模型太小，PRO 6000 算力闲置）。
        用多进程并行：N 个进程各加载一个 Qwen3-TTS 实例，分配 1/N 的 turns，
        并行合成 → 利用率拉满、3-4x 提速（95.6GB 显存装 4 个 ~10GB 实例绰绰有余）。
        """
        import numpy as np
        import soundfile as sf
        import torch
        from collections import defaultdict

        # voice_map 传音色名（dylan/ryan），不是路径
        s1_voice = str(voice_map.get("S1", "dylan"))
        s2_voice = str(voice_map.get("S2", "ryan"))
        speaker_voice = {"S1": s1_voice, "S2": s2_voice}

        segments_dir = Path(opts.output_dir) / "segments"
        segments_dir.mkdir(parents=True, exist_ok=True)
        segments: list[Path] = []
        total_frames = 0

        # 收集有效 turns（保留原顺序）
        valid_turns = [(i, t.speaker, (t.text or "").strip())
                       for i, t in enumerate(script.turns) if (t.text or "").strip()]

        # 并行合成：N 进程（默认 2，防 CPU/内存过载——4 进程同时加载模型实测卡死）
        # 教训：每个进程 from_pretrained 读 7GB 权重 + CPU 初始化，同时起 4 个会打满
        # CPU/内存。降到 2 进程，且 spawn 天然错开加载（进程逐个初始化）。
        import multiprocessing as mp
        n_proc = 1  # 单进程（内存受限，多进程卡死）
        if n_proc <= 1 or len(valid_turns) < 4:
            # 少量 turn 直接单进程
            turn_wavs = _synthesize_turns(self.model_dir, valid_turns, speaker_voice)
        else:
            # 按 turn 索引轮转分配（保证相邻 turn 在不同进程，负载均衡）
            chunks: list[list[tuple[int, str, str]]] = [[] for _ in range(n_proc)]
            for k, item in enumerate(valid_turns):
                chunks[k % n_proc].append(item)
            ctx = mp.get_context("spawn")
            results: dict[int, tuple[np.ndarray, int]] = {}
            with ctx.Pool(n_proc) as pool:
                partials = pool.starmap(
                    _synthesize_turns,
                    [(self.model_dir, ch, speaker_voice) for ch in chunks],
                )
                for partial in partials:
                    results.update(partial)
            turn_wavs = results

        # 按顺序拼接，说话人切换插 350-500ms，同人句间 150-250ms
        import random
        rng = random.Random(42)
        all_frames: list[np.ndarray] = []
        prev_spk = None
        sr = None
        for i, spk, text in valid_turns:
            if i not in turn_wavs:
                continue
            wav, sr = turn_wavs[i]
            # 停顿：切换 350-500ms，同人 150-250ms
            if prev_spk is not None:
                if spk != prev_spk:
                    pause_ms = rng.randint(*self.PAUSE_SPEAKER_SWITCH_MS)
                else:
                    pause_ms = rng.randint(*self.PAUSE_SAME_SPEAKER_MS)
                all_frames.append(np.zeros(int(sr * pause_ms / 1000), dtype=np.float32))
            all_frames.append(np.asarray(wav, dtype=np.float32))
            prev_spk = spk

            # 保存分段
            seg_path = segments_dir / f"turn{i:03d}.wav"
            sf.write(str(seg_path), wav.astype("float32"), sr)
            segments.append(seg_path)
            total_frames += len(wav)

        # 按顺序拼接，说话人切换插 350-500ms，同人句间 150-250ms
        import random
        rng = random.Random(42)
        all_frames: list[np.ndarray] = []
        prev_spk = None
        for i, turn in enumerate(script.turns):
            if i not in turn_wavs:
                continue
            wav, sr = turn_wavs[i]
            # 停顿：切换 350-500ms，同人 150-250ms
            if prev_spk is not None:
                if turn.speaker != prev_spk:
                    pause_ms = rng.randint(*self.PAUSE_SPEAKER_SWITCH_MS)
                else:
                    pause_ms = rng.randint(*self.PAUSE_SAME_SPEAKER_MS)
                all_frames.append(np.zeros(int(sr * pause_ms / 1000), dtype=np.float32))
            all_frames.append(np.asarray(wav, dtype=np.float32))
            prev_spk = turn.speaker

            # 保存分段
            seg_path = segments_dir / f"turn{i:03d}.wav"
            sf.write(str(seg_path), wav.astype("float32"), sr)
            segments.append(seg_path)
            total_frames += len(wav)

        # 拼接总音频
        combined = np.concatenate(all_frames, axis=0) if all_frames else np.zeros(1, dtype=np.float32)
        bundle_path = Path(opts.output_dir) / "episode.wav"
        sf.write(str(bundle_path), combined.astype("float32"), sr)

        duration_s = len(combined) / sr
        vram_gb = 0.0
        try:
            free0 = torch.cuda.mem_get_info(0)[0] / 1024 ** 3
            _ = free0
            used = (torch.cuda.get_device_properties(0).total_memory - torch.cuda.mem_get_info(0)[0]) / 1024 ** 3
            vram_gb = round(used, 1)
        except Exception:
            pass

        return AudioBundle(wav_path=bundle_path, segments=segments, duration_s=round(duration_s, 2), vram_gb=vram_gb)


class VLLMTTSProvider(LocalTTSProvider):
    """vLLM-Omni 后端（HTTP 调用，2026-08-05 部署成功）。

    vLLM-Omni 连续批处理：RTF 2.0 → 0.14（14x），单进程吃满 GPU，
    无多进程 CPU/内存过载问题。35 分钟一期 ~5 分钟合成。
    Server: docker run vllm/vllm-omni:latest（见 _diag/run_vllm_tts.sh）
    """
    native_dialogue = False
    PAUSE_SPEAKER_SWITCH_MS = (350, 500)
    PAUSE_SAME_SPEAKER_MS = (150, 250)

    def __init__(self, model_dir: str | Path = "vllm", device: str = "", dtype: str = "",
                 base_url: str = "http://localhost:8000", speed: float = 1.15):
        super().__init__(model_dir, device, dtype)
        self.base_url = base_url.rstrip("/")
        self.speed = speed

    def _synthesize_one(self, text: str, voice: str):
        """调用 vLLM-Omni /v1/audio/speech 合成一句。返回 (wav, sr)。"""
        import json
        import numpy as np
        import requests

        payload = {
            "model": "/models/qwen3-tts",
            "input": text,
            "voice": voice,
            "language": "chinese",
            "response_format": "wav",
            "task_type": "CustomVoice",
            "non_streaming_mode": True,
            # 语速：默认 1.15（35 分钟目标用；实测 vLLM-Omni 输出偏慢需微调）
            "speed": self.speed,
            # 采样稳定性（2026-08-05 实测）：temperature 只能经 extra_params 传，
            # 顶层 temperature 被 server 忽略。0.1 显著降低语调随机（浮夸/哭腔）。
            "extra_params": {"temperature": 0.1, "top_p": 0.9, "top_k": 50},
        }
        resp = requests.post(f"{self.base_url}/v1/audio/speech", json=payload, timeout=300)
        resp.raise_for_status()
        import io
        import soundfile as sf
        wav, sr = sf.read(io.BytesIO(resp.content), dtype="float32")
        return np.asarray(wav, dtype=np.float32), sr

    def synthesize(self, script, voice_map: dict, opts: TTSOpts) -> AudioBundle:
        """逐句合成 + 拼接（HTTP 到 vLLM-Omni server）。"""
        import numpy as np
        import soundfile as sf

        s1_voice = str(voice_map.get("S1", "dylan"))
        s2_voice = str(voice_map.get("S2", "ryan"))
        speaker_voice = {"S1": s1_voice, "S2": s2_voice}

        segments_dir = Path(opts.output_dir) / "segments"
        segments_dir.mkdir(parents=True, exist_ok=True)
        segments: list[Path] = []
        total_frames = 0

        valid_turns = [(i, t.speaker, (t.text or "").strip())
                       for i, t in enumerate(script.turns) if (t.text or "").strip()]

        # 逐句合成（HTTP，server 端连续批处理）。
        # 实测单请求有 ~21s 固定开销（vLLM-Omni 每请求重建 cudagraph），
        # 用线程池并发发请求摊薄它（server 端连续批处理，GPU 单进程吃满）。
        from concurrent.futures import ThreadPoolExecutor

        def _synth(item):
            i, spk, text = item
            voice = speaker_voice.get(spk, "dylan")
            wav, sr = self._synthesize_one(text, voice)
            return i, wav, sr

        turn_wavs: dict[int, tuple[np.ndarray, int]] = {}
        with ThreadPoolExecutor(max_workers=8) as ex:
            for i, wav, sr in ex.map(_synth, valid_turns):
                turn_wavs[i] = (wav, sr)

        # 按顺序拼接（同 SegmentedTTSProvider）
        import random
        rng = random.Random(42)
        all_frames: list[np.ndarray] = []
        prev_spk = None
        for i, spk, _ in valid_turns:
            wav, sr = turn_wavs[i]
            if prev_spk is not None:
                if spk != prev_spk:
                    pause_ms = rng.randint(*self.PAUSE_SPEAKER_SWITCH_MS)
                else:
                    pause_ms = rng.randint(*self.PAUSE_SAME_SPEAKER_MS)
                all_frames.append(np.zeros(int(sr * pause_ms / 1000), dtype=np.float32))
            all_frames.append(wav)
            prev_spk = spk

            seg_path = segments_dir / f"turn{i:03d}.wav"
            sf.write(str(seg_path), wav.astype("float32"), sr)
            segments.append(seg_path)
            total_frames += len(wav)

        combined = np.concatenate(all_frames, axis=0) if all_frames else np.zeros(1, dtype=np.float32)

        # 响度归一化：防削波（vLLM-Omni 输出可能满幅 peak=1.0）
        peak = float(np.abs(combined).max())
        if peak > 0.95:
            combined = combined * (0.9 / peak)

        bundle_path = Path(opts.output_dir) / "episode.wav"
        sf.write(str(bundle_path), combined.astype("float32"), sr)

        return AudioBundle(wav_path=bundle_path, segments=segments,
                           duration_s=round(len(combined) / sr, 2), vram_gb=0.0)


def load_provider(config: dict) -> TTSProvider:
    kind = config.get("provider", "")
    if kind == "moss-ttsd":
        return DialogueTTSProvider(model_dir=config.get("model_dir", "models/moss-ttsd"))
    if kind == "qwen3-tts":
        return SegmentedTTSProvider(model_dir=config.get("model_dir", "models/qwen3-tts-customvoice"))
    if kind == "vllm-omni":
        return VLLMTTSProvider(base_url=config.get("base_url", "http://localhost:8000"),
                               speed=config.get("speed", 1.15))
    if kind == "cosyvoice3":
        return SegmentedTTSProvider(model_dir=config.get("model_dir", "models/cosyvoice3"))
    raise ValueError(f"未知 TTS provider: {kind!r}")


# ── CLI ──────────────────────────────────────────────────────────────────────

def _cli_synthesize(argv: list[str]) -> int:
    """python3 scripts/tts.py synthesize <script.md> --voice-map S1=wav S2=wav --output <dir> [--target-minutes N]"""
    args = argv[1:]  # drop subcommand
    if not args:
        print(__doc__, file=sys.stderr)
        return 2
    script_path = Path(args[0])
    voice_map: dict[str, str] = {}
    output_dir = Path("audio")
    target_minutes = 35.0
    provider_name = "qwen3-tts"  # 默认 Qwen3-TTS（2026-08-05 选定主方案）
    i = 1
    while i < len(args):
        if args[i] == "--voice-map" and i + 1 < len(args):
            for pair in args[i + 1].split(","):
                k, _, v = pair.partition("=")
                voice_map[k.strip()] = v.strip()
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output_dir = Path(args[i + 1])
            i += 2
        elif args[i] == "--target-minutes" and i + 1 < len(args):
            target_minutes = float(args[i + 1])
            i += 2
        elif args[i] == "--provider" and i + 1 < len(args):
            provider_name = args[i + 1]
            i += 2
        else:
            i += 1

    if not script_path.is_file():
        print(f"script 不存在: {script_path}", file=sys.stderr)
        return 1
    if "S1" not in voice_map or "S2" not in voice_map:
        print("voice-map 必须含 S1 和 S2（qwen3-tts 传音色名如 S1=dylan,S2=aiden；moss-ttsd 传 wav 路径）", file=sys.stderr)
        return 2

    # 导入 script parser（延迟，避免无 GPU 环境崩溃）
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.script_parser import parse

    script = parse(script_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    model_dir = {
        "moss-ttsd": "models/moss-ttsd",
        "qwen3-tts": "models/qwen3-tts-customvoice",
        "cosyvoice3": "models/cosyvoice3",
    }.get(provider_name, "models/qwen3-tts-customvoice")
    speed = 1.15
    if "--speed" in args:
        speed = float(args[args.index("--speed") + 1])
    provider = load_provider({"provider": provider_name, "model_dir": model_dir, "speed": speed})
    if provider_name != "vllm-omni":
        provider.warmup()
    opts = TTSOpts()
    opts.output_dir = str(output_dir)
    # 官方换算 1s ≈ 12.5 tokens；目标分钟数 × 60s × 12.5 tokens/s，加 30% 余量
    opts.max_new_tokens = int(target_minutes * 60 * 12.5 * 1.3)

    bundle = provider.synthesize(script, voice_map, opts)
    print(f"synthesized: {bundle.wav_path} ({bundle.duration_s}s, {len(bundle.segments)} segments, VRAM {bundle.vram_gb}GB)")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    if argv[0] == "synthesize":
        return _cli_synthesize(argv)
    print(f"tts.py: 未知命令 {argv[0]!r}（支持: synthesize）", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

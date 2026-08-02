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
        chunk_seconds = 45.0
        chunk_chars = int(chunk_seconds * 4.0)  # 4 字/秒口播
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

        # 3-5. 分段生成 + 解码
        device = self._model.device
        pad_code = processor.model_config.audio_pad_code
        segments_dir = Path(opts.output_dir) / "segments"
        segments_dir.mkdir(parents=True, exist_ok=True)
        segments: list[Path] = []
        total_frames = 0
        import soundfile as sf

        for ci, chunk_text in enumerate(chunks):
            conversation = [[
                processor.build_user_message(text=chunk_text, reference=ref_codes),
                processor.build_assistant_message(audio_codes_list=[prompt_audio]),
            ]]
            batch = processor(conversation, mode="continuation")

            # 每段 max_new_tokens：文本 → 步数 + 余量；温度 0.7（实测更稳定）
            chunk_steps = int(len(chunk_text) / 4.0 * 12.5 * 1.3)
            max_new_tokens = max(512, chunk_steps)
            expected_new = int(len(chunk_text) / 4.0 * 12.5)
            min_ok_steps = max(60, int(expected_new * 0.35))

            best_out = None
            best_new = -1
            for attempt in range(3):
                torch.manual_seed(42 + ci * 101 + attempt * 17)
                with torch.no_grad():
                    outputs = model.generate(
                        input_ids=batch["input_ids"].to(device),
                        attention_mask=batch["attention_mask"].to(device),
                        max_new_tokens=max_new_tokens,
                        text_temperature=0.7, text_top_p=0.9, text_top_k=50,
                        audio_temperature=0.7, audio_top_p=0.9, audio_top_k=50,
                        audio_repetition_penalty=1.1,
                    )
                new_steps = int(outputs[0][1].shape[0]) - int(outputs[0][0].item())
                if new_steps > best_new:
                    best_new = new_steps
                    best_out = outputs
                if new_steps >= min_ok_steps:
                    break
            outputs = best_out

            # 解码（自校准）
            audio_codes = outputs[0][1][:, 1:].cpu()
            dedelayed = processor.apply_de_delay_pattern(audio_codes)
            start_length = int(outputs[0][0].item())
            decoded_audio = self._calibrated_decode(dedelayed, start_length, n_vq, pad_code, target_sr)

            for wav in decoded_audio:
                wav_np = wav.cpu().numpy() if hasattr(wav, "cpu") else wav
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


class SegmentedTTSProvider(LocalTTSProvider):
    """CosyVoice3：逐句合成 + 规则插静音拼接。"""
    native_dialogue = False
    PAUSE_SPEAKER_SWITCH_MS = (350, 500)
    PAUSE_SAME_SPEAKER_MS = (150, 250)

    def synthesize(self, script, voice_map: dict, opts: TTSOpts) -> AudioBundle:
        raise NotImplementedError("CosyVoice3 模型接入在 fallback 任务")


def load_provider(config: dict) -> TTSProvider:
    kind = config.get("provider", "")
    if kind == "moss-ttsd":
        return DialogueTTSProvider(model_dir=config.get("model_dir", "models/moss-ttsd"))
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
        else:
            i += 1

    if not script_path.is_file():
        print(f"script 不存在: {script_path}", file=sys.stderr)
        return 1
    if "S1" not in voice_map or "S2" not in voice_map:
        print("voice-map 必须含 S1 和 S2（如 S1=voice-samples/laozhang.wav,S2=voice-samples/akai.wav）", file=sys.stderr)
        return 2

    # 导入 script parser（延迟，避免无 GPU 环境崩溃）
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.script_parser import parse

    script = parse(script_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    provider = load_provider({"provider": "moss-ttsd", "model_dir": "models/moss-ttsd"})
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

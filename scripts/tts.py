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

        # 3. conversation（官方 voice_clone_and_continuation 模式）
        conversation = [[
            processor.build_user_message(text=full_text, reference=ref_codes),
            processor.build_assistant_message(audio_codes_list=[prompt_audio]),
        ]]
        batch = processor(conversation, mode="continuation")

        # 4. 生成
        max_new_tokens = opts.max_new_tokens
        if max_new_tokens is None:
            # 官方换算：1s ≈ 12.5 tokens（README §Generation Hyperparameters）；
            # 中文口播 ~4 字/秒 → 文本字数 → 秒数 → tokens，加 30% 余量
            approx = int(len(full_text) / 4.0 * 12.5 * 1.3)
            max_new_tokens = max(512, approx)
        device = self._model.device
        with torch.no_grad():
            outputs = model.generate(
                input_ids=batch["input_ids"].to(device),
                attention_mask=batch["attention_mask"].to(device),
                max_new_tokens=max_new_tokens,
                text_temperature=1.1, text_top_p=0.9, text_top_k=50,
                audio_temperature=1.1, audio_top_p=0.9, audio_top_k=50,
                audio_repetition_penalty=1.1,
            )

        # 5. decode → 音频波形（官方用法：message.audio_codes_list 已是波形，
        #    不要再过 decode_audio_codes——那是对未解码 codes 的二次解码，时长会 ×n_vq）
        outputs_cpu = [(int(s.item()), t.cpu()) for s, t in outputs]
        decoded = processor.decode(outputs_cpu)

        segments_dir = Path(opts.output_dir) / "segments"
        segments_dir.mkdir(parents=True, exist_ok=True)
        segments: list[Path] = []
        total_frames = 0

        for j, msg in enumerate(decoded):
            for k, audio in enumerate(msg.audio_codes_list):
                if isinstance(audio, (list, tuple)):
                    audio = torch.cat([a if isinstance(a, torch.Tensor) else torch.as_tensor(a) for a in audio], dim=-1)
                if not isinstance(audio, torch.Tensor):
                    audio = torch.as_tensor(audio)
                wav_np = audio.cpu().numpy()
                if wav_np.ndim == 2 and wav_np.shape[0] == 1:
                    wav_np = wav_np[0]  # (1, T) → (T,)
                if wav_np.ndim > 1:
                    wav_np = wav_np[:, 0] if wav_np.shape[0] > 1 else wav_np[0]
                seg_path = segments_dir / f"segment_{j:03d}_{k:03d}.wav"
                import soundfile as sf
                sf.write(str(seg_path), wav_np.astype("float32"), target_sr)
                segments.append(seg_path)
                total_frames += wav_np.shape[0]

        # 6. 拼接总音频
        import soundfile as sf
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

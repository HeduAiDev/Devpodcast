"""TTS：FireRedTTS2 后端（原生双人对话模型，唯一主方案）。

CLI：
    python3 scripts/tts.py synthesize <script.md> --voice-map S1=wav S2=wav --output <dir> [--target-minutes 35] [--pronunciation <json>]

- voice_map 值是 wav 路径，prompt_text 从同目录的 <name>.txt 读
- 发音表（可选）：season/pronunciation.json，合成前替换专有名词为注音读法
"""
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

# 本文件顶层不 import torch，避免无 GPU 环境崩溃。模型在子进程内加载（FireRed 的
# torchaudio → soundfile 兼容 patch 在 infer 模板里，见 FireRedTTSProvider.synthesize）。


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


class FireRedTTSProvider(LocalTTSProvider):
    """FireRedTTS2 后端（2026-08-06 下载验证）。

    原生双人对话模型（codec 4.3GB + llm_posttrain 8.3GB），generate_dialogue
    一次吃整段 turn 列表。torch 2.11 可跑，但 torchaudio 2.11 在本机路由到
    torchcodec 且缺 FFmpeg DLL，需 monkeypatch load/save 走 soundfile。
    """
    native_dialogue = True
    FIRERED_PYTHON = r"E:\Laboratory\Devpodcast\_venv_soulx\Scripts\python.exe"
    FIRERED_REPO = r"E:\Laboratory\Devpodcast\_diag\fireredtts2_repo"

    def __init__(self, model_dir: str | Path = "models/fireredtts2", device: str = "cuda:0",
                 dtype: str = "bfloat16", temperature: float = 0.8, topk: int = 15):
        super().__init__(model_dir, device, dtype)
        # 2026-08-07 参数扫描结论（_diag/firered_sweep/，20 组人工试听）：
        #   temp=0.7 全灭（错字/发音差），topk=10 差；满分(10) 5 组集中在
        #   temp 0.8-1.1 × topk 15-30。选 t0.8_k15：时长 60.3s ≈ 中位 60.5s
        #   （无赶字/拖字），temp 0.8 比 1.1 更稳（长文本不易错）。
        self.temperature = temperature
        self.topk = topk

    def warmup(self) -> None:
        """无需预热（子进程内加载）。"""
        pass

    def synthesize(self, script, voice_map: dict, opts: TTSOpts) -> AudioBundle:
        """分段合成（动态分段，每段 ≤450 字，防超 max_seq_len），段间 350ms 拼接。"""
        import json
        import subprocess
        import time
        from pathlib import Path

        import numpy as np
        import soundfile as sf

        model_abs = Path(self.model_dir).resolve()
        tmp_dir = Path(opts.output_dir) / "firered_tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        # 参考音频转绝对路径
        prompt_wavs, prompt_texts = [], []
        for spk in ("S1", "S2"):
            info = voice_map.get(spk, {}) or {}
            audio = info.get("audio", "")
            prompt_wavs.append(str(Path(audio).resolve()) if audio else "")
            prompt_texts.append(f"[{spk}]{info.get('text', '')}")

        valid_turns = [t for t in script.turns if (t.text or "").strip()]
        # 动态分段（FireRed 上下文预算：max_seq_len=3100 - max_generation_len=375 = 2725 token）。
        # 每轮 ≈ 文本(字×1.5) + 音频(~12.5 token/s × 字数/4s)，实测 30 轮段爆 2725。
        # 450 字/段 ≈ 文本 675 + 音频 ~1400 + prompt ~300 ≈ 2375，留 13% 裕量。
        FIRE_CHUNK_CHARS = 450
        chunks: list[list] = []
        cur: list = []
        cur_chars = 0
        for t in valid_turns:
            n = len((t.text or "").strip())
            if cur and cur_chars + n > FIRE_CHUNK_CHARS:
                chunks.append(cur)
                cur, cur_chars = [], 0
            cur.append(t)
            cur_chars += n
        if cur:
            chunks.append(cur)
        print(f"  [tts] FireRed 分段合成：{len(chunks)} 段（每段 ≤{FIRE_CHUNK_CHARS} 字，动态）", flush=True)

        segments_dir = Path(opts.output_dir) / "segments"
        segments_dir.mkdir(parents=True, exist_ok=True)
        segments: list[Path] = []

        for ci, chunk_turns in enumerate(chunks):
            text_list = [f"[{t.speaker}]{(t.text or '').strip()}" for t in chunk_turns]
            payload = {
                "text_list": text_list,
                "prompt_wav_list": prompt_wavs,
                "prompt_text_list": prompt_texts,
            }
            chunk_json = (tmp_dir / f"chunk{ci:02d}.json").resolve()
            chunk_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

            chunk_wav = (segments_dir / f"chunk{ci:02d}.wav").resolve()
            infer_py = tmp_dir / f"infer_{ci:02d}.py"
            infer_py.write_text(f'''
import json, sys, time
REPO = r"{self.FIRERED_REPO}"
MODEL = r"{model_abs}"
SCRIPT = r"{chunk_json}"
OUT = r"{chunk_wav}"
sys.path.insert(0, REPO)

import numpy as np, soundfile as sf, torch, torchaudio

def _ta_load(path, *a, **kw):
    data, sr = sf.read(str(path), dtype="float32", always_2d=True)
    return torch.from_numpy(data.T).contiguous(), sr

def _ta_save(path, src, sample_rate, *a, **kw):
    arr = src.detach().cpu().numpy() if isinstance(src, torch.Tensor) else np.asarray(src)
    if arr.ndim == 2 and arr.shape[0] == 1:
        arr = arr[0]
    sf.write(str(path), arr, sample_rate)

torchaudio.load = _ta_load
torchaudio.save = _ta_save

from fireredtts2.fireredtts2 import FireRedTTS2

_t0 = time.time()
model = FireRedTTS2(pretrained_dir=MODEL, gen_type="dialogue", device="cuda", use_bf16=True)
_t1 = time.time()
print(f"  [firered] load: {{_t1 - _t0:.1f}}s", flush=True)

with open(SCRIPT, encoding="utf-8") as f:
    data = json.load(f)

_t2 = time.time()
audio = model.generate_dialogue(
    text_list=data["text_list"],
    prompt_wav_list=data["prompt_wav_list"],
    prompt_text_list=data["prompt_text_list"],
    temperature={self.temperature},
    topk={self.topk},
)
_t3 = time.time()
print(f"  [firered] decode: {{_t3 - _t2:.1f}}s", flush=True)

sf.write(OUT, audio.cpu().squeeze(0).numpy(), 24000)
print(f"chunk done: {{audio.shape[-1]/24000.0:.1f}}s")
''', encoding="utf-8")

            t0 = time.time()
            subprocess.run([self.FIRERED_PYTHON, str(infer_py)], check=True, timeout=1800)
            elapsed = time.time() - t0
            x, sr = sf.read(chunk_wav, dtype="float32")
            print(f"  chunk {ci+1}/{len(chunks)}: {len(x)/sr:.1f}s ({elapsed:.1f}s)", flush=True)
            segments.append(chunk_wav)

        all_frames = []
        for i, seg in enumerate(segments):
            x, sr = sf.read(seg, dtype="float32")
            if i > 0:
                all_frames.append(np.zeros(int(sr * 0.35), dtype=np.float32))
            all_frames.append(x)
        combined = np.concatenate(all_frames, axis=0)
        # FireRed 各段峰值归一化到 1.0，拼接后必然 0dB 削波——整体降到 0.95 留 headroom
        peak = float(np.abs(combined).max())
        if peak > 0.95:
            combined = combined * (0.95 / peak)
        out_wav = (Path(opts.output_dir) / "episode.wav").resolve()
        sf.write(str(out_wav), combined.astype("float32"), sr)

        return AudioBundle(
            wav_path=out_wav,
            segments=segments,
            duration_s=round(len(combined) / sr, 2),
            vram_gb=0.0,
        )


def load_provider(config: dict) -> TTSProvider:
    kind = config.get("provider", "")
    if kind == "firered-tts2":
        return FireRedTTSProvider(model_dir=config.get("model_dir", "models/fireredtts2"))
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
    provider_name = "firered-tts2"  # 默认 FireRedTTS2（2026-08-07 选定主方案）
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
        print("voice-map 必须含 S1 和 S2（firered-tts2 传 wav 路径，prompt_text 从同目录的 <name>.txt 读）", file=sys.stderr)
        return 2

    # firered-tts2: voice_map 值是 wav 路径，prompt_text 从同目录的 <name>.txt 读
    for spk in ("S1", "S2"):
        wav_path = voice_map[spk]
        txt_path = Path(wav_path).with_suffix(".txt")
        voice_map[spk] = {
            "audio": wav_path,
            "text": txt_path.read_text(encoding="utf-8").strip() if txt_path.is_file() else "",
        }

    # 导入 script parser（延迟，避免无 GPU 环境崩溃）
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.script_parser import parse

    script = parse(script_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    model_dir = "models/fireredtts2"
    provider = load_provider({"provider": provider_name, "model_dir": model_dir})
    provider.warmup()

    # 注音替换：script.md 里英文/专有名词 → 中文读法（如 SGLang → SG浪），
    # 避免 TTS 逐字母念。只改喂给 TTS 的文本，不改 script.md。
    # 发音表：<output 上级>/<show>/season/pronunciation.json，或 --pronunciation 显式指定
    pron_json = None
    if "--pronunciation" in args:
        pron_json = Path(args[args.index("--pronunciation") + 1])
    else:
        # 从 script 路径回退找 show 目录：episodes/<slug>/script.md → shows/<show>/season/pronunciation.json
        try:
            show_dir = script_path.resolve().parents[2]
            cand = show_dir / "season" / "pronunciation.json"
            if cand.is_file():
                pron_json = cand
        except Exception:
            pron_json = None
    if pron_json and pron_json.is_file():
        import json
        pron_data = json.loads(pron_json.read_text(encoding="utf-8"))
        pron_map = {k: v.get("replace", k) for k, v in pron_data.get("terms", {}).items() if v.get("replace")}
        if pron_map:
            # 长词优先（避免 "KV cache" 被 "cache" 先替换之类）
            for term, pron in sorted(pron_map.items(), key=lambda kv: -len(kv[0])):
                for t in script.turns:
                    if t.text and term in t.text:
                        t.text = t.text.replace(term, pron)
            print(f"  [tts] 注音替换：{len(pron_map)} 词（{pron_json.name}）", flush=True)
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

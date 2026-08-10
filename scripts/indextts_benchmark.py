#!/usr/bin/env python3
"""IndexTTS-2 benchmark：零样本克隆 + CUDA 发音 + RTF 测量。

用 itts310 conda 环境跑（CUDA torch）。对比 FireRed 单句基线。
测试：laozhang/akai/kurisu 三个参考音色，中文克隆 + CUDA 读法。

运行：D:/miniconda3/envs/itts310/python.exe scripts/indextts_benchmark.py
"""
import sys, time, os
from pathlib import Path

REPO = Path(__file__).parent.parent
MODEL_DIR = REPO / "models" / "indextts2"
CFG = MODEL_DIR / "config.yaml"
VS = REPO / "shows" / "vllm-podcast" / "voice-samples"
OUT = REPO / "_diag" / "indextts_bench"
OUT.mkdir(parents=True, exist_ok=True)

# IndexTTS 需要 16kHz mono 参考（脚本已预转好）
REFS = {
    "laozhang": str(VS / "laozhang_16k.wav"),
    "akai": str(VS / "akai_16k.wav"),
    "kurisu": str(VS / "kurisu_ref_16k.wav"),
}

# 测试文本：含 CUDA 测发音，普通句测克隆质量
TEST_TEXTS = {
    "cuda": "vLLM 用 CUDA graph 优化 GPU 上的算子执行，这样能减少内核启动开销。",
    "normal": "大家好，今天我们来聊一聊大语言模型的推理引擎，看看它是如何高效管理显存的。",
}


def main():
    print(f"[load] IndexTTS2 from {MODEL_DIR}", flush=True)
    t0 = time.time()
    from indextts.infer_v2 import IndexTTS2
    tts = IndexTTS2(cfg_path=str(CFG), model_dir=str(MODEL_DIR), use_fp16=False, device="cuda")
    print(f"[load] 模型加载 {time.time()-t0:.1f}s", flush=True)

    results = []
    for spk, ref in REFS.items():
        if not Path(ref).exists():
            print(f"[skip] {spk}: 参考音频不存在 {ref}", flush=True)
            continue
        for name, text in TEST_TEXTS.items():
            tag = f"{spk}_{name}"
            out_wav = str(OUT / f"{tag}.wav")
            t1 = time.time()
            tts.infer(spk_audio_prompt=ref, text=text, output_path=out_wav)
            elapsed = time.time() - t1
            # RTF = 合成耗时 / 音频时长
            import soundfile as sf
            x, sr = sf.read(out_wav, dtype="float32")
            dur = len(x) / sr if x.ndim == 1 else len(x[:, 0]) / sr
            rtf = elapsed / dur if dur > 0 else float("inf")
            results.append({"tag": tag, "gen_s": round(elapsed, 1), "audio_s": round(dur, 1), "rtf": round(rtf, 3)})
            print(f"[{tag}] 合成 {elapsed:.1f}s / 音频 {dur:.1f}s → RTF {rtf:.3f}", flush=True)

    print("\n=== RTF 汇总（越低越快）===", flush=True)
    for r in results:
        print(f"  {r['tag']:<25} RTF {r['rtf']}", flush=True)

    import json
    (OUT / "rtf_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n输出目录: {OUT}", flush=True)
    print("下一步: 用 whisper 转写检查 CUDA 是否读对 + 人耳听克隆质量", flush=True)


if __name__ == "__main__":
    main()

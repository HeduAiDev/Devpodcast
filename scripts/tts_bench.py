#!/usr/bin/env python3
"""TTS 调参基准测试：固定在 ep01 摘录（6 turns, ~69s 音频）上跑，避免每次烧 26 分钟。

用法：
    python scripts/tts_bench.py [--runs 3]

输出：
    - _diag/tts_bench/<provider>_<timestamp>/episode.wav
    - 每次跑打印 RTF (Real-Time Factor)：耗时 / 音频时长
"""
import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.tts import (
    FireRedTTSProvider,
    TTSOpts,
)
from scripts.script_parser import parse as parse_script


@dataclass
class BenchResult:
    provider: str
    audio_duration_s: float
    wall_time_s: float
    rtf: float
    output_path: str


def load_excerpt() -> tuple[object, dict]:
    """加载 _ep01_excerpt.md + 音色配置。"""
    script_path = Path("_ep01_excerpt.md")
    if not script_path.exists():
        raise FileNotFoundError(f"摘录不存在：{script_path}")

    script = parse_script(script_path)

    # 音色映射：参考音频 + 文本（voice-samples/ 官方中文样本）
    voice_map = {
        "S1": {
            "audio": "shows/vllm-podcast/voice-samples/laozhang.wav",
            "text": "大家好，我是老张，今天这期我们来聊聊大语言模型推理引擎。这个话题最近特别火，很多面试都会问到。",
        },
        "S2": {
            "audio": "shows/vllm-podcast/voice-samples/akai.wav",
            "text": "大家好，我是阿凯，负责技术侧的讲解。今天这期我们把 vLLM 拆开讲清楚。",
        },
    }
    return script, voice_map


def bench_one(provider_name: str, run_id: int) -> BenchResult:
    """单次基准测试。"""
    script, voice_map = load_excerpt()

    # 输出目录
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_dir = Path(f"_diag/tts_bench/{provider_name}_{ts}_r{run_id}")
    out_dir.mkdir(parents=True, exist_ok=True)

    opts = TTSOpts(output_dir=str(out_dir))

    # 构建 provider（唯一主方案：FireRedTTS2）
    provider = FireRedTTSProvider(model_dir="models/fireredtts2")

    print(f"\n=== Run {run_id}: {provider_name} ===")
    print(f"摘录：{len([t for t in script.turns if t.text.strip()])} turns")

    t0 = time.time()
    bundle = provider.synthesize(script, voice_map, opts)
    wall = time.time() - t0

    dur = bundle.duration_s
    rtf = wall / dur if dur > 0 else float("inf")

    print(f"音频时长：{dur:.1f}s")
    print(f"耗时：{wall:.1f}s")
    print(f"RTF：{rtf:.3f}  ({'< 1.0 合格' if rtf < 1.0 else '≥ 1.0 不合格'})")
    print(f"输出：{out_dir / 'episode.wav'}")

    return BenchResult(
        provider=provider_name,
        audio_duration_s=dur,
        wall_time_s=wall,
        rtf=rtf,
        output_path=str(out_dir / "episode.wav"),
    )


def main():
    parser = argparse.ArgumentParser(description="TTS 调参基准测试（固定 ep01 摘录，FireRedTTS2）")
    parser.add_argument("--runs", type=int, default=1, help="重复次数（取中位数）")
    args = parser.parse_args()

    results = []
    for i in range(1, args.runs + 1):
        r = bench_one("firered", i)
        results.append(r)

    # 汇总
    print(f"\n=== 汇总（{len(results)} 次）===")
    rtfs = [r.rtf for r in results]
    rtfs.sort()
    median_rtf = rtfs[len(rtfs) // 2]
    print(f"RTF 中位数：{median_rtf:.3f}")
    print(f"最快：{min(rtfs):.3f}  最慢：{max(rtfs):.3f}")

    # 保存结果
    summary = {
        "provider": "firered",
        "runs": len(results),
        "rtf_median": median_rtf,
        "rtf_min": min(rtfs),
        "rtf_max": max(rtfs),
        "details": [
            {
                "audio_duration_s": r.audio_duration_s,
                "wall_time_s": r.wall_time_s,
                "rtf": r.rtf,
                "output_path": r.output_path,
            }
            for r in results
        ],
    }
    summary_path = Path("_diag/tts_bench/firered_summary.json")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n结果已保存：{summary_path}")


if __name__ == "__main__":
    main()

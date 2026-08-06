#!/usr/bin/env python3
"""FireRedTTS2 参数扫描：temperature × topk 网格，固定在 ep01 摘录上跑。

模型只加载一次（38s），网格内所有组合共用，避免每组重复加载。

用法：
    python scripts/firered_param_sweep.py [--grid default|fine|quick]

输出：
    - _diag/firered_sweep/t<temp>_k<topk>.wav
    - _diag/firered_sweep/summary.json
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.script_parser import parse as parse_script

FIRERED_PYTHON = r"E:\Laboratory\Devpodcast\_venv_soulx\Scripts\python.exe"
FIRERED_REPO = "E:/Laboratory/Devpodcast/_diag/fireredtts2_repo"
FIRERED_MODEL = "E:/Laboratory/Devpodcast/models/fireredtts2"

GRIDS = {
    # 官方默认 temp=0.9/topk=20；firered_infer.py 验证用的是 topk=30
    "quick": ([0.7, 0.9], [20, 30]),
    "default": ([0.7, 0.9, 1.1], [15, 20, 30]),
    "fine": ([0.6, 0.7, 0.8, 0.9, 1.1], [10, 15, 20, 30]),
}


def load_excerpt():
    script_path = Path("_ep01_excerpt.md")
    if not script_path.exists():
        raise FileNotFoundError(f"摘录不存在：{script_path}")
    script = parse_script(script_path)

    voice_map = {
        "S1": {
            "audio": "shows/vllm-podcast/voice-samples/laozhang.wav",
            "text": "周一到周五每天早晨七点半到九点半的直播片段一下之意呢就是废话有点多大家也别嫌弃因为这都是直播间最真实的状态",
        },
        "S2": {
            "audio": "shows/vllm-podcast/voice-samples/akai.wav",
            "text": "如果大家想听到更丰富更及时的直播内容记得在周一到周五准时进入直播间和大家一起唱聊新消费新科技新趋势",
        },
    }
    return script, voice_map


def build_payload(script, voice_map, temps, topks, out_dir: Path) -> Path:
    prompt_wavs = [str(Path(voice_map[s]["audio"]).resolve()) for s in ("S1", "S2")]
    prompt_texts = [f"[{s}]{voice_map[s]['text']}" for s in ("S1", "S2")]
    text_list = [
        f"[{t.speaker}]{(t.text or '').strip()}"
        for t in script.turns
        if (t.text or "").strip()
    ]
    payload = {
        "text_list": text_list,
        "prompt_wav_list": prompt_wavs,
        "prompt_text_list": prompt_texts,
        "combos": [{"temperature": t, "topk": k} for t in temps for k in topks],
        "out_dir": str(out_dir.resolve()),
        "skip_existing": True,
    }
    p = out_dir / "payload.json"
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


SWEEP_TEMPLATE = '''
import json, sys, time
sys.path.insert(0, r"{repo}")
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

with open(r"{payload}", encoding="utf-8") as f:
    D = json.load(f)

_t0 = time.time()
model = FireRedTTS2(pretrained_dir=r"{model}", gen_type="dialogue", device="cuda", use_bf16=True)
print(f"[load] {{time.time()-_t0:.1f}}s", flush=True)

import os
records = []
for i, combo in enumerate(D["combos"], 1):
    temp, topk = combo["temperature"], combo["topk"]
    tag = f"t{{temp}}_k{{topk}}"
    wav_path = D["out_dir"] + "/" + tag + ".wav"
    if D.get("skip_existing") and os.path.exists(wav_path):
        arr, _sr = sf.read(wav_path, dtype="float32")
        dur = len(arr) / 24000
        print(f"[{{i}}/{{len(D['combos'])}}] {{tag}} SKIP (已存在 {{dur:.1f}}s)", flush=True)
        records.append({{
            "temperature": temp, "topk": topk, "audio_duration_s": round(dur, 2),
            "decode_s": None, "rtf": None, "wav": wav_path, "skipped": True,
        }})
        continue
    print(f"[{{i}}/{{len(D['combos'])}}] {{tag}}", flush=True)
    torch.manual_seed(1988)  # 固定种子，隔离参数影响
    _t = time.time()
    audio = model.generate_dialogue(
        text_list=D["text_list"],
        prompt_wav_list=D["prompt_wav_list"],
        prompt_text_list=D["prompt_text_list"],
        temperature=temp,
        topk=topk,
    )
    decode_s = time.time() - _t
    wav = D["out_dir"] + "/" + tag + ".wav"
    arr = audio.cpu().squeeze(0).numpy()
    sf.write(wav, arr, 24000)
    dur = len(arr) / 24000
    records.append({{
        "temperature": temp, "topk": topk, "audio_duration_s": round(dur, 2),
        "decode_s": round(decode_s, 1), "rtf": round(decode_s / dur, 3) if dur else None,
        "wav": wav,
    }})
    print(f"  {{dur:.1f}}s audio, decode {{decode_s:.1f}}s, RTF {{decode_s/dur:.2f}}", flush=True)

with open(D["out_dir"] + "/records.json", "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)
print("SWEEP DONE")
'''


def main():
    ap = argparse.ArgumentParser(description="FireRedTTS2 参数扫描")
    ap.add_argument("--grid", default="default", choices=list(GRIDS))
    args = ap.parse_args()

    temps, topks = GRIDS[args.grid]
    n = len(temps) * len(topks)

    script, voice_map = load_excerpt()
    out_dir = Path("_diag/firered_sweep")
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = build_payload(script, voice_map, temps, topks, out_dir)
    infer_py = out_dir / "sweep_infer.py"
    infer_py.write_text(
        SWEEP_TEMPLATE.format(repo=FIRERED_REPO, model=FIRERED_MODEL, payload=payload.resolve()),
        encoding="utf-8",
    )

    print(f"网格 {args.grid}：{len(temps)} temp × {len(topks)} topk = {n} 组")
    print(f"预估耗时：{n} × ~175s + 38s 加载 ≈ {(n * 175 + 38) / 60:.0f} 分钟")

    t0 = time.time()
    subprocess.run([FIRERED_PYTHON, str(infer_py)], check=True, timeout=n * 400 + 600)
    wall = time.time() - t0

    records = json.loads((out_dir / "records.json").read_text(encoding="utf-8"))
    summary = {
        "grid": args.grid,
        "total": len(records),
        "wall_time_s": round(wall, 1),
        "records": records,
        "note": "听 wav 后给每组填 manual_score（0-10）：音色自然度 / 无重复 / 无漂移",
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\n=== 汇总（{len(records)} 组，{wall/60:.1f} 分钟）===")
    for r in records:
        print(f"  temp={r['temperature']:<4} topk={r['topk']:<3} "
              f"{r['audio_duration_s']:>6.1f}s  RTF {r['rtf']:.2f}  {Path(r['wav']).name}")
    print(f"\n结果：{out_dir / 'summary.json'}")
    print("下一步：听 wav 挑最自然的一组，填 manual_score")


if __name__ == "__main__":
    main()

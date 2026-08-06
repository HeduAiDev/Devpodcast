#!/usr/bin/env python3
"""FireRedTTS2 单段合成（供手动分段续跑）。

背景：tts.py 的连续多段合成在 Windows 上会被进程回收（每段 infer 子进程 12.7GB 模型，
长时间运行被系统终止）。本脚本一次只合成一个 chunk，独立进程跑完即退，
段间由外部轮询续跑，规避长任务回收。

用法：
    python scripts/firered_synth_chunk.py <episode_dir> <chunk_idx> <segments_dir>
"""
import json
import subprocess
import sys
import time
from pathlib import Path

FIRERED_PYTHON = r"E:\Laboratory\Devpodcast\_venv_soulx\Scripts\python.exe"
FIRERED_REPO = "E:/Laboratory/Devpodcast/_diag/fireredtts2_repo"
FIRERED_MODEL = "E:/Laboratory/Devpodcast/models/fireredtts2"
TEMP = 0.8
TOPK = 15


def main():
    ep_dir = Path(sys.argv[1])
    idx = int(sys.argv[2])
    seg_dir = Path(sys.argv[3])

    payload = ep_dir / "audio" / "firered_tmp" / f"chunk{idx:02d}.json"
    if not payload.exists():
        raise SystemExit(f"chunk payload 不存在: {payload}")

    out_wav = seg_dir / f"chunk{idx:02d}.wav"
    if out_wav.exists():
        print(f"chunk{idx:02d} 已存在，跳过")
        return

    infer_py = ep_dir / "audio" / "firered_tmp" / f"infer_{idx:02d}.py"
    infer_py.write_text(f'''
import json, sys, time
sys.path.insert(0, r"{FIRERED_REPO}")
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
model = FireRedTTS2(pretrained_dir=r"{FIRERED_MODEL}", gen_type="dialogue", device="cuda", use_bf16=True)
print(f"[load] {{time.time()-_t0:.1f}}s", flush=True)

_t1 = time.time()
audio = model.generate_dialogue(
    text_list=D["text_list"],
    prompt_wav_list=D["prompt_wav_list"],
    prompt_text_list=D["prompt_text_list"],
    temperature={TEMP},
    topk={TOPK},
)
print(f"[decode] {{time.time()-_t1:.1f}}s", flush=True)

arr = audio.cpu().squeeze(0).numpy()
sf.write(r"{out_wav}", arr, 24000)
dur = len(arr) / 24000
print(f"chunk{idx:02d} done: {{dur:.1f}}s", flush=True)
''', encoding="utf-8")

    print(f"=== 合成 chunk{idx:02d} ===")
    t0 = time.time()
    subprocess.run([FIRERED_PYTHON, str(infer_py)], check=True, timeout=1800)
    print(f"chunk{idx:02d} 完成，耗时 {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()

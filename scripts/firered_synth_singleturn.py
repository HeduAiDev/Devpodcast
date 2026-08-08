#!/usr/bin/env python3
"""
FireRed 单句合成（逐 turn 独立，无上下文）
- 每个 turn 独立调用 generate_dialogue(text_list=[单句])
- 无 carryover、无段内上下文累积 → 音色零漂移、角色零错配
- 每 turn 固定 seed=turn_idx（可复现）
"""
import sys, json, subprocess
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: firered_synth_singleturn.py <episode_dir>")

    ep_dir = Path(sys.argv[1]).resolve()
    script_md = ep_dir / "script.md"
    seg_dir = ep_dir / "audio" / "segments"
    seg_dir.mkdir(parents=True, exist_ok=True)

    # 解析 script.md，提取所有 turns
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.script_parser import parse
    script = parse(script_md)
    turns = [t for t in script.turns if (t.text or '').strip()]

    if not turns:
        raise SystemExit(f"No turns in {script_md}")

    # 加载发音表
    show_dir = ep_dir.parent.parent
    pron_json = show_dir / "season" / "pronunciation.json"
    pron_map = {}
    if pron_json.exists():
        pron_data = json.loads(pron_json.read_text(encoding='utf-8'))
        pron_map = {k: v.get("replace", k) for k, v in pron_data.get("terms", {}).items() if v.get("replace")}
        print(f"Loaded {len(pron_map)} pronunciation rules from {pron_json}")

    print(f"Found {len(turns)} turns, synthesizing single-turn mode...")

    # 参考音频
    pw = [str(Path('shows/vllm-podcast/voice-samples/laozhang.wav').resolve()),
          str(Path('shows/vllm-podcast/voice-samples/akai.wav').resolve())]
    pt = ['[S1]' + Path('shows/vllm-podcast/voice-samples/laozhang.txt').read_text(encoding='utf-8').strip(),
          '[S2]' + Path('shows/vllm-podcast/voice-samples/akai.txt').read_text(encoding='utf-8').strip()]

    FIRERED_PYTHON = r"E:\Laboratory\Devpodcast\_venv_soulx\Scripts\python.exe"
    FIRERED_REPO = r"E:\Laboratory\Devpodcast\_diag\fireredtts2_repo"
    FIRERED_MODEL = r"E:\Laboratory\Devpodcast\models\fireredtts2"

    # 生成单进程 infer 脚本（加载模型一次，逐 turn 合成）
    tmp_dir = ep_dir / "audio" / "firered_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    infer_py = tmp_dir / "infer_singleturn.py"

    # 序列化 turns（应用发音表）
    turns_data = []
    for t in turns:
        text = (t.text or '').strip()
        # 应用发音表
        for term, pron in pron_map.items():
            text = text.replace(term, pron)
        text = f"[{t.speaker}]{text}"
        turns_data.append({'speaker': t.speaker, 'text': text})

    turns_json = tmp_dir / "turns.json"
    turns_json.write_text(json.dumps({
        'turns': turns_data,
        'prompt_wav': pw,
        'prompt_text': pt
    }, ensure_ascii=False, indent=2), encoding='utf-8')

    seg_dir_str = str(seg_dir).replace("\\", "\\\\")
    turns_json_str = str(turns_json).replace("\\", "\\\\")

    infer_py.write_text(f'''
import json, time, sys
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

print("[load] Loading FireRed model...", flush=True)
_t0 = time.time()
model = FireRedTTS2(pretrained_dir=r"{FIRERED_MODEL}", gen_type="dialogue", device="cuda", use_bf16=True)
print(f"[load] Model loaded in {{time.time()-_t0:.1f}}s", flush=True)

with open(r"{turns_json_str}", encoding="utf-8") as f:
    D = json.load(f)

seg_dir = r"{seg_dir_str}"

for i, turn in enumerate(D['turns']):
    _t1 = time.time()
    torch.manual_seed(i)  # 每 turn 固定 seed

    # 单句：text_list 只有 1 个元素，无上下文
    audio = model.generate_dialogue(
        text_list=[turn['text']],
        prompt_wav_list=D['prompt_wav'],
        prompt_text_list=D['prompt_text'],
        temperature=0.8, topk=15
    )

    arr = audio.cpu().squeeze(0).numpy()
    out_wav = f"{{seg_dir}}/turn{{i:03d}}.wav"
    sf.write(out_wav, arr, 24000)

    dur = len(arr) / 24000
    print(f"turn{{i:03d}} done: {{time.time()-_t1:.1f}}s gen, {{dur:.1f}}s audio", flush=True)

print("All done!", flush=True)
''', encoding='utf-8')

    # 运行单进程合成
    print(f"Running single-turn synthesis...")
    subprocess.run([FIRERED_PYTHON, str(infer_py)], check=True, timeout=7200)

    # 拼接所有 turns（简单拼接，每 turn 间加 100ms 静音过渡）
    print(f"Concatenating {len(turns)} turns...")
    concat_py = tmp_dir / "concat.py"
    concat_py.write_text(f'''
import soundfile as sf, numpy as np
from pathlib import Path
seg_dir = Path(r"{seg_dir_str}")
turns = sorted(seg_dir.glob("turn*.wav"))
if not turns:
    raise SystemExit("No turn*.wav found")
parts = []
silence_100ms = np.zeros(int(0.1 * 24000), dtype='float32')
for t in turns:
    x, sr = sf.read(t, dtype='float32')
    if x.ndim > 1: x = x.mean(1)
    parts.append(x)
    parts.append(silence_100ms)
out = np.concatenate(parts[:-1])  # 去掉最后的静音
# 峰值归一化 0.95（防削波）
peak = np.abs(out).max()
if peak > 0.95:
    out = out * (0.95 / peak)
out_path = seg_dir.parent / "full.wav"
sf.write(out_path, out, 24000)
print(f"Concat done: {{len(out)/24000:.1f}}s → {{out_path}}", flush=True)
''', encoding='utf-8')
    subprocess.run([FIRERED_PYTHON, str(concat_py)], check=True, timeout=120)

    print(f"Done! Full audio: {ep_dir}/audio/full.wav")

if __name__ == "__main__":
    main()

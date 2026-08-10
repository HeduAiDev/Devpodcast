# voice-samples/

三声线参考音色（IndexTTS-2 用），vllm-podcast 与 lacan-desire 两个栏目共用。

## 文件清单

| 文件 | 角色 | 说明 |
|---|---|---|
| `laozhang.wav` | S1 老张（主持人） | 原始 24kHz 源（MOSS-TTSD 官方示例 zh_spk1_moon.wav） |
| `laozhang_16k.wav` | S1 老张 | **IndexTTS-2 实际引用**，16kHz mono |
| `akai.wav` | S2 阿凯（作者/专家） | 原始 24kHz 源（MOSS-TTSD 官方示例 zh_spk2_moon.wav） |
| `akai_16k.wav` | S2 阿凯 | **IndexTTS-2 实际引用**，16kHz mono |
| `azhe_16k.wav` | S3 阿哲（读者代言人） | **IndexTTS-2 实际引用**，16kHz mono（Qwen3-TTS dylan 生成，无原始 24kHz 源） |
| `laozhang.txt` / `akai.txt` | 参考转录文本 | MOSS-TTSD 配套 prompt_text |

## 要求

- IndexTTS-2 用 16kHz mono 参考（`*_16k.wav`）
- 原始 wav 保留 24kHz 母本，重生成 16k 用 `ffmpeg -i X.wav -ar 16000 -ac 1 X_16k.wav`
- 原始 `*.wav` 与 `*.txt` 保留（MOSS-TTSD 时代的母本与转录）

## 来源与授权

- `laozhang.wav` / `akai.wav` = MOSS-TTSD v0.7 官方中文示例（`zh_spk1_moon.wav` / `zh_spk2_moon.wav`）
- `azhe_16k.wav` = Qwen3-TTS CustomVoice dylan（北京话）生成
- 用途：临时音色占位（验证 pipeline）。正式发布前建议替换为自录中文音色

## 代码引用

- `scripts/indextts_synth_singleturn.py` — REFS 字典（S1/S2/S3 → `*_16k.wav`）
- `scripts/indextts_synth_blog.py` — REF_S1（老张）
- `scripts/indextts_benchmark.py` / `scripts/fix_mumble_indextts.py` — 同 singleturn

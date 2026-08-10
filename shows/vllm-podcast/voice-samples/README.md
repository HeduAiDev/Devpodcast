# voice-samples/

S1（老张）与 S2（阿凯）的音色 prompt 音频（FireRedTTS2 参考音频）。

## 要求

- 格式：WAV，≥24000Hz，单声道
- 时长：5–10 秒，清晰单人录音
- 内容：自然说话（口语），不要念稿
- 末尾：留 1s 静音
- 文件名：`laozhang.wav` / `akai.wav`
- **必须配同目录 `<name>.txt`**：prompt_text（与音频内容对应的转写文本），FireRedTTS2 用它做参考。缺 .txt 会读空 → 音色退化

## 来源与授权

- `laozhang.wav` = MOSS-TTSD v0.7 官方中文示例 `zh_spk1_moon.wav`（MOSS-TTSD 仓库 legacy/v0.7/examples/）
- `akai.wav` = MOSS-TTSD v0.7 官方中文示例 `zh_spk2_moon.wav`
- 用途：临时音色占位（验证 pipeline）。正式发布前建议替换为自录的中文音色样本（各 5-10s 自然口语，配对应 .txt）。

<!-- 样本文件本身不入库（.gitignore 已排除 *.wav） -->

## FireRedTTS2 用法

- `scripts/tts.py synthesize` 的 voice_map 传 wav 路径，prompt_text 自动从同目录 `<name>.txt` 读
- prompt_wav_list / prompt_text_list 作为双人参考，模型按各自身份生成后续对话
- 音色稳定性的关键在参考音频质量与 prompt_text 准确性（whisper 转写即可）

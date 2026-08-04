# voice-samples/

S1（老张）与 S2（阿凯）的音色 prompt 音频。

## 要求

- 格式：WAV，≥24000Hz，单声道
- 时长：5–10 秒，清晰单人录音
- 内容：自然说话（口语），不要念稿
- 末尾：留 1s 静音
- 文件名：`laozhang.wav` / `akai.wav`

## 来源与授权

- `laozhang.wav` = MOSS-TTSD v0.7 官方中文示例 `zh_spk1_moon.wav`（MOSS-TTSD 仓库 legacy/v0.7/examples/）
- `akai.wav` = MOSS-TTSD v0.7 官方中文示例 `zh_spk2_moon.wav`
- 用途：临时音色占位（验证 pipeline）。**重要**：MOSS-TTSD 跨语言克隆不稳定
  （英文参考音频克隆中文会生成静音），必须用中文参考音频。
- 正式发布前建议替换为自录的中文音色样本（各 5-10s 自然口语）。

<!-- 样本文件本身不入库（.gitignore 已排除 *.wav） -->

## MOSS-TTSD 用法

`voice_clone_and_continuation` 模式：
- 把每个说话人的 prompt 音频 + 对应文本前缀传给模型
- 模型以连续模式按各自身份生成后续对话
- 始终开 `--sample_rate_normalize` 和 `--text_normalize`

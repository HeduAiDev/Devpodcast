# MOSS-TTSD 中文长文本生成调研结论（2026-08-04）

## 结论：MOSS-TTSD 对中文长文本生成不稳定，弃用，切 CosyVoice3 fallback

## 已验证的事实

### 权重修复（已解决）
- HF 下载的 model-00001-of-00004.safetensors 被 aria2 中断残留污染（sha256 与 ModelScope 版不一致）
- 修复：ModelScope 重下替换（models/moss-ttsd/），其余 3 分片 sha256 一致
- 修复后官方 demo 从 2.7s 提前终止 → 45s 完整清晰音频

### 跨语言克隆（已解决）
- 英文参考音频 + 中文文本 → 生成静音（19 步就停）
- 中文参考音频 + 中文文本 → 正常生成（529 步, 51.8% 非静音, 40.9s）
- 必须用中文参考音频（voice-samples 已换 zh_spk1/zh_spk2_moon.wav）

### 长文本生成（未解决，核心问题）
| 文本 | 生成时长 | 备注 |
|---|---|---|
| 英文 889 字符 | 48.8s | 官方 demo，正常 |
| 中文 180 字 + 100 前缀 | 28.5s | 正常 |
| 中文 484 字 | **4.6s** | **严重退化** |
| 中文 180 字（batch=4） | 各几秒 | 60/65 段"有语音"但碎片化 |

**规律**：中文文本超过 ~200 字后，生成时长断崖式下降。MOSS-TTSD 的
"60 分钟长对话"能力在中文上不可复现（跨语言克隆 + 中文 token 密集）。

### 已验证无效的尝试
- max_new_tokens 512→8192：无改善
- temperature 0.7→1.1：无改善（结果完全一致）
- eager vs SDPA：无改善（速度有差，质量无差）
- chunk 180→800 字：更差（484 字只出 4.6s）
- torch.compile：RoPE 就地修改冲突，需 patch Qwen3 源码（放弃）
- 参考文本前缀：180 字从 13.4s→28.5s（有改善但不够）

## 有效的手段
- SDPA attention：22 tok/s（vs eager 10-15）
- batch=4：总吞吐 60 tok/s（2.8x），GPU 利用率显著提升
- 官方 processor.decode() 解码路径（非自校准）

## 下一步
- CosyVoice3（Fun-CosyVoice3-0.5B）fallback：逐句合成+拼接，天然支持任意长度
- SegmentedTTSProvider 已预留（scripts/tts.py），PAUSE_SPEAKER_SWITCH_MS=(350,500)

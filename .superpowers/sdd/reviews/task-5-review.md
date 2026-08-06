# Task 5 Review — tts.py（TTS 抽象层）

评审对象：commit `5508b0e`（`feat: TTS 抽象层（对话/分段两类 provider + 本地基类）`）
评审方式：brief 逐项核对 + diff 独立验证（含 git 提交身份实查、torch import 位置 grep 验证、测试文件与 brief 逐字 diff）

## 1. Spec compliance 判定：✅

| 必达物 | 状态 |
|---|---|
| `TTSOpts` dataclass（24000 / None / 0.6 / 50 / 0.9） | ✅ 逐项一致 |
| `VoiceSpec` dataclass（name / ref_audio: Path\|None） | ✅ |
| `AudioBundle` dataclass（wav_path / segments / duration_s / vram_gb） | ✅ |
| `TTSProvider(Protocol)` 三成员（native_dialogue / synthesize / list_voices） | ✅（+@runtime_checkable，见偏离裁决） |
| `LocalTTSProvider`（init / warmup / vram_report） | ✅（+list_voices stub，见偏离裁决） |
| `DialogueTTSProvider`：native_dialogue=True，synthesize 抛 NotImplementedError | ✅ |
| `SegmentedTTSProvider`：native_dialogue=False，PAUSE_SPEAKER_SWITCH_MS=(350,500) / PAUSE_SAME_SPEAKER_MS=(150,250) | ✅ |
| `load_provider` 按 "moss-ttsd"/"cosyvoice3" 分派，未知键抛 ValueError | ✅ |
| 顶层不 import torch（仅 vram_report 内局部 import） | ✅ 已 grep 验证：顶层仅 dataclasses/pathlib/typing；`import torch` 唯一出现在文件第 59 行 vram_report 方法体内，含 ImportError/CUDA 不可用两个错误分支 |
| TDD 纪律（先失败测试→确认失败→实现→确认通过） | ✅ 报告确认 Step 2 失败为 collection error（ModuleNotFoundError，新模块 TDD 的预期失败形态），Step 4 6/6 通过、全量 24/24 无回归 |
| 独立仓库零跨仓依赖 | ✅ 仅 import 标准库 |
| 提交身份 `git -c user.name="devpodcast" -c user.email="devpodcast@local"` | ✅ 已实查 `git log`：`5508b0e devpodcast <devpodcast@local>`；commit message 与 brief 一致；工作树除 `.superpowers/`（SDD 基础设施）外干净 |

缺项：无。多余项：无（两处附加均为偏离项，见下）。

## 2. 偏离裁决：接受

**偏离内容**：`TTSProvider` 加 `@runtime_checkable`；`LocalTTSProvider` 基类补 `list_voices()` stub（抛 NotImplementedError）。测试文件未改动（与 brief 逐字一致，已 diff 验证）。

**必要性 —— 成立**。独立验证逻辑：
- 普通 `Protocol`（无 `@runtime_checkable`）在 Python 3.8+ 一律不支持 `isinstance`，运行时抛 `TypeError: Instance and class checks can only be used with @runtime_checkable protocols`（PEP 544 语义）。brief 自带的 `test_implements_protocol` 照原文无法通过——这是 brief 的代码缺陷，非实现者引入。
- 两处修正**缺一不可**：只加 `@runtime_checkable` 还不够——runtime_checkable 的 isinstance 会做结构性成员检查，`list_voices` 在类层级未定义则 isinstance 返回 False（测试断言失败而非异常）。故补 stub 同样是必要修正。实现者对因果链的分析正确。
- stub 签名 `-> list[VoiceSpec]` 与 Protocol 一致，抛 NotImplementedError 与既有 `warmup()` stub 模式统一，Task 17 前无行为影响。
- 保留测试（"测试为契约"）改实现，优于删测试或改测试；与 Task 2 已裁决接受的偏离同因（brief 自带的 runtime-check 测试缺陷），有先例。
- 附加验证：runtime_checkable 对数据成员 `native_dialogue` 在 3.11 及以下不检查、3.12+ 检查存在性——两种情形下类属性均存在，无边界问题。

## 3. 代码质量判定：Approved

- **Critical: 0**
- **Important: 0**
- **Minor: 3**
  1. `vram_report` 硬编码 `get_device_properties(0)`/`mem_get_info(0)`，多卡时只报主卡——与 brief 参考代码一致，实现者已在报告 Concern 3 主动披露，Task 17 装真模型时可再处理。
  2. brief 自身接口行写 `synthesize(script: Script, voice_map: dict[str, VoiceSpec])` 而 Step 3 参考代码用裸 `script`/`dict`——实现按参考代码执行（正确取舍）；建议 Task 17 接真模型时收紧类型标注（此时 Script 已可用）。
  3. 基类 docstring 称管理 "GPU/batch/预热/显存"，但 batch 管理尚未实现（brief 参考代码同样没有）——轻微超前描述，Task 17 落地即可。

## 4. ⚠️ Cannot verify 清单

1. 测试执行结果（6/6 + 全量 24/24）——按评审方法未重跑，采信实现者报告。
2. 环境 Python 版本——runtime_checkable 数据成员检查行为随 3.11/3.12 有差异，但实现者实测通过已从经验层面排除问题；本次未重跑，无法独立复现。
3. `vram_report` 的 torch/CUDA 实测数值（报告声称 RTX PRO 6000 / 95.6 GB）——仅代码审查错误分支路径，未独立运行验证。

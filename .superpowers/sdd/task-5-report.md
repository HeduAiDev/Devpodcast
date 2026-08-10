# Task 5 Report — tts.py（TTS 抽象层）

状态：DONE_WITH_CONCERNS（1 处 brief 代码缺陷已修正，见 Concerns）

## 做了什么

按 brief Step 1–5 执行：

1. **Step 1** — 创建 `tests/test_tts_abstraction.py`（brief 完整代码，6 个测试，未改动）。
2. **Step 2** — 跑测试确认失败：`ModuleNotFoundError: No module named 'scripts.tts'`（collection error，符合预期）。
3. **Step 3** — 创建 `scripts/tts.py` 实现：
   - `TTSOpts`（sample_rate=24000 / max_new_tokens=None / temperature=0.6 / top_k=50 / top_p=0.9）
   - `VoiceSpec`（name / ref_audio: Path|None）
   - `AudioBundle`（wav_path / segments / duration_s / vram_gb）
   - `TTSProvider(Protocol)`（native_dialogue / synthesize / list_voices）
   - `LocalTTSProvider`（model_dir / device="cuda:0" / dtype="bfloat16"；warmup、vram_report、list_voices）
   - `DialogueTTSProvider`（native_dialogue=True；synthesize 抛 NotImplementedError，Task 17 接入 MOSS-TTSD）
   - `SegmentedTTSProvider`（native_dialogue=False；PAUSE_SPEAKER_SWITCH_MS=(350,500)、PAUSE_SAME_SPEAKER_MS=(150,250)；synthesize 抛 NotImplementedError，fallback 任务接入 CosyVoice3）
   - `load_provider(config)`（按 "moss-ttsd" / "cosyvoice3" 分派，未知键抛 ValueError）
   - 顶层不 import torch；torch 仅在 `vram_report` 方法内局部 import（Global Constraint 遵守）。
4. **Step 4** — 6 个测试全过；全量 24 个通过（18 个既有 + 6 个新增），无回归。
5. **Step 5** — 提交。

## 测试命令与输出

```bash
# Step 2（失败确认）
$ python3 -m pytest tests/test_tts_abstraction.py -v
> ERROR collecting ... ModuleNotFoundError: No module named 'scripts.tts'   # FAIL（预期）

# Step 4（通过确认）
$ python3 -m pytest tests/test_tts_abstraction.py -v
> 6 passed in 0.06s

# 全量回归
$ python3 -m pytest tests/ -v
> 24 passed in 0.67s
```

补充 sanity check（非测试）：
- `vram_report()` 在本机（torch 已装 + CUDA 可用）返回真实显存数据：`{'device': 'NVIDIA RTX PRO 6000 Blackwell Workstation Edition', 'total_gb': 95.6, 'used_gb': 2.5}`；无 torch 时返回 `{"error": "torch not installed"}`、无 CUDA 时返回 `{"error": "cuda not available"}`（代码路径按 brief 编写）。
- `load_provider({})` 抛 `ValueError: 未知 TTS provider: ''`。
- `warmup()` 抛 NotImplementedError。

## 提交

- Hash: `5508b0e`
- Message: `feat: TTS 抽象层（对话/分段两类 provider + 本地基类）`
- 变更：`scripts/tts.py`（新增）、`tests/test_tts_abstraction.py`（新增），2 files changed, 124 insertions(+)

## Concerns

1. **brief 代码缺陷（已修正，本任务唯一偏离）**：brief 的 `TTSProvider` 是普通 `Protocol`（未标 `@runtime_checkable`），`test_implements_protocol` 里 `isinstance(p, TTSProvider)` 在 Python 3.11 下抛 `TypeError: Instance and class checks can only be used with @runtime_checkable protocols`（5/6 过，1 失败）。修正两处：
   - 给 `TTSProvider` 加 `@runtime_checkable` 装饰器（引入 `runtime_checkable` import）。
   - 因 runtime_checkable 的 isinstance 会校验协议全部成员存在，而 `list_voices` 在类层级中未定义，故在 `LocalTTSProvider` 基类补了 `list_voices()` stub（抛 NotImplementedError，与既有 `warmup` stub 模式一致）。测试代码未改动。
   - 若 Task 6+ 或后续 review 认为该 Protocol 不应 runtime-checkable，也可改用 `issubclass` + `@runtime_checkable` 语义或移除该测试——但按 brief"测试为契约"原则保留测试、改实现是更稳的选择。

2. `Script` 类型未在本模块 import/引用（synthesize 签名用裸 `script` 参数）——与 brief 一致，无前置接口依赖；Task 17 装真模型时再接入具体类型。

3. `vram_report` 硬编码 `get_device_properties(0)` / `mem_get_info(0)`（主卡），多卡时只报第一张卡——与 brief 一致，暂不处理。

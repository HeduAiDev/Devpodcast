# Task 10 Report: audio_qa.py — 试听质检

Status: DONE_WITH_CONCERNS

Commit: `27a27d2` — "feat: audio_qa 试听质检（时长/削波/静音/响度）" (branch feat/m0-m1)

## What was done

Implemented `scripts/audio_qa.py` — standalone audio-quality gate (no imports from other `scripts.*` modules, no cross-repo deps):

- `AudioQAReport` dataclass: `duration_s / peak_db / clipping / silence_ratio / rms_db / issues / vram_gb`, with `__post_init__` defaulting `issues=None → []`.
- `analyze(path, expected_minutes=35.0)` — reads wav via `soundfile` (float32, downmixed if stereo), computes:
  - 时长超目标 20%（`MAX_DURATION_TOLERANCE=1.20`）→ `BLOCKING: 时长 …s 超目标 …s 的 20% 余量`
  - 峰值 > `CLIP_DB=-0.1`dB → `BLOCKING: 峰值 …dB 削波`
  - 静音占比（`SILENCE_THRESHOLD_DB=-45.0`）> 25% → `WARN: 静音占比 … > 25%`
  - RMS 响度 < `MIN_RMS_DB=-40.0`dB → `WARN: 响度 …dB 偏低`
- `write_report(report, path)` — 写 `audio-qa.json`（`asdict`，utf-8，ensure_ascii=False）。
- `main()` CLI（沿用 Task 7/8/9 约定）：`sys.path` 插仓库根；无参守卫打印 usage 到 stderr 返回 2；退出码 0=通过 / 1=有 BLOCKING / 2=用法错误；输出 `[BLOCKING] msg` / `[WARN] msg`；`<wav> [out.json 默认 <wav>.audio-qa.json] [expected_minutes 默认 35]`。

测试 `tests/test_audio_qa.py`：5 个测试用合成正弦波（`sf.write` float32 → PCM16），覆盖基本时长/峰值、削波检测（amp=2.0 被 libsndfile 写回时饱和到 ±1.0，peak_db=0.0 > -0.1 判削波）、静音占比、超时 BLOCKING、JSON 报告落盘。

环境依赖：本机缺 `soundfile`，已 `pip install soundfile`（0.14.0）装好。

## TDD sequence

1. 按 brief 写 tests/test_audio_qa.py（修正 2 处 brief 测试漏洞，见 Concerns）。
2. `python3 -m pytest tests/test_audio_qa.py -v` → FAIL（`ModuleNotFoundError: No module named 'scripts.audio_qa'`，符合预期）。
3. 写 scripts/audio_qa.py（brief 实现 + CLI 约定：usage/无参守卫/sys.path 插入）。
4. 首跑：4 passed / 1 failed — `test_write_report` 挂于 `TypeError: Object of type bool_ is not JSON serializable`（brief 实现漏洞，见 Concerns #2）。修复后 5 passed。
5. 全量回归 + CLI 冒烟后提交。

## Test commands and output

New tests:

```
$ python3 -m pytest tests/test_audio_qa.py -v
tests/test_audio_qa.py::test_basic_duration PASSED          [ 20%]
tests/test_audio_qa.py::test_clipping_detected PASSED       [ 40%]
tests/test_audio_qa.py::test_silence_ratio PASSED           [ 60%]
tests/test_audio_qa.py::test_over_duration_blocking PASSED  [ 80%]
tests/test_audio_qa.py::test_write_report PASSED            [100%]
============================== 5 passed in 0.25s ===============================
```

Full suite (no regression; 61 old + 5 new = 66):

```
$ python3 -m pytest tests/
============================== 66 passed in 1.14s ==============================
```

CLI smoke (not covered by pytest):

- 无参 → `usage: python3 scripts/audio_qa.py <wav> [out.json] [expected_minutes]`（stderr），rc=2
- 正常 wav（2s, 440Hz, amp 0.5）→ rc=0，`/tmp/qa_good.json` 全字段正确（`peak_db: -6.02, clipping: false, silence_ratio: 0.01, issues: []`）
- 削波 wav（amp 2.0）→ `[BLOCKING] BLOCKING: 峰值 0.0dB 削波`，rc=1

## Concerns

1. **Brief 测试漏洞 ①：`test_over_duration_blocking` 永远不过。** brief 版 `make_wav(seconds=50.0)` + `expected_minutes=35.0` → 50s < 2100×1.2=2520s，实现（同样照 brief）不会报「时长」issue，断言必挂。测试语义（超时 → BLOCKING）不变，修正为 `make_wav(seconds=90.0)` + `analyze(p, expected_minutes=1.0)`（90s > 60×1.2=72s），并更新注释。实现未动。
2. **Brief 测试漏洞 ②：`write_report` 未 import。** brief 测试只 `from scripts.audio_qa import analyze, AudioQAReport`，但 `test_write_report` 调用 `write_report` → NameError。import 行补上 `write_report`。
3. **Brief 实现漏洞 ③：`clipping` 是 `numpy.bool_`，json 不可序列化。** `r.clipping = r.peak_db > CLIP_DB` 在 numpy 下产生 `np.bool_`，`test_write_report` 的 `json.dumps` 抛 `TypeError`。修法：`r.clipping = bool(r.peak_db > CLIP_DB)`（dataclass 声明的类型就是 `bool`）。其余数值字段（`np.float64` 是 `float` 子类）可正常序列化。
4. **`main()` 无参守卫缺失（brief 实现缺陷）。** brief 的 `main` 直接 `argv[0]` → IndexError；按 Task 7/8/9 既定 CLI 约定补 USAGE + `if not argv: return 2`。
5. **`vram_gb` 恒为 0.0，analyze 不计算显存。** 任务标题含「显存」但 brief 的 `analyze` 未实现该检查，仅 dataclass 字段占位——M0 骨架阶段按 brief 照抄，留待后续任务（如需 GPU 推理期实测显存，可在 tts 阶段接）。
6. 环境中已装 `soundfile 0.14.0`（pip，root 用户，系统级），属本任务环境依赖。
7. `.superpowers/` 保持未跟踪（与之前任务一致，brief/report 不进提交）。

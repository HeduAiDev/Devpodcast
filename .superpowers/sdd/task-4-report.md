# Task 4 Report: script.md 解析器

**Status**: DONE（带 2 处 brief 代码修正，见 Concerns）

## 做了什么

按 brief Step 1–5 严格执行 TDD：

1. **Step 1**：创建 `tests/test_script_parser.py`（brief 原样代码，5 个测试：parse_basic / parse_pause / unclosed_tag_raises / bad_speaker_raises / to_dialogue_tags）。
2. **Step 2**：跑测试确认失败 —— `ModuleNotFoundError: No module named 'scripts.script_parser'`（红线确认）。
3. **Step 3**：创建 `scripts/script_parser.py`，实现 `Turn` / `Script` dataclass、`parse()`、`to_dialogue_tags()`、`ScriptParseError`，TURN_RE / VOICE_RE / BREAK_RE 按 brief。
4. **Step 4**：`python3 -m pytest tests/test_script_parser.py -v` → **5 passed**；全量 `python3 -m pytest tests/ -v` → **18 passed**（无回归）。
5. **Step 5**：提交 `8b4f161`。

## 测试命令与输出

```
$ python3 -m pytest tests/test_script_parser.py -v
collected 5 items
tests/test_script_parser.py::test_parse_basic PASSED                 [ 20%]
tests/test_script_parser.py::test_parse_pause PASSED                 [ 40%]
tests/test_script_parser.py::test_unclosed_tag_raises PASSED         [ 60%]
tests/test_script_parser.py::test_bad_speaker_raises PASSED          [ 80%]
tests/test_script_parser.py::test_to_dialogue_tags PASSED            [100%]
============================== 5 passed in 0.06s ===============================

$ python3 -m pytest tests/ -v
============================== 18 passed in 0.58s ==============================
```

## 提交

- Commit: `8b4f161`（feat/m0-m1）`feat: script.md 解析器（speaker 成对/停顿/voices 引用）`
- 变更：`scripts/script_parser.py`（新增）+ `tests/test_script_parser.py`（新增），2 files, 110 insertions

## Concerns（brief 代码修正记录）

审查 brief 代码发现 2 处正则边界漏洞，已修正（均不影响 brief 的 5 个测试，已单独验证）：

1. **多行 turn 误报 bug**：brief 的 `open_stray` 用 `re.findall(r"\[(S[12])\](?!.*?\[/\1\])", text)`（无 `re.S`），而 `TURN_RE` 带 `re.S` 支持多行 turn。多行闭合的 turn（`[S1] 第一行\n第二行 [/S1]`）会被 `open_stray` 误判为"未闭合"而抛 `ScriptParseError`。修正：给该 findall 加 `re.S`。
2. **错配闭合标签被吞入 turn 文本**：`[S2] 开场 [/S1] 收尾 [/S2]` 能骗过 `open_stray`（`[S2]` 后面确实存在 `[/S2]`），`[/S1]` 会被 TURN_RE 静默吞进 turn.text。修正：追加闭合标签计数校验（`len(re.findall(r"\[/(S[12])\]", text)) != len(turns)` → 抛错）。

两个场景均已用临时脚本验证：多行 turn 正常解析，错配闭合正确抛错。

未处理（brief 明确接受的简化）：`open_stray`/`bad` 为兜底校验，`TURN_RE` 是主要结构捕获器；嵌套/交叉的复杂畸形输入依赖 writer 契约保证，不进一步加固。

其他：`to_dialogue_tags` 是 staticmethod（brief 如此），实例调用合法；`.superpowers/` 目录未跟踪（沿用此前 Task 1-3 状态，未纳入提交）。

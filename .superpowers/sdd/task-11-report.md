# Task 11 Report: season_bible.py + archivist.py

状态: DONE_WITH_CONCERNS（2 项轻微偏离，见下）

## 做了什么

严格按 brief Step 1–5 TDD 执行：

1. **Step 1 — 失败测试**：`tests/test_season_bible.py`（3 个，brief 逐字）、`tests/test_archivist.py`（3 个：brief 逐字 1 个 + 补 2 个，见偏离#1）。
2. **Step 2 — 确认失败**：收集阶段 2 errors（`ModuleNotFoundError: No module named 'scripts.archivist'/'scripts.season_bible'`），符合预期 FAIL。
3. **Step 3 — 实现**：`scripts/season_bible.py`（`due`/`register` 数据层函数 + `due` CLI）、`scripts/archivist.py`（`log_entry`/`read_entries` 数据层函数 + `status`/`log` CLI）。数据层函数与 brief 代码逐字一致。
4. **Step 4 — 确认通过**：6 个新测试全过；全量 72 passed（66 存量 + 6 新增），无回归。
5. **Step 5 — 提交**：`6020b89`（4 个文件，135 insertions）。

## 测试命令与输出

```
$ python3 -m pytest tests/test_season_bible.py tests/test_archivist.py -v
tests/test_season_bible.py::test_due_empty_bible PASSED
tests/test_season_bible.py::test_due_returns_foreshadow_and_payoff PASSED
tests/test_season_bible.py::test_register_updates_episode PASSED
tests/test_archivist.py::test_log_and_read PASSED
tests/test_archivist.py::test_read_entries_missing_file_returns_empty PASSED
tests/test_archivist.py::test_log_appends_preserving_order PASSED
============================== 6 passed in 0.15s ==============================

$ python3 -m pytest tests/ -v
============================== 72 passed in 1.11s ==============================
```

## 手工 CLI 冒烟（测试未覆盖 CLI，故实测）

```
$ python3 scripts/season_bible.py due <arc-map.json> ep01
伏笔甲 / 伏笔乙
$ python3 scripts/archivist.py <trace> log "hello world" note
$ python3 scripts/archivist.py <trace> status
1 entries / [2026-08-01T14:43:10] (note) hello world
$ python3 scripts/season_bible.py（无参）→ usage 到 stderr，exit=2
$ python3 scripts/archivist.py log（无 msg）→ usage 到 stderr，exit=2
```

## 提交

- hash: `6020b89` — `feat: season_bible（伏笔 due/回收）+ archivist（trace）`
- 文件：`scripts/season_bible.py`、`scripts/archivist.py`、`tests/test_season_bible.py`、`tests/test_archivist.py`
- 分支：feat/m0-m1；user.name/email 按 Global Constraints 用 devpodcast@local

## Concerns / 偏离

1. **brief 的 archivist 测试段疑似截断**：brief 仅给出 `test_log_and_read` 1 个测试，但任务要求「各 3 个测试共 6 个」且全量应 72 通过（66 存量 + 6 新增恰好吻合）。已补 2 个覆盖 brief 实现其余核心语义的测试：`test_read_entries_missing_file_returns_empty`（缺文件 → `[]`）、`test_log_appends_preserving_order`（JSONL 追加保序）。补的测试只断言 brief 实现已支持的既有行为，未改实现。
2. **CLI 参数守卫（对 brief 的 `main()` 微改）**：brief 的 `main()` 无参/缺参会裸 IndexError traceback——本仓 Task 7 评审曾把「CLI 无参崩溃」定为 Important 并修复、Task 8 接受了「无参守卫」，故按项目先例给两个 `main()` 加了最小守卫（usage 到 stderr + return 2），并实测 exit=2。数据层函数（`due`/`register`/`log_entry`/`read_entries`）与 brief 逐字一致，测试目标不受影响。
3. **CLI 范围**：season_bible CLI 仅暴露 `due`（register 为数据层函数，main 不调用），与父任务指示及 brief 代码一致；spec 提到的 payoff/glossary 子命令不在本 brief 范围内。
4. **日期用法**：`log_entry` 中 `datetime.datetime.now().isoformat(timespec="seconds")` 是唯一日期用法；测试只断言 `"at"` 键存在，不比对具体时间值。
5. **progress.md 未更新**：`.superpowers/` 整体未纳入版本库（Task 1–10 同），台账由 lead 维护，本任务只写 report。
6. `import pytest` 在两个测试文件顶部（brief 逐字包含，Task 9 先例为「brief 原样行为」保留；此前评审仅记 minor）。

## 接口产物（供后续任务）

- `scripts/season_bible.py`：`due(arc_map: Path, ep_id: str) -> list[str]`（foreshadow_due + payoff_due 合并）、`register(arc_map: Path, ep_id: str, fields: dict) -> None`（读改写，ensure_ascii=False indent=2）、CLI `due <arc-map.json> <ep_id>`。
- `scripts/archivist.py`：`log_entry(trace_dir, msg, kind="note")`（mkdir + JSONL 追加 `{"at","kind","msg"}`）、`read_entries(trace_dir) -> list[dict]`（缺文件返回 `[]`，跳过空行）、CLI `status`/`log <msg> [kind]`。

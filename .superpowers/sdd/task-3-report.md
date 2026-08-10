# Task 3 报告：ingest_book.py — 快照摄入

**状态**: DONE
**提交**: `3204622` — `feat: ingest_book 快照摄入（digest 可校验，篡改即漂移）`
**分支**: feat/m0-m1

## 做了什么

按 brief Step 1–5 严格执行：

1. **Step 1 — 写失败测试**：创建 `tests/test_ingest.py`（brief 完整代码，逐字），3 个测试：
   - `test_ingest_writes_snapshot`：`ingest(src, tmp_path)` 后断言 `res["chapters"] == 2`、`source-book/book.json` 含 2 章、`chapter-cards/ch01.json`、`glossary.json`、`outline.json` 均落盘
   - `test_digest_changes_on_refresh`：篡改 glossary.json 后 `compute_digest` 必须变化
   - `test_ingest_idempotent`：重复 ingest digest 必须一致
2. **Step 2 — 确认失败**：`python3 -m pytest tests/test_ingest.py -v` → `ModuleNotFoundError: No module named 'scripts.ingest_book'`（预期失败）
3. **Step 3 — 实现**：创建 `scripts/ingest_book.py`（brief 完整代码，逐字）：
   - `ingest(source, show_dir) -> dict`：BookSource → `shows/<name>/source-book/{book.json, outline.json, glossary.json, chapter-cards/<chid>.json}`，返回 `{"digest", "chapters", "ingested_at": ""}`（日期由 workflow 填，纯函数避免时间依赖）
   - `compute_digest(show_dir) -> str`：对 source-book/ 全部文件 sha256，确定性排序（路径排序 + 路径字节 + 文件字节混入哈希）
   - `_stable_digest(blob)`：单文件 sha256 辅助
4. **Step 4 — 确认通过**：`python3 -m pytest tests/test_ingest.py -v` → 3 passed
5. **Step 5 — 提交**：`git add scripts/ingest_book.py tests/test_ingest.py && git -c user.name="devpodcast" -c user.email="devpodcast@local" commit -m "feat: ingest_book 快照摄入（digest 可校验，篡改即漂移）"`

## 测试命令与输出

```bash
$ python3 -m pytest tests/test_ingest.py -v
tests/test_ingest.py::test_ingest_writes_snapshot PASSED    [ 33%]
tests/test_ingest.py::test_digest_changes_on_refresh PASSED [ 66%]
tests/test_ingest.py::test_ingest_idempotent PASSED         [100%]
============================== 3 passed in 0.23s ===============================

$ python3 -m pytest tests/ -v   # 全量无回归
============================== 13 passed in 0.52s ===============================
```

## 文件

- 新增 `scripts/ingest_book.py`（69 行含测试合计 69 insertions，其中实现 35 行）
- 新增 `tests/test_ingest.py`（34 行）

## Concerns

- `ingested_at` 恒为空字符串，语义由调用方（workflow）填充——符合 brief 注释"日期由调用方在 workflow 里填"的设计，非疏漏。
- `compute_digest` 对 source-book/ 目录不存在时抛 `FileNotFoundError`（拉闸语义，与 Task 2 Repo2BookSource 的路径校验风格一致）。
- digest 混入相对路径字符串 + 文件字节，文件改名/增删均会漂移，篡改检测已由测试覆盖。
- 无进一步 concern；本任务不触及跨仓依赖，符合 Global Constraints。

# Task 3 评审：ingest_book.py — 快照摄入

**评审对象**: commit `3204622`（`feat: ingest_book 快照摄入（digest 可校验，篡改即漂移）`，devpodcast <devpodcast@local>）
**评审方式**: brief 必达物逐项核对 + diff 逐行比对（与 brief 提供代码 verbatim 比对）+ 接口/提交/测试现场只读核验；未运行测试。

## 1. Spec compliance：✅

| Brief 必达物 | 状态 |
|---|---|
| 创建 `scripts/ingest_book.py` | ✅ 36 行，与 brief Step 3 代码逐字一致（仅多一行 `# scripts/ingest_book.py` 注释头） |
| 创建 `tests/test_ingest.py` | ✅ 33 行，与 brief Step 1 代码逐字一致（3 个测试齐全） |
| `ingest(source: BookSource, show_dir: Path) -> dict`，返回 `{"digest", "chapters", "ingested_at"}` | ✅ 返回键齐全；`ingested_at=""` 按 brief 注释由调用方填 |
| `compute_digest(show_dir: Path) -> str`：sha256、确定性排序 | ✅ `sorted(sb.rglob("*"))` + 相对路径字节 + 文件字节混入 |
| 落盘结构 `source-book/{book.json, outline.json, glossary.json, chapter-cards/<chid>.json}` | ✅ `book.as_dict()`、`source.outline()`、`source.glossary()`、`card.chapter_id`/`card.as_dict()`，与 Task 2 实际接口（`book_source.py` Protocol/数据类）逐一核对吻合 |
| TDD 纪律（先失败后通过） | ✅ 报告确认 Step 2 失败（ModuleNotFoundError）、Step 4 通过（3 passed） |
| 提交约束（身份、消息） | ✅ 已用 `git log` 现场核验：`devpodcast <devpodcast@local>`，消息与 brief 一致 |
| 零跨仓依赖 | ✅ 仅 stdlib（hashlib/json/pathlib）+ `scripts.book_source`，import 核验无误 |
| 无多余产物 | ✅ stat 精确 2 文件 69 insertions，无附带改动 |

缺项：无。多余项：无（`_stable_digest` 为 brief 自带，非实现者追加）。

## 2. 代码质量判定：Approved

digest 正确性（确定性 ✅、篡改检测 ✅ 均有测试覆盖）、快照结构 ✅、错误处理 ✅（缺快照目录抛 `FileNotFoundError`，拉闸语义）。

Minor（均不阻塞，其中前两条为 brief 自带设计，非实现者偏差）：
1. **digest 流无分隔符**：路径与文件内容、文件条目之间无分隔字节。理论上不同文件集可产出相同拼接流（如树 A 仅文件 `a` 内容 `bc` 与树 B 仅文件 `ab` 内容 `c` 均产出 `abc`）。本项目文件集由 ingest 固定写死（book/outline/glossary/chapter-cards/*.json），该碰撞不可达，纯理论。
2. **`_stable_digest` 死代码**：定义后无调用点（`compute_digest` 内联实现）。brief 自带，不影响行为。
3. **不清理陈旧文件**：ingest 只写不删。源中移除章节时旧 card 文件残留并继续计入 digest。brief 未要求，当前 fixture 稳定使 idempotent 测试成立。
4. 缺快照目录抛错路径无测试覆盖（brief 未要求该测试），仅代码阅读核验。

## 3. ⚠️ Cannot verify

- **测试执行结果**：按评审指示未运行 pytest。报告称 `tests/test_ingest.py` 3 passed、全量 13 passed。佐证充分（提交存在、接口吻合、fixture 树含 ch01/ch02 构件、测试与 brief 逐字），但通过与否本身未独立复现。
- **fixture 内容语义**：`repo2book-mini` 下 chapter-cards 产出 `ch01.json`/`ch02.json`、`len(book["chapters"]) == 2` 依赖 fixture 实际 JSON 内容，未逐文件读取核实（仅确认目录结构存在）。
- **全量 13 passed 的无回归声明**：Task 2/4 侧测试未独立复核。
- **`ingested_at` 空串的消费方约定**：由未来 workflow 任务填充，本任务内无消费方可验证。

## 结论

Spec ✅；Quality Approved；Critical 0 / Important 0 / Minor 4。可合入。

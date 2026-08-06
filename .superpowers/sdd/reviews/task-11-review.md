# Task 11 Review: season_bible.py + archivist.py

**评审对象**: commit `6020b89`（4 文件，135 insertions，作者 `devpodcast <devpodcast@local>`）
**评审方法**: 读 brief 列必达物 → 逐行核对 diff → 独立复跑测试/CLI/边界用例 → 查证先例 → 逐项裁决 2 处偏离

## 1. Spec compliance 判定：✅

| 必达物 | 判定 | 证据 |
|---|---|---|
| `scripts/season_bible.py` 数据层 | ✅ | `due`/`register` 与 brief 逐字一致（diff 逐行核对无偏差） |
| `scripts/archivist.py` 数据层 | ✅ | `log_entry`/`read_entries` 与 brief 逐字一致 |
| `due(arc_map, ep_id) -> list[str]` | ✅ | foreshadow_due + payoff_due 顺序拼接；独立边界验证：`["a"]+["b","c"] → ["a","b","c"]`，空 bible → `[]` |
| `register(arc_map, ep_id, fields)` | ✅ | 嵌套 setdefault（episodes→ep_id）创建缺失路径；独立验证保兄弟 episode、保顶层键、`ensure_ascii=False indent=2` 写回可往返 |
| `log_entry(trace_dir, msg, kind)` | ✅ | mkdir(parents, exist_ok) + `{"at": isoformat(timespec="seconds"), "kind", "msg"}` + append 模式 + `\n`；与 brief 逐字一致 |
| `read_entries(trace_dir) -> list[dict]` | ✅ | 缺文件 → `[]`；跳空行；保序（独立验证 3 条顺序往返） |
| CLI `due` / `status` / `log` | ✅ | 冒烟实测：log→status 输出 `[ts] (kind) msg`、`N entries`；status 打印末 10 条 |
| CLI 无参守卫 usage+rc2 | ✅ | 实测：两脚本无参 → usage 到 stderr + rc=2；`archivist log` 缺 msg → usage + rc=2；无 traceback |
| Global Constraints：TDD 红→绿 | ✅（红阶段见 ⚠️） | 绿阶段独立复跑：6 新增 passed；全量 72 passed（66 存量实测 + 6 新增，吻合） |
| Global Constraints：commit 身份 | ✅ | `git show 6020b89`：`devpodcast <devpodcast@local>`，单 commit，消息与 brief 一致 |
| Global Constraints：零跨仓依赖 | ✅ | 两脚本仅 import stdlib（json/sys/pathlib/datetime）；测试仅 import scripts + json + pytest |
| 工作树/提交完整性 | ✅ | `git status` 干净（`.superpowers/` 未入库系项目约定）；提交恰含 4 文件 |

**缺项**：无。
**多余项**：2 个补测 + 2 处 CLI 守卫（均裁决接受，见 §2）。

## 2. 偏离裁决

### 偏离 #1：archivist 测试补 2 个（缺文件返回 []、JSONL 追加保序）— 接受

- **事实核验**：brief 与 master plan（`docs/superpowers/plans/2026-08-01-devpodcast-m0-m1.md` Task 11 段，逐字同源）的 archivist 测试段确实只有 `test_log_and_read` 1 个测试；报告如实披露。
- **实质判断**：补的 2 个测试只断言 brief 实现逐字已支持的行为（`if not p.is_file(): return []`、append+读回保序），未改动实现、未给实现加约束；断言真实（非套套逻辑）；TDD 上同样先红后绿（实现前 import 即 collection error）。净效果是 `read_entries` 两个核心语义有了回归保护，属良性增补。
- **依据存疑部分**：「任务要求各 3 个测试共 6 个 / 全量应 72」在仓库内无外部来源（brief/plan 均未声明测试总数，「66+6=72」为自我实现式推断）→ 该理由列入 ⚠️，不影响裁决本身。

### 偏离 #2：两处 main() 无参守卫（usage 到 stderr + return 2）— 接受

- **先例查证**：Task 7 首评将「CLI 无参 IndexError 裸崩」定为 Important（`task-7-review.md:38`）；Task 7 rereview 确认修复为「无参 → USAGE stderr + 2」；Task 8 评审明确接受「main() 无参守卫返回 2」（`task-8-review.md:26`）；Task 9 评审将无参守卫归为 Global Constraints 要求（`task-9-review.md:24`）。本任务评审指令亦列「无参守卫 usage+rc2」为 CLI 先例。
- **独立实测**：两脚本无参、`log` 缺 msg 均 usage + rc=2，无 traceback；合法路径（due/status/log）不受影响。守卫最小化，数据层函数与 brief 逐字一致。
- **结论**：与项目既定模式一致的正确补齐，接受。

## 3. 代码质量判定：Approved（0 Critical / 0 Important）

### Minor（6 项，均不阻断）

1. **未知子命令静默 rc=0**：`season_bible.py foo x y`、`archivist.py <dir> foo` 未命中已知命令时静默返回 0（brief 原样继承）。后续 workflow 集成误调将无提示；建议后续 CLI 任务统一「unknown cmd → usage + rc=2」。
2. **时间戳为 naive 本地时间**（`isoformat` 无 tzinfo）：M0 单机单写者可接受，brief 指定格式逐字；跨时区/多机时需统一 UTC。记录为已知限制。
3. **read_entries 遇损坏行直接抛异常**（`json.loads` 无 per-line try/except）：append 单写者通常不产生半写行，接受；如需自愈可后续加固。
4. **due() 字段值为非 list（如 null）时 `list(None)` 抛 TypeError**：brief 逐字行为，接受（arc-map 为内部受控产物）。
5. **两测试文件 `import pytest` 未使用**（tmp_path 为注入 fixture）：与 Task 7/8/9 既有 minor 记录一致，按项目约定保留。
6. **测试依赖 `python3 -m pytest` 从仓库根运行**（无 conftest.py/pytest.ini，靠 `-m` 将 cwd 入 sys.path）：从仓库外运行收集失败——与全部既有任务同机制，系项目约定，非本任务回归。

### 已核验的健壮性点（非问题，评审指令要求显式确认）

- **JSONL 追加无需文件锁**：M0 单写者 + append 模式 + 单进程，无并发写竞争；`mkdir(exist_ok=True)` 幂等。✅
- **register 写回全文件重格式化**（indent=2）：brief 指定行为，兄弟键/顶层键均保留。✅
- **CLI 一致性**：两脚本守卫模式、错误输出通道（stderr）、返回码语义（2=用法错误 / 0=正常）与 Task 7/8/9 门禁逐点一致。✅
- **数据层零偏离**：diff 逐行核对，`due`/`register`/`log_entry`/`read_entries` 与 brief 代码无一行差异。✅

## 4. ⚠️ Cannot verify（2 项）

1. **偏离 #1 的「brief 截断」理由**：brief 与 master plan 均未声明「各 3 个测试共 6 个 / 全量 72 通过」，该推断无仓库内依据可证实（66 存量已独立实测属实；72 无外部基准，为自我实现）。补测本身已独立接受，仅理由存疑。
2. **Step 2 红阶段可回放性**：报告记载收集期 2 errors（ModuleNotFoundError），红→绿过程符合 TDD 叙述且绿阶段已实测复验，但红阶段原始输出无法独立回放。

## 结论

Spec ✅（无缺项，多余项均裁决接受）；偏离 2/2 接受；Quality Approved（Minor 6 项，无 Critical/Important）。

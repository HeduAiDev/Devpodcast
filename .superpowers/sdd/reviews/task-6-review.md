# Task 6 Review — voice_budget.py（时长/节奏预算）

评审方式：brief 必达物 → 实际 diff 逐项核对 → 独立复算偏离用例 → 运行测试与 git 验证。

## 1. Spec compliance 判定：✅

| 必达物 | 状态 | 核对依据 |
|---|---|---|
| `scripts/voice_budget.py`（26 行） | ✅ | 与 brief Step 3 代码逐字一致（实现代码，非测试） |
| `estimate_duration(text, cps=4.0) -> float`（len/cps，秒） | ✅ | 逐字 |
| `estimate_script_duration(script) -> float`（各 turn 求和） | ✅ | 逐字 |
| `budget_check(script, target_minutes) -> list[str]` | ✅ | 逐字；BLOCKING 阈值 `total_s > target_s * TOLERANCE`（>15% 严格大于） |
| 常量 DEFAULT_CPS=4.0 / MAX_TURN_CHARS=200 / TOLERANCE=1.15 | ✅ | 逐字 |
| BLOCKING 消息格式（lint_script 复用契约） | ✅ | `"BLOCKING: 预计 {total_s:.0f}s 超过目标 {target_s:.0f}s 的 {TOLERANCE:.0%} 余量"`，与 global constraint 的 `"BLOCKING: 预计 Xs 超过目标 Ys"` 一致（含 brief 规定的余量后缀） |
| WARN 消息（单 turn > 200 字） | ✅ | `"WARN: turn {i} ({speaker}) 长 {len} 字，超过 {MAX_TURN_CHARS} 字换气上限"`，逐字 |
| `tests/test_voice_budget.py`（6 个测试） | ✅ | 5 个逐字；1 个（test_budget_check_ok）有意修正，见第 2 节裁决 |
| TDD 纪律（Step 2 先失败） | ✅* | 报告记载 collection error（ModuleNotFoundError）为 RED，符合新模块的预期失败形态；见 ⚠️1 |
| 提交命令（git -c user.name="devpodcast" -c user.email="devpodcast@local"） | ✅ | 实测 `git log -1`：Author: devpodcast <devpodcast@local>；提交 f04990e 存在，stat 与 review pkg 一致（2 文件 +61 行） |
| 回归无破坏 | ✅ | 实测全量 `python3 -m pytest tests/`：30 passed（24 既有 + 6 新增），无失败 |

缺项：无。多余项：无。

## 2. 偏离裁决：接受

**偏离内容**：`test_budget_check_ok` 的 turn 字数由 brief 原文 400 改为 100，并加注释说明。

**独立验证（复算）**：brief 原用例（400 字，target=2.0min）：
- 预算：400/4.0 = 100s ≤ 120×1.15 = 138s → 无 BLOCKING ✓
- 单 turn：400 > 200 → **必然产生 WARN** ✗
- 断言 `budget_check(...) == []` 与实现行为（以及同文件 `test_budget_check_long_turn` 依赖的 >200 字报 WARN 行为）不可同时成立。

结论：brief 自身数据矛盾属实，400 字系其他用例复制笔误，偏离**必要**。

**修正质量**：改为 100 字后：100 ≤ 200 无 WARN；100/4.0 = 25s ≤ 138s 无 BLOCKING → `== []` 成立。该用例的本意语义（"预算内脚本无任何 issue"）完整保留；100 字远离 200 边界（不因 `>`/`>=` 实现细节而脆断），比 200 字边界值更稳健。注释说明了缘由。实现文件按 brief 逐字未动，换气上限语义未受损。

## 3. 代码质量判定：Approved

全部为 Minor 级观察，无 Critical / Important。多数系 brief 原文逐字所致，非实现者引入。

- **Minor-1**：`from scripts.script_parser import Script, Turn` 中 `Turn` 未被使用（模块内仅有 `Script` 出现在注解）。brief 逐字引入，无功能影响。
- **Minor-2**：`estimate_duration` 对 `cps=0` 无防御（ZeroDivisionError）。brief 未要求校验，契约上 cps 恒为正值。
- **Minor-3**：边界语义 `>`（恰 200 字、恰 1.15 倍不报）无测试覆盖。brief 未含边界用例。
- **Minor-4**（前瞻观察）：`Turn.pause_ms`（Task 4 数据模型已有）未计入 `estimate_script_duration`，时长仅按口播字数估算；与 brief 公式一致，属计划层设计选择，非本任务缺陷。后续任务若需含停顿时长需在此扩展。

**质量亮点**：预算公式（len/cps）正确；消息模板用 `:.0f`/`:0%` 格式化与 Task 7 复用契约一致；`DEFAULT_CPS` 常量复用优于字面量；报告对偏离的记载（位置、理由、替代方案排除）完整可审计。

## 4. ⚠️ Cannot verify

1. **测试先行顺序**：测试与实现同落于单一提交 f04990e，仓库无法独立证实"先写测试、见红、后写实现"的时序；仅能采信报告记载的 Step 2 collection error。RED 形态合理，无反常迹象。
2. **lint_script 实际消费行为**：Task 7 未实现，无法端到端验证复用。静态核对 task-7 brief：以 `issues.extend(budget_check(script, target_minutes))` 复用且其测试无任何预算消息格式断言，契约兼容。旁注（Task 7 侧问题，非本任务）：Task 7 CLI 对 budget_check 字符串会输出 `[BLOCKING] BLOCKING: ...` 双重前缀，属 Task 7 实现时需处理的事项。

## 评审结论

- Spec verdict：✅ 通过（无缺项/多余项；唯一差异为已裁决的必要修正）
- 偏离裁决：接受
- Quality verdict：Approved（4 项 Minor，无 Critical/Important）

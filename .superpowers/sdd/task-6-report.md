# Task 6 Report — voice_budget.py（时长/节奏预算）

状态：DONE_WITH_CONCERNS（1 处 brief 测试数据笔误已修正，见 Concerns）

## 做了什么

按 brief Step 1–5 执行：

1. **Step 1** — 创建 `tests/test_voice_budget.py`（brief 完整代码，6 个测试，唯一改动见 Concerns）。
2. **Step 2** — 跑测试确认失败：`ModuleNotFoundError: No module named 'scripts.voice_budget'`（collection error，符合预期）。
3. **Step 3** — 创建 `scripts/voice_budget.py` 实现（按 brief 逐字，未改动）：
   - `DEFAULT_CPS = 4.0`（中文默认 4 字/秒 = 240 字/分钟）
   - `MAX_TURN_CHARS = 200`（单 turn 换气上限）
   - `TOLERANCE = 1.15`（目标时长 15% 余量）
   - `estimate_duration(text, cps=DEFAULT_CPS) -> float`（len/cps，返回秒）
   - `estimate_script_duration(script: Script) -> float`（各 turn 时长求和）
   - `budget_check(script: Script, target_minutes: float) -> list[str]`
     - 超 15% 余量 → `"BLOCKING: 预计 {total_s:.0f}s 超过目标 {target_s:.0f}s 的 {TOLERANCE:.0%} 余量"`（逐字，Task 7 lint_script 复用）
     - 单 turn > 200 字 → `"WARN: turn {i} ({speaker}) 长 {len} 字，超过 {MAX_TURN_CHARS} 字换气上限"`
4. **Step 4** — 6 个测试全过；全量 30 个通过（24 个既有 + 6 个新增），无回归。
5. **Step 5** — 提交。

## 测试命令与输出

```bash
# Step 2（失败确认）
$ python3 -m pytest tests/test_voice_budget.py -v
> ERROR collecting ... ModuleNotFoundError: No module named 'scripts.voice_budget'   # FAIL（预期）

# Step 4（通过确认）
$ python3 -m pytest tests/test_voice_budget.py -v
> 6 passed in 0.08s

# 全量回归
$ python3 -m pytest tests/ -v
> 30 passed in 0.75s
```

## 提交

- `f04990e` feat: voice_budget 时长/换气预算（`git -c user.name="devpodcast" -c user.email="devpodcast@local" commit`）

## Concerns

1. **brief 测试数据自相矛盾（已修正）**：brief 的 `test_budget_check_ok` 用 400 字 turn 却断言 `budget_check == []`，而 brief 实现本身对 >200 字 turn 报 WARN（`test_budget_check_long_turn` 也依赖此行为），二者不可同时成立。400 字明显是其他用例的复制笔误。修正：该用例 turn 改为 100 字（25s < 2min×1.15，且 ≤200 字，无任何 issue），并在测试内注释说明。实现按 brief 逐字未动；200 字换气上限语义保持。
2. **全量测试数为 30 而非父任务预期的 29**：Task 5 report 记载基线即为 24 个（18 既有 + 6 新增），加本任务 6 个 = 30；"29" 为估算误差，非回归（无既有测试失败）。

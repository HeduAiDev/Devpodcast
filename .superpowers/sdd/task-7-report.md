# Task 7 Report — lint_script.py 脚本门禁

**状态**: DONE_WITH_CONCERNS
**提交**: `dac6a7d` — `feat: lint_script 门禁（voices 引用/声线平衡/我不知道/预算）`
**分支**: feat/m0-m1

## 做了什么

### Step 1: 写失败测试
- 新建 `tests/test_lint_script.py`，brief 提供的 5 个测试逐字落地：
  - `test_voice_refs_must_exist`（未知 voice 引用 → BLOCKING）
  - `test_voice_refs_valid_ok`（合法引用无误报）
  - `test_unknown_word_warn`（无「我不知道」类表述 → WARN）
  - `test_unknown_word_present_no_warn`（有「没搞清楚」不报）
  - `test_bald_broadcast_warn`（S2 占 1/4=25% < 30% → WARN）

### Step 2: 确认失败
`python3 -m pytest tests/test_lint_script.py -v` → collection error：
`ModuleNotFoundError: No module named 'scripts.lint_script'`（预期，实现不存在）。

### Step 3: 写实现
新建 `scripts/lint_script.py`（brief 代码 + 两处修正，见 concerns）：
- `lint_script(path, voices, target_minutes) -> list[dict]`：4 项检查
  1. `{{voice:<id>}}` 引用存在性 → BLOCKING
  2. 双声线平衡（任意说话人 turn 占比 < 30% → WARN，防捧哏）
  3. 「我不知道/没搞清/没想明白/说不准」至少一次 → WARN
  4. `budget_check` 结果合并
- `main(argv)` CLI：`python3 scripts/lint_script.py <path> [--voices v.json] [--target-minutes N]`，退出码 0=通过 / 1=有 BLOCKING

### Step 4: 确认通过
```
python3 -m pytest tests/test_lint_script.py -v   → 5 passed
python3 -m pytest tests/ -v                      → 35 passed（全量，无回归）
```

### Step 5: 提交
`git -c user.name="devpodcast" -c user.email="devpodcast@local" commit` → `dac6a7d`

### 额外验证（CLI 冒烟）
```
$ python3 scripts/lint_script.py smoke.md --target-minutes 0.01; echo exit=$?
[BLOCKING] turn 2 引用未知 voice id: voice-999
[WARN] 全脚本无「我不知道/没搞清」类表述——voice-guide 纪律 1 要求每期至少一次
exit=1
$ python3 scripts/lint_script.py smoke.md --target-minutes 5; echo exit=$?
exit=0（smoke 脚本只有 BLOCKING 与 WARN 分开验证）
```
- 从仓库根目录和任意 cwd 运行均正常，退出码符合规格（1=有 BLOCKING）。
- 预算数据抽查：总文本 2 字 ≈ 0.5s < 0.01min×60×1.15=0.69s，未误报 BLOCKING，逻辑正确。

## 修正记录（brief 之外的漏洞，已按指示自修）

1. **Lead 裁决**（类型修复，按要求执行）：`issues.extend(budget_check(...))` 的 `list[str]` vs `list[dict]` 不兼容。已改为把每条带前缀字符串转成 `{"level", "msg"}` dict：
   ```python
   for s in budget_check(script, target_minutes):
       if s.startswith("BLOCKING"):
           issues.append({"level": "BLOCKING", "msg": s[len("BLOCKING: "):]})
       else:
           issues.append({"level": "WARN", "msg": s[len("WARN: "):] if s.startswith("WARN") else s})
   ```

2. **CLI 无法运行的 bug**（新发现）：`python3 scripts/lint_script.py <path>` 直接崩溃
   `ModuleNotFoundError: No module named 'scripts'` —— 以脚本方式运行时 `sys.path[0]` 是
   `scripts/` 目录而非仓库根，`from scripts.script_parser import ...` 解析失败。这是全仓第一个
   带 CLI 入口的脚本，无既有约定可循；brief 规格明确要求该命令可用（退出码 0/1）。
   修复：import 前插入仓库根到 sys.path：
   ```python
   sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
   ```
   测试不受影响（pytest 从仓库根 import，路径幂等）。若后续任务（如 Task 8 lint_voices）
   也要 CLI，建议共用此模式或改用 `python3 -m scripts.lint_script`。

## Concerns

- **未使用 import**：brief 原样保留 `from scripts.voice_budget import budget_check, MAX_TURN_CHARS`，
  但 `MAX_TURN_CHARS` 在实现中未使用（lint 本身只消费 budget_check 的返回，无直接引用）。
  为逐字贴合 brief 未删；后续如有 flake8/lint 任务会报 F401，可届时一并清理。
- **CLI 直接依赖仓库根布局**：`sys.path` hack 让脚本可在任意 cwd 运行，但本质依赖 scripts/
  与仓库根的相对结构；M1 阶段如果脚本被复制/打包运行会失效。M0 骨架阶段可接受。
- brief 检查项 2 与 3 均为 WARN 级，测试对"无未知引用/有我不知道表述"场景只断言了
  `not any(...)` 关键词缺席，未断言 issues 为空（其他 WARN 可能仍在），符合 brief 语义，未改。

---

## FIX ROUND 1（评审修复）

**状态**: DONE
**提交**: `aa5ae8f` — `fix: lint_script CLI 参数守卫 + budget 转换路径测试覆盖`
**评审依据**: `.superpowers/sdd/reviews/task-7-review.md`（Important 2 / Minor 4，无 Critical）

### Important ① 修复：budget dict 转换路径补回归测试（+2）
`tests/test_lint_script.py` 新增 2 用例，直接覆盖 Lead 裁决的前缀剥离/级别归类路径：
- `test_budget_overrun_blocking_strips_prefix`：`[S1]` 60 字 turn（≈15s）vs `target_minutes=0.1`（6s×1.15=6.9s 余量）→ BLOCKING；断言 msg 含「预计」且不以 `"BLOCKING: "` 开头（前缀剥离）。60 < 200 不掺入换气 WARN，用例聚焦。
- `test_long_turn_warn_strips_prefix`：`[S1]` 250 字 turn（> 200 字换气上限）vs `target_minutes=35`（总时长 62.5s 远低于余量）→ WARN；断言 msg 含「长 250 字」且不以 `"WARN: "` 开头，并断言无 BLOCKING 混入。

### Important ② 修复：CLI 参数守卫（main() 前置防御）
`scripts/lint_script.py` `main()` 现对三类误调用均打印到 stderr 并返回 2（无 traceback）：
- 无 argv → 打印 `USAGE`（`usage: python3 scripts/lint_script.py <path> [--voices <json>] [--target-minutes N]`），返回 2；
- `--voices` / `--target-minutes` 缺值（后无参数或下一参数以 `--` 开头，即被另一选项占位）→ 打印 `USAGE`，返回 2；
- `--target-minutes` 非法数值（`float()` 抛 ValueError）→ 打印 `error: --target-minutes 需要合法数值，得到 '<值>'`，返回 2。

CLI 行为测试（直接调 `main(argv)`，无 subprocess）：无参 → 2、缺 voices 值 → 2、缺 target 值 → 2、非法 target → 2（stderr 含该值）、合法干净脚本 → 0、未知 voice 引用 → 1。原 0/1 语义不变。

### Minor 顺带修复
- 删未用 import：`re`（lint_script.py）、`MAX_TURN_CHARS`（lint_script.py）；tests 内 `json` 现被 CLI 测试 `json.dumps(VOICES)` 实际使用，不再未用。
- 未改：前缀判定宽于实际（当前源码仅产出两种格式，无现存 bug）；`test_unknown_word_present_no_warn` 间接断言（brief 自带）。

### 验证输出
```
$ python3 -m pytest tests/test_lint_script.py -v
13 passed（原 5 + 新 8）

$ python3 -m pytest tests/ -v
43 passed in 0.94s（原 35 + 新 8，无回归）

CLI 冒烟：
$ python3 scripts/lint_script.py; echo $? → usage 打印到 stderr，exit=2
$ python3 scripts/lint_script.py /tmp/nope.md --voices; echo $? → usage，exit=2
$ python3 scripts/lint_script.py /tmp/nope.md --target-minutes abc → error 信息，exit=2
```

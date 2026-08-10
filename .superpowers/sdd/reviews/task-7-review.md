# Task 7 Review — lint_script.py 脚本门禁

**评审对象**: commit `dac6a7d`（feat: lint_script 门禁）| 分支 feat/m0-m1
**评审方式**: brief 必达物逐项核对 + 独立运行验证（pytest / CLI 冒烟 / 边界注入 / 无修复版模拟）

## 1. Spec compliance 判定：✅

| 必达物 | 状态 |
|---|---|
| `lint_script(path, voices, target_minutes) -> list[dict]`，每项 `{"level": "BLOCKING"\|"WARN", "msg": str}` | ✅ 签名与结构逐字一致 |
| 检查① `{{voice:<id>}}` 引用存在性 → BLOCKING | ✅ 独立复验（含 `--voices` JSON 端到端：合法引用 exit=0，未知引用 BLOCKING exit=1） |
| 检查② 任意说话人 turn < 30% → WARN | ✅ 25% 场景独立复验；0 turn 有 `if script.turns:` 守卫，无除零 |
| 检查③ 无「我不知道/没搞清/没想明白/说不准」→ WARN | ✅ 子串匹配含"没搞清楚"→命中"没搞清"，语境误报防护正确 |
| 检查④ budget_check 合并（Lead 裁决版） | ✅ 真实超预算场景输出 `[BLOCKING] 预计 25s 超过目标 1s 的 115% 余量`，前缀剥离干净 |
| CLI `python3 scripts/lint_script.py <path> [--voices <json>] [--target-minutes N]`，退出码 0/1 | ✅ 从仓库根与任意 cwd（/tmp）均运行正常；仅 WARN → 0，含 BLOCKING → 1 |
| 测试 `tests/test_lint_script.py` 5 个用例逐字落地 | ✅ 独立复验 5 passed |
| 提交约束 | ✅ 作者 `devpodcast <devpodcast@local>`；仅含规格内 2 文件；零跨仓依赖；`re`/`MAX_TURN_CHARS`/测试内 `json` 为 brief 自带未用 import（无多余项） |

无缺项，无规格外多余文件（sys.path 修复为必要偏离，见 §3）。

## 2. Lead 裁决执行核验：已正确执行

- `budget_check` 现返回 `list[str]`（前缀 "BLOCKING: "/"WARN: "，与 Task 6 voice_budget.py 实际源码一致）；
- lint_script 已改为逐条转 `{"level", "msg"}` dict 再并入 issues：`startswith("BLOCKING")` → BLOCKING + `s[len("BLOCKING: "):]`（10 字符精确剥离）；否则 WARN + `s[len("WARN: "):]`（6 字符精确剥离）。
- 独立复验：CLI 打印 `i['level']` 无 TypeError，与转换前会崩的裁决前提吻合。

## 3. sys.path 偏离裁决：接受

- **必要性（已证明）**：在 /tmp 模拟删除 sys.path 插入的版本，`python3 scripts/lint_script.py <path>` 即 `ModuleNotFoundError: No module named 'scripts'`（`sys.path[0]`=scripts/）。brief 规格要求该命令可用，修复必要。
- **无副作用（已验证）**：`python3 -m pytest tests/` 全量 35 passed；pytest 场景下仓库根本已在 sys.path，插入幂等。
- 残留风险（实现者已披露）：顶层 `sys.path.insert(0, ...)` 若仓库根未来出现与 stdlib 同名模块会遮蔽——M0 可接受；建议 Task 8 lint_voices CLI 沿用此模式或改用 `python3 -m scripts.lint_script`。

## 4. 代码质量判定：Issues

### Important

1. **Lead 裁决的 dict 转换路径零自动化测试**：brief 的 5 个测试脚本文本均极短且 `target_minutes=5`，budget_check 永不产出任何 issue——被裁决修复的代码（前缀剥离/级别归类）只有人工冒烟覆盖，无回归测试。TDD 纪律在裁决项上未闭环。建议补一个超长文本触发 BLOCKING 与 200 字 turn 触发 WARN 的用例。
2. **CLI 参数解析健壮性缺口（报告未披露）**：独立验证 `python3 scripts/lint_script.py`（无参）→ IndexError traceback；`--voices`/`--target-minutes` 缺值 → IndexError；非法数值 → ValueError traceback。门禁类工具在 CI 场景极易被错误调用，无 usage 提示且崩溃输出不友好。退出码虽仍非 0，但属未设计行为。建议 `main()` 对 argv 长度与选项值做防御并在 `__main__` 捕获。

### Minor

- `startswith("BLOCKING")`/`startswith("WARN")` 前缀判定宽于实际前缀（缺冒号空格断言）；未来 budget_check 若产出无前缀消息会被默认归类 WARN 且 msg 带前缀。当前源码仅产出两种格式，无现存 bug。
- 未使用 import：`re`（lint_script.py，实现者 concerns 遗漏此项，只报了 MAX_TURN_CHARS）；tests 内 `json`（brief 自带）；`MAX_TURN_CHARS`（已披露）。
- `test_unknown_word_present_no_warn` 断言依赖 WARN 消息固定文案中的"我不知道"子串（间接断言），若文案改动会静默失效——brief 自带测试，非实现者引入。
- 无参 CLI traceback（见 Important 2 的行为细节，归级为同一问题的健壮性表现）。

## 5. ⚠️ Cannot verify 清单

- **TDD 红→绿顺序**：单 commit 同时含测试与实现，提交历史无法独立证明测试先写；报告文档化了 red 阶段（collection error），可信但不可独立复验。
- **报告 smoke.md 证据**：smoke.md 已不存在于仓库（临时文件，未提交）。报告引用的冒烟输出无法复核——但本人已用等价 fixture 独立复验 CLI 行为（结果与报告一致），风险低。
- **"任意 cwd 运行均正常"**：同因 smoke.md 缺失无法复现原始命令；本人从仓库根与 /tmp 独立验证均通过。

---

**最终结论**: Spec ✅ | Lead 裁决已正确执行 | sys.path 偏离接受 | Quality: Issues（Important 2 / Minor 4）| 无 Critical。建议修复项：补 budget 合并路径的回归测试、加固 CLI 参数解析。

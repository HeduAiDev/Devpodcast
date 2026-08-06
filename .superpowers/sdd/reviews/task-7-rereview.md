# Task 7 Re-review — 修复轮复审

**评审对象**: commit `aa5ae8f`（fix: lint_script CLI 参数守卫 + budget 转换路径测试覆盖），基于 `dac6a7d`
**评审方式**: 读 `f04990e..HEAD` 全量 diff + `dac6a7d..aa5ae8f` 精确 delta；对照 `scripts/voice_budget.py`、`scripts/script_parser.py` 实际源码逐条核对断言有效性；按约束不重跑测试。

## 1. Important ①（dict 转换路径测试覆盖）：已修复

- **测试真实存在**：delta 确认仅新增 2 用例（`test_budget_overrun_blocking_strips_prefix`、`test_long_turn_warn_strips_prefix`），原有 5 个未动。
- **断言真实有效（非空转）**，与源码逐行核对：
  - **BLOCKING 用例**：60 字 turn → `estimate_duration = 60/4 = 15s > 0.1×60×1.15 = 6.9s` → budget_check 实际产出 `"BLOCKING: 预计 15s 超过目标 6s 的 115% 余量"`（voice_budget.py L21-22 格式）。断言 `blocking` 非空 + msg 含 `"预计"` + 不以 `"BLOCKING: "` 开头。若级别被误归类（BLOCKING→WARN）过滤即空 → 失败；若 10 字符前缀未剥离 → 失败。断言有效。
  - **WARN 用例**：250 字 > MAX_TURN_CHARS=200 → 产出 `"WARN: turn 0 (S1) 长 250 字，超过 200 字换气上限"`（L24-25 格式）；总时长 62.5s < 35min×60×1.15=2415s → 无 BLOCKING。断言含"换气"的 WARN 非空 + 含 `"长 250 字"` + 不以 `"WARN: "` 开头 + 无 BLOCKING（防向上误归类）。断言有效。
- **确实覆盖转换路径**：两用例均强制 budget_check 产出 issue（0.1min 超限 / 250 字超换气），分别命中转换循环的 `startswith("BLOCKING")` 分支（10 字符剥离）与 else/WARN 分支（6 字符剥离）——被裁决修复的代码两条分支均有回归测试，TDD 纪律闭环。
- **parser 侧核对**：TURN_RE 剥离标签并 strip，`t.text` 恰为 60/250 字，与注释及断言精确一致（即便最坏情况含标签，67/257 字也不影响判定，余量充足）。
- 报告声称 13 passed 与文件内测试数（5+2+6=13）一致；断言文案与 voice_budget.py 源码逐字吻合，测试通过声明可信。

## 2. Important ②（CLI 参数守卫）：已修复

- **守卫逻辑正确**（delta 确认）：`if not argv` → USAGE 到 stderr + 返回 2；`--voices`/`--target-minutes` 缺值（`i+1 >= len(argv)` 或下一参数以 `--` 开头）→ USAGE + 2；`float()` 抛 ValueError → `error: --target-minutes 需要合法数值，得到 '<值>'` 到 stderr + 2。首轮枚举的三个失败模式（无参/缺值/非法数值 IndexError/ValueError traceback）全部消除，无 traceback。
- **返回码语义未破坏**：合法路径代码未动（`return 1 if any(level=="BLOCKING") else 0`），`__main__` 仍 `raise SystemExit(main())`；exit 2 仅用于用法错误，不违反规格 0/1 契约。
- **守卫无误伤合法路径**：新 6 个 CLI 测试全部非空转（无参→2、缺 voices 值→2、缺 target 值→2、非法 target→2 且 stderr 含该值、合法干净→0、未知引用→1）；若守卫被删，前 4 个测试将因 IndexError 报错而非通过，回归保护有效。`--target-minutes 0`/负值不崩溃（budget_check 无目标除法，仅产出误报 BLOCKING，不属本次修复范围）。

## 3. 新问题：无

无 Critical、无 Important 新问题。残余观察（非本次引入，不阻塞）：
- **Minor（残余）**：`--voices` 指向不存在文件（FileNotFoundError）或非法 JSON（JSONDecodeError）仍会 traceback——首轮建议的"__main__ 捕获"未实施，但该输入类不在首轮枚举的三个失败模式内，属修复范围之外残留。
- **信息性**：tests 内 `import pytest` 仍未被使用（brief 自带，首轮未标记，delta 确认非本次新增）；`re`/`MAX_TURN_CHARS` 未用 import 已按 Minor 清理（delta 确认删除），tests 内 `json` 现被 `json.dumps` 实际使用。

## 4. 最终判定：**Approved**

- Important 2/2 均已彻底修复（转换路径两分支有有效回归测试；三类误调用有守卫 + 测试，返回码语义完整）。
- 无新增 Critical/Important；Minor 残余 2 项（voices 文件读取类 traceback、tests 未用 pytest import）非阻塞、非本次引入。

## ⚠️ Cannot verify

- 13 passed / 全量 43 passed：按约束未重跑；但断言与 voice_budget.py/script_parser.py 源码逐行核对一致，测试数与文件吻合（5+2+6=13；35+8=43），可信度高。
- 新增测试的 TDD 红→绿顺序：修复单 commit 同时含测试与实现，无法独立证明。

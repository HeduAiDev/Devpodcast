# Task 14 复审（FIX ROUND 1）：2 Important + 2 Minor 修复验证

复审对象：提交 `c9a8b62`（fix: season_bible register CLI + writer 自检命令修正，5 文件 70 insertions/6 deletions）。注：复审包 `task-14-rereview.pkg` 生成时被截断（仅 135 行，diff 止于 season_bible.py 中段），本次复审直接从 git 取 `444522e..HEAD` 与 `c9a8b62` 完整 diff 验证，无盲区。约束：不重跑测试，凭修复者附带的 9 passed + 全量 85 passed 输出。

## 1. 四项修复逐一验证

### Important ① — season_bible.py register CLI 静默 no-op：**已修复**

- **before 状态确认**：`b73ef6b` 版 `main()` 仅分发 `due`，无条件 `return 0`——register 子命令静默 no-op 属实。
- **main() 真实挂上 register**：`scripts/season_bible.py` L41-54 新增 `register` 分支，成功落盘 `return 0`。
- **数据层签名未变**：`register(arc_map, ep_id, fields)` 原样保留（diff 仅动 USAGE 与 main()）。
- **错误守卫齐全**：缺参（`len(argv) < 4`）→ usage 到 stderr + `return 2`；非法 JSON（`json.JSONDecodeError` 捕获）→「非法 JSON」+ 2；fields 非对象（`isinstance(fields, dict)` 校验）→「JSON 对象」+ 2。
- **未知命令从静默改响亮**：原无条件 `return 0` 改为报「未知命令」+ usage + `return 2`，堵死同类 no-op（L55-57）。
- **USAGE 双命令**：due + register 两行 usage 齐备（L7-10）。
- **archivist.md 提示词命令与 CLI 一致**：archivist.md L45 `scripts/season_bible.py register <arc-map.json> <ep_id> '{"payoff_due": [...]}'` 与新签名逐字匹配，走「改脚本」路线、提示词无需改动，评审 Important #1 解除。
- **6 个新测试真实断言**（tests/test_season_bible.py 新增 6 用例）：
  - `test_cli_register_writes_arc_map`：rc==0 后读回文件断言 `foreshadow_laid` 已写入——真落盘断言。
  - `test_cli_register_full_archivist_flow`：按 archivist.md 命令形态传中文内容，读回断言 payoff/foreshadow 均落盘。
  - `test_cli_register_missing_fields_arg` / `test_cli_register_invalid_json` / `test_cli_register_rejects_non_object_fields`：rc==2 + stderr 消息断言（含缺参时文件未被写坏断言）。
  - `test_cli_unknown_command_fails_loudly`：未知命令 rc==2 +「未知命令」报错断言。

### Important ② — writer.md lint_punct 自检命令缺参数：**已修复**

- writer.md L83 改为 `python3 scripts/lint_punct.py <ep_dir>/script.md`。
- 与 lint_punct.py 实际签名一致：`USAGE = "usage: python3 scripts/lint_punct.py <file>"`，main 取 `argv[0]` 为文件路径——`<ep_dir>/script.md` 正确。
- 与同节 L82 lint_script 命令的 `<ep_dir>/script.md` 占位符写法完全一致。

### Minor ① — researcher.md original_text 非 schema 字段：**已修复**

- 「取材要求」由「（`original_text` 或 claim 的原文形态）」改为「（以 `claim` 字段存原文形态）」。
- `.claude/agents/` 全目录 grep `original_text` 零残留；`claim` 是 voices.schema 12 个 required 字段之一，不再诱导 schema 非法记录。

### Minor ② — hook-engineer.md voice-guide 读项缺容错：**已修复**

- hook-engineer.md L16 读项加「（若已存在，Phase A 由 Lead 落笔）」。
- 与 planner.md L22「若已存在」同模式，容忍 Phase A 三条腿并行时 bible 尚未建立。

## 2. 新问题

**无。**

逐项核查无回归：due 分支行为不变（显式 return 0，输出逻辑未动）；register 错误路径全部 stderr + rc 2、成功路径唯一且落盘；未知命令改动不影响既有 79 个测试（修复者附全量 85 passed 输出，其中原 79 个不变）；修复提交只动 5 个文件（3 agent + 1 脚本 + 1 测试），无越界改动；工作树与 HEAD 一致。

## 3. 最终判定

**Approved**

- Critical：0（修复后）
- Important：0（修复后）
- Minor：0（修复后）

首轮 2 Important + 2 Minor 全部彻底修复，无新引入问题，可合并。

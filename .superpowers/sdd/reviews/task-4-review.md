# Task 4 Review: script.md 解析器

**评审对象**: commit `8b4f161`（`scripts/script_parser.py` + `tests/test_script_parser.py`，2 files, +110）
**评审方式**: brief → diff 逐项核对；两处偏离按正则语义独立推演（未跑测试）；磁盘状态核验（`git show 8b4f161` 与工作区文件逐字节一致，工作区干净，仅 `.superpowers/` 未跟踪）。

---

## 1. Spec compliance 判定: ✅

| Brief 必达物 | 状态 |
|---|---|
| 创建 `scripts/script_parser.py` | ✅ 与 brief Step 3 参考实现逐行一致（除 2 处经裁决的加固） |
| 创建 `tests/test_script_parser.py` | ✅ 5 个测试原样照抄 brief Step 1 |
| `Turn` dataclass（speaker/text/voice_refs/pause_ms，default_factory/None 默认值） | ✅ |
| `Script` dataclass（title/turns）+ 模块级 `parse(path) -> Script` | ✅（`Path(path)` 兼容 str，超集） |
| `to_dialogue_tags(turn) -> str`（`[S1] text [/S1]`，按测试断言含空格） | ✅ staticmethod，实例调用合法 |
| `ScriptParseError(ValueError)` | ✅ |
| `TURN_RE`（backreference `\1` + `re.S`）、`VOICE_RE`、`BREAK_RE` | ✅ 逐字符一致 |
| `open_stray`/`bad` 兜底校验 | ✅（`open_stray` 加了 `re.S`，见裁决 1；追加闭合计数，见裁决 2） |
| TDD 纪律（红 → 绿 → 提交） | ✅ 报告 Step 2 红线 `ModuleNotFoundError`，Step 4 绿 5/5 + 全量 18/18 |
| 提交 | ✅ HEAD=`8b4f161`，message 与 brief 一字不差；**作者身份已核实** `devpodcast <devpodcast@local>`（`git show` 实测，满足 Global Constraint 的 git identity） |
| 零跨仓依赖 | ✅ 代码只 import `re`/`dataclasses`/`pathlib`（stdlib），无任何跨仓引用 |

**缺项**: 无。**多余项**: 无（2 处偏离属于 brief 代码修正而非多余功能，见裁决）。

## 2. 两处偏离裁决: 接受 / 接受

### 偏离 1（`open_stray` 补 `re.S`）— **接受**

brief 原式 `re.findall(r"\[(S[12])\](?!.*?\[/\1\])", text)` 无 `re.S`。推演：`TURN_RE` 带 `re.S`，多行 turn（`[S1] 第一行\n第二行 [/S1]`）能正常匹配；但 `open_stray` 的负向前瞻 `.*?` 不跨 `\n`，在 `[S1]` 处同一行内找不到 `[/S1]` → 误判"未闭合"抛 `ScriptParseError`。**这是 brief 原代码的真实 bug**（brief 的 `open_stray` 兜底逻辑与其主解析器行为自相矛盾）。加 `re.S` 后前瞻可跨行看到配对闭合标签，不再误报；单行未闭合（无任何 `[/S1]`）仍正确抛错。不破坏 5 个 brief 测试（逐一推演：basic/pause/to_dialogue_tags 的 turn 均单行闭合、闭合计数 3/1/1 匹配；unclosed 仍经 open_stray 抛错；bad_speaker 路径不受影响）。

### 偏离 2（闭合标签计数校验）— **接受**

`[S2] 开场 [/S1] 收尾 [/S2]`：推演 `TURN_RE` 会整段匹配为一个 S2 turn，`[/S1]` 静默吞入 turn.text（将来直接进 dialogue tags 输出）；`open_stray` 只找开标签（`[/S1]` 不匹配 `\[(S[12])\]`），`bad` 也不命中 → 原 brief 代码完全漏检。**真实漏洞**。修复 `len(re.findall(r"\[/(S[12])\]", text)) != len(turns)` → 抛错：契约合法输入下每个 TURN_RE 匹配恰好消耗一个闭合标签，计数恒等，**无假阳性**；任何不等号情形（吞入错配闭合、孤立 `[/S1]`、交叉嵌套如 `[S1] a [S2] b [/S1] c [/S2]`）均被捕获。5 个 brief 测试逐一推演不受影响。

两处修正均属于 brief 明示的"兜底校验"职责范围内，方向是加固而非改变语义，与 brief 测试契约无冲突。

## 3. 代码质量判定: Approved（含 5 条 Minor 记录）

- **`TURN_RE` 正则**: `\[(S[12])\](.*?)\[/\1\]` + `re.S` — backreference 正确（闭合须同 speaker），lazy `.*?` 停在首个同类闭合（成对解析正确，不会贪婪跨 turn），`re.S` 与 writer 契约的多行 turn 一致。✅
- **`VOICE_RE`** `[a-zA-Z0-9_-]+`：连字符置于类尾，按字面匹配（`voice-001` 正确）。✅
- **`BREAK_RE`** `<break\s+(\d+)ms\s*>`：宽容首尾空白，`int()` 对 `\d+` 安全。✅
- **清洗顺序**: 先 `findall` 提取 refs 再 `sub` 移除，`pause` 取自清洗前 body —— 正确。
- **错误信息**: 中文 + 列出肇事标签列表（`未闭合的说话人标记: ['S1']` 等），可读性好。
- **健壮性**: 文件缺失抛 `FileNotFoundError`（未包装，brief 同款）；空文件解析为空 Script 不抛错；对畸形输入有兜底而非崩溃。

### Minor 清单

1. **两处修正未沉淀为回归测试**：偏离 1/2 仅用临时脚本验证，`tests/test_script_parser.py` 与 brief 完全一致，这两个防御性检查没有常驻测试保护（TDD 纪律的灰色地带——brief 原样规定了测试文件内容，可辩护，但日后重构失去护栏）。
2. **非法 `<break>` 值未校验**：brief 接口 bullet 声称 format_error 集合覆盖"非法 `<break>` 值"，但 brief 参考代码与最终实现均未实现——`<break abc>` 静默留在 turn.text 中。属 brief 内部不一致（接口声明 vs 参考实现），非实现者回归；建议 brief 作者澄清或后续任务补。
3. **非 S1/S2 闭合标签静默忽略**：`[/S3]` 单独出现时，`bad` 只扫开标签、闭合计数只数 S1/S2 → 不报错。brief 同款缺口，writer 契约下不发生。
4. **break 移除残留双空格**：`"前面 <break 500ms> 后面"` → `"前面  后面"`（双空格）。brief-identical，纯观感。
5. **turn 内嵌套同 speaker 开标签被吞**（`[S1] a [S1] b [/S1]` 合为一个 turn）：报告已声明、brief 明确接受的简化（"嵌套/交叉的复杂畸形输入依赖 writer 契约保证"）。

**Critical: 0 | Important: 0 | Minor: 5**

## 4. ⚠️ Cannot verify 清单

1. **测试运行结果 5/5 + 18/18**：实现者声明；按指示未重跑。补充：对 5 个 brief 测试逐一做了逻辑推演，最终代码均满足断言路径。
2. **两处修正的临时脚本验证**：报告所述过程不可复现（无产物留存）；但修正正确性已在本评审第 2 节按正则语义独立推演确认。
3. **跨任务/跨仓无干扰**（"零跨仓依赖"中仓库间部分）：仅能确认本提交 diff 无外部引用；其他任务仓状态不在评审包内。

---
**结论**: Spec ✅（无缺项/多余项）；偏离 1 接受、偏离 2 接受；质量 Approved（5 Minor，0 Critical/Important）。

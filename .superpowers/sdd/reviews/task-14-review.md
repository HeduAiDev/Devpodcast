# Task 14 评审：8 个 agent 提示词（spec 对齐性）

评审对象：提交 `b73ef6b`（8 文件 595 insertions，与磁盘一致，`git diff` 为空；提示词内嵌 7 个 JSON 示例全部通过 `json.loads`）。
对齐源头：spec §4（角色表 + 硬规则）、§5（voice-guide）、§6（voices 字段/取证/三档）、§7.3（TTS 停顿分支）、§11（BLOCKED/回环/降级）、§12.3（评审 6 维）+ `schemas/*.json` + `scripts/` 实际 CLI。

## 1. 逐文件核对结果表

| 文件 | 契约点覆盖 | 判定 |
|---|---|---|
| planner.md | season-plan.json 与 schema 一致（show + episodes 六字段齐）；议题驱动 + 跨章抽线（≥2 章判据、范例 ch15/16/25）；依赖无环；期数 5–8；素材不足（<6 章/要点全空/纯概念）BLOCKED；快照只读 | ✅ 通过 |
| book-analyst.md | episode-card 7 required 字段 + cross_chapter_threads{nchapter_id,mechanism} / narrative_anchors{chapter_id,section} 与 schema 一致；要点源优先级 sections > key_classes > mechanisms 专节 + 逐级定义；无支撑/自相矛盾 BLOCKED；voices_refs 空数组=有意 | ✅ 通过 |
| researcher.md | 12 字段与 schema required 逐字一致；category/verified/confidence 三值枚举、source_platform 15 平台枚举与 schema 逐字一致；取证纪律 5 条全（不编/评论≠事实/匿名化/平台偏差/3 个月时效）；查不到 → BLOCKED 或 low confidence「未一手核实」（与 lint_voices ③ 一致）；voices_coverage=partial 显式上报 | ✅ 通过（1 Minor） |
| hook-engineer.md | arc.json key=episode_id + opening/closing/controversy{claim,counter,resolution}/foreshadow_map 四件套与 schema 一致；钩子「一句生活化或反直觉」+ 反例；收尾「不总结给悬念或行动」；争议双方都站得住、resolution 不和稀泥；cover-prompt 可选 | ✅ 通过（1 Minor） |
| writer.md | 唯一写稿权（§4.1 硬规则 1）；格式契约与 script_parser 一致（`[S1]`/`[/S1]` 成对闭合、`{{voice:<id>}}` 存在性 BLOCKING、`<break Nms>`）；voice-guide 三条纪律 + 老张/阿凯性格底线与 §5.1/§5.2 对齐；求职者配额（≤2 处、挂真实 voices、融老张提问）；原声三档策略（a 默认重合成 / b 需授权未标一律不用 / c 转述也包 `{{voice:}}`，三档显式标注引述边界 + claim vs verified 层次）；零脚手架泄漏；receiving-code-review；收工自检 lint_script BLOCKING 清零；时长数字（4 字/秒、×1.15、单段 ≤200 字）与 voice_budget 常量（200/1.15）完全一致 | ✅ 通过（1 Important） |
| producer.md | 只写 production-notes.md 不改稿（§4.1 硬规则 2）；script_line ≥1 + severity 四值与 schema 一致；口播四类检查（换气 >200 字/节奏/引述停顿/时长 ×1.15）；两类 provider 分支（native_dialogue=true MOSS-TTSD=软提示不写死毫秒 / false CosyVoice3=350–500ms 切换、150–250ms 同人）与 §7.3 逐字一致；与 reviewer 分工；回环 ≤2 升级 | ✅ 通过 |
| reviewer.md | 6 维与 §12.3 逐字对齐（事实准确/批判强度/口播可懂/双声线平衡/求职者共鸣/原声保真，看什么逐项对应）；reviews/<run>-review.json + run-ledger 更新；有界回环 ≤3（第 2 轮起只看 fail）、review-exhausted → BLOCKED（§11.1/§11.2）；无权因风格偏好退稿（退稿必须指到契约）；voices_coverage=partial 降级知情（§11.3）；不改稿 | ✅ 通过 |
| archivist.md | Season Bible 四件套与 season-bible schema 一致（glossary/voice-guide/arc-map{episodes:{foreshadow_due,payoff_due}}/voices-index）；voice-guide 由 Lead 落笔只建占位不改内容（§5）；trace 长期记忆（archivist.py log 签名一致）；每完成一期核对 arc-map；只回写 bible 与 trace；未回收伏笔点名、连续两期升级 | ✅ 通过（1 Important） |

## 2. 代码质量判定：**Issues**

spec 契约点零缺失、零字段不一致，但有两处「命令写错」会在运行时误导 agent 执行。

### Critical：0

### Important：2

1. **archivist.md「回写 arc-map」的 `register` 命令是静默 no-op**
   `scripts/season_bible.py` 的 `main()` 只分发 `due`（`if cmd == "due"`），`register` 函数定义了但从未挂到 CLI；`python3 scripts/season_bible.py register <arc-map.json> <ep_id> '{"payoff_due": [...]}'` 会打印 usage 后 exit 0 且不写文件。archivist 照命令执行会拿到成功码却无落盘——跨期伏笔回写静默丢失，且收工自检「本期 due 伏笔全部核对并回写 arc-map」只有在 agent 主动复查文件内容时才能兜住。修复点在 `scripts/season_bible.py`（上一任务产物，出本任务范围）加一行分发，或改提示词只依赖 `due` + 明确回写由脚本 API 完成；报告声称的契约点「register 回写 arc-map」目前不成立。

2. **writer.md 收工自检的 `lint_punct` 命令缺参数**
   提示词写 `python3 scripts/lint_punct.py 无报错（半角标点）`，实际签名是 `lint_punct.py <file>`（spec §12.1 的 `--all` 也不存在）：无参调用打印 usage、exit 2，「自检」命令本身必失败。应改为 `python3 scripts/lint_punct.py <ep_dir>/script.md`。

### Minor：2

1. **researcher.md 取材要求提到 `original_text` 字段**——「（`original_text` 或 claim 的原文形态）」。`original_text` 不在 voices.schema（`additionalProperties: false`，12 required 字段），照字面写会产出 schema 非法记录。建议只保留「存 claim 原文形态」，spec §6.4 的 original_text 属引述素材概念而非 voices.json 字段。
2. **hook-engineer.md 开工前读 voice-guide.md 无「若已存在」容错**——planner.md 对同一文件写了「若已存在」，hook-engineer 没写。Phase A 三条腿并行时 bible 可能尚未建立（voice-guide 由 Lead 落笔），缺容错说明可能让 agent 在语气来源缺失时误判或瞎编语气。

### 已核对一致、无问题的细节

- lint_script / lint_voices / lint_trace / archivist 的 CLI 签名与提示词写法逐一核实一致；voice_budget 的 200 字/1.15/4 字每秒与 writer、producer 数字一致；script_parser 的 `<break Nms>` 记号与规范形态 `<break 500ms>` 一致（parser 正则要求 ms 字面后缀，记号本身含 ms）。
- 8 文件 frontmatter 五字段齐全；提交干净（仅 8 个 agents 文件）。

## 3. ⚠️ Cannot verify 清单

1. **运行时效果**：本任务无 pytest，提示词的引导质量（agent 实际产出是否达契约）只能真跑 pipeline 验证，不在本次评审范围。
2. **voice-guide.md 实际内容与提示词一致性**：writer/reviewer 里老张/阿凯性格底线、三条纪律的措辞来自 spec；Lead 落笔的 voice-guide.md 最终内容（含 voice-samples、说话人命名 §16 待定项）尚未存在，无法核对「提示词措辞 vs bible 内容」是否互相打架。
3. **`<break 300>` 无 ms 后缀的容错边界**：parser 正则 `(?:<break\s+(\d+)ms\s*>)` 对无 ms 后缀的停顿标记静默吞为文本不报错（不触发 BLOCKING），提示词未显式声明「ms 后缀必须字面存在」；风险低但属运行时才暴露的类别。
4. **reviews/<run>-review.json 的结构**：无对应 schema（9 个 schema 里没有 reviews），维度结构是提示词自定义（score/issues/verdict），与 Task 15 workflow 的消费端一致性待 workflow 落地后核。
5. **season_bible.py `register` 修复责任归属**（改脚本还是改提示词）需 Lead 定夺——若走改脚本路线，archivist.md 无需改动，本评审的 Important #1 即解除。

---

**结论**：spec §4/§5/§6/§7.3/§11/§12.3 契约点全落、schema 字段全对齐，无 Critical；2 个 Important（1 个是出本任务范围的脚本分发缺失被提示词引用、1 个 lint_punct 命令缺参）+ 2 个 Minor。建议：合并前修 Important #2（一行改动）；Important #1 修脚本或由 Lead 裁定改法；Minor 随 Task 15 一并处理。

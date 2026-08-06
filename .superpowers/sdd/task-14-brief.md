### Task 14: 8 个 agent 提示词

**Files:**
- Create: `.claude/agents/planner.md`、`.claude/agents/book-analyst.md`、`.claude/agents/researcher.md`、`.claude/agents/hook-engineer.md`、`.claude/agents/writer.md`、`.claude/agents/producer.md`、`.claude/agents/reviewer.md`、`.claude/agents/archivist.md`

**Interfaces:**
- 每个提示词 = 持久角色契约。workflow（Task 15）经 `agentType` 调用；产物契约对齐 §2.4 schema。
- 本任务无 pytest（提示词文件）；验收 = 每个文件存在 + 关键契约点齐全（人工/评审核对）。

- [ ] **Step 1: 写 planner.md**

关键内容：输入 `source-book/` 快照 + 书大纲；输出 `season/season-plan.json`（议题 N 期 + 顺序 + 依赖 + 钩子 + 伏笔）；触发条件：素材不足以支撑议题驱动 → BLOCKED；不按章节一一对应，**跨章抽线**（如「内存是主角」抽 ch15/16/25）。

- [ ] **Step 2: 写 book-analyst.md**

关键内容：输入 `season-plan.json` 的议题定义 + `source-book/chapter-cards/*.json`；输出 `episodes/epNN-*/episode-card.json`（topic / cross_chapter_threads / key_mechanisms / voices_refs）；要点源优先级：sections（narrative 小节）> key_classes > mechanisms；议题在书里找不到支撑 → BLOCKED。

- [ ] **Step 3: 写 researcher.md**

关键内容：输出 `season/voices.json`；字段纪律照 spec §6.2/§6.4（url/date/平台/confidence/anonymized/category/writer_note）；源类 = 批判源 + 求职者源（国内外社交平台清单见 spec §6.1）；四类取材角度；取证纪律（评论≠事实 / 匿名化 / 平台偏差 / 时效）；查不到 → BLOCKED 或 low confidence 标注，**不许编**。

- [ ] **Step 4: 写 hook-engineer.md**

关键内容：输入 season-plan 议题；输出 `season/arc.json`（每期开场钩子 / 收尾金句 / 争议框架 / 伏笔映射）；钩子标准：一句生活化或反直觉的话让听众想继续听；收尾标准：不总结，给悬念或行动。

- [ ] **Step 5: 写 writer.md**

关键内容：**唯一有权写 script.md**；输入 episode-card + voices + arc + Season Bible（voice-guide 强制复用）；script.md 格式契约（Task 4：`[S1]`/`[S2]` 成对、`{{voice:}}` 引用、`<break Nms>`）；voice-guide 三条纪律 + 求职者配额（每期至多两处、必须挂真实 voices 条目）；**原声引述三档策略**（spec §6.4：a 按原说话人音色重合成=默认 / b 真实音频片段=需授权 / c 只标引述由 S1/S2 转述；三档都须在脚本里显式标注引述边界）；零脚手架泄漏；producer 意见逐条采纳或带理由反驳（receiving-code-review skill）；收工自检跑 lint_script（BLOCKING 清零）。

- [ ] **Step 6: 写 producer.md**

关键内容：**只写 production-notes.md 不改稿**；每条带 script 行号；看什么 = 口播换气（单段>200字）/ 双声线节奏（连续短句平了）/ 引述前停顿 / 时长预算；两类 provider 的停顿语义分支（对话模型=改文本节奏引导、分段模型=插静音毫秒）；与 reviewer 分工：producer 看"口播感"，reviewer 看"内容质量"。

- [ ] **Step 7: 写 reviewer.md**

关键内容：6 维并行（事实准确 / 批判强度 / 口播可懂 / 双声线平衡 / 求职者共鸣 / 原声保真）；输出 `reviews/*.json`；有界回环 ≤3 轮；review-exhausted → BLOCKED 升级；评审无权因风格偏好退稿（writer 说了算怎么写）。

- [ ] **Step 8: 写 archivist.md**

关键内容：归档 + 回写 Season Bible（glossary 口播译名 / arc-map 伏笔回写 / voices-index 引用台账）；trace 长期记忆（scripts/archivist.py）；跨期连贯性：每完成一期核对 arc-map。

- [ ] **Step 9: 提交**

```bash
git add .claude/agents/
git commit -m "feat: 8 个持久角色提示词（spec §4/§5/§6 落地）"
```

---

### Task 15: 两个 workflow 骨架

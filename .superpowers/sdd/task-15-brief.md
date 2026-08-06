### Task 15: 两个 workflow 骨架

**Files:**
- Create: `.claude/workflows/season-pipeline.js`
- Create: `.claude/workflows/episode-pipeline.js`

**Interfaces:**
- 结构完全照 repo2book 的 `chapter-pipeline.js` 模式（meta+phases / args 解析 / STATUS_SCHEMA / 逃生舱 / head() 注入角色契约）——**自写实现，不复制粘贴**。
- season-pipeline 阶段：`Plan → Research → Hooks → Slice → Bible`（planner / researcher / hook-engineer / book-analyst×N 并行 / archivist）
- episode-pipeline 阶段：`Write → Produce → Revise → TTS → AudioQA → Review → Archive`（writer / producer / writer / tts-engine / audio-qa / reviewer / archivist）
- **args 契约**（对齐 Task 18/19 发车调用）：
  - season-pipeline: `{show: string, episodes: number}`（episodes 为议题数，planner 自行定议题）
  - episode-pipeline: `{show: string, ep_id: string, target_minutes: number}`
- 每个阶段完成后跑对应确定性 linter（Task 7/8/9 的 CLI），BLOCKING 回环该阶段 ≤2 轮再升级。
- 本任务无 pytest；验收 = 文件存在 + `node --check` 语法通过 + meta.phases 与上述阶段一致。

- [ ] **Step 1: 写 season-pipeline.js**（完整结构，含公共件）

```js
export const meta = {
  name: 'season-pipeline',
  description: 'Phase A：整季编排——planner 抽议题 → researcher 查 voices → hook-engineer 出钩子 → book-analyst 按议题切片 → archivist 建 Bible',
  phases: [
    { title: 'Plan', detail: 'planner 通读书源快照，产出 season-plan.json（N 期议题/顺序/依赖/伏笔）' },
    { title: 'Research', detail: 'researcher 真上网查批判源+求职者源，产 voices.json' },
    { title: 'Hooks', detail: 'hook-engineer 每期开场钩子/收尾金句/争议框架，产 arc.json' },
    { title: 'Slice', detail: 'book-analyst×N 按议题跨章切片，每期产 episode-card.json' },
    { title: 'Bible', detail: 'archivist 建/更新 Season Bible + trace' },
  ],
}

// args 契约（与脚本内 CFG 同构，参考 repo2book 的 args 可靠解析模式）：
//   { show: "vllm-podcast", episodes: 5 }
// 逃生舱：任一站返回 { status: "BLOCKED", blocker_reason } → 立即中止升级 Lead。
// 公共件（两文件共享模式）：
//   STATUS_SCHEMA = { type: 'object', required: ['status', 'note'],
//                     properties: { status: { enum: ['OK','BLOCKED'] }, note: {...} } }
//   function head(role, showDir) → 注入角色契约路径 + 产物绝对路径 + 书源快照路径
//   每个 agent 调用的 prompt 均含：角色契约路径、本期输入产物路径、输出产物路径、逃生舱文案
// Plan 阶段：planner 产出 season/season-plan.json（episodes 数组，每项按 season-plan.schema）
// Research 阶段：researcher 产出 season/voices.json（跑 lint_voices 无 BLOCKING）
// Hooks 阶段：hook-engineer 产出 season/arc.json
// Slice 阶段：book-analyst × episodes 并行，每个产出 episodes/<slug>/episode-card.json
// Bible 阶段：archivist 产出 season/bible/* + trace 记录
// 写完后：node --check
```

- [ ] **Step 2: 写 episode-pipeline.js**（完整结构，含公共件）

```js
export const meta = {
  name: 'episode-pipeline',
  description: 'Phase B：单期制作——writer 主笔 → producer 提意见 → writer 定稿 → TTS 合成 → audio-qa 质检 → reviewer 6 维评审 → archivist 归档',
  phases: [
    { title: 'Write', detail: 'writer 以 episode-card+voices+arc+Bible 为源写 script.md（唯一有权写）' },
    { title: 'Produce', detail: 'producer 出 production-notes.md（只建议，带行号）' },
    { title: 'Revise', detail: 'writer 逐条采纳/反驳 producer 意见，定稿' },
    { title: 'TTS', detail: 'tts-engine 本地 GPU 合成 episode.wav + segments/' },
    { title: 'AudioQA', detail: 'audio-qa 试听质检（时长/削波/静音/响度），有界回环 ≤2' },
    { title: 'Review', detail: 'reviewer 6 维并行评审，有界回环 ≤3' },
    { title: 'Archive', detail: 'archivist 归档 + 回写 Bible' },
  ],
}

// args 契约：{ show: "vllm-podcast", ep_id: "ep01", target_minutes: 35 }
// Write 阶段后跑 lint_script/lint_punct/lint_anchors/lint_trace，BLOCKING 回环 writer ≤2 轮
// TTS 阶段：DialogueTTSProvider.synthesize（script → [S1]/[S2] 标签串 → episode.wav）
// AudioQA 阶段：audio_qa.py，BLOCKING 回环 tts-engine（重合成）或 writer（改稿）≤2 轮
// Review 阶段：reviewer 6 维并行（spec §12.3），BLOCKING 回环 writer ≤3 轮，超限 review-exhausted
// Archive 阶段：archivist 归档 + season_bible.register 回写 arc-map + shownotes.md
// 写完后：node --check
```

- [ ] **Step 3: 语法检查**

Run: `node --check .claude/workflows/season-pipeline.js && node --check .claude/workflows/episode-pipeline.js`
Expected: 无输出（语法通过）

- [ ] **Step 4: 提交**

```bash
git add .claude/workflows/
git commit -m "feat: season-pipeline / episode-pipeline 骨架"
```

---

### Task 16: CLAUDE.md + ARCHITECT-RUNBOOK + README

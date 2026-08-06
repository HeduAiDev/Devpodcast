// .claude/workflows/season-pipeline.js
// devpodcast Phase A：整季编排（spec §3.2 / §3.3①）。Task 15 骨架。
// 阶段链：Plan → Research(+lint_voices 门禁 + voices_coverage 落盘) → Hooks → Slice(book-analyst×N 并行) → Bible。
// args 契约：{ show: "vllm-podcast", episodes: 5 }
//   show：节目名（shows/<show>/ 目录）；episodes：议题数（正整数，具体议题由 planner 定）。
// 配置兜底（repo2book 教训：Workflow 的 args 注入不可靠）：完全未传 args 才允许脚本内 CFG；
//   传了 args 但解析不出关键字段 → 立即返回 { escalated: 'bad-args' } 拉闸，绝不静默默认
//   （repo2book 曾静默默认错实例烧 692k tokens）。
// 逃生舱（spec §11.1）：任一 agent 返回 { status: 'BLOCKED', blocker_reason } → 立即中止升级 Lead。
//   宁可拉闸，不要产出错误成果一路跑到底。
// 公共件（真实可用，非摆设）：STATUS_SCHEMA / head(role, ctx) / ESC / runLints()。
// 工作流无模块系统（repo2book 同），公共件按需内联；本仓如自维护 lib/ 需逐字同步此处。

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

// ---------- args 解析：CFG 兜底 + bad-args 拉闸 ----------
const CFG = { show: 'vllm-podcast', episodes: 5 }  // 仅完全未传 args 的手工调试场景使用

function validArgs(x) {
  return !!x &&
    typeof x.show === 'string' && x.show.length > 0 &&
    Number.isInteger(x.episodes) && x.episodes > 0
}

let A = (typeof args !== 'undefined' && args) ? args : null
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = null } }  // named 调用 args 可能被字符串化
if (A && !validArgs(A)) A = null
if (!A) {
  if (typeof args !== 'undefined' && args) {
    return { escalated: 'bad-args', note: 'args 存在但解析不出关键字段（show 需非空字符串、episodes 需正整数）——拒绝 CFG 回退，请检查发车参数' }
  }
  A = CFG
}

// REPO 路径自动检测：Windows Git Bash 用 E:\ 风格，WSL 用 /mnt/e/ 风格（同 episode-pipeline.js）
const _win = typeof process !== 'undefined' && process.platform === 'win32'
const REPO = A.repo_root || (_win ? 'E:/Laboratory/Devpodcast' : '/mnt/e/Laboratory/Devpodcast')
const SHOW = REPO + '/shows/' + A.show
const SRC = SHOW + '/source-book'    // ★ 书源快照（摄入后只读，spec §2/§8，各站只读它）
const SEASON = SHOW + '/season'

// 模型策略：默认不指定 model → agent 继承 session 模型（本 harness 的 alias 解析不可靠，
// 曾出现 claude-sonnet-5 不被识别导致 Slice 全挂）；args.models 显式提供才传值覆盖。
const MODELS = A.models || {}

// mo(key)：只有 args.models 显式提供时才传 model 字段，否则省略（继承 session 模型）
function mo(key) { return MODELS[key] ? { model: MODELS[key] } : {} }

// 逃生舱：任何阶段发现路线/素材是错的，不许硬着头皮做错
const ESC = '\n\n**逃生舱（重要）**：如果发现给定输入/路线是错的——素材与任务对不上、产物无法忠实产出、发现无法在不撒谎的前提下继续——不要硬着头皮做。立即返回 status="BLOCKED"，blocker_reason 写清「哪里不对 + 建议怎么改」。workflow 会**立即中止**并把问题交给 Lead（项目负责人），Lead 修正后从断点续跑。**宁可拉闸，不要产出错误成果一路跑到底。**'

// 任一阶段 agent 的统一返回契约（spec §11.1）：BLOCKED → 立即中止升级 Lead
const STATUS_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['status', 'note'],
  properties: {
    status: { type: 'string', enum: ['OK', 'BLOCKED'] },
    note: { type: 'string' },
    blocker_reason: { type: 'string' },
  },
}

// planner 专属：除 STATUS_SCHEMA 外必须带回 episodes——工作流沙箱无文件系统，
// Slice 的并行调度只能靠返回值拿议题清单；与落盘 season-plan.json 的 episodes 必须一一对应
const PLAN_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['status', 'note', 'episodes'],
  properties: {
    status: { type: 'string', enum: ['OK', 'BLOCKED'] },
    note: { type: 'string' },
    blocker_reason: { type: 'string' },
    episodes: { type: 'array', items: { type: 'object', additionalProperties: false,
      required: ['episode_id', 'slug', 'topic', 'hook', 'depends_on', 'foreshadow_due'],
      properties: {
        episode_id: { type: 'string' },
        slug: { type: 'string' },
        topic: { type: 'string' },
        hook: { type: 'string' },
        depends_on: { type: 'array', items: { type: 'string' } },
        foreshadow_due: { type: 'array', items: { type: 'string' } },
        payoff_due: { type: 'array', items: { type: 'string' } },
      } } },
  },
}

// head(role, ctx)：注入角色契约路径 + 产物/书源快照路径 + 逃生舱文案。
// role 为 null 的确定性站点（linter 门禁等）无角色契约文件，只注入 ctx + ESC。
function head(role, ctxLines) {
  const lines = []
  if (role) lines.push('你的角色契约：' + REPO + '/.claude/agents/' + role + '.md —— **先读它**，严格遵守其中所有铁律。')
  lines.push(Array.isArray(ctxLines) ? ctxLines.join('\n') : String(ctxLines))
  lines.push(ESC)
  return lines.join('\n')
}

// 确定性门禁执行：workflow 沙箱无文件系统/Bash，借一个「只跑命令、不做判断」的 agent
// 把 linter CLI 的退出码与完整输出如实带回（spec §12.1：确定性 linter 前置于评审）。
async function runLints(cmds, label, phaseName) {
  return agent(
    '你是门禁执行员。只做一件事：依次运行下面 ' + cmds.length + ' 条命令——**全部跑完**（不要因一条失败跳过其余；不要读产物内容、不要评价、不要修改任何东西）：\n' +
    cmds.join('\n') + '\n' +
    '把每条命令的退出码与完整输出带回 note（命令不存在/报错也照实记录）。\n' +
    '判定：全部退出码 0 → status=OK；任一条退出码 ≠ 0（linter 找到 BLOCKING 级问题，或命令本身失败）→ status=BLOCKED，blocker_reason 写清是哪条命令、退出码多少。',
    { schema: STATUS_SCHEMA, label: label, phase: phaseName, agentType: 'claude', ...mo('runner'), effort: 'max' },
  )
}

// ---------- Plan：planner 通读全书抽议题 ----------
phase('Plan')
const plan = await agent(
  head('planner', [
    '书源快照（只读，摄入即快照，绝不回读外部书源路径）：' + SRC + '/（book.json / outline.json / chapter-cards/*.json / glossary.json）',
    '节目配置：' + SHOW + '/devpodcast.json（audience / format.target_minutes / episodes_planned）',
    'Season Bible 现状（若已存在）：' + SEASON + '/bible/voice-guide.md（议题命名要符合节目语气）',
    '产出：' + SEASON + '/season-plan.json，对齐 schemas/season-plan.schema.json',
    '目标议题数：' + A.episodes + '（可依书况微调，每增减 1 期必须在 note 说明理由）',
    '任务：通读全书快照，抽约 ' + A.episodes + ' 期议题，定顺序/依赖/伏笔。**slug 即 episodes/<slug>/ 目录名**，格式 epNN-<简短英文描述>（如 ep01-memory），全季唯一——Phase B 的 ep_id 就落在它身上。',
    '返回的 episodes 数组必须与落盘的 season-plan.json 的 episodes **一一对应**（同 episode_id、同序、同 slug）——工作流据此并行调度 Slice。',
  ]),
  { schema: PLAN_SCHEMA, label: 'plan', phase: 'Plan', agentType: 'planner', ...mo('planner') },
)
if (!plan) return { show: A.show, escalated: 'plan-failed', stage: 'Plan', note: 'planner agent 失败（限流/崩溃），无 season-plan 不得继续' }
if (plan.status === 'BLOCKED') return { show: A.show, escalated: 'plan', stage: 'Plan', reason: plan.blocker_reason }
const EPS = plan.episodes || []
if (EPS.length < 1) return { show: A.show, escalated: 'plan-empty', stage: 'Plan', note: 'planner 未返回任何议题（episodes 为空）——无法调度 Slice，升级 Lead' }
if (!EPS.every(function (e) { return e && typeof e.slug === 'string' && e.slug.length > 0 })) {
  return { show: A.show, escalated: 'plan-bad', stage: 'Plan', note: 'planner 返回的 episodes 缺 slug 或 slug 为空——无法定位 episodes/<slug>/ 目录，升级 Lead' }
}
log('Plan 完成：' + EPS.length + ' 期议题')

// ---------- Research：researcher 真上网查外部声音 + lint_voices 门禁（回环 ≤2 轮） ----------
phase('Research')
const research = await agent(
  head('researcher', [
    '书源快照（只读）：' + SRC + '/',
    '议题清单：' + SEASON + '/season-plan.json（按 episodes 逐期查声音）',
    '产出：' + SEASON + '/voices.json，对齐 schemas/voices.schema.json（字段/枚举/取证纪律见你的契约，spec §6）',
    '任务：真上网查批判源 + 求职者源，每条带 source_url/source_date/source_platform/confidence/匿名化；关键议题查不到任何可信外部声音 → status=BLOCKED（spec §11.1 researcher 拉闸条件），不许编、不许凭记忆写。',
  ]),
  { schema: STATUS_SCHEMA, label: 'research', phase: 'Research', agentType: 'researcher', ...mo('researcher') },
)
if (!research) return { show: A.show, escalated: 'research-failed', stage: 'Research', note: 'researcher agent 失败（限流/崩溃），无 voices.json 不得继续' }
if (research.status === 'BLOCKED') return { show: A.show, escalated: 'research', stage: 'Research', reason: research.blocker_reason }
let voicesLint = null
let voicesFixes = 0
for (;;) {
  voicesLint = await runLints(
    ['python ' + REPO + '/scripts/lint_voices.py ' + SEASON + '/voices.json'],
    'voices-lint r' + (voicesFixes + 1), 'Research',
  )
  if (!voicesLint) return { show: A.show, escalated: 'voices-lint-failed', stage: 'Research', note: '门禁执行 agent 失败（限流/崩溃）——lint_voices 未执行不放行' }
  if (voicesLint.status === 'OK') break
  if (voicesFixes >= 2) return { show: A.show, escalated: 'research-lint-exhausted', stage: 'Research', fixes: voicesFixes, note: 'lint_voices 两轮修复后仍 BLOCKING，输出：\n' + voicesLint.note }
  voicesFixes++
  const fix = await agent(
    head('researcher', [
      '任务：修复 lint_voices 的 BLOCKING 后重写 ' + SEASON + '/voices.json。上一轮门禁输出（逐条修复，修完自跑 `python ' + REPO + '/scripts/lint_voices.py ' + SEASON + '/voices.json` 确认 BLOCKING 清零）：\n' + voicesLint.note,
    ]),
    { schema: STATUS_SCHEMA, label: 'voices-fix r' + voicesFixes, phase: 'Research', agentType: 'researcher', ...mo('researcher') },
  )
  if (!fix) return { show: A.show, escalated: 'voices-fix-failed', stage: 'Research', round: voicesFixes, note: 'researcher 修复 agent 失败（限流/崩溃）' }
  if (fix.status === 'BLOCKED') return { show: A.show, escalated: 'voices-fix', stage: 'Research', round: voicesFixes, reason: fix.blocker_reason }
}
log('Research 完成：voices.json 过 lint_voices 门禁')

// ---------- Research 收尾：voices_coverage 显式落盘（spec §11.3） ----------
// 降级知情链：researcher 契约允许交付有覆盖缺口的 voices.json（某议题查不到求职者声音，
// coverage=partial），但缺口必须显式落盘 voices-coverage.json 并在 log/返回对象标注——
// 不许静默截断（静默截断读起来像全覆盖，实际没有，reviewer 会按全覆盖评审求职者维度）。
// 判定：job-seeker ≥1 且 total ≥3 → full；job-seeker ≥1 → partial；job-seeker = 0 → none。
// M0 用 python -c 内联（不新建脚本文件），正式化留给 M3。
const COVERAGE_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['status', 'note', 'coverage'],
  properties: {
    status: { type: 'string', enum: ['OK', 'BLOCKED'] },
    note: { type: 'string' },
    blocker_reason: { type: 'string' },
    coverage: { type: 'string', enum: ['full', 'partial', 'none'] },
    total_voices: { type: 'integer' },
    job_seeker_voices: { type: 'integer' },
  },
}
const COV_CMD = 'python -c \'import sys,json,datetime; d=json.load(open(sys.argv[1])); vs=list(d.values()) if isinstance(d,dict) else [d]; js=sum(1 for v in vs if v.get("category")=="job-seeker"); cov="none" if js==0 else ("full" if len(vs)>=3 else "partial"); out=dict(checked_at=datetime.date.today().isoformat(), total_voices=len(vs), job_seeker_voices=js, coverage=cov, note="voice 总数 %d 条，其中求职者声音 %d 条" % (len(vs), js)); json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=2)\' ' + SEASON + '/voices.json ' + SEASON + '/voices-coverage.json'
const voicesCov = await agent(
  '你是门禁执行员。只做一件事：运行下面 1 条命令并如实转述结果（不要修改任何文件、不要评价、不要重写）：\n' +
  COV_CMD + '\n' +
  '然后 cat ' + SEASON + '/voices-coverage.json，把 coverage / total_voices / job_seeker_voices 如实填回返回字段。\n' +
  '判定：命令退出码 0 → status=OK；命令失败（voices.json 缺失/解析错等）→ status=BLOCKED，blocker_reason 写清退出码与错误输出。',
  { schema: COVERAGE_SCHEMA, label: 'voices-coverage', phase: 'Research', agentType: 'claude', ...mo('runner'), effort: 'max' },
)
if (!voicesCov) return { show: A.show, escalated: 'voices-coverage-failed', stage: 'Research', note: 'coverage 执行 agent 失败（限流/崩溃）——voices_coverage 未落盘不放行（spec §11.3 不许静默）' }
if (voicesCov.status === 'BLOCKED') return { show: A.show, escalated: 'voices-coverage', stage: 'Research', reason: voicesCov.blocker_reason }
if (voicesCov.coverage !== 'full') {
  log('voices_coverage=' + voicesCov.coverage + '——researcher 未找到足够求职者声音（求职者 ' + voicesCov.job_seeker_voices + ' 条 / 总 ' + voicesCov.total_voices + ' 条），reviewer 知情降权（spec §11.3），已落盘 ' + SEASON + '/voices-coverage.json')
} else {
  log('voices_coverage=full——voice 总 ' + voicesCov.total_voices + ' 条，其中求职者 ' + voicesCov.job_seeker_voices + ' 条，已落盘 ' + SEASON + '/voices-coverage.json')
}

// ---------- Hooks：hook-engineer 出钩子/金句/争议框架 ----------
phase('Hooks')
const hooks = await agent(
  head('hook-engineer', [
    '书源快照（只读）：' + SRC + '/',
    '议题清单：' + SEASON + '/season-plan.json',
    '产出：' + SEASON + '/arc.json，对齐 schemas/arc.schema.json',
    '任务：每期开场钩子/收尾金句/争议框架/伏笔映射（foreshadow_map 与 season-plan 的 foreshadow_due/payoff_due 对齐）。',
  ]),
  { schema: STATUS_SCHEMA, label: 'hooks', phase: 'Hooks', agentType: 'hook-engineer', ...mo('hookEngineer') },
)
if (!hooks) return { show: A.show, escalated: 'hooks-failed', stage: 'Hooks', note: 'hook-engineer agent 失败（限流/崩溃），无 arc.json 不得继续' }
if (hooks.status === 'BLOCKED') return { show: A.show, escalated: 'hooks', stage: 'Hooks', reason: hooks.blocker_reason }

// ---------- Slice：book-analyst × N 并行，每期产 episode-card.json ----------
// spec §3.3①：Phase A 三条腿（plan/research/hooks）汇于此——planner 定「讲什么」、
// hook-engineer 定「怎么起头收尾」、researcher 定「别人怎么说」；本骨架按 meta.phases
// 顺序执行，三腿并行化是后续优化项（并行会改变 lint_voices 门禁的时序，见报告）。
phase('Slice')
const sliceThunks = EPS.map(function (ep) {
  return function () {
    const epDir = SHOW + '/episodes/' + ep.slug
    return agent(
      head('book-analyst', [
        '你负责的议题定义（以落盘的 ' + SEASON + '/season-plan.json 为准，此处为调度副本）：' + JSON.stringify(ep),
        '三腿素材：' + SEASON + '/season-plan.json + ' + SEASON + '/arc.json + ' + SEASON + '/voices.json',
        '书源快照（只读，跨章切片只从快照取）：' + SRC + '/（outline.json / chapter-cards/*.json / glossary.json）',
        '产出：' + epDir + '/episode-card.json，对齐 schemas/episode-card.schema.json',
        '任务：按议题跨章切片，抽必讲要点 + voices 引用（voices_refs 必须在 voices.json 真实存在）；议题在书里找不到足够支撑、或跨章切片自相矛盾 → status=BLOCKED（spec §11.1 book-analyst 拉闸条件）。',
      ]),
      { schema: STATUS_SCHEMA, label: 'slice ' + ep.slug, phase: 'Slice', agentType: 'book-analyst', ...mo('bookAnalyst') },
    )
  }
})
const sliceOut = await parallel(sliceThunks)
for (let i = 0; i < sliceOut.length; i++) {
  const s = sliceOut[i]
  if (!s) return { show: A.show, escalated: 'slice-failed', stage: 'Slice', episode: EPS[i].slug, note: 'book-analyst agent 失败（限流/崩溃）——该期无 episode-card 不得继续' }
  if (s.status === 'BLOCKED') return { show: A.show, escalated: 'slice', stage: 'Slice', episode: EPS[i].slug, reason: s.blocker_reason }
}
log('Slice 完成：' + sliceOut.length + ' 张 episode-card')

// ---------- Bible：archivist 建 Season Bible 四件套 + trace ----------
phase('Bible')
const bible = await agent(
  head('archivist', [
    '输入：' + SEASON + '/season-plan.json + arc.json + voices.json + 全部 episodes/<slug>/episode-card.json',
    '书源快照（只读，glossary 提炼来源）：' + SRC + '/',
    '产出：' + SEASON + '/bible/ 四件套（glossary.json / voice-guide.md / arc-map.json / voices-index.json，对齐 schemas/season-bible.schema.json）+ trace 记录',
    '任务（Phase A 建季）：glossary 从书源快照 + episode-cards 提炼口播译名；arc-map 从 season-plan + arc 汇总伏笔登记（每期 foreshadow_due/payoff_due）；voices-index 初始为空；voice-guide.md **由 Lead 落笔**（spec §5）——你只核对其存在，绝不建占位/改内容（空占位会废掉缺失检查，writer 照读空 guide 无从退稿），若缺失 → status=BLOCKED。trace 至少一条 entry（建季 + 经验）。\n[裁定]：若 season-plan.json 与 episodes/ 目录/arc.json 期数或 slug 不一致，**以目录与 arc 为准**登记（Bible 不为无素材的期数背书），并在 note 中说明差异；不要因编排文件的历史残迹而拉闸。',
  ]),
  { schema: STATUS_SCHEMA, label: 'bible', phase: 'Bible', agentType: 'archivist', ...mo('archivist') },
)
if (!bible) return { show: A.show, escalated: 'bible-failed', stage: 'Bible', note: 'archivist agent 失败（限流/崩溃），Season Bible 未建成' }
if (bible.status === 'BLOCKED') return { show: A.show, escalated: 'bible', stage: 'Bible', reason: bible.blocker_reason }
log('Bible 完成：' + (bible.note || 'Season Bible 已建'))

return {
  show: A.show,
  episodes: EPS.map(function (e) { return e.slug }),
  voices_coverage: {
    coverage: voicesCov.coverage,
    total_voices: voicesCov.total_voices,
    job_seeker_voices: voicesCov.job_seeker_voices,
    file: SEASON + '/voices-coverage.json',
  },
  note: 'Phase A 完成：' + EPS.length + ' 期议题 + Season Bible' + (voicesCov.coverage === 'full' ? '' : '（voices_coverage=' + voicesCov.coverage + '，reviewer 知情降权）'),
}

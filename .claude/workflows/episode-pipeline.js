// .claude/workflows/episode-pipeline.js
// devpodcast Phase B：单期制作（spec §3.2 / §3.3②③）。Task 15 骨架。
// 阶段链：Write(+4 linter 门禁) → Produce → Revise(+定稿复跑门禁) → TTS → AudioQA(回环 ≤2)
//         → Review(6 维并行回环 ≤3) → Archive。
// args 契约：{ show: "vllm-podcast", ep_id: "ep01", target_minutes: 35 }
//   show：节目名；ep_id：episodes/ 下的目录名或 epNN 前缀（解析器用 ls 匹配唯一目录）；
//   target_minutes：目标时长（lint_script 时长预算 / audio_qa 期望时长 / writer 字数预算共用）。
// 配置兜底与 bad-args 拉闸规则同 season-pipeline（repo2book 教训：传了 args 但解析不出
//   关键字段 → 拉闸，绝不静默默认；完全未传 args 才允许脚本内 CFG）。
// 逃生舱（spec §11.1）：任一 agent 返回 BLOCKED → 立即中止升级 Lead；
//   宁可拉闸，不要产出错误成果一路跑到底。TTS 是必经站（spec §11.3），无降级后门。
// 公共件（真实可用，非摆设）：STATUS_SCHEMA / head(role, ctx) / ESC / runLints()。
// 工作流无模块系统（repo2book 同），公共件按需内联；与 season-pipeline.js 的公共件保持同构。

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

// ---------- args 解析：CFG 兜底 + bad-args 拉闸 ----------
const CFG = { show: 'vllm-podcast', ep_id: 'ep01', target_minutes: 35 }  // 仅完全未传 args 的手工调试场景使用

function validArgs(x) {
  return !!x &&
    typeof x.show === 'string' && x.show.length > 0 &&
    typeof x.ep_id === 'string' && x.ep_id.length > 0 &&
    typeof x.target_minutes === 'number' && isFinite(x.target_minutes) && x.target_minutes > 0
}

let A = (typeof args !== 'undefined' && args) ? args : null
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = null } }  // named 调用 args 可能被字符串化
if (A && !validArgs(A)) A = null
if (!A) {
  if (typeof args !== 'undefined' && args) {
    return { escalated: 'bad-args', note: 'args 存在但解析不出关键字段（show/ep_id 需非空字符串、target_minutes 需正数）——拒绝 CFG 回退，请检查发车参数' }
  }
  A = CFG
}

const REPO = A.repo_root || '/mnt/e/Laboratory/Devpodcast'
const SHOW = REPO + '/shows/' + A.show
const SEASON = SHOW + '/season'
const TARGET = A.target_minutes

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

// head(role, ctx)：注入角色契约路径 + 产物路径 + 逃生舱文案。
// role 为 null 的确定性站点（TTS / 门禁 / 质检执行）无角色契约文件，只注入 ctx + ESC。
function head(role, ctxLines) {
  const lines = []
  if (role) lines.push('你的角色契约：' + REPO + '/.claude/agents/' + role + '.md —— **先读它**，严格遵守其中所有铁律。')
  lines.push(Array.isArray(ctxLines) ? ctxLines.join('\n') : String(ctxLines))
  lines.push(ESC)
  return lines.join('\n')
}

// 确定性门禁执行：workflow 沙箱无文件系统/Bash，借一个「只跑命令、不做判断」的 agent
// 把 CLI 的退出码与完整输出如实带回（spec §12.1：确定性 linter 前置于评审）。
async function runLints(cmds, label, phaseName) {
  return agent(
    '你是门禁执行员。只做一件事：依次运行下面 ' + cmds.length + ' 条命令——**全部跑完**（不要因一条失败跳过其余；不要读产物内容、不要评价、不要修改任何东西）：\n' +
    cmds.join('\n') + '\n' +
    '把每条命令的退出码与完整输出带回 note（命令不存在/报错也照实记录）。\n' +
    '判定：全部退出码 0 → status=OK；任一条退出码 ≠ 0（linter 找到 BLOCKING 级问题，或命令本身失败）→ status=BLOCKED，blocker_reason 写清是哪条命令、退出码多少。',
    { schema: STATUS_SCHEMA, label: label, phase: phaseName, agentType: 'claude', ...mo('runner'), effort: 'max' },
  )
}

// ---------- 预解析：定位本期目录（workflow 沙箱无文件系统，借 bash agent 做机械匹配） ----------
// ep_id 契约：episodes/ 下的目录名（ep01-<slug>）或 epNN 前缀均可；解析出唯一目录后，
// 所有阶段的产物绝对路径都由 EP 派生（head() 注入）。
const EP_RESOLVE_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['status', 'note', 'dir'],
  properties: {
    status: { type: 'string', enum: ['OK', 'BLOCKED'] },
    note: { type: 'string' },
    blocker_reason: { type: 'string' },
    dir: { type: 'string' },
  },
}
const epResolve = await agent(
  '只做一件事：解析本期目录（不要读文件内容、不要评价、不要修改任何东西）。\n' +
  '运行 `ls ' + SHOW + '/episodes/` 并带回实际输出。\n' +
  '判定规则（机械匹配，勿加判断）：\n' +
  '  1. 输出里恰好有名为 ' + A.ep_id + ' 的目录 → OK，dir 填它；\n' +
  '  2. 否则找以 ' + A.ep_id + '- 开头的目录：唯一一个 → OK，dir 填它；多个 → BLOCKED（blocker_reason 写「ambiguous」，note 列出全部候选）；\n' +
  '  3. 一个都没有 → BLOCKED（blocker_reason 写「not-found」，note 写 ls 的实际输出——可能是 Phase A 未跑，或 ep_id 拼错）。',
  { schema: EP_RESOLVE_SCHEMA, label: 'ep-resolve', phase: 'Write', agentType: 'claude', ...mo('runner'), effort: 'max' },
)
if (!epResolve) return { show: A.show, ep_id: A.ep_id, escalated: 'ep-resolve-failed', stage: 'Write', note: '目录解析 agent 失败（限流/崩溃）' }
if (epResolve.status === 'BLOCKED') return { show: A.show, ep_id: A.ep_id, escalated: 'ep-not-found', stage: 'Write', reason: epResolve.blocker_reason, note: epResolve.note }
const EP = SHOW + '/episodes/' + epResolve.dir
const AUDIO = EP + '/audio'
const WRITER_INPUTS = '四份素材（缺一不写）：' + EP + '/episode-card.json、' + SEASON + '/voices.json、' + SEASON + '/arc.json、' + SEASON + '/bible/（voice-guide.md ★强制复用 + glossary.json + arc-map.json）'
const LINT_CMDS = [
  'python ' + REPO + '/scripts/lint_script.py ' + EP + '/script.md --voices ' + SEASON + '/voices.json --target-minutes ' + TARGET,
  'python ' + REPO + '/scripts/lint_punct.py ' + EP + '/script.md',
  'python ' + REPO + '/scripts/lint_anchors.py ' + EP + ' ' + SHOW,
  'python ' + REPO + '/scripts/lint_trace.py ' + EP + ' ' + SEASON + '/voices.json',
]

// ---------- Write：writer 主笔（唯一有权写 script.md）+ 四 linter 门禁（回环 ≤2 轮修复） ----------
phase('Write')
let writeLedger = ''   // 上轮门禁 BLOCKING 输出（修复轮依据）
for (let w = 1; w <= 3; w++) {   // w=1 初稿；w=2/3 为门禁修复轮（回环 ≤2 轮）
  const writeV = await agent(
    head('writer', [
      '本期目录：' + EP,
      WRITER_INPUTS,
      '书源快照（只读）：' + SHOW + '/source-book/',
      '目标时长：' + TARGET + ' 分钟（时长预算按此计算，约 ' + Math.round(TARGET * 60 * 4) + ' 字正文；单段 ≤200 字；任一方 turn 占比 ≥30%）',
      '任务：' + (w === 1
        ? '写初稿 ' + EP + '/script.md（你是全季唯一有权写它的人，spec §4.1 硬规则 1）。'
        : '修复门禁 BLOCKING 后修订 ' + EP + '/script.md。上一轮四 linter 输出（逐条修复，修完自跑 lint_script 确认 BLOCKING 清零）：\n' + writeLedger) +
      '\n完成后自跑你契约的「收工自检」清单。',
    ]),
    { schema: STATUS_SCHEMA, label: 'write r' + w, phase: 'Write', agentType: 'writer', ...mo('writer') },
  )
  if (!writeV) return { show: A.show, ep_id: A.ep_id, escalated: 'write-failed', stage: 'Write', round: w, note: 'writer agent 失败（限流/崩溃），无 script.md 不得继续' }
  if (writeV.status === 'BLOCKED') return { show: A.show, ep_id: A.ep_id, escalated: 'write', stage: 'Write', round: w, reason: writeV.blocker_reason }
  // 四 linter 门禁（spec §12.1）：lint_script / lint_punct / lint_anchors / lint_trace
  const gate = await runLints(LINT_CMDS, 'write-lint r' + w, 'Write')
  if (!gate) return { show: A.show, ep_id: A.ep_id, escalated: 'write-lint-failed', stage: 'Write', round: w, note: '门禁执行 agent 失败（限流/崩溃）——四 linter 未执行不放行' }
  if (gate.status === 'OK') { log('Write 通过四 linter 门禁（第 ' + w + ' 轮）'); break }
  if (w === 3) return { show: A.show, ep_id: A.ep_id, escalated: 'write-lint-exhausted', stage: 'Write', rounds: w, note: '四 linter 经 2 轮修复仍 BLOCKING——升级 Lead 裁定（改提示词 / 砍期）。输出：\n' + gate.note }
  writeLedger = gate.note
  log('Write 第 ' + w + ' 轮门禁 BLOCKING，回 writer 修复')
}

// ---------- Produce：producer 只提意见，绝不改稿 ----------
phase('Produce')
const produce = await agent(
  head('producer', [
    '本期目录：' + EP,
    '只读输入：' + EP + '/script.md + episode-card.json + ' + SEASON + '/voices.json + arc.json + bible/voice-guide.md',
    '产出：' + EP + '/production-notes.md，对齐 schemas/production-notes.schema.json',
    '任务：口播工程师视角提意见（换气 / 双声线节奏 / 引述前停顿 / 时长预算；每条意见带 script 行号）。**绝不修改 script.md**——连 typo 都只写进 note（spec §4.1 硬规则 2）。',
  ]),
  { schema: STATUS_SCHEMA, label: 'produce', phase: 'Produce', agentType: 'producer', ...mo('producer') },
)
if (!produce) return { show: A.show, ep_id: A.ep_id, escalated: 'produce-failed', stage: 'Produce', note: 'producer agent 失败（限流/崩溃）' }
if (produce.status === 'BLOCKED') return { show: A.show, ep_id: A.ep_id, escalated: 'produce', stage: 'Produce', reason: produce.blocker_reason }

// ---------- Revise：writer 逐条采纳/反驳 producer 意见，定稿；复跑四 linter 一次 ----------
phase('Revise')
const revise = await agent(
  head('writer', [
    '本期目录：' + EP,
    WRITER_INPUTS,
    '输入：' + EP + '/production-notes.md（producer 意见）',
    '任务：用 superpowers:receiving-code-review 方法逐条处理 producer 意见（采纳的改、反驳的写明理由），定稿 ' + EP + '/script.md。完成后自跑「收工自检」清单。',
  ]),
  { schema: STATUS_SCHEMA, label: 'revise', phase: 'Revise', agentType: 'writer', ...mo('writer') },
)
if (!revise) return { show: A.show, ep_id: A.ep_id, escalated: 'revise-failed', stage: 'Revise', note: 'writer agent 失败（限流/崩溃），未定稿' }
if (revise.status === 'BLOCKED') return { show: A.show, ep_id: A.ep_id, escalated: 'revise', stage: 'Revise', reason: revise.blocker_reason }
// 定稿后四 linter 复跑一次（不进回环：修复预算已在 Write 阶段消耗；TTS 前必须干净，不让带病脚本烧 GPU）
const gate2 = await runLints(LINT_CMDS, 'revise-lint', 'Revise')
if (!gate2 || gate2.status === 'BLOCKED') {
  return { show: A.show, ep_id: A.ep_id, escalated: 'revise-lint-gate', stage: 'Revise', note: (gate2 ? '定稿后四 linter 仍 BLOCKING，升级 Lead 裁定：\n' + gate2.note : '门禁执行 agent 失败（限流/崩溃）——四 linter 未执行不放行') }
}
log('Revise 定稿通过四 linter')

// ---------- TTS：tts-engine 本地 GPU 合成（spec §7） ----------
// tts-engine 无角色提示词（spec §7 契约在文档 + scripts/tts.py），head(null, ctx) 只注入任务与逃生舱。
phase('TTS')
const tts = await agent(
  head(null, [
    '任务：把 ' + EP + '/script.md 合成 ' + AUDIO + '/episode.wav + ' + AUDIO + '/segments/（对齐 scripts/tts.py 的 AudioBundle 契约）。',
    '方式：优先 scripts/tts.py 的 DialogueTTSProvider（MOSS-TTSD：script → [S1]/[S2] 标签串 → 单次生成；1s ≈ 12.5 tokens 换算 --max_new_tokens 与时长预算；多说话人开 --sample_rate_normalize，始终开 --text_normalize）。模型/环境接入以 Task 17 落地的入口为准。',
    '说话人映射：' + SHOW + '/devpodcast.json 的 tts.voice_map（S1=老张 / S2=阿凯，voice-samples/ 音色样本）。',
    '目标时长：' + TARGET + ' 分钟（超过 20% 余量会被 audio-qa BLOCKING）。',
    '拉闸（spec §11.1）：音色样本质量不足 / 显存不够 / 模型加载失败 → status=BLOCKED。**TTS 是必经站**（spec §11.3）：环境没配好 = BLOCKED，不给「先出脚本、音频待补」的后门。',
  ]),
  { schema: STATUS_SCHEMA, label: 'tts', phase: 'TTS', agentType: 'claude', ...mo('tts'), effort: 'max' },
)
if (!tts) return { show: A.show, ep_id: A.ep_id, escalated: 'tts-failed', stage: 'TTS', note: 'tts 执行 agent 失败（限流/崩溃）' }
if (tts.status === 'BLOCKED') return { show: A.show, ep_id: A.ep_id, escalated: 'tts', stage: 'TTS', reason: tts.blocker_reason }

// ---------- AudioQA：audio_qa.py 质检，BLOCKING 回环 ≤2 轮（时长超 → writer 改稿；削波等 → tts 重合成） ----------
phase('AudioQA')
const QA_CMD = 'python ' + REPO + '/scripts/audio_qa.py ' + AUDIO + '/episode.wav ' + AUDIO + '/audio-qa.json ' + TARGET
const QA_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['status', 'note', 'issues', 'route'],
  properties: {
    status: { type: 'string', enum: ['OK', 'BLOCKED'] },
    note: { type: 'string' },
    blocker_reason: { type: 'string' },
    issues: { type: 'array', items: { type: 'string' } },
    route: { type: 'string', enum: ['writer', 'tts', 'both', 'none'] },
  },
}
async function runAudioQA(qaRound) {
  return agent(
    '你是质检执行员。只做一件事：运行下面命令并如实转述报告（不要修改任何文件、不要评价、不要重写）：\n' +
    QA_CMD + '\n' +
    '然后 Read ' + AUDIO + '/audio-qa.json，把 issues 数组逐条原样转述到 issues 字段。\n' +
    'route 判定（机械规则，勿加判断）：issues 里「时长」开头的 BLOCKING → route 含 writer；「削波」开头的 BLOCKING → route 含 tts；两者都有 → both；无 BLOCKING → none。\n' +
    '无 BLOCKING → status=OK；有 BLOCKING → status=BLOCKED（blocker_reason 写哪类问题）。',
    { schema: QA_SCHEMA, label: 'audio-qa r' + qaRound, phase: 'AudioQA', agentType: 'claude', ...mo('runner'), effort: 'max' },
  )
}
let qaFixes = 0
for (;;) {
  const qa = await runAudioQA(qaFixes + 1)
  if (!qa) return { show: A.show, ep_id: A.ep_id, escalated: 'audio-qa-failed', stage: 'AudioQA', note: '质检执行 agent 失败（限流/崩溃）——audio-qa 未执行不放行' }
  if (qa.status === 'OK') { log('AudioQA 通过'); break }
  if (qaFixes >= 2) return { show: A.show, ep_id: A.ep_id, escalated: 'audio-qa-exhausted', stage: 'AudioQA', fixes: qaFixes, issues: qa.issues, note: 'audio-qa BLOCKING 经 2 轮修复未过——升级 Lead（spec §11.2：tts-engine ↔ audio-qa 回环上限 2）' }
  qaFixes++
  const route = qa.route || 'tts'
  if (route === 'writer' || route === 'both') {
    const fixW = await agent(
      head('writer', [
        '任务：audio-qa BLOCKING 为**时长超限**（目标 ' + TARGET + ' 分钟）。压缩 ' + EP + '/script.md 正文到时长预算内（约 ' + Math.round(TARGET * 60 * 4) + ' 字；删冗余、不砍必讲机制），保持双声线平衡与「我不知道」纪律。完成后自跑「收工自检」。\n质检 issues：' + JSON.stringify(qa.issues),
      ]),
      { schema: STATUS_SCHEMA, label: 'audio-qa-fix-writer r' + qaFixes, phase: 'AudioQA', agentType: 'writer', ...mo('writer') },
    )
    if (!fixW || fixW.status === 'BLOCKED') return { show: A.show, ep_id: A.ep_id, escalated: 'audio-qa-fix-writer', stage: 'AudioQA', round: qaFixes, reason: (fixW && fixW.blocker_reason) || 'writer 改稿 agent 失败（限流/崩溃）' }
  }
  if (route === 'tts' || route === 'both') {
    const fixT = await agent(
      head(null, [
        '任务：audio-qa BLOCKING（削波/静音/响度类）。重合成 ' + AUDIO + '/episode.wav：按上轮参数调整（削波 → 降增益/检查响度归一；时长 → 检查 tokens 换算），重新产出 ' + AUDIO + '/episode.wav + ' + AUDIO + '/segments/。\n质检 issues：' + JSON.stringify(qa.issues),
      ]),
      { schema: STATUS_SCHEMA, label: 'audio-qa-fix-tts r' + qaFixes, phase: 'AudioQA', agentType: 'claude', ...mo('tts'), effort: 'max' },
    )
    if (!fixT || fixT.status === 'BLOCKED') return { show: A.show, ep_id: A.ep_id, escalated: 'audio-qa-fix-tts', stage: 'AudioQA', round: qaFixes, reason: (fixT && fixT.blocker_reason) || '重合成 agent 失败（限流/崩溃）' }
  }
  log('AudioQA 第 ' + qaFixes + ' 轮修复完成，复检中')
}

// ---------- Review：reviewer 6 维并行评审，BLOCKING 回环 writer ≤3 轮 ----------
phase('Review')
// 6 维（spec §12.3）：事实准确 / 批判强度 / 口播可懂 / 双声线平衡 / 求职者共鸣 / 原声保真
const DIMS = [
  ['factual_accuracy', '事实准确：每个技术断言能在 episode-card 找到支撑；数字不漂移；「我不知道」处是真的不知道还是回避'],
  ['critical_depth', '批判强度：是不是只有赞美？争议有没有真展开（claim/counter 都站得住）？反方立场有没有被公平呈现？批判有没有靶子（具体的人/场景）？'],
  ['spoken_clarity', '口播可懂：闭眼只听能不能跟上？有没有依赖视觉的表述？术语首现有没有口头解释？'],
  ['voice_balance', '双声线平衡：两人是不是各有性格？有没有一方沦为「嗯嗯对对」的捧哏（任一方 turn 占比 <30%）？'],
  ['job_seeker_resonance', '求职者共鸣：求职视角落到具体场景了吗？还是空泛的「这个技术很重要」？配额（≤2 处）与「必须挂真实 voices」守住没？'],
  ['quote_fidelity', '原声保真：引述有没有被曲解？claim vs verified 层次保持（community-only 说成事实 = 事故）？匿名化做到？引述边界标注？'],
]
const DIM_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['pass', 'issues'],
  properties: {
    pass: { type: 'boolean' },
    issues: { type: 'array', items: { type: 'object', additionalProperties: false,
      required: ['problem', 'suggested_fix', 'rationale', 'blocking'],
      properties: {
        problem: { type: 'string' },
        suggested_fix: { type: 'string' },
        rationale: { type: 'string' },
        blocking: { type: 'boolean' },
      } } },
  },
}
let reviewV = null
let reviewIssues = []
for (let r = 1; r <= 3; r++) {
  const dimThunks = DIMS.map(function (dim) {
    return function () {
      return agent(
        head('reviewer', [
          '评审对象：' + EP + '/script.md（当前稿）',
          '核对基准：' + EP + '/episode-card.json、' + SEASON + '/voices.json、' + SEASON + '/arc.json、' + SEASON + '/bible/voice-guide.md + arc-map.json',
          '音频参考（若有）：' + AUDIO + '/episode.wav + audio-qa.json（audio-qa 的 issues 直接引用，不重复质检）',
          '本轮限定：第 2 轮起只看上轮 fail 维度；第 3 轮只看仍未清的阻断项。',
          '上轮意见：' + (reviewIssues.length ? JSON.stringify(reviewIssues) : '（首轮，无）'),
          '任务：只从「' + dim[1] + '」维度评审。产物：' + EP + '/reviews/r' + r + '-' + dim[0] + '.json（对齐你契约的产物格式）。返回 pass 与 issues（每条给 problem + evidence 行号 + suggested_fix + rationale + blocking）。**退稿必须指到契约**（voice-guide 纪律 / episode-card 支撑 / voices 保真 / 格式契约），无权因风格偏好退稿。',
          '**run-ledger.json 只由 factual_accuracy 维写**（' + EP + '/reviews/run-ledger.json：轮数 + 本轮 verdict + 各维 pass/fail；其余维不要碰它——避免并行写同一文件的竞态）。',
        ]),
        { schema: DIM_SCHEMA, label: 'review:' + dim[0] + ' r' + r, phase: 'Review', agentType: 'reviewer', ...mo('reviewer') },
      )
    }
  })
  const dimOut = await parallel(dimThunks)
  if (dimOut.some(function (d) { return !d })) return { show: A.show, ep_id: A.ep_id, escalated: 'review-agents-failed', stage: 'Review', round: r, note: '部分评审维 agent 失败（限流/崩溃）——评审未完成，不假通过' }
  reviewIssues = dimOut.flatMap(function (d) { return (d.issues || []).slice() })
  const blocking = reviewIssues.filter(function (i) { return i.blocking })
  if (dimOut.every(function (d) { return d.pass }) && blocking.length === 0) {
    reviewV = { verdict: 'APPROVED', round: r, issues: reviewIssues }
    log('Review 第 ' + r + ' 轮通过（6 维全 pass）')
    break
  }
  if (r === 3) {
    return { show: A.show, ep_id: A.ep_id, escalated: 'review-exhausted', stage: 'Review', rounds: 3, issues: reviewIssues, note: '3 轮评审后仍有关键问题——升级 Lead。依据 reviewer 契约附：哪些维度 3 轮内改不动 + 已尝试的方向（Lead 决定改提示词还是砍期）。' }
  }
  const rev = await agent(
    head('writer', [
      '任务：评审 REVISE（第 ' + r + ' 轮）。用 superpowers:receiving-code-review 方法逐条处理（采纳或带理由反驳），改 ' + EP + '/script.md。\n' +
      '本轮 blocking 清单：\n' + JSON.stringify(blocking) +
      '\n完成后自跑「收工自检」清单。',
    ]),
    { schema: STATUS_SCHEMA, label: 'revise-review r' + r, phase: 'Review', agentType: 'writer', ...mo('writer') },
  )
  if (!rev) return { show: A.show, ep_id: A.ep_id, escalated: 'review-revise-failed', stage: 'Review', round: r, note: 'writer 修订 agent 失败（限流/崩溃）' }
  if (rev.status === 'BLOCKED') return { show: A.show, ep_id: A.ep_id, escalated: 'review-revise', stage: 'Review', round: r, reason: rev.blocker_reason }
  reviewV = { verdict: 'REVISE', round: r }
  log('Review 第 ' + r + ' 轮 REVISE：' + blocking.length + ' 个阻断项回 writer')
}

// ---------- Archive：archivist 归档 + season_bible register 回写 arc-map + shownotes ----------
phase('Archive')
const archive = await agent(
  head('archivist', [
    '归档对象：' + EP + '/ 全部产物（episode-card / script.md / production-notes / audio/audio-qa.json / reviews/）',
    'Season Bible：' + SEASON + '/bible/（arc-map.json / voices-index.json / glossary.json）；trace：' + SHOW + '/trace',
    '任务（按你契约的「工作流程」）：\n' +
    '1. 核对伏笔：先 Read ' + EP + '/episode-card.json 取 episode_id 字段（arc-map 的键，如 ep01）；跑 `python ' + REPO + '/scripts/season_bible.py due ' + SEASON + '/bible/arc-map.json <episode_id>` 取本期应回收项，逐一在 script.md 确认回收；未回收的点名记录；连续两期欠账 → status=BLOCKED。\n' +
    '2. 回写 arc-map：`python ' + REPO + '/scripts/season_bible.py register ' + SEASON + '/bible/arc-map.json <episode_id> \'{"payoff_due": [...]}\'`（字段按契约；先读现状，只增量）。\n' +
    '3. 回写 voices-index：解析 script.md 的 {{voice:...}} 全部引用追加台账（先读现状只增量）。\n' +
    '4. 补录 glossary：本期新术语口播译名。\n' +
    '5. 写 shownotes.md：' + EP + '/shownotes.md。\n' +
    '6. 写 trace：`python ' + REPO + '/scripts/archivist.py ' + SHOW + '/trace log "<msg>" <kind>`（本期归档 + 跨期经验）。\n' +
    '铁律：只回写 bible 与 trace，**不改任何 episode 产物**（script / episode-card / production-notes 都是别人的领土）。',
  ]),
  { schema: STATUS_SCHEMA, label: 'archive', phase: 'Archive', agentType: 'archivist', ...mo('archivist') },
)
if (!archive) return { show: A.show, ep_id: A.ep_id, escalated: 'archive-failed', stage: 'Archive', note: 'archivist agent 失败（限流/崩溃）' }
if (archive.status === 'BLOCKED') return { show: A.show, ep_id: A.ep_id, escalated: 'archive', stage: 'Archive', reason: archive.blocker_reason }
log('Archive 完成：' + (archive.note || ''))

return { show: A.show, ep_id: A.ep_id, dir: epResolve.dir, review: reviewV, note: 'Phase B 完成：' + epResolve.dir }

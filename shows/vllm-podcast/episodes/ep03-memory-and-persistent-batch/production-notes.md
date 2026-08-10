# production-notes — ep03-memory-and-persistent-batch（口播工程师意见 · 三人版 script 第 1 轮）

> 本文件全部内容均为意见，不包含任何改好的稿子正文。script_line 对应**当前** script.md（2026-08-09 三人版，359 行 / 179 轮）的真实行号。
> 本文件取代旧双人稿时代的 production-notes——旧稿 81/80 轮两人交替，行号已整体失效（旧稿存档见 script_2person.bak.md）。
> TTS 语义分支：`devpodcast.json` 中 `tts.provider = indextts2`（单句合成，逐 turn 独立生成）——停顿由模型从标点自主生成，以下停顿建议均为**软提示**（断句 / 加引出句 / 改标点），不写死毫秒。稿内现有 3 处 `<break 300ms>`（L175/L185/L203）均为术语后垫停、前后子句均 ≥14 字，符合 voice-guide 节奏纪律 3，予以保留。轮间 100ms 静音由 pipeline 拼接时统一插入，无需在稿面标注。
> 校验基线：`lint_script.py` / `lint_punct.py` / `lint_trace.py` 对当前 script.md 全部 exit 0（无超 200 字段落、无未闭合标记、voice 引用全部存在、三方占比全过 25% 线）。

## 旧双人稿 notes 去向（三人版新稿已吸收，writer 无需再动）

- 旧「金句被长引述挤在尾巴」→ 当前 L319 引述收束后，金句已拆成独立拍 L321（「这话得品一品：……」），解决。拆分带来了新副作用（S2 三连轮），见意见〔2〕。
- 旧「三段式分配快速对答节奏平」→ 当前 L147–L181 段阿哲五度喊停（L149/L153/L161/L169/L177），快答被拆开，解决。
- 旧「voice-026 引述冒号直贴」→ 当前 L329 已改「他们承认——」，与全稿引述节奏统一，解决。

## 四类审计结论（本轮）

| 类别 | 结论 | 说明 |
|---|---|---|
| 1. 口播换气 | 无 warning | lint exit 0，全稿无超 200 字段落；最长 7 段均为引述 turn（L309=179 / L59=175 / L319=174 / L11=156 / L301=151 / L139=148 / L281=144），内部句号/问号断点充分。L309/L319 数字密集，建议合成后抽查语速，见意见〔5〕 |
| 2. 三方节奏 | 1 条 warning + 1 条 suggestion | L325–L341 连续 9 轮无 S3，恰是全期争议落锤段（集群短板引述/判据/面试题回扣），见意见〔1〕；L317–L321 S2 三连轮约 230 字无人接话，见意见〔2〕。其余：无连续 5 轮以上 <40 字乒乓短句（自动扫描确认）；turn 占比 S1 25.1% / S2 49.2% / S3 25.7%，过线但余量极薄，见意见〔6〕 |
| 3. 引述前停顿 | 无问题 | 9 处 voice 嵌入（L11/L59/L139/L281/L289/L301/L309/L319/L329）全部带「——」收尾的引出句，引述后均有独立转述短句锚定边界。见意见〔4〕 |
| 4. 时长预算 | 无超标 | 口播文本 9450 字，按 4 字/秒 ≈ 39.4 分钟，加 179 轮×100ms 轮间静音 ≈ 39.7 分钟，低于 target×1.15（40.25）。本季实测语速 5.2–5.9 字/秒，成片预计 27–31 分钟，无超时风险。见意见〔7〕 |

## 意见清单（按严重级）

### warning

**〔1〕script_line 337 — warning（三方节奏：阿哲 9 连轮缺席，落在全期落锤段）**
阿哲最后开口在 L323（问 FutureAGI 数据硬核吗），再回到对话已是 L343——中间 L325–L341 连续 9 轮全是 S1↔S2 往返。这段恰好是全期争议的落锤：voice-026 集群短板引述（L329）、「前缀共享率盖不盖得住碎片开销」的判据（L337）、开场面试题的回扣（L341）。按 voice-guide 难点动线，「阿哲复述确认」必须真实存在，而读者代言人在全期最重要的 resolution 段消失约两分钟；L343 阿哲回归句直接跳进「16 这个数怎么定的」，对判据没有确认拍。建议在 L337（判据）之后或 L341（面试题回扣）之后插一个阿哲的复述确认短 turn（一句话即可，如把判据折成「共享率盖得住碎片就值、盖不住就往小调」式的复述），把 9 连轮断成两段。插哪儿、写什么由 writer 裁。

### suggestion

**〔2〕script_line 319 — suggestion（三方节奏：S2 三连轮，约 230 字同一声音无间断）**
L317（给 170 倍泼冷水）→ L319（voice-030 引述，174 字）→ L321（「这话得品一品」金句点评）连续三轮都是 S2。轮间只有 100ms 拼接静音，三人节目里听感是一段约 40–60 秒的单人陈述（按 4 字/秒约 58 秒，按本季实测语速约 42 秒）。这是旧双人稿 note「金句别挤在引述尾巴上」拆分修复的副作用——拆分方向本身是对的，但三人版里拆出来的拍可以交给别人接。建议把 L321（点评）或 L317（冷水）其中一拍让给 S1 或 S3（如 S1 递一句「这话怎么讲」、或 S3 接一句反应），把三连断成 2+1。让谁接、怎么写由 writer 裁。

**〔3〕script_line 163 — suggestion（发音表缺口：本期新术语在 indextts2 下未验证）**
本期出现一批 pronunciation.json 未收录、或仅有 FireRed 时代试听结论的记号：PD 分离（L163）、lookahead（L167）、Input Batch（L209）、worker（L221 起多处）、update states（L231）、block table（L247）、commit（L251/L265）、Triton（L255/L265/L349）、CUDA graph（L263/L353——CUDA 会触发「库达」替换，graph 未验证）、GQA（L293）、UCX（L301 两处）、Mistral（L301）、P90/p50/p99（L309/L311 共 4 处）、llm-d（L309/L325/L329）、Qwen-32B 与 H100（L309）、Groundedness（L319 两处）、FutureAGI（L319/L323）、RAG（L319）、O(1)/O(n)（L81/L83/L101——带括号符号，被读成「括号一」或吞掉的风险最高）、128K（L35/L37）。建议合成前先对 L81、L163、L293、L301、L309、L319 做摘录级试听，读错再补发音表条目；writer 无需改稿，由发音表在合成前替换。

### info

**〔4〕script_line 11 — info（引述前停顿审计：无问题）**
9 处 voice 嵌入逐一核过：引出句全部以「——」收尾（是这么说的——／是这么讲的——／是这么问的——×2／他是这么说的——／根因是——／贴的数字是——／结论是——／承认——），给模型最强标点停顿信号；引述结束后均有独立转述短句锚定边界（原话大概这个意思。／大意就是这样。／他给的就是这组数。）。旧双人稿 note 的 voice-026 引出问题在当前 L329 已解决。本条仅记录确认。

**〔5〕script_line 309 — info（换气审计：无超线段；数字密集段合成后抽查）**
全稿无超 200 字段落（lint exit 0）。最长 7 段均为引述 turn（字数见上表第 1 行），内部句号/问号级断点充分，读感可承受，均不拆。L309 数字串最密（16 块 H100／Qwen-32B／150 客户／6000 token／93 秒／0.542 秒／170 倍连排），L319 次之（0.55／0.88／0.69）——合成后抽查这两段语速，若偏快再考虑在「差了 170 倍」前断句，改不改由 writer 定。

**〔6〕script_line 7 — info（三方节奏审计：占比过线但余量极薄）**
179 轮：S1 45（25.1%）/ S2 88（49.2%）/ S3 46（25.7%）。S1 只富余 0.1 个百分点——删 1 个 S1 短 turn 即穿 25% lint 线（44/178=24.7%）；S3 最多删 1 个短 turn。自动扫描：无连续 5 轮以上 <40 字乒乓短句；同 speaker 连轮全稿仅 L317–L321 一处（见意见〔2〕）。另记录：S1 在 L67–L83 缺席 9 轮（块池/链表段），但阿哲四度喊停（L69/L73/L77/L81）补位、难点动线成立，不算失衡。提示 writer：后续删改勿删穿 S1/S3 短 turn，要减字优先从 S2 讲解段（字数占比 66.9%）。

**〔7〕script_line 359 — info（时长审计：无超标）**
口播文本 9450 字（179 轮，已剥离 voice 标记 / `<break>` / speaker 标签）。按 4 字/秒规则估算 ≈ 39.4 分钟，加轮间静音 ≈ 39.7 分钟，低于 target×1.15（40.25）——规则余量约 0.5 分钟偏薄，但不触发 warning。实测校准：本季 IndexTTS-2 已成片三期的真实语速为 5.2–5.9 字/秒（ep01 7973 字→24.0 分钟、ep02 9367 字→26.6 分钟、ep03 旧双人稿 8044 字→25.7 分钟），按此区间本期成片预计 27–31 分钟，与 ep01/ep02 同区间，无超时风险、无需删减。

## 附：机器可读版（对齐 schemas/production-notes.schema.json）

```json
[
  {"ep_dir": "shows/vllm-podcast/episodes/ep03-memory-and-persistent-batch", "script_line": 337,
   "note": "阿哲 9 连轮缺席落在全期落锤段：L323 之后 S3 直到 L343 才再开口，L325–L341 全是 S1↔S2，且这段含 voice-026 集群短板引述（L329）、争议判据（L337）、开场面试题回扣（L341）。按 voice-guide 难点动线，建议在 L337 后或 L341 后插一个阿哲复述确认短 turn（一句话即可），把 9 连轮断成两段。插哪儿、写什么由 writer 裁", "severity": "warning"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep03-memory-and-persistent-batch", "script_line": 319,
   "note": "S2 三连轮：L317（泼冷水）→L319（voice-030 引述 174 字）→L321（金句点评）约 230 字同一声音无间断，轮间仅 100ms 拼接静音，听感是 40–60 秒单人陈述。这是旧双人稿 note 拆分修复的副作用——拆分方向对，但拆出的拍可交给别人。建议把 L321 或 L317 其中一拍让给 S1/S3 接一句，断成 2+1。让谁接由 writer 裁", "severity": "suggestion"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep03-memory-and-persistent-batch", "script_line": 163,
   "note": "发音表缺口：PD 分离（L163）、lookahead（L167）、Input Batch（L209）、worker（L221 起）、update states（L231）、block table（L247）、commit（L251/L265）、Triton（L255/L265/L349）、CUDA graph（L263/L353）、GQA（L293）、UCX/Mistral（L301）、P90/p50/p99（L309/L311）、llm-d/Qwen-32B/H100（L309）、Groundedness/FutureAGI/RAG（L319/L323）、O(1)/O(n)（L81/L83/L101，误读风险最高）、128K（L35/L37）均未收录 pronunciation.json 或仅 FireRed 时代验证，indextts2 下未试听。建议合成前对 L81/L163/L293/L301/L309/L319 做摘录级试听，读错再补条目；writer 无需改稿", "severity": "suggestion"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep03-memory-and-persistent-batch", "script_line": 11,
   "note": "引述前停顿审计：无问题。9 处 voice 嵌入（L11/L59/L139/L281/L289/L301/L309/L319/L329）全部带「——」收尾的引出句，引述后均有独立转述短句锚定边界；稿内 3 处 <break 300ms>（L175/L185/L203）均为术语后垫停、前后子句 ≥14 字，符合 voice-guide 节奏纪律 3。旧双人稿 voice-026 引出问题已解决，本条仅记录确认", "severity": "info"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep03-memory-and-persistent-batch", "script_line": 309,
   "note": "换气审计：全稿无超 200 字段落（lint exit 0），最长 7 段均为引述 turn（L309=179/L59=175/L319=174/L11=156/L301=151/L139=148/L281=144）且内部断点充分，不拆。L309 数字串最密（16 块 H100/Qwen-32B/150 客户/6000 token/93 秒/0.542 秒/170 倍），L319 次之（0.55/0.88/0.69），合成后抽查这两段语速，偏快再考虑断句，改不改由 writer 定", "severity": "info"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep03-memory-and-persistent-batch", "script_line": 7,
   "note": "三方节奏审计：179 轮 S1 45（25.1%）/S2 88（49.2%）/S3 46（25.7%），全员过 25% lint 线但 S1 仅富余 0.1 个百分点（删 1 个 S1 短 turn 即穿线）、S3 最多删 1 个。无连续 5 轮以上 <40 字乒乓短句；同 speaker 连轮仅 L317–L321 一处。S1 在 L67–L83 缺席 9 轮但阿哲四度喊停补位，动线成立。后续删改勿删穿 S1/S3 短 turn，减字优先从 S2 讲解段（字数占比 66.9%）", "severity": "info"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep03-memory-and-persistent-batch", "script_line": 359,
   "note": "时长审计：口播文本 9450 字（179 轮）。按 4 字/秒 ≈ 39.4 分钟、加轮间静音 ≈ 39.7 分钟，低于 target×1.15（40.25），余量约 0.5 分钟偏薄但不触发 warning。实测校准：本季 indextts2 已成片三期语速 5.2–5.9 字/秒（ep01 24.0 分钟/ep02 26.6 分钟/ep03 旧稿 25.7 分钟），本期成片预计 27–31 分钟，无超时风险、无需删减", "severity": "info"}
]
```

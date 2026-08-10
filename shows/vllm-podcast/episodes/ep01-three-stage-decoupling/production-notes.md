[
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 1,
    "note": "谱系与停顿语义（info）：本文件全部意见针对当前三人版 script.md（行号以当前文件为准）。目录内上一份 production-notes 针对已退役的两人版（script_2person.bak.md，MOSS-TTSD 语境），其三大问题——引述展开后单段 222-306 字、总时长 9211 字顶穿上限、六处「——voice——」同型过渡——在当前版本均已解决（最长 turn 160 字、全篇 7482 字、引出句已差异化），旧意见不再适用，以本版为准。当前 tts.provider=indextts2 单句合成（逐 turn 独立）：停顿由模型生成，以下所有停顿建议均为文本节奏软提示（断句、「。——」、引出句），毫秒数仅为目标参考、模型自主决定；turn 间 100ms 静音由 pipeline 统一插入，段间无需标注；按 voice-guide 节奏纪律 2，不使用 <break> 标签。",
    "severity": "info"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 21,
    "note": "三方节奏审计（info）：无问题。全篇 129 turn（S1 36 / S2 59 / S3 34，turn 占比 27.9% / 45.7% / 26.4%，三方均过 voice-guide 的 25% 底线）；无连续三段以上同方独白，最长同方连续仅 2 段（L55-57、L239-241，均为小结+转场，属合理段落呼吸）；阿哲喊停/打断/复述贯穿全程（L13、21、37、61、83、95、119、203、231 等），未被淹没；无三人连续短句的平节奏段，问答轮次长短错落。各方字数占比（S2 约 66%）属 reviewer 声线平衡维度，此处不重复开单。",
    "severity": "info"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 53,
    "note": "换气（warning）：「他原话大意是：」之后一口气列举五个术语（PagedAttention、连续批处理、v0/v1 架构、chunked prefill、prefix caching），其中三个英文多音节词，合成出来是约十秒不间断列举——念的人换不过气，听的人也接不住。建议在第 53 行把列举拆成两口气：在「v0/v1 架构」后断成句号或「。——」，后两个词另起半句（如「还有 chunked prefill、prefix caching」式领起）。拆法由 writer 裁。",
    "severity": "warning"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 53,
    "note": "引述前停顿审计（info）：六处 voice 嵌入（L53、193、201、215、221、225）均带差异化引出句（「他原话大意是：」「他的数据是：」「先把证据摆上桌。」等），无贴脸引述，旧轮「六处同型过渡」问题已解决。本类仅 L193、L221 两处边界偏薄（已单列 suggestion），其余四处无问题。",
    "severity": "info"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 59,
    "note": "换气（suggestion）：「第一条/第二条/第三条」三路列举是本期骨架信息，目前三个分号一口气到底。建议在「第二条」「第三条」之前各给一次「。——」级断句（目标停顿约 300ms，模型自主决定），让三路分叉听得出落点；领起词保留，本身就是天然断句锚点。",
    "severity": "suggestion"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 171,
    "note": "换气+难点降速（warning）：四步列举（调度/执行模型前向/采样/更新状态）以分号一逗到底，且字母拼写「e-x-e-c-u-t-e 下划线 m-o-d-e-l」嵌在第二步中段，四步节奏被拉成短-长-短-短。这是本期核心机制（一拍四步），按 voice-guide 难点要慢。建议：「每一拍里有四步：」之后先给一拍；四步各自断成独立短句（分号改「。——」或句号）；拼写段前后各留半拍，让听众跟得上字母。",
    "severity": "warning"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 187,
    "note": "换气（suggestion）：末句「还有第三步采样——从 logits，就是模型给每个词打的分数，到挑出那一颗 token，那条路比你想的长」中，「从 logits……那一颗 token」是逗号级插入语，主干被绕行约 30 字，一口气绕。建议把 logits 释义独立成短句（先释义、再说「那条路比你想的长」），或在「到挑出那一颗 token」后断句。",
    "severity": "suggestion"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 193,
    "note": "引述前停顿（suggestion）：voice-001 嵌入点，从归属（「写过一篇很出名的 vLLM 架构剖析」）到内容（「他把这套结构从头剖了一遍」）只靠单个破折号过渡，引述入场偏薄。建议把此处「——」改成「。——」（目标停顿约 300-400ms，模型自主决定），或加半句引出（如「他是这么剖的——」），给听众一个「要引别人了」的信号。",
    "severity": "suggestion"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 201,
    "note": "换气（warning）：「他的数据是：」之后一个句子装进七个数字（2%、4%、80%、50 并发、195 毫秒、310 毫秒、37%），数字朗读展开后实际时长远超字面 160 字，且这是反方核心证据，必须颗颗听清。建议：「几乎打平」后的分号改句号，断成两口气；「50 并发时」后再给一拍；落点「差了 37%」前留半拍。另：前半句双破折号插入语「——SGLang 是另一个主流推理框架——」可考虑独立成短句，是否动由 writer 裁。",
    "severity": "warning"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 209,
    "note": "换气（suggestion）：vLLM 侧三连从句（要手动开/只认平铺的前缀/多轮对话每轮还得重算历史）一逗到底，与 SGLang 侧之间没有换挡点。建议把「跨请求自动匹配」后的分号改成「。——」，在两家对比之间给一次换气。",
    "severity": "suggestion"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 221,
    "note": "引述前停顿（suggestion）：voice-021 嵌入点从「量性能损失」跳到「可惜那篇全文我们没抓到」只靠单破折号，「没抓到全文」这个诚实声明容易被一带而过。建议「——」改「。——」，转折前留一拍。",
    "severity": "suggestion"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 225,
    "note": "换气（warning）：引述内容一句六个数字（340 毫秒、190 毫秒、1.2 秒、9.8 秒、2.1 秒、27 秒），p50→p99→p99.9 三连跳是全期最硬的生产证据，一口气念完听众一个都记不住。建议：「降到 190 毫秒」后断成句号，「但 p99……」另起一口气；「p99.9」前再留半拍（目标约 300ms，模型自主决定），让 27 秒这个落点砸实。",
    "severity": "warning"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 229,
    "note": "换气（suggestion）：括号式插入语「——就是第一次把整段提示词喂给模型那一步——」（16 字）拦腰卡在「一次 60 毫秒的 prefill」与「让 23 个在飞的请求全部排队」之间，主干两端各悬一个数字。建议把 prefill 释义前置成独立短句或挪到句尾，保持「60 毫秒导致 23 个排队」的因果一口气说完。挪法由 writer 裁。",
    "severity": "suggestion"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 259,
    "note": "时长预算（info）：无超支。全篇口播 7482 字，按 4 字/秒约 31.2 分钟；加 129 个 turn 间 100ms 静音（约 13 秒）与四处字母拼写段（L59/79/167/171，拼写朗读比字面长约 20-30 秒），实估约 32 分钟，对 target 35 分钟利用率约 91%，距 target×1.15 上限（40.25 分钟）余量充足。lint_script.py 基线 exit 0。本期无 blocking 项。",
    "severity": "info"
  }
]

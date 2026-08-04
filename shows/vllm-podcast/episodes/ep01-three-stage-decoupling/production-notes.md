[
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 69,
    "note": "换气：voice-002 引述 96 字，含 5 项中英混排枚举（pagedattention、连续批处理、v0/v1 架构、chunked prefill、prefix caching），一口气读完必绊；引文内「等……」省略号在 TTS 里容易变成悬空停顿或被吞掉。建议：枚举砍到 3 项、删掉省略号，或把枚举拆成两句读（MOSS-TTSD 下给模型断句锚点，<break> 仅参考值，模型自主决定）。引文保真度由 writer/reviewer 裁，此处只管读感。",
    "severity": "suggestion"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 69,
    "note": "引述前停顿：六处引述（69/237/245/257/269/273 行）全部是「——{{voice}}——」同一种过渡，MOSS-TTSD 靠模型生成停顿，六次同型过渡缺乏文本锚点差异，模型容易把所有引述处理成一个节奏。建议：其中两三处换成句号/冒号收尾的引出句（如「原话是。」「他是这么说的：」），其余保留破折号式，给模型不同的断句信号。",
    "severity": "suggestion"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 77,
    "note": "换气：「第一段/第二段/第三段」三截枚举一镜到底（130 字），段际几乎没有呼吸点，读到第三段开头时已经需要换气。建议：三段各自独立成句，或在段际加显式断句锚点（可写 <break 300ms> 作参考值，MOSS-TTSD 下由模型自主决定；更稳的做法是改写文本节奏——每段开头重复「第一段」「第二段」「第三段」的领起词，天然生成停顿）。",
    "severity": "suggestion"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 107,
    "note": "双声线节奏：107-203 行连续 25+ 轮「S1 短问（13-46 字）→ S2 中长答（60-130 字）」同一节拍往返，读起来是台节拍器；按字量 S1 全剧只占 25.1%（lint 按 turn 数算 50% 通过，但按听感这是典型捧哏读数）。不用改结构，建议在 2-3 处（如 155、167、175 附近）让 S1 加一句反应或自我打断，或让 S2 答到一半自打断反问一句，破掉节拍器。",
    "severity": "suggestion"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 237,
    "note": "换气：voice-001 引述展开后整段 222 字（引文 146 字），且引文里三处括号式插入语（（FastAPI 前端）（调度+模型执行）（数据并行协调））是口播大忌——每处插入都是一次被迫中断、读感连续被切。建议：引文砍到核心判句（「这不是过度设计，而是服务千万并发请求时唯一经得起拷问的架构选型」），进程清单改用 S2 自己的口吻在引述之外说；括号务必拆出，不要让口播者读括号。",
    "severity": "warning"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 245,
    "note": "换气/引述停顿：全剧最长口播段——voice-036 引述展开后整段 306 字（引文 239 字，约 1 分钟密集英文+数字），一口气不可能读完；且 195ms/310ms/37% 这些数字在 249 行会再讲一遍，听众被灌两遍。建议：引文砍到前两句（2-4% 打平 + 195/310 数据），RadixAttention/APC 细节留给 253 行自己的话；若保留全引文，至少断成两句并在句间给模型明确断句锚点。",
    "severity": "warning"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 245,
    "note": "时长预算：全剧按 4 字/秒估算共 9211 字 = 38.4 分钟，距 40.2 分钟（target×1.15）上限只剩约 1.9 分钟；且 6 条引述共 1012 字、英文数字密集（SGLang/p50/TTFT/prefix 等），实际语速显著低于 4 字/秒，实读大概率顶穿上限。删减优先从本行及 237/257/273 三条超长引述下手——每条压到 1-2 句，换气和时长一箭双雕。减哪儿由 writer 定。",
    "severity": "warning"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 257,
    "note": "换气：voice-025 引述展开后整段 256 字（引文 204 字，4 句，含 --max-total-tokens/--max-model-len 英文旗标），一口气读不完；且引文末句「迁移成本被低估」与 261 行 S2 自己的话重复，收尾再讲一遍，节奏上是二次灌入。建议：引文砍到「7GB vs 21GB 乌龙 + 参数映射错误」两句，末句删掉（261 行会补这句）。",
    "severity": "warning"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 269,
    "note": "换气：voice-021 引述展开后整段 228 字，前有 48 字引出链，引文里还有括号枚举（PagedAttention、continuous batching、prefix caching 等）；且 S2 紧接着自曝「没抓到全文、数字给不出」——这条引述本来就不承重。建议：引文压到一句（「摘掉优化、量性能损失」即可），括号枚举删掉；引出链「有人干过——一家技术媒体做过消融实验——」两个破折号之间可缩，给引述前留出干净的停顿位。",
    "severity": "suggestion"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep01-three-stage-decoupling",
    "script_line": 273,
    "note": "换气/引述停顿：voice-027 引述展开后整段 249 字（引文 179 字，3 句 8 个数字：340ms/190ms/1.2s/9.8s/2.1s/27s/60ms/23 个 decode 流），数字 avalanche 一口气读不完；且引文末句「GPU 利用率 81%，瓶颈不在算力在调度」与引述后 S2 自己的点评（「GPU 利用率才 81%，瓶颈不在算力」）重叠，同一拳打两遍。建议：引文砍到前两句或只留 p99 飙升那句；引文末句与 S2 点评二选一保留。",
    "severity": "warning"
  }
]

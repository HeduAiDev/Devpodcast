[
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep04-gpu-execution-pipeline",
    "script_line": 1,
    "note": "谱系与停顿语义（info）：本文件全部意见针对当前三人版 script.md（309 行 / 154 轮，行号以当前文件为准）；目录内上一份 production-notes 针对已退役的双人稿（script_2person.bak.md，FireRedTTS2 语境），其行号已整体失效。旧稿七条意见逐条核对：五步流程被延迟出生旁白截断（旧 L29）→ 现 L31 旁白已句号独立成句，解决；三件事冒号嵌套两层（旧 L45）→ 现 L69 三件事各占一句、破折号引出，十个字段盒子改在 L73 回指不展开，解决；十三轮节拍器问答（旧 L55–L81）→ 现稿无该定式、阿哲高频插入，解决；「核对」两句三连（旧 L93）→ 现 L147 首句「形状核对。」独立钉术语、后两处为定义复述，可接受；voice-015 紧贴冒号起势（旧 L135）→ 现 L183「是这么问的——」破折号引出，解决；引述收尾与评论挤同一行（旧 L165）→ 现 L257 引述在 turn 内收束、评论由 L259 阿哲接，解决；voice-032 三项顿号连排（旧 L189）→ 现 L287 三项已改分号，解决。旧意见全部关闭，以本版为准。tts.provider=indextts2 单句合成（逐 turn 独立）：停顿由模型从标点自主生成，以下停顿建议均为文本节奏软提示（断句 / 引出句 / 合规 <break>），毫秒数仅为参考、模型自主决定；轮间 100ms 静音由 pipeline 统一插入，段间无需标注。稿内现有 4 处 <break 300ms>（L63 / L67 / L229 / L235）均为术语后垫停、前后子句均 ≥14 字，符合 voice-guide 节奏纪律 3，予以保留。校验基线：lint_script.py / lint_punct.py / lint_trace.py 对当前 script.md 全部 exit 0。",
    "severity": "info"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep04-gpu-execution-pipeline",
    "script_line": 3,
    "note": "时长预算：口播文本约 9000 字（含标点，去 {{voice:}} 与 <break> 标记本身、含引述内文），按 4 字/秒约 37.5 分钟，加 154 轮×100ms 轮间静音约 37.8 分钟，低于 target×1.15（40.25 分钟）；按本季实测语速 5.2–5.9 字/秒，成片预计 25–29 分钟。另有约 40 个逐字母拼读音节（L43 collective rpc / L117 forward cuda 与 forward native / L155 split graph）未计入字符数，量级约 15 秒，不影响结论。本类无超标、无需删减，无 warning。",
    "severity": "info"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep04-gpu-execution-pipeline",
    "script_line": 159,
    "note": "口播换气整类结论：lint exit 0，全稿无超 200 字段落——最长 L241=181 字，其次 L269=175 / L117=159 / L159=143 / L257=140 / L183=137 / L287=137。无括号式插入语；几处列举（L31 四步启动流程、L85 四级套娃、L133 三条规矩、L217 录像段小结）均为短分句加分号的可控节奏，语势有抬点。密度级意见仅两条，见 L241 与 L117 条目；本类无 blocking、无 warning。",
    "severity": "info"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep04-gpu-execution-pipeline",
    "script_line": 241,
    "note": "全期最长 turn（181 字），voice-012 引述内文约 90 字一句到底：数字三连（2% 到 10%、2 到 5 倍、100 秒）挤在分号前半拍，后半拍再叠「猴子补丁」「Blackwell 倒退」两个信息点，一口气念完数字容易糊。分号能给模型一个停顿，但句界更稳——建议把引述内文的分号断成句号（「实测大模型冷启动编译可达 100 秒」之后另起一句），让模型拿到明确句界停顿；或维持原样、合成后抽查该 turn 有无吞字。引述是转述大意，断句不动数字，断不断由 writer 裁（停顿软提示，模型自主决定）。",
    "severity": "suggestion"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep04-gpu-execution-pipeline",
    "script_line": 117,
    "note": "该 turn 159 字，但含两组逐字母拼读（f-o-r-w-a-r-d 下划线 c-u-d-a / n-a-t-i-v-e），朗读音节约 190 以上，实际一口气长度是字符数的一倍半，是全稿拼读密度最高的一段。两句之间（「省掉反复读写显存。」与「另一套叫 forward native」之间）是完整子句边界、前后均 ≥14 字——可加 <break 300ms> 垫出换气（合成器拆段插真实静音，是 voice-guide 节奏纪律 3 允许的唯一可靠停顿位）；不加则依赖句号停顿，也可接受。软提示，模型自主决定，加不加由 writer 裁。",
    "severity": "suggestion"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep04-gpu-execution-pipeline",
    "script_line": 183,
    "note": "引述前停顿整类审计：6 处 {{voice:}} 嵌入（L183 voice-015 / L241 voice-012 / L257 voice-013 / L265 voice-031 / L283 voice-014 / L287 voice-032）全部带「——」收尾的差异化引出句（是这么问的 / 他是这么说的 / 答话的大意是 / 原话是 / 他是这么写的 / 写得更全），无一同型连排、无一贴着上一句硬接；引述后均有独立锚定短句收束语势（——原话大概这个意思 / ——大意就是这样 / ——基本就是这个意思 / ——就这组数 / ——这是他们的原话）。indextts2 逐 turn 合成下引出与引述同处一个合成单元，停顿靠标点由模型生成，破折号已是最强软提示。本类无问题。",
    "severity": "info"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep04-gpu-execution-pipeline",
    "script_line": 243,
    "note": "三方节奏整类审计：154 轮严格轮换、零同方连轮；turn 占比 S1 26.6% / S2 47.4% / S3 26.0%，均过 voice-guide 25% 线（S3 余量薄，占比与声线平衡本身归 reviewer，此处仅记录口播面数据）。阿哲最长连续缺席 5 轮（L15–L23 开场技术段，另有数处并列 5 轮），无 ep03 那样争议段 9 连轮缺席的问题——争议落锤段（L239–L291）阿哲 6 度开口（L243 / L251 / L259 / L271 / L279 / L285），全稿喊停十余次且次次有落点：真实回答（L15 / L27 / L163 等）、挂账回收（L73 挂号 L219 还、L215 挂下期）或明说不知道（L245「这个我们也没搞清楚」）。L127–L139 短短短三拍接一段长解是有意的悬念拍（预制菜反转），听感不平，保留。本类无 warning。",
    "severity": "info"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep04-gpu-execution-pipeline",
    "script_line": 11,
    "note": "发音表缺口（沿用 ep03 先例，合成前摘录级试听、读错补 pronunciation.json，writer 无需改稿）：本期新出现或未在 indextts2 下验证的记号——Inductor（L159 / L273）、guard（L143–L147）、LoRA（L191 起多处）、SIGTERM / SIGKILL（L55 / L59）、RMS Norm（L125）、logits（L229 / L295）、Blackwell（L241 起）、FlashAttention（L11 / L101 / L163 / L265）、C++（L11 / L265 / L269）、JSON（L299 / L301）、Softmax（L283）、KV cache（L287）、H100（L11 起多处）、Triton（多处）、100.7%（L11 / L265 / L269，百分数读法）、128000（L295，稿内已有「十二万八千」冗余，核对数字本体读法）、CUDA graph 的 graph（L3 / L183，CUDA 会触发「库达」替换、graph 未验证）。另核对三处逐字母拼读段（L43 / L117 / L155）连字符是否被逐个字母读出，及 execute model / sample tokens（L67 / L229 / L235）两个词的空格分词读法。重点试听行：L11、L55、L117、L125、L159、L241、L283、L287、L295。",
    "severity": "suggestion"
  }
]

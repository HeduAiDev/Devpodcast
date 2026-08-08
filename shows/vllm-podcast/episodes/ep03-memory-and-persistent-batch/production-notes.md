[
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep03-memory-and-persistent-batch",
    "script_line": 137,
    "note": "上轮遗留项核对（info）：对照当前 script.md 逐行复查，上一轮 production-notes 的意见均已落实——L137 双枚举已改为一遍+句号断句（「顺序不是随便排的。」独立成句），L285 引子已换「他们贴出的数字是——」不再与 L293 同型，L293 引文已在「0.69」后加句号断开，L183 已含堵车类比承接。上述点本轮一律不再重提；下剩意见见 L139/L293/L297 三条。",
    "severity": "info"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep03-memory-and-persistent-batch",
    "script_line": 293,
    "note": "换气（suggestion）：L293 是全剧最长 turn 之一（178 字，与 L5 并列）。引述收尾「——原话大概这个意思。」之后紧接评论句「命中率低不只是慢，是模型开始犯傻」——这是本段金句，但被长引述挤在尾巴上，读出来容易一带而过。建议在引述收尾与评论句之间加一拍：把评论句拆成同一 speaker 的独立段落（换行），或前面加半句引出（如「这话得品一品——」）。当前 firered-tts2 停顿由模型生成，此为文本节奏软提示，不是硬毫秒。",
    "severity": "suggestion"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep03-memory-and-persistent-batch",
    "script_line": 139,
    "note": "双声线节奏（suggestion）：L139–L157 连续 5 轮短句对答——S1 递话仅 5–18 字（L151「第三段呢？」只有 5 字），S2 答案 30–78 字、多数不到 60 字，是全剧最平的节奏段，而内容恰是「三段式分配」的结构性讲解，听众没时间把每段立住。建议任选：a) L143/L151 的短问前各加半句承接，把「第二段」「第三段」的序号感立住；b) L153 答完 lookahead 后让 S1 接一句确认再进 L155。另外 L147–L149「外部预填充」岔路埋在快速对答里，若保留需放慢，否则建议并入 L145。",
    "severity": "suggestion"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep03-memory-and-persistent-batch",
    "script_line": 297,
    "note": "引述前停顿（suggestion）：全剧 9 处引述中唯一非破折号引出的点。「同一个团队也承认：」冒号后直接贴引述内容，对话模型容易把「承认」和引述粘成一个节奏单位；其余 8 处（L5/61/133/261/269/277/285/293）均为「——」引出。建议改为「承认——」或「承认，原话是——」，与全剧引述节奏统一。停顿由模型生成，此为软提示。",
    "severity": "suggestion"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep03-memory-and-persistent-batch",
    "script_line": 25,
    "note": "换气核查（info）：全稿无单段超 200 字 lint 线。最长四段为 L5=178、L293=178、L285=154、L25=152，内部句号级断点充分，读感可承受，均不拆。唯一读感偏紧的是 L285 的数字串（16 H100 / Qwen-32B / 150 客户 / 6000 token / 93 秒 / 0.542 秒 / 170 倍连排），合成后抽查该段语速，若偏快再考虑在「差了 170 倍」前断句。",
    "severity": "info"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep03-memory-and-persistent-batch",
    "script_line": 5,
    "note": "双声线节奏核查（info）：全剧 81/80 轮严格交替，S1 平均 24 字/轮、S2 平均 76 字/轮——老张短问、阿凯长句自打断（「为什么？」「——」式折返），与 voice-guide 性格差一致；无单方连续独白失衡段，S1 最长 turn（L183=62 字）也只是带反应的提问，不越界。唯一偏离见 L139 意见。",
    "severity": "info"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep03-memory-and-persistent-batch",
    "script_line": 3,
    "note": "时长预算（info）：全稿正文 8044 字，按 4 字/秒 ≈ 33.5 分钟，低于 target 35 分钟；按保守 3.5 字/秒 ≈ 38.3 分钟，仍在 target×1.15（40.25 分钟）之内。无超时风险，无需删减。",
    "severity": "info"
  }
]

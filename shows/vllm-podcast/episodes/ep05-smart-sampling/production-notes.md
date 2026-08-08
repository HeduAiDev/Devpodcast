[
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep05-smart-sampling",
    "script_line": 3,
    "note": "时长预算：正文共 8456 字（含标点，去 voice 占位符），按 4 字/秒约 35.2 分钟；target 35 分钟、余量线 40.25 分钟，未超。voice 占位符当前合成时被剥除、不产音频，无额外 clip 时长；L17 的 <break 300ms> 等停顿由模型生成，实际时长可能略长，仍在预算内。若想留冗余，L157/L185（全场最长段之二，161-163 字且数字最密）是天然删减位——删不删由 writer 定。",
    "severity": "info"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep05-smart-sampling",
    "script_line": 69,
    "note": "口播换气总检：全文无单段 ≥180 字（最长 L69=168 字），200 字 lint 线无触发。L69 虽为全场最长段，但逗号/分号断点密、五句分明，读感可接受；L83 的七项列举（留底、改分、砍尾巴、分路、截断、抽、交卷）、L121 的六项契约（接收、试走、倒带、填掩码、判终、重置）均为 2-4 字短项，无一口气念不完的问题。除 L109（另见意见）外，本类别无其他问题。",
    "severity": "info"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep05-smart-sampling",
    "script_line": 91,
    "note": "双声线节奏（明显问题）：L91-L129 连续十轮，S1 全部 ≤28 字（26/27/13/28/4/26/20/5/22/27），S2 每轮 70-124 字大段连答，S1 整段占比约 17%、无类比无回嘴，读感像审讯笔录、中段声部失衡。全片按字数 S1 约占 24%（turn 数层面 30% lint 线未触发，此处只谈听感）。对照 L47-L75 已加厚的轮次（L55「憋作文」、L59「复读机」带类比后听感明显变活），建议在 L91-L129 内同样给 2-3 轮加 30 字以上的类比或回嘴，位置由 writer 裁；L107「坑二呢？」和 L119「好，坑三？」作为结构转折保留超短没问题，但别让十轮全是这个密度。",
    "severity": "warning"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep05-smart-sampling",
    "script_line": 109,
    "note": "口播换气（明显问题）：「json、regex、choice、grammar、json_object、structural_tag」六个英文标识符中英混排一口气连读，json_object、structural_tag 这类长驼峰/下划线词口播必卡，是典型「一口气念不完的列举」。建议拆两拍：json、regex、choice、grammar 四个短词一顿，再单列 json_object 和 structural_tag 并各带半句说明（例如长词后面直接跟用途短句）；或在此处拆段。当前 firered-tts2 对话模型停顿由模型生成，以上为软提示——通过断句/换行引导，不写死毫秒。",
    "severity": "warning"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep05-smart-sampling",
    "script_line": 161,
    "note": "引述前停顿（TTS 语义提示，9 处通用）：9 处 voice 嵌入全部带引出句（「提过——」「做过系统评测——」「报了个 bug——」等），无贴着上一句接的问题，此点无问题。但「——{{voice:xx}}——」双侧破折号会在合成时被剥除占位符后拼成四连破折号——L161 实际进 TTS 的文本是「提过————他的大意：」，L173/L177/L185/L213/L221/L229/L249/L273 同构。TTS 对罕见「————」大概率读出异常长停顿或糊音。建议只留左侧引出（「提过——」），右侧改逗号或句号再接「他的大意：」；9 处同改。fire-tts2 停顿由模型生成，此项是文本节奏引导，改完模型自会在引出句后换气。",
    "severity": "suggestion"
  },
  {
    "ep_dir": "shows/vllm-podcast/episodes/ep05-smart-sampling",
    "script_line": 185,
    "note": "口播换气/读感：「并发吞吐从每秒 232 颗暴跌到每秒 24 至 157 颗，墙钟时间从 6.3 秒膨胀到 40 至 60 秒」——同句「每秒」连用两次，四组数字（232/24-157/6.3/40-60）一口气，口播必糊、TTS 也容易赶。建议去掉第二个「每秒」（「从每秒 232 颗，暴跌到 24 至 157 颗」）或在此处断句，给数字组之间留停顿点；句末根因那句（「短路判断发生在草稿模型前向之后」）是全段最有价值的增量信息，值得拆出来单独成句、放慢读。",
    "severity": "suggestion"
  }
]

# production-notes — ep02-engine-heartbeat（口播工程师意见 · 第 2 轮）

> 本文件全部内容均为意见，不包含任何改好的稿子正文。script_line 对应 script.md 当前真实行号。
> TTS 语义分支：`devpodcast.json` 中 `tts.provider = firered-tts2`（对话模型）——停顿由模型生成，以下停顿建议均为**软提示**（断句 / 加引出句 / 改标点），不写死毫秒。
> 校验基线：`lint_script.py` 对当前 script.md 通过（exit 0，无超 200 字段落）。
> 本轮为回环第 2 轮：第 1 轮提出的问题大多已被 writer 的修订解决，本文先列「已解决确认」，再列「剩余/新增意见」，供 writer 只处理增量。

## 四类审计结论（第 2 轮）

| 类别 | 结论 | 说明 |
|---|---|---|
| 1. 口播换气 | 无问题（1 条 suggestion 见下） | 全片无超 lint 线单段；最长 turn 是 L133（含 voice-028 引述共 185 字），但引述是独立声音段，S2 实际连续口播只有引出句约 42 字 + 收尾 15 字，无一口气风险。L189 一处三连破折号嵌套需拆（见下） |
| 2. 双声线节奏 | 无遗留问题 | 第 1 轮两处问题已解决：23–37 段 S2 答案已拉出长短差（L25 加「嗯，这么说太抽象。说人话：」自打断，四答 63/82/33/76 字错落）；219–225 段 L223 已补承接句。当前 79/79 轮严格交替、无连续三轮短句、无同 speaker 连轮；S1 字量约 32%（剥离引述后），过 30% 底线 |
| 3. 引述前停顿 | 1 条 suggestion | 5 处 voice 嵌入（13/109/117/133/161 行）全部带引出句；109/117/133/161 引述后均有句号+转述收尾，边界清晰。仅 L13 一处引述与转述之间无断点（见下） |
| 4. 时长预算 | 无 warning | 口播文本 8253 字（含 5 段引述约 296 字）按 4 字/秒 ≈ 34.4 分钟；加轮间停顿实估 35–36.5 分钟，在 target 35 之上、target×1.15=40.25 之内。余量薄，L109/L133/L141 数字密集段是风险最高处 |

## 第 1 轮问题 · 已解决确认（writer 无需再动）

- **〔1〕L273 四英文关 warning → 已解决**：四道关卡已拆「分两拨」并挂中文注解（结束符 EOS / 停止词 / 停止编号 / max tokens 硬上限），半句一拍，读感成立；check_stop、EOS 均已进 pronunciation.json。剩余英文仅 EOS（逐字母，已收录）与 max tokens（缺口见下）。
- **〔2〕L21 四方法名 pronunciation → 已解决**：schedule / execute model / sample tokens / update from output 均已收录 pronunciation.json；SchedulerOutput、EngineCoreOutputs、prepend_request、allocate_slots、collective RPC、step with batch queue、max num batched tokens、skipped waiting、chunked prefill、LIFO、FCFS、IPC 同批已收录。
- **〔3〕L23–37 节拍器 → 已解决**：见上表节奏行。
- **〔4〕L219–225 极短拍连发 → 已解决**：L223 已补承接（「开会喊一嗓子——行，那谁负责把结果取回来？」，22 字），两轮问答不再连发抢拍。

## 意见清单（按严重级，仅增量）

### suggestion

**〔5〕script_line 13 — suggestion（引述停顿）**
voice-005 引述以两个问句收尾（「……为什么？……差在哪？」），紧接着「它还总结了一句：考的就是「为什么这样设计」，不是 API 怎么用」是 S2 的转述——但引述与转述之间没有任何断点标记，对话模型可能把「它还总结了一句」整段读进引述语气里，听众分不清引述到哪儿结束。建议在第 13 行做两选一：引述句末补句号并让「它还总结了一句」另起一句；或引述后加收尾引子（如「——它还有一句总结：」）。给模型一个在引述边界停半拍、切回 S2 语气的文本信号。停顿由模型生成，此处是软提示。

**〔6〕script_line 279 — suggestion（读感/TTS 发音）**
「max tokens」在全片出现 3 次（L273「还有 max tokens 这个硬上限」、L279「那 max tokens 呢？」、L281「max tokens 管硬上限」）。全片方法名/机制名/缩写类术语已全部收录 pronunciation.json（check_stop、EOS、schedule、execute model、sample tokens、update from output、max num batched tokens、chunked prefill、prepend request、allocate slots、collective RPC、Engine Core Outputs、LIFO、FCFS、IPC 等），唯独 max tokens 是同类中唯一的漏网（token、JSON、kernel 等通用英文词不在收录范围，TTS 可正常读）。「max」容易被拼读成「马科斯/马克斯」整词。建议补一条 pronunciation.json 条目（如 max tokens → 「最大token数」，与 max num batched tokens → 「单批最大token数」同型），writer 无需改稿，由发音表在合成前替换。

**〔7〕script_line 189 — suggestion（换气/断句）**
「冤，但有补偿：FCFS——就是先到先得的排队——模式下，抢占请求靠 prepend request 直接回队头——下一拍优先重新上桌，相当于插队补偿。」一句里两个破折号插入语（FCFS 释义 + 回队头递进）叠成三连破折号，读感像一句话卡两次壳。建议把第一个插入语改用逗号/顿号或句号拆开（如「FCFS，就是先到先得的排队模式；抢占请求靠 prepend request 直接回队头——下一拍优先重新上桌」），只留一个破折号做递进。拆法由 writer 裁。

### info

**〔8〕script_line 133 — info（换气审计确认）**
全片无超 200 字段落（lint exit 0）。L133 虽是全稿最长 turn（含 voice-028 引述共 185 字），但引述是独立声音段，S2 实际连续口播只有引出句约 42 字 + 收尾 15 字，无一口气风险；「尾延迟回归正常。这两组数字，都是论文里的实测。」句号断句已到位。本行为全片时长最重处，若成片超时是首选压缩点（减哪儿由 writer 定）。

**〔9〕script_line 109 — info（时长审计）**
口播文本 8253 字（含 5 段引述约 296 字），按 4 字/秒 ≈ 34.4 分钟；加 159 轮轮间停顿（约 1 分钟）实估 35–36.5 分钟，低于 target×1.15（40.25 分钟），无需删减。余量薄：L109（p50/p99/p99.9 三组数字）、L133、L141 三处数字密集段实际语速会低于 4 字/秒均线，是超时风险最高处。

**〔10〕script_line 273 — info（读感确认）**
第 1 轮 warning 已解决（见上「已解决确认」第〔1〕条），本条仅记录确认：当前 L273「一拨是模型自己的事……吐个结束符，EOS；另一拨是你定的规矩——……到数就停」分两拨 + 中文注解的拆法读感成立，S2 不需要为四个英文标识符换气。唯一遗留是 max tokens 的发音表缺口（见〔6〕条）。

## 附：机器可读版（对齐 schemas/production-notes.schema.json）

```json
[
  {"ep_dir": "shows/vllm-podcast/episodes/ep02-engine-heartbeat", "script_line": 13,
   "note": "[引述停顿] voice-005 引述以两个问句收尾后紧接 S2 转述「它还总结了一句：考的就是……」，引述与转述之间无断点标记，对话模型可能把转述读进引述语气。建议引述句末补句号让「它还总结了一句」另起一句，或加收尾引子（如「——它还有一句总结：」），给模型引述边界停顿信号；停顿由 FireRedTTS2 自主生成，此处为文本节奏软提示",
   "severity": "suggestion"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep02-engine-heartbeat", "script_line": 279,
   "note": "[读感/TTS] max tokens 全片出现 3 次（L273/L279/L281），是方法名/机制名/缩写类术语中唯一未收录 pronunciation.json 的（check_stop/EOS/schedule/execute model/sample tokens/update from output/max num batched tokens/chunked prefill/prepend request/allocate slots/collective RPC/Engine Core Outputs/LIFO/FCFS/IPC 均已收录），max 易被拼读成「马科斯」。建议补 pronunciation.json 条目（max tokens → 最大token数，与 max num batched tokens 同型），writer 无需改稿",
   "severity": "suggestion"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep02-engine-heartbeat", "script_line": 189,
   "note": "[换气/断句] 「FCFS——就是先到先得的排队——模式下……直接回队头——下一拍优先重新上桌」一句两个破折号插入语叠成三连破折号，读感卡壳。建议第一个插入语改逗号/句号拆开，只留一个破折号做递进，拆法由 writer 裁",
   "severity": "suggestion"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep02-engine-heartbeat", "script_line": 133,
   "note": "[换气确认] 全片无超 200 字段落（lint exit 0）；L133 为全稿最长 turn（含 voice-028 引述 185 字），但引述是独立声音段，S2 连续口播仅引出句约 42 字+收尾 15 字，无一口气风险；句号断句已到位。本行是全片时长最重处，超时首选压缩点",
   "severity": "info"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep02-engine-heartbeat", "script_line": 109,
   "note": "[时长] 口播 8253 字（含引述约 296 字）按 4 字/秒 ≈ 34.4 分钟，加轮间停顿实估 35–36.5 分钟，低于 target×1.15（40.25），无 warning；L109/L133/L141 数字密集段语速慢于均线，是超时风险最高处",
   "severity": "info"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep02-engine-heartbeat", "script_line": 23,
   "note": "[节奏确认] 第 1 轮两处节奏问题已解决：23–37 段 S2 四答已拉出长短差（63/82/33/76 字，L25 含自打断），219–225 段 L223 已补承接。当前 79/79 轮严格交替、无连续三轮短句、无同 speaker 连轮；S1 字量约 32%（剥离引述后）过 30% 底线，节奏无遗留问题",
   "severity": "info"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep02-engine-heartbeat", "script_line": 273,
   "note": "[读感确认] 第 1 轮四英文关 warning 已解决：四道关卡已拆「分两拨」并挂中文注解，check_stop/EOS 已进 pronunciation.json；仅 max tokens 发音缺口见 L279 条",
   "severity": "info"}
]
```

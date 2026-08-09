# production-notes — ep02-engine-heartbeat（口播工程师意见 · 三人版 script 第 1 轮）

> 本文件全部内容均为意见，不包含任何改好的稿子正文。script_line 对应**当前** script.md（2026-08-09 三人版，349 行 / 174 轮）的真实行号。
> 本文件取代 2026-08-07 那份针对旧双人稿的第 2 轮 notes——旧稿行号已整体失效（旧稿存档见 script_2person.bak.md）。
> TTS 语义分支：`devpodcast.json` 中 `tts.provider = indextts2`（单句合成，逐 turn 独立生成）——停顿由模型从标点自主生成，以下停顿建议均为**软提示**（断句 / 加引出句 / 改标点），不写死毫秒；按 voice-guide 节奏纪律，不建议使用 `<break>` 标签。轮间 100ms 静音由 pipeline 拼接时统一插入，无需在稿面标注。
> 校验基线：`lint_script.py` 对当前 script.md 通过（exit 0，无超 200 字段落，无未闭合 speaker 标记）。

## 旧第 2 轮意见去向（三人版新稿已吸收，writer 无需再动）

- 旧〔5〕voice-005 引述/转述无断点 → 当前 L21 已补边界标记「——它还有一句总结：」，引述以问句收尾、转述另起，解决。
- 旧〔6〕max tokens 发音表缺口 → 已收录 pronunciation.json（max tokens / max_tokens 双形态均在），解决。
- 旧〔7〕FCFS 句三连破折号 → 当前 L213 已改为「FCFS，就是先到先得的排队模式；……直接回队头——下一拍优先重新上桌」，只留一个递进破折号，解决。

## 四类审计结论（本轮）

| 类别 | 结论 | 说明 |
|---|---|---|
| 1. 口播换气 | 无 warning（1 条 suggestion） | 全稿无超 200 字段落（lint exit 0），最长 turn 为 L157（含 voice-028 引述共 184 字）。仅 L157 引述后半句一处四逗号连读，见意见〔2〕 |
| 2. 三方节奏 | 1 条 warning | L315–331 连续 9 轮无 S3，阿哲复述确认在本期收尾难点段缺位，见意见〔1〕。其余：无连续 5 轮以上 <40 字乒乓短句（自动扫描确认），无同 speaker 连轮；turn 数 S1 45 / S2 83 / S3 46，S1 占 25.9%、S3 占 26.4%，均过 voice-guide 25% 线但余量薄，见意见〔5〕 |
| 3. 引述前停顿 | 无问题 | 5 处 voice 嵌入（L21 / L129 / L141 / L157 / L185）全部带「——」收尾的引出句（是这么问的——／他是这么说的——／用户反映——／是这么写的——／记了下来——），引述后均有独立转述短句收尾（原话大概这个意思。／他给的就是这些数字。／大意是这样。／这两组数字，都是论文里的实测。／这是他的原话。），引述边界清晰。全稿无 `<break>` 标签，符合 indextts2 分支纪律。见意见〔4〕 |
| 4. 时长预算 | 无超标 | 口播文本 9060 字（含 5 段引述），按 4 字/秒 ≈ 37.8 分钟，加 174 轮×100ms 轮间静音 ≈ 38 分钟；target 35，×1.15 上限 40.25，在预算内。余量约 2 分钟，L129/L157 数字密集段实际语速低于均线，是风险最高处但不触发 warning。见意见〔6〕 |

## 意见清单（按严重级）

### warning

**〔1〕script_line 323 — warning（三方节奏：阿哲 9 连轮缺席）**
阿哲最后一个 turn 在 L313（「指定的停止词是什么」），再回到对话已是 L333——中间 L315–331 连续 9 轮全是 S1↔S2 往返。这段恰好塞了本期收尾的五个新点：FINISHED 标记与整型枚举判定（L319）、完成态是一整个状态家族（L321–323）、显存释放出口（L325）、未停请求重新入队（L327）、Engine Core Outputs 经 IPC 回传（L331）。按 voice-guide 难点动线，「阿哲复述确认」必须真实存在，而这串难点没有一个他的确认拍——读者代言人在全期信息密度最高的收尾段消失约两分钟。建议在第 323 行（完成态家族）之后或第 327 行（重新入队）之后插一个阿哲的复述确认短 turn（一句话即可，如复述「完成是一整个状态家族、一个整型比较就判完」或「没停的下一拍重新排队竞争预算」），把 9 连轮断成 5+4。插哪儿、写什么由 writer 裁。

### suggestion

**〔2〕script_line 157 — suggestion（换气：引述后半句四逗号连读）**
voice-028 引述的第二半句「把长 prefill 切成小块、插在 decode 批中间跑，也就是 chunked prefill，吞吐提升 2.6 倍到 6.9 倍，尾延迟回归正常」约 44 字四个逗号一逗到底——定义（chunked prefill 是什么）和效果（2.6–6.9 倍）挤在同一口气里，读出来两组信息糊成一团。建议在第 157 行把「也就是 chunked prefill」后面的逗号改成句号或「。——」，定义一口气、效果一口气。这是引述文本，只动标点不动数据；停顿由模型生成，此处是软提示。

**〔3〕script_line 129 — suggestion（发音表缺口：本期新增术语未做 indextts2 试听）**
当前 pronunciation.json 的试听结论全部是 FireRed 时代的（各条 notes 均为「FireRed 读对，恢复原文不替换」），而本期 script 出现了一批表里完全没有的英文/数字记号：p50 / p99 / p99.9（共 10 处，散布 L129–L177）、FLOPS（L153）、Sarathi-Serve（L157）、OSDI（L157/L159）、Mistral-7B / Falcon-180B（L165）、SLA（L177）、PD 分离（L185）、FINISHED / RUNNING / WAITING（L93/L201/L225/L319）。这些在 IndexTTS-2 下怎么读没人验证过——数字型（p99.9）和缩写型（SLA/OSDI/PD）是最容易被念歪的两类。建议合成前先对 L129、L157、L165、L177、L185 做摘录级试听，读错再补发音表条目；writer 无需改稿，由发音表在合成前替换。

### info

**〔4〕script_line 21 — info（引述前停顿审计：无问题）**
5 处 voice 嵌入逐一核过：引出句均以「——」收尾给模型停顿信号，引述结束后均有独立转述短句锚定边界（明细见上表第 3 行）。全稿无 `<break>` 标签，符合 indextts2 分支「停顿由模型从标点生成」的语义。旧第 2 轮 note〔5〕的 voice-005 边界问题在当前 L21 已解决（「——它还有一句总结：」），本条仅记录确认。

**〔5〕script_line 7 — info（三方节奏审计：turn 占比过线但余量薄）**
全稿 174 轮，自动扫描无连续 5 轮以上 <40 字的乒乓短句，无同 speaker 连轮，除意见〔1〕外节奏无平段。turn 数占比 S1 25.9% / S2 47.7% / S3 26.4%——S1、S3 均过 voice-guide 25% 底线，但分别只富余 0.9 和 1.4 个百分点。提示 writer：后续任何删改若动到 S1/S3 的短 turn，容易把占比删穿；要删请优先从 S2 的讲解段里减字（S2 字数占比 65.7%，压缩空间最大）。

**〔6〕script_line 349 — info（时长审计：无超标）**
口播文本 9060 字（含 5 段引述，已剥离 voice 标记与 speaker 标签），按 4 字/秒 ≈ 37.8 分钟，加轮间静音 ≈ 38 分钟，低于 target×1.15（40.25 分钟），无需删减。余量约 2 分钟偏薄：L129（p50/p99/p99.9 三组数字）与 L157（28 倍 / 2.6–6.9 倍）两段数字密集引述实际语速会低于 4 字/秒均线。若成片超时，首选压缩点是 L157 所在 turn（全稿最长，184 字）——减哪儿由 writer 定。

**〔7〕script_line 311 — info（听感：「四道关卡」复述只点三摊）**
L303 说「四道关卡，分两拨」并列出四道（EOS／停止词／停止编号／max tokens），L311 复述「四道关卡各管一摊」时只点了三摊（EOS 管模型自觉，停止词管你指定，max tokens 管硬上限）——「停止编号」没有着落。听众跟数会在这里卡一下（「第四道呢？」）。数字对不上属内容一致性，归 reviewer 判；本条只记录口播听感上的磕绊点，改不改由 writer 裁。

## 附：机器可读版（对齐 schemas/production-notes.schema.json）

```json
[
  {"ep_dir": "shows/vllm-podcast/episodes/ep02-engine-heartbeat", "script_line": 323,
   "note": "阿哲 9 连轮缺席：L313 之后 S3 直到 L333 才再开口，L315–331 全是 S1↔S2，且这段塞了 FINISHED 状态家族、整型枚举判定、显存释放、重新入队、Engine Core Outputs/IPC 五个新点。按 voice-guide 难点动线，建议在 L323（完成态家族）后或 L327（重新入队）后插一个阿哲复述确认短 turn，把 9 连轮断成 5+4。插哪儿、写什么由 writer 裁", "severity": "warning"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep02-engine-heartbeat", "script_line": 157,
   "note": "voice-028 引述后半句「把长 prefill 切成小块……也就是 chunked prefill，吞吐提升 2.6 倍到 6.9 倍，尾延迟回归正常」约 44 字四逗号一逗到底，定义和效果挤在一口气里。建议把「也就是 chunked prefill」后的逗号改句号或「。——」，定义一口气、效果一口气。只动标点不动数据；indextts2 停顿由模型生成，此为软提示", "severity": "suggestion"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep02-engine-heartbeat", "script_line": 129,
   "note": "发音表缺口：p50/p99/p99.9（10 处，L129–L177）、FLOPS（L153）、Sarathi-Serve（L157）、OSDI（L157/L159）、Mistral-7B/Falcon-180B（L165）、SLA（L177）、PD 分离（L185）、FINISHED/RUNNING/WAITING（L93/L201/L225/L319）均未收录 pronunciation.json，且表内试听结论全是 FireRed 时代的，indextts2 下未验证。建议合成前对 L129/L157/L165/L177/L185 做摘录级试听，读错再补条目；writer 无需改稿", "severity": "suggestion"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep02-engine-heartbeat", "script_line": 21,
   "note": "引述前停顿审计：无问题。5 处 voice 嵌入（L21/L129/L141/L157/L185）全部带「——」收尾的引出句，引述后均有独立转述短句锚定边界；全稿无 <break> 标签，符合 indextts2 分支纪律。旧第 2 轮 note〔5〕的 voice-005 边界问题已解决，本条仅记录确认", "severity": "info"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep02-engine-heartbeat", "script_line": 7,
   "note": "三方节奏审计：174 轮无连续 5 轮以上 <40 字乒乓短句，无同 speaker 连轮。turn 占比 S1 25.9%/S2 47.7%/S3 26.4%，S1/S3 过 25% 线但余量不足 1.5 个百分点——后续删改勿删穿 S1/S3 短 turn，要删优先从 S2 讲解段减字（字数占比 65.7%）", "severity": "info"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep02-engine-heartbeat", "script_line": 349,
   "note": "时长审计：口播文本 9060 字按 4 字/秒 ≈ 37.8 分钟，加轮间静音 ≈ 38 分钟，低于 target×1.15（40.25），无超标、无需删减。余量约 2 分钟偏薄，L129/L157 数字密集段实际语速低于均线；若成片超时首选压缩 L157 所在 turn（全稿最长 184 字），减哪儿由 writer 定", "severity": "info"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep02-engine-heartbeat", "script_line": 311,
   "note": "听感磕绊：L303 列「四道关卡」（EOS/停止词/停止编号/max tokens），L311 复述「四道关卡各管一摊」只点三摊，「停止编号」没着落，听众跟数会卡。数字一致性归 reviewer 判，本条只记听感风险，改不改由 writer 裁", "severity": "info"}
]
```

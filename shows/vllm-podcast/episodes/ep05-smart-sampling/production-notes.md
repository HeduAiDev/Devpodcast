# production-notes — ep05-smart-sampling（口播工程师意见 · 三人版 script 第 1 轮）

> 本文件全部内容均为意见，不包含任何改好的稿子正文。script_line 对应**当前** script.md（2026-08-09 三人版，339 行 / 169 轮）的真实行号。
> 本文件取代目录内旧版 production-notes——旧版针对双人旧稿（旧稿统计 8456 字、最长段 161-163 字、firered-tts2 语义），行号已整体失效；旧稿存档见 script_2person.bak.md。
> TTS 语义分支：`devpodcast.json` 中 `tts.provider = indextts2`（单句合成，逐 turn 独立生成）——停顿由模型从标点/文本节奏生成，以下停顿建议均为**软提示**（断句 / 挪注解 / 加反应拍），不写死毫秒；轮间 100ms 静音由 pipeline 拼接时统一插入，无需在稿面标注。
> 校验基线：`lint_script.py` 对当前 script.md 通过（exit 0，无超 200 字 turn，无未闭合 speaker 标记）。

## 旧版意见去向（三人版新稿已吸收，writer 无需再动）

- 旧〔3〕L91-L129「S1 审讯笔录」warning → 新稿九道关卡段（L45-L109）阿哲密布 10 轮（含 L67「憋作文」、L83「老鼠屎」类比后听感变活），解决。
- 旧〔4〕L109 六英文标识符连读 warning → 新稿 L139/L141 已改中文对译「json、正则、choice、grammar——给结构、给正则、给选项、给语法规则」，长词 json object / structural tag 各带半句说明，解决。
- 旧〔5〕「——{{voice:xx}}——」剥除占位符后四连破折号 suggestion → 新稿 9 处引述均为「引出——{{voice}}引文。——大意/原话」结构，剥除后只剩单破折号，解决。
- 旧〔6〕L185「每秒」连用两次 + 四组数字 suggestion → 新稿 L239 已删第二个「每秒」；数字密度仍在，口播侧无修复动作，语速提示并入本轮意见〔8〕。
- 旧〔1〕〔2〕时长与换气统计基于旧稿字数与行号，全部失效，以本轮审计为准。

## 四类审计结论（本轮）

| 类别 | 结论 | 说明 |
|---|---|---|
| 1. 口播换气 | 无 warning（1 条 suggestion） | lint exit 0，全稿无超 200 字 turn（最长 L285=137 字含引述）；列举均为 2-4 字短项。仅 L199 双破折号插入语一处读感问题，见意见〔3〕 |
| 2. 三方节奏 | 1 条 warning + 1 条 suggestion | L231-L245 阿哲 8 连轮缺席约 109 秒，见意见〔1〕；L301-L313 7 连轮约 96 秒，见意见〔2〕。其余：无同 speaker 三连轮（S2 双连轮 8 处均 ≤143 字且后有三方接应），无 ≥5 轮全 <40 字平段；turn 数 S1 43 / S2 83 / S3 43 = 25.4% / 49.1% / 25.4%，过 25% 线但余量仅 0.4pp，见意见〔9〕 |
| 3. 引述前停顿 | 无问题 | 9 处 voice 嵌入全部带「——」收尾引出句 + 「大意/原话」收束短句，见意见〔7〕。L285 引述内夹注解一句，边界听感问题见意见〔4〕 |
| 4. 时长预算 | 无超标 | 口播文本 8873 字按 4 字/秒 ≈ 36.9 分钟，加 169 轮 × 100ms 轮间静音 ≈ 37.3 分钟；target 35、上限 ×1.15 = 40.25，在预算内，余量约 3 分钟。数字密集段实际语速低于均线，见意见〔8〕 |

## 意见清单（按严重级）

### warning

**〔1〕script_line 241 — warning（三方节奏：阿哲 8 连轮缺席，约 109 秒）**
阿哲最后开口在 L229（「那社区里有真人踩过坑吗？」），再回到对话已是 L247——中间 L231-L245 连续 8 轮全是 S1↔S2，约 434 字 / 109 秒。这段恰好压了全期最重的内容：voice-018 引述（L231）、「开不开」的准话加一次「我们也没搞清楚」（L235）、解扣启动（L237）、voice-034 bug 引述（L239）、根因「短路发生在草稿模型前向之后」（L241）、「关了个寂寞」往返（L243/L245）。S1 提问密度高、节奏本身不闷，但全期悬念的解开 + 两条外部引述全在这 109 秒里，读者代言人零确认拍——按 voice-guide 难点动线，这是「阿哲复述确认」最该出现的位置。建议在第 241 行（根因句）之后插一个阿哲复述/反应短 turn（一句话即可，把「关了还扣钱」这个点钉住），把 8 连轮断成 5+3。插哪儿、写什么由 writer 裁。

### suggestion

**〔2〕script_line 309 — suggestion（三方节奏：L301-L313 阿哲 7 连轮，约 96 秒）**
判据（L301）→「怎么知道遮不遮得住」（L303）→ voice-035 量化引述（L305）→ 原理追问（L307/L309）→ 三笔账收口（L311/L313），约 382 字 / 96 秒无 S3。S1 三轮追问在做读者代理，且 L315 阿哲「摆齐三笔账」兜住了段落，可不改；若想再稳，在第 305 行引述后或第 309 行「真没搞清」后插半句反应，把 7 连轮断成两截。改不改由 writer 裁。

**〔3〕script_line 199 — suggestion（换气/读感：双破折号插入语切断主线）**
该 turn 133 字（全稿第二长），主线「一类纯 CPU……另一类是模型类……」被两组破折号插入语切断两次：「——用的 KMP，K-M-P，字符串匹配的老算法——」和「——M-T-P，多 token 预测——」。听感上「另一类」出场时听众要回找主线。建议把两处注解各自断成独立短句（插入语收尾的破折号改句号，主句一气读完再补注解），或接受现状——字母拼读本身已带降速。改不改由 writer 裁。

**〔4〕script_line 285 — suggestion（引述边界听感 + 全稿最长 turn）**
voice-016 引述中段夹了一句口播注解「——LLGuidance，另一个引导解码库；」——听众分不出这句是评测原话还是阿凯插的注释（引述保真归 reviewer 判，此处只报口播听感：引述听到一半冒出一句旁白，边界糊）。且该 turn 137 字为全稿最长。建议把注解挪到引述结束之后（「大意是这样」一句里交代 LLGuidance 是什么），或在「反超」处句号断开、注解独立成句。怎么挪由 writer 裁。

**〔5〕script_line 281 — suggestion（发音表缺口：本期新术语 indextts2 下未验证）**
按发音表 2026-08-09 的教训（CamelCase 整词被 IndexTTS 按单词误读，如 AsyncLLM→哦新可），本期出现而表里没有的术语：MLSys（L221）、xgrammar（L281）/ XGrammar（L285）、LLGuidance（L285）、AWQ / INT4 / FP16（L305/L309）、GB10（L239）、RTX（L281）、EAGLE（L199/L203/L221）、Medusa（L203）、outlines（L281）、OpenAI（L69）、argmax（L75/L77）、n-gram（L199/L201/L203）、logprobs（L51/L105）、min p（L75/L79/L93/L107）、bad words（L61）、logit bias（L59）、min tokens（L65）、flash infer（L101）、copy stream（L177）、deferred sampling（L257）、validate tokens / accept tokens（L161）、MTP 裸形（L269——L199 已教过 M-T-P 拼读，引述里的裸形会不会被打回整词读，未验证）。JSON / C++ / Llama / Triton 有 ep04 成片实证可读，不在此列。建议合成前对 L75/L199/L221/L239/L269/L281/L285/L305 做摘录级试听，读错再补发音表条目；writer 无需改稿，替换在合成前做。

### info

**〔6〕script_line 65 — info（口播换气审计：无问题）**
lint exit 0；全稿 169 轮无超 200 字 turn（最长 L285=137 字）。L153 六方法（接收、试走、倒带、填掩码、判终、重置）、L47 四类活（留底、改分、分路、交卷）、L139-L141 六种约束均为 2-4 字短项列举，无一口气念不完的长列举；字母拼读段（L75 m-i-n、L101 r-a-n-d-o-m、L145 E-B-N-F、L177 c-o-p-y、L199 K-M-P / M-T-P）是 voice-guide 规定的术语钉读，慢是设计意图。除意见〔3〕外本类别无其他问题。

**〔7〕script_line 203 — info（引述前停顿审计：无问题）**
9 处 voice 嵌入（L203/L221/L231/L239/L269/L279/L285/L305/L329）逐一核过：引出句均以「——」收尾给模型停顿信号（他是这么说的——／系统测了投机解码——／有人报过——／报了个 bug——／记过一串追问——／公开承认过——／做过系统评测——／有份评测——／比较过几家——），引述后均有「——大意/原话」收束短句锚定边界；剥除占位符后无连破折号残留（旧版〔5〕问题不复现）。全稿 5 处 `<break 300ms>`（L25×2 / L35×2 / L61）均位于英文术语后，属 voice-guide 节奏纪律 3 的术语垫停合规用法，无用于口头禅转折的违规 `<break>`。

**〔8〕script_line 339 — info（时长审计：在预算内，余量约 3 分钟）**
口播文本 8873 字（含 9 段引述，剥离 speaker 标记 / voice 占位符 / `<break>` 标签，计全部非空白字符含标点），按 4 字/秒 ≈ 36.9 分钟，加 169 轮 × 100ms 轮间静音 ≈ 37.3 分钟。target 35、上限 ×1.15 = 40.25——超 target 约 2.3 分钟但在预算内，无需删减。余量约 3 分钟偏薄：数字密集引述（L221 六个数字、L239 四组、L305 四个小数）与字母拼读段实际语速低于 4 字/秒均线，是最可能再吃余量的位置；这些段落断点已合规，口播侧无修复动作。若成片超时，首选压缩点是 L285 所在 turn（全稿最长，137 字）——减哪儿由 writer 定。

**〔9〕script_line 7 — info（三方节奏审计：turn 占比过线但余量仅 0.4pp）**
全稿 169 轮，turn 数 S1 43 / S2 83 / S3 43 = 25.4% / 49.1% / 25.4%——S1、S3 均过 voice-guide 25% 底线，但只富余 0.4 个百分点。提示 writer：后续任何删改若动到 S1/S3 的短 turn 容易把占比删穿；要删请优先从 S2 讲解段减字（S2 字数占比约三分之二，压缩空间最大）。其余：S2 双连轮 8 处（L59/61、L79/81、L139/141、L169/171、L175/177、L197/199、L239/241、L279/281）均 ≤143 字且后有三方接应，无独白失衡；L49-L65 过关卡段短问答密集，但三方交替、内容递进，是「快步过关卡」质感而非平段；阿哲喊停 6 处（L11/L77/L155/L167/L183/L215）均获正面接应，无被打断淹没。除意见〔1〕〔2〕外节奏无其他问题。

## 附：机器可读版（对齐 schemas/production-notes.schema.json）

```json
[
  {"ep_dir": "shows/vllm-podcast/episodes/ep05-smart-sampling", "script_line": 241,
   "note": "阿哲 8 连轮缺席：S3 最后开口 L229，再回到对话已是 L247，中间 L231-L245 连续 8 轮 S1↔S2（约 434 字 / 109 秒），且这段压了 voice-018 引述、「开不开」准话加一次「我们也没搞清楚」、voice-034 bug 引述、根因、「关了个寂寞」往返——全期悬念解开加两条引述，读者代言人零确认拍。建议在 L241（根因句）后插一个阿哲复述/反应短 turn，把 8 连轮断成 5+3。插哪儿、写什么由 writer 裁", "severity": "warning"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep05-smart-sampling", "script_line": 309,
   "note": "阿哲 7 连轮：L301-L313 约 382 字 / 96 秒无 S3（判据→怎么测→voice-035 量化引述→原理追问→三笔账收口）。S1 三轮追问在做读者代理、L315 阿哲摆齐三笔账兜住了段落，可不改；若想再稳，在 L305 引述后或 L309「真没搞清」后插半句反应。改不改由 writer 裁", "severity": "suggestion"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep05-smart-sampling", "script_line": 199,
   "note": "双破折号插入语切断主线：该 turn 133 字（全稿第二长），「一类纯 CPU……另一类是模型类……」被「——用的 KMP，K-M-P，字符串匹配的老算法——」和「——M-T-P，多 token 预测——」切断两次，听感上「另一类」出场时听众要回找主线。建议两处注解各自断成独立短句（插入语收尾破折号改句号），或接受现状。改不改由 writer 裁", "severity": "suggestion"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep05-smart-sampling", "script_line": 285,
   "note": "voice-016 引述中段夹口播注解「——LLGuidance，另一个引导解码库；」，听众分不出是原话还是注释，引述边界听感糊（保真归 reviewer）；且该 turn 137 字为全稿最长。建议注解挪到引述结束后（「大意是这样」句里交代），或在「反超」处句号断开、注解独立成句。怎么挪由 writer 裁", "severity": "suggestion"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep05-smart-sampling", "script_line": 281,
   "note": "发音表缺口：MLSys(L221)、xgrammar(L281)/XGrammar(L285)、LLGuidance(L285)、AWQ/INT4/FP16(L305/L309)、GB10(L239)、RTX(L281)、EAGLE(L199/L203/L221)、Medusa(L203)、outlines(L281)、OpenAI(L69)、argmax(L75/L77)、n-gram(L199/L201/L203)、logprobs(L51/L105)、min p(L75/L79/L93/L107)、bad words(L61)、logit bias(L59)、min tokens(L65)、flash infer(L101)、copy stream(L177)、deferred sampling(L257)、validate/accept tokens(L161)、MTP 裸形(L269) 均未收录 pronunciation.json，indextts2 下未验证（CamelCase 整词误读有 2026-08-09 教训）。JSON/C++/Llama/Triton 有 ep04 成片实证不在此列。建议合成前对 L75/L199/L221/L239/L269/L281/L285/L305 做摘录级试听，读错补表；writer 无需改稿", "severity": "suggestion"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep05-smart-sampling", "script_line": 65,
   "note": "口播换气审计：无问题。lint exit 0，全稿 169 轮无超 200 字 turn（最长 L285=137）；L153 六方法、L47 四类活、L139-L141 六种约束均为 2-4 字短项列举；字母拼读段（L75/L101/L145/L177/L199）是 voice-guide 规定的术语钉读，慢是设计意图。除意见〔3〕外本类别无其他问题", "severity": "info"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep05-smart-sampling", "script_line": 203,
   "note": "引述前停顿审计：无问题。9 处 voice 嵌入（L203/L221/L231/L239/L269/L279/L285/L305/L329）全部带「——」收尾引出句，引述后均有「——大意/原话」收束短句锚定边界，剥除占位符后无连破折号残留。全稿 5 处 <break 300ms>（L25x2/L35x2/L61）均位于英文术语后，属 voice-guide 术语垫停合规用法，无违规 <break>", "severity": "info"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep05-smart-sampling", "script_line": 339,
   "note": "时长审计：口播文本 8873 字按 4 字/秒约 36.9 分钟，加 169 轮 x100ms 轮间静音约 37.3 分钟；target 35、上限 40.25，在预算内、无需删减。余量约 3 分钟偏薄，数字密集引述（L221/L239/L305）与字母拼读段实际语速低于均线；若成片超时首选压缩 L285 所在 turn（全稿最长 137 字），减哪儿由 writer 定", "severity": "info"},
  {"ep_dir": "shows/vllm-podcast/episodes/ep05-smart-sampling", "script_line": 7,
   "note": "三方节奏审计：turn 数 S1 43/S2 83/S3 43 = 25.4%/49.1%/25.4%，S1/S3 过 25% 线但余量仅 0.4 个百分点——后续删改勿删穿 S1/S3 短 turn，要删优先从 S2 讲解段减字。S2 双连轮 8 处均不超 143 字且后有三方接应；L49-L65 短问答段三方交替有递进非平段；阿哲喊停 6 处（L11/L77/L155/L167/L183/L215）均获接应无淹没。除意见〔1〕〔2〕外节奏无其他问题", "severity": "info"}
]
```

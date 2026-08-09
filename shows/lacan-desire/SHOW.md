# SHOW.md — lacan-desire 当前状态

> 一张图，九站，把雅克·拉康的欲望图（graphe du désir）从零讲到完整。
> 读者：哲学入门者——有哲学/人文基础，但没读过拉康。
> 形式：**博客栏目（单角色朗读稿）**，非对谈播客。递进式系列，篇间钩子咬合，术语首现必展开，引文一手核验。

## 书源
- kind: blog-column（无 repo2book 书源）
- 一手文献核验：`season/research/r5a-seminar-primary-en.md`（Seminar V/VI/X/XI +《Écrits》逐字核对）、`r5b-seminar-primary-zh.md`（中译本盘点）
- 概念库（写作基准）：`season/bible/concept-library.md`
- 系列大纲（编排真相源）：`season/outline.md`

## 篇目（9 期，朗读稿已定稿 v2，2026-08-09）

| # | 期 | 这篇回答的问题 | script | audio |
|---|----|----------------|--------|-------|
| 1 | ep01-concepts-language | 能指/所指？语言为什么是链？隐喻/换喻怎么让意义动？ | [x] | [ ] |
| 2 | ep02-concepts-speaking | 划杠主体 $？大他者 A？自我 m vs 主体？需要/要求/欲望？ | [x] | [ ] |
| 3 | ep03-path-signifying-chain | 意义怎么滑动？après-coup 才落定？缝合点 s(A)？ | [x] | [ ] |
| 4 | ep04-path-subject-vector | 马蹄形矢线？需要→要求→欲望→幻象怎么接？ | [x] | [ ] |
| 5 | ep05-path-circle | 屈从为什么是圆圈？需求的环形地狱？Che vuoi 被反抛？ | [x] | [ ] |
| 6 | ep06-path-mirror | 自我从哪来？i(a)→m？I(A) 为什么「母亲的表情」？ | [x] | [ ] |
| 7 | ep07-path-upper-chain | 享乐 vs 快乐？S(Ⱥ)？$◇D 为什么在代码位置？语音召唤？ | [x] | [ ] |
| 8 | ep08-full-graph | 五条路径怎么互锁？朋友圈例子走全程 + 三问自检 | [x] | [ ] |
| 9 | ep09-critique | 中文世界怎么读？图过时了吗？德勒兹批什么？Fink vs Žižek？ | [x] | [ ] |

## Phase B（TTS）
- [ ] 全 9 期音频：待合成（`scripts/indextts_synth_blog.py`，单角色老张音色，cut5 断句已并入）
- 产物位置：`episodes/epNN-*/audio/episode.wav` + `audio/segments/`

## 环境状态
- TTS: IndexTTS-2 定案（conda env `itts310`，`models/indextts2`）
- 发音表：`season/pronunciation.json`（138 条拉康术语读法：`$◇D`→划杠 S 菱形 D、`Écrits`→艾克利、`Žižek`→齐泽克）
- 参考音色：复用 vllm-podcast 的 `laozhang_16k.wav`（shows/vllm-podcast/voice-samples/）

## 写作纪律（沿袭工厂铁律）
- 来源真实：概念定义可溯源到 research/ 真实文献，引文带出处；分歧处显式标注
- 不编造：查不到的宁可删
- 类比承重：删掉类比后读者仍能答出「这里在讲什么逻辑」
- 术语首现必展开：术语（法语/英语）+ 一句不靠术语的解释

## 已知边界
- 通行解读（Fink / Žižek / Soler 等）个别点有分歧，文章按主流共识写作并显式标出
- 图编号以《Écrits》(1966) + Fink 英译本为基准；中文译名以褚孝泉译《拉康选集》、吴琼《阅读你的症状》为准
- 一手核验（2026-08-09）：图编号定案 Graphe 1→2→3→complet（法文版 pp.805/808–809/815/816–820）；五条路径均有原文依据
- v2 重构（2026-08-09）：9 篇经 writer×9 + 审核×9 + 修复轮 + 全局覆盖审核（23 项概念检查，0 残余 BLOCKING）

# 拉康的欲望图 · 博客栏目

> 一张图，七站，把雅克·拉康（Jacques Lacan）的欲望图（graphe du désir / graph of desire）从头走到尾。
> 目标读者：**哲学入门者**——有哲学/人文基础，但没读过拉康。
> 形式：递进式系列文章，篇间钩子咬合，术语首次出现必展开，概念定义可溯源。

## 系列文章（按阅读顺序）

| # | 文章 | 这篇回答的问题 |
|---|------|----------------|
| 1 | [为什么拉康要画一张图](posts/01-why-a-graph.md) | 欲望图是什么、为什么拉康不定义欲望而要画图、怎么读图（三条约定）、图的来路 |
| 2 | [能指链与划杠主体](posts/02-signifying-chain.md) | 意义在哪落定？句号是谁打的？$ 是什么？隐喻/换喻怎么让意义滑动 |
| 3 | [需要、要求、欲望](posts/03-need-demand-desire.md) | 开口要东西的「我」是谁？需要为什么一开口就变味？欲望为什么是换喻性的「差一点」 |
| 4 | [Che vuoi? 幻象与客体小 a](posts/04-fantasy-object-a.md) | 大他者想要什么？为什么欲望没有对象？幻象 $◇a 是欲望的剧本还是欲望的崩溃阀 |
| 5 | [大他者的匮乏与享乐](posts/05-lack-jouissance.md) | 规则缺的那颗钉子 S(Ⱥ) 在哪？为什么图的顶端是失败不是满足？J(A) 为什么不是「大他者的爽」 |
| 6 | [驱力、语音召唤与代码](posts/06-drive-voice-code.md) | 享乐被禁了人为什么还在绕圈？代码为什么是构成层？「被喊到名字」如何先于「我说话」 |
| 7 | [完整图合读与批判延伸](posts/07-full-graph-critique.md) | 整图三条矢线怎么同时运转？吴琼/褚译、德勒兹、Fink vs Žižek 三场争论，以及三问自检清单 |

阅读顺序：1 → 2 → … → 7。每篇结尾有「→ 下一篇」链接；第 7 篇回链开篇收束。

## 材料库（生产侧，非阅读侧）

```
research/r1-structure.md          欲望图结构本体：四层楼、全部节点、两条矢线（Fink/Žižek 等英文核心文献）
research/r2-origin-texts.md       原文语境：Subversion 一文、Seminar V/VI、L 图→欲望图演变、中译本
research/r3-concept-network.md    概念网络：无意识像语言、need/demand/desire、大他者、幻象、S(Ⱥ)、语音召唤/代码
research/r4-chinese-critical.md   中文接受史（吴琼/张一兵/李新雨）+ 批判与争议（德勒兹、后期转向、Fink vs Žižek）
analysis/concept-library.md       概念库：每个概念的定义 / 平实转述 / 图内位置 / 常见误解 / 关联（写作基准）
outline.md                        系列大纲：串联逻辑、每篇小节、概念映射、讲解手法
```

## 音频生产（TTS）

博客是单角色朗读（老张音色，与播客 S1 同款）。管线已就绪，待 TTS 环境（IndexTTS-2 权重 + itts310 + ffmpeg）：

```bash
# 全 7 篇
D:/Env/Miniconda/envs/itts310/python.exe scripts/indextts_synth_blog.py columns/lacan-desire
# 单篇重跑
D:/Env/Miniconda/envs/itts310/python.exe scripts/indextts_synth_blog.py columns/lacan-desire --only 01
# 无模型环境预览清洗+发音表效果（本机可跑）
python scripts/indextts_synth_blog.py columns/lacan-desire --dry-run
```

产物：`audio/NN-slug.wav`（22050Hz）+ `audio/segments/NN-*_turn*.wav`。与播客同链：拆段护栏 / 剪边 / 插静音 / 响度 -17dB / atempo 0.88x。

- **发音表**：`pronunciation.json`（发音真相源）。拉康术语/图符号→中文读法（`$◇D`→划杠 S 菱形 D、`Écrits`→艾克利、`Žižek`→齐泽克…）；英文引文/书名保留原文。改文章术语前先查这里。
- **清洗规则**（`scripts/indextts_synth_blog.py`）：剔代码块（ASCII 图）/ 剔导航行 / 表格转口语 / 删括号内纯外语注释 / 删括号开头拉丁前缀（「（signifiant de l'Autre——中文」→「（中文」）。

## 写作纪律（本栏目沿袭 devpodcast 工厂铁律）

- **来源真实**：一切概念定义可溯源到研究笔记中的真实文献（书/研讨班/论文）；引文带出处文本名；拿不准的细节标注置信度或写明「学者间有分歧」。
- **不编造**：查不到的宁可删，不硬写。
- **类比承重**：删掉类比后读者仍能答出「这里在讲什么逻辑」，否则换掉。
- **术语首现必展开**：每个术语首次出现给「术语（法语/英语）」+ 一句不靠术语的解释。

## 已知边界

- 拉康欲望图的通行解读（Fink / Žižek / Soler / Eidelsztein 等）在个别点上存在分歧，文章按主流共识写作，分歧处显式标出（如第 5 篇 S(Ⱥ) 与 Φ 共用符号的时间线、第 7 篇 Fink vs Žižek）。
- 图上节点/图编号以《Écrits》(1966) 及 Fink 英译本为基准；中文译名以褚孝泉译《拉康选集》与吴琼《雅克·拉康：阅读你的症状》为准，两处不同会注明。

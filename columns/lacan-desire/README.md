# 拉康的欲望图 · 博客栏目

> 一张图，九站，把雅克·拉康（Jacques Lacan）的欲望图（graphe du désir / graph of desire）从零讲到完整。
> 目标读者：**哲学入门者**——有哲学/人文基础，但没读过拉康。
> 结构（v2，2026-08-09 重构）：**先基础概念引入 → 再逐条路径分析（每条路径配承重例子）→ 结束时所有概念和路径全覆盖**。
> 形式：递进式系列文章，篇间钩子咬合，术语首次出现必展开，概念定义可溯源，拉康引文一手核验。

## 系列文章（按阅读顺序）

| # | 文章 | 这篇回答的问题 |
|---|------|----------------|
| 1 | [概念准备（上）：无意识像语言](posts/01-concepts-language.md) | 能指/所指是什么？语言为什么是链？隐喻和换喻怎么让意义动？ |
| 2 | [概念准备（下）：谁在说话](posts/02-concepts-speaking.md) | 划杠主体 $ 是什么？大他者 A 是什么？自我 m 和主体差在哪？需要/要求/欲望怎么分？ |
| 3 | [路径一：能指链 S→S′](posts/03-path-signifying-chain.md) | 意义怎么滑动？为什么事后（après-coup）才落定？缝合点 s(A) 是谁的钉子？ |
| 4 | [路径二：主体矢线 ΔS](posts/04-path-subject-vector.md) | 马蹄形矢线从哪出发？需要→要求→欲望→幻象怎么接？「逮住的鱼儿」在哪？ |
| 5 | [路径三：屈从圆圈 s(A)→A→s(A)](posts/05-path-circle.md) | 为什么屈从是圆圈？需求的环形地狱怎么转？Che vuoi? 为什么被反抛？ |
| 6 | [路径四：镜像路 i(a)→m](posts/06-path-mirror.md) | 自我从哪来？i(a)→m 什么意思？I(A) 为什么是「母亲的表情」？ |
| 7 | [路径五：上层链 享乐→阉割](posts/07-path-upper-chain.md) | 享乐和快乐差在哪？S(Ⱥ) 是什么？$◇D 为什么写在代码位置？语音召唤是什么？ |
| 8 | [完整图合读：五条路径同时运转](posts/08-full-graph.md) | 五条路径怎么互锁？一个朋友圈例子走全程 + 三问自检清单 |
| 9 | [批判与延伸](posts/09-critique.md) | 中文世界怎么读这张图？图过时了吗？德勒兹批的是什么？Fink 与 Žižek 的分歧？ |

阅读顺序：1 → 2 → … → 9。每篇结尾有「→ 下一篇」链接 + 钩子问题；第 9 篇回链开篇收束。**读完整个系列，欲望图涉及的所有概念和路径都能让人明白**（概念覆盖清单见 outline「硬约束」节 4）。

## 材料库（生产侧，非阅读侧）

```
research/r1-structure.md          欲望图结构本体：四层楼、全部节点、两条矢线（Fink/Žižek 等英文核心文献）
research/r2-origin-texts.md       原文语境：Subversion 一文、Seminar V/VI、L 图→欲望图演变、中译本
research/r3-concept-network.md    概念网络：无意识像语言、need/demand/desire、大他者、幻象、S(Ⱥ)、语音召唤/代码
research/r4-chinese-critical.md   中文接受史（吴琼/张一兵/李新雨）+ 批判与争议（德勒兹、后期转向、Fink vs Žižek）
research/r5a-seminar-primary-en.md 研讨班一手文本核验（2026-08-09）：Seminar V/VI/X/XI 讲稿 +《Écrits》法文原文逐字核对；图编号定案（Graphe 1/2/3/complet）；引文勘误（代码句出处、pulsion 定义、XI 定位）
research/r5b-seminar-primary-zh.md 中文世界可得性盘点：研讨班中译本（仅七·商务版）、褚译《拉康选集》两版、图式1 原文摘录、法/英/中公开资源入口
analysis/concept-library.md       概念库：每个概念的定义 / 平实转述 / 图内位置 / 常见误解 / 关联（写作基准）
outline.md                        系列大纲：串联逻辑、每篇小节、概念映射、讲解手法
```

## 音频生产（TTS）

博客是单角色朗读（老张音色，与播客 S1 同款）。管线已就绪，待 TTS 环境（IndexTTS-2 权重 + itts310 + ffmpeg）：

```bash
# 全 9 篇
D:/Env/Miniconda/envs/itts310/python.exe scripts/indextts_synth_blog.py columns/lacan-desire
# 单篇重跑
D:/Env/Miniconda/envs/itts310/python.exe scripts/indextts_synth_blog.py columns/lacan-desire --only 03
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
- **一手核验（2026-08-09）**：图编号已逐字定案（Graphe 1 → 2 → 3 → complet，法文版 pp.805/808–809/815/816–820；「Graphe 4」是顺推叫法）；「五条路径」体系（路一 能指链 S→S′ / 路二 主体矢线 ΔS / 路三 屈从圆圈 / 路四 镜像路 i(a)→m / 路五 上层链 享乐→阉割）均有原文逐字依据（褚译图式1 说明 + Seminar VI 首讲）。
- 引文勘误已按一手文本修正：「主体由代码构成…」出处为《Écrits》Graphe 1 评注段（法文版 pp.806–807）非研讨班讲稿；「le besoin devient pulsion」改为原文句 pulsion = ce qui advient de la demande…（p.817）；Seminar XI 引文定位为 1964 年 3 月驱力诸讲（法文版 p.96，回应萨福安提问）；shofar 段直引 STA-F 稿（1963-05-22 讲，Seuil 2004 pp.283–298）；S1/S2 系后期记号（Seminar XX），欲望图时代原文写作 S→S′（03 篇注明）。
- **v2 重构（2026-08-09）**：9 篇新结构（2 概念 + 5 路径 + 合读 + 批判）经 writer×9 + 严格审核员×9 + 修复轮 + 全局覆盖审核（23 项概念检查，链接闭环，0 残余 BLOCKING）。

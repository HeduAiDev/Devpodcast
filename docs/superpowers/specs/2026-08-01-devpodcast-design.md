# devpodcast 设计规格

> 把一本技术书变成一季**双人对谈播客**——议题驱动、批判先行、引真实社区声音、本地 GPU 合成音频。
>
> 状态：设计定稿，待实施
> 日期：2026-08-01
> 参考方法论：Repo2Book（多 agent 书籍工厂）——**仅方法论参考，零运行时依赖**

---

## 0. 一句话

给定一本技术书，产出一季可听的播客：`planner` 从全书抽出 N 个议题，`researcher` 真上网找批判声音与求职者声音，`writer` 写成老张与阿凯的对谈逐字稿，本地 GPU 合成音频。

**不是**有声书朗读，**不是**章节摘要。侧重**提取要点 + 批判性讨论 + 互联网声音 + 生活场景**。

---

## 1. 方法论：复用什么、重做什么

Repo2Book 的灵魂是四样东西，devpodcast **直接继承**：

- **A 档案即唯一真相源** — 每站吃同一份档案，不以彼此产物为准
- **B 素材先行** — 素材（议题切片 / 外部声音 / 论证骨架）先于写作产出并过门禁
- **C 有界回环 + 逃生舱** — 质量问题走有界回环，路线问题立即 `BLOCKED` 升级 Lead
- **D 持久角色 + 显式工件** — 角色 = 提示词文件（持久），进程按任务 spawn；跨期记忆靠显式工件，不赌对话记忆

Repo2Book 其余的东西是因为**输入是代码仓**才长出来的（pin blobless clone、`# SOURCE:` 逐字内嵌、subtract-only 精简版、单测闸门、数值轨迹、图形几何 linter），devpodcast **一律不继承**。

### 1.1 对照表

| 维度 | Repo2Book | devpodcast | 关系 |
|---|---|---|---|
| 输入真相源 | `dossier.json`（pin 源码档案） | `episode-card.json`（议题 + 跨章切片 + 必讲机制） | 改内容，结构参考 |
| 外部背景 | `research/concepts.json`（名词/项目/记法） | `voices.json`（批判源 + 求职者源） | 改内容，结构参考 |
| 素材先行产物 | `explainer.json`（数值轨迹）+ 图 | `arc.json`（论证骨架）+ 时长预算 | 改内容，纪律参考 |
| 唯一可写正文者 | writer 写 `chapter.md` | writer 写 `script.md` | 直接继承（叙事守护） |
| 评审 | 多维并行（事实/结构/公式/源码根基） | 多维并行（6 个口播维度） | 结构参考，维度重写 |
| 跨单元连贯 | Book Bible | Season Bible | 结构参考 |
| 角色 | 8 个基础 + researcher + curator（10 个） | 8 个 | 结构参考，逐份重写 |
| Workflow | `chapter-pipeline.js`（单章 10 阶段） | `season-pipeline.js` + `episode-pipeline.js` | 结构参考，拆成两段 |
| 门禁 | 11 个 linter | 5 个 linter | 结构参考，规则重写 |
| 经验回流 | run-ledger → retro → 台账 | 同上 | 直接继承，台账独立 |

### 1.2 三层真相源

互不替代，合成时按各自 confidence 标识：

1. **`episode-card.json`** — 议题内容真相源（书里怎么说）
2. **`voices.json`** — 外部声音真相源（别人怎么说）
3. **`season-plan.json`** — 编排真相源（这一季怎么走）

---

## 2. 独立仓库原则（HARD RULE）

**devpodcast 是完全独立的代码仓，零运行时跨仓依赖。**

- 不 import 其他项目的代码，不读其他项目的路径，不做 submodule
- 参考 Repo2Book 的脚本（`bible.py` / `archivist.py` / `instance.py` / `lint_punct.py` / workflow `lib/`）**逐份重写**进本仓，按 devpodcast 的域重新命名与定义语义
- 唯一的外部接触面：`scripts/ingest_book.py` 在**用户显式给出路径时**读一次书源，**快照摄入**本仓后即断开
- clone 下来就能跑，不要求机器上存在任何其他项目

---

## 3. 架构总览

### 3.1 两阶段

**Phase A（每本书一次）** — `season-pipeline.js`
三条腿并行，汇于 book-analyst，archivist 收尾建 Season Bible。

**Phase B（逐期，可并发）** — `episode-pipeline.js`
命中 Phase A 素材缓存，writer 主笔 → producer 提意见 → writer 定稿 → TTS → 质检 → 评审 → 归档。

### 3.2 数据流

```
用户指定书源路径
        │
        ▼
┌─ ingest_book.py（一次性快照摄入）─┐
│  Repo2BookSource / EpubSource /   │  ← BookSource 抽象层
│  MarkdownSource / PdfSource       │
└───────────────┬───────────────────┘
                ▼
    shows/<name>/source-book/
      ├ book.json           （书的元数据 + digest）
      ├ outline.json        （大纲）
      ├ chapter-cards/*.json（每章要点清单）
      └ glossary.json       （术语表）
                │
    ════════════╪══════════ Phase A ══════════════════
                │
    ┌───────────┼────────────────────┐
    ▼           ▼                    ▼
┌ planner ┐ ┌ hook-engineer ┐ ┌ researcher ┐
│ 通读全书│ │ 钩子/金句     │ │ 真上网查   │
│ 抽议题  │ │ 争议框架      │ │ 批判+求职  │
└────┬────┘ └───────┬───────┘ └──────┬─────┘
     │              │                │
season-plan.json  arc.json      voices.json
     │              │                │
     └──────┬───────┴────────────────┘
            ▼
   ┌ book-analyst ×N（每期一个，并行）┐
   │ 按议题跨章切片，抽必讲要点        │
   └──────────────┬────────────────────┘
                  ▼
        episode-card.json ×N
                  │
            ┌ archivist ┐
            │ 建 Season Bible │
            └──────┬─────┘
                   │
    ═══════════════╪══════════ Phase B ══════════════
                   │
             ┌ writer ┐  ← episode-card + voices + arc + Bible
             │唯一有权写│
             └────┬───┘
                  ▼
            script.md（初稿）
                  │
            ┌ producer ┐  ← 只提意见，不改稿
            └────┬─────┘
                  ▼
        production-notes.md（每条带行号）
                  │
             ┌ writer ┐  ← 逐条采纳或带理由反驳
             └────┬───┘
                  ▼
            script.md（定稿）
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
┌ 确定性 linter ┐    ┌ tts-engine ┐
│ lint_script   │    │ 本地 GPU   │
│ lint_voices   │    └──────┬─────┘
│ lint_punct    │           ▼
│ lint_anchors  │    episode.wav + segments/
│ lint_trace    │           │
└───────┬───────┘    ┌ audio-qa ┐
        │            └─────┬────┘
        └────────┬─────────┘
                 ▼
    ┌ reviewer（6 维并行）┐
    └──────────┬──────────┘
               │ ≤3 轮回环，BLOCKED 拉逃生舱
               ▼
        ┌ archivist ┐
        │ 归档+回写 Bible │
        └────────────┘
```

### 3.3 三处关键设计

**① Phase A 三条腿并行、汇于 book-analyst。** planner 定"讲什么"，hook-engineer 定"怎么起头收尾"，researcher 定"别人怎么说"，三者互不阻塞。book-analyst 是汇流点——吃 season-plan 的议题定义，把散落多章的要点聚拢成一期的内容真相源。

**② writer 前后各一次，中间夹 producer。** producer 不是评审（不判对错），是**口播工程师**：看的是"这段读出来会不会喘不过气"、"两人连续三轮短句、节奏平了"、"这个引述前需要半秒停顿"。它**只写 production-notes.md，绝不碰 script.md**——继承叙事守护硬规则。

**③ linter 与 TTS 并行、汇于 reviewer。** 文本门禁不必等音频。音频问题（削波/时长超标）走 audio-qa 单独回环到 tts-engine，或回 writer（脚本太长）。reviewer 是最后一道，同时看文本和音频。

---

## 4. 角色（8 个持久提示词，`.claude/agents/`）

| 角色 | 产物 | 阶段 | 职责 |
|---|---|---|---|
| **planner** | `season-plan.json` | A | 通读全书，抽 N 个议题、定顺序/依赖/伏笔 |
| **hook-engineer** | `arc.json` | A | 每期开场钩子、收尾金句、争议框架 |
| **researcher** | `voices.json` | A | 真上网查批判源 + 求职者源，带 URL/日期/平台/confidence |
| **book-analyst** | `episode-card.json` | A | 按议题跨章切片，抽必讲要点 |
| **writer** | `script.md` | B | **唯一有权写脚本**，双说话人逐字稿 |
| **producer** | `production-notes.md` | B | 口播工程师，只提意见 |
| **reviewer** | `reviews/*.json` | B | 6 维并行评审 |
| **archivist** | Season Bible + trace | A/B | 跨期连贯性 + 长期记忆 |

**不设**：implementer / tester / explainer / illustrator / curator（无代码、无精简版、无数值轨迹、无图）。

### 4.1 硬规则

1. **叙事守护** — 主编排者不得直接写/编 `script.md`，只有 writer 可写。质量不对就改提示词，不改脚本内容。
2. **producer 不改稿** — 只写 `production-notes.md`，每条带 script 行号定位。
3. **零脚手架泄漏** — 脚本是正式节目，不提 `episode-card` / `voices.json` / `arc.json` 等内部文件名。
4. **researcher 不编** — 查不到就标 low confidence 或拉逃生舱，不许凭记忆写。

---

## 5. 风格：voice-guide.md 是这个项目的灵魂

由 Lead 在 Phase A 一次性落笔到 `shows/<name>/season/bible/voice-guide.md`，writer 强制复用。

### 5.1 两个说话人

**老张 —— 主持人**
- 定位：**读过书、但不装懂的人**。价值不是知识量，是**替听众问出那个笨问题**。
- 语言习惯：短句多，爱打断，爱用生活类比（"这就跟你租仓库一样"）。遇到没懂的地方**明确说"等一下，你刚才那句我没跟上"**——这是节目最重要的诚实机制。
- 对争议的态度：**主动挑事**。"社区里有人说这就是过度工程，你怎么看？"
- 禁忌：不许假装惊叹（"哇好厉害"），不许当捧哏。

**阿凯 —— 嘉宾/技术侧**
- 定位：**真读过源码的人**，但**知道自己知识的边界**。
- 语言习惯：长句会自我打断改成短句（"它会把——嗯，我这么说吧"）。给数字前先给量级感（"大概是几十 GB 这个量级"）。
- 对争议的态度：**不护短**。书里/项目里做得不好的地方，承认"这块设计确实是历史包袱"。
- 禁忌：不许背书（念定义），不许说"这个很简单"（对听众的隐性攻击）。

### 5.2 三条内容纪律（linter + reviewer 双查）

1. **每期至少一次"我不知道"** — 某个问题两人都答不上来，明确说"这个我们也没搞清楚，评论区有懂的说说"。**这是反 AI 播客的最强信号**——AI 生成的节目从不承认无知。

2. **批判必须有靶子** — 不许空泛的"当然它也有局限"。必须具体：谁在什么场景踩了什么坑（引 voices.json 的真实社区声音），或这个设计牺牲了什么换了什么。

3. **生活场景必须承重** — 类比不是装饰，是理解的脚手架。判据：**删掉这个类比，听众还能不能答出"为什么这么设计"**？能——类比是废话，删掉；不能——类比在承重，留下。

### 5.3 求职者视角怎么落地

**不做成单独段落**（生硬），融进老张的提问：

> 老张："这个 block_size 的选择，面试要是问到，该答到什么程度？"
> 阿凯："初面说清楚它是内存碎片和调度灵活性的权衡就够了。但我看牛客上有人被追问到要口算——那就得知道……"

**配额纪律**：求职话题**每期至多两处**，且必须挂在真实 voices 条目上（面经/社区/在职者平台），不许凭空说"面试会考"。避免节目变成面试培训班。

---

## 6. 外部声音：voices.json

### 6.1 源类

**批判源**：论文作者的澄清、GitHub issue 的争论、权威技术博客的反驳、竞品的不同选择。

**求职者源（社交平台评论区，国内外）**：
- 国外：X（回复串是重点，不只主贴）、Reddit（r/cscareerquestions、r/MachineLearning、r/ExperiencedDevs）、Hacker News 评论区、Blind、LinkedIn 评论
- 国内：知乎（回答 + 评论）、V2EX、牛客面经区、脉脉、小红书、B站评论区、即刻

取材角度四类：这个技术在面试里怎么被考（问到什么深度、哪些是八股哪些真考理解）、社区对这个技术栈的前景判断、转岗/选型焦虑、在职者回头看面试题的落差感。

### 6.2 字段

```json
{
  "id": "voice-001",
  "category": "job-seeker",        // critical（批判源）| job-seeker（求职者源）
  "term": "PagedAttention 的内存换算",
  "claim": "「面试官让我口算 8 卡 A100 跑 7B 模型、batch=32、seq=2048 时 KV cache 占多少显存」",
  "verified": "claim-self-checked",
  "source_url": "https://www.zhihu.com/question/xxx/answer/yyy",
  "source_date": "2026-07-15",
  "source_platform": "zhihu",
  "speaker_handle": "@匿名（面经答主）",
  "anonymized": true,
  "confidence": "high",
  "writer_note": "用在 ep03 开场钩子作「面试的尺度感」反差；只转述不挂人"
}
```

- `verified`：`official`（官方/作者一手）| `claim-self-checked`（转述且已核实其技术内容）| `community-only`（只能证明有人这么说）
- `confidence`：`high`（一手权威核实）| `medium` | `low`（说清哪里没核实）
- `source_platform`：`zhihu | v2ex | niuke | maimai | xhs | bili | jike | reddit | hn | x | blind | linkedin | official | paper | github-issue`

### 6.3 取证纪律（写进 researcher 契约）

1. 每条带 `source_url` + `source_date` + `confidence`，**不靠模型记忆现编**——评论区尤其是幻觉重灾区。
2. **评论 ≠ 事实** — 一条高赞吐槽只能证明"有人这么认为"，不能证明"事情就是这样"。`claim`（他说了什么）与 `verified`（这说法有没有被核实）是两层，writer 引用时必须保留这个差别。
3. **不点名素人** — 大V/作者/官方账号可指名（本就是公开发言）；普通用户只做**匿名化转述**（"牛客上一条高赞面经提到…"），不搬 ID、不搬原文截图。既是隐私，也免得节目变成挂人。
4. **平台代表性偏差要标出来** — Blind 的薪资焦虑和牛客的应届焦虑不是同一群人，writer 引用时得知道自己在引哪个池子。
5. **时效性** — 面经半年就过时。voices 有保质期，3 个月后需刷新（写进 SHOW.md 硬规则）。

### 6.4 原声引述的三档策略

引述素材带 `original_text + source + speaker_handle`，TTS 站可选：
- **(a) 按原说话人音色重新合成** — 最轻、最不挂人（默认）
- **(b) 用真实音频片段** — 需授权
- **(c) 只标引述不带音色** — 由阿凯/老张转述

---

## 7. TTS：本地 GPU

### 7.1 硬件（本机已核实 2026-08-01）

```
NVIDIA RTX PRO 6000 Blackwell Workstation Edition
95.6 GB 显存 | CUDA 13.1 | Driver 591.86 | torch 2.11.0+cu130
```

CUDA 生态全可用，无 ROCm 顾虑。95.6GB 意味着 8B 级对话模型毫无压力，可并行加载多模型做对比。注意本机可能有其他进程占用显存（观测到 3.9GB），audio-qa 站报告 VRAM 占用。

> **2026-08-10 换机**：本机已改为 NVIDIA GeForce RTX 5080 16GB / CUDA 13.0 / torch 2.11.0+cu130。§7.1 的硬件记录保留为原始设计上下文；IndexTTS-2 推理约需 3-4GB 显存，16GB 可用。当前实况见 CLAUDE.md「TTS 环境」。

### 7.2 选型（2026-08-08 定案）

**唯一主方案：IndexTTS-2 单句合成**（逐 turn 独立生成）

| 判据 | 数据 |
|---|---|
| 合成方式 | **逐 turn 独立生成**（`indextts_synth_singleturn.py`），无跨 turn 上下文累积 —— 解决 FireRed 逐段/carryover 的尾部喃喃伪影 |
| 中文克隆质量 | laozhang/akai 参考克隆清晰，无读标签、无明显音色漂移；**尾部伪影仅 4/156（ep01），且可重生成修复**（FireRed 为 16/156） |
| 参考音色 | 内置 laozhang/akai（16kHz mono，零样本克隆，无需 voice_map） |
| 协议 | Apache-2.0（权重开源，IndexTeam/IndexTTS-2） |
| 显存/环境 | conda env `itts310`（Python 3.10 + torch 2.8.0+cu128），子进程隔离 |
| 速度 | RTF ~1.8-2.0（单句逐 turn；比 FireRed 1.2 略慢但**干净**） |

**定案理由（2026-08-08 实测）**：
- FireRed 逐段合成存在**尾部喃喃伪影**（模型说完正文后多吐一段不成语言的咕哝），ep01 实测 16 处，逐段/carryover 两种分段策略均触发；carryover 还引入 S1/S2 串色（上下文污染）。
- IndexTTS-2 单句合成逐 turn 独立，天然免疫上下文污染类伪影；ep01 全量检测仅 4 处轻微伪影，且换 seed 重生成即修复。
- IndexTTS-2 附带原生拼音/IPA 发音标注能力（备用，可正面替代"CUDA→库达"谐音替换）。

**FireRed（firered-tts2）已弃用**（尾部伪影不可接受），保留代码仅作历史参考。其余历史排除项（MOSS-TTSD / SoulX / Qwen3 / CosyVoice3 / vLLM-Omni / F5-TTS / VibeVoice 等）同 2026-08-07 调研结论。

**发音表（2026-08-07 researcher 调研）**：`shows/<name>/season/pronunciation.json` — 合成前把专有名词替换为注音读法（SGLang→SG浪、vLLM→V-L-L-M、CUDA→库达、KV cache→K-V缓存 等），防 TTS 逐字母念。词条带 confidence + source_url。

### 7.3 抽象层

唯一 provider 为 IndexTTS-2，抽象层保留以隔离 CLI/工作流：

```python
class TTSProvider(Protocol):
    def synthesize(self, script: Script, voice_map: dict, opts: TTSOpts) -> AudioBundle: ...
    def list_voices(self) -> list[VoiceSpec]: ...
    @property
    def native_dialogue(self) -> bool: ...

class LocalTTSProvider:
    """本地基类：GPU 设备管理、模型预热、显存监控"""
    def warmup(self): ...
    def vram_report(self) -> dict: ...

class IndexTTS2Provider(LocalTTSProvider):
    """IndexTTS-2 单句合成（唯一主方案）。
    子进程调用 conda env itts310 的 indextts_synth_singleturn.py：
    逐 turn 独立 infer（无跨 turn 上下文），按 S1/S2 选内置参考音色，
    应用 pronunciation.json 注音替换，concat 输出 22050Hz episode.wav。
    停顿由模型生成，production-notes 的停顿建议是软提示（改写文本节奏）。"""
    native_dialogue = True
```

**输入是结构化 `Script` 对象**（不是 raw markdown）——说话人/停顿/重音/引述嵌入点全是结构化字段，provider 自己负责标签转换。

**对 producer 的影响**：IndexTTS-2 单句模式下停顿由**模型生成**，停顿建议是"改写文本节奏引导模型"的软提示，不写死毫秒。

---

## 8. BookSource 抽象

```python
class BookSource(Protocol):
    def load(self) -> Book: ...
    def chapter_cards(self) -> list[ChapterCard]: ...
    def glossary(self) -> dict: ...
    def outline(self) -> Outline: ...

class Repo2BookSource(BookSource):
    """从 repo2book 实例目录抽取——当前唯一实现。
    读 cartography/outline-final.json + artifacts/ch*/dossier(mechanisms) +
    artifacts/ch*/narrative/chapter.md + book/bible/glossary.json，
    归一化成本项目的 Book 结构。"""
```

**摄入即快照**：`scripts/ingest_book.py` 把书源归一化落盘到 `shows/<name>/source-book/`，此后 pipeline **只读快照**，不再触碰外部路径。

三个好处：
1. **仓库自包含** — clone 下来就能跑，不要求机器上存在其他项目
2. **书源漂移不是隐患** — 书更新不会静默改变已产出的节目；要更新是显式 `ingest_book.py --refresh`，digest 变化被记录
3. **抽象验证更真** — epub/markdown adapter 只需产出同样的快照结构，pipeline 无感

路径无效 / instance 无效时直接拉闸，不静默降级。

后续可加 `EpubSource` / `MarkdownSource` / `PdfSource`，不动 pipeline。

---

## 9. 目录结构

```
Devpodcast/
├── CLAUDE.md                      通用操作手册（书无关），每会话自动加载
├── devpodcast.json                顶层注册表：active_show + 节目清单
├── README.md
│
├── .claude/
│   ├── agents/                    8 个持久角色提示词
│   │   ├── planner.md
│   │   ├── book-analyst.md
│   │   ├── researcher.md
│   │   ├── hook-engineer.md
│   │   ├── writer.md
│   │   ├── producer.md
│   │   ├── reviewer.md
│   │   └── archivist.md
│   ├── workflows/
│   │   ├── season-pipeline.js     Phase A
│   │   ├── episode-pipeline.js    Phase B
│   │   ├── season-retrofit.js     中途修整季
│   │   └── lib/                   resolve-cfg / revise-routing（自维护）
│   └── skills/                    项目专属技能（口播文本规范等）
│
├── schemas/                       9 个产物契约 schema
│
├── scripts/
│   ├── book_source.py             BookSource 抽象 + Repo2BookSource
│   ├── ingest_book.py             快照摄入 CLI
│   ├── show_resolver.py           活动节目定位
│   ├── new_show.py                新建节目 scaffold
│   ├── season_plan.py             season-plan CLI
│   ├── season_bible.py            Season Bible CLI（due/payoff/glossary）
│   ├── archivist.py               trace / 长期记忆
│   ├── tts.py                     TTS 抽象 + 本地实现
│   ├── audio_qa.py                试听质检
│   ├── voice_budget.py            时长/节奏预算
│   ├── lint_script.py
│   ├── lint_voices.py
│   ├── lint_punct.py
│   ├── lint_anchors.py
│   └── lint_trace.py
│
├── tests/                          §12.2 单元测试
│
├── docs/superpowers/
│   ├── specs/                     设计文档
│   ├── ARCHITECT-RUNBOOK.md       发车/监控/逃生舱/续跑
│   └── experience-ledger.md       经验回流台账
│
└── shows/<name>/                  一档节目 = 一个实例
    ├── devpodcast.json            节目配置
    ├── SHOW.md                    当前状态 + 专属硬规则
    ├── source-book/               ★ 书源快照（摄入后只读）
    │   ├── book.json
    │   ├── outline.json
    │   ├── chapter-cards/*.json
    │   └── glossary.json
    ├── season/
    │   ├── season-plan.json
    │   ├── arc.json
    │   ├── voices.json
    │   └── bible/
    │       ├── glossary.json      术语口播译名（书面语 → 口语）
    │       ├── voice-guide.md     ★ 声线人格定义（Lead 落笔）
    │       ├── arc-map.json       议题依赖 + 伏笔/回收登记
    │       └── voices-index.json  voices 引用台账
    ├── trace/                     长期记忆（archivist 持有）
    ├── voice-samples/             音色克隆的 prompt 音频
    └── episodes/ep01-slug/
        ├── episode-card.json
        ├── script.md              ★ writer 唯一有权写
        ├── production-notes.md
        ├── audio/
        │   ├── episode.wav
        │   ├── segments/
        │   └── audio-qa.json
        ├── shownotes.md
        └── reviews/
            └── run-ledger.json
```

### 9.1 节目配置

```json
{
  "show": "vllm-podcast",
  "title": "把 vLLM 拆开讲",
  "book_source": {
    "kind": "repo2book",
    "root": "<用户提供的路径，不预设>",
    "instance": "vllm",
    "ingested_at": "2026-08-01",
    "snapshot_digest": "sha256:..."
  },
  "audience": {
    "profile": "对 LLM 推理有兴趣的工程师 + 正在准备相关面试的求职者",
    "assumed_knowledge": ["Python", "Transformer 基本概念"],
    "language": "zh-CN"
  },
  "format": {
    "hosts": 2,
    "target_minutes": 35,
    "episodes_planned": null
  },
  "tts": {
    "provider": "moss-ttsd",
    "fallback": "cosyvoice3",
    "voice_map": {"S1": "voice-samples/laozhang.wav", "S2": "voice-samples/akai.wav"}
  }
}
```

---

## 10. Schema 清单（`schemas/`）

| Schema | 内容 |
|---|---|
| `book.schema.json` | 书的元数据 + digest |
| `season-plan.schema.json` | N 期议题 + 依赖 + 钩子 + 伏笔/应回收 |
| `episode-card.schema.json` | 议题 / 跨章切片 / 必讲要点 / voices 引用 |
| `voices.schema.json` | §6.2 的字段 |
| `arc.schema.json` | 每期开场/收尾/争议框架/伏笔映射 |
| `script.schema.json` | 双说话人轮换 + 停顿标记 + 引述嵌入点 |
| `production-notes.schema.json` | 仅建议，每条带 script 行号 |
| `audio-qa.schema.json` | 试听报告 |
| `season-bible.schema.json` | glossary / voice-guide / arc-map / voices-index |

---

## 11. 错误处理

### 11.1 逃生舱（`status=BLOCKED` → 立即中止升级 Lead）

| 站点 | 拉闸条件 |
|---|---|
| planner | 书的素材不足以支撑议题驱动（章节太少/太碎/无要点清单） |
| book-analyst | 议题在书里找不到足够支撑，或跨章切片自相矛盾 |
| researcher | 关键议题**查不到任何可信外部声音**——不许编，升级让 Lead 决定"降级为纯书内讨论"还是"换议题" |
| writer | episode-card 与 voices 冲突（书说 A，社区一致说 B）且无法在脚本里诚实呈现张力 |
| tts-engine | 音色样本质量不足 / 显存不够 / 模型加载失败 |
| reviewer | 发现事实错误但 writer 三轮改不动 |

**宁可拉闸，不要产出错误成果一路跑到底。**

### 11.2 有界回环

| 回环 | 上限 | 超限动作 |
|---|---|---|
| writer ↔ producer | 2 | 升级 Lead 裁定节奏问题 |
| writer ↔ reviewer | 3 | `review-exhausted` → 升级 |
| tts-engine ↔ audio-qa | 2 | 升级 Lead |

### 11.3 不做降级路径

**TTS 是必经站。** 环境没配好 = `BLOCKED`，不给"先出脚本、音频待补"的后门。理由：音频是交付物的一半，允许绕过会让整条链路的质量约束形同虚设。

**唯一允许的部分降级**：researcher 查不到某议题的求职者声音 → 该期标 `voices_coverage=partial`，writer 不硬编，reviewer 知情降低该维度权重。**必须显式落盘到 run-ledger.json，不许静默**（静默截断读起来像"全覆盖了"，实际没有）。

---

## 12. 测试策略

### 12.1 确定性 linter（无 LLM，秒级，前置于评审）

```bash
python3 scripts/lint_script.py <ep_dir>/script.md
  # 双说话人标记合法（每段有 speaker）/ 停顿标记格式 / 引述嵌入点有对应 voices.id
  # 时长预算不超标（按语速估算）/ 单段不超过 N 字（口播换气）
  # 零脚手架泄漏 / 三条内容纪律的机械可查部分
  #   （"我不知道"是否出现——warn 级提示而非阻断，避免语境误报如"你以为我不知道吗"）

python3 scripts/lint_voices.py <show>/season/voices.json
  # ① source_url + source_date 必填
  # ② anonymized=false 仅允许官方/作者/已认证账号（source_platform ∈
  #    {official, paper, github-issue}，或社区平台上凭认证凭据）
  # ③ confidence=low 须 writer_note 显式标注"未一手核实"
  # ④ 同一 term 至少 2 条不同平台（除非 verified=official），否则 warn 单一来源风险
  # ⑤ category=job-seeker 条目：source_platform 必须落在求职者源平台集合内
  #    （zhihu | v2ex | niuke | maimai | xhs | bili | jike | reddit | hn | x |
  #    blind | linkedin），保证求职者视角在数据层就有保证

python3 scripts/lint_punct.py --all      # 半角标点（口播文本可读性）
python3 scripts/lint_anchors.py --all    # 跨期引用链接有效
python3 scripts/lint_trace.py <ep_dir>   # 脚本引用的每条 claim 能在 voices.json 找到原文
```

### 12.2 单元测试（pytest，TDD）

```
tests/test_book_source.py       Repo2BookSource 读取 + 归一化字段完整
tests/test_ingest.py            快照摄入 / digest / --refresh
tests/test_season_plan.py       schema 校验 / 依赖环检测
tests/test_script_parser.py     script.md → Script 对象（说话人/停顿/嵌入点）
tests/test_tts_abstraction.py   Provider 协议 / voice_map（mock provider，不跑真模型）
tests/test_audio_qa.py          削波检测/时长计算/静音段检测（合成测试音频）
tests/test_linters.py           每个 linter 的正例/反例
```

按 test-driven-development 纪律：先写测试再写实现。

### 12.3 LLM 评审（6 维并行，最后跑）

| 维度 | 看什么 |
|---|---|
| 事实准确 | 每个技术断言能在 episode-card 找到支撑；数字不漂移 |
| 批判强度 | 是不是只有赞美？争议有没有真展开？反方立场有没有被公平呈现？ |
| 口播可懂 | 闭眼只听能不能跟上？有没有依赖视觉的表述（"如图"、"看这段代码"）？术语首现有没有口头解释？ |
| 双声线平衡 | 两人是不是各有性格？有没有一方沦为"嗯嗯对对"的捧哏？ |
| 求职者共鸣 | 求职视角有没有落到具体场景？还是空泛的"这个技术很重要"？ |
| 原声保真 | 引述有没有被曲解？claim vs verified 的层次有没有保持？匿名化有没有做到？ |

### 12.4 端到端冒烟（人工）

**第一个真实验证目标**：拿一本书跑通 1 期，**人工听完整音频**，判定三问：
- 听得懂吗？（不看脚本）
- 有意思吗？（批判和生活场景真的落地了吗）
- 两个人像人吗？（不是两个 TTS 在轮流念稿）

**这一关过不了，pipeline 再漂亮也没用。**

---

## 13. Milestones

| M | 验收标准 | 阻塞什么 |
|---|---|---|
| **M0 骨架 + 环境** | CLAUDE.md + 8 个 agent 提示词骨架 + 空 workflows + devpodcast.json + README + show_resolver 跑得通；**用 IndexTTS-2 跑通一段样例合成**（2026-08-08 定案） | 一切 |
| **M1 一期能听** | 书源摄入 → Phase A → ep01 → 脚本 + wav + audio-qa.json；**人工完整听一遍**，通过 §12.4 三问 | pipeline 真伪验证 |
| **M2 一季跑通** | 整季 5–8 期全部走通；Season Bible 在最后两期被有效回收 | 整季编排是否可行 |
| **M3 抽象层验证** | 写一个 MarkdownSource（或 EpubSource），用它产出一期对比；BookSource 抽象真的不用重构 | "给一本书就能生成"承诺的真伪 |
| **M4 经验回流** | 至少一次 retro → 经验候选 → 落进 linter/契约/RUNBOOK → 台账验证生效 | 工厂是否自我进化 |

**M1 优先于一切**——连一期都没让真人听过，后面的 milestone 是空中楼阁。

---

## 14. 风险

| # | 风险 | 应对 |
|---|---|---|
| 1 | **TTS 是单点故障** — 模型加载失败、显存抖动、合成超时 | IndexTTS-2 子进程隔离（独立 conda env itts310）；加载失败即 BLOCKED 升级 Lead，无静默降级 |
| 2 | **TTS 尾部喃喃伪影** — 自回归模型正文后多吐咕哝声 | IndexTTS-2 单句逐 turn 独立生成（无上下文累积）大幅规避；残余伪影换 seed 重生成修复 |
| 3 | **求职者声音过时** — 面经半年就过时 | 写进 SHOW.md：voices 有 3 个月保质期，到期刷新 |
| 4 | **researcher 找不到某议题的声音** | §11.1 逃生舱兜底，允许议题降级或删除，不许编 |
| 5 | **book-analyst 跨章切片质量** — 这是 devpodcast 的新增逻辑，最容易踩坑 | M1 选最容易切片的议题验证（如内存管理天然跨多章） |
| 6 | **voice-guide 一锤定音后难改** — 听众会期待一致声线 | M1 用最小集（两个说话人 + 三条纪律），留余地；M2 后再扩充 |
| 7 | **书源漂移** — 源书还在更新 | 快照摄入 + digest 记录；显式 `--refresh` 才更新 |

---

## 15. 非目标（YAGNI）

| 不做 | 理由 |
|---|---|
| 播客平台自动发布（Apple/Spotify/小宇宙） | 运营不在范围，M3 后再议 |
| 封面图自动生成 | 文字节目不需要；hook-engineer 可选输出 cover-prompt 但不接生成 |
| 多语种（中英双语一期） | 单语种先跑通 |
| 听众反馈自动归档 | 与发布强耦合 |
| 自定义音色 finetune（GPT-SoVITS 路线） | 与"灵活切音色"冲突 |
| 自动翻译英文论文/issue | researcher 不是翻译机；引原文 + 中文摘要 |
| 多 show 并行 | 单 show 流程先稳 |
| 音频后期（配乐/混音/降噪） | TTS 直出先跑通 |

---

## 16. 待定项

| 项 | 谁定 | 何时 |
|---|---|---|
| 节目名称 / 两个说话人的最终命名 | Lead | 落笔 voice-guide.md 时 |
| 一季几期 | planner | Phase A |
| 第一期议题 | planner | Phase A |
| 单期时长（config 默认 35 分钟，随时可调） | Lead | M1 前 |
| 音色样本从哪来 | Lead | M0 |

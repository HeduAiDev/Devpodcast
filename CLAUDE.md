# devpodcast — 工厂操作手册

> 把一本技术书变成一季**双人对谈播客**——议题驱动、批判先行、引真实社区声音、本地 GPU 合成音频。
>
> **不是**有声书朗读，**不是**章节摘要。侧重**提取要点 + 批判性讨论 + 互联网声音 + 生活场景**。

## 先读 spec

设计真相源：`docs/superpowers/specs/2026-08-01-devpodcast-design.md`。任何实现偏离 spec 都是 bug。

## 架构：两阶段发车

```
Phase A（每本书一次）> Phase B（逐期，可并发）
```

### Phase A — `season-pipeline.js`

```js
Workflow({ name: "season-pipeline", args: { show: "vllm-podcast", episodes: 5 } })
```

`planner` 通读书源快照抽 N 个议题 → `researcher` 真上网查批判声+求职者声 → `hook-engineer` 出钩子/金句/争议框架 → `book-analyst` ×N 并行按议题跨章切片 → `archivist` 建 Season Bible。

### Phase B — `episode-pipeline.js`

```js
Workflow({ name: "episode-pipeline", args: { show: "vllm-podcast", ep_id: "ep01", target_minutes: 35 } })
```

`writer` 主笔（唯一有权写 script.md）→ `producer` 提意见（只建议，不改稿）→ `writer` 定稿 → TTS 本地 GPU 合成 → audio-qa 质检 → `reviewer` 6 维并行评审 → `archivist` 归档+回写 Bible。

## HARD RULES（铁律，不可绕过）

1. **叙事守护** — 只有 writer 可写 `script.md`。质量不对就改提示词，不改脚本内容。producer 只写 `production-notes.md`，每条带 script 行号。
2. **producer 不改稿** — 连 typo 都只写进 note，绝不碰 script.md。
3. **零脚手架泄漏** — 脚本是正式节目，不提 `episode-card` / `voices.json` / `arc.json` 等内部文件名。
4. **researcher 不编** — 查不到就标 low confidence 或拉逃生舱（`status=BLOCKED`），不许凭记忆写。
5. **TTS 是必经站** — 环境没配好 = BLOCKED，不给"先出脚本、音频待补"的后门。
6. **逃生舱** — 任一阶段 `status=BLOCKED` → 立即中止升级 Lead。**宁可拉闸，不要产出错误成果一路跑到底。**

## 角色清单（8 个，`.claude/agents/`）

| 角色 | 产物 | 阶段 | 模型 |
|---|---|---|---|
| **planner** | `season-plan.json` | Phase A | sonnet |
| **hook-engineer** | `arc.json` | Phase A | sonnet |
| **researcher** | `voices.json` | Phase A | sonnet |
| **book-analyst** | `episode-card.json` | Phase A | sonnet |
| **writer** | `script.md` | Phase B | opus |
| **producer** | `production-notes.md` | Phase B | sonnet |
| **reviewer** | `reviews/*.json` | Phase B | opus |
| **archivist** | Season Bible + trace | Phase A/B | sonnet |

## 常用命令

### 节目管理

```bash
python3 scripts/new_show.py <name>              # 新建节目 scaffold
python3 scripts/show_resolver.py                # 查看当前活动节目
DEVPODCAST_SHOW=demo python3 scripts/show_resolver.py  # 环境变量覆盖
```

### 书源摄入

```bash
python3 scripts/ingest_book.py <repo2book-root> <instance> --show <name>
```

### Linter（确定性门禁，无 LLM，秒级）

```bash
python3 scripts/lint_script.py <ep_dir>/script.md --voices <season>/voices.json --target-minutes 35
python3 scripts/lint_voices.py <season>/voices.json
python3 scripts/lint_punct.py <ep_dir>/script.md
python3 scripts/lint_anchors.py <ep_dir> <show_dir>
python3 scripts/lint_trace.py <ep_dir> <season>/voices.json
```

### 工具

```bash
python3 scripts/audio_qa.py <audio>/episode.wav <audio>/audio-qa.json <target_minutes>
python3 scripts/season_bible.py due <season>/bible/arc-map.json <ep_id>
python3 scripts/season_bible.py register <season>/bible/arc-map.json <ep_id> '<json>'
python3 scripts/archivist.py <show>/trace log "<msg>" <kind>
```

### 运行工作流

```bash
# Phase A：整季编排
# （在 Claude Code 会话中）
Workflow({ name: "season-pipeline", args: { show: "vllm-podcast", episodes: 5 } })

# Phase B：单期制作
Workflow({ name: "episode-pipeline", args: { show: "vllm-podcast", ep_id: "ep01", target_minutes: 35 } })

# 监控
/workflows
```

### 测试

```bash
python3 -m pytest tests/ -v
```

## 书写纪律（writer 必须遵守）

- **speaker 标记**：每段 `[S1]…[/S1]` 或 `[S2]…[/S2]` 成对闭合
- **voices 引用**：`{{voice:<id>}}` 嵌入到发言中，id 必须在 voices.json 真实存在
- **显式停顿**：`<break Nms>`（如 `<break 500ms>`）
- **每期至少一次"我不知道"** — 这是反 AI 播客的最强信号
- **批判必须有靶子** — 不许空泛"当然它也有局限"，必须引用真实社区声音
- **生活场景必须承重** — 删掉类比后听众答不出"为什么这么设计"，类比才有资格留下
- **单段 ≤200 字**（口播换气）、任一方 turn 占比 ≥30%（防捧哏）

## 三层真相源（互不替代）

1. **`episode-card.json`** — 议题内容真相源（书里怎么说）
2. **`voices.json`** — 外部声音真相源（别人怎么说）
3. **`season-plan.json`** — 编排真相源（这一季怎么走）

## 独立仓库原则

devpodcast 是完全独立的代码仓，零运行时跨仓依赖：
- 不 import 其他项目代码，不读其他项目路径，不做 submodule
- 书源经 `ingest_book.py` 快照摄入到 `shows/<name>/source-book/` 后**只读**
- clone 下来就能跑

## 目录速查

```
shows/<name>/source-book/      ★ 书源快照（摄入后只读）
shows/<name>/season/           Phase A 产物（season-plan / arc / voices / bible）
shows/<name>/episodes/<slug>/  Phase B 产物（episode-card / script / audio / reviews）
shows/<name>/trace/            长期记忆（archivist 持有）
.claude/agents/                8 个持久角色提示词
.claude/workflows/             season-pipeline.js / episode-pipeline.js
schemas/                       9 个产物契约 schema
scripts/                       Python 脚本（linter / TTS / QA / 工具）
tests/                         pytest 单元测试
docs/superpowers/              设计规格 + 发车手册 + 经验台账
```

## TTS 环境

- GPU: NVIDIA GeForce RTX 5080 16GB, CUDA 13.0（2026-08-10 换机，原 RTX PRO 6000 Blackwell 95.6GB 已不在）
- **唯一主方案: IndexTTS-2 单句合成**（2026-08-08 定案；逐 turn 独立生成，无跨 turn 上下文累积，解决 FireRed 逐段/carryover 的尾部喃喃伪影）
- 模型环境：conda env `itts310`（Python 3.10 + torch 2.8.0+cu128）+ 权重 `models/indextts2/`（gpt.pth 3.3G + s2mel.pth 1.2G + qwen 情感模型 1.2G）—— **2026-08-10 换机后已重建，smoke test RTF 1.73 通过**
- 调用：`D:/miniconda3/envs/itts310/python.exe scripts/indextts_synth_singleturn.py <episode_dir>`，或 `python scripts/tts.py synthesize <script.md> --provider indextts2 --output <dir>`
- 换机重建要点（2026-08-10 实测，见 `docs/superpowers/ARCHITECT-RUNBOOK.md`「TTS 环境」）：
  - 代码与权重是**两个地址**：代码 `git clone https://github.com/index-tts/index-tts` → `_diag/index-tts-repo`；权重 ModelScope/HF `IndexTeam/IndexTTS-2`
  - torch 走阿里云镜像 `mirrors.aliyun.com/pytorch-wheels/cu128/` 手动下 whl（`download.pytorch.org` 国内极慢）
  - **transformers 必须 `==4.52.1`**（官方 uv.lock 锁定；新版移除 `OffloadedCache`，import 即挂）；wetext/munch/json5/keras==2.9.0 等按官方 pyproject
  - 首次运行设 `HF_ENDPOINT=https://hf-mirror.com`（自动拉 w2v-bert-2.0/campplus/bigvgan 辅助模型，缓存 `models/indextts2/hf_cache/`）
- 内置参考音色 laozhang/akai（16kHz mono，voice-samples/laozhang_16k.wav / akai_16k.wav），无需 voice_map
- **发音表**：`shows/<name>/season/pronunciation.json` — 合成前替换专有名词为注音读法（CUDA→库达 等），避免逐字母念
- 输出 22050Hz；FireRed（firered-tts2）为历史备选，已因尾部伪影弃用
- 模型详情见 `docs/superpowers/specs/2026-08-01-devpodcast-design.md` §7

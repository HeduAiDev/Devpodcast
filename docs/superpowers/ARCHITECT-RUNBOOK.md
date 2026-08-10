# ARCHITECT-RUNBOOK — devpodcast 发车手册

> 面向 Lead（项目负责人）和 devpodcast 操作员。不是角色契约，不是 spec——是**怎么把车发起来**的操作手册。

## 前置条件

- [ ] 本机有 Python 3.11+ / pytest / torch 2.11+cu130 / soundfile / numpy
- [ ] GPU: NVIDIA GeForce RTX 5080 16GB, CUDA 13.0（2026-08-10 换机，原 RTX PRO 6000 已不在；IndexTTS-2 推理约 3-4GB 显存，16GB 可用）
- [ ] 本仓 `git clone` 到本地，`pip install -r requirements.txt`（如有）或按 spec §7 装好依赖
- [ ] 有一本 repo2book 产出的书（`instances/<name>/` 目录存在）
- [ ] 读过 `docs/superpowers/specs/2026-08-01-devpodcast-design.md`（至少 §0–§5、§11）

## 快速发车

### Step 0: 验证环境

```bash
cd /mnt/e/Laboratory/Devpodcast
python3 -m pytest tests/ -v
```

79 tests passed → 代码层健康。

### Step 1: 新建节目 + 摄入书源

```bash
# 建节目 scaffold（含 voice-guide 模板）
python3 scripts/new_show.py vllm-podcast

# 编辑 voice-guide.md ★ 这是项目灵魂，Lead 亲自落笔
vim shows/vllm-podcast/season/bible/voice-guide.md

# 摄入书源快照
python3 scripts/ingest_book.py /path/to/repo2book vllm --show vllm-podcast

# 验证快照
ls shows/vllm-podcast/source-book/
# 期望看到: book.json / outline.json / glossary.json / chapter-cards/

# 编辑节目配置
vim shows/vllm-podcast/devpodcast.json
# 核对: audience / format.target_minutes / tts.voice_map / episodes_planned
```

### Step 2: Phase A — 整季编排

在 Claude Code 会话中：

```js
Workflow({ name: "season-pipeline", args: { show: "vllm-podcast", episodes: 5 } })
```

**阶段**（在 `/workflows` 可视化面板中监控）：
1. **Plan** — planner 通读书源抽议题，产 `season-plan.json`
2. **Research** — researcher 真上网查批判+求职声音，产 `voices.json`，自动过 `lint_voices` 门禁 + voices_coverage 落盘
3. **Hooks** — hook-engineer 出开场钩子/收尾金句/争议框架，产 `arc.json`
4. **Slice** — book-analyst ×N 并行切片，每期产 `episode-card.json`
5. **Bible** — archivist 建 Season Bible（glossary / arc-map / voices-index / voice-guide → 核对存在）

**期望产物**：
```
shows/vllm-podcast/season/
├── season-plan.json
├── arc.json
├── voices.json
├── voices-coverage.json
└── bible/
    ├── glossary.json
    ├── voice-guide.md
    ├── arc-map.json
    └── voices-index.json

shows/vllm-podcast/episodes/ep01-<slug>/episode-card.json
shows/vllm-podcast/episodes/ep02-<slug>/episode-card.json
...
```

### Step 3: Phase B — 逐期制作

```js
// 第一期
Workflow({ name: "episode-pipeline", args: { show: "vllm-podcast", ep_id: "ep01", target_minutes: 35 } })

// 后续各期（可并发启动多个会话）
Workflow({ name: "episode-pipeline", args: { show: "vllm-podcast", ep_id: "ep02", target_minutes: 35 } })
```

**阶段**：
1. **Write** — writer 写 `script.md`，自动过四 linter 门禁（回环 ≤2 轮）
2. **Produce** — producer 出 `production-notes.md`（只建议带行号，不改稿）
3. **Revise** — writer 采纳/反驳 producer 意见定稿，复跑 linter
4. **TTS** — 本地 GPU 合成 `audio/episode.wav`
5. **AudioQA** — 试听质检（时长/削波/静音），回环 ≤2 轮
6. **Review** — reviewer 6 维并行评审，BLOCKING 回环 writer ≤3 轮
7. **Archive** — archivist 归档 + season_bible register 回写 Bible + shownotes

**期望产物**：
```
shows/vllm-podcast/episodes/ep01-<slug>/
├── episode-card.json
├── script.md           ★ 最终定稿
├── production-notes.md
├── shownotes.md
├── audio/
│   ├── episode.wav
│   ├── segments/
│   └── audio-qa.json
└── reviews/
    ├── run-ledger.json
    ├── r1-factual_accuracy.json
    ├── r1-critical_depth.json
    └── ...
```

### Step 4: 人工验收（spec §12.4）

**三问**：
- 听得懂吗？（不看脚本）
- 有意思吗？（批判和生活场景真的落地了吗）
- 两个人像人吗？（不是两个 TTS 在轮流念稿）

**这一关过不了，pipeline 再漂亮也没用。**

## 逃生舱处理

工作流中任一阶段返回 `status=BLOCKED` → **立即中止，升级 Lead**。

| 场景 | 拉闸原因 | Lead 该做什么 |
|---|---|---|
| planner 拉闸 | 书素材不足以支撑议题驱动 | 换书 / 减议题 / 手工补素材 |
| researcher 拉闸 | 关键议题查不到任何可信外部声音 | 决定降级为纯书内讨论 / 换议题 |
| book-analyst 拉闸 | 议题在书里找不到支撑 / 切片矛盾 | 改议题 / 补章 / 重跑 planner |
| writer 拉闸 | episode-card 与 voices 冲突 | 裁决取舍，可能回溯 researcher |
| lint 门禁耗尽 | 2 轮修复仍未通过 | 手动看门禁输出定位问题 |
| TTS 拉闸 | 模型加载失败 / 显存不够 | 检查环境与 itts310 环境/日志，修好重跑（唯一方案 IndexTTS-2，无 fallback） |
| review-exhausted | 3 轮评审仍 BLOCKING | 改提示词 / 降级问题级别 / 砍期 |

**处理流程**：
1. 看 workflow 返回的 `escalated` 和 `reason`/`note` 字段
2. 确定修复方案
3. 如需续跑：用 `resumeFromRunId` 从断点继续（失败的阶段重跑）

## 续跑

```js
// 修好问题后，从上次断点续跑
Workflow({ scriptPath: ".claude/workflows/season-pipeline.js", resumeFromRunId: "wf_xxxxxx" })
```

**注意**：`resumeFromRunId` 仅在同一会话有效。如果会话已结束，需重新发起完整 workflow——Phase A 产物已落盘的会被复用。

## 监控

- `/workflows` — 实时查看运行中/已完成的工作流
- 每个 agent 的返回都可展开查看详情
- Phase B 多期并行时，每期一个独立 workflow 调用，互不阻塞

## 常见坑

### args 注入

Workflow 的 `args` 参数是 JSON 对象（不是字符串）。如果发车时遇到 `escalated: 'bad-args'`：
- 检查 `show` 字段是否为非空字符串
- `episodes` 是否为正整数（Phase A）
- `ep_id` / `target_minutes` 是否有效（Phase B）
- **不要手工修改 workflow JS 文件内的 CFG 来绕过**——那是仅用于完全未传 args 的手工调试场景

### voices 时效

面经半年就过时。voices.json 有 3 个月保质期。重跑 Phase A 或手动更新 `voices.json`。

### 显存占用

本机 16GB 显存（RTX 5080），IndexTTS-2 推理约需 3-4GB。audio-qa 站报告 VRAM，如不足：
- 检查是否有其他模型加载中（`nvidia-smi`）
- IndexTTS-2 子进程独占加载（itts310 env），合成期间勿同时跑其他大模型

### 书源漂移

书更新不会静默改变已产出的节目。要更新需显式：
```bash
python3 scripts/ingest_book.py /path/to/repo2book vllm --show vllm-podcast --refresh
```
digest 变化会被自动记录到 `book.json`。

### voice-guide.md 缺失

Phase A Bible 阶段只核对 voice-guide.md 存在，**绝不建占位/改内容**——空占位会废掉缺失检查。缺失时必须 Lead 落笔后再重跑 Bible 阶段。

### ep_id 解析

ep_id 可以是完整目录名（`ep01-memory-management`）或前缀（`ep01`）。workflow 用 ls 做机械匹配：
- 恰好一个目录名为 ep_id → OK
- 恰好一个目录以 `ep_id-` 开头 → OK
- 多个 → ambiguous → 拉闸
- 零个 → not-found → 拉闸

### TTS 环境

- **唯一方案：IndexTTS-2 单句合成**（`models/indextts2`，逐 turn 独立生成，解决 FireRed 尾部喃喃伪影）
- 调用：`D:/miniconda3/envs/itts310/python.exe scripts/indextts_synth_singleturn.py <episode_dir>`，或 `python scripts/tts.py synthesize <script.md> --provider indextts2 --output <dir>`
- 环境：conda env `itts310`（Python 3.10 + torch 2.8.0+cu128），子进程隔离
- 内置参考音色 laozhang/akai（`voice-samples/laozhang_16k.wav` / `akai_16k.wav`，16kHz mono），无需 voice_map
- **发音表**：`shows/<name>/season/pronunciation.json` 自动应用（CUDA→库达 等）
- 输出 22050Hz episode.wav + segments/turn*.wav；FireRed（firered-tts2）已因尾部伪影弃用
- 若尾部出现喃喃伪影：对单个 turn 换 seed 重生成（indextts_synth_singleturn.py 逐 turn 独立，可单独重跑某 turn）

## 相关文件

| 文件 | 用途 |
|---|---|
| `CLAUDE.md` | 通用操作手册，每会话自动加载 |
| `docs/superpowers/specs/2026-08-01-devpodcast-design.md` | 完整设计规格（真相源） |
| `.claude/agents/*.md` | 8 个角色提示词 |
| `.claude/workflows/season-pipeline.js` | Phase A workflow |
| `.claude/workflows/episode-pipeline.js` | Phase B workflow |
| `schemas/*.json` | 9 个产物契约 schema |
| `shows/<name>/SHOW.md` | 当前状态 + 专属硬规则（手动维护） |

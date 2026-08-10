# devpodcast

> **把一本技术书变成一季双人对谈播客**——议题驱动、批判先行、引真实社区声音、本地 GPU 合成音频。

不是有声书朗读，不是章节摘要。侧重**提取要点 + 批判性讨论 + 互联网声音 + 生活场景**。

## 快速开始

```bash
# 0. 克隆 + 验证环境
git clone <this-repo> && cd Devpodcast
python3 -m pytest tests/ -v          # 期望: 79 tests passed

# 1. 新建节目 + 摄入书源
python3 scripts/new_show.py vllm-podcast
# 编辑 voice-guide.md（Lead 落笔）→ vim shows/vllm-podcast/season/bible/voice-guide.md
python3 scripts/ingest_book.py /path/to/repo2book vllm --show vllm-podcast

# 2. Phase A：整季编排（Claude Code 会话中）
Workflow({ name: "season-pipeline", args: { show: "vllm-podcast", episodes: 5 } })

# 3. Phase B：逐期制作
Workflow({ name: "episode-pipeline", args: { show: "vllm-podcast", ep_id: "ep01", target_minutes: 35 } })

# 4. 人工听完整音频，过 §12.4 三问
```

## 架构一页图

```
用户指定书源路径
        │
        ▼
┌ ingest_book.py（一次性快照摄入）┐
│ shows/<name>/source-book/       │  ← 此后只读
└───────────────┬─────────────────┘
                │
    ════════════╪════ Phase A ═════════════════
                │
    ┌───────────┼──────────────────┐
    ▼           ▼                  ▼
 planner    hook-engineer    researcher
    │           │                  │
 season-plan  arc.json       voices.json
    │           │                  │
    └──────┬────┴─────────────────┘
           ▼
    book-analyst ×N（并行切片）
           ▼
    episode-card.json ×N
           │
       archivist → Season Bible
           │
    ═══════╪══════════ Phase B ═══════════════
           │
    writer → producer → writer（定稿）
           │
    ┌──────┴──────┐
    ▼             ▼
 4 linter    tts-engine → episode.wav
    │             │
    └──────┬──────┘
           ▼
    reviewer（6 维并行）≤3 轮
           ▼
       archivist（归档 + 回写 Bible）
```

## 角色（8 个）

| 角色 | 产物 | 阶段 |
|---|---|---|
| planner | `season-plan.json` | Phase A |
| researcher | `voices.json` | Phase A |
| hook-engineer | `arc.json` | Phase A |
| book-analyst | `episode-card.json` | Phase A |
| writer | `script.md` | Phase B |
| producer | `production-notes.md` | Phase B |
| reviewer | `reviews/*.json` | Phase B |
| archivist | Season Bible + trace | Phase A/B |

## Linter（确定性门禁，秒级）

```bash
python3 scripts/lint_script.py <ep>/script.md --voices <season>/voices.json --target-minutes 35
python3 scripts/lint_voices.py <season>/voices.json
python3 scripts/lint_punct.py <ep>/script.md
python3 scripts/lint_anchors.py <ep_dir> <show_dir>
python3 scripts/lint_trace.py <ep_dir> <season>/voices.json
```

## 里程碑状态

| M | 验收标准 | 状态 |
|---|---|---|
| **M0 骨架+环境** | CLAUDE.md + 8 agent 提示词 + workflows + README + 测试全绿；TTS 环境打通 | 🟡 进行中（Task 16/17 待完成） |
| **M1 一期能听** | 书源摄入 → Phase A → ep01 → 脚本 + wav；人工听完过三问 | ⬜ 待开始 |
| **M2 一季跑通** | 整季 5–8 期走通；Bible 有效回收 | ⬜ 待开始 |
| **M3 抽象层验证** | 第二个 BookSource 实现产出一期对比 | ⬜ 待开始 |
| **M4 经验回流** | 至少一次 retro → 经验落进 linter/契约/RUNBOOK | ⬜ 待开始 |

## HARD RULES

1. **叙事守护** — 只有 writer 可写 script.md
2. **producer 不改稿** — 只写 production-notes.md 带行号
3. **零脚手架泄漏** — 脚本不提内部文件名
4. **researcher 不编** — 查不到标 low confidence 或拉闸
5. **TTS 必经站** — 无降级后门
6. **逃生舱** — BLOCKED → 立即中止升级 Lead

## 目录结构

```
Devpodcast/
├── CLAUDE.md                     通用操作手册
├── devpodcast.json                顶层注册表
├── README.md
├── .claude/agents/                8 个持久角色提示词
├── .claude/workflows/             season-pipeline.js / episode-pipeline.js
├── schemas/                       9 个 schema
├── scripts/                       Python 脚本（linter/TTS/QA/工具）
├── tests/                         pytest
├── docs/superpowers/              specs + ARCHITECT-RUNBOOK.md
└── shows/<name>/                  节目实例（一个节目 = 一个目录）
    ├── source-book/               ★ 书源快照（摄入后只读）
    ├── season/                    Phase A 产物 + bible/
    ├── episodes/<slug>/           Phase B 产物
    └── trace/                     长期记忆
```

## 文档索引

| 文档 | 读者 | 内容 |
|---|---|---|
| `CLAUDE.md` | AI agent（自动加载） | 通用操作手册 |
| `docs/superpowers/ARCHITECT-RUNBOOK.md` | Lead（人类） | 发车/监控/逃生舱/续跑/常见坑 |
| `docs/superpowers/specs/2026-08-01-devpodcast-design.md` | 全员 | 完整设计规格（真相源） |
| `.claude/agents/*.md` | 各角色 agent | 角色契约 |

## 技术栈

- **语言**：Python 3.11+ / JavaScript（workflow）
- **测试**：pytest
- **TTS**：IndexTTS-2 单句合成（逐 turn 独立生成，Apache-2.0，conda env itts310 / torch 2.8.0+cu128）
- **GPU**：NVIDIA RTX PRO 6000 Blackwell 95.6GB, CUDA 13.1
- **设计参考**：Repo2Book 方法论（仅方法论，零运行时依赖）

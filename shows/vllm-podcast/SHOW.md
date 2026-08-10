# SHOW.md — vllm-podcast 当前状态

## 书源
- kind: repo2book
- root: E:/Laboratory/Repo2Book
- instance: vllm
- ingested_at: 2026-08-02
- snapshot_digest: 588dedb12793c828
- 状态: 已摄入 39 章 + 115 术语 → `source-book/`

## Phase A 进度
- [x] season/season-plan.json | arc.json | voices.json | bible/ 四件套
- [x] episodes/epNN-*/episode-card.json ×5
- [x] **voice-guide.md** — 三人版定稿（2026-08-08：老张主持推进 / 阿凯作者讲解 / 阿哲读者代言人，含口头禅 + 开场/节奏/术语纪律）

## Phase B 进度（三人对话版，IndexTTS-2，cut5 断句方案）
| 期 | turns | 时长 | 峰值 | RMS | QA |
|---|---|---|---|---|---|
| ep01-three-stage-decoupling | 129 | 25.6min | -0.45dB | -16.93dB | ✓ 0 issue（2026-08-11 术语修复后重合成） |
| ep02-engine-heartbeat | 175 | 28.3min | -0.45dB | -16.93dB | ✓ 0 issue（2026-08-11 术语修复后重合成） |
| ep03-memory-and-persistent-batch | 180 | 30.3min | -0.45dB | -17.05dB | ✓ 0 issue |
| ep04-gpu-execution-pipeline | 154 | 28.0min | -0.45dB | -17.08dB | ✓ 0 issue |
| ep05-smart-sampling | 171 | 29.3min | -0.45dB | -17.06dB | ✓ 0 issue |

共 809 turns / 141.5 分钟。ep01/02 含阿凯笔记本修复（Worker/块/调度器/前向问答 + 判据前向预告，见 season/akai-notebook.md 修复记录）。

## 环境状态
- GPU: RTX PRO 6000 Blackwell 95.6GB, CUDA 13.1, torch 2.11.0+cu128 — OK
- TTS: **IndexTTS-2 定案**（2026-08-08，单句逐 turn 合成，conda env `itts310` / torch 2.8.0+cu128，`models/indextts2`）
- voice-samples（16kHz mono）：`laozhang_16k.wav`（老张）/ `akai_16k.wav`（阿凯）/ `azhe_16k.wav`（阿哲），见 voice-samples/README.md
- 发音表：`season/pronunciation.json`（CUDA→库达、SGLang→S G 朗、CamelCase 拆词等）
- 术语审计：`scripts/term_order.py`（S1/S3 首现 vs S2 首解释，防回归门禁）

## 硬规则
- voices 有 3 个月保质期（面经半年就过时），到期刷新。
- TTS 是必经站：环境没配好 = BLOCKED，无降级路径。
- 修改 voice-guide.md 需 Lead 批准。

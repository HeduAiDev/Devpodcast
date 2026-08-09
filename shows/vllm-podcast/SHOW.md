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

## Phase B 进度（三人对话版，IndexTTS-2）
- [x] ep01-three-stage-decoupling: 27.9min，QA 全过，评审 APPROVED
- [x] ep02-engine-heartbeat: 30.7min，QA 全过，评审 APPROVED
- [x] ep03-memory-and-persistent-batch: 32.7min，QA 全过，评审 APPROVED
- [x] ep04-gpu-execution-pipeline: 30.4min，QA 全过，评审 APPROVED
- [x] ep05-smart-sampling: 32.3min，QA 全过，评审 APPROVED

## 环境状态
- GPU: RTX PRO 6000 Blackwell 95.6GB, CUDA 13.1, torch 2.11.0+cu128 — OK
- TTS: **IndexTTS-2 定案**（2026-08-08，单句逐 turn 合成，conda env `itts310` / torch 2.8.0+cu128，`models/indextts2`）
- voice-samples（16kHz mono，归一化 -16dB RMS）：`laozhang_16k.wav`（老张）/ `akai_firered_16k.wav`（阿凯，FireRed 重读慢速稿治连读）/ `azhe_16k.wav`（阿哲，北京话主持人）
- 发音表：`season/pronunciation.json`（CUDA→库达、SGLang→S G 朗、CamelCase 拆词等）

## 硬规则
- voices 有 3 个月保质期（面经半年就过时），到期刷新。
- TTS 是必经站：环境没配好 = BLOCKED，无降级路径。
- 修改 voice-guide.md 需 Lead 批准。

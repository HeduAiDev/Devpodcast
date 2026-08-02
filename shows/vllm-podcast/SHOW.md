# SHOW.md — vllm-podcast 当前状态

## 书源
- kind: repo2book
- root: E:/Laboratory/Repo2Book
- instance: vllm
- ingested_at: 2026-08-02
- snapshot_digest: 588dedb12793c828
- 状态: 已摄入 39 章 + 115 术语 → `source-book/`

## Phase A 进度
- [ ] **voice-guide.md** — 待 Lead 落笔（当前为 scaffold 模板，需敲定老张/阿凯的最终人格细节）
- [ ] **season-pipeline** — 待 voice-guide 定稿后发车
- [ ] season/season-plan.json | arc.json | voices.json | bible/
- [ ] episodes/epNN-*/episode-card.json ×N

## Phase B 进度
- [ ] 待 Phase A 完成

## 环境状态
- GPU: RTX PRO 6000 Blackwell 95.6GB, CUDA 13.1, torch 2.11.0+cu128 — OK
- F5-TTS 验证: 通过（CUDA/torch/flash-attn 链路 OK，不用于生产）
- MOSS-TTSD v1.0: 下载中（8B 权重 ~16GB）
- voice-samples: 待录制（`laozhang.wav` / `akai.wav`，各 5-10s）

## 硬规则
- voices 有 3 个月保质期（面经半年就过时），到期刷新。
- TTS 是必经站：环境没配好 = BLOCKED，无降级路径。
- 修改 voice-guide.md 需 Lead 批准。

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
- [ ] **voice-guide.md** — 待 Lead 落笔（当前为 scaffold 模板，需敲定老张/阿凯的最终人格细节）

## Phase B 进度
- [x] ep01-three-stage-decoupling: script.md + audio（IndexTTS-2 版，1371s，QA 全过）
- [x] ep02-engine-heartbeat: audio（IndexTTS-2 版，1249s，QA 全过）
- [ ] ep03 / ep04 / ep05: 待 IndexTTS-2 重做

## 环境状态
- GPU: RTX PRO 6000 Blackwell 95.6GB, CUDA 13.1, torch 2.11.0+cu128 — OK
- TTS: **IndexTTS-2 定案**（2026-08-08，单句逐 turn 合成，conda env `itts310` / torch 2.8.0+cu128，`models/indextts2`）
- voice-samples: `laozhang.wav` / `akai.wav`（MOSS-TTSD 官方中文示例，临时占位；正式发布前建议换自录中文样本）+ 16kHz 版（laozhang_16k/akai_16k，IndexTTS-2 用）

## 硬规则
- voices 有 3 个月保质期（面经半年就过时），到期刷新。
- TTS 是必经站：环境没配好 = BLOCKED，无降级路径。
- 修改 voice-guide.md 需 Lead 批准。

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

## Phase B 进度 — 全 5 期完成（2026-08-09，cut5 断句方案）
| 期次 | turns | 时长 | 峰值 | RMS | QA |
|---|---|---|---|---|---|
| ep01-three-stage-decoupling | 129 | 25.0min | -0.45dB | -16.93dB | ✓ 0 issue |
| ep02-engine-heartbeat | 175 | 27.7min | -0.45dB | -16.96dB | ✓ 0 issue |
| ep03-memory-and-persistent-batch | 180 | 30.3min | -0.45dB | -17.05dB | ✓ 0 issue |
| ep04-gpu-execution-pipeline | 154 | 28.0min | -0.45dB | -17.08dB | ✓ 0 issue |
| ep05-smart-sampling | 171 | 29.3min | -0.45dB | -17.06dB | ✓ 0 issue |

共 809 turns / 140.3 分钟，全季 RMS 一致性 ±0.08dB。

## 环境状态
- GPU: NVIDIA GeForce RTX 5080 16GB, CUDA 13.0（**2026-08-10 换机**，原 RTX PRO 6000 Blackwell 95.6GB 已不在）— TTS 环境待重建
- TTS: **IndexTTS-2 定案**（2026-08-08，单句逐 turn 合成）— 换机后 conda env `itts310` 与 `models/indextts2` 权重**均未恢复，待部署**（5 期音频已全部完成，短期无合成需求）
- voice-samples: `laozhang.wav` / `akai.wav`（MOSS-TTSD 官方中文示例，临时占位；正式发布前建议换自录中文样本）+ 16kHz 版（laozhang_16k/akai_16k，IndexTTS-2 用）

## 硬规则
- voices 有 3 个月保质期（面经半年就过时），到期刷新。
- TTS 是必经站：环境没配好 = BLOCKED，无降级路径。
- 修改 voice-guide.md 需 Lead 批准。

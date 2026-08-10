# Task 8 Review: lint_voices.py — voices 五条门禁

评审对象：commit `7c16dc4`（scripts/lint_voices.py + tests/test_lint_voices.py，129 insertions）
评审方式：brief 逐条对照 + diff 逐分支核对 + 独立运行验证（54/54 全量测试、11 个本任务测试、5 组手工边界用例、CLI 退出码实测）

## 1. Spec compliance 判定：✅

五条门禁逐条核对（实现与 brief 参考代码逐字一致，且与 spec §12.1 lint_voices 块内容吻合）：

| # | 规则 | 实现 | 核对 |
|---|---|---|---|
| ① | source_url + source_date 必填 → BLOCKING | `if not v.get(...)` ×2，缺失键与空串均捕获 | ✅ |
| ② | anonymized=false 仅允许 OFFICIAL_PLATFORMS → BLOCKING | `not v.get("anonymized", True) and platform not in OFFICIAL_PLATFORMS` | ✅ |
| ③ | confidence=low 须 writer_note 含「未一手核实」→ BLOCKING | 子串检查，缺失 note 默认 "" | ✅ |
| ④ | 同 term <2 平台且无 verified=official → WARN 单一来源 | 按 term 聚合 + set 去重 + official 抑制 | ✅ |
| ⑤ | category=job-seeker 平台必须在 JOB_SEEKER_PLATFORMS → BLOCKING | 集合成员检查 | ✅ |

- 常量逐字：`JOB_SEEKER_PLATFORMS`（12 平台，与 brief 及 spec §6.2 enum 减官方三平台完全一致）、`OFFICIAL_PLATFORMS`（3 平台）— 均逐字。✅
- CLI：`main(argv=None)` + `raise SystemExit`，退出码 0=通过（WARN 不阻断）/ 1=有 BLOCKING / 2=用法错误；`sys.path.insert(0, 仓库根)` 在 import 前；无参守卫返回 2。与 Task 7 lint_script.py 模式逐点一致（已实测：WARN-only → exit 0，BLOCKING → exit 1，无参 → exit 2 + stderr usage）。✅
- 无缺项、无多余项。唯一 scope 说明：spec §12.1 ② 尾部"或社区平台上凭认证凭据"子句无字段可查（schema §6.2 无 credential 字段），brief 规则 ② 未包含，实现从 brief — 正确取舍。
- 注：brief 将门禁标注为"spec §6.4"，实际五条门禁的 spec 出处是 §12.1 的 lint_voices CLI 块（§6.4 是 TTS 三档策略）。内容与 §12.1 逐字吻合，不影响合规判定。

## 2. 偏离裁决：接受（2 处均接受）

1. **`from pathlib import Path` 提升到模块级** — 接受。理由：Task 7 确立的前置模式要求模块级 `sys.path.insert(0, str(Path(__file__)...))`，此处使用 `Path`；brief 仅在 `main()` 内局部导入，照抄即 NameError（模块导入即崩，CLI 和测试同时失效）。提升与 lint_script.py 一致，是最小正确修复。已实测导入、测试、CLI 全部正常。
2. **`main()` 无参守卫返回 2** — 接受。理由：brief 的 `Path(argv[0])` 在空 argv 时 IndexError 裸崩；Task 7 已确立"无参 → stderr usage + 退出码 2"模式（lint_script.py 同名守卫 + 同名测试镜像），本任务评审指令亦将其列为前置约束。已实测 exit 2 + usage 正确。

报告微瑕（不影响裁决）：偏离 1 的表述为"brief 代码在模块级 sys.path 插入处使用 Path 但未导入"——brief 实际并无模块级插入，插入是依 Task 7 模式新增的；事实核心（模块级插入需要模块级 Path 导入）成立。

## 3. 代码质量判定：Approved（Critical 0 / Important 0 / Minor 5）

**验证证据**：
- 全量回归 54/54 passed（含本任务 11 个）；独立复核通过。
- 门禁 ④ 聚合逻辑独立验证：同 term 同平台 2 条 → WARN（set 去重正确区分"不同平台"）；混合 term 仅对单源 term 报警；term 内任一条 verified=official 抑制 WARN（含官方 + 社区混合场景）；空 term/缺 platform 值不崩（by_term 每表至少 1 元素，`plats[0]` 安全）。实现与 brief 参考逐字一致。
- 门禁 ② 正例实测：anonymized=false + github-issue/paper 均正确豁免（exit 0）。
- 测试真实性：10 个 brief 测试 + 1 个 CLI 守卫测试全部为真断言（msg 子串 + level 双条件），非套套逻辑；负例（断言"不出现"）均有对应正例配对。

**Minor（均不阻断）**：
1. `verified_official` 推导式用 `v["id"]` 直接索引（其余全部 `.get()` 防御）— verified=official 且缺 id 的越界数据会 KeyError 裸崩（已复现）。schema §6.2 强制 id，契约内数据不触发；且与 brief 参考逐字一致。建议后续统一为 `.get("id")`。
2. `from collections import Counter` 未使用（brief 逐字保留的冗余导入）。
3. 测试文件 `import pytest` 未使用（brief 逐字保留）。
4. 文件不存在 → FileNotFoundError 裸 traceback（exit 1）— 与 Task 7 lint_script 行为一致（Task 7 评审已接受该语义），守卫只覆盖参数缺失不覆盖 IO。
5. 测试覆盖缺口（brief 层级，非实现者责任）：同平台 2 条 → WARN、混合 term、官方抑制的混合场景、门禁 ② 正例仅测 "official"（paper/github-issue 豁免仅手工验证）未入自动化。

## 4. ⚠️ Cannot verify 清单

1. 父任务"预测 53 通过"的预测本身无法核实（实际 54 = 43 既有 + 10 brief + 1 CLI 守卫，已实测确认；报告算术正确）。
2. spec §12.1 ②"或社区平台上凭认证凭据"子句是否曾被意图强制 — schema 无对应字段、brief 规则 ② 未包含，实现从 brief。判定依据充足，但 brief 作者意图无法核实。
3. brief 门禁出处标注"§6.4" vs 实际 §12.1 的错位原因（内容已核实一致，仅标注问题）。

**结论**：Spec ✅，偏离均接受，Quality Approved。可直接进入 Task 9。

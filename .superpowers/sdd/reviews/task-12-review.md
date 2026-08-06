# Task 12 评审：schemas/ — 产物契约 JSON Schema

评审对象：commit `9de8837`（10 文件，241 insertions）
评审方式：brief 逐项核对 + 偏离独立实测（jsonschema 4.21.1）+ 与 Task 4/10/11 产码交叉核对

## 1. Spec compliance 判定：✅

| 必达物 | 状态 |
|---|---|
| 9 个 draft-07 schema 全量创建（book/season-plan/episode-card/voices/arc/script/production-notes/audio-qa/season-bible） | ✅ 9/9 存在，全部带 `$schema: draft-07` |
| tests/test_schemas.py（brief 逐字） | ✅ 与 brief Step 1 代码逐字符一致；`pytest tests/test_schemas.py -v` = 4 passed |
| 全仓无回归 | ✅ `pytest tests/ -q` = 76 passed（与报告一致） |
| 提交纪律：单 commit、作者 devpodcast、内容仅 schemas/ + tests/ | ✅ `git show 9de8837`：Author `devpodcast <devpodcast@local>`，10 文件 = 9 schema + 1 测试，无杂项 |
| TDD 红→绿 | ✅ 父 commit `6020b89` 无 schemas/ 目录（`git ls-tree` 确认），测试在实现前必红（FileNotFoundError） |
| episode-card / script / season-plan 三 schema | ✅ brief 逐字 |
| script.schema speaker 枚举 | ✅ `["S1","S2"]`，与 `scripts/script_parser.py`（[S1]/[S2] 成对标签）对齐 |
| voices.schema 与 lint_voices 五条门禁同口径 | ✅ 见偏离裁决；15 项 source_platform 枚举逐字 = `lint_voices.py:11-13` 的 JOB_SEEKER_PLATFORMS(12) + OFFICIAL_PLATFORMS(3)；category（critical/job-seeker）、verified（official/claim-self-checked/community-only）、confidence（high/medium/low）枚举与 lint 各门禁取值一致；required 12 字段清单与 brief 逐字 |

缺项：无。多余项：无。

## 2. 偏离裁决：接受（唯一偏离，实测证据充分）

**偏离内容**：voices.schema 从 brief 的 `patternProperties: {"^voice-": ...}` + `additionalProperties: false`（纯容器形态）改为 `definitions.voice-record`（字段/枚举/required 逐字）+ 顶层 `anyOf`（单条记录 or 容器）。

**独立实测**（jsonschema 4.21.1，Python 直跑）：

| 用例 | brief 原形态 | 实现形态 |
|---|---|---|
| 单条记录 `{"id":"v1", ...12 字段}`（= test_voices_schema_accepts_valid 实例） | **REJECTED**（additionalProperties 拒绝 'id'/'category'/...） | ACCEPTED |
| lint_voices 真实容器 `{"v1": {...}}`（= tests/test_lint_voices.py 全部用例形态） | **REJECTED**（`'v1' does not match any of the regexes: '^voice-'`） | ACCEPTED |
| `{"voice-1": {...}}` 容器 | ACCEPTED | ACCEPTED |
| 单条缺 source_url（= test_voices_schema_rejects_missing_url） | — | REJECTED（ValidationError） |
| 容器内成员缺 source_url | — | REJECTED |
| 容器内 source_platform="wechat" | — | REJECTED |
| 单条 category="priority" | — | REJECTED |

**裁决依据**：
1. brief 原形态对 brief 自己的测试实例必挂，与 brief Step 4「Expected: PASS」直接冲突——brief 内部自相矛盾（容器形态 vs 单条记录测试 + lint 容器 key "v1" 无 voice- 前缀）。实现者的选择是唯一能同时满足「测试通过」与「与 lint_voices 真实容器同口径」的路径。
2. 偏离不改变契约内容：enums/required/字段类型全部逐字保留（与 diff 中 `definitions.voice-record` 逐条比对），anyOf 仅放宽「容器 vs 单条」的形状判定；两条分支的拒绝行为（缺字段、非法枚举）均实测生效。
3. 附带收益：原形态连 lint_voices 实际产出的 `{"v1": ...}` 容器都收不了，anyOf 修正了这一点（本项目 tests/test_lint_voices.py 的 `lint_voices({"v1": v})` 是真实消费形态）。

**注意（非偏离）**：lint 五条门禁中的跨字段门禁 ②（anonymized=false 仅限官方平台）、③（low confidence 须 writer_note 标注）、⑤（job-seeker 须求职者平台）在 draft-07 单文档内不可表达（无 if/then），brief 原形态同样不表达；schema 与 lint 的「同口径」落在字段级枚举与 required 上，此为本任务可及的最大口径。见 Minor-1。

## 3. 代码质量判定：Approved

### 分级清单

**Critical**：无。

**Important**：无。

**Minor**：
1. voices.schema 无法表达 lint 跨字段门禁 ②③⑤（anonymized/confidence/category 条件约束），这些约束仍只能由 lint_voices 把关——schema 是"字段级契约"，lint 是"跨字段契约"，分工明确但建议在 schema 注释或未来升级到 draft 2019-09+（if/then）时补齐。属 brief 原形态同样存在的边界，非实现缺陷。
2. `test_all_schemas_are_valid_json` 在 schemas/ 为空时 vacuous pass（glob 空转）；实现者已在报告中如实标注（Concern 3）。brief 逐字，可接受。
3. voices anyOf 下空对象 `{}` 通过「空容器」分支（无 minProperties）——语义上等于"无 voices"，可接受；若需拒绝可加 `minProperties: 1`（非必要）。
4. season-bible 的 arc-map.episodes 成员对象未设 additionalProperties:false，与 `season_bible.py register()` 的 `update(fields)` 任意字段写入行为一致（这是正确选择，仅记录）。

### 与 Task 4/10/11 dataclass 对齐核对（无测试的 5 个 schema，逐一读源码比对）

- **audio-qa.schema.json** ✅：required 七字段 = `AudioQAReport`（audio_qa.py:23-30）逐字；silence_ratio 0..1（len 占比）、duration_s/vram_gb minimum 0、issues 为 string 数组（实际 issue 文本均为 "BLOCKING:/WARN:" 前缀字符串）。
- **book.schema.json** ✅：title/chapters + chapter 六字段 = `Book/ChapterCard.as_dict()`（book_source.py:27-39）逐字；key_classes/mechanisms 为 dict 数组（dossier.json 形状）、sections 为 string 数组（"13.1 ..." 形式）——schema 用 items object/string 与之一致；narrative_path 未进 as_dict，schema 正确未收。
- **season-bible.schema.json** ✅：arc-map.episodes 的 `data["episodes"][ep_id]` 用法（season_bible.py:16-24）与 schema 的 episodes 对象（foreshadow_due/payoff_due 数组）一致，且允许其他字段（register 会 update 任意字段）。
- **arc.schema.json** ✅（前向契约）：opening/closing/controversy/foreshadow_map 四项 required 与 brief 描述一致；controversy=claim/counter/resolution 框架与 foreshadow_map=ep_id→string 数组是合理的最小形状，与 season-plan 的 foreshadow_due/payoff_due 概念自洽。
- **production-notes.schema.json** ✅（前向契约）：ep_dir/script_line/note/severity 与 brief 描述一致；script_line minimum 1（行号语义正确）、severity 四值枚举合理。

## 4. ⚠️ Cannot verify 清单

1. **arc 的 controversy 子结构（claim/counter/resolution）与 production-notes 的 severity 枚举**：本 commit 时点仓库内无任何生产者（grep 全仓无 opening/controversy/script_line 产出代码，属 Task 13/14 agent 契约）。合理性与对齐只能到 Task 13/14 实现时验证；实现者已在 Concern 2 如实声明"以 schema 即契约"的处理策略。若届时形状不符，schema 需回改——评审时点无法排除此风险。
2. **season-bible 的 glossary/voice-guide/voices-index 全量形状**：voice-guide 定为 string、两个 index 定为 term/voice_id→string 映射，均无现存生产者佐证；season_bible.py 目前只产出 arc-map 部分。
3. **报告声称的 Step 2 具体失败形态**（3 failed FileNotFoundError + 1 vacuous pass）：已通过父 commit 无 schemas/ 目录间接证实红相存在，具体到每条 traceback 未复跑（需临时检出父 commit 工作区，评审判定不必要——红相已由 `git ls-tree 6020b89` 证实）。
4. **lint_voices 在实际剧集数据（非测试 fixture）上的完整容器 key 分布**：仓库 fixtures 中无真实 voices.json 产物；"容器 key 是 v1 无 voice- 前缀"由 tests/test_lint_voices.py 的 `{"v1": v}` 用例证实，真实产物形态待 Task 13 产出后复验（若届时出现 voice- 前缀 key，anyOf 分支 2 仍可容纳，无回归风险）。

## 结论

- Spec compliance：✅（9/9 schema + 测试逐字 + 纪律合规，无缺项/多余项）
- 偏离：接受（brief 原形态实测拒绝 brief 自身测试与 lint 真实容器，anyOf 修正且不破坏任何分支）
- 质量：Approved（0 Critical / 0 Important / 4 Minor）

# Task 12 报告：schemas/ — 产物契约 JSON Schema

状态：DONE_WITH_CONCERNS
提交：`9de8837`（feat/m0-m1）

## 做了什么

按 brief Step 1–5 完成：

1. **Step 1** — `tests/test_schemas.py`（brief 逐字，4 个测试）：
   - `test_all_schemas_are_valid_json`：9 个 schema 全部可解析
   - `test_voices_schema_accepts_valid` / `test_voices_schema_rejects_missing_url`：voices 单条记录收/拒
   - `test_episode_card_schema`：episode-card 样例验证
2. **Step 2** — 确认失败：`schemas/` 不存在，3 failed（FileNotFoundError）/ 1 vacuous pass
3. **Step 3** — 9 个 draft-07 schema：
   - `episode-card.schema.json` / `script.schema.json` / `season-plan.schema.json`：brief 逐字
   - `voices.schema.json`：见下方 Concern 1（一处必要偏离）
   - `arc.schema.json`（season 级容器，key=episode_id，每期 required `opening/closing/controversy/foreshadow_map`；controversy = claim/counter/resolution 框架，foreshadow_map = ep_id → string 数组——对齐 Task 13 hook-engineer 契约）
   - `production-notes.schema.json`（顶层数组，每条 required `ep_dir/script_line/note/severity`；severity = info/suggestion/warning/blocking）
   - `audio-qa.schema.json`（required 对齐 `AudioQAReport` 七字段：duration_s/peak_db/clipping/silence_ratio/rms_db/issues/vram_gb，类型/范围按 dataclass 语义）
   - `season-bible.schema.json`（required `glossary/voice-guide/arc-map/voices-index`；arc-map 含 `episodes`（ep_id → foreshadow_due/payoff_due），与 `scripts/season_bible.py` 的 `data["episodes"]` 用法对齐；glossary/voices-index 为 term/voice_id → string 映射）
   - `book.schema.json`（required `title/chapters`；chapter 项对齐 `Book/ChapterCard.as_dict()` 六字段：chapter_id/title/slug/sections/key_classes/mechanisms）
4. **Step 4** — 4 个测试全过；另加口径自检（见下）
5. **Step 5** — 提交 `9de8837`（10 文件：9 schema + 1 测试，241 insertions）

## 测试命令与输出

```
$ python3 -m pytest tests/test_schemas.py -v
4 passed in 0.21s

$ python3 -m pytest tests/ -q
76 passed in 1.51s   （基线 73 passed + 3 failed（待建）→ 实现后 76 passed，无回归）
```

voices.schema 口径自检（jsonschema 实测）：
- `{"v1": {...全字段}}`（lint_voices 容器形态）→ ACCEPTED
- `{"voice-1": {...}}`（brief patternProperties 形态）→ ACCEPTED
- 容器内单条缺 `source_url` → REJECTED（ValidationError）
- `source_platform` 枚举 15 项逐字 = `lint_voices.py` 的 `JOB_SEEKER_PLATFORMS`(12) + `OFFICIAL_PLATFORMS`(3)；`category`/`verified`/`confidence` 枚举与 spec §6.2、lint 五条门禁同口径；required 12 字段清单逐字来自 brief

## 提交

```
9de8837 feat: 9 个产物契约 schema（voices/episode-card/script/season-plan 等）
```

## Concerns

1. **voices.schema 对 brief 有一处必要偏离（唯一偏离）**。brief 逐字的 schema 是
   `patternProperties: {"^voice-": {...}}` + `additionalProperties: false`（纯容器形态），
   但 brief 自己的两个测试把 schema 当"单条记录"用：实测该形态对 `{"id": "v1", ...}`
   会因 `additionalProperties: false` 拒绝（jsonschema 4.21.1 实测确认，见 Step 2 前验证），
   `test_voices_schema_accepts_valid` 必挂，与 Step 4 要求冲突。且该形态连 lint_voices
   的真实容器 key（`"v1"` 而非 `"voice-"` 前缀）也收不了。
   解决：`definitions.voice-record`（字段/枚举/required 全部逐字）+ 顶层 `anyOf` =
   单条记录 or `additionalProperties: {"$ref": record}` 容器。两条分支都实测通过，
   枚举与 required 清单零改动，与 lint_voices 五条门禁保持同口径。
2. **其余 5 个 schema 无测试覆盖**（brief 只测 voices/episode-card）。arc 的
   controversy 子结构（claim/counter/resolution）与 production-notes 的 severity 枚举
   （info/suggestion/warning/blocking）是本任务定义的新契约，Task 13/14 的 agent 契约
   若产出不同形状，届时以这两个 schema 为准调整（schema 即契约）。
3. `test_all_schemas_are_valid_json` 在 schemas/ 为空时 vacuous pass（glob 为空），
   Step 2 的"失败"实际由其余 3 个测试的 FileNotFoundError 呈现，符合 brief 预期。
4. `.superpowers/` 目录保持 untracked（SDD 工作流目录），本报告未纳入提交；
   提交内容严格按 brief Step 5：`schemas/` + `tests/test_schemas.py`。

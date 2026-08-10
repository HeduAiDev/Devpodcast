# Task 14 报告：8 个持久角色提示词

状态：DONE
提交：`b73ef6b`（feat/m0-m1，8 文件 595 insertions）

## 做了什么

按 brief Step 1–8 写出 `.claude/agents/` 下 8 个持久角色契约，全部对齐 spec §4（角色表 + 硬规则）、§5（voice-guide）、§6（voices 字段/取证/三档引述）、§7.3（TTS provider 停顿语义分支）、§12.3（评审 6 维）与 `schemas/*.json` 的产物形状。正文统一结构：YAML frontmatter（name/description/tools/model/color）→ 开工前读什么 → 产物契约（含 JSON 示例）→ 工作流程 → 铁律 → BLOCKED → 收工自检。

模型分工：writer / reviewer 用 opus（叙事质量与终审判断），其余 6 个 sonnet；researcher 挂 WebSearch/WebFetch 工具。

## 8 个文件的契约点清单

| 文件 | 行数 | 契约点 |
|---|---|---|
| `planner.md` | 81 | 输入 source-book 快照（book/outline/chapter-cards/glossary）+ 节目配置；产物 `season/season-plan.json`（episode_id/slug/topic/hook/depends_on/foreshadow_due/payoff_due，对齐 schema）；议题驱动不按章节一一对应、跨章抽线（判据：每议题 ≥2 章，范例「内存是主角」抽 ch15/16/25）；依赖无环；期数 5–8；素材不足（章节 <6 / 要点全空 / 纯概念堆叠）→ BLOCKED；快照只读 |
| `book-analyst.md` | 77 | 输入 season-plan 议题定义 + chapter-cards + voices.json（只挑关联条目不核实）；产物 `episodes/epNN-<slug>/episode-card.json`（episode_id/slug/topic/cross_chapter_threads/key_mechanisms/voices_refs/narrative_anchors 全 7 字段）；要点源优先级 **sections > key_classes > mechanisms** 专节 + 逐级定义；切片可核对（anchors 必须真实存在）；议题无支撑 / 切片自相矛盾（不许悄悄选边）→ BLOCKED；空 voices_refs = 有意不硬编 |
| `researcher.md` | 83 | 产物 `season/voices.json`（dict 形态，与 lint 遍历一致）；字段纪律照 §6.2 全 12 字段（id/category/term/claim/verified/source_url/source_date/source_platform/speaker_handle/anonymized/confidence/writer_note）+ 三值枚举与 15 个平台枚举逐字对齐 schema；源类 = 批判源 + 求职者源（国内外 12 平台清单 + 国外回复串重点）；四类取材角度；取证纪律 5 条（不靠记忆编 / 评论≠事实 claim vs verified 两层 / 不点名素人匿名化 / 平台代表性偏差标注 / 3 个月时效）；查不到 → BLOCKED 或 low confidence（writer_note 含「未一手核实」），不许编；覆盖缺口显式上报（voices_coverage=partial 落盘 run-ledger）；收工自检跑 lint_voices |
| `hook-engineer.md` | 66 | 输入 season-plan 议题；产物 `season/arc.json`（key=episode_id，opening/closing/controversy{claim,counter,resolution}/foreshadow_map 四件套，对齐 schema）；钩子标准「一句生活化或反直觉的话」（反例：「今天我们聊…」）；收尾标准「不总结，给悬念或行动」；争议双方都站得住、resolution 不许和稀泥；可选 cover-prompt；伏笔映射与 season-plan 互证 |
| `writer.md` | 85 | **唯一有权写 script.md**（叙事守护）；输入 episode-card + voices + arc + Season Bible（voice-guide 强制复用，不读不写）；script.md 格式契约逐字对齐 parser（`[S1]`/`[/S1]` 成对闭合、`{{voice:<id>}}` 必须真实存在、`<break Nms>`）；voice-guide 三条纪律 + 老张/阿凯性格底线；求职者配额（每期至多两处、必须挂真实 voices、融进老张提问不做单独段落）；**原声引述三档策略**（a 重合成=默认 / b 真实片段=需授权，writer_note 未标授权一律不用 / c 转述也包 `{{voice:}}` 保溯源；三档都必须显式标注引述边界 + 保持 claim vs verified 层次 + 匿名化）；零脚手架泄漏（内部词清单）；时长预算（4 字/秒，超 1.15 倍 BLOCKING、单段 ≤200 字）；producer 意见逐条采纳或带理由反驳（receiving-code-review skill）；episode-card 与 voices 冲突无法诚实呈现 → BLOCKED；收工自检跑 lint_script（BLOCKING 清零）+ lint_punct + 边界 grep |
| `producer.md` | 68 | **只写 production-notes.md 不改稿**（typo 也不直接改）；产物对齐 schema（ep_dir/script_line 必填≥1/note/severity 四值）；看什么四类：口播换气（单段 >200 字，指拆段位置）、双声线节奏（三轮短句平了 / 一方独白失衡，对照 voice-guide）、引述前停顿（每个 `{{voice:}}` 嵌入点）、时长预算（超 target×1.15）；**两类 provider 停顿语义分支**（native_dialogue=true MOSS-TTSD = 软提示改写文本节奏不写死毫秒；false CosyVoice3 = 插静音毫秒，说话人切换 350–500ms / 同人句间 150–250ms）；与 reviewer 分工（口播感 vs 内容质量，不重复开清单）；回环 ≤2 轮升级 Lead；收工自检四查 |
| `reviewer.md` | 72 | 6 维并行（事实准确 / 批判强度 / 口播可懂 / 双声线平衡 / 求职者共鸣 / 原声保真，每维结论+证据行号+可执行问题，表格式契约逐字对齐 §12.3）；输出 `reviews/<run>-review.json`（维度结构示例）+ 更新 run-ledger.json；有界回环 ≤3（第 2 轮起只看 fail 维度），第 3 轮后仍有关键问题 → review-exhausted → BLOCKED 升级；**评审无权因风格偏好退稿**（退稿必须指到契约：voice-guide 纪律 / episode-card 支撑 / voices 保真 / 格式契约）；voices_coverage=partial 降级知情（第 5 维降权不退稿）；不改稿 |
| `archivist.md` | 63 | Phase A 建 Season Bible 四件套（glossary 口播译名 / voice-guide 由 Lead 落笔只建占位不改内容 / arc-map 伏笔登记 / voices-index 引用台账），对齐 season-bible schema；Phase B 每期归档：`season_bible.py due` 核对本期应回收伏笔（未回收点名，连续两期欠账升级）→ `register` 回写 arc-map → 解析 `{{voice:...}}` 回写 voices-index → 补录 glossary → `archivist.py log` 写 trace；**每完成一期核对 arc-map**（跨期连贯性，下一期 writer 开工的前置状态）；只回写 bible 与 trace 不改 episode 产物；收工自检含 lint_trace 无 BLOCKING |

## 自检结果

- 8 文件全部存在，frontmatter 五字段（name/description/tools/model/color）齐全、无非法冒号；行数 63–85 均在 60–150 区间
- 脚本验证：8 个文件的 YAML frontmatter 键序与结构正确；全部 ```json``` 代码块（含缩进内嵌的 archivist arc-map 示例）通过 `json.loads` 校验
- 关键词 grep 全命中：researcher 的 source_url/confidence/anonymized/category/writer_note + 12 平台枚举逐字 = schema 枚举；writer 的 voice-guide/`[S1]`/`{{voice:}}`/`<break Nms>`/三档/引述边界/receiving-code-review；producer 的不改稿/script_line/MOSS-TTSD/CosyVoice3 分支/350–500ms；reviewer 的 6 个维度名/review-exhausted/风格偏好
- 无 pytest（提示词任务），验收 = 契约点齐全（见上表），提交 `b73ef6b` 干净（仅 8 个 agents 文件）

## 提交

```
b73ef6b feat: 8 个持久角色提示词（spec §4/§5/§6 落地）
```

## 备注（供 Task 15 参考）

- 角色 ID 即文件名：`planner / book-analyst / researcher / hook-engineer / writer / producer / reviewer / archivist`，workflow 按 agentType 调用即可
- writer/reviewer 用 opus、其余 sonnet；如需统一改模型只动 frontmatter
- researcher 报告契约含「每期素材覆盖（critical/job-seeker）随回复返回」，workflow 负责把 voices_coverage=partial 落盘 run-ledger.json（spec §11.3 不许静默）

---

# FIX ROUND 1（Task 14 评审修复）

状态：DONE

## 修复说明

按评审 2 Important + 2 Minor 逐项修复：

1. **Important #1 — `season_bible.py` register CLI 静默 no-op**：`main()` 增加 `register` 子命令分发（`python3 scripts/season_bible.py register <arc-map.json> <ep_id> <fields-json>`，fields-json 为 JSON 字符串），成功落盘返回 0；参数不足返回 2、非法 JSON 打印错误返回 2、fields 非 JSON 对象返回 2；顺带把未知命令从「exit 0 静默」改为打印错误 + usage 后返回 2（堵死同类 no-op）。数据层 `register(arc_map, ep_id, fields)` 签名未变。USAGE 更新为双命令形态。archivist.md 无需改动，其提示词命令现在真实可用。
2. **Important #2 — writer.md `lint_punct` 缺文件参数**：自检命令改为 `python3 scripts/lint_punct.py <ep_dir>/script.md`（与同节 lint_script 命令的 `<ep_dir>/script.md` 写法一致）。
3. **Minor #1 — researcher.md `original_text` 非 schema 字段**：改为「以 `claim` 字段存原文形态」（voices.schema 12 字段之一），不再诱导产出 schema 非法记录。
4. **Minor #2 — hook-engineer.md voice-guide 缺容错**：开工前读项加「（若已存在，Phase A 由 Lead 落笔）」，与 planner.md 的「若已存在」写法一致，容忍三条腿并行时 bible 尚未建立。

## 测试命令与输出

```
$ python3 -m pytest tests/test_season_bible.py -v
collected 9 items
tests/test_season_bible.py::test_due_empty_bible PASSED
tests/test_season_bible.py::test_due_returns_foreshadow_and_payoff PASSED
tests/test_season_bible.py::test_register_updates_episode PASSED
tests/test_season_bible.py::test_cli_register_writes_arc_map PASSED
tests/test_season_bible.py::test_cli_register_full_archivist_flow PASSED
tests/test_season_bible.py::test_cli_register_missing_fields_arg PASSED
tests/test_season_bible.py::test_cli_register_invalid_json PASSED
tests/test_season_bible.py::test_cli_register_rejects_non_object_fields PASSED
tests/test_season_bible.py::test_cli_unknown_command_fails_loudly PASSED
============================== 9 passed in 0.23s ===============================

$ python3 -m pytest tests/
============================== 85 passed in 3.12s ==============================
```

新增 6 个 CLI 层测试（真落盘断言 + 参数不足/非法 JSON/非对象 fields/未知命令守卫）；全量 85 通过（原 79 + 新 6）。另在 shell 端到端验证：`register` 写入 arc-map.json 中文内容成功（rc=0）、非法 JSON rc=2、缺参 rc=2、未知命令 rc=2 且报「未知命令」。

## 提交

```
c9a8b62 fix: season_bible register CLI + writer 自检命令修正
```

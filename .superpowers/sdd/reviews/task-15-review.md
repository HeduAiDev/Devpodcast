# Task 15 评审：season-pipeline.js / episode-pipeline.js

评审人：评审代理（编排中枢专项）
评审对象：提交 `349214d`（.claude/workflows/season-pipeline.js 229 行 + episode-pipeline.js 350 行，与工作区 HEAD 逐字节一致，git diff HEAD = 0）
评审基准：task-15-brief.md / design spec §3.3 §11 §12 / .claude/agents/*.md 8 份契约 / scripts/ 6 个 CLI 真实签名

**结论先行：Quality verdict = PASS（0 Critical / 2 Important / 6 Minor）**

---

## 1. A 结构正确性

| # | 检查项 | 判定 | 证据 |
|---|---|---|---|
| A1 | meta.phases 与 brief 一致 | ✅ PASS | season：Plan→Research→Hooks→Slice→Bible；episode：Write→Produce→Revise→TTS→AudioQA→Review→Archive。title+detail 与 brief 逐字一致 |
| A2 | args 解析：bad-args 拉闸 + CFG 仅无参调试 | ✅ PASS | 传了 args 但解析不出（含空对象 `{}`、字符串化 JSON 失败）→ 立即 `return {escalated:'bad-args'}` 拒绝 CFG 回退；CFG 仅在 `typeof args === 'undefined'` 时启用。validArgs 完整：season=show 非空字符串 + episodes 正整数；episode=show/ep_id 非空 + target_minutes 正有限数 |
| A3 | 逃生舱：任一 BLOCKED 立即中止升级 | ✅ PASS | 13（season）/18（episode）个 agent 调用点逐一核对：每个都有 `!x → escalated-'<stage>-failed'` 与 `status==='BLOCKED' → escalated-'<stage>'` 立即返回；Slice 并行任一 BLOCKED 带期号中止；Review 6 维任一失败不假通过；TTS BLOCKED 无降级后门（spec §11.3） |
| A4 | STATUS_SCHEMA 一致性 | ✅ PASS | 两文件同构：`{type:'object', additionalProperties:false, required:['status','note'], properties:{status:{enum:['OK','BLOCKED']}, note, blocker_reason}}` |
| A5 | head(role, ctx) 数组/字符串分支 | ✅ PASS | `Array.isArray(ctxLines) ? ctxLines.join('\n') : String(ctxLines)` —— 数组 vs 字符串 join bug 已正确修复，两文件一致；role=null 站点（TTS/AudioQA fix）只注入 ctx+ESC |

## 2. B 门禁正确性（逐条对照真实 CLI 签名）

| 命令 | 真实签名（源码核实） | 工作流实际命令 | 判定 |
|---|---|---|---|
| lint_script.py | `<path> [--voices <json>] [--target-minutes N]`（argv 手工解析，path 必须 argv[0]） | `<EP>/script.md --voices <SEASON>/voices.json --target-minutes <TARGET>` | ✅ 顺序正确 |
| lint_punct.py | `<file>`（argv[0]） | `<EP>/script.md` | ✅ |
| lint_anchors.py | `<ep_dir> [<show_dir>]` | `<EP> <SHOW>` | ✅ 显式传 show_dir |
| lint_trace.py | `<ep_dir> <voices.json>`（缺参 return 2） | `<EP> <SEASON>/voices.json` | ✅ 两参齐 |
| lint_voices.py | `<voices.json>`（argv[0]） | `<SEASON>/voices.json` | ✅ |
| audio_qa.py | `<wav> [out.json] [expected_minutes]` | `<AUDIO>/episode.wav <AUDIO>/audio-qa.json <TARGET>` | ✅ 第 3 参数值合法 |
| season_bible.py | `due <arc-map> <ep_id>` / `register <arc-map> <ep_id> <fields-json>` | 提示词内完整命令形态 | ✅ |
| archivist.py | `<trace_dir> [status\|log <msg> [kind]]` | `<SHOW>/trace log "<msg>" <kind>` | ✅ |

退出码语义核对：全部 linter 0=无 BLOCKING / 1=有 BLOCKING（lint_punct 恒 0），gate runner「退出码≠0 → BLOCKED」正确；命令本身失败（缺文件/缺 voices.json）同样 BLOCK——安全方向，不会静默放行。

回环轮数：Research 门禁 ≤2 修复轮（lint 最多 3 次）✅；Write 四 linter ≤2 修复轮（w=1 初稿 + w=2/3 修复，w=3 仍 BLOCK → write-lint-exhausted）✅；Revise 定稿复跑一次不进回环（BLOCK → revise-lint-gate 升级）✅；AudioQA ≤2 轮（qaFixes>=2 → audio-qa-exhausted）✅；Review ≤3 轮（第 3 轮后仍有阻断 → review-exhausted）✅。均与 spec §11.2 上限一致。

## 3. C 编排正确性

| # | 检查项 | 判定 | 证据 |
|---|---|---|---|
| C9 | Slice 并行 + 每期 episode-card | ✅ PASS | `parallel(sliceThunks)` book-analyst×N，每期 `episodes/<slug>/episode-card.json`；提示词强制「调度副本以落盘 season-plan 为准」；episodes 空 → plan-empty、缺 slug → plan-bad 拉闸 |
| C10 | Review 6 维与 §12.3 逐字对齐 + run-ledger 竞态 | ✅ PASS | factual_accuracy / critical_depth / spoken_clarity / voice_balance / job_seeker_resonance / quote_fidelity 六项与 spec §12.3 逐字对齐（含契约扩展：批判靶子/配额/引述边界）；run-ledger 仅 factual_accuracy 维写，其余维禁碰（防并行写同一文件竞态） |
| C11 | Archive register 用 episode_id | ✅ PASS | 提示词明令「先 Read episode-card.json 取 episode_id 字段（arc-map 的键）」——不是目录名 epNN-<slug>；season_bible.py 的 arc-map 键形态（"ep01"）与 register argv[3] JSON 均核对一致 |
| C12 | TTS 桩不实现模型、契约完整 | ✅ PASS | scripts/tts.py `DialogueTTSProvider.synthesize` 仍 `raise NotImplementedError`（Task 17 桩），工作流不实现模型；阶段契约完整：AudioBundle、script→[S1]/[S2] 标签串、1s≈12.5 tokens 换算 --max_new_tokens、tts.voice_map（S1/S2 音色样本）、必经站无降级（spec §11.3） |
| C13 | agentType 与 8 个契约文件名一致 | ✅ PASS | planner/researcher/hook-engineer/book-analyst/writer/producer/reviewer/archivist 全部与 .claude/agents/*.md 一致；TTS/AudioQA 无契约文件，用 'claude'（正确取舍）；model 显式传值与 frontmatter 一致（writer/reviewer=opus，其余 sonnet），args.models 可覆盖 |

## 4. D 代码质量

| # | 检查项 | 判定 | 证据 |
|---|---|---|---|
| D14 | node --check | ✅ PASS | 实测 `node --check` 双文件无输出（Node v24.13.1） |
| D15 | JS 语法细节 | ✅ PASS | 无 template literal 误用（全字符串拼接）；register 命令内 `\'{"payoff_due": [...]}\'` 转义合法；`\n` 转义正常；ESC 内 `"BLOCKED"` 双引号在单引号串内合法 |
| D16 | label 唯一性 | ⚠️ 1 处例外 | 见 M-2（AudioQA 循环内 'audio-qa' 重复）；其余全部唯一（含 write r1-r3 / voices-fix r1-r2 / review:<dim> r<r> / slice <slug>） |

---

## 5. 分级清单

### Critical（0）

无。最大风险点（四 linter 命令签名、lint_script 参数顺序、lint_trace 双参必填、audio_qa 第 3 参、season_bible register 的 argv[3] JSON）全部逐条对照源码核实正确；逃生舱 31 个调用点全覆盖；bad-args 拉闸与 CFG 边界正确；node --check 通过。

### Important（2）

- **I-1. Review 产物落盘命名与 reviewer 契约不一致**（episode-pipeline.js L303-312 vs .claude/agents/reviewer.md「产物契约」）。
  契约规定每轮 1 个文件 `reviews/<run>-review.json`（内含 dimensions dict）+ reviewer 更新 run-ledger；工作流要求 6 个文件 `reviews/r<r>-<dim>.json`（每维一个）且 run-ledger 仅 factual_accuracy 维写。工作流靠返回值驱动控制流所以**能跑**，但：① 落盘工件与契约文件名对不上，后续按契约取文件的环节（archivist 归档清单、Task 18/19 检查点、runbook）会落空；② 提示词括注「对齐你契约的产物格式」与文件名事实不符，reviewer agent 读着契约、被要求写不同名字的文件，5/6 的维还被禁止执行契约收工自检里的 run-ledger 更新——指令冲突。建议：把 DIM 产物名改为契约的 `<run>-review.json`（每维写一个文件不可行——同一文件名 6 维并行写 = 新竞态），或先改 reviewer 契约（Task 14 产物）为每维一文件 + 限定 run-ledger 归属，两处必须对齐。

- **I-2. spec §11.3 的 voices_coverage=partial 显式落盘未实现**。
  researcher 契约写明「`voices_coverage=partial` 落盘 run-ledger.json **由 workflow 执行**」，reviewer 契约据此「run-ledger 记录 voices_coverage=partial 时，求职者共鸣维度权重降低」；但两个 workflow 均无任何 coverage 收集/传递/落盘逻辑（season Research 阶段用 STATUS_SCHEMA，无 coverage 字段；episode Review 只读 run-ledger 不写）。后果：researcher 允许交付的 partial 覆盖期，降级知情链静默断裂，reviewer 按全覆盖评审求职者维度 → 可能误退稿或虚假全通过。修复方向：season 返回带 per-episode coverage，episode 在 Review 前把 coverage 落盘到 run-ledger.json。

### Minor（6）

- **M-1.** Bible 阶段 voice-guide 提示词自相矛盾：「你只建占位/核对其存在」vs「若缺失 → status=BLOCKED」——archivist 若建空占位文件，「缺失检查」即失效（空 voice-guide 比缺失更糟：writer 照读、reviewer 无从退稿）。建议删去「建占位」表述，缺失即 BLOCKED 升级 Lead 落笔。
- **M-2.** AudioQA 循环内 `runAudioQA` label 固定为 'audio-qa'，同 run 内重复 2-3 次，resume/caching 按 label 定位时粒度受损。建议带轮号（'audio-qa r'+(qaFixes+1)）。
- **M-3.** `runLints()` 的 gate runner 提示词未走 head()（无 ESC 逃生舱文案），与实现报告「确定性站点（门禁/质检）只注入 ctx+ESC」的表述不符；功能无碍（命令失败照实记录 → BLOCKED），属报告与代码不一致。
- **M-4.** Phase A 三条腿按 meta.phases 串行，未实现 spec §3.3① 并行（报告 Concern 2 已备案，符合 brief 阶段序，并行留待后续优化）——不构成缺陷但需 Lead 知悉与 spec 的偏差已登记。
- **M-5.** AudioQA route 机械规则表述（issues 里「时长」**开头**的 BLOCKING → writer）与实际 issue 串（`"BLOCKING: 时长 …"` / `"BLOCKING: 峰值 … 削波"`）不完全吻合——LLM 执行下按包含匹配能正确归类，建议措辞精确化为「含『时长』」。
- **M-6.** 逃生舱返回结构不统一：升级路径混用 `reason` / `note` 字段承载 BLOCKED 原因（如 revise-lint-gate 只带 note、plan-empty 只带 note、research-lint-exhausted 带 fixes+note），Lead 消费端需同时读两字段。另 Slice 阶段未校验 slug 唯一性（重复 slug 会导致两 book-analyst 并行写同一目录），建议 plan-bad 检查加 `new Set(slugs).size === length`。

---

## 6. ⚠️ Cannot verify

- **C-1. harness 层加载与自定义 agentType 识别**：`agent()`/`parallel()`/`phase()`/`log()` 全局、label/resume 语义、8 个自定义 agentType 在运行会话中是否被 harness 识别——本评审环境无法执行 workflow（报告 Concern 1 已声明：不识别则**首个 agent 调用处大声失败**，不会静默错产物；退路是统一改回 'claude' + head() 注入，一处改动）。
- **C-2. 顶层 `return` + `export const meta` 与 harness 加载器兼容**：node --check 通过且与 repo2book chapter-pipeline.js 同构，但 harness 真实加载行为需 Task 18/19 实测。
- **C-3. 门禁 agent 在 workflow 沙箱中的 Bash 可用性**：「沙箱无文件系统/无 Bash」是 repo2book 的实证假设，本仓 harness 版本下 gate runner 能否真跑 python3 需运行期验证；若可用则 runLints 反而多余，若不成立则门禁路径整体失效——两种情况的应急路径（BLOCKED → 升级）都已就位。
- **C-4. 前置条件存在性**：shows/<show>/source-book/、season/bible/voice-guide.md（Lead 落笔）等依赖 Task 13/ingest 与实际运营动作，非本任务可验证。

---

## 7. 与实现报告的核对

报告全部 6 条 Concerns 与代码一致：①自定义 agentType 风险如实；②串行化备案；③无重试包装属实；④run-ledger 竞态约束如实落地（提示词级）；⑤TTS 桩属实（tts.py raise NotImplementedError）；⑥ep_id 解析多一次 agent 调用属实。报告「node --check 通过」复验通过。唯一不符：runLints 未走 head(null, ctx)（M-3）。

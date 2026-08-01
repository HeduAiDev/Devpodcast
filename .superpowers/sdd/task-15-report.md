# Task 15 报告：season-pipeline / episode-pipeline 骨架

状态：DONE
提交：`349214d`（feat: season-pipeline / episode-pipeline 骨架，2 files changed, 579 insertions）
分支：feat/m0-m1

## 交付文件

- `.claude/workflows/season-pipeline.js`（Phase A 整季编排，~250 行）
- `.claude/workflows/episode-pipeline.js`（Phase B 单期制作，~330 行）

## meta.phases（与 brief 逐字一致）

season-pipeline：`Plan → Research → Hooks → Slice → Bible`
episode-pipeline：`Write → Produce → Revise → TTS → AudioQA → Review → Archive`

## 阶段清单（含 agentType 与门禁）

### season-pipeline.js

| 阶段 | agentType | 产物 | 门禁 |
|---|---|---|---|
| Plan | planner | season/season-plan.json | 返回 PLAN_SCHEMA（须带 episodes 数组，工作流沙箱无文件系统，靠返回值调度 Slice）；episodes 为空/缺 slug → plan-empty/plan-bad 拉闸 |
| Research | researcher | season/voices.json | `python3 scripts/lint_voices.py` 门禁，BLOCKING 回环 researcher ≤2 轮修复，超限 research-lint-exhausted |
| Hooks | hook-engineer | season/arc.json | — |
| Slice | book-analyst ×N（parallel 并行） | episodes/<slug>/episode-card.json ×N | 任一期 BLOCKED → 立即中止（escalated='slice'，带期号） |
| Bible | archivist | season/bible/ 四件套 + trace | voice-guide.md 缺失 → BLOCKED（spec §5：Lead 落笔） |

### episode-pipeline.js

| 阶段 | agentType | 产物 | 门禁 |
|---|---|---|---|
| （预解析） | claude（runner） | 定位 episodes/ 下唯一目录（ep_id 可为目录名或 epNN 前缀，ls 机械匹配，ambiguous/not-found → 拉闸） | — |
| Write | writer | script.md | 四 linter：lint_script（--voices --target-minutes）/ lint_punct / lint_anchors / lint_trace，BLOCKING 回环 writer ≤2 轮修复，超限 write-lint-exhausted |
| Produce | producer | production-notes.md（只建议带行号，绝不碰 script.md） | — |
| Revise | writer | script.md 定稿 | 定稿后四 linter 复跑一次（不进回环，TTS 前必须干净），BLOCKING → revise-lint-gate 升级 |
| TTS | claude（无角色契约文件，head(null, ctx)） | audio/episode.wav + audio/segments/（DialogueTTSProvider 契约） | spec §11.3：TTS 是必经站，环境没配好 = BLOCKED，无降级后门 |
| AudioQA | claude（runner 执行 audio_qa.py + 机械转述） | audio/audio-qa.json | BLOCKING 回环 ≤2 轮：时长超 → writer 改稿；削波 → tts 重合成；both → 先 writer 后 tts；超限 audio-qa-exhausted |
| Review | reviewer ×6（parallel） | reviews/r<run>-<dim>.json | 6 维并行（factual_accuracy / critical_depth / spoken_clarity / voice_balance / job_seeker_resonance / quote_fidelity，spec §12.3），BLOCKING 回环 writer ≤3 轮，超限 review-exhausted |
| Archive | archivist | 归档 + season_bible register 回写 arc-map（episode_id 取自 episode-card.json）+ voices-index + glossary + shownotes.md + trace | 伏笔连续两期欠账 → BLOCKED |

## 公共件说明（两份文件内联同构，均真实可用）

1. **args 解析**（repo2book 教训落地）：`let A = (typeof args !== 'undefined' && args) ? args : null`；字符串化 args 先 JSON.parse；`validArgs()` 校验——season：show 非空字符串 + episodes 正整数；episode：show/ep_id 非空字符串 + target_minutes 正数。**传了 args 但解析不出关键字段 → 立即返回 `{ escalated: 'bad-args' }`，拒绝 CFG 回退**；CFG（season: `{show:'vllm-podcast', episodes:5}`；episode: `{show:'vllm-podcast', ep_id:'ep01', target_minutes:35}`）仅在完全未传 args 的手工调试场景启用。支持 `A.repo_root` / `A.models` 覆盖。
2. **STATUS_SCHEMA**：`{type:'object', additionalProperties:false, required:['status','note'], properties:{status:{enum:['OK','BLOCKED']}, note, blocker_reason}}`——任一 agent 返回 BLOCKED 立即 return `{escalated:'<stage>', reason}` 中止升级 Lead。planner 用 PLAN_SCHEMA（STATUS_SCHEMA + episodes 数组）；audio-qa runner 用 QA_SCHEMA（+issues/route）；ep 解析用 EP_RESOLVE_SCHEMA（+dir）。
3. **head(role, ctx)**：注入角色契约路径（REPO/.claude/agents/<role>.md）+ 每阶段产物绝对路径 + 书源快照路径（shows/<show>/source-book/）+ ESC 逃生舱文案（含「宁可拉闸，不要产出错误成果一路跑到底」）。role=null 的确定性站点（TTS/门禁/质检）只注入 ctx+ESC。
4. **runLints(cmds, label, phase)**：workflow 沙箱无文件系统/Bash（repo2book 实证），确定性门禁借「只跑命令、不做判断」的 claude agent 执行，退出码 0→OK、≠0→BLOCKED，输出带回作为回环修复依据。
5. **按阶段 agentType 调度**：8 角色用角色名（planner / researcher / hook-engineer / book-analyst / writer / producer / reviewer / archivist），确定性站用 'claude'；model 显式传值（writer/reviewer=opus，其余 sonnet）与角色 frontmatter 一致，args.models 可覆盖。
6. **有界回环**：Research 门禁 ≤2 修复轮、Write 门禁 ≤2 修复轮、AudioQA ≤2 修复轮、Review ≤3 评审轮（第 2 轮起只看上轮 fail 维、第 3 轮后仍有阻断 → review-exhausted）——均与 spec §11.2 上限一致。

## node --check 输出

```
$ node --check .claude/workflows/season-pipeline.js && echo "season OK" && node --check .claude/workflows/episode-pipeline.js && echo "episode OK"
season OK
episode OK
```

（无输出即通过；实测 Node v24.13.1 下 `export const meta` + 顶层 `return` 与 repo2book chapter-pipeline.js 同构可过。）

## 验收对照（brief Step 1-4）

- [x] Step 1: season-pipeline.js 完整结构（meta+phases / args / STATUS_SCHEMA / ESC / head / 按阶段调度 / Slice 并行 / Bible）
- [x] Step 2: episode-pipeline.js 完整结构（7 阶段 + 4 linter 门禁 + TTS + AudioQA 回环 ≤2 + Review 6 维回环 ≤3 + Archive register 回写）
- [x] Step 3: node --check 双文件通过
- [x] Step 4: `git add .claude/workflows/` + commit（hash 见上）

## Concerns

1. **自定义 agentType 依赖 harness 注册**：`.claude/agents/*.md` 的角色名作为 agentType 调用，需 Task 18/19 运行的会话能加载项目级 subagent（本会话 system-reminder 未列出这 8 个角色，属预期——Task 14 产物在会话启动后才注册）。若 harness 不识别，管线会在首个 agent 调用处**大声失败**（不会静默错产物），届时退路是统一改回 agentType:'claude' + head() 注入契约（repo2book 模式），一处改动。
2. **三条腿（planner/researcher/hook-engineer）按 meta.phases 顺序执行**，未做 spec §3.3① 的并行化——并行会打乱 Research 的 lint_voices 门禁时序（门禁须在 Slice 前完成），骨架先保确定性，并行是后续优化。
3. **临时故障（限流/崩溃）一律拉闸**：阶段 agent 返回 null → escalated '<stage>-failed'，未做 repo2book 的「API 崩重试」包装（其 write/map-insert/archive 有 ≤2 次重试）。骨架可接受；运行期若频繁遇限流可加 withRetry 包装器。
4. **reviewer 并行写 run-ledger.json 竞态**：6 维并行下多 agent 写同一文件会丢条目（repo2book 同款经验）。骨架在提示词里规定**仅 factual_accuracy 维写 run-ledger**，其余维只写自己的 <run>-<dim>.json——属对 reviewer 契约的微约束，报告备案。
5. **TTS 站是接 Task 17 的桩**：scripts/tts.py 的 synthesize 仍 raise NotImplementedError（M0 环境任务），工作流已把阶段契约（DialogueTTSProvider、[S1]/[S2] 标签串、1s≈12.5 tokens、必经站无降级）写进提示词，Task 17 落地入口后即真实可用。
6. **ep_id 目录解析多一次 agent 调用**：brief 的 ep_id 示例是 "ep01"，但实际目录是 episodes/ep01-<slug>；骨架用一次 bash runner 机械匹配（目录名或 epNN 前缀），歧义/缺失即拉闸，代价可控、收益是 head() 能注入真实绝对路径。

---

## FIX ROUND 1（2026-08-01）：评审 2 Important + 2 Minor 修复

状态：DONE
提交：`<commit-hash>`（fix: voices-coverage 显式落盘 + reviewer 产物命名对齐）
分支：feat/m0-m1

### Important ①：Review 产物命名与 reviewer 契约对齐（I-1）

裁决：保留 workflow 的 `reviews/r<run>-<dim>.json`（6 维并行防文件互相覆盖的合理工程决策），**改 reviewer.md 契约**：

- 产物契约改为「**每轮每维一个文件** `reviews/r<run>-<dim>.json`（dim = 维度 key，如 `r1-factual_accuracy.json`）」，并写明这是 6 维并行防竞态设计；
- 单维文件格式对齐 workflow 返回契约（`pass` + `issues`，外加 episode_id/run/dimension 元信息；issue 四元组 problem/suggested_fix/rationale/blocking，problem 带 script 行号）；
- **补上 run-ledger 归属**：`reviews/run-ledger.json` 仅 factual_accuracy 维写、其余 5 维禁碰（评审已规定、契约此前未写，现补上），收工自检「更新 run-ledger」限定 factual_accuracy 维；
- 降级知情措辞改为指向 `season/voices-coverage.json`（原「run-ledger 记录 voices_coverage」与落盘位置不符）。

### Important ②：voices_coverage 显式落盘（I-2，spec §11.3）

season-pipeline.js Research 阶段、lint_voices 门禁通过后新增 coverage 检查（runLints 同款 runner agent 模式，label `'voices-coverage'` 唯一）：

- runner 跑一条 `python3 -c` 内联检查：读 `season/voices.json`，统计 category=job-seeker 条目数，写 `season/voices-coverage.json`（checked_at / total_voices / job_seeker_voices / coverage / note）；
- 判定：job-seeker ≥1 且 total ≥3 → `full`；job-seeker ≥1 → `partial`；job-seeker = 0 → `none`（全分支实测通过：full 4/1、partial 2/1、none 1/0、empty 0/0）；
- partial/none → workflow log 显式标注「voices_coverage=partial——researcher 未找到足够求职者声音，reviewer 知情降权（spec §11.3）」，最终返回对象带 `voices_coverage` 字段（coverage/total_voices/job_seeker_voices/file）；
- 命令失败（voices.json 缺失/解析错）→ `voices-coverage` BLOCKED 升级（与门禁一致，不许静默）；
- 不新建脚本文件（python3 -c 内联，正式化留给 M3）；
- researcher.md 契约措辞对齐：降级一节由「落盘 run-ledger.json 由 workflow 执行」改为「workflow 统计落盘 season/voices-coverage.json + 判定标准」，消除失实表述。

### Minor（低成本两项）

- **M-2**：AudioQA 循环 label `'audio-qa'` → `'audio-qa r<轮号>'`（runAudioQA(qaFixes+1)），resume/caching 粒度恢复；
- **M-1**：Bible 阶段 voice-guide 提示词删去「建占位」表述——只核对存在，绝不建占位/改内容，缺失即 BLOCKED（空占位会废掉缺失检查）。

### node --check 输出

```
$ node --check .claude/workflows/season-pipeline.js && echo "season OK" && node --check .claude/workflows/episode-pipeline.js && echo "episode OK"
season OK
episode OK
```

### 改动文件

- `.claude/workflows/season-pipeline.js`（coverage 检查 + log + 返回对象字段；M-1 voice-guide 措辞）
- `.claude/agents/reviewer.md`（产物命名 r<run>-<dim>.json + run-ledger 归属 + 降级知情指正）
- `.claude/agents/researcher.md`（coverage 落盘措辞对齐）
- `.claude/workflows/episode-pipeline.js`（M-2 audio-qa label 轮号）

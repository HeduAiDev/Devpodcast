### Task 16: CLAUDE.md + ARCHITECT-RUNBOOK + README

**Files:**
- Create: `CLAUDE.md`
- Create: `docs/superpowers/ARCHITECT-RUNBOOK.md`
- Modify: `README.md`

**Interfaces:** 无代码接口。CLAUDE.md 是本仓通用操作手册（每会话自动加载），RUNBOOK 是发车手册。内容对齐 spec §3（两阶段）/§4（角色）/§11（逃生舱）/§13（milestone）。

- [ ] **Step 1: 写 CLAUDE.md**

要点：项目一句话；先读 spec；两阶段发车（Phase A → Phase B）；HARD RULES（叙事守护 / producer 不改稿 / 零脚手架泄漏 / researcher 不编 / TTS 必经站 / 逃生舱）；角色清单与产物；常用命令（linter 五个 / ingest / pytest）；书写纪律（speaker 标记 / voices 引用 / 停顿）；独立仓库原则。

- [ ] **Step 2: 写 ARCHITECT-RUNBOOK.md**

要点：发车流程（`Workflow({name:"season-pipeline", args:{...}})` 然后逐期 `episode-pipeline`）；监控（`/workflows`）；逃生舱处理（BLOCKED 升级 Lead → 修 → resumeFromRunId）；续跑；常见坑（args 注入、显存占用、voices 时效）。

- [ ] **Step 3: 改 README.md**

要点：项目定位；快速开始（new_show → ingest → season-pipeline → episode-pipeline）；架构一页图；里程碑状态。

- [ ] **Step 4: 提交**

```bash
git add CLAUDE.md docs/superpowers/ARCHITECT-RUNBOOK.md README.md
git commit -m "docs: CLAUDE.md + RUNBOOK + README（工厂操作手册）"
```

---

### Task 17: M0 环境 — F5-TTS 试金石 + MOSS-TTSD 安装

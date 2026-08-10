# Task 13 报告：new_show.py — 节目 scaffold

状态：DONE_WITH_CONCERNS
提交：`444522e`（feat/m0-m1）

## 做了什么

按 brief Step 1–5 完成：

1. **Step 1** — `tests/test_new_show.py`（brief 逐字，3 个测试）：
   - `test_scaffold_creates_structure`：目录树（season/bible、trace、voice-samples、episodes）+ devpodcast.json + SHOW.md + voice-guide.md
   - `test_scaffold_registers_and_activates`：顶层注册表登记 + active 切换 + resolve_show 定位
   - `test_config_embeds_book_source`：书源 root/instance 写入节目配置
2. **Step 2** — 确认失败：`ModuleNotFoundError: No module named 'scripts.new_show'`（collection error，符合 TDD 预期红态）
3. **Step 3** — `scripts/new_show.py`：
   - `VOICE_GUIDE_TEMPLATE` / `SHOW_MD_TEMPLATE` 中文内容与 brief **逐字一致**（脚本比对：401/302 字符 BRIEF-MATCH，零差异）
   - `scaffold_show` 按 brief 逐字：目录 scaffold → 节目 cfg（book_source/audience/format/tts 全字段）→ SHOW.md → voice-guide.md → 顶层注册表登记 + 设为 active，返回节目目录
   - `main` 按 brief 逐字 + 本仓先例 CLI 守卫（`USAGE` + stderr + rc 2，沿 Task 7/8/9/10/11 模式，见 Concern 1）
   - 一处必要偏离：顶层注册表缺失时先建（见 Concern 2）
4. **Step 4** — 3 个测试全过；全量 79 passed，无回归；CLI 冒烟两发（见下）
5. **Step 5** — 提交 `444522e`（2 文件，118 insertions，`git -c user.name="devpodcast" -c user.email="devpodcast@local"`）

## 测试命令与输出

```
$ python3 -m pytest tests/test_new_show.py -v
3 passed in 0.10s

$ python3 -m pytest tests/ -q
79 passed in 1.65s   （基线 76 + 新增 3，无回归）

CLI 冒烟（真实命令行路径）：
$ python3 scripts/new_show.py; echo rc=$?
usage: new_show.py <root> <name> <title> <book_root> <instance>
rc=2

$ python3 scripts/new_show.py /tmp/newshow-smoke demo "演示节目" /mnt/fake/repo vllm
scaffolded shows/demo
（目录树 6 项全建齐；顶层注册 active_show=demo、shows=[demo]；冒烟后已清理）
```

## 提交

```
444522e feat: new_show 节目 scaffold（voice-guide 模板落笔）
```

## Concerns

1. **main 无参守卫**：brief 的 main 直接取 argv[0..4]，无参数时 IndexError。按全局
   约束"main 无参守卫 usage+rc2（沿 Task 7/8/9/10/11 模式）"补了
   `USAGE = "usage: new_show.py <root> <name> <title> <book_root> <instance>"` +
   `len(argv) < 5` 时 stderr 打印并返回 2（与 season_bible.py/lint_script.py 同款）。
   其余 main 主体逐字未动。CLI 冒烟实测 rc=2。
2. **对 brief 的一处必要偏离（唯一偏离）**：brief 的 `scaffold_show` 对顶层注册表
   直接 `reg_path.read_text()`，但 brief 自己的 `test_scaffold_registers_and_activates`
   在全新 `tmp_path` 上调用（注册表不存在）→ FileNotFoundError，与 Step 4 冲突。
   解决（最小改动，仅加 missing 分支）：
   `if reg_path.exists(): reg = json.loads(...) else: reg = {"version": "1.0", "active_show": "", "shows": {}}`
   ——注册表缺失时新建并登记（符合"顶层注册表自动登记新节目并设为 active"的接口
   语义）；既有文件路径的行为与 brief 完全一致（读 → 改 active_show → 追加 shows
   条目 → 原样写回，production 下顶层 devpodcast.json 已存在，行为零差异）。
3. **生产注册表未被本任务触碰**：仓库顶层 `devpodcast.json`（active_show="vllm-podcast"）
   未跑过 scaffold，保持 Task 1 原状；冒烟只在 /tmp 临时目录进行。
4. `.superpowers/` 目录保持 untracked（SDD 工作流目录），本报告未纳入提交；
   提交内容严格按 brief Step 5：`scripts/new_show.py` + `tests/test_new_show.py`。

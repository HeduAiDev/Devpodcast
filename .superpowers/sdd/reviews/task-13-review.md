# Task 13 评审：new_show.py — 节目 scaffold（commit 444522e）

## 1. Spec compliance 判定：✅

必达物逐项核对（brief vs diff vs 仓库实测）：

| 必达物 | 结果 |
|---|---|
| `scripts/new_show.py` + `tests/test_new_show.py`（仅此 2 文件） | ✅ stat 2 files / 118 insertions，与 Step 5 一致 |
| 接口 `scaffold_show(root: Path, name: str, title: str, book_root: str, instance: str) -> Path` | ✅ 签名逐字 |
| 目录 scaffold：`shows/<name>/{season/bible, trace, voice-samples, episodes}` | ✅ 实测 /tmp 冒烟目录树 6 项全建齐 |
| 节目 devpodcast.json 全字段（show/title/book_source/audience/format/tts/voice_map） | ✅ 与 brief 逐字一致，ensure_ascii=False + indent=2 |
| SHOW.md 模板（含书源/硬规则 3 条） | ✅ 与 brief 逐字一致（脚本比对 EXACT MATCH） |
| **voice-guide.md 模板（老张/阿凯 + 三条纪律 + 求职者配额）** | ✅ **逐字一致（EXACT MATCH）**；实测 scaffold 产出字节级 MATCH——本任务最重要产物完整保留 |
| 顶层注册表登记 + 设为 active | ✅ 实测 active_show=demo、shows.demo 条目、resolve_show 定位成功 |
| 返回节目目录 | ✅ 返回 `root/shows/name` |
| 测试（brief 逐字 3 个） | ✅ diff 与 brief 仅差 markdown 围栏；3 passed |
| 全量无回归 | ✅ 79 passed（基线 76 + 3） |
| TDD 红→绿 | ✅ 红态可由提交结构独立证实：两文件均 new file，父提交无 `scripts/new_show.py`，import 必 ModuleNotFoundError |
| 提交纪律 | ✅ author `devpodcast <devpodcast@local>`，message 与 brief Step 5 一致 |
| 生产注册表未触碰 | ✅ 顶层 devpodcast.json 仍 active_show="vllm-podcast"，shows 仅 vllm-podcast |
| 零跨仓依赖 | ✅ 仅引用本仓 scripts.show_resolver |

缺项/多余项：无缺项。实现相对 brief 仅有两处**增补**（见 §2），非多余项。

## 2. 偏离裁决：接受（两处，均已声明）

**偏离 A（注册表缺失时新建）— 接受，必要偏离。**
独立验证：按 brief Step 3 原版代码（`reg = json.loads(reg_path.read_text(...))` 直接读）在全新 tmp_path 上复现 `FileNotFoundError: '/tmp/.../devpodcast.json'`。brief 自身自相矛盾——Step 1 测试在全新 tmp_path 调用，Step 3 代码要求注册表已存在，Step 4 不可能绿。修复最小（仅 3 行 missing 分支），语义符合接口"顶层注册表自动登记新节目并设为 active"；新建形状 `{"version": "1.0", "active_show": "", "shows": {}}` 与生产注册表现有形状一致（version "1.0"）；既有文件路径行为与 brief 零差异（实测）。

**偏离 B（main 无参守卫 USAGE + rc 2）— 接受。**
函数级 diff 证实为纯增补（3 行），不改变 brief 主体行为；本仓先例属实（season_bible.py/lint_script.py 同款 `USAGE` + `len(argv)` + `return 2`）；实测 no-arg rc=2、usage 打 stderr；不触碰任何测试行为。虽然该约束不在本任务绑定清单内，但符合仓内 CLI 一致性且已声明，无拒绝理由。

## 3. 代码质量判定：Approved

- 目录创建：`mkdir(parents=True, exist_ok=True)` 幂等正确
- JSON 写入：`ensure_ascii=False, indent=2, encoding="utf-8"`，中文无转义
- 注册表更新：读→改→原样写回，编码一致；missing 分支与既有路径互不影响
- 模板保真：函数级 diff 证实 `scaffold_show`/`main` 仅上述两处增补，其余逐字；模板为任务最高优先级产物，字节级保留
- main 返回 int、`raise SystemExit(main())`，符合仓内 CLI 模式

分级清单：
- Critical：0
- Important：0
- Minor：
  1. `reg["shows"][name]` 对同名已存在节目静默覆盖，无重复 scaffold 保护（brief 未要求，非缺陷）
  2. trace/voice-samples/episodes 为空目录，git 不追踪——符合 brief"空档"意图，留待后续任务填充
  3. SHOW.md 书源行较长（{book_root} 内嵌命令）——纯格式，与 brief 逐字一致

## 4. ⚠️ Cannot verify

- 无实质性项。报告中的红态（ModuleNotFoundError）、模板 401/302 字符比对声明均已独立复核（前者由提交结构证明，后者本人重跑比对 EXACT MATCH）；CLI 冒烟已实测复现（rc=2 与 rc=0 两路径）。
- 唯一无法复核的是报告声称的"冒烟后已清理"这一过程性细节——产物为 /tmp 临时目录，不影响仓库状态（git status 仅 .superpowers/ untracked，符合 SDD 工作流）。

## 结论

Spec ✅ / 偏离接受 / Quality Approved。Task 13 是最后一个纯代码任务，可放行进入 Task 14。

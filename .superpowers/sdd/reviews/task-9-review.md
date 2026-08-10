# Task 9 Review: lint_punct / lint_anchors / lint_trace

Reviewer verification performed (not just diff reading):
- `git log`: commit `fcbadfe` 存在，作者 `devpodcast <devpodcast@local>`，单 commit，与报告一致
- 7 个新测试独立重跑全部 PASSED；全量 `pytest tests/` 61 passed 无回归
- CLI smoke 独立复测：三脚本无参 → usage 到 stderr + rc=2；`lint_punct` 带 WARN 输入 → rc=0；`lint_anchors`/`lint_trace` 带坏链接/未知 voice → `[BLOCKING]` + rc=1
- brief 原版 `test_valid_link_ok` 用独立脚本复现（见偏离裁决）

## 1. Spec compliance 判定：✅

| 必达物 | 状态 |
|---|---|
| `scripts/lint_punct.py` + `tests/test_lint_punct.py` | ✅ |
| `scripts/lint_anchors.py` + `tests/test_lint_anchors.py` | ✅ |
| `scripts/lint_trace.py` + `tests/test_lint_trace.py` | ✅ |
| `lint_punct(text) -> list[dict]`：CJK 间半角 `,.;` → WARN；反引号代码段剥离后扫描；纯 WARN（main 恒 0） | ✅ 与 brief 逐行一致 |
| `lint_anchors(ep_dir, show_dir)`：LINK_RE `\]\(\.\./\.\./episodes/([^/)]+)/`，目标 `show_dir/episodes/<slug>/script.md` 不存在 → BLOCKING | ✅ 与 brief 逐行一致 |
| `lint_trace(ep_dir, voices)`：REF_RE `\{\{voice:([a-zA-Z0-9_-]+)\}\}` 不在 voices → BLOCKING | ✅ 与 brief 逐行一致 |
| 三模块互不 import、独立 | ✅ diff 确认零 import scripts.* |
| CLI 模式（Task 7/8）：import 前插仓库根进 sys.path；无参守卫返回 2；`[BLOCKING]/[WARN]` 输出；退出码 0/1/2 | ✅ 与 lint_script.py 现网模式逐项核对一致 |
| TDD 纪律：测试先行（collection 失败）→ 实现 → 转绿 | ✅ 报告序列与 commit 相符 |
| 提交命令与作者 | ✅ `devpodcast <devpodcast@local>` |

**多余项**：无实质多余。实现相对 brief 代码新增的 sys.path 插入、USAGE、无参守卫是 Global Constraints 明确要求（brief 代码片段本身缺守卫，实现补齐了约束而非违背），属正确增补，不判为偏离。

**测试吻合度**：test_lint_punct（3 个）、test_lint_trace（2 个）与 brief 逐字一致；test_lint_anchors（2 个）为修复版（见下）。

## 2. 偏离裁决：接受

偏离声明：`test_valid_link_ok` 补了 `ep01-slug`/`ep02-slug` 两个 mkdir + 空 `ep02-slug/script.md`。

独立复现（在本机执行 brief 原版代码）证实 brief 原样**双重必挂**：
1. `(tmp_path / "episodes" / "ep01-slug" / "script.md").write_text(...)` 在 `ep01-slug` 目录未创建时直接抛 `FileNotFoundError`（已复现报错），测试在调用 lint 前就挂；
2. 即使目录存在，`ep02-slug/script.md` 未被创建，`lint_anchors` 会正确报 `BLOCKING: 跨期链接目标不存在: ep02-slug`，`assert issues == []` 必挂（已复现输出）。

修复最小化：仅补 setup（2 个 mkdir + 空目标文件），测试意图（有效链接 → 零 issues）完整保留，且修复落在测试而非实现，正确。裁决：**接受**。

## 3. 代码质量判定：Approved

### 正则核对（均正确）
- **CJK 类** `一-鿿`（U+4E00–U+9FFF）：与 brief 界定一致，恰为 CJK 基本区；不含 Ext A（U+3400–4DBF）为 brief 原样行为，非缺陷。
- **LINK_RE** `\]\(\.\./\.\./episodes/([^/)]+)/`：相对 `episodes/epNN-x/script.md` 的正确深度是 `../../episodes/`（上两级到 show，再下 episodes/）；接口 prose 的 `../episodes/` 是简写，regex/测试自洽，正确。
- **REF_RE** 与 `scripts/script_parser.py` 的 `VOICE_RE` 逐字一致——lint_trace 与 lint_script 规则 1 检出口径真正一致（非只声明），符合 brief "保持一致" 要求。
- 反引号剥离 `r"`[^`]*`"`、HALF `([一-鿿])[,.;]([一-鿿])` 均与 brief 逐字一致，测试三分支（命中/全角豁免/代码段豁免）有效覆盖。

### Minor（不阻塞）
1. `lint_anchors`/`lint_trace` 的 `main()` 双调用 lint 函数（打印一次 + 退出码再算一次）——brief 原样，纯函数无害，报告已声明；可改为先存 issues 再打印，但非本任务缺陷。
2. CLI 契约（无参 rc=2、退出码 0/1）无 pytest 自动化覆盖，仅手工 smoke——与 Task 7/8 既有模式一致，属既有约定。
3. `lint_punct` 输出无行号/文件名，仅带上下文切片；多行文件中定位靠人工——brief 原样。
4. HALF 对紧邻多个半角标点（如 `一,二.三`）仅报第一个（finditer 非重叠消费）——brief 原样边界行为。

### Critical / Important：0 / 0

## 4. ⚠️ Cannot verify

1. **CLI 默认 `show_dir = ep_dir.parent.parent` 的 canonical 布局假设**：当前仓库 `shows/` 目录尚不存在（`devpodcast.json` 的 active_show=vllm-podcast 指向 `shows/vllm-podcast/devpodcast.json`，但目录未建），无法实证。逻辑推导正确（`show/episodes/epNN-x` → parent.parent = show），但只能推理，且仅对 `ep_dir` 恰为 `show/episodes/<slug>` 两级深成立——与报告 Concern 2 一致，caller 显式传 show_dir 可规避。
2. **workflow 端集成**：lint_trace 作为"供 workflow 使用的独立 CLI"的调用方代码不在本任务内，只能验证 CLI 契约与 voices.json 直读格式（`json.loads` 顶层 dict），无法验证 workflow 传入的 voices 结构是否与 `shows/<name>/devpodcast.json` 的 voices 块匹配。
3. **lint_anchors 链接深度与实际产出文件的关系**：仓库尚无真实 episode 产出，LINK_RE 对 `../../episodes/` 深度的适配性只能依据测试与布局推理，无真实数据实证。

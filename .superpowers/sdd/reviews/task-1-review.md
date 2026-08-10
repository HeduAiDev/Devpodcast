# Task 1 Review — 骨架：devpodcast.json + show_resolver.py

评审对象：commit `470b834`（`feat: 顶层注册表 + 活动节目定位（show_resolver）`）
评审方式：diff 与 brief 逐行比对 + 仓库现场核验（git show / git log / git status）

## 1. Spec compliance 判定：✅

全部必达物齐备，无缺项、无多余项：

| 必达物 | 判定 | 核对结果 |
|---|---|---|
| `tests/test_show_resolver.py`（3 个测试） | ✅ | 与 brief Step 1 逐字一致（导入、3 个测试、断言内容全部相同） |
| Step 2 RED 确认 | ✅ | 报告附失败输出（collection error）。实际报错为 `No module named 'scripts'`，与 brief 预期 `No module named 'show_resolver'` 属同类失败（模块不存在），可接受 |
| `scripts/show_resolver.py` | ✅ | 与 brief Step 3 逐字一致：`_root`、`active_show_name`（env 覆盖）、`resolve_show`（FileNotFoundError）、`show_config`，签名完全吻合接口（`resolve_show(root=None) -> Path`、`active_show_name() -> str`、`show_config(show_dir) -> dict`） |
| Step 4 GREEN 确认 | ✅ | 报告附 3 passed 输出 |
| `devpodcast.json` 顶层注册表 | ✅ | 与 brief Step 5 逐字一致（version、description、active_show=vllm-podcast、shows、shared 全部 7 项含 5 个 linters），`python3 -m json.tool` 校验通过（报告证据） |
| Step 6 提交 | ✅ | 现场核验：commit `470b834` 恰含 3 个文件（无多余文件）；message 与 brief 一致；author 与 committer 均为 `devpodcast <devpodcast@local>` |
| 工作区状态 | ✅ | 现场核验：干净，仅 untracked `.superpowers/`（sdd 工作区，brief Step 6 未列入，符合预期） |

**Global Constraints 核验：**
- 零跨仓依赖 ✅：实现仅 import stdlib（`json`、`os`、`pathlib`）；测试仅 import stdlib + `pytest`。代码不读取任何其他项目路径，仅用 `__file__` 相对定位和调用方传入的 root。
- TDD 纪律 ⚠️：见第 3 节（RED/GREEN 证据来自报告，diff 无法独立验证）。
- 提交身份 ✅：现场核验 `git log`，author/committer 均为 `devpodcast <devpodcast@local>`，符合。

**YAGNI 检查**：无多余物。恰好 3 个文件、70 行插入，无额外函数、无 conftest/pyproject/pytest.ini、无未提交的杂散文件（`__pycache__`、`.pytest_cache` 已被 .gitignore 排除）。

## 2. 代码质量判定：Approved（附分级清单）

测试有效、错误处理合理、实现与接口一致。无 Critical、无 Important。

发现的问题全部为 Minor，且全部继承自 brief 自身给出的样板代码——实现者逐字照搬 brief，非实现者偏差，供后续任务设计参考：

- **[Minor] `import json, os` 违反 PEP8**（应一行一个 import），且顶层函数前无空行。纯风格问题。
- **[Minor] 测试未隔离 `DEVPODCAST_SHOW` 环境变量**：`active_show_name` 中 env 优先于注册表，而 3 个测试均未 monkeypatch os.environ。若运行环境恰好设置了 `DEVPODCAST_SHOW`，`test_resolve_active_show`（断言返回 "demo"）与 `test_resolve_missing_show_raises`（期望按 "nope" 抛错）都会失效——潜在的不稳定测试（flaky）来源。
- **[Minor] env 覆盖分支零测试覆盖**：`DEVPODCAST_SHOW` 是文档化的接口行为（docstring 声明），但 brief 规定的 3 个测试没有覆盖该分支。
- **[Minor] 边缘语义**：`_root("")` 因空串为假值会静默回退到仓库根；`resolve_show` 只校验 `shows/<name>/devpodcast.json` 存在、不校验 `shows/<name>` 是目录。均为骨架阶段可接受的隐式行为。

**正面确认（测试有效性）**：3 个测试都有真实断言——`test_resolve_active_show` 断言 `.name == "demo"` 与 `active_show_name == "demo"`；`test_show_config_reads_instance_file` 断言嵌套值 `cfg["format"]["hosts"] == 2`；`test_resolve_missing_show_raises` 用 `pytest.raises(FileNotFoundError)`。无空转测试。

**报告准确性**：如实披露 RED 失败信息与 brief 预期措辞的差异、`resolve_show()` 在真实仓库下将持续抛错（因 `shows/vllm-podcast/devpodcast.json` 由后续任务创建）——该行为与 brief 设计一致，非缺陷。

## 3. ⚠️ Cannot verify from diff

以下需求点依赖报告证据或仓库现场无法还原，diff 本身无法验证：

1. **TDD 顺序（测试先写、先确认失败）**：测试与实现同在一个 commit 内落地，git 历史无法证明先后顺序；RED（Step 2）与 GREEN（Step 4）输出均为报告自述。报告附带的失败输出与通过输出相互印证、内容可信，但严格意义上属于 self-report。
2. **Step 4 "3 passed" 运行结果**：报告自述，未在 diff 中体现（评审按要求未复跑测试）。
3. **`python3 -m json.tool` 校验、环境（Python 3.11.5 / pytest 9.0.3）与端到端 sanity check 输出**：均为报告自述。
4. **提交时使用 `-c user.name=... -c user.email=...` 内联身份的方式**：结果（author/committer 为 devpodcast@local）已现场核验通过；至于是否用内联 flag 而非全局配置，属过程细节，无法从最终状态还原。

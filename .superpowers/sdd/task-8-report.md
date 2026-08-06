# Task 8 Report: lint_voices.py — voices 五条门禁

**Status**: DONE
**Commit**: `7c16dc4` feat: lint_voices 五条门禁（spec §6.4）
**Branch**: feat/m0-m1

## 做了什么

1. **Step 1 — 失败测试**：按 brief 逐字创建 `tests/test_lint_voices.py`（10 个测试，`base_voice()` 工厂 + 五条门禁覆盖：URL/日期必填、匿名化、low-confidence 标注、单一来源 warn、job-seeker 平台约束）。
2. **Step 2 — 确认失败**：`python3 -m pytest tests/test_lint_voices.py -v` → `ModuleNotFoundError: No module named 'scripts.lint_voices'`（collect error），符合 TDD 预期。
3. **Step 3 — 实现**：创建 `scripts/lint_voices.py`，代码按 brief 逐字实现（含 `JOB_SEEKER_PLATFORMS` / `OFFICIAL_PLATFORMS` 两个常量集合，逐字拷贝），另加 Task 7 已确立的两个 CLI 模式：
   - `sys.path.insert(0, str(Path(__file__).resolve().parent.parent))`（import 前插入仓库根，注释风格同 lint_script.py）——需注意 brief 代码里 `Path` 只在 `main()` 内局部导入，而 sys.path 插入在模块级使用 `Path`，因此将 `from pathlib import Path` 提升到模块级（与 lint_script.py 一致），避免 NameError。
   - CLI 参数守卫：`USAGE = "usage: python3 scripts/lint_voices.py <voices.json>"`，无参 → stderr 打印 usage、返回 2（不再裸 IndexError traceback）。
   - 输出格式与 lint_script 一致：`[BLOCKING] msg` / `[WARN] msg`；退出码 0=通过 / 1=有 BLOCKING / 2=用法错误。
4. **Step 4 — 确认通过**：10/10 通过。
5. **Step 5（推荐项）— CLI 守卫测试**：追加 `test_cli_no_args_usage_returns_2`（镜像 Task 7 的 `test_cli_no_args_usage_returns_2`：`main([]) == 2` 且 stderr 含 usage）→ 11/11 通过。
6. **Step 6 — 提交**：`git -c user.name="devpodcast" -c user.email="devpodcast@local" commit -m "feat: lint_voices 五条门禁（spec §6.4）"`。

## 测试命令与输出

- 失败阶段（Step 2）：
  ```
  collected 0 items / 1 error
  E   ModuleNotFoundError: No module named 'scripts.lint_voices'
  ```
- 通过阶段（Step 4）：`python3 -m pytest tests/test_lint_voices.py -v` → **11 passed in 0.10s**
- 全量回归：`python3 -m pytest tests/ -v` → **54 passed in 0.89s**

  （父任务预测 53 个通过，实为 54：53 = 43 既有 + 10 条 brief 测试；实际另有 1 个新增的 CLI 守卫测试。无回归、无失败。）

- CLI 端到端手工验证：
  - 无参：`usage: python3 scripts/lint_voices.py <voices.json>`（stderr）+ exit 2
  - 干净 voices.json：无输出 + exit 0
  - 违规 voices.json（空 URL/日期、job-seeker + github-issue、low confidence 无标注、单源）：4 条 BLOCKING + 1 条 WARN + exit 1；anonymized=false + github-issue 正确豁免（官方平台集合内），job-seeker 规则正确触发。

## 涉及文件

- 新增 `/mnt/e/Laboratory/Devpodcast/scripts/lint_voices.py`
- 新增 `/mnt/e/Laboratory/Devpodcast/tests/test_lint_voices.py`

## Concerns

1. **偏离 brief 的两处（均为必要修正，已注释说明）**：
   - `Path` 导入从 `main()` 局部提升到模块级——brief 代码在模块级 sys.path 插入处使用 `Path` 但未导入，照抄会 NameError。
   - `main()` 增加无参守卫（brief 代码 `Path(argv[0])` 在空 argv 时 IndexError）——父任务明确要求。
2. **无害冗余**：brief 代码含 `from collections import Counter`，实际未使用（按 brief 逐字保留）。
3. **不存在文件仍裸 traceback**（`FileNotFoundError`）——与 Task 7 的 lint_script 行为一致（守卫只覆盖参数缺失/缺值，不覆盖 IO 错误），未改动以保持一致。
4. 退出码/输出格式与 lint_script 完全一致；单一来源 WARN 按 term 聚合，`verified=official` 的条目豁免。

## 验证快照

```
[feat/m0-m1 7c16dc4] feat: lint_voices 五条门禁（spec §6.4）
 2 files changed, 129 insertions(+)
```

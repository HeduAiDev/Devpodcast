# Task 2 Review — BookSource 抽象 + Repo2BookSource

Reviewer: 独立评审（基于 brief / report / review.pkg / 实仓核查 / 环境实证片段）
Date: 2026-08-01

---

## 1. Spec compliance 判定：✅

### 必达物核对（brief Interfaces / Steps / Global Constraints）

| 必达物 | 状态 | 备注 |
|---|---|---|
| `scripts/book_source.py` | ✅ | 100 行，与 brief Step 4 代码逐字一致（唯一差异：`@runtime_checkable`，见偏离 2） |
| `tests/test_book_source.py` | ✅ | 7 个测试，与 brief Step 2 逐字一致（含 `FIX` 定义） |
| `tests/fixtures/repo2book-mini/` | ✅ | 4 类文件内容与 brief Step 1 逐字一致；路径多一层 `instances/mini/`（见偏离 1 裁决） |
| `Book` dataclass（title / chapters） | ✅ | ⚠️ Interfaces 段落提到的 `digest: str` 未实现——但 brief 自身 Step 4 代码也无 digest，属 brief 内部不一致，非实现缺陷（见 Minor 5） |
| `ChapterCard` dataclass 全 7 字段 | ✅ | chapter_id/title/slug/sections/key_classes/mechanisms/narrative_path(`Path\|None`) |
| `Repo2BookSource(root, instance)` + load/chapter_cards/glossary/outline | ✅ | 构造闸门 `root/instances/<instance>` 存在性校验 → FileNotFoundError；接口段落写 `(BookSource)` 继承但 brief 代码未继承（结构型 Protocol 即设计意图），亦非实现缺陷 |
| `BookSource(Protocol)` 同签名 | ✅ | 4 个方法签名一致 + `@runtime_checkable` |
| sections 规则 `^##\s+(\d+\.\d+)\s+` | ✅ | 实测：`["1.1 Foo 的第一步", "1.2 Foo 的第二步"]`，`## 你在这里` 正确跳过，`1.1.1` 子小节不误抓 |
| key_classes = dossier.json | ✅ | `dd.get("key_classes", []) or []` |
| mechanisms = dossier.json，容忍空数组 | ✅ | `or []` 双重防护（缺失或 null 均可） |
| 标题 `# 第N章　<标题>` 去章号前缀 | ✅ | 实测 U+3000 全角空格被 `\s` 匹配，title = "Foo 章" |
| outline-final.json 是 list | ✅ | 直接 json.loads，测试断言 isinstance list |
| glossary.json 是 dict（key=中文术语） | ✅ | 测试断言 key 访问 |
| TDD 纪律 | ✅ | 报告证据：Step 3 先红（ModuleNotFoundError）→ Step 5 全绿；commit 与 brief Step 6 一致（`7e2334b`，8 文件 167 insertions，message 逐字匹配，作者 `devpodcast <devpodcast@local>`，经 `git show` 实仓核实） |
| 独立仓库、零跨仓依赖 | ✅ | 单仓库 4 commits（Task1 3 个 + 本任务）；新文件仅 import stdlib（json/re/dataclasses/pathlib/typing）+ pytest |

### 缺项清单
- `Book.digest`：brief Interfaces 声明但 brief 代码未包含，实现与代码一致 —— 记为 brief 内部矛盾，非任务缺陷（需跟踪至 Task 3，见 Minor 5）。

### 多余项清单
- 无。`as_dict()`、`_chapter_dirs()`、docstring、缺失文件守卫（glossary/outline 返回 `{}`/`[]`）均逐字来自 brief Step 4 代码。

---

## 2. 两处偏离的裁决

### 偏离 1：fixture 加 `instances/mini/` 层级 → **接受**

**必要且正确**。brief 自身矛盾经逐字核对属实：
- Step 1 mkdir/fixture 文件路径：`tests/fixtures/repo2book-mini/artifacts/...`、`.../repo2book-mini/book/...`（无 instances 层）；
- 但 brief 自己的测试代码 `Repo2BookSource(FIX, "mini")`（FIX = `repo2book-mini`）+ 实现代码 `inst_dir = root / "instances" / instance` + 闸门 `if not inst_dir.is_dir(): raise FileNotFoundError`，必然要求 `repo2book-mini/instances/mini/` 存在。

若照 brief Step 1 布局落地，7 个测试中 6 个应过的（test_load_book 等）会全部因闸门抛 FileNotFoundError（第 7 个 test_missing_instance_raises 反而"假绿"），brief 自己的测试套件不可通过。实现者的解法——代码与测试逐字保留、fixture 文件内容逐字保留、仅移动位置——是唯一自洽读法。反向解法（删掉代码里的 instances 闸门）会偏离 brief 明确给出的实现代码并破坏 test_missing_instance_raises 的语义。接受。

### 偏离 2：`BookSource` 加 `@runtime_checkable` → **接受**

**必要且正确**。本环境（Python 3.11.5）实证：
```
plain protocol isinstance: TypeError -> Instance and class checks can only be used with @runtime_checkable protocols
runtime_checkable isinstance: True
```
brief 自带测试 `test_implements_protocol` 要求 `isinstance(Repo2BookSource(FIX, "mini"), BookSource)` 成立，不带装饰器的纯 Protocol 在运行时必抛 TypeError——brief 的测试/实现组合本身不可运行。装饰器是最小修复：协议签名未变，结构型 duck-type 语义保留，isinstance 按 4 个方法存在性判定通过。接受。

---

## 3. 代码质量判定：**Approved**

无 Critical / 无 Important。Minor 级观察如下（均不阻塞）：

1. **Minor — sections 正则的尾随空格边缘**（继承自 brief 代码，非实现者引入）：实测 `## 1.1 `（数字后只有空白、无标题）会被 `(.+)` 回溯匹配，产出垃圾 section `"1.1 "`（strip 后空标题）。真实 repo2book 数据 39/39 章小节均有标题，实际风险为零；若想加固可改 `(\S.*)` 或过滤 `name.strip()`。评审意见：留给 Task 3 用真实实例验证后再定，不必现在动。
2. **Minor — outline()/glossary() 返回未做类型断言**：若 outline-final.json 意外为 dict，`-> list` 契约会被静默违反。已核实真实数据为 list，且测试覆盖了形状。可接受。
3. **Minor — `_chapter_dirs()` 的 `arts.iterdir()` 未守卫**：artifacts 目录缺失时抛裸 FileNotFoundError 而非闸门式错误信息。构造闸门已保证 inst_dir 存在，实际不可达。可接受。
4. **Minor — 缺失文件回退分支未测**：glossary/outline 的 `{}`/`[]` 回退、narrative/dossier 缺失时的默认值均无测试。mini fixture 可接受，Task 3+ 真实实例会覆盖。
5. **Minor — `Book.digest` 悬空**：brief Interfaces 声明 digest: str 但代码（brief 与实现均）无此字段。建议在 Task 3（ingest_book）设计时显式决定 digest 归属，避免接口漂移。
6. **Minor — fixture 真实性**：结构忠实于 repo2book（`instances/<name>/artifacts/<slug>/{dossier,narrative}`、`book/cartography`、`book/bible`、U+3000 章标题、非编号标题干扰项、空 mechanisms 章）——在 mini 尺寸下覆盖了全部要点抽取规则路径，质量良好。

测试有效性（正向确认）：7 个测试逐字来自 brief 且组合上覆盖了全部核心规则——多小节抽取、非编号标题排除（由成员断言隐含）、key_classes/mechanisms 非空与空容忍、glossary dict 形状、outline list 形状、协议 isinstance、缺失实例闸门。实现与 brief 规则的一致性已由独立片段实测复核。

---

## 4. ⚠️ Cannot verify 清单

1. **Step 3 先红输出与 Step 5 的 7 passed / 全套 10 passed**：未按指示重跑测试套件，依据实现者报告（输出格式与真实 pytest 9.0.3 一致、环境参数属实）。实现代码与测试的静态一致性、两处偏离的 Python 语义已独立实证，但"通过"本身未独立复现。
2. **"39/39 章"要点抽取规则的实测来源**：brief 声称来自真实 repo2book 数据核实；本次评审只能确认实现与 brief 规则逐字一致，无法独立访问真实 repo2book 数据验证该统计。
3. **Task 1 回归（3 测试）不受影响**：同上，依赖实现者报告的全套输出。

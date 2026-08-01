# devpodcast M0+M1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建起 devpodcast 工厂骨架（M0）+ 用 vllm 书跑通第一期能听的节目（M1）。

**Architecture:** 参考已批准规格 `docs/superpowers/specs/2026-08-01-devpodcast-design.md`。两阶段流水线：Phase A（season-pipeline.js：planner/hook-engineer/researcher/book-analyst/archivist 并行产素材）→ Phase B（episode-pipeline.js：writer → producer → writer → tts → audio-qa → reviewer → archivist）。独立代码仓，零运行时跨仓依赖；书源经 `ingest_book.py` 快照摄入 `shows/<name>/source-book/` 后只读。

**Tech Stack:** Python 3.11+ / pytest / torch 2.11.0+cu130（已装）/ MOSS-TTSD v1.0（8B, Apache-2.0, 默认 TTS）/ CosyVoice3 fallback / F5-TTS 仅作 M0 环境试金石。

## Global Constraints

- **独立仓库**：不 import、不读路径、不 submodule 任何其他项目；脚本逐份自写。唯一外部接触面 = `ingest_book.py` 在用户显式给路径时读一次，快照摄入后即断开。
- **叙事守护**：只有 writer 可写 `script.md`；producer 只写 `production-notes.md` 且每条带 script 行号；编排者不得直接改脚本。
- **零脚手架泄漏**：脚本内不得出现 `episode-card` / `voices.json` / `arc.json` 等内部文件名。
- **researcher 不编**：查不到标 low confidence 或拉逃生舱；评论 ≠ 事实；普通用户匿名化转述。
- **TTS 是必经站**：无降级路径；环境没配好 = BLOCKED。
- **逃生舱**：任一阶段 `status=BLOCKED` 立即中止升级 Lead；`宁可拉闸，不要产出错误成果一路跑到底`。
- **书写纪律**：speaker 标记 `[S1]`/`[S2]` 成对；voices 引用 `{{voice:<id>}}`；显式停顿 `<break Nms>`。
- **语气纪律（voice-guide）**：每期至少一次"我不知道"（warn 级检查）；批判必须有靶子；生活场景必须承重。
- **测试纪律**：先写失败测试再写实现（TDD）；每个代码任务以 pytest 绿为准。
- **GPU**：NVIDIA RTX PRO 6000 Blackwell 95.6GB，CUDA 13.1，torch cu130。MOSS 需 torch cu128 系列（sm_120）。

---

## 文件结构

```
Devpodcast/
├── CLAUDE.md                        # M0：通用操作手册
├── devpodcast.json                  # M0：顶层注册表
├── README.md                        # M0
├── .claude/
│   ├── agents/                      # M0：8 个角色提示词
│   │   ├── planner.md / book-analyst.md / researcher.md / hook-engineer.md
│   │   ├── writer.md / producer.md / reviewer.md / archivist.md
│   └── workflows/
│       ├── season-pipeline.js       # M0：Phase A 骨架
│       └── episode-pipeline.js      # M0：Phase B 骨架
├── schemas/                         # M1：9 个 schema
│   ├── book.schema.json / season-plan.schema.json / episode-card.schema.json
│   ├── voices.schema.json / arc.schema.json / script.schema.json
│   ├── production-notes.schema.json / audio-qa.schema.json / season-bible.schema.json
├── scripts/
│   ├── show_resolver.py             # Task 1
│   ├── book_source.py               # Task 2
│   ├── ingest_book.py               # Task 3
│   ├── script_parser.py             # Task 4
│   ├── tts.py                       # Task 5
│   ├── voice_budget.py              # Task 6
│   ├── lint_script.py               # Task 7
│   ├── lint_voices.py               # Task 8
│   ├── lint_punct.py                # Task 9
│   ├── lint_anchors.py              # Task 9
│   ├── lint_trace.py                # Task 9
│   ├── audio_qa.py                  # Task 10
│   ├── season_bible.py              # Task 11
│   ├── archivist.py                 # Task 11
│   └── new_show.py                  # Task 13
├── tests/                           # 各代码任务对应测试
│   ├── test_show_resolver.py / test_book_source.py / test_ingest.py
│   ├── test_script_parser.py / test_tts_abstraction.py / test_voice_budget.py
│   ├── test_lint_script.py / test_lint_voices.py / test_lint_punct.py
│   ├── test_lint_anchors.py / test_lint_trace.py / test_audio_qa.py
│   ├── test_season_bible.py / test_archivist.py / test_new_show.py
│   └── fixtures/                    # 测试固定物（假书源/假脚本/假音频）
├── docs/superpowers/
│   ├── specs/                       # 已存在：设计规格
│   └── ARCHITECT-RUNBOOK.md         # M0：发车手册
└── shows/<name>/                    # M1 起：实例目录
    ├── devpodcast.json / SHOW.md
    ├── source-book/                 # ingest_book.py 产出（快照）
    ├── season/{season-plan.json, arc.json, voices.json, bible/}
    ├── trace/  voice-samples/
    └── episodes/ep01-slug/{episode-card.json, script.md, production-notes.md, audio/, shownotes.md, reviews/}
```

---

### Task 1: 骨架 — devpodcast.json + show_resolver.py

**Files:**
- Create: `devpodcast.json`
- Create: `scripts/show_resolver.py`
- Test: `tests/test_show_resolver.py`

**Interfaces:**
- Produces: `resolve_show(root=None) -> Path`（活动节目目录）、`active_show_name() -> str`、`show_config(show_dir) -> dict`（读该节目 devpodcast.json）。后续所有脚本经它定位节目。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_show_resolver.py
import json
from pathlib import Path
import pytest
from scripts.show_resolver import resolve_show, active_show_name, show_config

def test_resolve_active_show(tmp_path):
    (tmp_path / "shows" / "demo").mkdir(parents=True)
    (tmp_path / "shows" / "demo" / "devpodcast.json").write_text(
        json.dumps({"show": "demo"}), encoding="utf-8")
    (tmp_path / "devpodcast.json").write_text(
        json.dumps({"active_show": "demo", "shows": {"demo": {"config": "shows/demo/devpodcast.json"}}}),
        encoding="utf-8")
    assert resolve_show(tmp_path).name == "demo"
    assert active_show_name(tmp_path) == "demo"

def test_show_config_reads_instance_file(tmp_path):
    (tmp_path / "shows" / "demo").mkdir(parents=True)
    (tmp_path / "shows" / "demo" / "devpodcast.json").write_text(
        json.dumps({"show": "demo", "format": {"hosts": 2}}), encoding="utf-8")
    cfg = show_config(tmp_path / "shows" / "demo")
    assert cfg["format"]["hosts"] == 2

def test_resolve_missing_show_raises(tmp_path):
    (tmp_path / "devpodcast.json").write_text(
        json.dumps({"active_show": "nope", "shows": {}}), encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        resolve_show(tmp_path)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_show_resolver.py -v`
Expected: FAIL（ModuleNotFoundError: show_resolver）

- [ ] **Step 3: 写实现**

```python
# scripts/show_resolver.py
"""活动节目定位：devpodcast.json.active_show 或环境变量 DEVPODCAST_SHOW 覆盖。"""
import json, os
from pathlib import Path

def _root(root=None) -> Path:
    return Path(root) if root else Path(__file__).resolve().parent.parent

def active_show_name(root=None) -> str:
    env = os.environ.get("DEVPODCAST_SHOW")
    if env:
        return env
    reg = json.loads((_root(root) / "devpodcast.json").read_text(encoding="utf-8"))
    return reg["active_show"]

def resolve_show(root=None) -> Path:
    name = active_show_name(root)
    p = _root(root) / "shows" / name
    if not (p / "devpodcast.json").exists():
        raise FileNotFoundError(f"活动节目 {name} 缺少 shows/{name}/devpodcast.json")
    return p

def show_config(show_dir: Path) -> dict:
    return json.loads((Path(show_dir) / "devpodcast.json").read_text(encoding="utf-8"))
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_show_resolver.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: 写顶层注册表**

```json
// devpodcast.json
{
  "version": "1.0",
  "description": "devpodcast — 把一本技术书变成一季双人对谈播客（议题驱动、批判先行、引真实社区声音、本地 GPU 合成）。",
  "active_show": "vllm-podcast",
  "shows": {
    "vllm-podcast": { "config": "shows/vllm-podcast/devpodcast.json", "title": "把 vLLM 拆开讲" }
  },
  "shared": {
    "operating_doc": "CLAUDE.md",
    "runbook": "docs/superpowers/ARCHITECT-RUNBOOK.md",
    "spec": "docs/superpowers/specs/2026-08-01-devpodcast-design.md",
    "agents_dir": ".claude/agents",
    "workflow_phase_a": ".claude/workflows/season-pipeline.js",
    "workflow_phase_b": ".claude/workflows/episode-pipeline.js",
    "linters": [
      "scripts/lint_script.py", "scripts/lint_voices.py", "scripts/lint_punct.py",
      "scripts/lint_anchors.py", "scripts/lint_trace.py"
    ]
  }
}
```

- [ ] **Step 6: 提交**

```bash
git add devpodcast.json scripts/show_resolver.py tests/test_show_resolver.py
git commit -m "feat: 顶层注册表 + 活动节目定位（show_resolver）"
```

---

### Task 2: BookSource 抽象 + Repo2BookSource

**Files:**
- Create: `scripts/book_source.py`
- Test: `tests/test_book_source.py`
- Test fixture: `tests/fixtures/repo2book-mini/`（微型 repo2book 结构：outline-final.json + 2 章 dossier/narrative + glossary.json）

**Interfaces:**
- Consumes: —（纯新）
- Produces:
  - `Book` dataclass（title / chapters: list[ChapterCard] / digest: str）
  - `ChapterCard` dataclass（chapter_id / title / slug / sections: list[str] / key_classes: list[dict] / mechanisms: list[dict] / narrative_path: Path）
  - `class Repo2BookSource(BookSource)` with `__init__(root: Path, instance: str)`、`load() -> Book`、`chapter_cards() -> list[ChapterCard]`、`glossary() -> dict`、`outline() -> list`
  - `class BookSource(Protocol)` 定义同签名的 duck-type 协议

**要点抽取规则（本任务核心，来自真实核实）：**
- `sections`：从 narrative `chapter.md` 正则 `^##\s+(\d+\.\d+)\s+(.*)$` 抓 `<章号>.<节号> <标题>` 成 `"13.1 没有 prefill 相，没有 decode 相"` 形式
- `key_classes`：dossier.json `key_classes`（39/39 章有）
- `mechanisms`：dossier.json `mechanisms`（可能为空数组，容忍）
- 标题：narrative 首行 `# 第N章　<标题>` 去章号前缀
- outline-final.json 是 **list**（非 dict）；glossary.json 是 **dict**（key=中文术语）

- [ ] **Step 1: 建测试 fixture**

```bash
mkdir -p tests/fixtures/repo2book-mini/artifacts/ch01-foo/dossier tests/fixtures/repo2book-mini/artifacts/ch01-foo/narrative tests/fixtures/repo2book-mini/artifacts/ch02-bar/dossier tests/fixtures/repo2book-mini/artifacts/ch02-bar/narrative tests/fixtures/repo2book-mini/book/cartography tests/fixtures/repo2book-mini/book/bible
```

```python
# tests/fixtures/repo2book-mini/book/cartography/outline-final.json
[{"chapter_id": "ch01", "slug": "ch01-foo", "title": "Foo 章"}, {"chapter_id": "ch02", "slug": "ch02-bar", "title": "Bar 章"}]

# tests/fixtures/repo2book-mini/book/bible/glossary.json
{"连续批处理": "continuous batching", "分页 KV 缓存": "PagedAttention"}
```

```python
# tests/fixtures/repo2book-mini/artifacts/ch01-foo/dossier/dossier.json
{"chapter_id": "ch01", "title": "Foo 章", "key_classes": [{"name": "FooEngine", "file": "demo/foo.py", "responsibility": "干 Foo"}], "mechanisms": [{"id": "m1", "name": "机制甲", "difficulty": "core"}], "code_spine": []}

# tests/fixtures/repo2book-mini/artifacts/ch02-bar/dossier/dossier.json
{"chapter_id": "ch02", "title": "Bar 章", "key_classes": [{"name": "BarEngine", "file": "demo/bar.py", "responsibility": "干 Bar"}], "mechanisms": [], "code_spine": []}
```

```markdown
# tests/fixtures/repo2book-mini/artifacts/ch01-foo/narrative/chapter.md
# 第1章　Foo 章

## 你在这里

这里讲 Foo。

## 1.1 Foo 的第一步

正文。

## 1.2 Foo 的第二步

正文。
```

```markdown
# tests/fixtures/repo2book-mini/artifacts/ch02-bar/narrative/chapter.md
# 第2章　Bar 章

## 2.1 Bar 的唯一一步

正文。
```

- [ ] **Step 2: 写失败测试**

```python
# tests/test_book_source.py
import json
from pathlib import Path
import pytest
from scripts.book_source import Repo2BookSource, BookSource

FIX = Path(__file__).parent / "fixtures" / "repo2book-mini"

def test_load_book():
    src = Repo2BookSource(FIX, "mini")
    book = src.load()
    assert book.title == "mini"
    assert len(book.chapters) == 2

def test_chapter_cards_sections():
    src = Repo2BookSource(FIX, "mini")
    cards = src.chapter_cards()
    c1 = [c for c in cards if c.chapter_id == "ch01"][0]
    assert c1.title == "Foo 章"
    assert "1.1 Foo 的第一步" in c1.sections
    assert "1.2 Foo 的第二步" in c1.sections
    assert len(c1.key_classes) == 1 and c1.key_classes[0]["name"] == "FooEngine"
    assert c1.mechanisms[0]["id"] == "m1"

def test_empty_mechanisms_tolerated():
    src = Repo2BookSource(FIX, "mini")
    c2 = [c for c in src.chapter_cards() if c.chapter_id == "ch02"][0]
    assert c2.mechanisms == []
    assert len(c2.sections) == 1

def test_glossary_dict_shape():
    src = Repo2BookSource(FIX, "mini")
    g = src.glossary()
    assert g["连续批处理"] == "continuous batching"

def test_outline_is_list():
    src = Repo2BookSource(FIX, "mini")
    o = src.outline()
    assert isinstance(o, list) and o[0]["chapter_id"] == "ch01"

def test_implements_protocol():
    assert isinstance(Repo2BookSource(FIX, "mini"), BookSource)

def test_missing_instance_raises():
    with pytest.raises(FileNotFoundError):
        Repo2BookSource(FIX, "nope")
```

- [ ] **Step 3: 跑测试确认失败**

Run: `python3 -m pytest tests/test_book_source.py -v`
Expected: FAIL（ModuleNotFoundError / assertion）

- [ ] **Step 4: 写实现**

```python
# scripts/book_source.py
"""BookSource 抽象 + Repo2BookSource 实现（读 repo2book 实例目录，归一化成本项目 Book）。

要点抽取策略（2026-08-01 实测核实）：
- sections 主来源 = narrative 的 "## N.M 标题" 小节行（39/39 章稳定存在）
- key_classes = dossier.json（39/39 章存在）
- mechanisms = dossier.json（仅 8/39 章有 v3 账本，可能为空数组，容忍）
"""
import json, re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

SECTION_RE = re.compile(r"^##\s+(\d+\.\d+)\s+(.+)$", re.M)
TITLE_RE = re.compile(r"^#\s+第\d+章\s+(.+)$", re.M)


@dataclass
class ChapterCard:
    chapter_id: str
    title: str
    slug: str
    sections: list[str] = field(default_factory=list)       # "13.1 没有 prefill 相" 形式
    key_classes: list[dict] = field(default_factory=list)
    mechanisms: list[dict] = field(default_factory=list)
    narrative_path: Path | None = None

    def as_dict(self) -> dict:
        return {"chapter_id": self.chapter_id, "title": self.title, "slug": self.slug,
                "sections": self.sections, "key_classes": self.key_classes,
                "mechanisms": self.mechanisms}


@dataclass
class Book:
    title: str
    chapters: list[ChapterCard] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"title": self.title, "chapters": [c.as_dict() for c in self.chapters]}


class BookSource(Protocol):
    def load(self) -> Book: ...
    def chapter_cards(self) -> list[ChapterCard]: ...
    def glossary(self) -> dict: ...
    def outline(self) -> list: ...


class Repo2BookSource:
    """从 repo2book 实例目录抽取（当前唯一实现）。构造时校验路径与实例存在，否则拉闸。"""

    def __init__(self, root: Path | str, instance: str):
        self.root = Path(root)
        self.instance = instance
        self.inst_dir = self.root / "instances" / instance
        if not self.inst_dir.is_dir():
            raise FileNotFoundError(f"repo2book 实例不存在: {self.inst_dir}")

    def _chapter_dirs(self) -> list[Path]:
        arts = self.inst_dir / "artifacts"
        return sorted([p for p in arts.iterdir() if p.is_dir() and p.name.startswith("ch")])

    def chapter_cards(self) -> list[ChapterCard]:
        cards = []
        for d in self._chapter_dirs():
            chid = d.name.split("-")[0]
            narr = d / "narrative" / "chapter.md"
            dossier_path = d / "dossier" / "dossier.json"
            title = chid
            sections: list[str] = []
            key_classes: list[dict] = []
            mechanisms: list[dict] = []
            if narr.is_file():
                text = narr.read_text(encoding="utf-8")
                m = TITLE_RE.search(text)
                if m:
                    title = m.group(1).strip()
                sections = [f"{num} {name.strip()}" for num, name in SECTION_RE.findall(text)]
            if dossier_path.is_file():
                dd = json.loads(dossier_path.read_text(encoding="utf-8"))
                key_classes = dd.get("key_classes", []) or []
                mechanisms = dd.get("mechanisms", []) or []
            cards.append(ChapterCard(chid, title, d.name, sections, key_classes, mechanisms, narr if narr.is_file() else None))
        return cards

    def glossary(self) -> dict:
        p = self.inst_dir / "book" / "bible" / "glossary.json"
        if not p.is_file():
            return {}
        return json.loads(p.read_text(encoding="utf-8"))

    def outline(self) -> list:
        p = self.inst_dir / "book" / "cartography" / "outline-final.json"
        if not p.is_file():
            return []
        return json.loads(p.read_text(encoding="utf-8"))

    def load(self) -> Book:
        return Book(self.instance, self.chapter_cards())
```

- [ ] **Step 5: 跑测试确认通过**

Run: `python3 -m pytest tests/test_book_source.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add scripts/book_source.py tests/test_book_source.py tests/fixtures/repo2book-mini
git commit -m "feat: BookSource 抽象 + Repo2BookSource（narrative 小节为要点主源）"
```

---

### Task 3: ingest_book.py — 快照摄入

**Files:**
- Create: `scripts/ingest_book.py`
- Test: `tests/test_ingest.py`

**Interfaces:**
- Consumes: `BookSource.load()/chapter_cards()/glossary()/outline()`（Task 2）
- Produces:
  - `ingest(source: BookSource, show_dir: Path) -> dict`（返回 `{"digest": str, "chapters": int, "ingested_at": str}`）
  - `compute_digest(show_dir: Path) -> str`（对 source-book/ 全部文件做 sha256，确定性排序）
  - 落盘结构：`shows/<name>/source-book/{book.json, outline.json, glossary.json, chapter-cards/<chid>.json}`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_ingest.py
import json
from pathlib import Path
import pytest
from scripts.ingest_book import ingest, compute_digest
from scripts.book_source import Repo2BookSource

FIX = Path(__file__).parent / "fixtures" / "repo2book-mini"

def test_ingest_writes_snapshot(tmp_path):
    src = Repo2BookSource(FIX, "mini")
    res = ingest(src, tmp_path)
    assert res["chapters"] == 2
    book = json.loads((tmp_path / "source-book" / "book.json").read_text(encoding="utf-8"))
    assert len(book["chapters"]) == 2
    assert (tmp_path / "source-book" / "chapter-cards" / "ch01.json").is_file()
    assert (tmp_path / "source-book" / "glossary.json").is_file()
    assert (tmp_path / "source-book" / "outline.json").is_file()

def test_digest_changes_on_refresh(tmp_path):
    src = Repo2BookSource(FIX, "mini")
    d1 = ingest(src, tmp_path)["digest"]
    # 篡改快照后 digest 必须变化
    p = tmp_path / "source-book" / "glossary.json"
    p.write_text(json.dumps({"改": "了"}), encoding="utf-8")
    d2 = compute_digest(tmp_path)
    assert d1 != d2

def test_ingest_idempotent(tmp_path):
    src = Repo2BookSource(FIX, "mini")
    d1 = ingest(src, tmp_path)["digest"]
    d2 = ingest(src, tmp_path)["digest"]
    assert d1 == d2
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_ingest.py -v`
Expected: FAIL

- [ ] **Step 3: 写实现**

```python
# scripts/ingest_book.py
"""书源快照摄入：BookSource → shows/<name>/source-book/（此后 pipeline 只读快照，不再触碰外部路径）。"""
import hashlib, json
from pathlib import Path
from scripts.book_source import BookSource

def _stable_digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()

def compute_digest(show_dir: Path) -> str:
    sb = Path(show_dir) / "source-book"
    if not sb.is_dir():
        raise FileNotFoundError(f"缺少快照目录: {sb}")
    h = hashlib.sha256()
    for p in sorted(sb.rglob("*")):
        if p.is_file():
            h.update(p.relative_to(sb).as_posix().encode())
            h.update(p.read_bytes())
    return h.hexdigest()

def ingest(source: BookSource, show_dir: Path) -> dict:
    show_dir = Path(show_dir)
    sb = show_dir / "source-book"
    cards_dir = sb / "chapter-cards"
    cards_dir.mkdir(parents=True, exist_ok=True)
    book = source.load()
    (sb / "book.json").write_text(
        json.dumps(book.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    (sb / "outline.json").write_text(
        json.dumps(source.outline(), ensure_ascii=False, indent=2), encoding="utf-8")
    (sb / "glossary.json").write_text(
        json.dumps(source.glossary(), ensure_ascii=False, indent=2), encoding="utf-8")
    for card in book.chapters:
        (cards_dir / f"{card.chapter_id}.json").write_text(
            json.dumps(card.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return {"digest": compute_digest(show_dir), "chapters": len(book.chapters), "ingested_at": ""}
```

（`ingested_at` 日期由调用方在 workflow 里填；纯函数避免 Date.now 依赖。）

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_ingest.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/ingest_book.py tests/test_ingest.py
git commit -m "feat: ingest_book 快照摄入（digest 可校验，篡改即漂移）"
```

---

### Task 4: script.md 解析器

**Files:**
- Create: `scripts/script_parser.py`
- Test: `tests/test_script_parser.py`

**Interfaces:**
- Produces:
  - `@dataclass Turn`: `speaker: str`（"S1"/"S2"）、`text: str`、`voice_refs: list[str]`、`pause_ms: int | None`
  - `@dataclass Script`: `title: str`、`turns: list[Turn]`；`parse(path) -> Script`；`to_dialogue_tags(turn) -> str`（`[S1]text[/S1]` 形式，MOSS-TTSD 输入）
  - `format_error` 集合：缺 `[` 或 `[/` 成对、未知 speaker、非法 `<break>` 值

**script.md 约定格式（writer 契约的一部分）：**

```markdown
# ep01 议题标题

## 开场
[S1] 大家好，这期聊…… [/S1]
[S2] 开场第一个点…… {{voice:voice-001}} [/S2]

## 主体
[S1] …… <break 500ms> 停顿后继续…… [/S1]

## 收尾
[S2] 收尾金句。 [/S2]
```

- [ ] **Step 1: 写失败测试**

```python
# tests/test_script_parser.py
from pathlib import Path
import pytest
from scripts.script_parser import parse, ScriptParseError

def test_parse_basic(tmp_path):
    p = tmp_path / "script.md"
    p.write_text("""# 议题标题

## 开场
[S1] 大家好 [/S1]
[S2] 嗯，这期聊这个 {{voice:voice-001}} [/S2]

## 收尾
[S2] 收尾金句 [/S2]
""", encoding="utf-8")
    s = parse(p)
    assert s.title == "议题标题"
    assert len(s.turns) == 3
    assert s.turns[0].speaker == "S1"
    assert s.turns[1].voice_refs == ["voice-001"]
    assert s.turns[2].speaker == "S2"

def test_parse_pause(tmp_path):
    p = tmp_path / "script.md"
    p.write_text("[S1] 前面 <break 500ms> 后面 [/S1]\n", encoding="utf-8")
    s = parse(p)
    assert s.turns[0].pause_ms == 500

def test_unclosed_tag_raises(tmp_path):
    p = tmp_path / "script.md"
    p.write_text("[S1] 没关括号 [/S2]\n", encoding="utf-8")
    with pytest.raises(ScriptParseError):
        parse(p)

def test_bad_speaker_raises(tmp_path):
    p = tmp_path / "script.md"
    p.write_text("[S3] 不该出现 [/S3]\n", encoding="utf-8")
    with pytest.raises(ScriptParseError):
        parse(p)

def test_to_dialogue_tags(tmp_path):
    p = tmp_path / "script.md"
    p.write_text("[S1] 你好 [/S1]\n", encoding="utf-8")
    s = parse(p)
    assert s.to_dialogue_tags(s.turns[0]) == "[S1] 你好 [/S1]"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_script_parser.py -v`
Expected: FAIL

- [ ] **Step 3: 写实现**

```python
# scripts/script_parser.py
"""script.md → Script 结构化对象（speaker 成对 / 停顿 / voices 引用）。
格式：每段以 [S1] 或 [S2] 开头、[/S1] 或 [/S2] 结尾；{{voice:<id>}} 引 voices；
<break Nms> 显式停顿。"""
import re
from dataclasses import dataclass, field
from pathlib import Path

TURN_RE = re.compile(r"\[(S[12])\](.*?)\[/\1\]", re.S)
VOICE_RE = re.compile(r"\{\{voice:([a-zA-Z0-9_-]+)\}\}")
BREAK_RE = re.compile(r"<break\s+(\d+)ms\s*>")


class ScriptParseError(ValueError):
    pass


@dataclass
class Turn:
    speaker: str
    text: str
    voice_refs: list[str] = field(default_factory=list)
    pause_ms: int | None = None


@dataclass
class Script:
    title: str
    turns: list[Turn] = field(default_factory=list)

    @staticmethod
    def to_dialogue_tags(turn: Turn) -> str:
        return f"[{turn.speaker}] {turn.text} [/{turn.speaker}]"


def parse(path: Path) -> Script:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    title = ""
    m = re.search(r"^#\s+(.+)$", text, re.M)
    if m:
        title = m.group(1).strip()

    turns: list[Turn] = []
    for m in TURN_RE.finditer(text):
        speaker = m.group(1)
        body = m.group(2).strip()
        refs = VOICE_RE.findall(body)
        bm = BREAK_RE.search(body)
        pause = int(bm.group(1)) if bm else None
        clean = VOICE_RE.sub("", body)
        clean = BREAK_RE.sub("", clean).strip()
        turns.append(Turn(speaker, clean, refs, pause))

    # 校验：找到 [S1] 开头但无配对闭合的片段
    open_stray = re.findall(r"\[(S[12])\](?!.*?\[/\1\])", text)
    if open_stray:
        raise ScriptParseError(f"未闭合的说话人标记: {open_stray}")
    bad = re.findall(r"\[S[^12]\]", text)
    if bad:
        raise ScriptParseError(f"非法说话人标记: {bad}")
    return Script(title, turns)
```

（简化实现：`TURN_RE` 已捕获成对结构，`open_stray`/`bad` 为兜底校验。）

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_script_parser.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/script_parser.py tests/test_script_parser.py
git commit -m "feat: script.md 解析器（speaker 成对/停顿/voices 引用）"
```

---

### Task 5: tts.py — TTS 抽象 + 本地 provider 骨架

**Files:**
- Create: `scripts/tts.py`
- Test: `tests/test_tts_abstraction.py`

**Interfaces:**
- Produces:
  - `@dataclass TTSOpts`: `sample_rate=24000`、`max_new_tokens: int | None`、`temperature=0.6`、`top_k=50`、`top_p=0.9`
  - `@dataclass VoiceSpec`: `name`、`ref_audio: Path | None`
  - `@dataclass AudioBundle`: `wav_path: Path`、`segments: list[Path]`、`duration_s: float`、`vram_gb: float`
  - `class TTSProvider(Protocol)`: `synthesize(script: Script, voice_map: dict[str, VoiceSpec], opts: TTSOpts) -> AudioBundle`、`list_voices() -> list[VoiceSpec]`、`native_dialogue -> bool`
  - `class LocalTTSProvider`: `__init__(model_dir, device="cuda:0", dtype="bfloat16")`、`warmup()`、`vram_report() -> dict`
  - `class DialogueTTSProvider(LocalTTSProvider)`: `native_dialogue = True`（MOSS-TTSD 挂接点；synthesize 先抛 NotImplementedError，Task 17 装真模型后实现）
  - `class SegmentedTTSProvider(LocalTTSProvider)`: `native_dialogue = False`，类常量 `PAUSE_SPEAKER_SWITCH_MS=(350,500)`、`PAUSE_SAME_SPEAKER_MS=(150,250)`（CosyVoice3 fallback 挂接点）
  - `load_provider(config: dict) -> TTSProvider`（按 devpodcast.json `tts.provider` 键分派；未知键抛 ValueError）

- [ ] **Step 1: 写失败测试**

```python
# tests/test_tts_abstraction.py
import pytest
from scripts.tts import (DialogueTTSProvider, SegmentedTTSProvider, load_provider,
                         TTSProvider, TTSOpts)

def test_dialogue_provider_native_flag():
    p = DialogueTTSProvider(model_dir="/tmp/nonexistent")
    assert p.native_dialogue is True

def test_segmented_provider_pause_constants():
    p = SegmentedTTSProvider(model_dir="/tmp/nonexistent")
    assert p.PAUSE_SPEAKER_SWITCH_MS == (350, 500)
    assert p.PAUSE_SAME_SPEAKER_MS == (150, 250)

def test_load_provider_dispatch():
    p = load_provider({"provider": "moss-ttsd"})
    assert isinstance(p, DialogueTTSProvider)
    p2 = load_provider({"provider": "cosyvoice3"})
    assert isinstance(p2, SegmentedTTSProvider)

def test_load_provider_unknown_raises():
    with pytest.raises(ValueError):
        load_provider({"provider": "nope"})

def test_synthesize_not_implemented_yet():
    p = DialogueTTSProvider(model_dir="/tmp/nonexistent")
    with pytest.raises(NotImplementedError):
        p.synthesize(script=None, voice_map={}, opts=TTSOpts())

def test_implements_protocol():
    assert isinstance(DialogueTTSProvider(model_dir="/tmp/nonexistent"), TTSProvider)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_tts_abstraction.py -v`
Expected: FAIL

- [ ] **Step 3: 写实现**

```python
# scripts/tts.py
"""TTS 抽象层：DialogueTTSProvider（MOSS-TTSD，原生对话）与 SegmentedTTSProvider
（CosyVoice3，逐句+拼接）两类，统一 Protocol。本地基类管理 GPU/batch/预热/显存。"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

# 需在 M0 环境任务（Task 17）安装 torch；本文件顶层不 import torch，避免无 GPU 环境崩溃。


@dataclass
class TTSOpts:
    sample_rate: int = 24000
    max_new_tokens: int | None = None
    temperature: float = 0.6
    top_k: int = 50
    top_p: float = 0.9


@dataclass
class VoiceSpec:
    name: str
    ref_audio: Path | None = None


@dataclass
class AudioBundle:
    wav_path: Path
    segments: list[Path] = field(default_factory=list)
    duration_s: float = 0.0
    vram_gb: float = 0.0


class TTSProvider(Protocol):
    native_dialogue: bool

    def synthesize(self, script, voice_map: dict, opts: TTSOpts) -> AudioBundle: ...
    def list_voices(self) -> list[VoiceSpec]: ...


class LocalTTSProvider:
    """本地基类：GPU 设备管理、模型预热、显存报告。子类实现 synthesize。"""

    def __init__(self, model_dir: str | Path, device: str = "cuda:0", dtype: str = "bfloat16"):
        self.model_dir = Path(model_dir)
        self.device = device
        self.dtype = dtype

    def warmup(self) -> None:
        """预热到稳态：子类实现（Task 17 真装模型后）。"""
        raise NotImplementedError

    def vram_report(self) -> dict:
        try:
            import torch
        except ImportError:
            return {"error": "torch not installed"}
        if not torch.cuda.is_available():
            return {"error": "cuda not available"}
        props = torch.cuda.get_device_properties(0)
        return {"device": torch.cuda.get_device_name(0),
                "total_gb": round(props.total_memory / 1024 ** 3, 1),
                "used_gb": round((props.total_memory - torch.cuda.mem_get_info(0)[0]) / 1024 ** 3, 1)}


class DialogueTTSProvider(LocalTTSProvider):
    """MOSS-TTSD：整段对话一次合成。Script → [S1]/[S2] 标签串 → 单次生成。"""
    native_dialogue = True

    def synthesize(self, script, voice_map: dict, opts: TTSOpts) -> AudioBundle:
        raise NotImplementedError("MOSS-TTSD 模型接入在 Task 17（M0 环境）")


class SegmentedTTSProvider(LocalTTSProvider):
    """CosyVoice3：逐句合成 + 规则插静音拼接。"""
    native_dialogue = False
    PAUSE_SPEAKER_SWITCH_MS = (350, 500)
    PAUSE_SAME_SPEAKER_MS = (150, 250)

    def synthesize(self, script, voice_map: dict, opts: TTSOpts) -> AudioBundle:
        raise NotImplementedError("CosyVoice3 模型接入在 fallback 任务")


def load_provider(config: dict) -> TTSProvider:
    kind = config.get("provider", "")
    if kind == "moss-ttsd":
        return DialogueTTSProvider(model_dir=config.get("model_dir", "models/moss-ttsd"))
    if kind == "cosyvoice3":
        return SegmentedTTSProvider(model_dir=config.get("model_dir", "models/cosyvoice3"))
    raise ValueError(f"未知 TTS provider: {kind!r}")
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_tts_abstraction.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/tts.py tests/test_tts_abstraction.py
git commit -m "feat: TTS 抽象层（对话/分段两类 provider + 本地基类）"
```

---

### Task 6: voice_budget.py — 时长/节奏预算

**Files:**
- Create: `scripts/voice_budget.py`
- Test: `tests/test_voice_budget.py`

**Interfaces:**
- Consumes: `Script`/`Turn`（Task 4）
- Produces:
  - `estimate_duration(text: str, cps: float = 4.0) -> float`（中文默认 4 字/秒 = 240 字/分钟；返回秒）
  - `estimate_script_duration(script: Script) -> float`
  - `budget_check(script: Script, target_minutes: float) -> list[str]`（超 15% 报 BLOCKING 级 issue；单 turn > 200 字报 issue）

- [ ] **Step 1: 写失败测试**

```python
# tests/test_voice_budget.py
import pytest
from scripts.voice_budget import estimate_duration, estimate_script_duration, budget_check
from scripts.script_parser import parse
from pathlib import Path

def test_estimate_duration_default_speed():
    # 80 字 @ 4字/秒 = 20 秒
    assert estimate_duration("x" * 80) == pytest.approx(20.0)

def test_estimate_duration_custom_speed():
    assert estimate_duration("x" * 80, cps=2.0) == pytest.approx(40.0)

def test_estimate_script_duration(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] " + "x" * 400 + " [/S1]\n", encoding="utf-8")
    s = parse(p)
    assert estimate_script_duration(s) == pytest.approx(100.0)

def test_budget_check_ok(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] " + "x" * 400 + " [/S1]\n", encoding="utf-8")
    assert budget_check(parse(p), target_minutes=2.0) == []

def test_budget_check_over(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] " + "x" * 400 + " [/S1]\n", encoding="utf-8")
    issues = budget_check(parse(p), target_minutes=1.0)  # 100s > 69s(1.15x)
    assert len(issues) >= 1

def test_budget_check_long_turn(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] " + "x" * 300 + " [/S1]\n", encoding="utf-8")
    issues = budget_check(parse(p), target_minutes=5.0)
    assert any("300" in i for i in issues)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_voice_budget.py -v`
Expected: FAIL

- [ ] **Step 3: 写实现**

```python
# scripts/voice_budget.py
"""时长/节奏预算：中文默认 4 字/秒口播；单 turn 上限 200 字（口播换气）。"""
from scripts.script_parser import Script, Turn

DEFAULT_CPS = 4.0
MAX_TURN_CHARS = 200
TOLERANCE = 1.15  # 目标时长的 15% 余量


def estimate_duration(text: str, cps: float = DEFAULT_CPS) -> float:
    return len(text) / cps


def estimate_script_duration(script: Script) -> float:
    return sum(estimate_duration(t.text) for t in script.turns)


def budget_check(script: Script, target_minutes: float) -> list[str]:
    issues: list[str] = []
    total_s = estimate_script_duration(script)
    target_s = target_minutes * 60
    if total_s > target_s * TOLERANCE:
        issues.append(f"BLOCKING: 预计 {total_s:.0f}s 超过目标 {target_s:.0f}s 的 {TOLERANCE:.0%} 余量")
    for i, t in enumerate(script.turns):
        if len(t.text) > MAX_TURN_CHARS:
            issues.append(f"WARN: turn {i} ({t.speaker}) 长 {len(t.text)} 字，超过 {MAX_TURN_CHARS} 字换气上限")
    return issues
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_voice_budget.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/voice_budget.py tests/test_voice_budget.py
git commit -m "feat: voice_budget 时长/换气预算"
```

---

### Task 7: lint_script.py — 脚本门禁

**Files:**
- Create: `scripts/lint_script.py`
- Test: `tests/test_lint_script.py`

**Interfaces:**
- Consumes: `Script.parse`（Task 4）、`budget_check`（Task 6）、voices.json（外部输入）
- Produces: `lint_script(path, voices: dict, target_minutes: float) -> list[dict]`（每项 `{"level": "BLOCKING"|"WARN", "msg": str}`）；CLI 入口 `python3 scripts/lint_script.py <path> [--voices <voices.json>] [--target-minutes N]`，退出码 0=通过 / 1=有 BLOCKING。

检查项：
1. `{{voice:<id>}}` 引用必须在 voices dict 中存在（id 集合）
2. speaker 比例不一边倒：任意说话人 turn 数 < 总数 30% → WARN（防捧哏）
3. 至少一个"我不知道"类表述（`我不知道`/`没搞清`/`没想明白`/`说不准`）→ WARN 级提示（防语境误报，非阻断）
4. 预算检查（Task 6 结果合并）

- [ ] **Step 1: 写失败测试**

```python
# tests/test_lint_script.py
import json
from pathlib import Path
import pytest
from scripts.lint_script import lint_script

VOICES = {"voice-001": {"claim": "面试要口算"}, "voice-002": {"claim": "社区吐槽"}}

def test_voice_refs_must_exist(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] 这里 {{voice:voice-999}} 不存在 [/S1]\n", encoding="utf-8")
    issues = lint_script(p, VOICES, target_minutes=5)
    assert any("voice-999" in i["msg"] and i["level"] == "BLOCKING" for i in issues)

def test_voice_refs_valid_ok(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] 这里 {{voice:voice-001}} 存在 [/S1]\n", encoding="utf-8")
    issues = lint_script(p, VOICES, target_minutes=5)
    assert all("voice-999" not in i["msg"] for i in issues)

def test_unknown_word_warn(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] 开场 [/S1]\n[S2] 主体内容 [/S2]\n", encoding="utf-8")
    issues = lint_script(p, VOICES, target_minutes=5)
    assert any("我不知道" in i["msg"] and i["level"] == "WARN" for i in issues)

def test_unknown_word_present_no_warn(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] 这个我们也没搞清楚，评论区有懂的说说 [/S1]\n[S2] 回应 [/S2]\n", encoding="utf-8")
    issues = lint_script(p, VOICES, target_minutes=5)
    assert not any("我不知道" in i["msg"] for i in issues)

def test_bald_broadcast_warn(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] a [/S1]\n[S1] b [/S1]\n[S1] c [/S1]\n[S2] d [/S2]\n", encoding="utf-8")
    issues = lint_script(p, VOICES, target_minutes=5)
    assert any("30%" in i["msg"] and i["level"] == "WARN" for i in issues)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_lint_script.py -v`
Expected: FAIL

- [ ] **Step 3: 写实现**

```python
# scripts/lint_script.py
"""脚本门禁：voices 引用存在性 / 双声线平衡 / 「我不知道」warn / 时长预算。"""
import json, re, sys
from pathlib import Path
from scripts.script_parser import parse
from scripts.voice_budget import budget_check, MAX_TURN_CHARS

UNKNOWN_WORDS = ("我不知道", "没搞清", "没想明白", "说不准")
MIN_SPEAKER_RATIO = 0.30


def lint_script(path: Path, voices: dict, target_minutes: float) -> list[dict]:
    issues: list[dict] = []
    script = parse(path)

    # 1. voices 引用存在性
    known = set(voices.keys())
    for i, t in enumerate(script.turns):
        for ref in t.voice_refs:
            if ref not in known:
                issues.append({"level": "BLOCKING", "msg": f"turn {i} 引用未知 voice id: {ref}"})

    # 2. 双声线平衡
    if script.turns:
        n = len(script.turns)
        s1 = sum(1 for t in script.turns if t.speaker == "S1")
        s2 = n - s1
        for sp, cnt in (("S1", s1), ("S2", s2)):
            if cnt / n < MIN_SPEAKER_RATIO:
                issues.append({"level": "WARN", "msg": f"{sp} 仅 {cnt}/{n} turn（{cnt/n:.0%}），低于 {MIN_SPEAKER_RATIO:.0%}——防捧哏"})

    # 3. 「我不知道」出现（warn，防语境误报）
    all_text = "".join(t.text for t in script.turns)
    if not any(w in all_text for w in UNKNOWN_WORDS):
        issues.append({"level": "WARN", "msg": "全脚本无「我不知道/没搞清」类表述——voice-guide 纪律 1 要求每期至少一次"})

    # 4. 时长/换气预算
    issues.extend(budget_check(script, target_minutes))
    return issues


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    path = Path(argv[0])
    voices: dict = {}
    target = 35.0
    if "--voices" in argv:
        voices = json.loads(Path(argv[argv.index("--voices") + 1]).read_text(encoding="utf-8"))
    if "--target-minutes" in argv:
        target = float(argv[argv.index("--target-minutes") + 1])
    issues = lint_script(path, voices, target)
    for i in issues:
        print(f"[{i['level']}] {i['msg']}")
    return 1 if any(i["level"] == "BLOCKING" for i in issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_lint_script.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/lint_script.py tests/test_lint_script.py
git commit -m "feat: lint_script 门禁（voices 引用/声线平衡/我不知道/预算）"
```

---

### Task 8: lint_voices.py — voices 门禁

**Files:**
- Create: `scripts/lint_voices.py`
- Test: `tests/test_lint_voices.py`

**Interfaces:**
- Produces: `lint_voices(voices: dict) -> list[dict]`（`{"level", "msg"}`）；CLI 退出码同 Task 7。
- 校验规则（spec §6.4 的 5 条）：
  1. `source_url` + `source_date` 必填
  2. `anonymized=false` 仅允许 `source_platform` ∈ {official, paper, github-issue}
  3. `confidence=low` 须 `writer_note` 含「未一手核实」
  4. 同 term 至少 2 条不同平台（除非 verified=official），否则 WARN 单一来源
  5. `category=job-seeker` 条目的 `source_platform` 必须在求职者平台集合内

```python
JOB_SEEKER_PLATFORMS = {"zhihu", "v2ex", "niuke", "maimai", "xhs", "bili", "jike",
                        "reddit", "hn", "x", "blind", "linkedin"}
OFFICIAL_PLATFORMS = {"official", "paper", "github-issue"}
```

- [ ] **Step 1: 写失败测试**

```python
# tests/test_lint_voices.py
import pytest
from scripts.lint_voices import lint_voices

def base_voice(**kw):
    v = {"id": "v1", "category": "critical", "term": "t", "claim": "c",
         "verified": "community-only", "source_url": "https://x.example/1",
         "source_date": "2026-07-15", "source_platform": "hn",
         "speaker_handle": "@匿名", "anonymized": True,
         "confidence": "high", "writer_note": ""}
    v.update(kw)
    return v

def test_missing_url_blocking():
    v = base_voice(source_url="")
    issues = lint_voices({"v1": v})
    assert any("source_url" in i["msg"] and i["level"] == "BLOCKING" for i in issues)

def test_missing_date_blocking():
    v = base_voice(source_date="")
    issues = lint_voices({"v1": v})
    assert any("source_date" in i["msg"] and i["level"] == "BLOCKING" for i in issues)

def test_non_anonymous_requires_official_platform():
    v = base_voice(anonymized=False, source_platform="reddit")
    issues = lint_voices({"v1": v})
    assert any("anonymized" in i["msg"] and i["level"] == "BLOCKING" for i in issues)

def test_official_platform_can_be_named():
    v = base_voice(anonymized=False, source_platform="official")
    issues = lint_voices({"v1": v})
    assert not any("anonymized" in i["msg"] for i in issues)

def test_low_confidence_requires_note():
    v = base_voice(confidence="low", writer_note="")
    issues = lint_voices({"v1": v})
    assert any("未一手核实" in i["msg"] and i["level"] == "BLOCKING" for i in issues)

def test_single_source_warn():
    issues = lint_voices({"v1": base_voice()})
    assert any("单一来源" in i["msg"] and i["level"] == "WARN" for i in issues)

def test_two_platforms_no_warn():
    v1 = base_voice()
    v2 = base_voice(id="v2", source_url="https://y.example/2", source_platform="zhihu")
    issues = lint_voices({"v1": v1, "v2": v2})
    assert not any("单一来源" in i["msg"] for i in issues)

def test_verified_official_single_source_ok():
    v = base_voice(verified="official")
    issues = lint_voices({"v1": v})
    assert not any("单一来源" in i["msg"] for i in issues)

def test_job_seeker_platform_rule():
    v = base_voice(category="job-seeker", source_platform="github-issue")
    issues = lint_voices({"v1": v})
    assert any("job-seeker" in i["msg"] and i["level"] == "BLOCKING" for i in issues)

def test_job_seeker_platform_ok():
    v = base_voice(category="job-seeker", source_platform="niuke")
    issues = lint_voices({"v1": v})
    assert not any("job-seeker" in i["msg"] for i in issues)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_lint_voices.py -v`
Expected: FAIL

- [ ] **Step 3: 写实现**

```python
# scripts/lint_voices.py
"""voices 门禁（spec §6.4 五条）：URL/日期必填 / 匿名化 / low-confidence 标注 /
多平台 / 求职者平台约束。"""
import sys
from collections import Counter

JOB_SEEKER_PLATFORMS = {"zhihu", "v2ex", "niuke", "maimai", "xhs", "bili", "jike",
                        "reddit", "hn", "x", "blind", "linkedin"}
OFFICIAL_PLATFORMS = {"official", "paper", "github-issue"}


def lint_voices(voices: dict) -> list[dict]:
    issues: list[dict] = []
    for vid, v in voices.items():
        # ① URL/日期必填
        if not v.get("source_url"):
            issues.append({"level": "BLOCKING", "msg": f"{vid}: source_url 必填"})
        if not v.get("source_date"):
            issues.append({"level": "BLOCKING", "msg": f"{vid}: source_date 必填"})
        # ② 匿名化
        if not v.get("anonymized", True) and v.get("source_platform") not in OFFICIAL_PLATFORMS:
            issues.append({"level": "BLOCKING",
                           "msg": f"{vid}: anonymized=false 仅允许官方/作者/论文/issue 源（当前 {v.get('source_platform')}）"})
        # ③ low confidence 标注
        if v.get("confidence") == "low" and "未一手核实" not in v.get("writer_note", ""):
            issues.append({"level": "BLOCKING", "msg": f"{vid}: confidence=low 须 writer_note 标注「未一手核实」"})
        # ⑤ 求职者平台约束
        if v.get("category") == "job-seeker" and v.get("source_platform") not in JOB_SEEKER_PLATFORMS:
            issues.append({"level": "BLOCKING",
                           "msg": f"{vid}: job-seeker 条目须落在求职者平台集合内（当前 {v.get('source_platform')}）"})
    # ④ 单一来源 warn（按 term 聚合）
    by_term: dict[str, list[str]] = {}
    verified_official = {v["id"] for v in voices.values() if v.get("verified") == "official"}
    for vid, v in voices.items():
        by_term.setdefault(v.get("term", ""), []).append(v.get("source_platform", ""))
    for term, plats in by_term.items():
        if len(set(plats)) < 2 and all(vid not in verified_official for vid in voices if voices[vid].get("term") == term):
            issues.append({"level": "WARN", "msg": f"term「{term}」单一来源（{plats[0]}），建议 ≥2 平台或 verified=official"})
    return issues


def main(argv=None) -> int:
    import json
    from pathlib import Path
    argv = argv if argv is not None else sys.argv[1:]
    voices = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    issues = lint_voices(voices)
    for i in issues:
        print(f"[{i['level']}] {i['msg']}")
    return 1 if any(i["level"] == "BLOCKING" for i in issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_lint_voices.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/lint_voices.py tests/test_lint_voices.py
git commit -m "feat: lint_voices 五条门禁（spec §6.4）"
```

---

### Task 9: lint_punct / lint_anchors / lint_trace

**Files:**
- Create: `scripts/lint_punct.py`、`scripts/lint_anchors.py`、`scripts/lint_trace.py`
- Test: `tests/test_lint_punct.py`、`tests/test_lint_anchors.py`、`tests/test_lint_trace.py`

**Interfaces:**
- Produces:
  - `lint_punct(text: str) -> list[dict]`：中文全角语境里夹半角标点（`,.;` 夹在汉字之间）→ WARN（口播可读性）
  - `lint_anchors(ep_dir: Path, show_dir: Path) -> list[dict]`：`../epNN-xxx/` 跨期链接目标必须存在
  - `lint_trace(ep_dir: Path, voices: dict) -> list[dict]`：script 每个 `{{voice:<id>}}` 引用在 voices 中存在（与 lint_script 规则 1 重复——此为独立 CLI 供 workflow 使用，保持一致）

- [ ] **Step 1: 写失败测试**

```python
# tests/test_lint_punct.py
import pytest
from scripts.lint_punct import lint_punct

def test_halfwidth_between_cjk_warn():
    issues = lint_punct("这里用了半角,逗号")
    assert any("半角" in i["msg"] for i in issues)

def test_fullwidth_ok():
    issues = lint_punct("这里用了全角，逗号。")
    assert issues == []

def test_code_span_ignored():
    # 反引号内的半角标点不查（代码/术语）
    issues = lint_punct("看这里 `foo,bar` 结束")
    assert issues == []
```

```python
# tests/test_lint_anchors.py
import pytest
from scripts.lint_anchors import lint_anchors

def test_valid_link_ok(tmp_path):
    (tmp_path / "episodes" / "ep02-slug").mkdir(parents=True)
    (tmp_path / "episodes" / "ep01-slug" / "script.md").write_text(
        "[S1] 详见 [ep02](../../episodes/ep02-slug/script.md) [/S1]\n", encoding="utf-8")
    issues = lint_anchors(tmp_path / "episodes" / "ep01-slug", tmp_path)
    assert issues == []

def test_broken_link_blocking(tmp_path):
    (tmp_path / "episodes" / "ep01-slug").mkdir(parents=True)
    (tmp_path / "episodes" / "ep01-slug" / "script.md").write_text(
        "[S1] 详见 [ep02](../../episodes/ep02-ghost/script.md) [/S1]\n", encoding="utf-8")
    issues = lint_anchors(tmp_path / "episodes" / "ep01-slug", tmp_path)
    assert any("ep02-ghost" in i["msg"] and i["level"] == "BLOCKING" for i in issues)
```

```python
# tests/test_lint_trace.py
import pytest
from scripts.lint_trace import lint_trace
from pathlib import Path

VOICES = {"voice-001": {"claim": "面试要口算"}}

def test_ref_traceable(tmp_path):
    ep = tmp_path / "ep01"
    ep.mkdir()
    (ep / "script.md").write_text("[S1] {{voice:voice-001}} [/S1]\n", encoding="utf-8")
    issues = lint_trace(ep, VOICES)
    assert issues == []

def test_ref_missing_blocking(tmp_path):
    ep = tmp_path / "ep01"
    ep.mkdir()
    (ep / "script.md").write_text("[S1] {{voice:voice-999}} [/S1]\n", encoding="utf-8")
    issues = lint_trace(ep, VOICES)
    assert any("voice-999" in i["msg"] for i in issues)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_lint_punct.py tests/test_lint_anchors.py tests/test_lint_trace.py -v`
Expected: FAIL

- [ ] **Step 3: 写实现**

```python
# scripts/lint_punct.py
"""半角标点门禁：汉字之间的半角 ,.; 提示为 WARN（口播可读性；反引号代码段豁免）。"""
import re
import sys

CJK = r"一-鿿"
HALF = re.compile(rf"([{CJK}])[,.;]([{CJK}])")


def lint_punct(text: str) -> list[dict]:
    issues: list[dict] = []
    # 剥离反引号代码段后再查
    cleaned = re.sub(r"`[^`]*`", "", text)
    for m in HALF.finditer(cleaned):
        issues.append({"level": "WARN", "msg": f"汉字间半角标点: …{cleaned[max(0, m.start()-6):m.end()+6]}…（应全角）"})
    return issues


def main(argv=None) -> int:
    from pathlib import Path
    argv = argv if argv is not None else sys.argv[1:]
    text = Path(argv[0]).read_text(encoding="utf-8")
    for i in lint_punct(text):
        print(f"[{i['level']}] {i['msg']}")
    return 0  # 纯 WARN


if __name__ == "__main__":
    raise SystemExit(main())
```

```python
# scripts/lint_anchors.py
"""跨期锚点门禁：脚本里 `../episodes/epNN-xxx/` 链接目标必须存在。"""
import re
import sys
from pathlib import Path

LINK_RE = re.compile(r"\]\(\.\./\.\./episodes/([^/)]+)/")


def lint_anchors(ep_dir: Path, show_dir: Path) -> list[dict]:
    issues: list[dict] = []
    script = Path(ep_dir) / "script.md"
    if not script.is_file():
        return issues
    text = script.read_text(encoding="utf-8")
    for slug in LINK_RE.findall(text):
        target = Path(show_dir) / "episodes" / slug / "script.md"
        if not target.is_file():
            issues.append({"level": "BLOCKING", "msg": f"跨期链接目标不存在: {slug}"})
    return issues


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    ep_dir = Path(argv[0])
    show_dir = Path(argv[1]) if len(argv) > 1 else ep_dir.parent.parent
    for i in lint_anchors(ep_dir, show_dir):
        print(f"[{i['level']}] {i['msg']}")
    return 1 if any(i["level"] == "BLOCKING" for i in lint_anchors(ep_dir, show_dir)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

```python
# scripts/lint_trace.py
"""溯源门禁：script 的 {{voice:<id>}} 必须在 voices 集合内（workflow 独立 CLI 用）。"""
import json, re, sys
from pathlib import Path

REF_RE = re.compile(r"\{\{voice:([a-zA-Z0-9_-]+)\}\}")


def lint_trace(ep_dir: Path, voices: dict) -> list[dict]:
    issues: list[dict] = []
    script = Path(ep_dir) / "script.md"
    if not script.is_file():
        return issues
    text = script.read_text(encoding="utf-8")
    for ref in REF_RE.findall(text):
        if ref not in voices:
            issues.append({"level": "BLOCKING", "msg": f"引用了未知 voice id: {ref}"})
    return issues


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    ep_dir = Path(argv[0])
    voices_path = Path(argv[1])
    voices = json.loads(voices_path.read_text(encoding="utf-8"))
    for i in lint_trace(ep_dir, voices):
        print(f"[{i['level']}] {i['msg']}")
    return 1 if any(i["level"] == "BLOCKING" for i in lint_trace(ep_dir, voices)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_lint_punct.py tests/test_lint_anchors.py tests/test_lint_trace.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/lint_punct.py scripts/lint_anchors.py scripts/lint_trace.py tests/test_lint_punct.py tests/test_lint_anchors.py tests/test_lint_trace.py
git commit -m "feat: lint_punct/anchors/trace 三个门禁"
```

---

### Task 10: audio_qa.py — 试听质检

**Files:**
- Create: `scripts/audio_qa.py`
- Test: `tests/test_audio_qa.py`

**Interfaces:**
- Produces:
  - `@dataclass AudioQAReport`: `duration_s / peak_db / clipping: bool / silence_ratio: float / rms_db: float / issues: list[str] / vram_gb: float`
  - `analyze(path: Path, expected_minutes: float = 35.0) -> AudioQAReport`
  - `write_report(report, path)`（audio-qa.json）
  - 检查：时长超目标 20% → BLOCKING；clipping → BLOCKING；静音占比 > 25% → WARN；RMS < -40dB → WARN（太轻）

**依赖：`soundfile`（numpy 已随 torch 装）。** 测试用合成正弦波。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_audio_qa.py
import math
import numpy as np
import pytest
import soundfile as sf
from scripts.audio_qa import analyze, AudioQAReport

def make_wav(path, seconds=2.0, sr=24000, freq=440.0, amp=0.5, silence_frac=0.1):
    n = int(seconds * sr)
    t = np.arange(n) / sr
    x = amp * np.sin(2 * math.pi * freq * t).astype(np.float32)
    sil = int(n * silence_frac)
    x[:sil] = 0.0
    sf.write(str(path), x, sr)

def test_basic_duration(tmp_path):
    p = tmp_path / "a.wav"
    make_wav(p, seconds=2.0)
    r = analyze(p, expected_minutes=35.0)
    assert r.duration_s == pytest.approx(2.0, abs=0.05)
    assert not r.clipping
    assert r.peak_db < 0.0

def test_clipping_detected(tmp_path):
    p = tmp_path / "b.wav"
    make_wav(p, seconds=1.0, amp=2.0)  # 削波
    r = analyze(p)
    assert r.clipping

def test_silence_ratio(tmp_path):
    p = tmp_path / "c.wav"
    make_wav(p, seconds=4.0, silence_frac=0.5)
    r = analyze(p)
    assert r.silence_ratio > 0.4

def test_over_duration_blocking(tmp_path):
    p = tmp_path / "d.wav"
    make_wav(p, seconds=50.0)  # 目标 35min 的 20% 余量外
    r = analyze(p, expected_minutes=35.0)
    assert any("时长" in i for i in r.issues)

def test_write_report(tmp_path):
    p = tmp_path / "e.wav"
    make_wav(p, seconds=1.0)
    r = analyze(p)
    out = tmp_path / "audio-qa.json"
    write_report(r, out)
    import json
    assert json.loads(out.read_text(encoding="utf-8"))["duration_s"] == pytest.approx(1.0, abs=0.05)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_audio_qa.py -v`
Expected: FAIL（audio_qa 未定义）

- [ ] **Step 3: 写实现**

```python
# scripts/audio_qa.py
"""试听质检：时长/削波/静音占比/响度/显存。CLI 输出 JSON 报告。"""
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import soundfile as sf

CLIP_DB = -0.1  # 峰值超过 0dB 视为削波（接近满幅）
SILENCE_THRESHOLD_DB = -45.0
MAX_DURATION_TOLERANCE = 1.20
MIN_RMS_DB = -40.0


@dataclass
class AudioQAReport:
    duration_s: float = 0.0
    peak_db: float = -float("inf")
    clipping: bool = False
    silence_ratio: float = 0.0
    rms_db: float = -float("inf")
    issues: list[str] = None
    vram_gb: float = 0.0

    def __post_init__(self):
        if self.issues is None:
            self.issues = []


def _db(x: float) -> float:
    return 20.0 * np.log10(max(x, 1e-10))


def analyze(path: Path, expected_minutes: float = 35.0) -> AudioQAReport:
    path = Path(path)
    x, sr = sf.read(str(path), dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)
    r = AudioQAReport()
    r.duration_s = len(x) / sr
    r.peak_db = _db(float(np.abs(x).max()))
    r.clipping = r.peak_db > CLIP_DB
    rms = float(np.sqrt(np.mean(x ** 2)))
    r.rms_db = _db(rms)
    sil = x[np.abs(x) < 10 ** (SILENCE_THRESHOLD_DB / 20)]
    r.silence_ratio = len(sil) / len(x)

    target_s = expected_minutes * 60
    if r.duration_s > target_s * MAX_DURATION_TOLERANCE:
        r.issues.append(f"BLOCKING: 时长 {r.duration_s:.0f}s 超目标 {target_s:.0f}s 的 20% 余量")
    if r.clipping:
        r.issues.append(f"BLOCKING: 峰值 {r.peak_db:.1f}dB 削波")
    if r.silence_ratio > 0.25:
        r.issues.append(f"WARN: 静音占比 {r.silence_ratio:.0%} > 25%")
    if r.rms_db < MIN_RMS_DB:
        r.issues.append(f"WARN: 响度 {r.rms_db:.1f}dB 偏低（< {MIN_RMS_DB}dB）")
    return r


def write_report(report: AudioQAReport, path: Path) -> None:
    path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    wav = Path(argv[0])
    out = Path(argv[1]) if len(argv) > 1 else wav.with_suffix(".audio-qa.json")
    expected = float(argv[2]) if len(argv) > 2 else 35.0
    r = analyze(wav, expected)
    write_report(r, out)
    for i in r.issues:
        print(f"[{'BLOCKING' if i.startswith('BLOCKING') else 'WARN'}] {i}")
    return 1 if any(i.startswith("BLOCKING") for i in r.issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_audio_qa.py -v`
Expected: PASS

（若无 soundfile：`pip install soundfile`，或先用 `wave` 模块实现读取。**优先 soundfile，需保证测试环境装好再开工**。）

- [ ] **Step 5: 提交**

```bash
git add scripts/audio_qa.py tests/test_audio_qa.py
git commit -m "feat: audio_qa 试听质检（时长/削波/静音/响度）"
```

---

### Task 11: season_bible.py + archivist.py

**Files:**
- Create: `scripts/season_bible.py`、`scripts/archivist.py`
- Test: `tests/test_season_bible.py`、`tests/test_archivist.py`

**Interfaces:**
- Produces:
  - `season_bible.py` CLI：`due <ep_id>`（读 arc-map.json 返回应埋伏笔/应回收项）、`register <ep_id>`（回写 arc-map）
  - `archivist.py` CLI：`status`（打印 trace 统计）、`log <msg>`（追加 trace/entries.jsonl 带时间戳）；数据层函数 `log_entry(trace_dir, msg, kind)`、`read_entries(trace_dir) -> list[dict]`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_season_bible.py
import json
import pytest
from scripts.season_bible import due, register

def test_due_empty_bible(tmp_path):
    p = tmp_path / "arc-map.json"
    p.write_text(json.dumps({"episodes": {}, "foreshadow": {}}), encoding="utf-8")
    assert due(p, "ep01") == []

def test_due_returns_foreshadow_and_payoff(tmp_path):
    p = tmp_path / "arc-map.json"
    p.write_text(json.dumps({
        "episodes": {"ep01": {"foreshadow_due": ["伏笔甲"], "payoff_due": ["伏笔乙"]}}
    }), encoding="utf-8")
    r = due(p, "ep01")
    assert "伏笔甲" in r and "伏笔乙" in r

def test_register_updates_episode(tmp_path):
    p = tmp_path / "arc-map.json"
    p.write_text(json.dumps({"episodes": {"ep01": {}}}), encoding="utf-8")
    register(p, "ep01", {"foreshadow_laid": ["伏笔丙"], "payoff_resolved": ["伏笔乙"]})
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["episodes"]["ep01"]["foreshadow_laid"] == ["伏笔丙"]
```

```python
# tests/test_archivist.py
import json
import pytest
from scripts.archivist import log_entry, read_entries

def test_log_and_read(tmp_path):
    log_entry(tmp_path, "msg1", kind="note")
    log_entry(tmp_path, "msg2", kind="warning")
    entries = read_entries(tmp_path)
    assert len(entries) == 2
    assert entries[0]["msg"] == "msg1" and entries[0]["kind"] == "note"
    assert "at" in entries[0]
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_season_bible.py tests/test_archivist.py -v`
Expected: FAIL

- [ ] **Step 3: 写实现**

```python
# scripts/season_bible.py
"""Season Bible CLI：伏笔 due/回收登记（spec §4 archivist 职责的跨期部分）。"""
import json
import sys
from pathlib import Path


def _load(p: Path) -> dict:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def due(arc_map: Path, ep_id: str) -> list[str]:
    data = _load(arc_map)
    ep = data.get("episodes", {}).get(ep_id, {})
    return list(ep.get("foreshadow_due", [])) + list(ep.get("payoff_due", []))


def register(arc_map: Path, ep_id: str, fields: dict) -> None:
    p = Path(arc_map)
    data = _load(p)
    data.setdefault("episodes", {}).setdefault(ep_id, {})
    data["episodes"][ep_id].update(fields)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    cmd, arc_map, ep = argv[0], Path(argv[1]), argv[2]
    if cmd == "due":
        for item in due(arc_map, ep):
            print(item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

```python
# scripts/archivist.py
"""archivist 数据层：trace 长期记忆（JSONL 追加）。"""
import datetime
import json
import sys
from pathlib import Path


def log_entry(trace_dir: Path, msg: str, kind: str = "note") -> None:
    d = Path(trace_dir)
    d.mkdir(parents=True, exist_ok=True)
    entry = {"at": datetime.datetime.now().isoformat(timespec="seconds"), "kind": kind, "msg": msg}
    with (d / "entries.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_entries(trace_dir: Path) -> list[dict]:
    p = Path(trace_dir) / "entries.jsonl"
    if not p.is_file():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    trace_dir = Path(argv[0])
    cmd = argv[1] if len(argv) > 1 else "status"
    if cmd == "status":
        entries = read_entries(trace_dir)
        print(f"{len(entries)} entries")
        for e in entries[-10:]:
            print(f"[{e['at']}] ({e['kind']}) {e['msg']}")
    elif cmd == "log":
        log_entry(trace_dir, argv[2], argv[3] if len(argv) > 3 else "note")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_season_bible.py tests/test_archivist.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/season_bible.py scripts/archivist.py tests/test_season_bible.py tests/test_archivist.py
git commit -m "feat: season_bible（伏笔 due/回收）+ archivist（trace）"
```

---

### Task 12: schemas/ — 产物契约 JSON Schema

**Files:**
- Create: `schemas/book.schema.json`、`schemas/season-plan.schema.json`、`schemas/episode-card.schema.json`、`schemas/voices.schema.json`、`schemas/arc.schema.json`、`schemas/script.schema.json`、`schemas/production-notes.schema.json`、`schemas/audio-qa.schema.json`、`schemas/season-bible.schema.json`
- Test: `tests/test_schemas.py`

**Interfaces:**
- Produces: 9 个 JSON Schema（draft-07）。全部 schema 与 lint 规则一致（尤其 voices.schema 必须与 Task 8 的五条门禁同口径）。后续 workflow 校验产物时用 `jsonschema.validate`。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_schemas.py
import json
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError

SCHEMAS = Path(__file__).parent.parent / "schemas"

def all_schemas_parse():
    for p in SCHEMAS.glob("*.schema.json"):
        json.loads(p.read_text(encoding="utf-8"))

def test_all_schemas_are_valid_json():
    all_schemas_parse()  # 不抛即通过

def test_voices_schema_accepts_valid():
    s = json.loads((SCHEMAS / "voices.schema.json").read_text(encoding="utf-8"))
    v = {"id": "v1", "category": "critical", "term": "t", "claim": "c",
         "verified": "community-only", "source_url": "https://x.example/1",
         "source_date": "2026-07-15", "source_platform": "hn",
         "speaker_handle": "@匿名", "anonymized": True,
         "confidence": "high", "writer_note": ""}
    validate(v, s)

def test_voices_schema_rejects_missing_url():
    s = json.loads((SCHEMAS / "voices.schema.json").read_text(encoding="utf-8"))
    v = {"id": "v1", "category": "critical", "term": "t", "claim": "c"}
    with pytest.raises(ValidationError):
        validate(v, s)

def test_episode_card_schema(tmp_path):
    s = json.loads((SCHEMAS / "episode-card.schema.json").read_text(encoding="utf-8"))
    card = {"episode_id": "ep01", "slug": "ep01-memory", "topic": "显存是主角",
            "cross_chapter_threads": [{"chapter_id": "ch15", "mechanism": "KV cache"}],
            "key_mechanisms": ["PagedAttention"], "voices_refs": ["v1"],
            "narrative_anchors": [{"chapter_id": "ch15", "section": "15.2 分页 KV 缓存"}]}
    validate(card, s)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_schemas.py -v`（先 `pip install jsonschema`）
Expected: FAIL（schemas/ 空）

- [ ] **Step 3: 写 9 个 schema**（关键 3 个给全量，其余 6 个按同风格）

```json
// schemas/voices.schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "additionalProperties": false,
  "patternProperties": {"^voice-": {
    "type": "object",
    "required": ["id", "category", "term", "claim", "verified", "source_url",
                 "source_date", "source_platform", "speaker_handle", "anonymized",
                 "confidence", "writer_note"],
    "properties": {
      "id": {"type": "string"},
      "category": {"enum": ["critical", "job-seeker"]},
      "term": {"type": "string"},
      "claim": {"type": "string"},
      "verified": {"enum": ["official", "claim-self-checked", "community-only"]},
      "source_url": {"type": "string", "minLength": 8},
      "source_date": {"type": "string", "pattern": "^20\\d\\d-\\d\\d-\\d\\d$"},
      "source_platform": {"enum": ["zhihu", "v2ex", "niuke", "maimai", "xhs", "bili",
                                   "jike", "reddit", "hn", "x", "blind", "linkedin",
                                   "official", "paper", "github-issue"]},
      "speaker_handle": {"type": "string"},
      "anonymized": {"type": "boolean"},
      "confidence": {"enum": ["high", "medium", "low"]},
      "writer_note": {"type": "string"}
    }
  }}
}
```

```json
// schemas/episode-card.schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["episode_id", "slug", "topic", "cross_chapter_threads",
               "key_mechanisms", "voices_refs", "narrative_anchors"],
  "properties": {
    "episode_id": {"type": "string"},
    "slug": {"type": "string"},
    "topic": {"type": "string"},
    "cross_chapter_threads": {"type": "array", "items": {
      "type": "object", "required": ["chapter_id", "mechanism"],
      "properties": {"chapter_id": {"type": "string"}, "mechanism": {"type": "string"}}}},
    "key_mechanisms": {"type": "array", "items": {"type": "string"}},
    "voices_refs": {"type": "array", "items": {"type": "string"}},
    "narrative_anchors": {"type": "array", "items": {
      "type": "object", "required": ["chapter_id", "section"],
      "properties": {"chapter_id": {"type": "string"}, "section": {"type": "string"}}}}
  }
}
```

```json
// schemas/script.schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["title", "turns"],
  "properties": {
    "title": {"type": "string"},
    "turns": {"type": "array", "items": {
      "type": "object", "required": ["speaker", "text"],
      "properties": {
        "speaker": {"enum": ["S1", "S2"]},
        "text": {"type": "string"},
        "voice_refs": {"type": "array", "items": {"type": "string"}},
        "pause_ms": {"type": "integer", "minimum": 0}
      }}}
  }
}
```

```json
// schemas/season-plan.schema.json（其余 6 个同风格）
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["show", "episodes"],
  "properties": {
    "show": {"type": "string"},
    "episodes": {"type": "array", "items": {
      "type": "object",
      "required": ["episode_id", "slug", "topic", "hook", "depends_on", "foreshadow_due"],
      "properties": {
        "episode_id": {"type": "string"},
        "slug": {"type": "string"},
        "topic": {"type": "string"},
        "hook": {"type": "string"},
        "depends_on": {"type": "array", "items": {"type": "string"}},
        "foreshadow_due": {"type": "array", "items": {"type": "string"}},
        "payoff_due": {"type": "array", "items": {"type": "string"}}
      }}}
  }
}
```

（`arc.schema.json` / `production-notes.schema.json` / `audio-qa.schema.json` / `season-bible.schema.json` / `book.schema.json`：按同样 draft-07 风格定义，字段与 Task 4/10/11 的 dataclass、Task 13 的 agent 契约对齐——arc 含 opening/closing/controversy/foreshadow_map；production-notes 每条含 ep_dir+script_line+note+severity；audio-qa 对齐 AudioQAReport 字段；season-bible 含 glossary/voice-guide/arc-map/voices-index；book 含 title/chapters。）

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_schemas.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add schemas/ tests/test_schemas.py
git commit -m "feat: 9 个产物契约 schema（voices/episode-card/script/season-plan 等）"
```

---

### Task 13: new_show.py — 节目 scaffold

**Files:**
- Create: `scripts/new_show.py`
- Test: `tests/test_new_show.py`

**Interfaces:**
- Produces: `scaffold_show(root: Path, name: str, title: str, book_root: str, instance: str) -> Path`（建 `shows/<name>/` 全套目录 + devpodcast.json + SHOW.md 模板 + season/bible 空档 + voice-samples/ + trace/ + episodes/，返回节目目录）
- 顶层注册表自动登记新节目并设为 active

- [ ] **Step 1: 写失败测试**

```python
# tests/test_new_show.py
import json
from pathlib import Path
import pytest
from scripts.new_show import scaffold_show
from scripts.show_resolver import resolve_show

def test_scaffold_creates_structure(tmp_path):
    show_dir = scaffold_show(tmp_path, "demo", "演示节目", "/mnt/fake/repo", "vllm")
    assert (show_dir / "devpodcast.json").is_file()
    assert (show_dir / "SHOW.md").is_file()
    assert (show_dir / "season" / "bible" / "voice-guide.md").is_file()
    assert (show_dir / "trace").is_dir()
    assert (show_dir / "episodes").is_dir()
    assert (show_dir / "voice-samples").is_dir()

def test_scaffold_registers_and_activates(tmp_path):
    scaffold_show(tmp_path, "demo", "演示", "/mnt/fake/repo", "vllm")
    reg = json.loads((tmp_path / "devpodcast.json").read_text(encoding="utf-8"))
    assert reg["active_show"] == "demo"
    assert "demo" in reg["shows"]
    assert resolve_show(tmp_path).name == "demo"

def test_config_embeds_book_source(tmp_path):
    show_dir = scaffold_show(tmp_path, "demo", "演示", "/mnt/fake/repo", "vllm")
    cfg = json.loads((show_dir / "devpodcast.json").read_text(encoding="utf-8"))
    assert cfg["book_source"]["root"] == "/mnt/fake/repo"
    assert cfg["book_source"]["instance"] == "vllm"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_new_show.py -v`
Expected: FAIL

- [ ] **Step 3: 写实现**

```python
# scripts/new_show.py
"""新建一档节目：scaffold 目录 + 配置文件 + 顶层注册。"""
import json
import sys
from pathlib import Path

VOICE_GUIDE_TEMPLATE = """# voice-guide.md — 声线人格定义（Lead 落笔）

> 本文件是节目灵魂。writer 强制复用；修改需 Lead 批准。

## 说话人
- **S1（老张）——主持人**：读过书但不装懂；替听众问笨问题；爱用生活类比；
  没听懂就明说；主动挑事；禁止假装惊叹、禁止捧哏。
- **S2（阿凯）——嘉宾/技术侧**：真读过源码但知道边界；长句自我打断成短句；
  数字先给量级；不护短；禁止背书、禁止说「这个很简单」。

## 三条内容纪律
1. 每期至少一次「我不知道」——答不上来就明说，反 AI 播客的最强信号。
2. 批判必须有靶子——谁在什么场景踩了什么坑，或牺牲了什么换了什么。
3. 生活场景必须承重——删掉类比听众就答不出「为什么」时，类比才保留。

## 求职者视角
融进 S1 的提问，每期至多两处，必须挂真实 voices 条目，不许凭空说「面试会考」。
"""

SHOW_MD_TEMPLATE = """# SHOW.md — {name} 当前状态

## 书源
- kind: {book_kind}
- root: {book_root}
- instance: {instance}
- 状态: 未摄入（跑 `python3 scripts/ingest_book.py --show {name} --root {book_root} --instance {instance}`）

## 硬规则
- voices 有 3 个月保质期（面经半年就过时），到期刷新。
- TTS 是必经站：环境没配好 = BLOCKED，无降级路径。
- 修改 voice-guide.md 需 Lead 批准。
"""


def scaffold_show(root: Path, name: str, title: str, book_root: str, instance: str) -> Path:
    root = Path(root)
    show_dir = root / "shows" / name
    for sub in ["season/bible", "trace", "voice-samples", "episodes"]:
        (show_dir / sub).mkdir(parents=True, exist_ok=True)

    cfg = {
        "show": name,
        "title": title,
        "book_source": {"kind": "repo2book", "root": book_root, "instance": instance,
                        "ingested_at": "", "snapshot_digest": ""},
        "audience": {"profile": "对 LLM 推理有兴趣的工程师 + 正在准备相关面试的求职者",
                     "assumed_knowledge": ["Python", "Transformer 基本概念"], "language": "zh-CN"},
        "format": {"hosts": 2, "target_minutes": 35, "episodes_planned": None},
        "tts": {"provider": "moss-ttsd", "fallback": "cosyvoice3",
                "voice_map": {"S1": "voice-samples/laozhang.wav", "S2": "voice-samples/akai.wav"}},
    }
    (show_dir / "devpodcast.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    (show_dir / "SHOW.md").write_text(
        SHOW_MD_TEMPLATE.format(name=name, book_kind="repo2book", book_root=book_root, instance=instance),
        encoding="utf-8")
    (show_dir / "season" / "bible" / "voice-guide.md").write_text(VOICE_GUIDE_TEMPLATE, encoding="utf-8")

    reg_path = root / "devpodcast.json"
    reg = json.loads(reg_path.read_text(encoding="utf-8"))
    reg["active_show"] = name
    reg["shows"][name] = {"config": f"shows/{name}/devpodcast.json", "title": title}
    reg_path.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")
    return show_dir


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    root = Path(argv[0])
    name, title, book_root, instance = argv[1], argv[2], argv[3], argv[4]
    scaffold_show(root, name, title, book_root, instance)
    print(f"scaffolded shows/{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_new_show.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/new_show.py tests/test_new_show.py
git commit -m "feat: new_show 节目 scaffold（voice-guide 模板落笔）"
```

---

### Task 14: 8 个 agent 提示词

**Files:**
- Create: `.claude/agents/planner.md`、`.claude/agents/book-analyst.md`、`.claude/agents/researcher.md`、`.claude/agents/hook-engineer.md`、`.claude/agents/writer.md`、`.claude/agents/producer.md`、`.claude/agents/reviewer.md`、`.claude/agents/archivist.md`

**Interfaces:**
- 每个提示词 = 持久角色契约。workflow（Task 15）经 `agentType` 调用；产物契约对齐 §2.4 schema。
- 本任务无 pytest（提示词文件）；验收 = 每个文件存在 + 关键契约点齐全（人工/评审核对）。

- [ ] **Step 1: 写 planner.md**

关键内容：输入 `source-book/` 快照 + 书大纲；输出 `season/season-plan.json`（议题 N 期 + 顺序 + 依赖 + 钩子 + 伏笔）；触发条件：素材不足以支撑议题驱动 → BLOCKED；不按章节一一对应，**跨章抽线**（如「内存是主角」抽 ch15/16/25）。

- [ ] **Step 2: 写 book-analyst.md**

关键内容：输入 `season-plan.json` 的议题定义 + `source-book/chapter-cards/*.json`；输出 `episodes/epNN-*/episode-card.json`（topic / cross_chapter_threads / key_mechanisms / voices_refs）；要点源优先级：sections（narrative 小节）> key_classes > mechanisms；议题在书里找不到支撑 → BLOCKED。

- [ ] **Step 3: 写 researcher.md**

关键内容：输出 `season/voices.json`；字段纪律照 spec §6.2/§6.4（url/date/平台/confidence/anonymized/category/writer_note）；源类 = 批判源 + 求职者源（国内外社交平台清单见 spec §6.1）；四类取材角度；取证纪律（评论≠事实 / 匿名化 / 平台偏差 / 时效）；查不到 → BLOCKED 或 low confidence 标注，**不许编**。

- [ ] **Step 4: 写 hook-engineer.md**

关键内容：输入 season-plan 议题；输出 `season/arc.json`（每期开场钩子 / 收尾金句 / 争议框架 / 伏笔映射）；钩子标准：一句生活化或反直觉的话让听众想继续听；收尾标准：不总结，给悬念或行动。

- [ ] **Step 5: 写 writer.md**

关键内容：**唯一有权写 script.md**；输入 episode-card + voices + arc + Season Bible（voice-guide 强制复用）；script.md 格式契约（Task 4：`[S1]`/`[S2]` 成对、`{{voice:}}` 引用、`<break Nms>`）；voice-guide 三条纪律 + 求职者配额（每期至多两处、必须挂真实 voices 条目）；**原声引述三档策略**（spec §6.4：a 按原说话人音色重合成=默认 / b 真实音频片段=需授权 / c 只标引述由 S1/S2 转述；三档都须在脚本里显式标注引述边界）；零脚手架泄漏；producer 意见逐条采纳或带理由反驳（receiving-code-review skill）；收工自检跑 lint_script（BLOCKING 清零）。

- [ ] **Step 6: 写 producer.md**

关键内容：**只写 production-notes.md 不改稿**；每条带 script 行号；看什么 = 口播换气（单段>200字）/ 双声线节奏（连续短句平了）/ 引述前停顿 / 时长预算；两类 provider 的停顿语义分支（对话模型=改文本节奏引导、分段模型=插静音毫秒）；与 reviewer 分工：producer 看"口播感"，reviewer 看"内容质量"。

- [ ] **Step 7: 写 reviewer.md**

关键内容：6 维并行（事实准确 / 批判强度 / 口播可懂 / 双声线平衡 / 求职者共鸣 / 原声保真）；输出 `reviews/*.json`；有界回环 ≤3 轮；review-exhausted → BLOCKED 升级；评审无权因风格偏好退稿（writer 说了算怎么写）。

- [ ] **Step 8: 写 archivist.md**

关键内容：归档 + 回写 Season Bible（glossary 口播译名 / arc-map 伏笔回写 / voices-index 引用台账）；trace 长期记忆（scripts/archivist.py）；跨期连贯性：每完成一期核对 arc-map。

- [ ] **Step 9: 提交**

```bash
git add .claude/agents/
git commit -m "feat: 8 个持久角色提示词（spec §4/§5/§6 落地）"
```

---

### Task 15: 两个 workflow 骨架

**Files:**
- Create: `.claude/workflows/season-pipeline.js`
- Create: `.claude/workflows/episode-pipeline.js`

**Interfaces:**
- 结构完全照 repo2book 的 `chapter-pipeline.js` 模式（meta+phases / args 解析 / STATUS_SCHEMA / 逃生舱 / head() 注入角色契约）——**自写实现，不复制粘贴**。
- season-pipeline 阶段：`Plan → Research → Hooks → Slice → Bible`（planner / researcher / hook-engineer / book-analyst×N 并行 / archivist）
- episode-pipeline 阶段：`Write → Produce → Revise → TTS → AudioQA → Review → Archive`（writer / producer / writer / tts-engine / audio-qa / reviewer / archivist）
- **args 契约**（对齐 Task 18/19 发车调用）：
  - season-pipeline: `{show: string, episodes: number}`（episodes 为议题数，planner 自行定议题）
  - episode-pipeline: `{show: string, ep_id: string, target_minutes: number}`
- 每个阶段完成后跑对应确定性 linter（Task 7/8/9 的 CLI），BLOCKING 回环该阶段 ≤2 轮再升级。
- 本任务无 pytest；验收 = 文件存在 + `node --check` 语法通过 + meta.phases 与上述阶段一致。

- [ ] **Step 1: 写 season-pipeline.js**（完整结构，含公共件）

```js
export const meta = {
  name: 'season-pipeline',
  description: 'Phase A：整季编排——planner 抽议题 → researcher 查 voices → hook-engineer 出钩子 → book-analyst 按议题切片 → archivist 建 Bible',
  phases: [
    { title: 'Plan', detail: 'planner 通读书源快照，产出 season-plan.json（N 期议题/顺序/依赖/伏笔）' },
    { title: 'Research', detail: 'researcher 真上网查批判源+求职者源，产 voices.json' },
    { title: 'Hooks', detail: 'hook-engineer 每期开场钩子/收尾金句/争议框架，产 arc.json' },
    { title: 'Slice', detail: 'book-analyst×N 按议题跨章切片，每期产 episode-card.json' },
    { title: 'Bible', detail: 'archivist 建/更新 Season Bible + trace' },
  ],
}

// args 契约（与脚本内 CFG 同构，参考 repo2book 的 args 可靠解析模式）：
//   { show: "vllm-podcast", episodes: 5 }
// 逃生舱：任一站返回 { status: "BLOCKED", blocker_reason } → 立即中止升级 Lead。
// 公共件（两文件共享模式）：
//   STATUS_SCHEMA = { type: 'object', required: ['status', 'note'],
//                     properties: { status: { enum: ['OK','BLOCKED'] }, note: {...} } }
//   function head(role, showDir) → 注入角色契约路径 + 产物绝对路径 + 书源快照路径
//   每个 agent 调用的 prompt 均含：角色契约路径、本期输入产物路径、输出产物路径、逃生舱文案
// Plan 阶段：planner 产出 season/season-plan.json（episodes 数组，每项按 season-plan.schema）
// Research 阶段：researcher 产出 season/voices.json（跑 lint_voices 无 BLOCKING）
// Hooks 阶段：hook-engineer 产出 season/arc.json
// Slice 阶段：book-analyst × episodes 并行，每个产出 episodes/<slug>/episode-card.json
// Bible 阶段：archivist 产出 season/bible/* + trace 记录
// 写完后：node --check
```

- [ ] **Step 2: 写 episode-pipeline.js**（完整结构，含公共件）

```js
export const meta = {
  name: 'episode-pipeline',
  description: 'Phase B：单期制作——writer 主笔 → producer 提意见 → writer 定稿 → TTS 合成 → audio-qa 质检 → reviewer 6 维评审 → archivist 归档',
  phases: [
    { title: 'Write', detail: 'writer 以 episode-card+voices+arc+Bible 为源写 script.md（唯一有权写）' },
    { title: 'Produce', detail: 'producer 出 production-notes.md（只建议，带行号）' },
    { title: 'Revise', detail: 'writer 逐条采纳/反驳 producer 意见，定稿' },
    { title: 'TTS', detail: 'tts-engine 本地 GPU 合成 episode.wav + segments/' },
    { title: 'AudioQA', detail: 'audio-qa 试听质检（时长/削波/静音/响度），有界回环 ≤2' },
    { title: 'Review', detail: 'reviewer 6 维并行评审，有界回环 ≤3' },
    { title: 'Archive', detail: 'archivist 归档 + 回写 Bible' },
  ],
}

// args 契约：{ show: "vllm-podcast", ep_id: "ep01", target_minutes: 35 }
// Write 阶段后跑 lint_script/lint_punct/lint_anchors/lint_trace，BLOCKING 回环 writer ≤2 轮
// TTS 阶段：DialogueTTSProvider.synthesize（script → [S1]/[S2] 标签串 → episode.wav）
// AudioQA 阶段：audio_qa.py，BLOCKING 回环 tts-engine（重合成）或 writer（改稿）≤2 轮
// Review 阶段：reviewer 6 维并行（spec §12.3），BLOCKING 回环 writer ≤3 轮，超限 review-exhausted
// Archive 阶段：archivist 归档 + season_bible.register 回写 arc-map + shownotes.md
// 写完后：node --check
```

- [ ] **Step 3: 语法检查**

Run: `node --check .claude/workflows/season-pipeline.js && node --check .claude/workflows/episode-pipeline.js`
Expected: 无输出（语法通过）

- [ ] **Step 4: 提交**

```bash
git add .claude/workflows/
git commit -m "feat: season-pipeline / episode-pipeline 骨架"
```

---

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

**Files:**
- 环境产物（不入库）：`models/` 目录、venv 或 conda 环境
- Create: `shows/vllm-podcast/voice-samples/README.md`（音色样本说明）
- 无 pytest；验收 = 命令实际跑通。

**先决检查（务必先做）：**
- `nvidia-smi` 确认 GPU 空闲（有别的进程占了 3.9GB，若占用大先等/协调）
- torch 2.11.0+cu130 已装（本机核实）；MOSS 官方要求 cu128 系——**先验证 cu130 能否直接跑，不能则装 cu128 侧环境**

- [ ] **Step 1: 验证 GPU 链路（F5-TTS 试金石）**

```bash
# 独立 venv 装 F5-TTS（试金石专用，不进生产）
python3 -m venv .venv-f5
.venv-f5/bin/pip install f5-tts
.venv-f5/bin/f5-tts_infer-cli --model F5TTS_v1_Base --ref_audio <voice-sample.wav> \
  --ref_text "<样本文本>" --gen_text "这是环境验证用的试金石句子。" --output_file /tmp/f5-test.wav
python3 -c "
import soundfile as sf
x, sr = sf.read('/tmp/f5-test.wav')
print(f'OK: {len(x)/sr:.1f}s @ {sr}Hz')
"
```

Expected: 输出 `OK: ~2s @ 24000Hz`——GPU/torch/flash-attn 链路打通。

- [ ] **Step 2: 安装 MOSS-TTSD（默认 provider）**

```bash
# 按官方 README（OpenMOSS/MOSS-TTSD）：
# 1. conda 环境 + requirements.txt + flash-attn
# 2. SGLang 从 moss-ttsd-v1.0-with-cat 分支源码安装
# 3. python scripts/fuse_moss_tts_delay_with_codec.py 融合模型与 codec
# 4. 下载 HF 权重 OpenMOSS-Team/MOSS-TTSD-v1.0 到 models/moss-ttsd/
# 若 sm_120 编译失败：参照 F5-TTS Discussion #1095 配方装 torch 2.9.0+cu128 系
```

- [ ] **Step 3: 样例合成**

```bash
# voice_clone_and_continuation 模式，S1/S2 各给一段 prompt 音频（5-10s）
python3 scripts/demo_moss.py \
  --model models/moss-ttsd \
  --text "[S1] 大家好，这期我们聊聊 vLLM 的显存问题。[S2] 嗯，这个话题面试也常考。[S1] 那我们就从 KV cache 说起。" \
  --output /tmp/demo-dialogue.wav \
  --ref S1:voice-samples/laozhang.wav --ref S2:voice-samples/akai.wav
```

Expected: 生成双人对话音频，可人工试听；时长 ≈ 文本字数/4 秒；vram_report 显示占用 < 20GB。

- [ ] **Step 4: 写 voice-samples/README.md**

```markdown
# voice-samples/

S1（老张）与 S2（阿凯）的音色 prompt 音频（5-10s，清晰单人录音，末留 1s 静音）。

来源与授权说明写在这里。**音色样本本身不入库**（.gitignore 已排除）。
```

- [ ] **Step 5: 提交（只有 README 与配置，模型/音频不入库）**

```bash
git add shows/vllm-podcast/voice-samples/README.md
git commit -m "env: M0 GPU 链路验证 + MOSS-TTSD 样例合成通过"
```

---

### Task 18: M1 素材 — scaffold 节目 + 摄入 vllm 书 + Phase A

**Files:**
- Create（数据产物）：`shows/vllm-podcast/`（scaffold）、`source-book/`（摄入）、`season/season-plan.json`、`season/voices.json`、`season/arc.json`、`season/bible/`、若干 `episodes/epNN-*/episode-card.json`
- Modify: `devpodcast.json`（active_show 指向 vllm-podcast，new_show 已自动做）
- 无 pytest；验收 = 各产物存在 + schema 校验 + lint_voices 无 BLOCKING

- [ ] **Step 1: scaffold 节目**

```bash
python3 scripts/new_show.py . vllm-podcast "把 vLLM 拆开讲" /mnt/e/Laboratory/Repo2Book vllm
```

Expected: `scaffolded shows/vllm-podcast`

- [ ] **Step 2: Lead 落笔 voice-guide.md（spec §5 硬要求，Phase A 前必做）**

Lead（主 session）编辑 `shows/vllm-podcast/season/bible/voice-guide.md`：把 scaffold 模板升级为最终版——敲定两个说话人的最终命名与人格细节（默认 S1=老张/主持人、S2=阿凯/技术侧）、三条内容纪律的判据示例、求职者视角的落地配额。此文件此后为 writer 强制复用的真相源，改动需 Lead 批准。

- [ ] **Step 3: 摄入书源**

```bash
# ingest_book.py 需支持 --show 参数；先按 Task 3 的 ingest(source, show_dir) 实现 CLI：
#   python3 scripts/ingest_book.py --show vllm-podcast --root /mnt/e/Laboratory/Repo2Book --instance vllm
python3 -c "
from scripts.book_source import Repo2BookSource
from scripts.ingest_book import ingest
from scripts.show_resolver import resolve_show
src = Repo2BookSource('/mnt/e/Laboratory/Repo2Book', 'vllm')
print(ingest(src, resolve_show()))
"
```

Expected: `{'digest': 'sha256:...', 'chapters': 39, 'ingested_at': ''}`；`source-book/chapter-cards/ch01.json` 等 39 个文件存在。

- [ ] **Step 4: 运行 Phase A（season-pipeline workflow）**

```bash
# 主 session 发车（你 = Team Lead）：
Workflow({ name: "season-pipeline", args: { show: "vllm-podcast", episodes: 5 } })
```

流程：planner 抽 5 个议题（跨章抽线，如：①显存是主角（ch15/16/25）②调度是排队还是取舍（ch13/14）③投机解码值不值得（ch33/34）④结构化输出的工程化（ch31/32）⑤PD 分离的账（ch35/36））→ researcher 真查 voices（批判源 + 求职者源，含平台）→ hook-engineer 每期钩子 → book-analyst×5 并行切片 → archivist 建 Bible。

- [ ] **Step 5: 校验产物**

```bash
python3 scripts/lint_voices.py shows/vllm-podcast/season/voices.json   # 期望无 BLOCKING
python3 -c "
import json
sp = json.load(open('shows/vllm-podcast/season/season-plan.json'))
assert len(sp['episodes']) == 5, '一期一个议题'
for e in sp['episodes']:
    assert e['slug'].startswith('ep'), e
print('season-plan OK:', [e['slug'] for e in sp['episodes']])
"
```

Expected: voices 无 BLOCKING；season-plan 5 期通过断言。

- [ ] **Step 6: 提交（只提交素材，不提交音色样本）**

```bash
git add shows/vllm-podcast/
git commit -m "feat: vllm-podcast 节目 scaffold + 书源快照 + Phase A 素材（season-plan/voices/arc/episode-cards）"
```

---

### Task 19: M1 制作 — 第一期（ep01）走通 Phase B

**Files:**
- Create: `shows/vllm-podcast/episodes/ep01-*/script.md`（writer 产出）、`production-notes.md`、`audio/episode.wav`、`audio/audio-qa.json`、`shownotes.md`、`reviews/run-ledger.json`
- 无 pytest；验收 = Phase B 全链路产物存在 + linter 全绿 + 人工试听三问

- [ ] **Step 1: 运行 Phase B（episode-pipeline workflow）**

```bash
Workflow({ name: "episode-pipeline", args: { show: "vllm-podcast", ep_id: "ep01", target_minutes: 35 } })
```

流程：writer（吃 ep01 episode-card + voices + arc + Bible）→ producer（production-notes.md）→ writer 定稿 → tts-engine（MOSS-TTSD，S1/S2 音色）→ audio-qa（时长/削波/静音/响度）→ reviewer 6 维 → archivist 归档。

- [ ] **Step 2: 跑全部 linter**

```bash
python3 scripts/lint_script.py shows/vllm-podcast/episodes/ep01-*/script.md \
  --voices shows/vllm-podcast/season/voices.json --target-minutes 35
python3 scripts/lint_punct.py shows/vllm-podcast/episodes/ep01-*/script.md
python3 scripts/lint_anchors.py shows/vllm-podcast/episodes/ep01-*/script.md
python3 scripts/lint_trace.py shows/vllm-podcast/episodes/ep01-*/script.md \
  shows/vllm-podcast/season/voices.json
python3 scripts/audio_qa.py shows/vllm-podcast/episodes/ep01-*/audio/episode.wav \
  shows/vllm-podcast/episodes/ep01-*/audio/audio-qa.json 35
```

Expected: lint_script 无 BLOCKING（WARN 可接受）；lint_punct 纯 WARN；lint_anchors 无 BLOCKING；lint_trace 无 BLOCKING；audio_qa 无 BLOCKING。

- [ ] **Step 3: 人工试听三问**

自己完整听一遍 ep01 音频，对三问做判定并记入 run-ledger.json：

| 问 | 判定标准 |
|---|---|
| 听得懂吗？ | 不看脚本能跟上全部主线；术语首现有口头解释 |
| 有意思吗？ | 批判和生活场景真的落地了；有至少一处"我想继续听" |
| 两个人像人吗？ | 不是两个 TTS 在轮流念稿；有接话、有停顿、有"我不知道" |

**任一否 → M1 未过**：升级 Lead 定位问题（writer 提示词 / voice-guide / producer 停顿 / TTS 参数），修后重跑 Phase B（改提示词不改脚本，除非事实错误）。

- [ ] **Step 4: 记录归档**

```bash
python3 scripts/archivist.py shows/vllm-podcast/trace log "M1 ep01 试听判定：三问（听懂了/有意思/像人）结果 = <记录>"
```

- [ ] **Step 5: 提交**

```bash
git add shows/vllm-podcast/episodes/
git commit -m "feat: M1 ep01 一期走通（脚本/音频/质检/评审归档）"
```

---

## 执行顺序与依赖

```
Task 1  ← 2 ← 3 ──────────────────────┐
        ← 4 ← 5 ← 6 ← 7 ← 8 ← 9 ← 10 ├→ 11 ← 12 ← 13 ──────────┐
                                      │                          │
        Task 14（agents）← 15（workflow）← 16（文档）←────────────┤
        Task 17（环境，可与 1–16 并行——GPU 安装不依赖代码）←──────┤
        Task 18（M1 素材 + Phase A）←─────────────────────────────┤
        Task 19（M1 制作 + 人工试听）←────────────────────────────┘
```

- Task 1–13 是纯代码（含 schemas，按依赖链推进）
- Task 14–16 是提示词/文档/workflow（依赖代码任务完成后的接口知识）
- Task 17 是环境（可与 1–16 并行跑——GPU 安装不依赖代码）
- Task 18 依赖 2/3/13/14/15/17；Task 19 依赖 18 + 4/5/7/9/10/15/17

**建议执行节奏**：代码任务（1–13）按序一次做完（TDD 每步提交）→ 环境任务 17 与 14–16 并行 → 18 → 19。每个 Task 结束后由执行者（或子代理）跑该任务的 pytest，全绿才进下一个。

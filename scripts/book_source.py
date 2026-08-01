"""BookSource 抽象 + Repo2BookSource 实现（读 repo2book 实例目录，归一化成本项目 Book）。

要点抽取策略（2026-08-01 实测核实）：
- sections 主来源 = narrative 的 "## N.M 标题" 小节行（39/39 章稳定存在）
- key_classes = dossier.json（39/39 章存在）
- mechanisms = dossier.json（仅 8/39 章有 v3 账本，可能为空数组，容忍）
"""
import json, re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

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


@runtime_checkable
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

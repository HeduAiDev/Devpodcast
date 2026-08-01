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

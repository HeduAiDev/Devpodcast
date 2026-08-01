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

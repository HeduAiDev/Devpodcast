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

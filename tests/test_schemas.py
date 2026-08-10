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

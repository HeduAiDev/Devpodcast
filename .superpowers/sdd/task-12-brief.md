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

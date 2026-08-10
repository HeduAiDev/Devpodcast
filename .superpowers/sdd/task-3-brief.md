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

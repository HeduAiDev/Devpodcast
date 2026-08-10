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

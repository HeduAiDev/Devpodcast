# scripts/archivist.py
"""archivist 数据层：trace 长期记忆（JSONL 追加）。"""
import datetime
import json
import sys
from pathlib import Path

USAGE = "usage: archivist.py <trace_dir> [status|log <msg> [kind]]"


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
    if not argv:
        print(USAGE, file=sys.stderr)
        return 2
    trace_dir = Path(argv[0])
    cmd = argv[1] if len(argv) > 1 else "status"
    if cmd == "status":
        entries = read_entries(trace_dir)
        print(f"{len(entries)} entries")
        for e in entries[-10:]:
            print(f"[{e['at']}] ({e['kind']}) {e['msg']}")
    elif cmd == "log":
        if len(argv) < 3:
            print(USAGE, file=sys.stderr)
            return 2
        log_entry(trace_dir, argv[2], argv[3] if len(argv) > 3 else "note")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

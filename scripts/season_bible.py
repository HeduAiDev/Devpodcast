# scripts/season_bible.py
"""Season Bible CLI：伏笔 due/回收登记（spec §4 archivist 职责的跨期部分）。"""
import json
import sys
from pathlib import Path

USAGE = (
    "usage: season_bible.py due <arc-map.json> <ep_id>\n"
    "       season_bible.py register <arc-map.json> <ep_id> <fields-json>"
)


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
    if len(argv) < 3:
        print(USAGE, file=sys.stderr)
        return 2
    cmd, arc_map, ep = argv[0], Path(argv[1]), argv[2]
    if cmd == "due":
        for item in due(arc_map, ep):
            print(item)
        return 0
    if cmd == "register":
        if len(argv) < 4:
            print(USAGE, file=sys.stderr)
            return 2
        try:
            fields = json.loads(argv[3])
        except json.JSONDecodeError as exc:
            print(f"season_bible.py register: 非法 JSON: {exc}", file=sys.stderr)
            return 2
        if not isinstance(fields, dict):
            print("season_bible.py register: fields 必须是 JSON 对象", file=sys.stderr)
            return 2
        register(arc_map, ep, fields)
        return 0
    print(f"season_bible.py: 未知命令 {cmd!r}", file=sys.stderr)
    print(USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

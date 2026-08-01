"""溯源门禁：script 的 {{voice:<id>}} 必须在 voices 集合内（workflow 独立 CLI 用）。"""
import json
import re
import sys
from pathlib import Path

# 以 `python3 scripts/lint_trace.py ...` 直接运行时 sys.path[0] 是 scripts/，
# 需把仓库根目录加回 path（与 lint_script 同模式）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

REF_RE = re.compile(r"\{\{voice:([a-zA-Z0-9_-]+)\}\}")

USAGE = "usage: python3 scripts/lint_trace.py <ep_dir> <voices.json>"


def lint_trace(ep_dir: Path, voices: dict) -> list[dict]:
    issues: list[dict] = []
    script = Path(ep_dir) / "script.md"
    if not script.is_file():
        return issues
    text = script.read_text(encoding="utf-8")
    for ref in REF_RE.findall(text):
        if ref not in voices:
            issues.append({"level": "BLOCKING", "msg": f"引用了未知 voice id: {ref}"})
    return issues


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) < 2:
        print(USAGE, file=sys.stderr)
        return 2
    ep_dir = Path(argv[0])
    voices_path = Path(argv[1])
    voices = json.loads(voices_path.read_text(encoding="utf-8"))
    for i in lint_trace(ep_dir, voices):
        print(f"[{i['level']}] {i['msg']}")
    return 1 if any(i["level"] == "BLOCKING" for i in lint_trace(ep_dir, voices)) else 0


if __name__ == "__main__":
    raise SystemExit(main())

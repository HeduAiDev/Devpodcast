"""跨期锚点门禁：脚本里 `../episodes/epNN-xxx/` 链接目标必须存在。"""
import re
import sys
from pathlib import Path

# 以 `python3 scripts/lint_anchors.py ...` 直接运行时 sys.path[0] 是 scripts/，
# 需把仓库根目录加回 path（与 lint_script 同模式）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

LINK_RE = re.compile(r"\]\(\.\./\.\./episodes/([^/)]+)/")

USAGE = "usage: python3 scripts/lint_anchors.py <ep_dir> [<show_dir>]"


def lint_anchors(ep_dir: Path, show_dir: Path) -> list[dict]:
    issues: list[dict] = []
    script = Path(ep_dir) / "script.md"
    if not script.is_file():
        return issues
    text = script.read_text(encoding="utf-8")
    for slug in LINK_RE.findall(text):
        target = Path(show_dir) / "episodes" / slug / "script.md"
        if not target.is_file():
            issues.append({"level": "BLOCKING", "msg": f"跨期链接目标不存在: {slug}"})
    return issues


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(USAGE, file=sys.stderr)
        return 2
    ep_dir = Path(argv[0])
    show_dir = Path(argv[1]) if len(argv) > 1 else ep_dir.parent.parent
    for i in lint_anchors(ep_dir, show_dir):
        print(f"[{i['level']}] {i['msg']}")
    return 1 if any(i["level"] == "BLOCKING" for i in lint_anchors(ep_dir, show_dir)) else 0


if __name__ == "__main__":
    raise SystemExit(main())

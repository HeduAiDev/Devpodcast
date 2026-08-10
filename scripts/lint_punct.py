"""半角标点门禁：汉字之间的半角 ,.; 提示为 WARN（口播可读性；反引号代码段豁免）。"""
import re
import sys
from pathlib import Path

# 以 `python3 scripts/lint_punct.py ...` 直接运行时 sys.path[0] 是 scripts/，
# 需把仓库根目录加回 path（与 lint_script 同模式）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

CJK = r"一-鿿"
HALF = re.compile(rf"([{CJK}])[,.;]([{CJK}])")

USAGE = "usage: python3 scripts/lint_punct.py <file>"


def lint_punct(text: str) -> list[dict]:
    issues: list[dict] = []
    # 剥离反引号代码段后再查
    cleaned = re.sub(r"`[^`]*`", "", text)
    for m in HALF.finditer(cleaned):
        issues.append({"level": "WARN", "msg": f"汉字间半角标点: …{cleaned[max(0, m.start()-6):m.end()+6]}…（应全角）"})
    return issues


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(USAGE, file=sys.stderr)
        return 2
    text = Path(argv[0]).read_text(encoding="utf-8")
    for i in lint_punct(text):
        print(f"[{i['level']}] {i['msg']}")
    return 0  # 纯 WARN


if __name__ == "__main__":
    raise SystemExit(main())

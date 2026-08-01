"""脚本门禁：voices 引用存在性 / 双声线平衡 / 「我不知道」warn / 时长预算。"""
import json, re, sys
from pathlib import Path

# 以 `python3 scripts/lint_script.py ...` 直接运行时 sys.path[0] 是 scripts/，
# 需把仓库根目录加回 path 才能 import scripts.* 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.script_parser import parse
from scripts.voice_budget import budget_check, MAX_TURN_CHARS

UNKNOWN_WORDS = ("我不知道", "没搞清", "没想明白", "说不准")
MIN_SPEAKER_RATIO = 0.30


def lint_script(path: Path, voices: dict, target_minutes: float) -> list[dict]:
    issues: list[dict] = []
    script = parse(path)

    # 1. voices 引用存在性
    known = set(voices.keys())
    for i, t in enumerate(script.turns):
        for ref in t.voice_refs:
            if ref not in known:
                issues.append({"level": "BLOCKING", "msg": f"turn {i} 引用未知 voice id: {ref}"})

    # 2. 双声线平衡
    if script.turns:
        n = len(script.turns)
        s1 = sum(1 for t in script.turns if t.speaker == "S1")
        s2 = n - s1
        for sp, cnt in (("S1", s1), ("S2", s2)):
            if cnt / n < MIN_SPEAKER_RATIO:
                issues.append({"level": "WARN", "msg": f"{sp} 仅 {cnt}/{n} turn（{cnt/n:.0%}），低于 {MIN_SPEAKER_RATIO:.0%}——防捧哏"})

    # 3. 「我不知道」出现（warn，防语境误报）
    all_text = "".join(t.text for t in script.turns)
    if not any(w in all_text for w in UNKNOWN_WORDS):
        issues.append({"level": "WARN", "msg": "全脚本无「我不知道/没搞清」类表述——voice-guide 纪律 1 要求每期至少一次"})

    # 4. 时长/换气预算（budget_check 返回带前缀的字符串，转成统一 dict 结构）
    for s in budget_check(script, target_minutes):
        if s.startswith("BLOCKING"):
            issues.append({"level": "BLOCKING", "msg": s[len("BLOCKING: "):]})
        else:
            issues.append({"level": "WARN", "msg": s[len("WARN: "):] if s.startswith("WARN") else s})
    return issues


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    path = Path(argv[0])
    voices: dict = {}
    target = 35.0
    if "--voices" in argv:
        voices = json.loads(Path(argv[argv.index("--voices") + 1]).read_text(encoding="utf-8"))
    if "--target-minutes" in argv:
        target = float(argv[argv.index("--target-minutes") + 1])
    issues = lint_script(path, voices, target)
    for i in issues:
        print(f"[{i['level']}] {i['msg']}")
    return 1 if any(i["level"] == "BLOCKING" for i in issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())

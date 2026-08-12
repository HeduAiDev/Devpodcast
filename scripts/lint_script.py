"""脚本门禁：voices 引用存在性 / 双声线平衡 / 「我不知道」warn / 时长预算。"""
import json
import sys
from pathlib import Path

# 以 `python3 scripts/lint_script.py ...` 直接运行时 sys.path[0] 是 scripts/，
# 需把仓库根目录加回 path 才能 import scripts.* 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.script_parser import parse
from scripts.voice_budget import budget_check

UNKNOWN_WORDS = ("我不知道", "没搞清", "没想明白", "说不准")
MIN_SPEAKER_RATIO = 0.25  # 三人模式（S1/S2/S3）任一方 turn 占比不低于 25%（voice-guide 硬约束）

USAGE = "usage: python3 scripts/lint_script.py <path> [--voices <json>] [--target-minutes N]"


def lint_script(path: Path, voices: dict, target_minutes: float) -> list[dict]:
    issues: list[dict] = []
    script = parse(path)

    # 1. voices 引用存在性
    known = set(voices.keys())
    for i, t in enumerate(script.turns):
        for ref in t.voice_refs:
            if ref not in known:
                issues.append({"level": "BLOCKING", "msg": f"turn {i} 引用未知 voice id: {ref}"})

    # 2. 多声线平衡（三人模式：S1/S2/S3 任一 ≥ 25%）
    if script.turns:
        n = len(script.turns)
        from collections import Counter
        counts = Counter(t.speaker for t in script.turns)
        for sp, cnt in sorted(counts.items()):
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

    # 5. {{em}} 重读标记纪律（成对闭合已由 parser 兜底抛错）
    for i, t in enumerate(script.turns):
        if not t.em_terms:
            continue
        if len(t.em_terms) > 1:
            issues.append({"level": "WARN", "msg": f"turn {i} 用了 {len(t.em_terms)} 处 {{em}}——纪律：每 turn ≤1 处，重读只给最重要的词"})
        for term in t.em_terms:
            if len(term) > 15:
                issues.append({"level": "WARN", "msg": f"turn {i} {{em}} 包了 {len(term)} 字（{term[:10]}…）——纪律：包核心术语，不包整句"})
            if "<break" in term:
                issues.append({"level": "BLOCKING", "msg": f"turn {i} {{em}} 内含 <break>——标记不能跨停顿"})
    return issues


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(USAGE, file=sys.stderr)
        return 2
    path = Path(argv[0])
    voices: dict = {}
    target = 35.0
    if "--voices" in argv:
        i = argv.index("--voices")
        if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
            print(USAGE, file=sys.stderr)
            return 2
        voices = json.loads(Path(argv[i + 1]).read_text(encoding="utf-8"))
    if "--target-minutes" in argv:
        i = argv.index("--target-minutes")
        if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
            print(USAGE, file=sys.stderr)
            return 2
        try:
            target = float(argv[i + 1])
        except ValueError:
            print(f"error: --target-minutes 需要合法数值，得到 '{argv[i + 1]}'", file=sys.stderr)
            return 2
    issues = lint_script(path, voices, target)
    for i in issues:
        print(f"[{i['level']}] {i['msg']}")
    return 1 if any(i["level"] == "BLOCKING" for i in issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())

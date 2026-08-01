"""voices 门禁（spec §6.4 五条）：URL/日期必填 / 匿名化 / low-confidence 标注 /
多平台 / 求职者平台约束。"""
import sys
from collections import Counter
from pathlib import Path

# 以 `python3 scripts/lint_voices.py ...` 直接运行时 sys.path[0] 是 scripts/，
# 需把仓库根目录加回 path 才能 import scripts.* 包（与 lint_script 同模式）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

JOB_SEEKER_PLATFORMS = {"zhihu", "v2ex", "niuke", "maimai", "xhs", "bili", "jike",
                        "reddit", "hn", "x", "blind", "linkedin"}
OFFICIAL_PLATFORMS = {"official", "paper", "github-issue"}

USAGE = "usage: python3 scripts/lint_voices.py <voices.json>"


def lint_voices(voices: dict) -> list[dict]:
    issues: list[dict] = []
    for vid, v in voices.items():
        # ① URL/日期必填
        if not v.get("source_url"):
            issues.append({"level": "BLOCKING", "msg": f"{vid}: source_url 必填"})
        if not v.get("source_date"):
            issues.append({"level": "BLOCKING", "msg": f"{vid}: source_date 必填"})
        # ② 匿名化
        if not v.get("anonymized", True) and v.get("source_platform") not in OFFICIAL_PLATFORMS:
            issues.append({"level": "BLOCKING",
                           "msg": f"{vid}: anonymized=false 仅允许官方/作者/论文/issue 源（当前 {v.get('source_platform')}）"})
        # ③ low confidence 标注
        if v.get("confidence") == "low" and "未一手核实" not in v.get("writer_note", ""):
            issues.append({"level": "BLOCKING", "msg": f"{vid}: confidence=low 须 writer_note 标注「未一手核实」"})
        # ⑤ 求职者平台约束
        if v.get("category") == "job-seeker" and v.get("source_platform") not in JOB_SEEKER_PLATFORMS:
            issues.append({"level": "BLOCKING",
                           "msg": f"{vid}: job-seeker 条目须落在求职者平台集合内（当前 {v.get('source_platform')}）"})
    # ④ 单一来源 warn（按 term 聚合）
    by_term: dict[str, list[str]] = {}
    verified_official = {v["id"] for v in voices.values() if v.get("verified") == "official"}
    for vid, v in voices.items():
        by_term.setdefault(v.get("term", ""), []).append(v.get("source_platform", ""))
    for term, plats in by_term.items():
        if len(set(plats)) < 2 and all(vid not in verified_official for vid in voices if voices[vid].get("term") == term):
            issues.append({"level": "WARN", "msg": f"term「{term}」单一来源（{plats[0]}），建议 ≥2 平台或 verified=official"})
    return issues


def main(argv=None) -> int:
    import json
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(USAGE, file=sys.stderr)
        return 2
    voices = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    issues = lint_voices(voices)
    for i in issues:
        print(f"[{i['level']}] {i['msg']}")
    return 1 if any(i["level"] == "BLOCKING" for i in issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())

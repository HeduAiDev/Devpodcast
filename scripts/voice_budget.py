"""时长/节奏预算：中文默认 4 字/秒口播；单 turn 上限 200 字（口播换气）。"""
from scripts.script_parser import Script, Turn

DEFAULT_CPS = 4.0
MAX_TURN_CHARS = 200
TOLERANCE = 1.15  # 目标时长的 15% 余量


def estimate_duration(text: str, cps: float = DEFAULT_CPS) -> float:
    return len(text) / cps


def estimate_script_duration(script: Script) -> float:
    return sum(estimate_duration(t.text) for t in script.turns)


def budget_check(script: Script, target_minutes: float) -> list[str]:
    issues: list[str] = []
    total_s = estimate_script_duration(script)
    target_s = target_minutes * 60
    if total_s > target_s * TOLERANCE:
        issues.append(f"BLOCKING: 预计 {total_s:.0f}s 超过目标 {target_s:.0f}s 的 {TOLERANCE:.0%} 余量")
    for i, t in enumerate(script.turns):
        if len(t.text) > MAX_TURN_CHARS:
            issues.append(f"WARN: turn {i} ({t.speaker}) 长 {len(t.text)} 字，超过 {MAX_TURN_CHARS} 字换气上限")
    return issues

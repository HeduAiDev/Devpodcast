### Task 6: voice_budget.py — 时长/节奏预算

**Files:**
- Create: `scripts/voice_budget.py`
- Test: `tests/test_voice_budget.py`

**Interfaces:**
- Consumes: `Script`/`Turn`（Task 4）
- Produces:
  - `estimate_duration(text: str, cps: float = 4.0) -> float`（中文默认 4 字/秒 = 240 字/分钟；返回秒）
  - `estimate_script_duration(script: Script) -> float`
  - `budget_check(script: Script, target_minutes: float) -> list[str]`（超 15% 报 BLOCKING 级 issue；单 turn > 200 字报 issue）

- [ ] **Step 1: 写失败测试**

```python
# tests/test_voice_budget.py
import pytest
from scripts.voice_budget import estimate_duration, estimate_script_duration, budget_check
from scripts.script_parser import parse
from pathlib import Path

def test_estimate_duration_default_speed():
    # 80 字 @ 4字/秒 = 20 秒
    assert estimate_duration("x" * 80) == pytest.approx(20.0)

def test_estimate_duration_custom_speed():
    assert estimate_duration("x" * 80, cps=2.0) == pytest.approx(40.0)

def test_estimate_script_duration(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] " + "x" * 400 + " [/S1]\n", encoding="utf-8")
    s = parse(p)
    assert estimate_script_duration(s) == pytest.approx(100.0)

def test_budget_check_ok(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] " + "x" * 400 + " [/S1]\n", encoding="utf-8")
    assert budget_check(parse(p), target_minutes=2.0) == []

def test_budget_check_over(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] " + "x" * 400 + " [/S1]\n", encoding="utf-8")
    issues = budget_check(parse(p), target_minutes=1.0)  # 100s > 69s(1.15x)
    assert len(issues) >= 1

def test_budget_check_long_turn(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] " + "x" * 300 + " [/S1]\n", encoding="utf-8")
    issues = budget_check(parse(p), target_minutes=5.0)
    assert any("300" in i for i in issues)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_voice_budget.py -v`
Expected: FAIL

- [ ] **Step 3: 写实现**

```python
# scripts/voice_budget.py
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
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_voice_budget.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/voice_budget.py tests/test_voice_budget.py
git commit -m "feat: voice_budget 时长/换气预算"
```

---

### Task 7: lint_script.py — 脚本门禁

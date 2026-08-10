### Task 7: lint_script.py — 脚本门禁

**Files:**
- Create: `scripts/lint_script.py`
- Test: `tests/test_lint_script.py`

**Interfaces:**
- Consumes: `Script.parse`（Task 4）、`budget_check`（Task 6）、voices.json（外部输入）
- Produces: `lint_script(path, voices: dict, target_minutes: float) -> list[dict]`（每项 `{"level": "BLOCKING"|"WARN", "msg": str}`）；CLI 入口 `python3 scripts/lint_script.py <path> [--voices <voices.json>] [--target-minutes N]`，退出码 0=通过 / 1=有 BLOCKING。

检查项：
1. `{{voice:<id>}}` 引用必须在 voices dict 中存在（id 集合）
2. speaker 比例不一边倒：任意说话人 turn 数 < 总数 30% → WARN（防捧哏）
3. 至少一个"我不知道"类表述（`我不知道`/`没搞清`/`没想明白`/`说不准`）→ WARN 级提示（防语境误报，非阻断）
4. 预算检查（Task 6 结果合并）

- [ ] **Step 1: 写失败测试**

```python
# tests/test_lint_script.py
import json
from pathlib import Path
import pytest
from scripts.lint_script import lint_script

VOICES = {"voice-001": {"claim": "面试要口算"}, "voice-002": {"claim": "社区吐槽"}}

def test_voice_refs_must_exist(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] 这里 {{voice:voice-999}} 不存在 [/S1]\n", encoding="utf-8")
    issues = lint_script(p, VOICES, target_minutes=5)
    assert any("voice-999" in i["msg"] and i["level"] == "BLOCKING" for i in issues)

def test_voice_refs_valid_ok(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] 这里 {{voice:voice-001}} 存在 [/S1]\n", encoding="utf-8")
    issues = lint_script(p, VOICES, target_minutes=5)
    assert all("voice-999" not in i["msg"] for i in issues)

def test_unknown_word_warn(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] 开场 [/S1]\n[S2] 主体内容 [/S2]\n", encoding="utf-8")
    issues = lint_script(p, VOICES, target_minutes=5)
    assert any("我不知道" in i["msg"] and i["level"] == "WARN" for i in issues)

def test_unknown_word_present_no_warn(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] 这个我们也没搞清楚，评论区有懂的说说 [/S1]\n[S2] 回应 [/S2]\n", encoding="utf-8")
    issues = lint_script(p, VOICES, target_minutes=5)
    assert not any("我不知道" in i["msg"] for i in issues)

def test_bald_broadcast_warn(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] a [/S1]\n[S1] b [/S1]\n[S1] c [/S1]\n[S2] d [/S2]\n", encoding="utf-8")
    issues = lint_script(p, VOICES, target_minutes=5)
    assert any("30%" in i["msg"] and i["level"] == "WARN" for i in issues)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_lint_script.py -v`
Expected: FAIL

- [ ] **Step 3: 写实现**

```python
# scripts/lint_script.py
"""脚本门禁：voices 引用存在性 / 双声线平衡 / 「我不知道」warn / 时长预算。"""
import json, re, sys
from pathlib import Path
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

    # 4. 时长/换气预算
    issues.extend(budget_check(script, target_minutes))
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
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_lint_script.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/lint_script.py tests/test_lint_script.py
git commit -m "feat: lint_script 门禁（voices 引用/声线平衡/我不知道/预算）"
```

---

### Task 8: lint_voices.py — voices 门禁

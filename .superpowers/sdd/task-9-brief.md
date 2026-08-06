### Task 9: lint_punct / lint_anchors / lint_trace

**Files:**
- Create: `scripts/lint_punct.py`、`scripts/lint_anchors.py`、`scripts/lint_trace.py`
- Test: `tests/test_lint_punct.py`、`tests/test_lint_anchors.py`、`tests/test_lint_trace.py`

**Interfaces:**
- Produces:
  - `lint_punct(text: str) -> list[dict]`：中文全角语境里夹半角标点（`,.;` 夹在汉字之间）→ WARN（口播可读性）
  - `lint_anchors(ep_dir: Path, show_dir: Path) -> list[dict]`：`../epNN-xxx/` 跨期链接目标必须存在
  - `lint_trace(ep_dir: Path, voices: dict) -> list[dict]`：script 每个 `{{voice:<id>}}` 引用在 voices 中存在（与 lint_script 规则 1 重复——此为独立 CLI 供 workflow 使用，保持一致）

- [ ] **Step 1: 写失败测试**

```python
# tests/test_lint_punct.py
import pytest
from scripts.lint_punct import lint_punct

def test_halfwidth_between_cjk_warn():
    issues = lint_punct("这里用了半角,逗号")
    assert any("半角" in i["msg"] for i in issues)

def test_fullwidth_ok():
    issues = lint_punct("这里用了全角，逗号。")
    assert issues == []

def test_code_span_ignored():
    # 反引号内的半角标点不查（代码/术语）
    issues = lint_punct("看这里 `foo,bar` 结束")
    assert issues == []
```

```python
# tests/test_lint_anchors.py
import pytest
from scripts.lint_anchors import lint_anchors

def test_valid_link_ok(tmp_path):
    (tmp_path / "episodes" / "ep02-slug").mkdir(parents=True)
    (tmp_path / "episodes" / "ep01-slug" / "script.md").write_text(
        "[S1] 详见 [ep02](../../episodes/ep02-slug/script.md) [/S1]\n", encoding="utf-8")
    issues = lint_anchors(tmp_path / "episodes" / "ep01-slug", tmp_path)
    assert issues == []

def test_broken_link_blocking(tmp_path):
    (tmp_path / "episodes" / "ep01-slug").mkdir(parents=True)
    (tmp_path / "episodes" / "ep01-slug" / "script.md").write_text(
        "[S1] 详见 [ep02](../../episodes/ep02-ghost/script.md) [/S1]\n", encoding="utf-8")
    issues = lint_anchors(tmp_path / "episodes" / "ep01-slug", tmp_path)
    assert any("ep02-ghost" in i["msg"] and i["level"] == "BLOCKING" for i in issues)
```

```python
# tests/test_lint_trace.py
import pytest
from scripts.lint_trace import lint_trace
from pathlib import Path

VOICES = {"voice-001": {"claim": "面试要口算"}}

def test_ref_traceable(tmp_path):
    ep = tmp_path / "ep01"
    ep.mkdir()
    (ep / "script.md").write_text("[S1] {{voice:voice-001}} [/S1]\n", encoding="utf-8")
    issues = lint_trace(ep, VOICES)
    assert issues == []

def test_ref_missing_blocking(tmp_path):
    ep = tmp_path / "ep01"
    ep.mkdir()
    (ep / "script.md").write_text("[S1] {{voice:voice-999}} [/S1]\n", encoding="utf-8")
    issues = lint_trace(ep, VOICES)
    assert any("voice-999" in i["msg"] for i in issues)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_lint_punct.py tests/test_lint_anchors.py tests/test_lint_trace.py -v`
Expected: FAIL

- [ ] **Step 3: 写实现**

```python
# scripts/lint_punct.py
"""半角标点门禁：汉字之间的半角 ,.; 提示为 WARN（口播可读性；反引号代码段豁免）。"""
import re
import sys

CJK = r"一-鿿"
HALF = re.compile(rf"([{CJK}])[,.;]([{CJK}])")


def lint_punct(text: str) -> list[dict]:
    issues: list[dict] = []
    # 剥离反引号代码段后再查
    cleaned = re.sub(r"`[^`]*`", "", text)
    for m in HALF.finditer(cleaned):
        issues.append({"level": "WARN", "msg": f"汉字间半角标点: …{cleaned[max(0, m.start()-6):m.end()+6]}…（应全角）"})
    return issues


def main(argv=None) -> int:
    from pathlib import Path
    argv = argv if argv is not None else sys.argv[1:]
    text = Path(argv[0]).read_text(encoding="utf-8")
    for i in lint_punct(text):
        print(f"[{i['level']}] {i['msg']}")
    return 0  # 纯 WARN


if __name__ == "__main__":
    raise SystemExit(main())
```

```python
# scripts/lint_anchors.py
"""跨期锚点门禁：脚本里 `../episodes/epNN-xxx/` 链接目标必须存在。"""
import re
import sys
from pathlib import Path

LINK_RE = re.compile(r"\]\(\.\./\.\./episodes/([^/)]+)/")


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
    ep_dir = Path(argv[0])
    show_dir = Path(argv[1]) if len(argv) > 1 else ep_dir.parent.parent
    for i in lint_anchors(ep_dir, show_dir):
        print(f"[{i['level']}] {i['msg']}")
    return 1 if any(i["level"] == "BLOCKING" for i in lint_anchors(ep_dir, show_dir)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

```python
# scripts/lint_trace.py
"""溯源门禁：script 的 {{voice:<id>}} 必须在 voices 集合内（workflow 独立 CLI 用）。"""
import json, re, sys
from pathlib import Path

REF_RE = re.compile(r"\{\{voice:([a-zA-Z0-9_-]+)\}\}")


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
    ep_dir = Path(argv[0])
    voices_path = Path(argv[1])
    voices = json.loads(voices_path.read_text(encoding="utf-8"))
    for i in lint_trace(ep_dir, voices):
        print(f"[{i['level']}] {i['msg']}")
    return 1 if any(i["level"] == "BLOCKING" for i in lint_trace(ep_dir, voices)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_lint_punct.py tests/test_lint_anchors.py tests/test_lint_trace.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/lint_punct.py scripts/lint_anchors.py scripts/lint_trace.py tests/test_lint_punct.py tests/test_lint_anchors.py tests/test_lint_trace.py
git commit -m "feat: lint_punct/anchors/trace 三个门禁"
```

---

### Task 10: audio_qa.py — 试听质检

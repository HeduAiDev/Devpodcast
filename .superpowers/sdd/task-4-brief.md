### Task 4: script.md 解析器

**Files:**
- Create: `scripts/script_parser.py`
- Test: `tests/test_script_parser.py`

**Interfaces:**
- Produces:
  - `@dataclass Turn`: `speaker: str`（"S1"/"S2"）、`text: str`、`voice_refs: list[str]`、`pause_ms: int | None`
  - `@dataclass Script`: `title: str`、`turns: list[Turn]`；`parse(path) -> Script`；`to_dialogue_tags(turn) -> str`（`[S1]text[/S1]` 形式，MOSS-TTSD 输入）
  - `format_error` 集合：缺 `[` 或 `[/` 成对、未知 speaker、非法 `<break>` 值

**script.md 约定格式（writer 契约的一部分）：**

```markdown
# ep01 议题标题

## 开场
[S1] 大家好，这期聊…… [/S1]
[S2] 开场第一个点…… {{voice:voice-001}} [/S2]

## 主体
[S1] …… <break 500ms> 停顿后继续…… [/S1]

## 收尾
[S2] 收尾金句。 [/S2]
```

- [ ] **Step 1: 写失败测试**

```python
# tests/test_script_parser.py
from pathlib import Path
import pytest
from scripts.script_parser import parse, ScriptParseError

def test_parse_basic(tmp_path):
    p = tmp_path / "script.md"
    p.write_text("""# 议题标题

## 开场
[S1] 大家好 [/S1]
[S2] 嗯，这期聊这个 {{voice:voice-001}} [/S2]

## 收尾
[S2] 收尾金句 [/S2]
""", encoding="utf-8")
    s = parse(p)
    assert s.title == "议题标题"
    assert len(s.turns) == 3
    assert s.turns[0].speaker == "S1"
    assert s.turns[1].voice_refs == ["voice-001"]
    assert s.turns[2].speaker == "S2"

def test_parse_pause(tmp_path):
    p = tmp_path / "script.md"
    p.write_text("[S1] 前面 <break 500ms> 后面 [/S1]\n", encoding="utf-8")
    s = parse(p)
    assert s.turns[0].pause_ms == 500

def test_unclosed_tag_raises(tmp_path):
    p = tmp_path / "script.md"
    p.write_text("[S1] 没关括号 [/S2]\n", encoding="utf-8")
    with pytest.raises(ScriptParseError):
        parse(p)

def test_bad_speaker_raises(tmp_path):
    p = tmp_path / "script.md"
    p.write_text("[S3] 不该出现 [/S3]\n", encoding="utf-8")
    with pytest.raises(ScriptParseError):
        parse(p)

def test_to_dialogue_tags(tmp_path):
    p = tmp_path / "script.md"
    p.write_text("[S1] 你好 [/S1]\n", encoding="utf-8")
    s = parse(p)
    assert s.to_dialogue_tags(s.turns[0]) == "[S1] 你好 [/S1]"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_script_parser.py -v`
Expected: FAIL

- [ ] **Step 3: 写实现**

```python
# scripts/script_parser.py
"""script.md → Script 结构化对象（speaker 成对 / 停顿 / voices 引用）。
格式：每段以 [S1] 或 [S2] 开头、[/S1] 或 [/S2] 结尾；{{voice:<id>}} 引 voices；
<break Nms> 显式停顿。"""
import re
from dataclasses import dataclass, field
from pathlib import Path

TURN_RE = re.compile(r"\[(S[12])\](.*?)\[/\1\]", re.S)
VOICE_RE = re.compile(r"\{\{voice:([a-zA-Z0-9_-]+)\}\}")
BREAK_RE = re.compile(r"<break\s+(\d+)ms\s*>")


class ScriptParseError(ValueError):
    pass


@dataclass
class Turn:
    speaker: str
    text: str
    voice_refs: list[str] = field(default_factory=list)
    pause_ms: int | None = None


@dataclass
class Script:
    title: str
    turns: list[Turn] = field(default_factory=list)

    @staticmethod
    def to_dialogue_tags(turn: Turn) -> str:
        return f"[{turn.speaker}] {turn.text} [/{turn.speaker}]"


def parse(path: Path) -> Script:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    title = ""
    m = re.search(r"^#\s+(.+)$", text, re.M)
    if m:
        title = m.group(1).strip()

    turns: list[Turn] = []
    for m in TURN_RE.finditer(text):
        speaker = m.group(1)
        body = m.group(2).strip()
        refs = VOICE_RE.findall(body)
        bm = BREAK_RE.search(body)
        pause = int(bm.group(1)) if bm else None
        clean = VOICE_RE.sub("", body)
        clean = BREAK_RE.sub("", clean).strip()
        turns.append(Turn(speaker, clean, refs, pause))

    # 校验：找到 [S1] 开头但无配对闭合的片段
    open_stray = re.findall(r"\[(S[12])\](?!.*?\[/\1\])", text)
    if open_stray:
        raise ScriptParseError(f"未闭合的说话人标记: {open_stray}")
    bad = re.findall(r"\[S[^12]\]", text)
    if bad:
        raise ScriptParseError(f"非法说话人标记: {bad}")
    return Script(title, turns)
```

（简化实现：`TURN_RE` 已捕获成对结构，`open_stray`/`bad` 为兜底校验。）

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_script_parser.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/script_parser.py tests/test_script_parser.py
git commit -m "feat: script.md 解析器（speaker 成对/停顿/voices 引用）"
```

---

### Task 5: tts.py — TTS 抽象 + 本地 provider 骨架

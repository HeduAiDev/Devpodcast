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
    p.write_text("[S4] 不该出现 [/S4]\n", encoding="utf-8")  # S4 超出当前支持的 S1-S3
    with pytest.raises(ScriptParseError):
        parse(p)

def test_to_dialogue_tags(tmp_path):
    p = tmp_path / "script.md"
    p.write_text("[S1] 你好 [/S1]\n", encoding="utf-8")
    s = parse(p)
    assert s.to_dialogue_tags(s.turns[0]) == "[S1] 你好 [/S1]"

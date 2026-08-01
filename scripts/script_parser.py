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

    # 校验：找到 [S1] 开头但无配对闭合的片段（re.S 以匹配多行 turn）
    open_stray = re.findall(r"\[(S[12])\](?!.*?\[/\1\])", text, re.S)
    if open_stray:
        raise ScriptParseError(f"未闭合的说话人标记: {open_stray}")
    bad = re.findall(r"\[S[^12]\]", text)
    if bad:
        raise ScriptParseError(f"非法说话人标记: {bad}")
    # 校验：闭合标签须与成对 turn 一一对应（捕获 [/S1]/[/S2] 错配被吞入文本的情况）
    closing = re.findall(r"\[/(S[12])\]", text)
    if len(closing) != len(turns):
        raise ScriptParseError(f"闭合标签与说话人标记不匹配: {closing}")
    return Script(title, turns)

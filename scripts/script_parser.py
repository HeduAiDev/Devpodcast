"""script.md → Script 结构化对象（speaker 成对 / 停顿 / voices 引用）。
格式：每段以 [S1] 或 [S2] 开头、[/S1] 或 [/S2] 结尾；{{voice:<id>}} 引 voices；
<break Nms> 显式停顿。"""
import re
from dataclasses import dataclass, field
from pathlib import Path

TURN_RE = re.compile(r"\[(S[123])\](.*?)\[/\1\]", re.S)
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
    # 带停顿的片段序列：[(文本片段, 片段后停顿ms)]，由 <break Nms> 切分。
    # 无 break 时为 [(text, None)]。合成器据此在 turn 内插静音。
    segments: list[tuple] = field(default_factory=list)


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
        body_novoice = VOICE_RE.sub("", body)
        # 按 <break Nms> 切成片段，保留每段后的停顿时长（turn 内停顿控制）
        seg_parts = []
        last = 0
        for bm in BREAK_RE.finditer(body_novoice):
            seg_text = body_novoice[last:bm.start()].strip()
            if seg_text:
                seg_parts.append((seg_text, int(bm.group(1))))
            last = bm.end()
        tail = body_novoice[last:].strip()
        if tail:
            seg_parts.append((tail, None))
        if not seg_parts:  # 兜底
            seg_parts = [(body_novoice.strip(), None)]
        bm_first = BREAK_RE.search(body_novoice)
        pause = int(bm_first.group(1)) if bm_first else None
        clean = BREAK_RE.sub("", body_novoice).strip()
        turns.append(Turn(speaker, clean, refs, pause, seg_parts))

    # 校验：找到 [S1] 开头但无配对闭合的片段（re.S 以匹配多行 turn）
    open_stray = re.findall(r"\[(S[123])\](?!.*?\[/\1\])", text, re.S)
    if open_stray:
        raise ScriptParseError(f"未闭合的说话人标记: {open_stray}")
    bad = re.findall(r"\[S[^123]\]", text)
    if bad:
        raise ScriptParseError(f"非法说话人标记: {bad}")
    # 校验：闭合标签须与成对 turn 一一对应（捕获 [/S1]/[/S2]/[/S3] 错配被吞入文本的情况）
    closing = re.findall(r"\[/(S[123])\]", text)
    if len(closing) != len(turns):
        raise ScriptParseError(f"闭合标签与说话人标记不匹配: {closing}")
    return Script(title, turns)

"""script.md → Script 结构化对象（speaker 成对 / 停顿 / voices 引用）。
格式：每段以 [S1] 或 [S2] 开头、[/S1] 或 [/S2] 结尾；{{voice:<id>}} 引 voices；
<break Nms> 显式停顿。"""
import re
from dataclasses import dataclass, field
from pathlib import Path

TURN_RE = re.compile(r"\[(S[123])\](.*?)\[/\1\]", re.S)
VOICE_RE = re.compile(r"\{\{voice:([a-zA-Z0-9_-]+)\}\}")
BREAK_RE = re.compile(r"<break\s+(\d+)ms\s*>")

# 标点 → 停顿时长（ms）。IndexTTS 自己的标点停顿不受控（同一句号实测 0ms/60ms/270ms
# 三种结果），所以抢在模型之前切开、由合成器插精确静音。冒号不切（紧跟其后的内容）。
PUNCT_PAUSE_MS = {
    "……": 400, "…": 400,   # 省略号：停顿感最强
    "——": 250, "—": 250,    # 破折号：转折
    "。": 350, "！": 350, "？": 350,
    "；": 250,
    "，": 200,
    "、": 150,
}
# 逗号只在长片段内切——短句本就一口气说完，切开反而破坏语流
COMMA_MIN_CHARS = 20
_PUNCT_SPLIT_RE = re.compile(r"(……|…|——|—|[。！？；，、])")


def auto_segment(text: str, default_pause: int | None = None) -> list[tuple]:
    """按标点切成 [(片段, 停顿ms)]，末段停顿沿用 default_pause（手写 <break> 的值）。

    手写 <break> 优先：调用方按 break 切完后，对每个片段调用本函数做细分，
    该片段原有的 pause 作为 default_pause 留给最后一个子片段。
    """
    parts = _PUNCT_SPLIT_RE.split(text)
    segs: list[tuple] = []
    buf = ""
    for i in range(0, len(parts), 2):
        buf += parts[i]
        punct = parts[i + 1] if i + 1 < len(parts) else ""
        if not punct:
            continue
        buf += punct
        pause = PUNCT_PAUSE_MS.get(punct)
        # 逗号/顿号在短片段内不切，让语流连贯
        if punct in ("，", "、") and len(buf.strip()) < COMMA_MIN_CHARS:
            continue
        if buf.strip():
            segs.append((buf.strip(), pause))
        buf = ""
    tail = buf.strip()
    if tail:
        segs.append((tail, default_pause))
    elif segs:
        # 文本以标点收尾：末段停顿让位于手写 break
        segs[-1] = (segs[-1][0], default_pause if default_pause is not None else segs[-1][1])
    return segs or [(text.strip(), default_pause)]


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
        # 先按 <break Nms> 切（手写停顿优先），再对每片按标点细分（自动兜底）
        seg_parts = []
        last = 0
        for bm in BREAK_RE.finditer(body_novoice):
            seg_text = body_novoice[last:bm.start()].strip()
            if seg_text:
                seg_parts.extend(auto_segment(seg_text, int(bm.group(1))))
            last = bm.end()
        tail = body_novoice[last:].strip()
        if tail:
            seg_parts.extend(auto_segment(tail, None))
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

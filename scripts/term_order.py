#!/usr/bin/env python3
"""术语首现顺序审计：按播出顺序扫全季 script.md，对每个技术名词记录
   - S2（专家）首次说出它的位置
   - S1/S3（非专家）首次说出它的位置
倒序（S1/S3 早于 S2）即为「提前使用」候选。

用法: python term_order.py <ep_dir1> <ep_dir2> ...
"""
import re, sys
from pathlib import Path

TURN_RE = re.compile(r"\[(S[123])\](.*?)\[/\1\]", re.S)
BREAK_RE = re.compile(r"<break\s+\d+ms\s*>")

# 技术名词候选：英文标识符 + 中文技术词。阿哲的后端母语词单独豁免。
BACKEND_NATIVE = {
    "线程池", "连接池", "消息队列", "负载均衡", "缓存", "熔断", "降级", "分布式锁",
    "队列", "进程", "线程", "内存", "显存", "数据库", "接口", "并发", "阻塞",
    "超时", "重试", "日志", "监控", "服务", "客户端", "服务端", "协程",
}

CN_TERM_RE = re.compile(
    r"(持久批次|连续批处理|前缀缓存|投机解码|草稿模型|残差分布|位掩码|块表|块池|"
    r"引用计数|算子融合|显存碎片|页表|写时复制|张量并行|流水线并行|分组查询注意力|"
    r"工作进程|工作者|调度器|执行器|采样器|分词器|预填充|解码|抢占|驱逐|"
    r"前向|后向|内核|算子|编译分区|录像|回放|图捕获|图重放)"
)
EN_TERM_RE = re.compile(
    r"\b(EngineCore|Scheduler|ModelRunner|Executor|KVCacheManager|BlockPool|AsyncLLM|"
    r"OutputProcessor|Worker|worker|Detokenizer|PagedAttention|CUDA\s?[Gg]raph|"
    r"chunked\s+prefill|prefill|decode|prefix\s+caching|tensor\s+parallel|"
    r"pipeline\s+parallel|speculative\s+decoding|KV\s?cache|block\s+table|logits?|"
    r"temperature|top[-_]?[kp]|min_p|beam\s+search|guided\s+decoding|"
    r"collective\s+RPC|RPC|ZMQ|zmq|asyncio|GIL|HBM|SM|kernel|Triton|Inductor|LoRA|"
    r"GQA|MQA|MLA|FlashAttention|Custom\s?Op|forward_cuda|forward_native|"
    r"execute_model|sample_tokens|add_request|schedule|allocate_slots|step|forward|"
    r"SchedulerOutput|ModelRunnerOutput|EngineCoreOutput|SequenceGroup|Request|"
    r"max_num_batched_tokens|max_num_seqs|logit_bias|bad_words|min_tokens|"
    r"n-gram|EAGLE|MTP|p50|p99|token|Blackwell|Hopper|Ampere)\b"
)


def norm(t):
    t = re.sub(r"\s+", " ", t.strip())
    low = t.lower()
    # 归一化同义写法
    alias = {
        "worker": "Worker", "cuda graph": "CUDA graph", "cudagraph": "CUDA graph",
        "kv cache": "KV cache", "kvcache": "KV cache", "logit": "logits",
        "工作进程": "Worker", "工作者": "Worker",
    }
    return alias.get(low, t)


def scan(ep_dirs):
    # term -> {"S2": (ep_order, ep_name, line, quote), "NON": (ep_order, ep_name, line, spk, quote)}
    first = {}
    for order, ed in enumerate(ep_dirs, 1):
        ed = Path(ed)
        f = ed / "script.md"
        if not f.exists():
            continue
        raw = f.read_text(encoding="utf-8")
        for m in TURN_RE.finditer(raw):
            spk, body = m.group(1), m.group(2)
            line = raw[: m.start()].count("\n") + 1
            body = BREAK_RE.sub("", body)
            terms = set()
            for tm in EN_TERM_RE.finditer(body):
                terms.add(norm(tm.group(1)))
            for tm in CN_TERM_RE.finditer(body):
                terms.add(norm(tm.group(1)))
            for t in terms:
                rec = first.setdefault(t, {})
                key = "S2" if spk == "S2" else "NON"
                if key not in rec:
                    q = re.sub(r"\s+", " ", body.strip())[:70]
                    rec[key] = (order, ed.name, line, spk, q)
    return first


def main():
    eps = [Path(e) for e in sys.argv[1:]]
    first = scan(eps)
    rows = []
    for t, rec in first.items():
        s2, non = rec.get("S2"), rec.get("NON")
        if not non:
            continue  # 非专家从没说过
        if not s2:
            rows.append((999, non[0], t, "全季 S2 未说过", non))
        elif (non[0], non[2]) < (s2[0], s2[2]):
            rows.append((non[0], non[0], t, f"S2 首现 {s2[1]}:{s2[2]}", non))
    rows.sort(key=lambda r: (r[0], r[2]))
    print(f"{'='*100}")
    print("倒序术语（S1/S3 早于 S2 说出，或 S2 全季未说过）")
    print(f"{'='*100}")
    if not rows:
        print("（无）")
    for _, _, t, s2info, non in rows:
        print(f"\n【{t}】")
        print(f"  非专家首现: {non[1]}:{non[2]} [{non[3]}] 「{non[4]}」")
        print(f"  S2 情况   : {s2info}")
    print(f"\n共 {len(rows)} 个倒序术语")


if __name__ == "__main__":
    main()

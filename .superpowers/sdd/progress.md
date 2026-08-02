# devpodcast M0+M1 SDD 进度台账

Task 1: complete (commits 006d08e..470b834, review clean) — minor: PEP8 导入风格 / DEVPODCAST_SHOW env 测试未隔离(flaky 风险) / env 覆盖分支零测试覆盖
Task 2: complete (commits 470b834..7e2334b, review clean) — minor: 尾随空格正则边缘 / 未类型断言 / iterdir 未守卫 / 回退分支未测 / digest 悬空待 Task 3; 偏离裁决: fixture 补 instances/mini 层级 + Protocol @runtime_checkable 均接受
Task 3: complete (commits 7e2334b..3204622, review clean) — minor: digest 流无分隔符理论碰撞 / _stable_digest 死代码 / 不清理陈旧文件 / 抛错路径无测试覆盖; Lead 验证: 全量 13 passed
Task 4: complete (commits 3204622..8b4f161, review clean) — minor: 两处正则修正未沉淀回归测试 / 非法 break 值未校验 / [/S3] 静默忽略 / break 移除残留双空格 / 嵌套标签被吞(brief 明示简化); 偏离裁决: re.S 修复 + 闭合标签计数 均接受
Task 5: complete (commits 8b4f161..5508b0e, review clean) — minor: vram_report 只报主卡 / brief 接口行与参考代码类型标注不一致 / docstring 超前提到 batch 管理; 偏离裁决: runtime_checkable + list_voices stub 接受(Task 2 同因先例)
Task 6: complete (commits 5508b0e..f04990e, review clean) — minor 4 项(brief 逐字/计划层); 偏离裁决: test_budget_check_ok 400→100 字接受(brief 自相矛盾); LEAD 裁决: Task 7 派发时带上「budget_check 返回 list[str] vs lint_script 期望 list[dict]」跨任务接口不一致修复
Task 7: complete (commits f04990e..aa5ae8f, review clean after 1 fix round) — r1 Important×2 (dict 转换零测试 / CLI 无参崩溃) 已修复并复审通过; minor 残余: --voices 文件不存在仍 traceback / tests import pytest 未用; Lead 裁决执行 + sys.path 偏离均接受
Task 8: complete (commits aa5ae8f..7c16dc4, review clean) — minor 5 项(KeyError 边角/Counter+pytest 冗余导入/缺文件 traceback 与 Task 7 一致/brief 层测试覆盖缺口); 偏离裁决: Path 模块级 + 无参守卫 接受; 评审独立验证 54/54
Task 9: complete (commits 7c16dc4..fcbadfe, review clean) — minor 4 项(brief 原样行为); 偏离裁决: test_valid_link_ok setup 修复 接受(brief 双重必挂已独立复现); LEAD 兜底 ⚠️×3: canonical 布局/workflow 集成/真实链接深度 → Task 18/19 实证
Task 10: complete (commits fcbadfe..27a27d2, review clean) — minor 5 项(np.float64 返回/CLI 非法参数裸 traceback/空 wav 除零/前缀冗余属 brief/vram_gb 恒 0.0 已披露); 偏离×3 全接受(50s 测试笔误/write_report 漏 import/numpy.bool_ 序列化)
Task 11: complete (commits 27a27d2..6020b89, review clean) — minor 6 项(brief 原样继承为主); 偏离×2 接受(补 2 archivist 测试 / 无参守卫先例)
Task 12: complete (commits 6020b89..9de8837, review clean) — minor 4 项(brief 边界); 偏离裁决: voices.schema anyOf 改法 接受(独立实测 brief 原形态自相矛盾); LEAD 兜底 ⚠️×4: arc/production-notes/season-bible 前向契约 + voices 真实形态 → Task 18/19 复验
Task 13: complete (commits 9de8837..444522e, review clean) — minor 3 项(同名覆盖/空目录不追踪/模板长行); 偏离×2 接受(注册表 missing 分支 / CLI 无参守卫); voice-guide 模板字节级一致
代码任务 1-13 全部完成：79 tests passed

Task 14: complete (commits 444522e..c9a8b62, review clean after 1 fix round) — r1 Important×2 (season_bible register CLI 静默 no-op / writer.md lint_punct 缺参数) 已修复并复审通过; Minor×2 全清; 8 提示词 spec 契约点全对齐
Task 15: complete (commits 349214d..e7c4362, review clean after 1 fix round) — season-pipeline.js + episode-pipeline.js 骨架; r1 Important×2 (Review 产物命名对齐 reviewer 契约 / voices_coverage 显式落盘) 已修复并复审通过; Minor×2 全清
Task 16: complete (commit 731dac6) — CLAUDE.md + docs/superpowers/ARCHITECT-RUNBOOK.md + README.md（工厂操作手册三件套）

Task 17: partial
  已完成:
    - 731dac6: SSL 修复 (sitecustomize.py 绕过损坏的 Windows 证书库)
    - 72774e7: F5-TTS 验证通过 (CUDA/torch/flash-attn OK) + pyproject.toml + ta_compat.py + vllm-podcast scaffold
    - e130e82: vllm-podcast 书源摄入 (39章+115术语→source-book/)
    - 2250062: ingest_book.py CLI (--show --root --instance --refresh)
    - 72a3024: 8 agent frontmatter effort: max
    - 9e69149: 7 workflow agentType:'claude' call effort: 'max'
  进行中:
    - MOSS-TTSD 8B 权重下载 → 子 agent a7ced79f 监控 (models/ 已 2.2GB/16GB)
    - 诊断修复: Windows cert store ASN1 损坏 / processing_moss_tts.py Path→str bug / torchaudio→soundfile fallback
  待 Lead:
    - voice-samples (laozhang.wav / akai.wav, 各 5-10s)

MOSS-TTSD sample_dialogue.wav: 34.6s/23.3s @ 1.5x; 额外发现并修复 2 个模型代码 bug (dtype/float mismatch + torch.split position→size)

Task 19: pending — 等待 Task 17 + 18 完成

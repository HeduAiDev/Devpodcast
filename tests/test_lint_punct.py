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

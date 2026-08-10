import pytest
from scripts.lint_voices import lint_voices

def base_voice(**kw):
    v = {"id": "v1", "category": "critical", "term": "t", "claim": "c",
         "verified": "community-only", "source_url": "https://x.example/1",
         "source_date": "2026-07-15", "source_platform": "hn",
         "speaker_handle": "@匿名", "anonymized": True,
         "confidence": "high", "writer_note": ""}
    v.update(kw)
    return v

def test_missing_url_blocking():
    v = base_voice(source_url="")
    issues = lint_voices({"v1": v})
    assert any("source_url" in i["msg"] and i["level"] == "BLOCKING" for i in issues)

def test_missing_date_blocking():
    v = base_voice(source_date="")
    issues = lint_voices({"v1": v})
    assert any("source_date" in i["msg"] and i["level"] == "BLOCKING" for i in issues)

def test_non_anonymous_requires_official_platform():
    v = base_voice(anonymized=False, source_platform="reddit")
    issues = lint_voices({"v1": v})
    assert any("anonymized" in i["msg"] and i["level"] == "BLOCKING" for i in issues)

def test_official_platform_can_be_named():
    v = base_voice(anonymized=False, source_platform="official")
    issues = lint_voices({"v1": v})
    assert not any("anonymized" in i["msg"] for i in issues)

def test_low_confidence_requires_note():
    v = base_voice(confidence="low", writer_note="")
    issues = lint_voices({"v1": v})
    assert any("未一手核实" in i["msg"] and i["level"] == "BLOCKING" for i in issues)

def test_single_source_warn():
    issues = lint_voices({"v1": base_voice()})
    assert any("单一来源" in i["msg"] and i["level"] == "WARN" for i in issues)

def test_two_platforms_no_warn():
    v1 = base_voice()
    v2 = base_voice(id="v2", source_url="https://y.example/2", source_platform="zhihu")
    issues = lint_voices({"v1": v1, "v2": v2})
    assert not any("单一来源" in i["msg"] for i in issues)

def test_verified_official_single_source_ok():
    v = base_voice(verified="official")
    issues = lint_voices({"v1": v})
    assert not any("单一来源" in i["msg"] for i in issues)

def test_job_seeker_platform_rule():
    v = base_voice(category="job-seeker", source_platform="github-issue")
    issues = lint_voices({"v1": v})
    assert any("job-seeker" in i["msg"] and i["level"] == "BLOCKING" for i in issues)

def test_job_seeker_platform_ok():
    v = base_voice(category="job-seeker", source_platform="niuke")
    issues = lint_voices({"v1": v})
    assert not any("job-seeker" in i["msg"] for i in issues)

def test_cli_no_args_usage_returns_2(capsys):
    from scripts.lint_voices import main
    assert main([]) == 2
    err = capsys.readouterr().err
    assert "usage: python3 scripts/lint_voices.py" in err

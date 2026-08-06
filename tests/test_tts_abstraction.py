import pytest
from scripts.tts import FireRedTTSProvider, load_provider, TTSProvider, TTSOpts


def test_firered_provider_native_flag():
    p = FireRedTTSProvider(model_dir="/tmp/nonexistent")
    assert p.native_dialogue is True


def test_firered_default_params():
    p = FireRedTTSProvider(model_dir="/tmp/nonexistent")
    # 2026-08-07 参数扫描选定：t0.8_k15（20 组人工试听）
    assert p.temperature == 0.8
    assert p.topk == 15


def test_load_provider_dispatch():
    p = load_provider({"provider": "firered-tts2"})
    assert isinstance(p, FireRedTTSProvider)


def test_load_provider_unknown_raises():
    with pytest.raises(ValueError):
        load_provider({"provider": "nope"})


def test_implements_protocol():
    assert isinstance(FireRedTTSProvider(model_dir="/tmp/nonexistent"), TTSProvider)

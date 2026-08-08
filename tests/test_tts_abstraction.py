import pytest
from scripts.tts import IndexTTS2Provider, load_provider, TTSProvider, TTSOpts


def test_indextts2_provider_native_flag():
    p = IndexTTS2Provider(model_dir="/tmp/nonexistent")
    assert p.native_dialogue is True


def test_indextts2_paths_configured():
    p = IndexTTS2Provider(model_dir="/tmp/nonexistent")
    # 2026-08-08 定案：IndexTTS-2 跑在 conda env itts310，经子进程调用单句脚本
    assert "itts310" in p.ITTS_PYTHON
    assert "indextts_synth_singleturn.py" in p.SYNTH_SCRIPT


def test_load_provider_dispatch_indextts2():
    p = load_provider({"provider": "indextts2"})
    assert isinstance(p, IndexTTS2Provider)


def test_load_provider_unknown_raises():
    with pytest.raises(ValueError):
        load_provider({"provider": "nope"})


def test_implements_protocol():
    assert isinstance(IndexTTS2Provider(model_dir="/tmp/nonexistent"), TTSProvider)

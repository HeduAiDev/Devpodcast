import pytest
from scripts.tts import (DialogueTTSProvider, SegmentedTTSProvider, load_provider,
                         TTSProvider, TTSOpts)

def test_dialogue_provider_native_flag():
    p = DialogueTTSProvider(model_dir="/tmp/nonexistent")
    assert p.native_dialogue is True

def test_segmented_provider_pause_constants():
    p = SegmentedTTSProvider(model_dir="/tmp/nonexistent")
    assert p.PAUSE_SPEAKER_SWITCH_MS == (350, 500)
    assert p.PAUSE_SAME_SPEAKER_MS == (150, 250)

def test_load_provider_dispatch():
    p = load_provider({"provider": "moss-ttsd"})
    assert isinstance(p, DialogueTTSProvider)
    p2 = load_provider({"provider": "cosyvoice3"})
    assert isinstance(p2, SegmentedTTSProvider)

def test_load_provider_unknown_raises():
    with pytest.raises(ValueError):
        load_provider({"provider": "nope"})

def test_synthesize_not_implemented_yet():
    p = DialogueTTSProvider(model_dir="/tmp/nonexistent")
    with pytest.raises(NotImplementedError):
        p.synthesize(script=None, voice_map={}, opts=TTSOpts())

def test_implements_protocol():
    assert isinstance(DialogueTTSProvider(model_dir="/tmp/nonexistent"), TTSProvider)

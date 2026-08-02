"""MOSS-TTSD v1.0 端到端测试脚本。需已下载模型到 models/moss-ttsd/。"""
import sys, os, time, torch
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import scripts.ta_compat

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
torch.backends.cuda.enable_cudnn_sdp(False)
for attr in ("flash_sdp", "mem_efficient_sdp", "math_sdp"):
    getattr(torch.backends.cuda, f"enable_{attr}")(True)

LOCAL = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "moss-ttsd")
REF_DIR = "E:/Laboratory/MOSS-TTSD/asset"
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_output")

from transformers import AutoModel, AutoProcessor
import torchaudio, soundfile as sf

def load():
    processor = AutoProcessor.from_pretrained(LOCAL, trust_remote_code=True)
    processor.audio_tokenizer = processor.audio_tokenizer.to("cuda").eval()
    model = AutoModel.from_pretrained(
        LOCAL, trust_remote_code=True, attn_implementation="sdpa",
        torch_dtype=torch.bfloat16, device_map="auto", low_cpu_mem_usage=True,
    ).eval()
    return processor, model

def prep_audio(processor):
    target_sr = int(processor.model_config.sampling_rate)
    wavs = []
    for name in ("reference_02_s1.wav", "reference_02_s2.wav"):
        w, sr = torchaudio.load(f"{REF_DIR}/{name}")
        if w.shape[0] > 1:
            w = w.mean(dim=0, keepdim=True)
        if sr != target_sr:
            w = torchaudio.functional.resample(w, sr, target_sr)
        wavs.append(w)
    return wavs[0], wavs[1], target_sr

def main():
    print("=== MOSS-TTSD v1.0 ===")

    processor, model = load()
    n_vq = getattr(processor.model_config, "n_vq", 16)
    target_sr = int(processor.model_config.sampling_rate)
    vram = torch.cuda.mem_get_info(0)[0] / 1024**3
    print(f"Loaded | VRAM free: {vram:.1f}GB | n_vq={n_vq} | sr={target_sr}")

    wav1, wav2, _ = prep_audio(processor)

    full_text = (
        "[S1] In short, we embarked on a mission to make America great again. "
        "[S2] NVIDIA reinvented computing for the first time after 60 years. "
        "[S1] Welcome to Devpodcast! This is the final MOSS-TTSD v1.0 verification test. "
        "[S2] Confirmed. The model loaded, generated tokens, and now we are decoding the audio."
    )

    ref_codes = processor.encode_audios_from_wav([wav1, wav2], sampling_rate=target_sr)
    prompt_audio = processor.encode_audios_from_wav(
        [torch.cat([wav1, wav2], dim=-1)], sampling_rate=target_sr
    )[0]
    conv = [[
        processor.build_user_message(text=full_text, reference=ref_codes),
        processor.build_assistant_message(audio_codes_list=[prompt_audio]),
    ]]

    batch = processor(conv, mode="continuation")

    t0 = time.time()
    with torch.no_grad():
        outputs = model.generate(
            input_ids=batch["input_ids"].to("cuda"),
            attention_mask=batch["attention_mask"].to("cuda"),
            max_new_tokens=1024,
            text_temperature=1.1, text_top_p=0.9, text_top_k=50,
            audio_temperature=1.1, audio_top_p=0.9, audio_top_k=50,
            audio_repetition_penalty=1.1,
        )
    gen_time = time.time() - t0

    # Show output structure
    print(f"outputs: {type(outputs).__name__} len={len(outputs)}")
    for i, item in enumerate(outputs):
        if isinstance(item, (list, tuple)):
            print(f"  [{i}] {type(item).__name__} len={len(item)}")
            for j, sub in enumerate(item):
                shape = sub.shape if hasattr(sub, "shape") else "?"
                print(f"    [{j}] {type(sub).__name__} shape={shape}")
        else:
            shape = item.shape if hasattr(item, "shape") else "?"
            print(f"  [{i}] {type(item).__name__} shape={shape}")

    n_tokens = outputs[0][1].shape[0]
    print(f"\nGen: {gen_time:.1f}s | {n_tokens} tokens ({n_tokens/gen_time:.0f} tok/s)")

    # Convert to CPU
    outputs_cpu = []
    for item in outputs:
        if isinstance(item, (list, tuple)):
            outputs_cpu.append(tuple(
                int(x.item()) if isinstance(x, torch.Tensor) and x.ndim == 0 else
                x.cpu() if isinstance(x, torch.Tensor) else x
                for x in item
            ))
        elif isinstance(item, torch.Tensor):
            outputs_cpu.append(item.cpu())
        else:
            outputs_cpu.append(item)

    # Decode
    decoded = processor.decode(outputs_cpu)

    # Save audio
    os.makedirs(OUT_DIR, exist_ok=True)
    total_dur = 0

    for i, msg in enumerate(decoded):
        codes_list = msg.audio_codes_list

        # Normalize: flatten any nested lists
        flat_codes = []
        def _collect(x):
            if isinstance(x, torch.Tensor):
                flat_codes.append(x)
            elif isinstance(x, (list, tuple)):
                for item in x:
                    _collect(item)
        _collect(codes_list)

        for j, codes in enumerate(flat_codes):
            codes = codes.cpu()
            if codes.ndim == 1:
                L = codes.shape[0] // n_vq * n_vq
                codes = codes[:L].reshape(-1, n_vq)
            codes = codes.contiguous()

            wav = processor.decode_audio_codes(codes)
            # wav may be a single tensor or list of segment tensors
            if isinstance(wav, list):
                wav = torch.cat(wav, dim=-1)
            wav_np = wav.cpu().numpy()
            if wav_np.ndim == 1:
                wav_np = wav_np.reshape(-1, 1)

            out_path = os.path.join(OUT_DIR, f"ep01_test_{i}_{j}.wav")
            sf.write(out_path, wav_np.astype("float32"), target_sr)
            dur = len(wav_np) / target_sr
            total_dur += dur
            size_kb = os.path.getsize(out_path) / 1024
            print(f"  {os.path.basename(out_path)}: {dur:.1f}s ({size_kb:.0f}KB)")

    print(f"\nTotal audio: {total_dur:.1f}s")
    print(f"Output dir: {OUT_DIR}")
    print("=== MOSS-TTSD v1.0 VERIFIED OK ===")
    return total_dur


if __name__ == "__main__":
    main()

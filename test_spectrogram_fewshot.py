"""
Few-Shot Spectrogram Test
==========================
Give the model EXAMPLES of what "no human" and "human present"
spectrograms look like, then ask it to classify new ones.

This is the approach validated in NeurIPS 2024:
"Vision Language Models Are Few-Shot Audio Spectrogram Classifiers"
"""

import numpy as np
import librosa
import librosa.display
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import soundfile as sf
import requests
import base64
import json
import time
import io
import os


# ── Settings ──────────────────────────────────────────────────
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL      = "gemma4:e4b"
SR         = 16000
CHUNK_SEC  = 5
AUDIO_DIR  = os.path.join("dataset", "audio")


def audio_to_spectrogram_b64(filepath, start_sec, duration_sec=CHUNK_SEC):
    """Audio chunk → mel spectrogram → PNG → base64."""
    audio, _ = sf.read(filepath, start=start_sec * SR,
                       stop=(start_sec + duration_sec) * SR)
    audio = audio.astype(np.float32)

    S = librosa.feature.melspectrogram(
        y=audio, sr=SR, n_mels=128, fmax=8000,
        hop_length=256, n_fft=1024,
    )
    S_dB = librosa.power_to_db(S, ref=np.max)

    fig, ax = plt.subplots(1, 1, figsize=(10, 4), dpi=100)
    librosa.display.specshow(
        S_dB, sr=SR, hop_length=256,
        x_axis='time', y_axis='mel', ax=ax, cmap='magma'
    )
    ax.set_title(f'Audio Spectrogram ({start_sec}-{start_sec+duration_sec}s)')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Frequency (Hz)')
    plt.colorbar(ax.collections[0], ax=ax, format='%+2.0f dB')
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


def parse_json(raw):
    """Extract JSON from response."""
    import re
    # Find the last JSON object (most likely the answer)
    matches = list(re.finditer(r'\{[^{}]*\}', raw, re.DOTALL))
    if matches:
        try:
            return json.loads(matches[-1].group()), "ok"
        except json.JSONDecodeError:
            pass
    return {"raw": raw[:300]}, "parse_error"


def few_shot_classify(target_img_b64, example_clean_b64, example_human_b64):
    """
    Few-shot classification using chat history as examples.
    
    Message flow:
    1. User shows CLEAN example → Assistant learns "no human"
    2. User shows HUMAN example → Assistant learns "human present"  
    3. User shows TARGET → Assistant classifies
    """
    messages = [
        # Example 1: Clean (S1 pump room)
        {
            "role": "user",
            "content": (
                "I will show you spectrogram images from industrial audio. "
                "Your job is to detect human voice.\n\n"
                "EXAMPLE 1 - NO HUMAN VOICE:\n"
                "This spectrogram shows ONLY machine noise. "
                "Notice the steady horizontal bands at the bottom — that is pump/motor hum. "
                "The upper area is dark/empty. No formant curves, no speech patterns.\n"
                "Correct answer: human_detected=false, confidence=0.1, alarm=false"
            ),
            "images": [example_clean_b64],
        },
        {
            "role": "assistant",
            "content": '{"human_detected": false, "confidence": 0.1, "distress_type": "none", "alarm": false, "reasoning": "Only steady machine noise bands visible, no speech formants"}'
        },
        # Example 2: Human voice (S4 masked voice)
        {
            "role": "user",
            "content": (
                "EXAMPLE 2 - HUMAN VOICE PRESENT:\n"
                "This spectrogram shows human voice mixed with background noise. "
                "Look at the bright curved/stacked horizontal bands between 512-2048Hz — "
                "those are speech formants. They appear as short bursts with gaps between them. "
                "Machine noise does NOT have these curved/stacked patterns.\n"
                "Correct answer: human_detected=true, confidence=0.85, alarm=true"
            ),
            "images": [example_human_b64],
        },
        {
            "role": "assistant",
            "content": '{"human_detected": true, "confidence": 0.85, "distress_type": "muffled_call", "alarm": true, "reasoning": "Clear speech formant bands visible at 512-2048Hz with syllable rhythm pattern"}'
        },
        # Target: classify this one
        {
            "role": "user",
            "content": (
                "NOW CLASSIFY THIS NEW SPECTROGRAM:\n"
                "Look carefully for speech formant patterns like in Example 2. "
                "If you see curved/stacked horizontal bands at 512-2048Hz = human voice.\n"
                "Respond ONLY with JSON:"
            ),
            "images": [target_img_b64],
        },
    ]

    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 512,
        }
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=180)
        resp.raise_for_status()
        data = resp.json()
        msg = data.get("message", {})
        content = msg.get("content", "")
        thinking = msg.get("thinking", "")
        return content if content.strip() else thinking
    except Exception as e:
        return f"ERROR: {e}"


def main():
    print("\n" + "=" * 65)
    print("  FEW-SHOT SPECTROGRAM CLASSIFICATION TEST")
    print("  Teaching the model with examples before asking")
    print("=" * 65)
    print(f"  Model: {MODEL}")
    print(f"  Method: 2 examples (clean + human) → classify target")
    print(f"  Reference: NeurIPS 2024 'VLMs as Audio Classifiers'")
    print("=" * 65)

    # Generate example spectrograms
    print("\n  Generating example spectrograms...")
    
    # Example CLEAN: S1 pump room (15-20s) — definitely no human
    clean_b64 = audio_to_spectrogram_b64(
        os.path.join(AUDIO_DIR, "S1_pump_room_normal.wav"), 15
    )
    print("  ✓ Clean example: S1 pump room (15-20s)")

    # Example HUMAN: S4 masked voice (25-30s) — clearly has formants
    human_b64 = audio_to_spectrogram_b64(
        os.path.join(AUDIO_DIR, "S4_manhole_masked.wav"), 25
    )
    print("  ✓ Human example: S4 masked voice (25-30s)")

    # Targets to classify
    targets = [
        ("S1", "S1_pump_room_normal.wav", 30, "Pump room 30-35s (NO human)"),
        ("S2", "S2_construction_human.wav", 30, "Construction + shouting (HUMAN)"),
        ("S3", "S3_pool_false_alarm.wav", 30, "Metallic sounds (NO human)"),
        ("S4", "S4_manhole_masked.wav", 35, "Masked voice 35-40s (HUMAN)"),
        ("S5", "S5_pool_critical.wav", 25, "Drowning scream (CRITICAL HUMAN)"),
        ("S5b", "S5_pool_critical.wav", 30, "Drowning 30-35s (HUMAN)"),
        ("S5c", "S5_pool_critical.wav", 40, "Drowning 40-45s (HUMAN)"),
    ]

    for label, filename, start_sec, desc in targets:
        filepath = os.path.join(AUDIO_DIR, filename)
        if not os.path.exists(filepath):
            print(f"\n  [SKIP] {filename} not found")
            continue

        print(f"\n  {'─' * 60}")
        print(f"  {label} | {start_sec}-{start_sec+CHUNK_SEC}s | {desc}")
        print(f"  {'─' * 60}")

        # Generate target spectrogram
        target_b64 = audio_to_spectrogram_b64(filepath, start_sec)

        # Few-shot classify
        print(f"  Classifying (few-shot)...")
        t0 = time.time()
        raw = few_shot_classify(target_b64, clean_b64, human_b64)
        elapsed = time.time() - t0

        # Parse
        parsed, status = parse_json(raw)

        alarm = parsed.get("alarm", False)
        conf  = parsed.get("confidence", 0.0)
        dtype = parsed.get("distress_type", "?")
        reason = parsed.get("reasoning", "?")

        flag = "🚨 ALARM" if alarm else "   ----"
        print(f"  {flag} | conf:{conf:.2f} | {dtype}")
        print(f"  Reasoning: {reason[:150]}")
        print(f"  Time: {elapsed:.1f}s | Parse: {status}")

        if status == "parse_error":
            print(f"  Raw: {raw[:400]}")

    print(f"\n{'=' * 65}")
    print(f"  Few-shot test complete.")
    print(f"{'=' * 65}\n")


if __name__ == "__main__":
    main()

"""
Feature-Text POC Test
======================
Extract audio features with librosa → convert to text → send to Gemma 4.
Model reads numbers, not audio. No images, no spectrograms.

"Doktora hastanın kan değerlerini ver, teşhis koysun."

Hypothesis: LLM is better at reasoning about structured data
than perceiving raw audio or spectrogram images.

Usage:
    python test_feature_text_poc.py
"""

import numpy as np
import librosa
import soundfile as sf
import requests
import json
import time
import os


# ── Settings ──────────────────────────────────────────────────
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL      = "gemma4:e4b"
SR         = 16000
CHUNK_SEC  = 5
AUDIO_DIR  = os.path.join("dataset", "audio")

# Test chunks — same ones used in spectrogram POC for comparison
TEST_CHUNKS = [
    ("S1", "S1_pump_room_normal.wav", 15, False, "Pump room - NO human"),
    ("S2_pre", "S2_construction_human.wav", 10, False, "Construction only - NO human"),
    ("S2_post", "S2_construction_human.wav", 30, True, "Construction + shouting - HUMAN"),
    ("S3", "S3_pool_false_alarm.wav", 25, False, "Metallic sounds - NO human"),
    ("S4_pre", "S4_manhole_masked.wav", 10, False, "Underground only - NO human"),
    ("S4_post", "S4_manhole_masked.wav", 25, True, "Underground + masked voice - HUMAN"),
    ("S5_pre", "S5_pool_critical.wav", 10, False, "Construction only - NO human"),
    ("S5_post", "S5_pool_critical.wav", 30, True, "Drowning scream - CRITICAL HUMAN"),
]


# ═══════════════════════════════════════════════════════════════
# FEATURE EXTRACTION
# ═══════════════════════════════════════════════════════════════

def extract_features(filepath, start_sec, duration_sec=CHUNK_SEC, sr=SR):
    """
    Extract acoustic features from a 5-second audio chunk.

    Returns a dict of numerical features that characterize the sound:
    - RMS energy (loudness)
    - Zero-crossing rate (noise vs tonal)
    - Spectral centroid (frequency center of mass)
    - Spectral bandwidth (frequency spread)
    - Spectral rolloff (where 85% of energy is below)
    - MFCC means and variances (speech fingerprint)
    - Formant band energy ratio (human voice indicator)
    - Harmonic-to-noise ratio approximation
    - Temporal energy variance (steady vs changing)
    """
    # Load chunk
    audio, _ = sf.read(filepath,
                       start=start_sec * sr,
                       stop=(start_sec + duration_sec) * sr)
    audio = audio.astype(np.float32)

    # ── Basic features ────────────────────────────────────────
    # RMS energy (overall loudness)
    rms = float(np.mean(librosa.feature.rms(y=audio)[0]))

    # RMS variance (steady sound vs bursts)
    rms_frames = librosa.feature.rms(y=audio)[0]
    rms_var = float(np.var(rms_frames))

    # Zero-crossing rate (noise-like vs tonal)
    zcr = float(np.mean(librosa.feature.zero_crossing_rate(audio)[0]))

    # ── Spectral features ─────────────────────────────────────
    # Spectral centroid (frequency "center of mass")
    centroid = float(np.mean(
        librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
    ))

    # Spectral bandwidth (how spread the frequencies are)
    bandwidth = float(np.mean(
        librosa.feature.spectral_bandwidth(y=audio, sr=sr)[0]
    ))

    # Spectral rolloff (frequency below which 85% of energy lies)
    rolloff = float(np.mean(
        librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]
    ))

    # ── MFCC features (speech fingerprint) ─────────────────────
    mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=8)
    mfcc_means = np.mean(mfccs, axis=1).tolist()
    mfcc_vars = np.var(mfccs, axis=1).tolist()
    # Overall MFCC variance (high = speech-like variation)
    mfcc_total_var = float(np.mean(np.var(mfccs, axis=1)))

    # ── Formant band analysis ──────────────────────────────────
    # Human voice formants: F1≈500Hz, F2≈1500Hz, F3≈2500Hz
    # Calculate energy ratio in voice band vs total
    spectrum = np.abs(np.fft.rfft(audio))
    freqs = np.fft.rfftfreq(len(audio), d=1/sr)

    # Voice band energy (300-3000Hz)
    voice_band = np.sum(spectrum[(freqs >= 300) & (freqs <= 3000)])
    # Low band energy (0-300Hz) — typically machine noise
    low_band = np.sum(spectrum[(freqs < 300)])
    # Total energy
    total_energy = np.sum(spectrum) + 1e-9

    voice_ratio = float(voice_band / total_energy)
    low_ratio = float(low_band / total_energy)

    # F1 band (400-600Hz) specific energy
    f1_band = np.sum(spectrum[(freqs >= 400) & (freqs <= 600)])
    f1_ratio = float(f1_band / total_energy)

    # F2 band (1200-1800Hz) specific energy
    f2_band = np.sum(spectrum[(freqs >= 1200) & (freqs <= 1800)])
    f2_ratio = float(f2_band / total_energy)

    # Formant presence: if both F1 and F2 bands have significant energy
    formant_present = bool(f1_ratio > 0.05 and f2_ratio > 0.05)

    # ── Spectral peak analysis ─────────────────────────────────
    # Find dominant peaks in voice range (300-3000Hz)
    voice_mask = (freqs >= 300) & (freqs <= 3000)
    voice_spectrum = spectrum.copy()
    voice_spectrum[~voice_mask] = 0

    # Find top 3 peaks
    peak_indices = np.argsort(voice_spectrum)[-3:][::-1]
    peak_freqs = freqs[peak_indices].tolist()
    peak_freqs = [float(f) for f in peak_freqs if f > 0]

    return {
        "rms_energy": round(rms, 4),
        "rms_variance": round(rms_var, 6),
        "zero_crossing_rate": round(zcr, 4),
        "spectral_centroid_hz": round(centroid, 1),
        "spectral_bandwidth_hz": round(bandwidth, 1),
        "spectral_rolloff_hz": round(rolloff, 1),
        "mfcc_total_variance": round(mfcc_total_var, 2),
        "voice_band_ratio": round(voice_ratio, 4),
        "low_band_ratio": round(low_ratio, 4),
        "f1_band_ratio": round(f1_ratio, 4),
        "f2_band_ratio": round(f2_ratio, 4),
        "formant_detected": formant_present,
        "dominant_peaks_hz": [round(f, 1) for f in peak_freqs[:3]],
    }


# ═══════════════════════════════════════════════════════════════
# FEATURE TO TEXT
# ═══════════════════════════════════════════════════════════════

def features_to_text(features, chunk_label, time_range):
    """Convert numerical features to human-readable analysis text."""
    return f"""AUDIO ANALYSIS REPORT — {chunk_label} ({time_range})

Measured acoustic features:
  Energy:
    RMS energy: {features['rms_energy']:.4f} (scale 0-1, loud if >0.3)
    Energy variance: {features['rms_variance']:.6f} (high = bursting/changing sound, low = steady)

  Frequency profile:
    Spectral centroid: {features['spectral_centroid_hz']:.0f} Hz (human speech: 500-2000Hz, machines: <500Hz or >3000Hz)
    Spectral bandwidth: {features['spectral_bandwidth_hz']:.0f} Hz (narrow = tonal/machine, wide = speech/noise)
    Spectral rolloff: {features['spectral_rolloff_hz']:.0f} Hz

  Speech indicators:
    Zero-crossing rate: {features['zero_crossing_rate']:.4f} (speech: 0.05-0.15, noise: >0.2)
    MFCC total variance: {features['mfcc_total_variance']:.2f} (speech: high variance, machine: low variance)

  Formant analysis (critical for human voice detection):
    Voice band (300-3000Hz) energy ratio: {features['voice_band_ratio']:.4f} (speech: >0.5)
    Low band (<300Hz) energy ratio: {features['low_band_ratio']:.4f} (machines: >0.5)
    F1 band (400-600Hz) ratio: {features['f1_band_ratio']:.4f} (human F1 formant if >0.05)
    F2 band (1200-1800Hz) ratio: {features['f2_band_ratio']:.4f} (human F2 formant if >0.05)
    Formant bands detected: {'YES — both F1 and F2 present' if features['formant_detected'] else 'NO — missing formant structure'}
    Dominant frequency peaks: {', '.join(f'{f:.0f}Hz' for f in features['dominant_peaks_hz'])}"""


# ═══════════════════════════════════════════════════════════════
# PROMPT
# ═══════════════════════════════════════════════════════════════

FEATURE_PROMPT = """You are an industrial acoustic safety classifier.
You will receive NUMERICAL FEATURES extracted from a 5-second audio recording
at a wastewater treatment plant. Your task: determine if human voice is present.

DECISION RULES:
- Human voice has BOTH F1 (400-600Hz) AND F2 (1200-1800Hz) formant energy
- Human speech has moderate ZCR (0.05-0.15) and HIGH MFCC variance
- Machine noise has LOW MFCC variance and often HIGH low-band ratio (>0.5)
- Construction noise has HIGH ZCR (>0.2) and WIDE bandwidth but NO formant structure
- If formant_detected is NO → almost certainly not human voice
- If formant_detected is YES AND MFCC variance is high → likely human voice

Respond ONLY with JSON:
{
    "human_detected": true/false,
    "confidence": 0.0-1.0,
    "distress_type": "none/shouting_help/screaming/muffled_call",
    "alarm": true/false,
    "reasoning": "which features led to this decision"
}"""


# ═══════════════════════════════════════════════════════════════
# MODEL CALL
# ═══════════════════════════════════════════════════════════════

def send_text_to_model(prompt_text, model=MODEL):
    """Send pure text to model — no audio, no images."""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt_text}],
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 512,
        }
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        msg = data.get("message", {})
        content = msg.get("content", "")
        thinking = msg.get("thinking", "")
        return content if content.strip() else thinking
    except Exception as e:
        return f"ERROR: {e}"


def parse_json(raw):
    """Extract JSON from response."""
    import re
    matches = list(re.finditer(r'\{[^{}]*\}', raw, re.DOTALL))
    if matches:
        for match in reversed(matches):
            try:
                return json.loads(match.group()), "ok"
            except json.JSONDecodeError:
                continue
    return {"raw": raw[:300]}, "parse_error"


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 70)
    print("  FEATURE-TEXT POC TEST")
    print("  Can Gemma 4 detect human voice from numerical features?")
    print("=" * 70)
    print(f"  Model: {MODEL}")
    print(f"  Method: Audio → librosa features → Text → LLM reasoning")
    print(f"  No audio sent. No images sent. Pure text inference.")
    print("=" * 70)

    results = []
    correct = 0
    total = 0

    for label, filename, start_sec, has_human, desc in TEST_CHUNKS:
        filepath = os.path.join(AUDIO_DIR, filename)
        if not os.path.exists(filepath):
            print(f"\n  [SKIP] {filename} not found")
            continue

        time_range = f"{start_sec}-{start_sec + CHUNK_SEC}s"

        print(f"\n  {'─' * 65}")
        print(f"  {label} | {time_range} | {desc}")
        print(f"  Ground truth: {'HUMAN' if has_human else 'NO HUMAN'}")
        print(f"  {'─' * 65}")

        # Step 1: Extract features
        features = extract_features(filepath, start_sec)

        # Print key features
        print(f"  Features:")
        print(f"    RMS: {features['rms_energy']:.4f} | "
              f"ZCR: {features['zero_crossing_rate']:.4f} | "
              f"Centroid: {features['spectral_centroid_hz']:.0f}Hz")
        print(f"    Voice ratio: {features['voice_band_ratio']:.4f} | "
              f"Low ratio: {features['low_band_ratio']:.4f} | "
              f"MFCC var: {features['mfcc_total_variance']:.2f}")
        print(f"    F1 ratio: {features['f1_band_ratio']:.4f} | "
              f"F2 ratio: {features['f2_band_ratio']:.4f} | "
              f"Formant: {'YES' if features['formant_detected'] else 'NO'}")
        print(f"    Peaks: {features['dominant_peaks_hz']}")

        # Step 2: Convert to text
        feature_text = features_to_text(features, label, time_range)

        # Step 3: Build full prompt
        full_prompt = FEATURE_PROMPT + "\n\n" + feature_text

        # Step 4: Send to model (pure text, no audio/image)
        print(f"  Sending to model (text only)...")
        t0 = time.time()
        raw = send_text_to_model(full_prompt)
        elapsed = time.time() - t0

        # Step 5: Parse response
        parsed, status = parse_json(raw)

        alarm = parsed.get("alarm", False)
        conf = parsed.get("confidence", 0.0)
        dtype = parsed.get("distress_type", "?")
        reason = parsed.get("reasoning", "?")
        detected = parsed.get("human_detected", False)

        # Check correctness
        is_correct = (detected == has_human)
        total += 1
        if is_correct:
            correct += 1

        flag = "🚨 ALARM" if alarm else "   ----"
        verdict = "✅ CORRECT" if is_correct else "❌ WRONG"

        print(f"  {flag} | conf:{conf:.2f} | {dtype} | {verdict}")
        print(f"  Reasoning: {str(reason)[:150]}")
        print(f"  Time: {elapsed:.1f}s | Parse: {status}")

        results.append({
            "label": label,
            "has_human": has_human,
            "detected": detected,
            "alarm": alarm,
            "confidence": conf,
            "correct": is_correct,
            "elapsed": elapsed,
            "features": features,
        })

    # Summary
    print(f"\n{'=' * 70}")
    print(f"  SUMMARY: {correct}/{total} correct ({100*correct/total:.0f}%)")
    print(f"{'=' * 70}")

    print(f"\n  {'Label':<12} {'Truth':<10} {'Model':<10} {'Conf':<8} {'Result':<10}")
    print(f"  {'─'*50}")
    for r in results:
        truth = "HUMAN" if r["has_human"] else "NO HUMAN"
        model_says = "HUMAN" if r["detected"] else "NO HUMAN"
        verdict = "✅" if r["correct"] else "❌"
        print(f"  {r['label']:<12} {truth:<10} {model_says:<10} {r['confidence']:<8.2f} {verdict}")

    avg_time = np.mean([r["elapsed"] for r in results])
    print(f"\n  Average inference time: {avg_time:.1f}s per chunk")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()

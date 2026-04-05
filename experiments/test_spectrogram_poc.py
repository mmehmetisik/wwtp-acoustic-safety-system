"""
Spectrogram Proof-of-Concept Test
==================================
Quick test: Can Gemma 4 detect human voice from a spectrogram image
better than from raw audio?

This sends the critical S5 chunk (25-30s, drowning scream) as a
mel spectrogram image to the model via Ollama's vision API.

Usage:
    python test_spectrogram_poc.py

Requires: librosa, matplotlib, requests, soundfile
"""

import numpy as np
import librosa
import librosa.display
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import soundfile as sf
import requests
import base64
import json
import time
import io
import os


# ── Settings ──────────────────────────────────────────────────
OLLAMA_URL  = "http://localhost:11434/api/chat"
MODEL       = "gemma4:e4b"
SR          = 16000
CHUNK_SEC   = 5
AUDIO_DIR   = os.path.join("dataset", "audio")

# Test chunks: scene, file, chunk_start_sec, description
TEST_CHUNKS = [
    ("S1", "S1_pump_room_normal.wav", 15, "Pump room - NO human (should be clean)"),
    ("S2", "S2_construction_human.wav", 30, "Construction + shouting (human present)"),
    ("S3", "S3_pool_false_alarm.wav", 25, "Metallic sounds - NO human (deceptive)"),
    ("S4", "S4_manhole_masked.wav", 25, "Underground + masked voice (human present)"),
    ("S5", "S5_pool_critical.wav", 25, "Drowning scream in construction (CRITICAL)"),
]


def audio_chunk_to_spectrogram_b64(filepath, start_sec, duration_sec=CHUNK_SEC, sr=SR):
    """
    Load audio chunk → mel spectrogram → PNG image → base64 string.
    
    This is the core conversion: audio becomes a visual representation
    that the model's vision system can analyze.
    """
    # Load audio chunk
    audio, _ = sf.read(filepath, start=start_sec * sr, 
                       stop=(start_sec + duration_sec) * sr)
    audio = audio.astype(np.float32)
    
    # Generate mel spectrogram
    S = librosa.feature.melspectrogram(
        y=audio, sr=sr, 
        n_mels=128,          # 128 mel bands (standard)
        fmax=8000,           # up to 8kHz
        hop_length=256,      # good time resolution
        n_fft=1024,          # good frequency resolution
    )
    S_dB = librosa.power_to_db(S, ref=np.max)
    
    # Create spectrogram image
    fig, ax = plt.subplots(1, 1, figsize=(10, 4), dpi=100)
    librosa.display.specshow(
        S_dB, sr=sr, hop_length=256,
        x_axis='time', y_axis='mel',
        ax=ax, cmap='magma'
    )
    ax.set_title(f'Mel Spectrogram ({start_sec}-{start_sec+duration_sec}s)')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Frequency (Hz)')
    plt.colorbar(ax.collections[0], ax=ax, format='%+2.0f dB')
    plt.tight_layout()
    
    # Save to PNG in memory → base64
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    
    return img_b64


def send_spectrogram_to_model(img_b64, prompt, model=MODEL):
    """
    Send spectrogram image to Gemma 4 via Ollama chat API.
    
    Uses /api/chat with messages format — more reliable for multimodal.
    """
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": [img_b64],
            }
        ],
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 1024,
        }
    }
    
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        msg = data.get("message", {})
        # Gemma 4 may put response in content OR thinking field
        content = msg.get("content", "")
        thinking = msg.get("thinking", "")
        # Prefer content, fall back to thinking
        result = content if content.strip() else thinking
        if not result:
            return f"EMPTY: {json.dumps(data)[:300]}"
        return result
    except Exception as e:
        return f"ERROR: {e}"


def parse_json_response(raw):
    """Extract JSON from model response."""
    import re
    # Try to find JSON in response
    json_match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group()), "ok"
        except json.JSONDecodeError:
            pass
    return {"error": "no_json", "raw": raw[:200]}, "parse_error"


# ── Prompt ────────────────────────────────────────────────────
SPECTROGRAM_PROMPT = """Look at this mel spectrogram image from an industrial plant microphone.

Your task: Is there human voice in this spectrogram?

How to read it:
- Human voice = horizontal formant bands with syllable rhythm (short bursts with gaps)
- Machine noise = steady horizontal lines, vertical streaks, or uniform energy
- If you see formant patterns typical of speech = human_detected: true, alarm: true
- If you see only machine patterns = human_detected: false, alarm: false

confidence means how sure you are that HUMAN VOICE IS PRESENT:
- 0.8+ = I clearly see speech formants
- 0.4-0.7 = I see something that might be voice
- 0.0-0.3 = I see only machine noise, no voice

Respond ONLY with this JSON, nothing else:
{
    "human_detected": true or false,
    "confidence": 0.0 to 1.0,
    "distress_type": "none" or "shouting_help" or "muffled_call" or "screaming",
    "alarm": true or false,
    "reasoning": "what patterns you see"
}"""


def main():
    print("\n" + "=" * 65)
    print("  SPECTROGRAM PROOF-OF-CONCEPT TEST")
    print("  Can Gemma 4 detect human voice from spectrogram images?")
    print("=" * 65)
    print(f"  Model: {MODEL}")
    print(f"  Method: Audio → Mel Spectrogram → Image → Vision API")
    print("=" * 65)
    
    # Also save spectrograms as files for visual inspection
    os.makedirs("spectrogram_test", exist_ok=True)
    
    for scene_id, filename, start_sec, desc in TEST_CHUNKS:
        filepath = os.path.join(AUDIO_DIR, filename)
        
        if not os.path.exists(filepath):
            print(f"\n  [SKIP] {filename} not found")
            continue
        
        print(f"\n  {'─' * 60}")
        print(f"  {scene_id} | {start_sec}-{start_sec+CHUNK_SEC}s | {desc}")
        print(f"  {'─' * 60}")
        
        # Generate spectrogram
        print(f"  Generating spectrogram...")
        img_b64 = audio_chunk_to_spectrogram_b64(filepath, start_sec)
        
        # Save spectrogram image for visual inspection
        img_data = base64.b64decode(img_b64)
        img_path = f"spectrogram_test/{scene_id}_chunk_{start_sec}s.png"
        with open(img_path, 'wb') as f:
            f.write(img_data)
        print(f"  Saved: {img_path}")
        
        # Send to model
        print(f"  Sending to {MODEL}...")
        t0 = time.time()
        raw_response = send_spectrogram_to_model(img_b64, SPECTROGRAM_PROMPT)
        elapsed = time.time() - t0
        
        # Parse response
        parsed, status = parse_json_response(raw_response)
        
        # Display results
        alarm = parsed.get("alarm", False)
        conf  = parsed.get("confidence", 0.0)
        dtype = parsed.get("distress_type", "?")
        reason = parsed.get("reasoning", "?")
        
        alarm_flag = "🚨 ALARM" if alarm else "   ----"
        
        print(f"  {alarm_flag} | conf:{conf:.2f} | {dtype}")
        print(f"  Reasoning: {reason[:120]}")
        print(f"  Time: {elapsed:.1f}s | Parse: {status}")
        
        if status == "parse_error":
            print(f"  Raw (first 300): {raw_response[:300]}")
    
    print(f"\n{'=' * 65}")
    print(f"  Test complete. Check spectrogram_test/ for images.")
    print(f"  Compare visually: can YOU see human voice in the spectrogram?")
    print(f"{'=' * 65}\n")


if __name__ == "__main__":
    main()

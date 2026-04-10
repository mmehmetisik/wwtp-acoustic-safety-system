#!/usr/bin/env python3
"""
WWTP Acoustic Safety System — Live Microphone Detector
=======================================================
Real-time audio monitoring using system microphone.
Captures 5-second chunks, generates mel spectrograms,
sends to Gemma 4 E4B via Ollama for human voice detection.

Usage:
    python live_detector.py
    python live_detector.py --model gemma4:e2b
    python live_detector.py --device 1 --chunk-size 5 --threshold 0.50

Requirements:
    - Ollama running locally (ollama serve)
    - Gemma 4 E4B model pulled (ollama pull gemma4:e4b)
    - Microphone access permission

Author: Mehmet ISIK — Adana ASKI
"""

import os
import sys
import json
import time
import base64
import io
import argparse
import urllib.request
from datetime import datetime

import numpy as np
import sounddevice as sd
import librosa
import librosa.display
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False

# ═══════════════════════════════════════════════════════════════
# SETTINGS (copied from acoustic_engine.py — frozen configuration)
# ═══════════════════════════════════════════════════════════════

OLLAMA_URL       = "http://localhost:11434/api/chat"
OLLAMA_MODEL     = "gemma4:e4b"
OLLAMA_TIMEOUT   = 180
OLLAMA_TEMP      = 0.0
SAMPLE_RATE      = 16000
CHUNK_SIZE_SEC   = 5
RETRY_LIMIT      = 3
RETRY_DELAY_SEC  = 5
AUDIO_DIR        = os.path.join(os.path.dirname(__file__), "dataset", "audio")
LOG_DIR          = os.path.join(os.path.dirname(__file__), "logs")


# ═══════════════════════════════════════════════════════════════
# SPECTROGRAM GENERATION
# ═══════════════════════════════════════════════════════════════

def audio_to_spectrogram_b64(audio_array, sr=SAMPLE_RATE, chunk_label="LIVE"):
    """
    Convert numpy audio array to mel spectrogram PNG → base64.
    Same settings as acoustic_engine.py: 300-3000Hz, 128 mel bands,
    power_to_db, magma colormap.
    """
    try:
        audio = audio_array.astype(np.float32)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)  # stereo → mono

        S = librosa.feature.melspectrogram(
            y=audio, sr=sr, n_mels=128,
            fmin=300, fmax=3000,
            hop_length=256, n_fft=1024,
        )
        S_dB = librosa.power_to_db(S, ref=np.max)

        fig, ax = plt.subplots(1, 1, figsize=(10, 4), dpi=100)
        librosa.display.specshow(
            S_dB, sr=sr, hop_length=256,
            x_axis='time', y_axis='mel', ax=ax, cmap='magma',
            fmin=300, fmax=3000,
        )
        ax.set_title(f'Voice-Range Spectrogram [{chunk_label}] [300-3000Hz]')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Frequency (Hz)')
        plt.colorbar(ax.collections[0], ax=ax, format='%+2.0f dB')
        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')

    except Exception as e:
        print(f"  [ERROR] Spectrogram generation failed: {e}")
        return None


def generate_spectrogram_from_file(filepath, chunk_idx, sr=SAMPLE_RATE):
    """Generate spectrogram from WAV file chunk (for few-shot examples)."""
    import soundfile as sf
    try:
        start_sample = chunk_idx * CHUNK_SIZE_SEC * sr
        stop_sample = start_sample + CHUNK_SIZE_SEC * sr
        audio, _ = sf.read(filepath, start=start_sample, stop=stop_sample)
        audio = audio.astype(np.float32)

        S = librosa.feature.melspectrogram(
            y=audio, sr=sr, n_mels=128,
            fmin=300, fmax=3000,
            hop_length=256, n_fft=1024,
        )
        S_dB = librosa.power_to_db(S, ref=np.max)

        start_sec = chunk_idx * CHUNK_SIZE_SEC
        end_sec = start_sec + CHUNK_SIZE_SEC

        fig, ax = plt.subplots(1, 1, figsize=(10, 4), dpi=100)
        librosa.display.specshow(
            S_dB, sr=sr, hop_length=256,
            x_axis='time', y_axis='mel', ax=ax, cmap='magma',
            fmin=300, fmax=3000,
        )
        ax.set_title(f'Voice-Range Spectrogram ({start_sec}-{end_sec}s) [300-3000Hz]')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Frequency (Hz)')
        plt.colorbar(ax.collections[0], ax=ax, format='%+2.0f dB')
        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')

    except Exception as e:
        print(f"  [ERROR] Few-shot spectrogram failed: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# FEW-SHOT EXAMPLES
# ═══════════════════════════════════════════════════════════════

def generate_fewshot_examples(audio_dir=AUDIO_DIR):
    """
    Generate 3 clean + 1 human reference spectrograms.
    Same examples as acoustic_engine.py.
    """
    print("  Generating few-shot reference spectrograms...")

    clean1 = generate_spectrogram_from_file(
        os.path.join(audio_dir, "S1_pump_room_normal.wav"), 3)
    if clean1:
        print("    [OK] Clean 1: S1 pump room (15-20s)")
    else:
        return None

    clean2 = generate_spectrogram_from_file(
        os.path.join(audio_dir, "S2_construction_human.wav"), 0)
    if clean2:
        print("    [OK] Clean 2: S2 construction noise (0-5s)")
    else:
        return None

    clean3 = generate_spectrogram_from_file(
        os.path.join(audio_dir, "S3_pool_false_alarm.wav"), 0)
    if clean3:
        print("    [OK] Clean 3: S3 metallic sounds (0-5s)")
    else:
        return None

    human1 = generate_spectrogram_from_file(
        os.path.join(audio_dir, "S4_manhole_masked.wav"), 5)
    if human1:
        print("    [OK] Human 1: S4 masked voice (25-30s)")
    else:
        return None

    return {
        'clean': (clean1, clean2, clean3),
        'human': human1,
    }


# ═══════════════════════════════════════════════════════════════
# OLLAMA API — SPECTROGRAM ANALYSIS
# ═══════════════════════════════════════════════════════════════

def analyze_spectrogram(spectrogram_b64, fewshot, chunk_num, model=OLLAMA_MODEL):
    """
    Send spectrogram to Ollama with few-shot CoT prompt.
    Same prompt structure as acoustic_engine.py.
    """
    c1, c2, c3 = fewshot['clean']
    h1 = fewshot['human']

    messages = [
        # Example 1: Clean — pump room
        {
            "role": "user",
            "content": (
                "I will show you voice-range spectrograms (300-3000Hz) from an industrial plant. "
                "Your job: detect human voice.\n\n"
                "EXAMPLE 1 - NO HUMAN (pump room):\n"
                "This shows only machine noise. Low energy, no clear patterns."
            ),
            "images": [c1],
        },
        {
            "role": "assistant",
            "content": json.dumps({
                "human_detected": False, "confidence": 0.1,
                "distress_type": "none", "alarm": False,
                "action": "CONTINUE_MONITORING", "notify": [],
                "reasoning": "Only low-level machine noise, no voice formants"
            })
        },
        # Example 2: Clean — construction noise
        {
            "role": "user",
            "content": (
                "EXAMPLE 2 - NO HUMAN (construction noise):\n"
                "This shows broadband construction noise. Energy is spread widely "
                "but there are NO curved formant bands. This is NOT human voice."
            ),
            "images": [c2],
        },
        {
            "role": "assistant",
            "content": json.dumps({
                "human_detected": False, "confidence": 0.1,
                "distress_type": "none", "alarm": False,
                "action": "CONTINUE_MONITORING", "notify": [],
                "reasoning": "Broadband construction noise, no speech formant curves"
            })
        },
        # Example 3: Clean — metallic sounds
        {
            "role": "user",
            "content": (
                "EXAMPLE 3 - NO HUMAN (metallic sounds):\n"
                "This shows metallic impacts and scraping. Vertical spikes and "
                "scattered energy. This is NOT human voice — no formant curves."
            ),
            "images": [c3],
        },
        {
            "role": "assistant",
            "content": json.dumps({
                "human_detected": False, "confidence": 0.1,
                "distress_type": "none", "alarm": False,
                "action": "CONTINUE_MONITORING", "notify": [],
                "reasoning": "Metallic impacts and scraping, no speech patterns"
            })
        },
        # Example 4: Human voice
        {
            "role": "user",
            "content": (
                "EXAMPLE - HUMAN VOICE PRESENT:\n"
                "This shows human voice. See the curved horizontal formant bands "
                "between 500-2000Hz. They appear as bright curved lines with "
                "syllable rhythm. Machine noise NEVER has these curved patterns."
            ),
            "images": [h1],
        },
        {
            "role": "assistant",
            "content": json.dumps({
                "human_detected": True, "confidence": 0.85,
                "distress_type": "muffled_call", "alarm": True,
                "action": "INITIATE_CONFINED_SPACE_RESCUE", "notify": [],
                "reasoning": "Clear speech formant curves at 500-2000Hz"
            })
        },
        # Target chunk
        {
            "role": "user",
            "content": (
                f"[LIVE CHUNK {chunk_num} | Time: {datetime.now().strftime('%H:%M:%S')}]\n"
                f"CLASSIFY THIS SPECTROGRAM. Follow these steps IN ORDER:\n\n"
                f"Step 1: Are there VERTICAL bright lines or spikes? "
                f"If yes, these are metallic impacts or mechanical transients — NOT human voice.\n\n"
                f"Step 2: Are there CURVED or SLANTED horizontal bands between 500-2000Hz "
                f"that look like stacked arches or stairs? These are speech formants.\n\n"
                f"Step 3: ONLY if you see the curved/stacked formant pattern from Step 2, "
                f"AND those patterns are NOT just vertical spikes from Step 1, "
                f"set human_detected=true and alarm=true.\n\n"
                f"If you see only scattered energy, vertical spikes, or flat bands "
                f"→ human_detected=false, alarm=false.\n\n"
                f"Respond ONLY with JSON:"
            ),
            "images": [spectrogram_b64],
        },
    ]

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {
            "temperature": OLLAMA_TEMP,
            "num_predict": 512,
        },
    }

    payload_bytes = json.dumps(payload).encode('utf-8')

    for attempt in range(RETRY_LIMIT):
        try:
            req = urllib.request.Request(
                OLLAMA_URL,
                data=payload_bytes,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                msg = result.get("message", {})
                content = msg.get("content", "")
                thinking = msg.get("thinking", "")
                return content if content.strip() else thinking

        except Exception as e:
            if attempt < RETRY_LIMIT - 1:
                print(f"    [RETRY {attempt + 1}] {e}")
                time.sleep(RETRY_DELAY_SEC)
            else:
                print(f"    [FAILED] {e}")
                return None

    return None


def parse_model_response(raw_response):
    """Parse JSON from model response, handling markdown code blocks."""
    if not raw_response:
        return None
    try:
        text = raw_response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON from mixed content
        import re
        match = re.search(r'\{[^}]+\}', raw_response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return None


# ═══════════════════════════════════════════════════════════════
# DISPLAY
# ═══════════════════════════════════════════════════════════════

def print_banner():
    """Print startup banner."""
    print("\n" + "=" * 65)
    print("  WWTP ACOUSTIC SAFETY SYSTEM — LIVE DETECTOR")
    print("  Real-time microphone monitoring with Gemma 4 E4B")
    print("=" * 65)


def print_result(chunk_num, result, elapsed, threshold):
    """Print analysis result with colors."""
    if result is None:
        print(f"\n  Chunk {chunk_num:03d} | [ERROR] No response from model")
        return False

    conf = result.get("confidence", 0)
    alarm = result.get("alarm", False)
    action = result.get("action", "UNKNOWN")
    dtype = result.get("distress_type", "none")
    reasoning = result.get("reasoning", "")

    is_alarm = alarm and conf >= threshold

    if HAS_COLOR:
        if is_alarm:
            print(f"\n{Back.RED}{Fore.WHITE}{Style.BRIGHT}" + " " * 65)
            print(f"  CHUNK {chunk_num:03d} | ALARM — HUMAN DISTRESS DETECTED")
            print(f"  Confidence: {conf:.0%} | Type: {dtype}")
            print(f"  Action: {action}")
            print(f"  Reasoning: {reasoning}")
            print(f"  Analysis time: {elapsed:.1f}s")
            print(" " * 65 + f"{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.GREEN}{Style.BRIGHT}"
                  f"  Chunk {chunk_num:03d} | SAFE — CONTINUE MONITORING"
                  f"{Style.RESET_ALL}")
            print(f"  Confidence: {conf:.0%} | Time: {elapsed:.1f}s | {reasoning}")
    else:
        if is_alarm:
            print(f"\n  !!! CHUNK {chunk_num:03d} | ALARM — HUMAN DISTRESS DETECTED !!!")
            print(f"  Confidence: {conf:.0%} | Type: {dtype}")
            print(f"  Action: {action}")
            print(f"  Reasoning: {reasoning}")
            print(f"  Analysis time: {elapsed:.1f}s")
        else:
            print(f"\n  Chunk {chunk_num:03d} | SAFE — Confidence: {conf:.0%} | Time: {elapsed:.1f}s")

    return is_alarm


def print_summary(stats):
    """Print session summary."""
    print("\n" + "=" * 65)
    print("  SESSION SUMMARY")
    print("=" * 65)
    print(f"  Total chunks analyzed:  {stats['total']}")
    print(f"  Alarms triggered:       {stats['alarms']}")
    print(f"  Safe chunks:            {stats['total'] - stats['alarms']}")
    if stats['total'] > 0:
        avg_conf = stats['total_conf'] / stats['total']
        print(f"  Average confidence:     {avg_conf:.0%}")
        print(f"  Average analysis time:  {stats['total_time'] / stats['total']:.1f}s")
    print(f"  Session duration:       {stats['duration']:.0f}s")
    print(f"  Model:                  {stats['model']}")
    print("=" * 65 + "\n")


# ═══════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════

def init_log(log_dir=LOG_DIR):
    """Create log directory and return log file path."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(log_dir, f"live_session_{timestamp}.jsonl")


def log_result(log_path, chunk_num, result, elapsed):
    """Append result to JSONL log file."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "chunk": chunk_num,
        "elapsed_sec": round(elapsed, 2),
        "result": result,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ═══════════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="WWTP Acoustic Safety System — Live Microphone Detector"
    )
    parser.add_argument("--device", type=int, default=None,
                        help="Microphone device index (use --list-devices to see options)")
    parser.add_argument("--list-devices", action="store_true",
                        help="List available audio input devices and exit")
    parser.add_argument("--duration", type=int, default=0,
                        help="Total listening duration in seconds (0 = unlimited)")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE_SEC,
                        help=f"Chunk duration in seconds (default: {CHUNK_SIZE_SEC})")
    parser.add_argument("--model", type=str, default=OLLAMA_MODEL,
                        help=f"Ollama model name (default: {OLLAMA_MODEL})")
    parser.add_argument("--threshold", type=float, default=0.50,
                        help="Alarm confidence threshold (default: 0.50)")
    args = parser.parse_args()

    # List devices mode
    if args.list_devices:
        print("\n  Available audio input devices:\n")
        devices = sd.query_devices()
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                marker = " <-- DEFAULT" if i == sd.default.device[0] else ""
                print(f"  [{i}] {d['name']} (channels: {d['max_input_channels']}, "
                      f"rate: {int(d['default_samplerate'])}Hz){marker}")
        print()
        return

    # ── Startup ──
    print_banner()
    model = args.model
    chunk_sec = args.chunk_size
    threshold = args.threshold

    print(f"\n  Model:          {model}")
    print(f"  Chunk size:     {chunk_sec}s")
    print(f"  Sample rate:    {SAMPLE_RATE} Hz")
    print(f"  Threshold:      {threshold}")
    print(f"  Duration:       {'Unlimited' if args.duration == 0 else f'{args.duration}s'}")

    # Check microphone
    try:
        device_info = sd.query_devices(args.device or sd.default.device[0], 'input')
        print(f"  Microphone:     {device_info['name']}")
    except Exception as e:
        print(f"\n  [ERROR] Cannot access microphone: {e}")
        print("  Make sure microphone permission is granted.")
        print("  Use --list-devices to see available devices.")
        sys.exit(1)

    # Check Ollama
    print(f"\n  Checking Ollama connection...")
    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/tags",
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            models = [m['name'] for m in data.get('models', [])]
            if model in models or any(model in m for m in models):
                print(f"    [OK] Model '{model}' available")
            else:
                print(f"    [WARNING] Model '{model}' not found. Available: {models}")
                print(f"    Run: ollama pull {model}")
                sys.exit(1)
    except Exception as e:
        print(f"    [ERROR] Cannot connect to Ollama: {e}")
        print("    Make sure Ollama is running: ollama serve")
        sys.exit(1)

    # Warmup — load model into GPU before listening
    print(f"\n  Warming up model... (this may take 30-60s on first run)")
    try:
        warmup_payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": "hello"}],
            "stream": False,
            "options": {"num_predict": 1},
        }).encode('utf-8')
        warmup_req = urllib.request.Request(
            OLLAMA_URL,
            data=warmup_payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        t0 = time.time()
        with urllib.request.urlopen(warmup_req, timeout=OLLAMA_TIMEOUT) as resp:
            resp.read()
        warmup_time = time.time() - t0
        print(f"    [OK] Model loaded and ready ({warmup_time:.1f}s)")
    except Exception as e:
        print(f"    [WARNING] Warmup failed: {e}")
        print(f"    First chunk may be slower than usual.")

    # Generate few-shot examples
    print()
    fewshot = generate_fewshot_examples()
    if fewshot is None:
        print("  [ERROR] Failed to generate few-shot examples.")
        print("  Make sure dataset/audio/ contains the WAV files.")
        sys.exit(1)
    print("    [OK] Few-shot examples ready\n")

    # Init logging
    log_path = init_log()
    print(f"  Logging to: {log_path}")

    # ── Main loop ──
    print(f"\n  {'=' * 55}")
    print(f"  LISTENING... (Ctrl+C to stop)")
    print(f"  {'=' * 55}")
    print(f"  First chunk may take ~25s (model loading).\n")

    stats = {
        'total': 0, 'alarms': 0,
        'total_conf': 0.0, 'total_time': 0.0,
        'duration': 0, 'model': model,
    }
    session_start = time.time()
    chunk_num = 0

    try:
        while True:
            # Check duration limit
            elapsed_session = time.time() - session_start
            if args.duration > 0 and elapsed_session >= args.duration:
                print(f"\n  Duration limit reached ({args.duration}s). Stopping.")
                break

            chunk_num += 1
            now = datetime.now().strftime("%H:%M:%S")
            print(f"\n  [{now}] Recording chunk {chunk_num} ({chunk_sec}s)...", end="", flush=True)

            # Record audio
            audio = sd.rec(
                int(chunk_sec * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype='float32',
                device=args.device,
            )
            sd.wait()  # Block until recording is done
            audio = audio.flatten()
            print(" done.", flush=True)

            # Check if audio is too quiet (silence detection)
            rms = np.sqrt(np.mean(audio ** 2))
            if rms < 1e-6:
                print(f"  [WARNING] Very low audio level (RMS={rms:.8f}). Check microphone.")

            # Generate spectrogram
            print(f"  Generating spectrogram...", end="", flush=True)
            spec_b64 = audio_to_spectrogram_b64(
                audio, sr=SAMPLE_RATE,
                chunk_label=f"LIVE #{chunk_num} {now}"
            )
            if spec_b64 is None:
                print(" failed.")
                continue
            print(" done.", flush=True)

            # Send to model
            print(f"  Analyzing with {model}...", end="", flush=True)
            t0 = time.time()
            raw = analyze_spectrogram(spec_b64, fewshot, chunk_num, model=model)
            elapsed = time.time() - t0
            print(f" {elapsed:.1f}s", flush=True)

            # Parse result
            result = parse_model_response(raw)

            # Display
            is_alarm = print_result(chunk_num, result, elapsed, threshold)

            # Alarm sound
            if is_alarm:
                try:
                    import winsound
                    winsound.Beep(1000, 500)  # 1kHz for 500ms
                except Exception:
                    print('\a')  # Terminal bell fallback

            # Stats
            stats['total'] += 1
            if result:
                stats['total_conf'] += result.get('confidence', 0)
                if is_alarm:
                    stats['alarms'] += 1
            stats['total_time'] += elapsed

            # Log
            log_result(log_path, chunk_num, result, elapsed)

    except KeyboardInterrupt:
        print(f"\n\n  Stopped by user (Ctrl+C).")

    # Summary
    stats['duration'] = time.time() - session_start
    print_summary(stats)
    print(f"  Log saved: {log_path}\n")


if __name__ == "__main__":
    main()

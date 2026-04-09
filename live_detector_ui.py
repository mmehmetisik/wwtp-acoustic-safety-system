#!/usr/bin/env python3
"""
WWTP Acoustic Safety System — Live Detector Web UI
====================================================
SCADA-style web interface for real-time acoustic monitoring.
Single command: python live_detector_ui.py → browser opens automatically.

Uses the same spectrogram + CoT + Ollama pipeline as acoustic_engine.py.
Does NOT modify live_detector.py or acoustic_engine.py.

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
import threading
import webbrowser
from datetime import datetime

import numpy as np
import sounddevice as sd
import librosa
import librosa.display
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import uvicorn

# ═══════════════════════════════════════════════════════════════
# SETTINGS (same as acoustic_engine.py — frozen config)
# ═══════════════════════════════════════════════════════════════

OLLAMA_URL      = "http://localhost:11434/api/chat"
OLLAMA_MODEL    = "gemma4:e4b"
OLLAMA_TIMEOUT  = 180
OLLAMA_TEMP     = 0.0
SAMPLE_RATE     = 16000
CHUNK_SIZE_SEC  = 5
RETRY_LIMIT     = 3
RETRY_DELAY_SEC = 5
AUDIO_DIR       = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset", "audio")

# ═══════════════════════════════════════════════════════════════
# SPECTROGRAM (same logic as live_detector.py)
# ═══════════════════════════════════════════════════════════════

def audio_to_spectrogram_b64(audio_array, sr=SAMPLE_RATE, chunk_label="LIVE"):
    try:
        audio = audio_array.astype(np.float32)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        S = librosa.feature.melspectrogram(
            y=audio, sr=sr, n_mels=128,
            fmin=300, fmax=3000, hop_length=256, n_fft=1024,
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
        print(f"  [ERROR] Spectrogram: {e}")
        return None


def generate_spectrogram_from_file(filepath, chunk_idx, sr=SAMPLE_RATE):
    import soundfile as sf
    try:
        start_sample = chunk_idx * CHUNK_SIZE_SEC * sr
        stop_sample = start_sample + CHUNK_SIZE_SEC * sr
        audio, _ = sf.read(filepath, start=start_sample, stop=stop_sample)
        audio = audio.astype(np.float32)
        S = librosa.feature.melspectrogram(
            y=audio, sr=sr, n_mels=128,
            fmin=300, fmax=3000, hop_length=256, n_fft=1024,
        )
        S_dB = librosa.power_to_db(S, ref=np.max)
        fig, ax = plt.subplots(1, 1, figsize=(10, 4), dpi=100)
        librosa.display.specshow(
            S_dB, sr=sr, hop_length=256,
            x_axis='time', y_axis='mel', ax=ax, cmap='magma',
            fmin=300, fmax=3000,
        )
        ax.set_title(f'Reference Spectrogram [300-3000Hz]')
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
        print(f"  [ERROR] Few-shot spectrogram: {e}")
        return None


def generate_fewshot_examples(audio_dir=AUDIO_DIR):
    print("  Generating few-shot reference spectrograms...")
    c1 = generate_spectrogram_from_file(os.path.join(audio_dir, "S1_pump_room_normal.wav"), 3)
    c2 = generate_spectrogram_from_file(os.path.join(audio_dir, "S2_construction_human.wav"), 0)
    c3 = generate_spectrogram_from_file(os.path.join(audio_dir, "S3_pool_false_alarm.wav"), 0)
    h1 = generate_spectrogram_from_file(os.path.join(audio_dir, "S4_manhole_masked.wav"), 5)
    if all([c1, c2, c3, h1]):
        print("    [OK] All 4 few-shot examples ready")
        return {'clean': (c1, c2, c3), 'human': h1}
    print("    [ERROR] Failed to generate few-shot examples")
    return None


# ═══════════════════════════════════════════════════════════════
# OLLAMA API (same CoT prompt as acoustic_engine.py)
# ═══════════════════════════════════════════════════════════════

def analyze_spectrogram(spectrogram_b64, fewshot, chunk_num, model=OLLAMA_MODEL):
    c1, c2, c3 = fewshot['clean']
    h1 = fewshot['human']

    messages = [
        {"role": "user", "content": "I will show you voice-range spectrograms (300-3000Hz) from an industrial plant. Your job: detect human voice.\n\nEXAMPLE 1 - NO HUMAN (pump room):\nThis shows only machine noise. Low energy, no clear patterns.", "images": [c1]},
        {"role": "assistant", "content": json.dumps({"human_detected": False, "confidence": 0.1, "distress_type": "none", "alarm": False, "action": "CONTINUE_MONITORING", "notify": [], "reasoning": "Only low-level machine noise, no voice formants"})},
        {"role": "user", "content": "EXAMPLE 2 - NO HUMAN (construction noise):\nThis shows broadband construction noise. Energy is spread widely but there are NO curved formant bands. This is NOT human voice.", "images": [c2]},
        {"role": "assistant", "content": json.dumps({"human_detected": False, "confidence": 0.1, "distress_type": "none", "alarm": False, "action": "CONTINUE_MONITORING", "notify": [], "reasoning": "Broadband construction noise, no speech formant curves"})},
        {"role": "user", "content": "EXAMPLE 3 - NO HUMAN (metallic sounds):\nThis shows metallic impacts and scraping. Vertical spikes and scattered energy. This is NOT human voice — no formant curves.", "images": [c3]},
        {"role": "assistant", "content": json.dumps({"human_detected": False, "confidence": 0.1, "distress_type": "none", "alarm": False, "action": "CONTINUE_MONITORING", "notify": [], "reasoning": "Metallic impacts and scraping, no speech patterns"})},
        {"role": "user", "content": "EXAMPLE - HUMAN VOICE PRESENT:\nThis shows human voice. See the curved horizontal formant bands between 500-2000Hz. They appear as bright curved lines with syllable rhythm. Machine noise NEVER has these curved patterns.", "images": [h1]},
        {"role": "assistant", "content": json.dumps({"human_detected": True, "confidence": 0.85, "distress_type": "muffled_call", "alarm": True, "action": "INITIATE_CONFINED_SPACE_RESCUE", "notify": [], "reasoning": "Clear speech formant curves at 500-2000Hz"})},
        {"role": "user", "content": (
            f"[LIVE CHUNK {chunk_num} | Time: {datetime.now().strftime('%H:%M:%S')}]\n"
            f"CLASSIFY THIS SPECTROGRAM. Follow these steps IN ORDER:\n\n"
            f"Step 1: Are there VERTICAL bright lines or spikes? If yes, these are metallic impacts or mechanical transients — NOT human voice.\n\n"
            f"Step 2: Are there CURVED or SLANTED horizontal bands between 500-2000Hz that look like stacked arches or stairs? These are speech formants.\n\n"
            f"Step 3: ONLY if you see the curved/stacked formant pattern from Step 2, AND those patterns are NOT just vertical spikes from Step 1, set human_detected=true and alarm=true.\n\n"
            f"If you see only scattered energy, vertical spikes, or flat bands → human_detected=false, alarm=false.\n\n"
            f"Respond ONLY with JSON:"
        ), "images": [spectrogram_b64]},
    ]

    payload = json.dumps({
        "model": model, "messages": messages, "stream": False, "think": False,
        "options": {"temperature": OLLAMA_TEMP, "num_predict": 512},
    }).encode('utf-8')

    for attempt in range(RETRY_LIMIT):
        try:
            req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                msg = result.get("message", {})
                content = msg.get("content", "")
                thinking = msg.get("thinking", "")
                return content if content.strip() else thinking
        except Exception as e:
            if attempt < RETRY_LIMIT - 1:
                time.sleep(RETRY_DELAY_SEC)
            else:
                return None
    return None


def parse_response(raw):
    if not raw:
        return None
    try:
        text = raw.strip()
        if text.startswith("```"):
            lines = [l for l in text.split("\n") if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()
        return json.loads(text)
    except json.JSONDecodeError:
        import re
        m = re.search(r'\{[^}]+\}', raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
    return None


# ═══════════════════════════════════════════════════════════════
# WARMUP
# ═══════════════════════════════════════════════════════════════

def warmup_model(model=OLLAMA_MODEL):
    print(f"  Warming up {model}...")
    try:
        payload = json.dumps({"model": model, "messages": [{"role": "user", "content": "hello"}], "stream": False, "options": {"num_predict": 1}}).encode('utf-8')
        req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
            resp.read()
        print(f"    [OK] Model ready ({time.time()-t0:.1f}s)")
        return True
    except Exception as e:
        print(f"    [WARNING] Warmup failed: {e}")
        return False


# ═══════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════

app = FastAPI()

# Global state
state = {
    "fewshot": None,
    "model": OLLAMA_MODEL,
    "device": None,
    "chunk_size": CHUNK_SIZE_SEC,
    "threshold": 0.50,
    "running": False,
    "clients": [],
}


@app.get("/", response_class=HTMLResponse)
async def index():
    return SCADA_HTML


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    state["clients"].append(ws)
    try:
        while True:
            # Keep connection alive, listen for commands
            data = await ws.receive_text()
            cmd = json.loads(data)
            if cmd.get("action") == "start" and not state["running"]:
                state["running"] = True
                threading.Thread(target=detection_loop, daemon=True).start()
            elif cmd.get("action") == "stop":
                state["running"] = False
    except Exception:
        pass
    finally:
        if ws in state["clients"]:
            state["clients"].remove(ws)


def broadcast(msg):
    """Send message to all connected WebSocket clients."""
    dead = []
    for ws in state["clients"]:
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            loop.run_until_complete(ws.send_text(json.dumps(msg)))
            loop.close()
        except Exception:
            dead.append(ws)
    for ws in dead:
        state["clients"].remove(ws)


def terminal_log(chunk_num, is_alarm, result, elapsed, now):
    """Print colored terminal log (same style as live_detector.py)."""
    conf = result.get("confidence", 0) if result else 0
    reasoning = result.get("reasoning", "") if result else ""
    dtype = result.get("distress_type", "none") if result else "none"
    action = result.get("action", "") if result else ""

    try:
        from colorama import Fore, Back, Style
        if is_alarm:
            print(f"\n{Back.RED}{Fore.WHITE}{Style.BRIGHT}" + " " * 70)
            print(f"  CHUNK {chunk_num:03d} | ALARM — HUMAN DISTRESS DETECTED")
            print(f"  Confidence: {conf:.0%} | Type: {dtype} | Action: {action}")
            print(f"  Reasoning: {reasoning}")
            print(f"  Time: {elapsed:.1f}s | {now}")
            print(" " * 70 + f"{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.GREEN}{Style.BRIGHT}  Chunk {chunk_num:03d} | SAFE — CONTINUE MONITORING{Style.RESET_ALL}")
            print(f"  Confidence: {conf:.0%} | Time: {elapsed:.1f}s | {reasoning[:100]}")
    except ImportError:
        if is_alarm:
            print(f"\n  !!! CHUNK {chunk_num:03d} | ALARM — {dtype} | {conf:.0%} | {elapsed:.1f}s !!!")
        else:
            print(f"  Chunk {chunk_num:03d} | SAFE | {conf:.0%} | {elapsed:.1f}s")


def detection_loop():
    """Background thread: record → spectrogram → analyze → broadcast."""
    chunk_num = 0
    session_start = time.time()
    stats = {"total": 0, "alarms": 0, "total_conf": 0.0}

    broadcast({"type": "status", "message": "Starting detection loop..."})
    print("\n  " + "=" * 55)
    print("  LISTENING... (Ctrl+C to stop)")
    print("  " + "=" * 55 + "\n")

    while state["running"]:
        chunk_num += 1
        now = datetime.now().strftime("%H:%M:%S")

        # Phase 1: Recording
        broadcast({"type": "phase", "phase": "recording", "chunk": chunk_num, "time": now})
        print(f"  [{now}] Recording chunk {chunk_num} ({state['chunk_size']}s)...", end="", flush=True)
        try:
            audio = sd.rec(
                int(state["chunk_size"] * SAMPLE_RATE),
                samplerate=SAMPLE_RATE, channels=1, dtype='float32',
                device=state["device"],
            )
            sd.wait()
            audio = audio.flatten()
        except Exception as e:
            broadcast({"type": "error", "message": f"Microphone error: {e}"})
            print(f" ERROR: {e}")
            break
        print(" done.", flush=True)

        # Audio level for VU meter
        rms = float(np.sqrt(np.mean(audio ** 2)))
        peak = float(np.max(np.abs(audio)))
        broadcast({"type": "audio_level", "rms": rms, "peak": peak})

        # Phase 2: Spectrogram
        broadcast({"type": "phase", "phase": "spectrogram", "chunk": chunk_num, "time": now})
        print(f"  Generating spectrogram...", end="", flush=True)
        spec_b64 = audio_to_spectrogram_b64(audio, sr=SAMPLE_RATE, chunk_label=f"LIVE #{chunk_num} {now}")
        if spec_b64 is None:
            broadcast({"type": "error", "message": "Spectrogram generation failed"})
            print(" failed.")
            continue
        print(" done.", flush=True)

        # Phase 3: Analysis
        broadcast({"type": "phase", "phase": "analyzing", "chunk": chunk_num, "time": now})
        print(f"  Analyzing with {state['model']}...", end="", flush=True)
        t0 = time.time()
        raw = analyze_spectrogram(spec_b64, state["fewshot"], chunk_num, model=state["model"])
        elapsed = time.time() - t0
        result = parse_response(raw)
        print(f" {elapsed:.1f}s", flush=True)

        # Build result message
        is_alarm = False
        if result:
            conf = result.get("confidence", 0)
            alarm = result.get("alarm", False)
            is_alarm = alarm and conf >= state["threshold"]
            stats["total"] += 1
            stats["total_conf"] += conf
            if is_alarm:
                stats["alarms"] += 1

        # Terminal log
        terminal_log(chunk_num, is_alarm, result, elapsed, now)

        broadcast({
            "type": "result",
            "chunk": chunk_num,
            "timestamp": now,
            "is_alarm": is_alarm,
            "confidence": result.get("confidence", 0) if result else 0,
            "distress_type": result.get("distress_type", "none") if result else "none",
            "action": result.get("action", "UNKNOWN") if result else "ERROR",
            "reasoning": result.get("reasoning", "") if result else "No response",
            "spectrogram_b64": spec_b64,
            "analysis_time": round(elapsed, 1),
            "session_time": round(time.time() - session_start),
            "stats": {
                "total": stats["total"],
                "alarms": stats["alarms"],
                "avg_conf": round(stats["total_conf"] / max(1, stats["total"]) * 100),
            },
        })

    state["running"] = False
    broadcast({"type": "stopped"})

    # Terminal summary
    duration = time.time() - session_start
    print(f"\n  {'=' * 55}")
    print(f"  SESSION SUMMARY")
    print(f"  {'=' * 55}")
    print(f"  Chunks: {stats['total']} | Alarms: {stats['alarms']} | Duration: {duration:.0f}s")
    if stats['total'] > 0:
        print(f"  Avg Confidence: {stats['total_conf']/stats['total']:.0%}")
    print(f"  {'=' * 55}\n")


# ═══════════════════════════════════════════════════════════════
# SCADA HTML (inline CSS + JS)
# ═══════════════════════════════════════════════════════════════

SCADA_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WWTP.AI — Acoustic Safety System</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');
  * { margin:0; padding:0; box-sizing:border-box; }
  html, body { height:100vh; overflow:hidden; }
  body {
    font-family: 'JetBrains Mono', monospace;
    background: #080c12;
    color: #e2e8f0;
    display: flex; flex-direction: column;
    background-image:
      linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
    background-size: 40px 40px;
  }
  /* Alarm screen pulse */
  .alarm-pulse { animation: screen-pulse 1.2s infinite; }
  @keyframes screen-pulse {
    0%,100% { box-shadow: inset 0 0 0 0 transparent; }
    50% { box-shadow: inset 0 0 60px rgba(255,51,85,0.06); }
  }

  /* Top bar */
  .topbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 16px; background: rgba(8,12,18,0.95);
    border-bottom: 1px solid rgba(255,255,255,0.04);
    height: 44px; flex-shrink: 0; backdrop-filter: blur(8px);
  }
  .topbar .left { display: flex; align-items: center; gap: 10px; }
  .topbar .dot { width: 8px; height: 8px; border-radius: 50%; background: #00e6b4; animation: pulse-dot 2s infinite; }
  .topbar .dot.inactive { background: #475569; animation: none; }
  @keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:0.3} }
  .topbar .logo { font-size: 13px; font-weight: 700; letter-spacing: 3px; color: #fff; }
  .topbar .logo-sub { font-size: 9px; font-weight: 400; color: rgba(255,255,255,0.25); letter-spacing: 1px; margin-left: 6px; }
  .topbar .clock { font-size: 18px; font-weight: 300; color: rgba(255,255,255,0.5); letter-spacing: 4px; }
  .topbar .right { display: flex; align-items: center; gap: 8px; }
  .topbar .meta { font-size: 8px; color: rgba(255,255,255,0.2); display: flex; align-items: center; gap: 6px; }
  .topbar .meta .sep { color: rgba(255,255,255,0.06); }
  .topbar .offline-badge {
    font-size: 8px; color: #00e6b4; border: 1px solid rgba(0,230,180,0.2);
    border-radius: 3px; padding: 2px 6px; letter-spacing: 1px;
  }
  .topbar .latency { font-size: 8px; color: rgba(255,255,255,0.15); }
  .btn {
    padding: 5px 14px; border: none; border-radius: 4px;
    font-family: inherit; font-size: 9px; font-weight: 600;
    cursor: pointer; letter-spacing: 1px; transition: all 0.2s;
  }
  .btn-start { background: transparent; color: #00e6b4; border: 1px solid rgba(0,230,180,0.3); }
  .btn-start:hover { background: rgba(0,230,180,0.1); }
  .btn-stop { background: transparent; color: #ff3355; border: 1px solid rgba(255,51,85,0.3); }
  .btn-stop:hover { background: rgba(255,51,85,0.1); }
  .btn:disabled { opacity: 0.2; cursor: not-allowed; }

  /* Alarm banner */
  .alarm-banner {
    margin: 6px 10px; padding: 10px 16px;
    border-radius: 6px; text-align: center;
    transition: all 0.4s; flex-shrink: 0;
    border: 1px solid rgba(255,255,255,0.04);
    background: rgba(0,230,180,0.03);
  }
  .alarm-banner.active {
    background: linear-gradient(135deg, rgba(255,51,85,0.08), rgba(255,51,85,0.15));
    border-color: rgba(255,51,85,0.3);
    padding: 14px 16px;
  }
  .alarm-banner.standby { border-color: rgba(255,255,255,0.04); background: rgba(255,255,255,0.01); }
  .alarm-banner .big { font-size: 18px; font-weight: 700; letter-spacing: 4px; }
  .alarm-banner .sub { font-size: 9px; color: rgba(255,255,255,0.3); margin-top: 3px; letter-spacing: 1px; }
  .alarm-banner .detail { font-size: 9px; color: #ff3355; margin-top: 3px; }

  /* Panels */
  .panels {
    display: grid; grid-template-columns: 1fr 1.5fr;
    gap: 8px; padding: 6px 10px;
    flex: 1; min-height: 0;
  }
  .panel {
    background: rgba(255,255,255,0.015); border: 1px solid rgba(255,255,255,0.04);
    border-radius: 8px; padding: 8px 10px;
    display: flex; flex-direction: column; min-height: 0;
  }
  .panel-title {
    font-size: 8px; font-weight: 500; letter-spacing: 2px;
    color: rgba(255,255,255,0.25); text-transform: uppercase;
    margin-bottom: 6px;
    display: flex; align-items: center; gap: 6px;
    flex-shrink: 0;
  }
  .panel-title .indicator { width: 5px; height: 5px; border-radius: 50%; background: rgba(255,255,255,0.15); }
  .panel-title .indicator.active { background: #00e6b4; animation: pulse-dot 2s infinite; }
  .panel-title .indicator.alarm { background: #ff3355; animation: pulse-dot 0.5s infinite; }

  /* Waveform */
  .waveform-area {
    flex: 1; background: rgba(0,0,0,0.3); border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    position: relative; overflow: hidden; min-height: 0;
    border: 1px solid rgba(255,255,255,0.03);
  }
  .waveform-area canvas { width: 100%; height: 100%; }
  .inaudible-overlay {
    position: absolute; inset: 0;
    display: flex; align-items: center; justify-content: center;
    pointer-events: none;
  }
  .inaudible-overlay .big { font-size: 20px; font-weight: 300; color: rgba(255,255,255,0.04); letter-spacing: 8px; }
  .vu-meter { margin-top: 6px; height: 3px; background: rgba(255,255,255,0.04); border-radius: 2px; overflow: hidden; flex-shrink:0; }
  .vu-meter .fill { height: 100%; background: #00e6b4; transition: width 0.15s; border-radius: 2px; }
  .chunk-info { font-size: 8px; color: rgba(255,255,255,0.2); margin-top: 4px; text-align: center; flex-shrink:0; letter-spacing: 1px; }

  /* Spectrogram */
  .spec-area { flex: 1; display: flex; flex-direction: column; gap: 5px; min-height: 0; }
  .spec-main {
    flex: 1; background: rgba(0,0,0,0.3); border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    overflow: hidden; border: 1px solid rgba(255,255,255,0.04); min-height: 0;
    transition: all 0.3s;
  }
  .spec-main.alarm-ring { border-color: rgba(255,51,85,0.5); box-shadow: 0 0 20px rgba(255,51,85,0.15); }
  .spec-main img { width: 100%; height: 100%; object-fit: contain; }
  .spec-thumbs { display: flex; gap: 3px; height: 36px; flex-shrink: 0; }
  .spec-thumbs .thumb {
    flex: 1; background: rgba(0,0,0,0.2); border-radius: 3px; overflow: hidden;
    border: 1px solid rgba(255,255,255,0.04); cursor: pointer; transition: border 0.2s;
  }
  .spec-thumbs .thumb:hover { border-color: rgba(255,255,255,0.15); }
  .spec-thumbs .thumb.alarm-thumb { border-color: rgba(255,51,85,0.5); }
  .spec-thumbs .thumb img { width: 100%; height: 100%; object-fit: cover; }
  .conf-bar { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
  .conf-bar .track { flex:1; height: 3px; background: rgba(255,255,255,0.04); border-radius: 2px; overflow: hidden; }
  .conf-bar .fill { height: 100%; border-radius: 2px; transition: width 0.5s ease-out; }
  .conf-bar .val { font-size: 10px; font-weight: 600; min-width: 32px; text-align: right; letter-spacing: 1px; }
  .cot-text {
    font-size: 8px; line-height: 1.5; letter-spacing: 0.5px;
    max-height: 32px; overflow-y: auto;
    padding: 5px 8px; background: rgba(0,0,0,0.2); border-radius: 4px;
    flex-shrink: 0; color: rgba(0,230,180,0.7);
  }
  .cot-text.alarm-text { color: rgba(255,51,85,0.8); }
  .spec-legend {
    display: flex; gap: 10px; font-size: 7px; color: rgba(255,255,255,0.15);
    padding: 2px 0; flex-shrink: 0; letter-spacing: 0.5px;
  }
  .spec-legend span::before { content: ''; display: inline-block; width: 8px; height: 2px; margin-right: 4px; border-radius: 1px; vertical-align: middle; }
  .spec-legend .mech::before { background: #f0c040; }
  .spec-legend .human::before { background: #ff3355; }

  /* Bottom — timeline with confidence heights */
  .bottom { padding: 6px 10px 4px; flex-shrink: 0; }
  .timeline-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
  .timeline-header .label { font-size: 7px; color: rgba(255,255,255,0.15); letter-spacing: 1px; text-transform: uppercase; }
  .timeline-header .info { font-size: 8px; color: rgba(255,255,255,0.25); }
  .timeline { display: flex; gap: 2px; height: 28px; align-items: flex-end; }
  .timeline .chunk-bar {
    flex: 1; max-width: 18px; border-radius: 2px 2px 0 0;
    background: rgba(255,255,255,0.04); transition: all 0.3s; cursor: pointer;
    min-height: 3px;
  }
  .timeline .chunk-bar.safe { background: rgba(0,230,180,0.35); }
  .timeline .chunk-bar.alarm { background: #ff3355; box-shadow: 0 0 6px rgba(255,51,85,0.3); }
  .timeline .chunk-bar.current { outline: 1px solid rgba(255,255,255,0.5); outline-offset: 1px; }
  .timeline .chunk-bar:hover { opacity: 0.8; }
  .session-stats {
    margin-top: 4px; font-size: 8px; color: rgba(255,255,255,0.15);
    display: flex; gap: 12px; letter-spacing: 0.5px;
  }
  .session-stats span b { color: rgba(255,255,255,0.35); }

  /* Footer */
  .footer {
    padding: 4px 10px; flex-shrink: 0; text-align: center;
    font-size: 7px; color: rgba(255,255,255,0.08); letter-spacing: 1px;
  }
</style>
</head>
<body>

<!-- TOP BAR -->
<div class="topbar">
  <div class="left">
    <div class="dot" id="systemDot"></div>
    <span class="logo">WWTP.AI</span>
    <span class="logo-sub">ACOUSTIC SAFETY SYSTEM</span>
  </div>
  <div class="clock" id="clock">--:--:--</div>
  <div class="right">
    <button class="btn btn-start" id="btnStart" onclick="startDetection()">&#9654; START</button>
    <button class="btn btn-stop" id="btnStop" onclick="stopDetection()" disabled>&#9632; STOP</button>
    <div class="meta">
      <span id="systemStatus">INIT</span>
      <span class="sep">|</span><span>Gemma 4 E4B</span>
      <span class="sep">|</span><span>Ollama</span>
      <span class="sep">|</span><span class="offline-badge">OFFLINE</span>
    </div>
    <div class="latency">Latency: <span id="badgeLatency">—</span> | FP: 0</div>
  </div>
</div>

<!-- ALARM BANNER -->
<div class="alarm-banner standby" id="mainStatus">
  <div class="big" id="statusText" style="color:rgba(255,255,255,0.2)">STANDBY</div>
  <div class="sub" id="statusSub">Press START to begin monitoring</div>
  <div class="detail" id="statusDetail"></div>
</div>

<!-- PANELS -->
<div class="panels" id="mainBody">
  <div class="panel">
    <div class="panel-title">
      <div class="indicator" id="audioIndicator"></div>
      LIVE AUDIO — MICROPHONE
    </div>
    <div class="waveform-area" id="waveArea">
      <canvas id="waveCanvas"></canvas>
      <div class="inaudible-overlay"><div class="big" id="waveOverlay">NO SIGNAL</div></div>
    </div>
    <div class="vu-meter"><div class="fill" id="vuFill" style="width:0%"></div></div>
    <div class="chunk-info" id="chunkInfo">Waiting...</div>
  </div>

  <div class="panel">
    <div class="panel-title">
      <div class="indicator" id="aiIndicator"></div>
      AI ANALYSIS — VOICE-RANGE SPECTROGRAM [300-3000Hz]
    </div>
    <div class="spec-area">
      <div class="spec-main" id="specMain">
        <span style="color:rgba(255,255,255,0.1);font-size:10px;letter-spacing:2px">AWAITING INPUT</span>
      </div>
      <div class="spec-thumbs" id="specThumbs">
        <div class="thumb" id="thumb1"></div>
        <div class="thumb" id="thumb2"></div>
        <div class="thumb" id="thumb3"></div>
      </div>
      <div class="conf-bar" id="confBar" style="display:none">
        <div class="track"><div class="fill" id="confFill"></div></div>
        <div class="val" id="confVal">0%</div>
      </div>
      <div class="cot-text" id="cotText">Chain-of-Thought reasoning will appear here...</div>
      <div class="spec-legend">
        <span class="mech">Vertical spikes = Mechanical noise</span>
        <span class="human">Curved bands = Human speech</span>
      </div>
    </div>
  </div>
</div>

<!-- BOTTOM -->
<div class="bottom">
  <div class="timeline-header">
    <span class="label">CHUNK TIMELINE — LAST 30</span>
    <span class="info" id="timelineInfo"></span>
  </div>
  <div class="timeline" id="timeline"></div>
  <div class="session-stats" id="sessionStats">
    <span>Chunks: <b>0</b></span>
    <span>Alarms: <b>0</b></span>
    <span>Avg Conf: <b>0%</b></span>
    <span>Session: <b>00:00</b></span>
  </div>
</div>

<!-- FOOTER -->
<div class="footer">WWTP.AI v1.0 &middot; Gemma 4 E4B &middot; Ollama &middot; Apache 2.0 &middot; Mehmet ISIK — Adana ASKI</div>

<script>
// ── State ──
let ws = null;
let running = false;
let chunks = [];          // {alarm, spec_b64, reasoning, confidence, chunk_num}
let spectrogramHistory = [];
const MAX_TIMELINE = 30;
const MAX_HISTORY = 20;   // keep last 20 chunks with spectrograms
let selectedChunk = null; // for click-to-view

// ── Clock ──
setInterval(() => {
  document.getElementById('clock').textContent = new Date().toLocaleTimeString('en-GB');
}, 1000);

// ── Waveform Canvas ──
const canvas = document.getElementById('waveCanvas');
const ctx = canvas.getContext('2d');
let wavePhase = 0;
let waveActive = false;
let waveAlarm = false;

function resizeCanvas() {
  canvas.width = canvas.parentElement.clientWidth;
  canvas.height = canvas.parentElement.clientHeight;
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

function drawWave() {
  const W = canvas.width, H = canvas.height, mid = H/2;
  ctx.clearRect(0, 0, W, H);
  const bars = 80, bw = W/bars - 1;
  for (let i = 0; i < bars; i++) {
    const x = i * (bw + 1);
    let amp;
    if (waveActive) {
      amp = (Math.sin(i*0.25+wavePhase)*0.35 + Math.sin(i*0.4+wavePhase*1.3)*0.25 + Math.cos(i*0.15+wavePhase*0.7)*0.2 + 0.15) * mid;
    } else {
      amp = (Math.sin(i*0.3)*0.05 + 0.03) * mid;
    }
    const h = Math.max(1, Math.abs(amp));
    ctx.fillStyle = waveAlarm ? `rgba(255,51,85,${0.5+Math.sin(wavePhase+i)*0.3})` :
                    waveActive ? `rgba(0,230,180,${0.3+Math.sin(wavePhase+i)*0.2})` :
                    'rgba(255,255,255,0.06)';
    ctx.beginPath();
    ctx.roundRect(x, mid-h, bw, h*2, 2);
    ctx.fill();
  }
  if (waveActive) wavePhase += 0.08;
  requestAnimationFrame(drawWave);
}
drawWave();

// ── Alarm Sound ──
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
function playAlarm() {
  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();
  osc.connect(gain); gain.connect(audioCtx.destination);
  osc.frequency.value = 880;
  osc.type = 'square';
  gain.gain.value = 0.15;
  osc.start(); osc.stop(audioCtx.currentTime + 0.4);
  setTimeout(() => {
    const osc2 = audioCtx.createOscillator();
    const gain2 = audioCtx.createGain();
    osc2.connect(gain2); gain2.connect(audioCtx.destination);
    osc2.frequency.value = 1100;
    osc2.type = 'square';
    gain2.gain.value = 0.15;
    osc2.start(); osc2.stop(audioCtx.currentTime + 0.3);
  }, 500);
}

// ── WebSocket ──
function connect() {
  ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onopen = () => {
    document.getElementById('systemStatus').textContent = 'SYSTEM READY';
  };
  ws.onmessage = (e) => handleMessage(JSON.parse(e.data));
  ws.onclose = () => {
    document.getElementById('systemStatus').textContent = 'DISCONNECTED';
    document.getElementById('systemDot').classList.add('inactive');
    setTimeout(connect, 2000);
  };
}

function handleMessage(msg) {
  if (msg.type === 'phase') {
    const info = document.getElementById('chunkInfo');
    const aiInd = document.getElementById('aiIndicator');
    const audioInd = document.getElementById('audioIndicator');
    document.getElementById('waveOverlay').textContent = 'LISTENING';
    if (msg.phase === 'recording') {
      info.textContent = `Chunk ${msg.chunk} | Recording...`;
      waveActive = true;
      audioInd.className = 'indicator active';
      aiInd.className = 'indicator';
    } else if (msg.phase === 'spectrogram') {
      info.textContent = `Chunk ${msg.chunk} | Generating spectrogram...`;
    } else if (msg.phase === 'analyzing') {
      info.textContent = `Chunk ${msg.chunk} | Analyzing with AI...`;
      audioInd.className = 'indicator';
      aiInd.className = 'indicator active';
    }
  }

  else if (msg.type === 'audio_level') {
    const pct = Math.min(100, msg.rms * 3000);
    const fill = document.getElementById('vuFill');
    fill.style.width = pct + '%';
    fill.style.background = pct > 70 ? '#ff3355' : pct > 40 ? '#f0c040' : '#00e6b4';
  }

  else if (msg.type === 'result') {
    const panel = document.getElementById('mainStatus');
    const text = document.getElementById('statusText');
    const sub = document.getElementById('statusSub');
    const detail = document.getElementById('statusDetail');
    const specMain = document.getElementById('specMain');
    const cotText = document.getElementById('cotText');
    const aiInd = document.getElementById('aiIndicator');
    const info = document.getElementById('chunkInfo');

    info.textContent = `Chunk ${msg.chunk} | ${msg.analysis_time}s`;
    waveAlarm = msg.is_alarm;

    // Confidence bar
    const confPct = Math.round(msg.confidence * 100);
    const confBar = document.getElementById('confBar');
    const confFill = document.getElementById('confFill');
    const confVal = document.getElementById('confVal');
    confBar.style.display = 'flex';
    confFill.style.width = confPct + '%';
    confFill.style.background = msg.is_alarm ? '#ff3355' : '#00e6b4';
    confVal.textContent = confPct + '%';
    confVal.style.color = msg.is_alarm ? '#ff3355' : '#00e6b4';

    // Edge badge latency
    document.getElementById('badgeLatency').textContent = msg.analysis_time + 's';

    if (msg.is_alarm) {
      panel.className = 'alarm-banner active';
      text.textContent = '\u26A0 ALARM — HUMAN DISTRESS DETECTED';
      text.style.color = '#ff3355';
      sub.textContent = `Action: ${msg.action.replace(/_/g,' ')}`;
      detail.textContent = `Type: ${msg.distress_type} \u00B7 Confidence: ${Math.round(msg.confidence*100)}% \u00B7 Chunk ${msg.chunk}`;
      aiInd.className = 'indicator alarm';
      cotText.className = 'cot-text alarm-text';
      specMain.className = 'spec-main alarm-ring';
      document.getElementById('mainBody').classList.add('alarm-pulse');
      playAlarm();
    } else {
      panel.className = 'alarm-banner';
      text.textContent = 'MONITORING — ALL CLEAR';
      text.style.color = '#00e6b4';
      sub.textContent = `Confidence: ${Math.round(msg.confidence*100)}%`;
      detail.textContent = '';
      aiInd.className = 'indicator active';
      cotText.className = 'cot-text';
      specMain.className = 'spec-main';
      document.getElementById('mainBody').classList.remove('alarm-pulse');
      waveAlarm = false;
    }

    // Store chunk data (keep last MAX_HISTORY with spectrograms)
    chunks.push({
      alarm: msg.is_alarm,
      spec_b64: msg.spectrogram_b64,
      reasoning: msg.reasoning || '',
      confidence: msg.confidence,
      chunk_num: msg.chunk,
      distress_type: msg.distress_type,
    });
    // Trim old spectrogram data to save memory
    if (chunks.length > MAX_HISTORY) {
      const old = chunks[chunks.length - MAX_HISTORY - 1];
      if (old) old.spec_b64 = null;
    }
    selectedChunk = null; // auto-show latest

    // Spectrogram — show latest
    if (msg.spectrogram_b64) {
      specMain.innerHTML = `<img src="data:image/png;base64,${msg.spectrogram_b64}" alt="spectrogram">`;
      // Thumbnails — last 3 with data
      const recent = chunks.filter(c => c.spec_b64).slice(-3).reverse();
      for (let i = 0; i < 3; i++) {
        const el = document.getElementById(`thumb${i+1}`);
        if (recent[i]) {
          const ci = chunks.indexOf(recent[i]);
          el.innerHTML = `<img src="data:image/png;base64,${recent[i].spec_b64}" alt="thumb">`;
          el.className = recent[i].alarm ? 'thumb alarm-thumb' : 'thumb';
          el.style.cursor = 'pointer';
          el.onclick = () => showChunk(ci);
        } else {
          el.innerHTML = '';
          el.className = 'thumb';
        }
      }
    }

    // CoT
    cotText.textContent = msg.reasoning || 'Analyzing...';

    // Timeline
    renderTimeline(msg.chunk);

    // Stats
    const s = msg.stats;
    const mins = Math.floor(msg.session_time / 60);
    const secs = msg.session_time % 60;
    document.getElementById('sessionStats').innerHTML =
      `<span>Chunks: <b>${s.total}</b></span>` +
      `<span>Alarms: <b>${s.alarms}</b></span>` +
      `<span>Avg Confidence: <b>${s.avg_conf}%</b></span>` +
      `<span>Avg Time: <b>${msg.analysis_time}s</b></span>` +
      `<span>Session: <b>${String(mins).padStart(2,'0')}:${String(secs).padStart(2,'0')}</b></span>`;
  }

  else if (msg.type === 'stopped') {
    running = false;
    waveActive = false;
    waveAlarm = false;
    document.getElementById('mainStatus').className = 'alarm-banner standby';
    document.getElementById('statusText').textContent = 'STOPPED';
    document.getElementById('statusText').style.color = 'rgba(255,255,255,0.2)';
    document.getElementById('statusSub').textContent = 'Press START to resume';
    document.getElementById('btnStart').disabled = false;
    document.getElementById('btnStop').disabled = true;
    document.getElementById('systemStatus').textContent = 'READY';
    document.getElementById('waveOverlay').textContent = 'NO SIGNAL';
    document.getElementById('mainBody').classList.remove('alarm-pulse');
  }
}

function renderTimeline(currentChunk) {
  const el = document.getElementById('timeline');
  const visible = chunks.slice(-MAX_TIMELINE);
  const startIdx = Math.max(0, chunks.length - MAX_TIMELINE);
  el.innerHTML = visible.map((c, i) => {
    const globalIdx = startIdx + i;
    const isCurrent = (globalIdx + 1) === currentChunk && selectedChunk === null;
    const isSelected = selectedChunk === globalIdx;
    const cls = c.alarm ? 'chunk-bar alarm' : 'chunk-bar safe';
    const sel = (isCurrent || isSelected) ? ' current' : '';
    const conf = c.confidence || 0.1;
    const h = Math.max(12, Math.round(conf * 100 * 0.28));
    const clickable = c.spec_b64 ? '' : 'opacity:0.3;cursor:default';
    return `<div class="${cls}${sel}" title="Chunk ${globalIdx+1} · ${Math.round(conf*100)}%${c.alarm?' · ALARM':''}" style="height:${h}px;${clickable}" onclick="showChunk(${globalIdx})"></div>`;
  }).join('');
  // Update timeline info
  const last = visible[visible.length - 1];
  if (last) {
    document.getElementById('timelineInfo').textContent = `Chunk ${chunks.length} \u00B7 Conf: ${Math.round((last.confidence||0)*100)}%`;
  }
}

function showChunk(idx) {
  const c = chunks[idx];
  if (!c || !c.spec_b64) return;
  selectedChunk = idx;
  const specMain = document.getElementById('specMain');
  const cotText = document.getElementById('cotText');
  specMain.innerHTML = `<img src="data:image/png;base64,${c.spec_b64}" alt="spectrogram">`;
  specMain.className = c.alarm ? 'spec-main alarm-ring' : 'spec-main';
  cotText.textContent = `[Chunk ${c.chunk_num}] ${c.reasoning}`;
  cotText.className = c.alarm ? 'cot-text alarm-text' : 'cot-text';
  // Update timeline highlight
  renderTimeline(null);
}

// ── Controls ──
function startDetection() {
  if (!ws || ws.readyState !== 1) return;
  audioCtx.resume();
  running = true;
  chunks = [];
  spectrogramHistory = [];
  document.getElementById('btnStart').disabled = true;
  document.getElementById('btnStop').disabled = false;
  document.getElementById('systemStatus').textContent = 'ACTIVE';
  document.getElementById('mainStatus').className = 'alarm-banner';
  document.getElementById('statusText').textContent = 'MONITORING — ANALYZING';
  document.getElementById('statusText').style.color = '#00e6b4';
  document.getElementById('statusSub').textContent = 'Listening for human distress signals...';
  document.getElementById('statusDetail').textContent = '';
  ws.send(JSON.stringify({ action: 'start' }));
}

function stopDetection() {
  if (ws && ws.readyState === 1) {
    ws.send(JSON.stringify({ action: 'stop' }));
  }
}

// ── Init ──
connect();
</script>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    default_model = OLLAMA_MODEL  # capture module-level default
    parser = argparse.ArgumentParser(description="WWTP Acoustic Safety System — Live Detector Web UI")
    parser.add_argument("--device", type=int, default=None, help="Microphone device index")
    parser.add_argument("--model", type=str, default=default_model, help=f"Ollama model (default: {default_model})")
    parser.add_argument("--port", type=int, default=8080, help="Web server port (default: 8080)")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE_SEC, help=f"Chunk duration seconds (default: {CHUNK_SIZE_SEC})")
    parser.add_argument("--threshold", type=float, default=0.50, help="Alarm threshold (default: 0.50)")
    args = parser.parse_args()

    model = args.model
    state["model"] = model
    state["device"] = args.device
    state["chunk_size"] = args.chunk_size
    state["threshold"] = args.threshold

    print("\n" + "=" * 60)
    print("  WWTP.AI — ACOUSTIC SAFETY SYSTEM — WEB UI")
    print("=" * 60)
    print(f"  Model:      {args.model}")
    print(f"  Port:       {args.port}")
    print(f"  Threshold:  {args.threshold}")

    # Warmup
    warmup_model(args.model)

    # Few-shot
    fewshot = generate_fewshot_examples()
    if fewshot is None:
        print("  [ERROR] Few-shot generation failed. Check dataset/audio/")
        sys.exit(1)
    state["fewshot"] = fewshot

    # Open browser
    url = f"http://localhost:{args.port}"
    print(f"\n  Opening browser: {url}")
    print(f"  Press Ctrl+C to stop.\n")
    threading.Timer(1.5, lambda: webbrowser.open(url)).start()

    # Run server
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()

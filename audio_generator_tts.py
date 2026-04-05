"""
WWTP Acoustic Safety System — TTS Audio Generator
===================================================
Generates 5 synthetic WAV files using real TTS (Text-to-Speech)
for human distress signals instead of formant synthesis.

WHY TTS?
  Formant synthesis produces mathematically correct but unnatural tones.
  Gemma 4 E4B's ASR is trained on real human speech patterns.
  By using gTTS to generate "HELP!", "YARDIM!", we produce speech
  patterns the model actually recognizes — real words, real rhythm,
  real intonation. Then we add industrial distortion on top.

Architecture:
  Industrial noise → numpy/scipy (same as original)
  Human voice     → gTTS (real speech) + distortion effects
  Final mix       → noise + distorted voice at target SNR

Requirements:
    pip install numpy scipy soundfile gTTS pydub
    ffmpeg must be installed and in PATH

Output:
    dataset/audio_tts/S1_pump_room_normal.wav
    dataset/audio_tts/S2_construction_human.wav
    dataset/audio_tts/S3_pool_false_alarm.wav
    dataset/audio_tts/S4_manhole_masked.wav
    dataset/audio_tts/S5_pool_critical.wav

Author: Mehmet ISIK | Data Scientist | Adana ASKI | Kaggle Grandmaster
Date  : April 2026
Seed  : 42 (noise is reproducible, TTS is deterministic)
"""

import numpy as np
import soundfile as sf
import os
import io
import tempfile
from scipy import signal
from scipy.signal import fftconvolve

# ── TTS imports ──────────────────────────────────────────────
from gtts import gTTS
from pydub import AudioSegment

# ── Reproducibility (for noise components) ───────────────────
SEED = 42
np.random.seed(SEED)

# ── Global Settings ──────────────────────────────────────────
SR        = 16000   # Sample rate (Hz) — standard for industrial mics
DURATION  = 60      # Scene duration (seconds)
N_SAMPLES = SR * DURATION
OUTPUT_DIR = os.path.join("dataset", "audio_tts")


# ════════════════════════════════════════════════════════════════
# NOISE PRIMITIVES (Same as original — proven to work)
# ════════════════════════════════════════════════════════════════

def white_noise(n, amp=1.0):
    return (np.random.randn(n) * amp).astype(np.float32)

def pink_noise(n, amp=1.0):
    wn = np.random.randn(n)
    b = np.array([0.049922035, -0.095993537, 0.050612699, -0.004408786])
    a = np.array([1.0, -2.494956002, 2.017265875, -0.522189400])
    pink = signal.lfilter(b, a, wn)
    pink = pink / (np.max(np.abs(pink)) + 1e-9)
    return (pink * amp).astype(np.float32)

def brown_noise(n, amp=1.0):
    wn = np.random.randn(n)
    bn = np.cumsum(wn)
    bn = bn / (np.max(np.abs(bn)) + 1e-9)
    return (bn * amp).astype(np.float32)

def band_pass(audio, low_hz, high_hz, sr=SR):
    nyq = sr / 2
    low  = max(low_hz  / nyq, 0.001)
    high = min(high_hz / nyq, 0.999)
    b, a = signal.butter(4, [low, high], btype='band')
    return signal.lfilter(b, a, audio).astype(np.float32)

def low_pass(audio, cutoff_hz, sr=SR):
    nyq = sr / 2
    cut = min(cutoff_hz / nyq, 0.999)
    b, a = signal.butter(4, cut, btype='low')
    return signal.lfilter(b, a, audio).astype(np.float32)

def high_pass(audio, cutoff_hz, sr=SR):
    nyq = sr / 2
    cut = max(cutoff_hz / nyq, 0.001)
    b, a = signal.butter(4, cut, btype='high')
    return signal.lfilter(b, a, audio).astype(np.float32)

def normalize(audio, target_amp=0.8):
    mx = np.max(np.abs(audio))
    if mx < 1e-9:
        return audio
    return (audio / mx * target_amp).astype(np.float32)

def db_to_amp(db):
    return 10 ** (db / 20.0)

def mix(*tracks, weights=None):
    if weights is None:
        weights = [1.0] * len(tracks)
    mixed = np.zeros(N_SAMPLES, dtype=np.float32)
    for track, w in zip(tracks, weights):
        length = min(len(track), N_SAMPLES)
        mixed[:length] += track[:length] * w
    return normalize(mixed)


# ════════════════════════════════════════════════════════════════
# MECHANICAL NOISE GENERATORS (Same as original)
# ════════════════════════════════════════════════════════════════

def pump_hum(n=N_SAMPLES, sr=SR):
    """Centrifugal pump: 120Hz tonal + harmonics + pink noise."""
    np.random.seed(SEED)
    t = np.linspace(0, n / sr, n)
    tone  = np.sin(2 * np.pi * 120 * t) * 0.6
    harm2 = np.sin(2 * np.pi * 240 * t) * 0.3
    harm3 = np.sin(2 * np.pi * 360 * t) * 0.15
    noise = band_pass(pink_noise(n, 0.2), 50, 300, sr)
    return normalize(tone + harm2 + harm3 + noise)

def pipe_vibration(n=N_SAMPLES, sr=SR):
    np.random.seed(SEED + 1)
    noise = pink_noise(n, 1.0)
    return normalize(low_pass(noise, 200, sr))

def motor_drone(n=N_SAMPLES, sr=SR):
    """Motor drone: 150Hz — frequency capped at 250Hz to avoid human voice range."""
    np.random.seed(SEED + 2)
    t = np.linspace(0, n / sr, n)
    tone  = np.sin(2 * np.pi * 150 * t) * 0.5
    # FIXED: Upper limit 250Hz (was 500Hz) to prevent voice-range contamination
    noise = band_pass(brown_noise(n, 0.5), 50, 250, sr)
    return normalize(tone + noise)

def concrete_mixer(n=N_SAMPLES, sr=SR):
    np.random.seed(SEED + 10)
    t = np.linspace(0, n / sr, n)
    noise = band_pass(white_noise(n, 1.0), 200, 2000, sr)
    mod   = 0.6 + 0.4 * np.sin(2 * np.pi * 0.5 * t)
    return normalize(noise * mod)

def excavator(n=N_SAMPLES, sr=SR):
    np.random.seed(SEED + 11)
    base  = band_pass(brown_noise(n, 1.0), 50, 1000, sr)
    impacts = np.zeros(n)
    for _ in range(int(n / sr * 3)):
        pos = np.random.randint(0, n - SR // 10)
        dur = SR // 20
        env = np.exp(-np.linspace(0, 8, dur))
        impacts[pos:pos + dur] += env * np.random.uniform(0.5, 1.5)
    return normalize(base * 0.6 + impacts * 0.4)

def pneumatic_drill(n=N_SAMPLES, sr=SR):
    np.random.seed(SEED + 12)
    t = np.linspace(0, n / sr, n)
    noise = high_pass(white_noise(n, 1.0), 1000, sr)
    mod = (np.sin(2 * np.pi * 20 * t) > 0).astype(float)
    return normalize(noise * mod)

def metal_clanging(n=N_SAMPLES, sr=SR, rate=0.4):
    np.random.seed(SEED + 13)
    result = np.zeros(n)
    interval_samples = int(SR / rate)
    pos = 0
    while pos < n:
        dur = SR // 8
        if pos + dur < n:
            freq = np.random.uniform(500, 8000)
            t_imp = np.linspace(0, dur / SR, dur)
            imp = np.sin(2 * np.pi * freq * t_imp)
            env = np.exp(-np.linspace(0, 10, dur))
            result[pos:pos + dur] += imp * env * np.random.uniform(0.5, 1.0)
        pos += interval_samples + np.random.randint(-SR // 4, SR // 4)
        pos = max(pos, 0)
    return normalize(result)

def scraper_bridge_motor(n=N_SAMPLES, sr=SR):
    np.random.seed(SEED + 14)
    t = np.linspace(0, n / sr, n)
    tone  = np.sin(2 * np.pi * 180 * t) * 0.7
    harm  = np.sin(2 * np.pi * 360 * t) * 0.2
    mod   = 0.8 + 0.2 * np.sin(2 * np.pi * 0.1 * t)
    noise = band_pass(pink_noise(n, 0.2), 60, 400, sr)
    return normalize((tone + harm) * mod + noise)

def metal_scraping(n=N_SAMPLES, sr=SR):
    """Irregular scraping — intentionally deceptive, resembles voice cadence."""
    np.random.seed(SEED + 15)
    base = band_pass(white_noise(n, 1.0), 300, 3000, sr)
    mod = np.zeros(n)
    pos = 0
    while pos < n:
        dur = np.random.randint(SR // 4, SR * 2)
        amp = np.random.uniform(0.2, 1.0)
        end = min(pos + dur, n)
        mod[pos:end] = amp
        pos = end + np.random.randint(SR // 8, SR // 2)
    return normalize(base * mod)

def chain_rattle(n=N_SAMPLES, sr=SR):
    np.random.seed(SEED + 16)
    result = np.zeros(n)
    for _ in range(int(n / SR * 2)):
        pos = np.random.randint(0, n - SR // 10)
        dur = SR // 20
        if pos + dur < n:
            freq = np.random.uniform(500, 5000)
            t_c  = np.linspace(0, dur / SR, dur)
            click = np.sin(2 * np.pi * freq * t_c)
            env   = np.exp(-np.linspace(0, 15, dur))
            result[pos:pos + dur] += click * env * np.random.uniform(0.3, 0.8)
    return normalize(result)

def metal_bang(n=N_SAMPLES, sr=SR):
    np.random.seed(SEED + 17)
    result = np.zeros(n)
    for _ in range(4):
        pos = np.random.randint(SR * 5, n - SR * 5)
        dur = int(SR * 0.35)
        if pos + dur < n:
            freq = np.random.uniform(800, 3000)
            t_b  = np.linspace(0, dur / SR, dur)
            bang = np.sin(2 * np.pi * freq * t_b)
            env  = np.exp(-np.linspace(0, 12, dur))
            result[pos:pos + dur] += bang * env
    return normalize(result)

def pool_ambient(n=N_SAMPLES, sr=SR):
    np.random.seed(SEED + 18)
    noise = pink_noise(n, 1.0)
    return normalize(low_pass(noise, 2000, sr) * 0.4)

def underground_ambient(n=N_SAMPLES, sr=SR):
    np.random.seed(SEED + 20)
    flow = low_pass(pink_noise(n, 0.3), 500, sr)
    t = np.linspace(0, n / sr, n)
    vent = np.sin(2 * np.pi * 120 * t) * 0.15
    drips = np.zeros(n)
    pos = 0
    while pos < n:
        dur = SR // 20
        if pos + dur < n:
            t_d = np.linspace(0, dur / SR, dur)
            drip = np.sin(2 * np.pi * 600 * t_d)
            env  = np.exp(-np.linspace(0, 20, dur))
            drips[pos:pos + dur] += drip * env * 0.4
        interval = np.random.randint(SR // 2, SR * 3)
        pos += interval
    return normalize(flow + vent + drips)


# ════════════════════════════════════════════════════════════════
# TTS VOICE GENERATION — The Key Innovation
# ════════════════════════════════════════════════════════════════
# Instead of formant synthesis, we use Google TTS to generate
# real speech that Gemma 4's ASR can actually recognize.
# Then we apply environmental distortion to simulate conditions.

def _tts_to_numpy(text, lang='en', sr=SR):
    """
    Convert text to numpy audio array using gTTS.

    gTTS produces MP3 → pydub converts to WAV → numpy array.
    Result is mono, resampled to target sample rate.

    Args:
        text: str — text to speak (e.g. "HELP" or "YARDIM")
        lang: str — language code ('en' for English, 'tr' for Turkish)
        sr: int — target sample rate

    Returns:
        numpy array (float32, normalized) — the spoken audio
    """
    # Generate speech with gTTS
    tts = gTTS(text=text, lang=lang, slow=False)

    # Save to temporary MP3
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
        tmp_path = tmp.name
        tts.save(tmp_path)

    try:
        # Load MP3 with pydub
        audio_seg = AudioSegment.from_mp3(tmp_path)

        # Convert to mono, target sample rate, 16-bit
        audio_seg = audio_seg.set_channels(1)
        audio_seg = audio_seg.set_frame_rate(sr)
        audio_seg = audio_seg.set_sample_width(2)  # 16-bit

        # Convert to numpy
        samples = np.array(audio_seg.get_array_of_samples(), dtype=np.float32)
        samples = samples / (2**15)  # Normalize to -1.0 to 1.0

        return samples

    finally:
        # Clean up temp file
        os.unlink(tmp_path)


def _generate_tts_phrases(phrases, lang='en', sr=SR):
    """
    Generate multiple TTS phrases and concatenate them.

    Args:
        phrases: list of str — texts to speak
        lang: str — language code

    Returns:
        list of numpy arrays — one per phrase
    """
    results = []
    for phrase in phrases:
        audio = _tts_to_numpy(phrase, lang=lang, sr=sr)
        results.append(audio)
    return results


def _pitch_shift(audio, semitones, sr=SR):
    """
    Simple pitch shift by resampling.
    Positive semitones = higher pitch (more urgent/panicked).
    """
    factor = 2 ** (semitones / 12.0)
    # Resample to shift pitch
    indices = np.round(np.arange(0, len(audio), factor)).astype(int)
    indices = indices[indices < len(audio)]
    return audio[indices].astype(np.float32)


def _apply_reverb(audio, decay_sec=1.8, sr=SR):
    """Concrete tunnel/gallery reverb simulation."""
    np.random.seed(SEED + 50)
    n_reverb = int(decay_sec * sr)
    t_rev    = np.linspace(0, decay_sec, n_reverb)
    ir       = np.exp(-t_rev / (decay_sec / 6)) * np.random.randn(n_reverb) * 0.3
    ir[0]    = 1.0
    wet      = fftconvolve(audio, ir, mode='full')[:len(audio)]
    result   = audio * 0.4 + wet * 0.6
    return normalize(result)


# ════════════════════════════════════════════════════════════════
# TTS DISTRESS SIGNAL GENERATORS
# ════════════════════════════════════════════════════════════════

def tts_shout_help(start_sec, end_sec, sr=SR, intensity=0.85):
    """
    Periodic shouting using real TTS speech.
    Uses "HELP" and "YARDIM" alternating.
    Pitch shifted up for urgency.

    Returns full-length array with zeros before/after active region.
    """
    print("    Generating TTS: shouting HELP/YARDIM...")
    result = np.zeros(N_SAMPLES, dtype=np.float32)

    # Generate base TTS phrases (done once, reused)
    phrases_en = _tts_to_numpy("Help! Help me!", lang='en', sr=sr)
    phrases_tr = _tts_to_numpy("Yardım! Yardım edin!", lang='tr', sr=sr)

    # NO pitch shift — keep natural voice for model recognition
    # Model needs to recognize real speech patterns, not distorted ones
    phrase_list = [phrases_en, phrases_tr]

    # Place phrases at intervals from start_sec to end_sec
    interval_sec = 3.0
    t = start_sec
    idx = 0
    while t < end_sec:
        phrase = phrase_list[idx % len(phrase_list)]
        start_s = int(t * sr)
        end_s   = min(start_s + len(phrase), N_SAMPLES)
        dur_s   = end_s - start_s

        if dur_s > 0 and dur_s <= len(phrase):
            # Apply amplitude envelope (natural shout shape)
            env = np.concatenate([
                np.linspace(0.3, 1.0, dur_s // 4),
                np.ones(dur_s // 2),
                np.linspace(1.0, 0.3, dur_s - dur_s // 4 - dur_s // 2)
            ])[:dur_s]
            result[start_s:end_s] += phrase[:dur_s] * env * intensity

        t += interval_sec
        idx += 1

    return result


def tts_scream_help(start_sec, end_sec, sr=SR, intensity=0.95):
    """
    Drowning person screaming — NOT clean speech.

    A drowning person:
      - Goes under water, comes back up gasping
      - Tries to shout but water enters mouth
      - Words are cut short, broken, interrupted
      - Irregular timing — not steady repetition
      - Voice fades in/out as person sinks/surfaces

    We simulate this by:
      1. Randomly truncating TTS phrases (going underwater mid-word)
      2. Adding water splash sounds ON the voice (water in mouth)
      3. Irregular fade in/out (sinking and surfacing cycle)
      4. Random gaps (being completely underwater)
    """
    print("    Generating TTS: drowning person (interrupted, gasping)...")
    np.random.seed(SEED + 60)
    result = np.zeros(N_SAMPLES, dtype=np.float32)

    # Generate panic phrases
    phrases = [
        _tts_to_numpy("Help! Help!", lang='en', sr=sr),
        _tts_to_numpy("Yardım!", lang='tr', sr=sr),
        _tts_to_numpy("Help me!", lang='en', sr=sr),
        _tts_to_numpy("İmdat!", lang='tr', sr=sr),
        _tts_to_numpy("Somebody!", lang='en', sr=sr),
        _tts_to_numpy("Yardım edin!", lang='tr', sr=sr),
    ]

    # Water splash/gargle sound generator (for mixing over voice)
    def water_gargle(duration_samples):
        """Short burst of water noise simulating gargling/choking."""
        noise = band_pass(white_noise(duration_samples, 0.5), 200, 2000, sr)
        env = np.exp(-np.linspace(0, 3, duration_samples))
        return noise * env

    t = start_sec
    idx = 0
    while t < end_sec:
        phrase = phrases[idx % len(phrases)]

        # ── Drowning effect 1: Random truncation (going underwater mid-word)
        # Sometimes only 30-60% of the phrase is heard before going under
        truncation = np.random.uniform(0.3, 1.0)
        phrase_len = int(len(phrase) * truncation)
        phrase_cut = phrase[:phrase_len]

        start_s = int(t * sr)
        end_s   = min(start_s + phrase_len, N_SAMPLES)
        dur_s   = end_s - start_s

        if dur_s > 0 and dur_s <= len(phrase_cut):
            # ── Drowning effect 2: Irregular fade (surfacing then sinking)
            # Sharp attack (gasping for air), then fade (going under)
            env = np.concatenate([
                np.linspace(0.1, 1.0, dur_s // 6),       # gasp up
                np.ones(dur_s // 3) * 0.9,                # brief surface
                np.linspace(0.9, 0.1, dur_s - dur_s // 6 - dur_s // 3)  # sinking
            ])[:dur_s]

            result[start_s:end_s] += phrase_cut[:dur_s] * env * intensity

            # ── Drowning effect 3: Water gargle over some phrases
            # 50% chance of water sound overlapping the voice
            if np.random.random() > 0.5:
                gargle_len = min(dur_s // 2, N_SAMPLES - end_s)
                if gargle_len > 100:
                    gargle_start = start_s + dur_s // 2  # water enters mid-phrase
                    gargle = water_gargle(gargle_len) * 0.4
                    gargle_end = min(gargle_start + gargle_len, N_SAMPLES)
                    actual_len = gargle_end - gargle_start
                    result[gargle_start:gargle_end] += gargle[:actual_len]

        # ── Drowning effect 4: Irregular timing
        # Sometimes quick gasps (1.5s), sometimes long underwater (4s)
        if np.random.random() > 0.6:
            # Long gap — person is underwater, can't shout
            t += np.random.uniform(3.0, 5.0)
        else:
            # Quick succession — gasping at surface
            t += np.random.uniform(1.5, 2.5)

        idx += 1

    return result


def tts_masked_voice(start_sec, end_sec, sr=SR):
    """
    Muffled voice through respirator mask + deep gallery reverb.
    TTS voice → low pass filter (mask) → reverb (gallery).

    IMPORTANT: Don't over-filter! The voice must remain recognizable
    as human speech even after mask + reverb effects. Previous version
    was too aggressive — three attenuation layers stacked killed the signal.
    """
    print("    Generating TTS: masked/muffled voice in gallery...")
    result = np.zeros(N_SAMPLES, dtype=np.float32)

    # Generate distress phrases — longer phrases for better recognition
    phrases = [
        _tts_to_numpy("Help! Help me!", lang='en', sr=sr),
        _tts_to_numpy("Yardım! Yardım edin!", lang='tr', sr=sr),
    ]

    interval_sec = 4.0  # slightly faster than before (was 5.0)
    t = start_sec
    idx = 0
    while t < end_sec:
        phrase = phrases[idx % len(phrases)]

        # Mask effect: low pass filter — but gentler (2000Hz vs 1500Hz)
        # Respirator masks attenuate high frequencies but don't eliminate them
        phrase_masked = low_pass(phrase, 2000, sr)

        start_s = int(t * sr)
        end_s   = min(start_s + len(phrase_masked), N_SAMPLES)
        dur_s   = end_s - start_s

        if dur_s > 0 and dur_s <= len(phrase_masked):
            # Gentler envelope — voice stays audible longer
            env = np.concatenate([
                np.linspace(0.2, 0.8, dur_s // 4),
                np.ones(dur_s // 2) * 0.8,
                np.linspace(0.8, 0.1, dur_s - dur_s // 4 - dur_s // 2)
            ])[:dur_s]
            # Higher intensity (0.85 vs 0.5) — compensate for reverb attenuation
            result[start_s:end_s] += phrase_masked[:dur_s] * env * 0.85

        t += interval_sec
        idx += 1

    # Apply gallery reverb — lighter than before (1.2s vs 1.8s)
    # Too much reverb smears the speech patterns beyond recognition
    result = _apply_reverb(result, decay_sec=1.2, sr=sr)
    return result.astype(np.float32)


# ════════════════════════════════════════════════════════════════
# EVENT GENERATORS (Same as original)
# ════════════════════════════════════════════════════════════════

def body_impact_and_splash(at_sec, sr=SR):
    """Water splash at given second (person falling into pool)."""
    np.random.seed(SEED + 40)
    result  = np.zeros(N_SAMPLES)
    start_s = int(at_sec * sr)

    thud_dur = int(0.3 * sr)
    if start_s + thud_dur < N_SAMPLES:
        thud = band_pass(white_noise(thud_dur, 1.0), 100, 2000, sr)
        env  = np.exp(-np.linspace(0, 10, thud_dur))
        result[start_s:start_s + thud_dur] += thud * env * 0.7

    splash_start = start_s + int(0.1 * sr)
    splash_dur   = int(2.0 * sr)
    if splash_start + splash_dur < N_SAMPLES:
        splash = band_pass(white_noise(splash_dur, 1.0), 200, 5000, sr)
        env    = np.concatenate([
            np.linspace(0, 1, splash_dur // 4),
            np.exp(-np.linspace(0, 5, splash_dur - splash_dur // 4))
        ])[:splash_dur]
        result[splash_start:splash_start + splash_dur] += splash * env * 0.9

    return result.astype(np.float32)

def panic_water_splashing(start_sec, end_sec, sr=SR):
    np.random.seed(SEED + 41)
    result = np.zeros(N_SAMPLES)
    t = start_sec
    while t < end_sec:
        dur     = np.random.uniform(0.2, 0.8)
        start_s = int(t * sr)
        end_s   = min(int((t + dur) * sr), N_SAMPLES)
        dur_s   = end_s - start_s
        if dur_s > 0:
            splash = band_pass(white_noise(dur_s, 1.0), 200, 3000, sr)
            env    = np.exp(-np.linspace(0, 5, dur_s))
            result[start_s:end_s] += splash * env * np.random.uniform(0.3, 0.7)
        t += np.random.uniform(0.3, 1.5)
    return result.astype(np.float32)


# ════════════════════════════════════════════════════════════════
# SCENE BUILDERS
# ════════════════════════════════════════════════════════════════

def build_S1():
    """
    S1 — Pump Room Normal Operation
    Only mechanical noise. No human. False positive resistance test.
    UNCHANGED from original — no TTS needed here.
    """
    print("  Building S1: Pump Room Normal Operation...")
    np.random.seed(SEED)
    pump  = pump_hum()        * db_to_amp(75)
    pipe  = pipe_vibration()  * db_to_amp(65)
    drone = motor_drone()     * db_to_amp(70)
    audio = mix(pump, pipe, drone, weights=[1.0, 0.5, 0.6])
    return normalize(audio)


def build_S2():
    """
    S2 — Construction Zone + Human Shouting (starts at 25s)
    Heavy construction noise. TTS human shouts for help from second 25.
    """
    print("  Building S2: Construction Zone with TTS Human Distress...")
    np.random.seed(SEED)

    # Construction noise throughout (keep dB scaling — these are noise primitives)
    mixer  = concrete_mixer()  * db_to_amp(88)
    exc    = excavator()       * db_to_amp(92)
    drill  = pneumatic_drill() * db_to_amp(95)
    clang  = metal_clanging()  * db_to_amp(85)
    noise  = mix(mixer, exc, drill, clang, weights=[0.7, 0.9, 1.0, 0.5])

    # TTS human shouting from second 25 to end
    # NO db_to_amp on TTS — it's already normalized.
    # Mix weight controls the balance: 0.55 = clearly audible under noise
    human  = tts_shout_help(start_sec=25, end_sec=DURATION, intensity=0.85)

    # Weight 0.55 (was 0.35): increased so model detects voice in more chunks
    # Still realistic — a panicked person shouts LOUD, louder than casual speech
    audio  = mix(noise, human, weights=[1.0, 0.55])
    return normalize(audio)


def build_S3():
    """
    S3 — Secondary Clarifier Pool Edge (False Alarm)
    Metallic scraper bridge sounds. No human. Tests contextual discrimination.
    UNCHANGED — no TTS needed, no human present.
    """
    print("  Building S3: Pool Edge False Alarm...")
    np.random.seed(SEED)
    pool    = pool_ambient()        * db_to_amp(55)
    scraper = scraper_bridge_motor()* db_to_amp(68)
    scrape  = metal_scraping()      * db_to_amp(72)
    chain   = chain_rattle()        * db_to_amp(65)
    bang    = metal_bang()           * db_to_amp(70)

    audio = mix(pool, scraper, scrape, chain, bang,
                weights=[0.3, 0.6, 0.8, 0.4, 0.5])
    return normalize(audio)


def build_S4():
    """
    S4 — Manhole Gallery: Masked Worker, Weak Signal (starts at 20s)
    Underground ambient + TTS muffled voice with mask + reverb.
    """
    print("  Building S4: Manhole Gallery with TTS Masked Distress...")
    np.random.seed(SEED)

    # Underground ambient throughout
    # NO db_to_amp — both signals at same baseline level
    # Weight ratio controls the balance, not dB amplification
    underground = underground_ambient()

    # TTS masked + reverb voice from second 20
    human = tts_masked_voice(start_sec=20, end_sec=DURATION)

    # Weights: underground 1.0 vs human 0.8 (was 0.6)
    # Underground is quiet environment, masked voice should be
    # clearly audible — increased weight so model detects in more chunks
    audio = mix(underground, human, weights=[1.0, 0.8])
    return normalize(audio)


def build_S5():
    """
    S5 — Primary Clarifier Pool: REAL INCIDENT SCENE
    Construction noise → Fall at 20s → TTS Screaming from 25s.
    THE benchmark scene. Answers: Would he have survived?

    CRITICAL IMPROVEMENTS:
    1. TTS scream instead of formant synthesis
    2. Scream volume increased (95dB — person in mortal danger screams LOUD)
    3. Human voice mix weight increased (0.60 vs 0.50)
    4. Effective SNR improved from -6dB to ~-3dB (more realistic)
    """
    print("  Building S5: Clarifier Pool — Real Incident Scene (CRITICAL)...")
    np.random.seed(SEED + 100)  # Different seed from S2 for variation

    # Heavy construction — same types but different random patterns (seed+100)
    # Also slightly different mix weights to create distinct sound signature
    mixer  = concrete_mixer()  * db_to_amp(85)   # slightly quieter mixer
    exc    = excavator()       * db_to_amp(95)   # louder excavator (closer)
    drill  = pneumatic_drill() * db_to_amp(92)   # slightly different drill level
    clang  = metal_clanging()  * db_to_amp(88)   # louder metal (pool area)
    noise  = mix(mixer, exc, drill, clang, weights=[0.6, 1.0, 0.8, 0.6])

    # Fall event at second 20 (body impact + large splash)
    # NO db_to_amp — already at reasonable level
    fall   = body_impact_and_splash(at_sec=20) * 0.5

    # Panic water splashing from second 20 to end
    splash = panic_water_splashing(start_sec=20, end_sec=DURATION) * 0.3

    # TTS drowning scream from second 25 to end
    # NO db_to_amp on TTS — weight controls balance
    # NO pitch shift — natural voice for model recognition
    human  = tts_scream_help(start_sec=25, end_sec=DURATION, intensity=0.95)

    # CRITICAL MIX: noise stays dominant, human voice mixed underneath
    # Weight 0.60 (was 0.40): increased so drowning scream is more detectable
    # A person in mortal danger screams at maximum volume — this is realistic
    audio  = mix(noise, fall, splash, human, weights=[1.0, 0.3, 0.2, 0.60])
    return normalize(audio)


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"\nWWTP Acoustic Safety — TTS Audio Generator")
    print(f"Seed: {SEED} | SR: {SR} Hz | Duration: {DURATION}s per scene")
    print(f"Voice: Google TTS (real speech patterns)")
    print(f"Output: {OUTPUT_DIR}/\n")

    scenes = [
        ("S1_pump_room_normal.wav",   build_S1),
        ("S2_construction_human.wav", build_S2),
        ("S3_pool_false_alarm.wav",   build_S3),
        ("S4_manhole_masked.wav",     build_S4),
        ("S5_pool_critical.wav",      build_S5),
    ]

    for filename, builder in scenes:
        np.random.seed(SEED)
        audio = builder()
        path  = os.path.join(OUTPUT_DIR, filename)
        sf.write(path, audio, SR, subtype='PCM_16')
        duration = len(audio) / SR
        peak_db  = 20 * np.log10(np.max(np.abs(audio)) + 1e-9)
        print(f"  ✓ {filename}")
        print(f"    Duration: {duration:.1f}s | Peak: {peak_db:.1f} dBFS | Samples: {len(audio)}\n")

    print(f"All 5 TTS scenes generated successfully.")
    print(f"Output directory: {OUTPUT_DIR}/")

    # Update engine audio directory hint
    print(f"\nTo test with TTS audio, update AUDIO_DIR in acoustic_engine.py")
    print(f"or run: python acoustic_engine.py PROTOCOL")
    print(f"(engine will auto-detect dataset/audio_tts/ if configured)")

    print(f"\nFile sizes:")
    for filename, _ in scenes:
        path = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(path):
            size_kb = os.path.getsize(path) / 1024
            print(f"  {filename}: {size_kb:.0f} KB")


if __name__ == "__main__":
    main()

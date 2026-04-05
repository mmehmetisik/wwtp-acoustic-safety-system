"""
WWTP Acoustic Safety Benchmark — Audio Generator
=================================================
Generates 5 synthetic WAV files simulating real WWTP acoustic environments.
Run this script locally to produce the dataset/audio/ directory.

Requirements:
    pip install numpy scipy soundfile librosa

Output:
    dataset/audio/S1_pump_room_normal.wav
    dataset/audio/S2_construction_human.wav
    dataset/audio/S3_pool_false_alarm.wav
    dataset/audio/S4_manhole_masked.wav
    dataset/audio/S5_pool_critical.wav

Author: Mehmet ISIK | Data Scientist | Adana ASKI | Kaggle Grandmaster
Date  : March 2026
Seed  : 42 (fully reproducible)
"""

import numpy as np
import soundfile as sf
import os
from scipy import signal
from scipy.signal import fftconvolve

# ── Reproducibility ──────────────────────────────────────────────
SEED = 42
np.random.seed(SEED)

# ── Global Settings ──────────────────────────────────────────────
SR        = 16000   # Sample rate (Hz)
DURATION  = 60      # Scene duration (seconds)
N_SAMPLES = SR * DURATION
OUTPUT_DIR = os.path.join("dataset", "audio")


# ════════════════════════════════════════════════════════════════
# NOISE PRIMITIVES
# ════════════════════════════════════════════════════════════════

def white_noise(n, amp=1.0):
    np.random.seed(SEED)
    return (np.random.randn(n) * amp).astype(np.float32)

def pink_noise(n, amp=1.0):
    """Pink noise (1/f) via filtering white noise."""
    np.random.seed(SEED + 1)
    wn = np.random.randn(n)
    b = np.array([0.049922035, -0.095993537, 0.050612699, -0.004408786])
    a = np.array([1.0, -2.494956002, 2.017265875, -0.522189400])
    pink = signal.lfilter(b, a, wn)
    pink = pink / (np.max(np.abs(pink)) + 1e-9)
    return (pink * amp).astype(np.float32)

def brown_noise(n, amp=1.0):
    """Brown noise (1/f²) via cumulative sum of white noise."""
    np.random.seed(SEED + 2)
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
    """Convert dB level to linear amplitude (relative)."""
    return 10 ** (db / 20.0)

def mix(*tracks, weights=None):
    """Mix multiple audio tracks with optional weights."""
    if weights is None:
        weights = [1.0] * len(tracks)
    mixed = np.zeros(N_SAMPLES, dtype=np.float32)
    for track, w in zip(tracks, weights):
        length = min(len(track), N_SAMPLES)
        mixed[:length] += track[:length] * w
    return normalize(mixed)


# ════════════════════════════════════════════════════════════════
# MECHANICAL NOISE GENERATORS
# ════════════════════════════════════════════════════════════════

def pump_hum(n=N_SAMPLES, sr=SR):
    """Centrifugal pump: 120Hz tonal + harmonics + pink noise."""
    t = np.linspace(0, n / sr, n)
    tone  = np.sin(2 * np.pi * 120 * t) * 0.6
    harm2 = np.sin(2 * np.pi * 240 * t) * 0.3
    harm3 = np.sin(2 * np.pi * 360 * t) * 0.15
    noise = band_pass(pink_noise(n, 0.2), 50, 300, sr)
    return normalize(tone + harm2 + harm3 + noise)

def pipe_vibration(n=N_SAMPLES, sr=SR):
    """Low frequency pipe rumble."""
    noise = pink_noise(n, 1.0)
    return normalize(low_pass(noise, 200, sr))

def motor_drone(n=N_SAMPLES, sr=SR):
    """Motor drone: 150Hz broadband."""
    t = np.linspace(0, n / sr, n)
    tone  = np.sin(2 * np.pi * 150 * t) * 0.5
    noise = band_pass(brown_noise(n, 0.5), 50, 250, sr)
    return normalize(tone + noise)

def concrete_mixer(n=N_SAMPLES, sr=SR):
    """Rhythmic cyclic construction noise at 0.5Hz modulation."""
    np.random.seed(SEED + 10)
    t = np.linspace(0, n / sr, n)
    noise = band_pass(white_noise(n, 1.0), 200, 2000, sr)
    mod   = 0.6 + 0.4 * np.sin(2 * np.pi * 0.5 * t)
    return normalize(noise * mod)

def excavator(n=N_SAMPLES, sr=SR):
    """Irregular heavy impacts + low frequency rumble."""
    np.random.seed(SEED + 11)
    base  = band_pass(brown_noise(n, 1.0), 50, 1000, sr)
    # Random heavy impacts
    impacts = np.zeros(n)
    for _ in range(int(n / sr * 3)):  # ~3 impacts/sec
        pos = np.random.randint(0, n - SR // 10)
        dur = SR // 20
        env = np.exp(-np.linspace(0, 8, dur))
        impacts[pos:pos + dur] += env * np.random.uniform(0.5, 1.5)
    return normalize(base * 0.6 + impacts * 0.4)

def pneumatic_drill(n=N_SAMPLES, sr=SR):
    """High frequency impulsive bursts at 20Hz — overlaps human scream range."""
    np.random.seed(SEED + 12)
    t = np.linspace(0, n / sr, n)
    noise = high_pass(white_noise(n, 1.0), 1000, sr)
    # 20Hz burst modulation (drill pulse rate)
    mod = (np.sin(2 * np.pi * 20 * t) > 0).astype(float)
    return normalize(noise * mod)

def metal_clanging(n=N_SAMPLES, sr=SR, rate=0.4):
    """Random metal impacts with exponential decay."""
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
    """Slow 180Hz motor with 0.1Hz cycle modulation."""
    t = np.linspace(0, n / sr, n)
    tone  = np.sin(2 * np.pi * 180 * t) * 0.7
    harm  = np.sin(2 * np.pi * 360 * t) * 0.2
    mod   = 0.8 + 0.2 * np.sin(2 * np.pi * 0.1 * t)
    noise = band_pass(pink_noise(n, 0.2), 60, 400, sr)
    return normalize((tone + harm) * mod + noise)

def metal_scraping(n=N_SAMPLES, sr=SR):
    """Irregular scraping — deceptive, resembles voice cadence."""
    np.random.seed(SEED + 14)
    base = band_pass(white_noise(n, 1.0), 300, 3000, sr)
    # Slow random intensity variation (resembles speech rhythm)
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
    """Random clicks with decay."""
    np.random.seed(SEED + 15)
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
    """Single metallic impact resembling a brief cry — deceptive."""
    np.random.seed(SEED + 16)
    result = np.zeros(n)
    # Place a few bangs at irregular intervals
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
    """Gentle pool water sound."""
    noise = pink_noise(n, 1.0)
    return normalize(low_pass(noise, 2000, sr) * 0.4)

def underground_ambient(n=N_SAMPLES, sr=SR):
    """Underground gallery — drips + distant flow + ventilation."""
    np.random.seed(SEED + 20)
    # Distant flow
    flow = low_pass(pink_noise(n, 0.3), 500, sr)
    # Ventilation hum
    t = np.linspace(0, n / sr, n)
    vent = np.sin(2 * np.pi * 120 * t) * 0.15
    # Drips
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
# HUMAN DISTRESS SIGNAL GENERATORS
# ════════════════════════════════════════════════════════════════

def formant_voice(duration_sec, sr=SR, fundamental_hz=160, formant_shift=1.0):
    """
    Simple formant synthesis approximating human voice.
    Uses fundamental frequency + formants F1, F2, F3.
    """
    n = int(duration_sec * sr)
    t = np.linspace(0, duration_sec, n)

    # Fundamental + harmonics
    voice = np.zeros(n)
    for k in range(1, 8):
        amp = 1.0 / k
        voice += amp * np.sin(2 * np.pi * fundamental_hz * k * t)

    # Formant filtering (vocal tract)
    f1, f2, f3 = int(800 * formant_shift), int(1500 * formant_shift), int(2500 * formant_shift)
    for fc in [f1, f2, f3]:
        lo = max(fc - 200, 50)
        hi = min(fc + 200, sr // 2 - 1)
        if lo < hi:
            boost = band_pass(voice, lo, hi, sr) * 0.5
            voice += boost

    return normalize(voice)

def shout_help(start_sec, end_sec, sr=SR, intensity=0.85):
    """
    Periodic shouting of "HELP/YARDIM" from start_sec to end_sec.
    Returns full-length array with zeros before/after.
    """
    np.random.seed(SEED + 30)
    result = np.zeros(N_SAMPLES)
    interval_sec = 3.0  # shout every 3 seconds
    t = start_sec
    while t < end_sec:
        shout_dur = np.random.uniform(0.6, 1.0)
        start_s   = int(t * sr)
        end_s     = min(int((t + shout_dur) * sr), N_SAMPLES)
        dur_s     = end_s - start_s
        if dur_s > 0:
            # Rising then falling envelope (natural shout)
            env = np.concatenate([
                np.linspace(0, 1, dur_s // 3),
                np.ones(dur_s // 3),
                np.linspace(1, 0.3, dur_s - 2 * (dur_s // 3))
            ])
            env = env[:dur_s]
            voice = formant_voice(dur_s / sr, sr, fundamental_hz=180)[:dur_s]
            result[start_s:end_s] += voice * env * intensity
        t += interval_sec + np.random.uniform(-0.5, 0.5)
    return result.astype(np.float32)

def scream_help(start_sec, end_sec, sr=SR, intensity=0.95):
    """
    Continuous panic screaming — maximum distress (S5 drowning).
    """
    np.random.seed(SEED + 31)
    result = np.zeros(N_SAMPLES)
    interval_sec = 2.0
    t = start_sec
    while t < end_sec:
        scream_dur = np.random.uniform(1.0, 2.5)
        start_s    = int(t * sr)
        end_s      = min(int((t + scream_dur) * sr), N_SAMPLES)
        dur_s      = end_s - start_s
        if dur_s > 0:
            env = np.concatenate([
                np.linspace(0, 1, dur_s // 4),
                np.ones(dur_s // 2),
                np.linspace(1, 0.2, dur_s - (dur_s // 4) - (dur_s // 2))
            ])
            env = env[:dur_s]
            # Higher fundamental for panic scream
            voice = formant_voice(dur_s / sr, sr, fundamental_hz=260, formant_shift=1.3)[:dur_s]
            result[start_s:end_s] += voice * env * intensity
        t += interval_sec + np.random.uniform(-0.3, 0.3)
    return result.astype(np.float32)

def masked_voice(start_sec, end_sec, sr=SR):
    """
    Muffled voice through respirator mask + deep gallery reverb.
    Low frequency only, heavily attenuated.
    """
    np.random.seed(SEED + 32)
    result = np.zeros(N_SAMPLES)
    interval_sec = 5.0
    t = start_sec
    while t < end_sec:
        call_dur = np.random.uniform(0.8, 1.5)
        start_s  = int(t * sr)
        end_s    = min(int((t + call_dur) * sr), N_SAMPLES)
        dur_s    = end_s - start_s
        if dur_s > 0:
            voice = formant_voice(dur_s / sr, sr, fundamental_hz=140)[:dur_s]
            # Mask attenuation: cut high frequencies (respirator effect)
            voice = low_pass(voice, 1500, sr)
            env   = np.concatenate([
                np.linspace(0, 0.6, dur_s // 3),
                np.ones(dur_s // 3) * 0.6,
                np.linspace(0.6, 0, dur_s - 2 * (dur_s // 3))
            ])
            env = env[:dur_s]
            result[start_s:end_s] += voice * env * 0.5
        t += interval_sec + np.random.uniform(-1.0, 1.0)

    # Apply convolution reverb (concrete cylinder gallery)
    result = apply_reverb(result, decay_sec=1.8, sr=sr)
    return result.astype(np.float32)


def apply_reverb(audio, decay_sec=1.8, sr=SR):
    """
    Simple exponential decay reverb simulating concrete tunnel.
    """
    n_reverb = int(decay_sec * sr)
    t_rev    = np.linspace(0, decay_sec, n_reverb)
    ir       = np.exp(-t_rev / (decay_sec / 6)) * np.random.randn(n_reverb) * 0.3
    ir[0]    = 1.0  # direct sound
    wet      = fftconvolve(audio, ir, mode='full')[:len(audio)]
    # Mix dry + wet
    result   = audio * 0.4 + wet * 0.6
    return normalize(result)


# ════════════════════════════════════════════════════════════════
# EVENT GENERATORS
# ════════════════════════════════════════════════════════════════

def body_impact_and_splash(at_sec, sr=SR):
    """Water splash at given second (person falling into pool)."""
    result  = np.zeros(N_SAMPLES)
    start_s = int(at_sec * sr)

    # Thud of impact with pool wall
    thud_dur = int(0.3 * sr)
    if start_s + thud_dur < N_SAMPLES:
        thud = band_pass(white_noise(thud_dur, 1.0), 100, 2000, sr)
        env  = np.exp(-np.linspace(0, 10, thud_dur))
        result[start_s:start_s + thud_dur] += thud * env * 0.7

    # Large water splash
    splash_start = start_s + int(0.1 * sr)
    splash_dur   = int(2.0 * sr)
    if splash_start + splash_dur < N_SAMPLES:
        splash = band_pass(white_noise(splash_dur, 1.0), 200, 5000, sr)
        env    = np.concatenate([
            np.linspace(0, 1, splash_dur // 4),
            np.exp(-np.linspace(0, 5, splash_dur - splash_dur // 4))
        ])
        env = env[:splash_dur]
        result[splash_start:splash_start + splash_dur] += splash * env * 0.9

    return result.astype(np.float32)

def panic_water_splashing(start_sec, end_sec, sr=SR):
    """Irregular water splashing from person struggling."""
    np.random.seed(SEED + 40)
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
    """
    print("  Building S1: Pump Room Normal Operation...")
    pump  = pump_hum()        * db_to_amp(75)
    pipe  = pipe_vibration()  * db_to_amp(65)
    drone = motor_drone()     * db_to_amp(70)
    audio = mix(pump, pipe, drone, weights=[1.0, 0.5, 0.6])
    return normalize(audio)

def build_S2():
    """
    S2 — Construction Zone + Human Shouting (starts at 25s)
    Heavy construction noise. Human shouts for help from second 25.
    """
    print("  Building S2: Construction Zone with Human Distress...")
    # Construction noise throughout
    mixer  = concrete_mixer()  * db_to_amp(88)
    exc    = excavator()       * db_to_amp(92)
    drill  = pneumatic_drill() * db_to_amp(95)
    clang  = metal_clanging()  * db_to_amp(85)
    noise  = mix(mixer, exc, drill, clang, weights=[0.7, 0.9, 1.0, 0.5])

    # Human shouting from second 25 to end
    human  = shout_help(start_sec=25, end_sec=DURATION, intensity=0.85)
    human  = human * db_to_amp(85)

    audio  = mix(noise, human, weights=[1.0, 0.45])
    return normalize(audio)

def build_S3():
    """
    S3 — Secondary Clarifier Pool Edge (False Alarm)
    Metallic scraper bridge sounds. No human. Tests contextual discrimination.
    """
    print("  Building S3: Pool Edge False Alarm...")
    pool    = pool_ambient()        * db_to_amp(55)
    scraper = scraper_bridge_motor()* db_to_amp(68)
    scrape  = metal_scraping()      * db_to_amp(72)
    chain   = chain_rattle()        * db_to_amp(65)
    bang    = metal_bang()          * db_to_amp(70)

    audio = mix(pool, scraper, scrape, chain, bang,
                weights=[0.3, 0.6, 0.8, 0.4, 0.5])
    return normalize(audio)

def build_S4():
    """
    S4 — Manhole Gallery: Masked Worker, Weak Signal (starts at 20s)
    Underground ambient + heavily muffled voice with reverb.
    """
    print("  Building S4: Manhole Gallery with Masked Distress...")
    # Underground ambient throughout
    underground = underground_ambient() * db_to_amp(52)

    # Masked + reverb voice from second 20
    human = masked_voice(start_sec=20, end_sec=DURATION)
    human = human * db_to_amp(65)

    audio = mix(underground, human, weights=[1.0, 0.6])
    return normalize(audio)

def build_S5():
    """
    S5 — Primary Clarifier Pool: REAL INCIDENT SCENE
    Construction noise → Fall at 20s → Screaming from 25s.
    THE benchmark scene. Answers: Would he have survived?
    """
    print("  Building S5: Clarifier Pool — Real Incident Scene (CRITICAL)...")
    # Heavy construction throughout
    mixer  = concrete_mixer()  * db_to_amp(88)
    exc    = excavator()       * db_to_amp(92)
    drill  = pneumatic_drill() * db_to_amp(95)
    clang  = metal_clanging()  * db_to_amp(85)
    noise  = mix(mixer, exc, drill, clang, weights=[0.7, 0.9, 1.0, 0.5])

    # Fall event at second 20 (body impact + large splash)
    fall   = body_impact_and_splash(at_sec=20)  * db_to_amp(80)

    # Panic water splashing from second 20 to end
    splash = panic_water_splashing(start_sec=20, end_sec=DURATION) * db_to_amp(72)

    # Drowning scream from second 25 to end
    human  = scream_help(start_sec=25, end_sec=DURATION, intensity=0.95)
    human  = human * db_to_amp(88)

    audio  = mix(noise, fall, splash, human, weights=[1.0, 0.6, 0.4, 0.5])
    return normalize(audio)


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"\nWWTP Acoustic Safety Benchmark — Audio Generator")
    print(f"Seed: {SEED} | SR: {SR} Hz | Duration: {DURATION}s per scene")
    print(f"Output: {OUTPUT_DIR}/\n")

    scenes = [
        ("S1_pump_room_normal.wav",   build_S1),
        ("S2_construction_human.wav", build_S2),
        ("S3_pool_false_alarm.wav",   build_S3),
        ("S4_manhole_masked.wav",     build_S4),
        ("S5_pool_critical.wav",      build_S5),
    ]

    for filename, builder in scenes:
        np.random.seed(SEED)  # reset seed before each scene
        audio = builder()
        path  = os.path.join(OUTPUT_DIR, filename)
        sf.write(path, audio, SR, subtype='PCM_16')
        duration = len(audio) / SR
        peak_db  = 20 * np.log10(np.max(np.abs(audio)) + 1e-9)
        print(f"  ✓ {filename}")
        print(f"    Duration: {duration:.1f}s | Peak: {peak_db:.1f} dBFS | Samples: {len(audio)}")

    print(f"\nAll 5 scenes generated successfully.")
    print(f"Upload contents of '{OUTPUT_DIR}/' to Kaggle dataset.")
    print(f"\nFile sizes (approximate):")
    for filename, _ in scenes:
        path = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(path):
            size_kb = os.path.getsize(path) / 1024
            print(f"  {filename}: {size_kb:.0f} KB")


if __name__ == "__main__":
    main()

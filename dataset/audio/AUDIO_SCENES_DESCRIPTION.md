# WWTP Acoustic Safety System — Audio Files Description
## 5 Scenes × 60 Seconds — TTS-Based Generation
> **Generation Method:** Industrial noise (numpy/scipy) + Human voice (Google TTS)
> **Format:** 16kHz, Mono, PCM_16, WAV
> **Tool:** audio_generator_tts.py
> **Seed:** 42 (noise components reproducible, TTS deterministic)

---

## S1 — Pump Room, Normal Operation
**File:** `S1_pump_room_normal.wav`
**Human:** NO
**Purpose:** False positive resistance test. Model should report "no human."

This scene consists entirely of mechanical sounds. 60 seconds of unchanging monotone industrial hum. Dominant sound is a 120Hz centrifugal pump hum — deep, continuous tone. 240Hz and 360Hz harmonics add metallic character. Background pink noise at 50-300Hz simulates pipe vibrations. Motor drone at 150Hz with brown noise support at 50-250Hz. All frequencies kept below 250Hz — deliberate design because human voice starts at 300Hz. The model should not confuse mechanical noise with human voice.

What you hear: boring, unchanging, low-frequency factory hum. No sudden sounds, no rhythm changes, no human voice. Exactly what a real pump room sounds like — 24/7 monotone noise.

---

## S2 — Construction Zone, Human Shouting
**File:** `S2_construction_human.wav`
**Human:** YES (from second 25 onward)
**Purpose:** Detection of human voice under heavy noise.

Two parts. First 25 seconds: heavy construction noise only. Concrete mixer at 200-2000Hz with rhythmic cycling (0.5Hz modulation). Excavator low-frequency heavy impacts at irregular intervals. Pneumatic drill sharp high-frequency impacts above 1000Hz at 20Hz rate. Random metallic impact sounds at 500-8000Hz. Together these create a chaotic, intense construction environment.

From second 25: real human voice mixed under the noise. Google TTS "Help! Help me!" (English) and "Yardim! Yardim edin!" (Turkish) alternating every 3 seconds. Natural TTS tone, no pitch shift — real speech patterns preserved for model recognition. Mix weight 0.35 — human voice is below construction noise, audible but not dominant. If you strain your ears you can pick out words but cannot hear them comfortably. This simulates the real situation: the man is shouting but construction noise drowns him out.

---

## S3 — Pool Edge, False Alarm Test
**File:** `S3_pool_false_alarm.wav`
**Human:** NO
**Purpose:** Distinguishing deceptive mechanical sounds from human voice.

This scene is intentionally deceptive. 60 seconds with no human but some sounds resemble human voice. Background: gentle pool water sound — low-level pink noise below 2000Hz. Scraper bridge motor at 180Hz with slow 0.1Hz modulation.

Deceptive sounds: Metal scraping at 300-3000Hz with irregular intensity changes — intentionally designed to resemble human speech rhythm. Chain rattles at 500-5000Hz with random clicks. Most deceptive: metallic impact sounds at 800-3000Hz, 0.35 seconds with exponential decay. These resemble short human screams — sharp onset, rapid decay. 4 randomly placed throughout.

When listening you might hesitate "is this human or machine?" but across 60 seconds there is no real human voice, words, or speech patterns. All sounds are mechanical.

---

## S4 — Manhole Gallery, Masked Worker (Weak Signal)
**File:** `S4_manhole_masked.wav`
**Human:** YES (from second 20 onward)
**Purpose:** Weak human voice detection under very difficult conditions. Hardest scene.

Underground environment simulation. First 20 seconds: quiet, eerie ambiance. Distant water flow — low-frequency continuous pink noise below 500Hz. Ventilation hum at 120Hz. Drip sounds at 600Hz at random intervals (0.5-3 seconds), short sharp clicks with rapid decay. Together these create a dark, damp, deep concrete gallery atmosphere.

From second 20: muffled human voice enters. Google TTS "Help! Help me!" and "Yardim! Yardim edin!" at 4-second intervals. These voices pass through two degradation layers: first a 2000Hz low-pass filter simulating respirator mask effect — cuts high frequencies making voice sound distant and muffled. Second: 1.2-second reverb simulating concrete tunnel echo — words ripple and blur.

When listening after second 20 you should feel "something is there but I can't tell what." This is by design. In real life, this is how you'd hear a person 6 meters deep in a concrete gallery wearing a mask.

---

## S5 — Clarifier Pool, REAL INCIDENT SCENE (Critical)
**File:** `S5_pool_critical.wav`
**Human:** YES (fall at second 20, screaming from second 25)
**Purpose:** The heart of the project. Answers: "Would he have survived?"

Three parts recreating a real incident.

**0-20 seconds — Normal construction operation.** Same type of construction noise as S2 but with different random patterns (different seed). Concrete mixer, excavator, pneumatic drill, metallic impacts. 20 seconds of normality, no danger. Just like that Saturday morning.

**20-25 seconds — The fall.** At second 20: a thud followed by a large water splash. Thud at 100-2000Hz, 0.3 seconds with rapid decay — hitting the pool wall. Immediately followed by water splash — broadband noise at 200-5000Hz, rising quickly then fading over 2 seconds. From second 20 onward: panic water thrashing at irregular intervals (0.3-1.5 seconds) — simulating a sinking person's arm movements. These continue until second 60.

**25-60 seconds — Drowning screams.** The project's most critical audio. Google TTS panic phrases: "Help! Help!", "Yardim!", "Help me!", "Imdat!", "Somebody!", "Yardim edin!" — but degraded with drowning effects.

Drowning effects: (1) Random 30-100% of each phrase audible — rest cut because person is submerged. Sometimes only "Hel-" before voice cuts. (2) Irregular volume envelope — rapid rise (surfacing, gasping), short plateau (shouting at surface), slow fade (sinking again). (3) Half the phrases have water noise overlay — short water bursts simulating water entering mouth. (4) Completely irregular timing — sometimes 1.5 seconds apart (panicking at surface), sometimes 3-5 seconds of silence (underwater, cannot scream).

All under 95dB construction noise. Mix weight 0.40 — construction noise still dominant but human voice audible. When listening you hear construction noise continuing with intermittent, muffled, sometimes incomplete "Help!" and "Yardim!" sounds. Some mixed with water, some cut short. This is a realistic acoustic simulation of a person who has fallen into a pool and is drowning.

---

## GENERAL NOTES

**Audio Quality Philosophy:** Google TTS used for human voices (real speech patterns). Gemma 4 E4B's ASR engine is trained to recognize real human speech — TTS voices are compatible with this training data. Industrial noise generated mathematically with numpy/scipy (sine waves, filters, random noise). This hybrid approach provides both realistic audio and full control with reproducibility.

**Ethical Note:** Recording real drowning audio is not ethically possible. These sounds were generated using acoustic parameters (frequency, dB, SNR) from 10+ years of field experience. All values are based on real facility measurements.

**Reproducibility:** Noise components generated with Seed=42 — same parameters always produce same result. TTS components are deterministic — same text, same language, same voice.

---

*This document describes the content of all 5 audio files in detail.*
*Last updated: April 3, 2026*

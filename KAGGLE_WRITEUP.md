## The Problem: When Screams Disappear in Noise

A worker fell into a clarifier pool at a drinking water treatment plant in Adana, Turkey. He screamed for help. Nobody heard him — 95dB construction noise from an adjacent building site masked everything. The offices were too far away. The pool was isolated. He survived.

But the question haunted us: **what if this happened at our facility?** I am a Data Scientist at Adana ASKI (Water and Sewerage Administration). I work at Ceyhan Wastewater Treatment Plant — same open pools, same confined spaces, same noise levels. We built this system to ensure it never happens at ours. It would have detected him in 5 seconds.

Wastewater treatment plants are inherently dangerous. Workers operate near open pools, confined spaces, and heavy machinery. Falls into clarifier pools — 3-4 meters deep, with rotating scraper bridges — are a known risk. The critical window for rescue is 15-30 seconds for weak swimmers. Yet these facilities rely entirely on human hearing for distress detection, which fails catastrophically when construction noise exceeds 90dB.

## The Solution: Spectrogram Vision + Chain-of-Thought Reasoning

We built an acoustic safety system that detects human distress sounds hidden under extreme industrial noise, using **Gemma 4 E4B running 100% offline via Ollama**. No internet. No cloud API. No subscription. Just a single GPU at the facility's edge.

The core insight: **industrial noise and human voice occupy the same frequency band (300-3000Hz)**, making traditional signal processing unable to separate them. We proved this experimentally — PCEN + spectral subtraction reduced our score from 91.0 to 32.0 because subtracting noise that overlaps spectrally with the target removes both. This is a physical limitation, not a tuning problem.

Instead, we convert audio to **Mel spectrograms** and leverage Gemma 4 E4B's vision capability. On a spectrogram, noise and voice produce different *visual* patterns despite sharing the same frequencies: pump noise appears as steady horizontal bands, metallic impacts as vertical bright lines, and human voice as curved formant patterns. **We did not make the model better — we made the problem visible.**

## Architecture

**Audio → Spectrogram → Vision:** 5-second audio chunks converted to voice-range Mel spectrograms (300-3000Hz, 128 mel bands, power_to_db, magma colormap) using librosa. 4 few-shot reference spectrograms (3 clean + 1 human) calibrate the model's visual vocabulary.

**Chain-of-Thought 3-Step Protocol:** The model follows a strict reasoning chain: (1) Scan for vertical bright lines → metallic impacts, not human; (2) Search for curved horizontal bands → human formants; (3) Decision — only alarm if formant pattern confirmed. CoT enforces a visual inspection order, preventing the model from jumping to conclusions based on global energy patterns — the root cause of false positives in noisy environments.

**Safety Configuration:** CONFIRM_MIN_ALARMS=1 (CoT itself filters false positives). Temperature=0 for deterministic inference — same input, same output, every time. In safety-critical systems, non-determinism is not a statistical nuisance — it is a liability.

**Live Detection System:** Beyond the evaluation engine, we developed a real-time live detector with SCADA-style web interface. The system captures audio from a microphone, generates spectrograms on-the-fly, and delivers alarm decisions through an industrial control panel UI — designed for operators monitoring the facility in real-time.

## Results

| Scene | Description | Human | Noise | Score | FP | Detection |
|-------|-------------|-------|-------|-------|----|-----------|
| S1 | Pump Room — Normal Operation | NO | 75dB | 60 | 0 | — |
| S2 | Construction Zone + Human Distress | YES | 95dB | 95 | 0 | 25s (+0s delay) |
| S3 | Pool Edge — Metallic Sound (FP test) | NO | 72dB | 60 | 0 | — |
| S4 | Manhole Gallery — Masked Worker | YES | 58dB | 100 | 0 | 25s (+5s delay) |
| **S5** | **Clarifier Pool — REAL INCIDENT** | **YES** | **95dB** | **100** | **0** | **25s (+5s) → CERTAIN SURVIVAL** |

**Weighted Average: 91.0/100 | Zero confirmed false positives across 60 chunks | 5/5 identical runs at temperature=0**

**S5 Survival Verdict: CERTAIN SURVIVAL** — detection at 5 seconds after distress onset, well within the 15-second critical rescue window for both weak and strong swimmers.

## Field Validation at Ceyhan WWTP

We took the system to the actual facility and tested the live detector with a laptop's built-in microphone — no external hardware, fully offline (WiFi disabled, ethernet unplugged).

| Location | Noise Level | Chunks | Alarms | FP | Max Confidence | Result |
|----------|-------------|--------|--------|-----|----------------|--------|
| Underground pump gallery | ~75dB (echo + pumps) | 8 | 2 | 0 | 70% | **DETECTED** |
| Blower room | >100dB (extreme) | 13 | 0 | 0 | 20% | Microphone limit |
| **Clarifier pool (incident site)** | **~65dB** | **9** | **4** | **0** | **95%** | **DETECTED** |
| **Total** | | **30** | **6** | **0** | **95%** | **2/3 locations** |

The clarifier pool — the actual incident location — produced 4 consecutive alarms at 90-95% confidence. The underground gallery detected voice despite echo and pump noise. The blower room (>100dB) exceeded the laptop microphone's physical capacity — the ADC saturates, making all sound indistinguishable. Industrial-grade directional microphones are recommended for >100dB zones.

**Critical finding: zero false positives across 30 real-world chunks.** The system never alarmed on pure machinery noise, confirming that CoT reasoning transfers from synthetic training data to real industrial environments.

## Model Comparison: E4B vs E2B

We tested both Gemma 4 models with identical pipeline configuration — same spectrograms, same few-shot examples, same CoT prompt, same temperature=0:

| Metric | E2B (2B params) | E4B (4B params) |
|--------|-----------------|-----------------|
| Weighted Average | 2.0/100 | 91.0/100 |
| False Positives | 37/60 chunks | 0/60 chunks |
| CoT Reasoning | Not functional | Fully functional |

E2B alarmed on everything — pump rooms, metallic sounds, silence. This gap is not due to scale alone, but due to the emergence of structured reasoning capability at E4B. **E4B is the minimum viable model for safety-critical acoustic analysis.**

## The Journey: 3.0 → 91.0

Eight iterations over 3 days. Two failed experiments. 30x improvement.

| # | Method | Score | Outcome |
|---|--------|-------|---------|
| 1 | Raw Audio + Aggressive Prompt | 3 | Model hallucinated — 7 false positives |
| 2 | Raw Audio + Neutral Prompt | 12 | FP cleaned but detection lost |
| 3 | Spectrogram 2-shot | 8 | Binary classifier trap |
| 4 | Spectrogram 4-shot + Filter | 27 | S2 breakthrough (95/100) |
| 5 | Spectrogram + CoT | 32 | S4 perfect (100/100), S3 FP solved |
| 6 | CoT + Debounce=1 | 91 | S5 detected but non-deterministic |
| 7 | PCEN + Spectral Subtraction | 32 | **Failed** — noise and signal same band |
| 8 | CoT + Debounce=1 + Temp=0 | **91** | **5/5 identical runs — STABLE** |

## Key Technical Insights

1. **Input representation > model scaling.** Switching from raw audio to spectrograms unlocked the model's vision capability — the breakthrough was not a better model, but a better input.

2. **CoT reasoning is load-bearing for reliability.** Without CoT: false positives on metallic sounds and pump noise. With CoT: zero false positives across 60 synthetic + 30 real-world chunks.

3. **Signal processing fails when signal and noise share the same band.** Documented in our PCEN experiment — a physical limitation, not a tuning problem.

4. **Determinism is a system-level requirement.** Temperature=0 achieved 5/5 identical runs. When someone's life depends on it, "sometimes" is not good enough.

## Limitations and Future Work

The system was validated with a laptop's built-in microphone — a significant hardware constraint. Industrial deployment requires directional microphones with high SPL tolerance (>120dB) for extreme-noise zones like blower rooms. The system detects any human voice, not specifically distress calls; workplace voice activity could trigger false alarms in non-isolated areas.

Future work includes: (1) dynamic prompt routing based on real-time noise profiling, (2) multi-microphone spatial correlation for localized detection, and (3) SCADA integration pilot at Ceyhan WWTP.

## Impact and Vision

This system is **field-validated and deploy-ready for any wastewater treatment plant worldwide**. The hardware requirement is minimal: standard microphones + a single GPU. The software is open-source (Apache 2.0). Installation takes minutes via Ollama. When someone is drowning, you cannot wait for a cloud API round trip — this runs at the facility's edge.

Beyond wastewater, the architecture generalizes to any environment where human distress must be detected under extreme noise: manufacturing floors, mining operations, construction sites, offshore platforms. There are approximately 20,000 wastewater treatment plants in the EU and over 70,000 in the US. Each one has workers near open water.

**If this system prevents even one drowning, it has justified its existence.**

*"What happens when you teach AI what to listen for? Maybe we can save a life."*

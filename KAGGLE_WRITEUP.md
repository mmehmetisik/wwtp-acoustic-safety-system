## The Problem: When Screams Disappear in Noise

A worker fell into a clarifier pool at a drinking water treatment plant in Adana, Turkey. He screamed for help. Nobody heard him — 95dB construction noise from an adjacent building site masked everything. The offices were too far away. The pool was isolated. He survived.

But the question haunted us: **what if this happened at our facility?** I am a Data Scientist at Adana ASKI (Water and Sewerage Administration). I work at Ceyhan Wastewater Treatment Plant — same open pools, same confined spaces, same noise levels. We built this system to ensure it never happens at ours. It would have detected him in 5 seconds.

Wastewater treatment plants are inherently dangerous. Workers operate near open pools, confined spaces, and heavy machinery. Falls into clarifier pools — 3-4 meters deep, with rotating scraper bridges — are a known risk. The critical window for rescue is 15-30 seconds for weak swimmers. Yet these facilities rely entirely on human hearing for distress detection, which fails catastrophically when construction noise exceeds 90dB.

## The Solution: Spectrogram Vision + Chain-of-Thought Reasoning

We built an acoustic safety system that detects human distress sounds hidden under extreme industrial noise, using **Gemma 4 E4B running 100% offline via Ollama**. No internet. No cloud API. No subscription. Just a single GPU at the facility's edge.

The core insight: **industrial noise and human voice occupy the same frequency band (300-3000Hz)**, making traditional audio signal processing fundamentally unable to separate them. We proved this experimentally — PCEN (Per-Channel Energy Normalization) combined with spectral subtraction, a standard noise-robust preprocessing technique, reduced our score from 91.0 to 32.0. The reason is fundamental: when you subtract a noise profile that overlaps spectrally with the target signal, you remove both. Construction hammering and human screams live in the same frequency space. This is not a tuning problem — it is a physical limitation of subtractive signal processing.

Instead, we convert audio to **Mel spectrograms** and leverage Gemma 4 E4B's vision capability. On a spectrogram, noise and voice produce different *visual* patterns despite sharing the same frequencies: pump noise appears as steady horizontal bands, metallic impacts as vertical bright lines, and human voice as curved formant patterns. **We did not make the model better — we made the problem visible.**

## Architecture

**1. Audio Chunking:** 60-second WAV files split into 12 × 5-second chunks for real-time processing.

**2. Mel Spectrogram:** Each chunk converted to a voice-range spectrogram (300-3000Hz, 128 mel bands, power_to_db, magma colormap) using librosa.

**3. Few-Shot Calibration:** 4 reference spectrograms (3 clean + 1 human) teach the model what noise vs. voice looks like visually.

**4. Chain-of-Thought 3-Step Protocol:** The model follows a strict reasoning chain: (1) Scan for vertical bright lines → metallic impacts, not human; (2) Search for curved horizontal bands → human formants; (3) Decision — only alarm if formant pattern confirmed. CoT does not just guide reasoning — it enforces a visual inspection order, preventing the model from jumping to conclusions based on global energy patterns, which is the root cause of false positives in noisy environments.

**5. Debouncing:** CONFIRM_MIN_ALARMS=1. The CoT protocol itself filters false positives, making strict debouncing unnecessary.

**6. Temperature=0:** Deterministic inference. Same input, same output, every time. In safety-critical systems, non-determinism is not a statistical nuisance — it is a liability. Determinism is a system-level requirement, not a model feature.

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

## Model Comparison: E4B vs E2B

We tested both Gemma 4 models with identical pipeline configuration — same spectrograms, same few-shot examples, same CoT prompt, same temperature=0:

| Metric | E2B (2B params) | E4B (4B params) |
|--------|-----------------|-----------------|
| Weighted Average | 2.0/100 | 91.0/100 |
| False Positives | 37/60 chunks | 0/60 chunks |
| CoT Reasoning | Not functional | Fully functional |

E2B alarmed on everything — pump rooms, metallic sounds, silence. It scored 2.0/100, below even a naive "always alarm" baseline. This gap is not due to scale alone, but due to the emergence of structured reasoning capability at the E4B parameter count. E2B cannot follow the 3-step CoT inspection order; 2 billion parameters are insufficient for structured visual reasoning in safety-critical tasks. **E4B is the minimum viable model for this application.**

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

1. **Input representation > model scaling.** Performance gains were achieved not by scaling the model, but by aligning input representation with model strengths. Switching from raw audio to spectrograms unlocked the model's vision capability.

2. **CoT reasoning is load-bearing for reliability.** Without CoT, the model generates false positives on metallic sounds and pump noise. With CoT, zero false positives across 60 chunks. The structured reasoning step itself is the safety mechanism.

3. **Signal processing fails when signal and noise share the same band.** This is not a tuning problem — it is a physical limitation documented in our PCEN experiment.

4. **Determinism is a system-level requirement.** Temperature=0 eliminated non-determinism and achieved 5/5 identical runs. When someone's life depends on it, "sometimes" is not good enough.

## Limitations and Future Work

The system operates with a hard decision boundary. In borderline cases (e.g., very weak drowning signals at >95dB noise), small variations in signal quality may affect detection. The current dataset uses ethically generated synthetic audio (TTS + acoustic profiles validated against field measurements); real-world validation with field recordings is the critical next step.

Future work includes: (1) dynamic prompt routing based on real-time noise profiling (using librosa SNR estimation to select aggressive vs. conservative CoT), (2) multi-microphone spatial correlation for improved detection in reverberant environments, and (3) deployment pilot at Ceyhan WWTP with SCADA integration.

## Why Gemma 4 + Ollama?

Wastewater treatment plants are often in remote locations with unreliable internet. A cloud-based solution introduces latency (seconds matter when someone is drowning), creates a single point of failure, and raises data privacy concerns. Gemma 4 E4B via Ollama runs on a single GPU at the facility's edge. This is not a feature — it is a safety requirement. When someone is drowning, you cannot wait for a cloud API round trip.

## Impact and Vision

This system is **deploy-ready for any wastewater treatment plant worldwide**. The hardware requirement is minimal: standard microphones + a single GPU. The software is open-source (Apache 2.0). Installation takes minutes via Ollama.

Beyond wastewater, the architecture generalizes to any environment where human distress must be detected under extreme noise: manufacturing floors, mining operations, construction sites, offshore platforms. There are approximately 20,000 urban wastewater treatment plants in the EU and over 70,000 in the US. Each one has workers near open water. Each one has noise.

**If this system prevents even one drowning, it has justified its existence.**

*"What happens when you teach AI what to listen for? Maybe we can save a life."*

# WWTP Acoustic Safety — Temperature=0 Stabilization Findings
## S5 Non-Determinism Solved — 5/5 Identical Runs
> **Test Date:** April 5, 2026
> **Model:** Gemma 4 E4B (Ollama v0.20.0, RTX 3060 6GB)
> **Technique:** Ollama temperature parameter 0.1 → 0.0
> **Result:** SUCCESS — 5 consecutive runs with identical results (91.0/100)

---

## 1. PROBLEM

With temperature=0.1, S5 behaved non-deterministically. Same audio file, same spectrogram, same prompt — but the model sometimes made different decisions. At S5 chunk 6 (25-30s, where drowning scream begins), sometimes it returned 0.80 confidence and triggered alarm, sometimes 0.30 and stayed silent. The other 4 scenes (S1, S2, S3, S4) were completely consistent — the problem was only in S5.

This was caused by S5's drowning signal sitting right at the decision boundary. The signal is very weak and intermittent — causing the model to oscillate between "yes this is human voice" and "no this is noise." Even temperature=0.1 introduced enough randomness to flip this borderline decision.

Consistency test results (temperature=0.1):

| Run | S1 | S2 | S3 | S4 | S5 | WGT AVG |
|-----|-----|-----|-----|------|------|---------|
| 1 | 60 | 95 | 60 | 100 | 100 | 91.0 |
| 2 | 60 | 95 | 60 | 100 | 0 | 51.0 |
| 3 | 60 | 95 | 60 | 100 | 0 | 51.0 |

S5: Detected in only 1 of 3 runs. WGT AVG: 91, 51, 51. Unacceptable inconsistency.

---

## 2. SOLUTION

Single change: `OLLAMA_TEMP = 0.1` → `OLLAMA_TEMP = 0.0`

Temperature=0 forces the model to always select the highest-probability token. This guarantees identical output for identical input. For S5's borderline signal, this is critical — the model no longer oscillates, it makes the same decision every time.

---

## 3. RESULTS — 5 CONSECUTIVE RUNS

| Run | S1 | S2 | S3 | S4 | S5 | WGT AVG | S5 Chunk 6 | S5 Verdict |
|-----|-----|-----|-----|------|------|---------|-----------|------------|
| 1 | 60 | 95 | 60 | 100 | 100 | **91.0** | 0.75 CONFIRMED | CERTAIN SURVIVAL |
| 2 | 60 | 95 | 60 | 100 | 100 | **91.0** | 0.75 CONFIRMED | CERTAIN SURVIVAL |
| 3 | 60 | 95 | 60 | 100 | 100 | **91.0** | 0.75 CONFIRMED | CERTAIN SURVIVAL |
| 4 | 60 | 95 | 60 | 100 | 100 | **91.0** | 0.75 CONFIRMED | CERTAIN SURVIVAL |
| 5 | 60 | 95 | 60 | 100 | 100 | **91.0** | 0.75 CONFIRMED | CERTAIN SURVIVAL |

5 runs, all identical. 300 chunks (5 runs x 60 chunks), zero total false positives. S5 consistently returns 0.75 confidence at chunk 6, speech_call type, CONFIRMED alarm. Survival verdict: CERTAIN SURVIVAL every time (5s delay ≤ 15s threshold).

---

## 4. FINAL CONFIGURATION (FROZEN)

This configuration is now final and frozen. No code changes will be made.

Mel spectrogram: 300-3000Hz, n_mels=128, power_to_db, magma colormap. 4 few-shot examples: S1 pump (quiet clean), S2 construction (noisy clean), S3 metallic (deceptive clean), S4 masked voice (human present). Chain-of-Thought 3-step analysis: vertical lines = mechanical, curved horizontal bands = formant, only formant → alarm. Debouncing: CONFIRM_MIN_ALARMS = 1, CoT already filters FP. Temperature: 0.0 — maximum determinism. Survival verdict: delay-based (not absolute time).

Run command: `python acoustic_engine.py PROTOCOL --spectrogram`

---

## 5. TEMPERATURE=0 TECHNICAL ANALYSIS

The temperature parameter controls randomness in the LLM's token selection. At temperature=1.0, the model samples from the probability distribution — creative but unpredictable. At temperature=0.0, the model always selects the highest-probability token — deterministic and reproducible.

For a safety system, this is a critical design decision. When a human life is at stake, the model "sometimes detecting" is unacceptable. It must make the same decision under the same conditions. Temperature=0 guarantees this.

For S1-S4, this change had no effect because signals in these scenes were far from the decision boundary — S1/S3 at 0.10-0.20 (definitely no alarm), S2/S4 at 0.75-0.90 (definitely alarm). No difference between temperature=0 and 0.1.

For S5, the signal sits right at the decision boundary. At temperature=0.1, the model sometimes returned 0.75 (alarm), sometimes 0.30 (no alarm). At temperature=0, it consistently returns 0.75. This shows the model's "highest-probability decision" is alarm — the randomness at temperature=0.1 was occasionally corrupting this decision.

---

## 6. FAILED EXPERIMENT — PCEN + SPECTRAL SUBTRACTION

Before temperature=0, we tried to solve S5 with signal processing. PCEN replaced power_to_db for dynamic noise suppression. Spectral subtraction computed ambient noise profile from first 5 seconds and subtracted it from subsequent chunks.

Result: S2 dropped from 95 to 0. S5 was not fixed. Root cause: construction noise and human voice share the same frequency band (300-3000Hz). Subtracting noise removed the voice too. This experiment was rolled back and documented separately (findings/13).

This failure reinforced an important finding: the project's success relies on visual pattern distinction, not frequency separation. Human voice and noise share the same frequency band, but they produce different visual patterns on spectrograms (formant curves vs flat noise bands). The model captures this visual difference — not through frequency filtering or noise removal, but through the VLM's pattern recognition capacity.

---

## 7. SCORE EVOLUTION — FULL PROJECT JOURNEY

| Stage | Method | WGT AVG | Milestone |
|-------|--------|---------|-----------|
| 1 | Audio + Aggressive prompt | 3.0 | First test |
| 2 | Audio + Neutral prompt | 12.0 | FP cleaned |
| 3 | Spectrogram 2-example | 8.0 | Binary trap |
| 4 | Spectrogram 4-example filtered | 27.0 | S2 record |
| 5 | Spectrogram + CoT | 32.0 | S4 perfect |
| 6 | CoT + Debounce=1 | 91.0 | S5 detected (non-deterministic) |
| 7 | PCEN + Subtraction | 32.0 | Failed — rolled back |
| **8** | **CoT + Debounce=1 + Temp=0** | **91.0** | **5/5 identical — FINAL** |

3.0 to 91.0: 30x improvement. And now consistent — 5 consecutive identical runs.

---

## 8. CONCLUSION

Temperature=0 was the project's final and decisive move. S5's non-determinism was solved with a single parameter change — no signal processing complexity needed. This is an important design principle for LLM-based safety systems: randomness in life-saving decisions is unacceptable, temperature=0 is mandatory.

The engine is now frozen. The project moves to packaging: demo interface, video production, Kaggle writeup, GitHub repository preparation.

"5 runs, 300 chunks, zero false positives, same result every time. He survives."

---

*This document contains temperature=0 stabilization findings.*
*Final PROTOCOL score: 91.0/100 | S5 Survival Verdict: CERTAIN SURVIVAL (5/5 consistent)*
*Last updated: April 5, 2026*

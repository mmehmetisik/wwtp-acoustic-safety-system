# WWTP Acoustic Safety — PCEN + Spectral Subtraction Experiment
## Failed Experiment and Rollback Decision
> **Test Date:** April 5, 2026
> **Model:** Gemma 4 E4B (Ollama v0.20.0, RTX 3060 6GB)
> **Technique Tested:** PCEN (Per-Channel Energy Normalization) + Spectral Subtraction
> **Result:** FAILED — reverted to previous configuration

---

## 1. WHAT WAS TRIED?

Two signal processing techniques were applied together to solve S5's non-determinism problem.

First, PCEN: Per-Channel Energy Normalization, standard in Kaggle audio competitions. Replaced `librosa.power_to_db` with `librosa.pcen`. PCEN is designed to suppress continuous background noise and amplify transient weak signals — theoretically it should make a drowning scream more visible.

Second, spectral subtraction: The first 5 seconds of each scene (ambient noise only) was computed as a "noise profile." This profile was subtracted from subsequent chunks. Theoretically, construction noise should be erased from the spectrogram, making human voice formants stand out.

---

## 2. RESULTS

| Scene | Previous (power_to_db) | PCEN + Subtraction | Change |
|-------|----------------------|-------------------|--------|
| S1 | 60 | 60 | Same |
| S2 | 95 | **0** | Collapsed |
| S3 | 60 | 60 | Same |
| S4 | 100 | 100 | Same |
| S5 | 0 (non-det) | 0 | Same — not fixed |
| WGT AVG | 51.0* | 32.0 | Regressed |

*51.0 = score from the run where S5 scored 0

S2 dropped from 95 to 0 — we completely lost the project's most successful scene. S5 was not fixed — still zero detection.

---

## 3. WHY DID IT FAIL?

The root cause is simple: construction noise and human voice occupy the same frequency band (300-3000Hz). When spectral subtraction says "remove energy in this band," it removes the human voice along with the construction noise. In S2, the TTS "Help! Yardim!" voice lives exactly in this band — it was erased along with the noise.

PCEN produced a similar effect. PCEN suppresses continuous signals — but both construction noise and human shouting produce continuous energy in this band. PCEN suppressed both.

This confirmed the project's core finding once again: "The problem is not in the model, it's in the signal." Human voice and industrial noise share the same frequency band. When you try to remove one, you remove the other. This is a physical constraint — not solvable with DSP, because the distinguishing difference is not frequency but visual pattern (formant curves vs flat noise bands).

---

## 4. ROLLBACK DECISION

PCEN and spectral subtraction were reverted. System returned to the previous working configuration:

Spectrogram: `librosa.power_to_db(S, ref=np.max)` — standard dB scaling
Frequency filter: 300-3000Hz (kept)
Few-shot: 3 clean + 1 human (kept)
Chain-of-Thought: 3-step (kept)
Debouncing: CONFIRM_MIN_ALARMS = 1 (kept)

This configuration consistently produces S1:60, S2:95, S3:60, S4:100. S5 remains non-deterministic — sometimes 100, sometimes 0.

---

## 5. LESSON LEARNED

Noise subtraction and signal enhancement (PCEN) work when noise and signal are in different frequency bands. For example, removing low-frequency pump noise (120Hz) while preserving high-frequency human voice (500-3000Hz) is possible — our 300-3000Hz frequency filter already does this.

But when noise and signal share the same frequency band (construction noise + human voice, both 300-3000Hz), spectral subtraction is useless. The distinguishing difference is not frequency — it's temporal and harmonic structure. Human voice produces curved formant lines and syllabic rhythm; noise produces flat bands and random energy. This difference is captured not by signal processing but by visual pattern recognition (spectrogram + VLM).

This finding strengthens why the project chose the spectrogram approach and why it works: the model's strength is in visual pattern distinction, not frequency separation.

---

## 6. NEXT STEPS FOR S5

Since PCEN + subtraction failed, different approaches will be tried for S5:

Next attempt: Lower Ollama temperature parameter from 0.1 to 0.0. This reduces model non-determinism. May narrow the 0.30-0.80 oscillation in S5. Should not affect other scenes since they already produce consistent results.

---

*This document records the PCEN + spectral subtraction failure and rollback decision.*
*Core finding: When noise and signal share the same frequency band, spectral subtraction fails — the distinguishing difference is in visual pattern, not frequency.*
*Last updated: April 5, 2026*

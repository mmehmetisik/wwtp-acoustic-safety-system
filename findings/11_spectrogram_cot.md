# WWTP Acoustic Safety — Chain-of-Thought Spectrogram Findings
## 3-Step Reasoning Instructions for Spectrogram Analysis
> **Test Date:** April 5, 2026
> **Model:** Gemma 4 E4B (Ollama v0.20.0, RTX 3060 6GB)
> **Method:** Mel Spectrogram (300-3000Hz) + 4 Few-Shot + Chain-of-Thought Prompt
> **Previous best WGT AVG:** 27.0 → This test: **32.0** (New project record)

---

## 1. WHAT CHANGED?

Only one change from the previous test: a 3-step reasoning instruction added to the final classify message.

**Step 1:** "Are there VERTICAL bright lines or spikes? If yes, these are metallic impacts or mechanical transients — NOT human voice."

**Step 2:** "Are there CURVED or SLANTED horizontal bands between 500-2000Hz that look like stacked arches or stairs? These are speech formants."

**Step 3:** "ONLY if you see the formant pattern from Step 2, AND those patterns are NOT just vertical spikes from Step 1, set alarm=true."

Few-shot examples, frequency filter (300-3000Hz), 3 clean + 1 human — all unchanged.

---

## 2. TEST RESULTS

| Scene | Human | Score | FP | Confirmed | First Alarm | Detail |
|-------|-------|-------|-----|-----------|-------------|--------|
| S1 | NO | **60/100** | 0 | 0 | — | Perfect — 12 chunks zero alarm |
| S2 | YES (25s) | 0/100 | 0 | 0 | — | 2 PRELIM (chunks 6, 12) but debouncing dropped |
| S3 | NO | **60/100** | 0 | 0 | — | **S3 SOLVED!** 12 chunks zero alarm |
| S4 | YES (20s) | **100/100** | 0 | 5 | 25s [+5s] | **PROJECT RECORD — PERFECT SCORE!** |
| S5 | YES (20s) | 0/100 | 0 | 0 | — | 1 PRELIM (chunk 6) but debouncing dropped |

**Weighted Average: 32.0/100** (New project record)
**Total time: 7.1 minutes**

---

## 3. RECORD SCENES

### S4: 100/100 — First Perfect Score in Project History

Detection Accuracy: +40/40 (5 post-distress chunks correctly detected)
Time to Detection: 30/30 (first alarm 25s, distress 20s, +5s delay)
False Alarm Control: 20/20 (zero pre-distress FP — 5 chunks all clean)
Action Quality: 10/10 (INITIATE_CONFINED_SPACE_RESCUE — correct for manhole gallery)

This result clearly shows the effect of Chain-of-Thought. Previous test had 3 FPs in S4 (chunks 2-3-4). This test: all cleared — model asked "are there vertical lines?" and correctly filtered underground ambient sounds.

### S3: 60/100 — FP Completely Eliminated

Previous test had 9 confirmed FPs. This test: zero. CoT's "vertical lines = metallic impacts, do NOT alarm" rule completely filtered metallic sounds. The model no longer says "screen is full = human" — it asks "vertical or horizontal?"

---

## 4. TRADE-OFF ANALYSIS

### S2 and S5: CoT Made the Model Too Cautious

In S2, model saw formant at chunk 6 (0.75 speech_call) and chunk 12 (0.90). But gave 0.20 for the 5 chunks in between. Debouncing requires consecutive alarms — chunk 6 was isolated, made PRELIM. Chunk 12 also isolated, made PRELIM. Result: 0 confirmed, 0/100.

In S5, same situation — chunk 6 showed 0.80 alarm but single chunk, made PRELIM.

**Why?** CoT instruction set a strict rule: "ONLY alarm if you see formants." In noisy scenes (S2, S5), the model sees formants in some chunks but not others — non-determinism persists. Alarms remain isolated and debouncing filters them.

### Comparison: CoT On vs Off

| Scene | CoT Off (previous) | CoT On (this test) |
|-------|--------------------|--------------------|
| S1 | 60 | 60 (same) |
| S2 | **95** | 0 (degraded) |
| S3 | 0 | **60** (fixed!) |
| S4 | 0 | **100** (perfect!) |
| S5 | 5 | 0 (degraded) |
| WGT AVG | 27.0 | **32.0** (improved!) |

Without CoT: Model aggressive → many alarms in S2/S5 (correct + FP) → many alarms in S3/S4 (FP)
With CoT: Model cautious → zero FP in S3/S4 (correct) → few alarms in S2/S5 (missed)

WGT AVG 32.0 > 27.0 because gains in S3 and S4 (60 + 100 = 160 points) outweigh losses in S2 and S5 (95 + 5 = 100 points).

---

## 5. "THE PROBLEM IS NOT IN THE MODEL, IT'S IN THE SIGNAL"

The most important finding across this test series: regardless of method (audio, spectrogram, feature-text, chain-of-thought), the same scenes cause problems.

**Easy scenes (every method works):**
- S1 pump: Very distinct signal, every method identifies correctly
- S4 masked voice: Formant clear in quiet environment, 100/100 with CoT

**Hard scenes (no method works consistently):**
- S2 construction + shouting: Human voice buried under 95dB noise
- S5 drowning: Intermittent scream + water effects + construction noise
- S3 metallic sound: Formant-like frequency pattern (deceptive)

This distribution is method-independent — it stems from the physical nature of the signal.

---

## 6. PROJECT SCORE EVOLUTION

| Test | S1 | S2 | S3 | S4 | S5 | WGT AVG | Milestone |
|------|-----|-----|-----|-----|-----|---------|-----------|
| Audio + Aggressive | 0 | 0 | 60 | 5 | 5 | 3.0 | First test |
| Audio + Neutral | 60 | 0 | 60 | 0 | 0 | 12.0 | FP cleaned |
| Spectrogram 2-example | 60 | 0 | 0 | 0 | 5 | 8.0 | Binary trap |
| Spectrogram 4-example filtered | 60 | **95** | 0 | 0 | 5 | 27.0 | S2 record |
| **Spectrogram 4-example + CoT** | 60 | 0 | **60** | **100** | 0 | **32.0** | **S4 perfect** |

3.0 → 32.0: Over **10x improvement** from start.

---

## 7. NEXT STEPS

Ideal scenario: combine CoT's S3/S4 success with non-CoT's S2/S5 success. Options:

Option A: Lower debouncing threshold — accept PRELIM alarms, allowing single-chunk alarms in S2/S5 to pass through.

Option B: Two-pass system — first scan with CoT (clean S3/S4 FP), then re-evaluate suspicious chunks without CoT.

Option C: Scene-based calibration — different prompt settings for different microphone locations.

---

*This document records Chain-of-Thought spectrogram test results.*
*S4 achieved 100/100 project record — CoT completely eliminated S3 false positives.*
*Last updated: April 5, 2026*

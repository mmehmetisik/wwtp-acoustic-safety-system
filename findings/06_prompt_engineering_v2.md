# WWTP Acoustic Safety — Prompt Engineering Findings v2
## Neutral Prompt Results + Non-Determinism Discovery
> **Test Date:** April 3, 2026
> **Model:** Gemma 4 E4B (Ollama v0.20.0, RTX 3060 6GB)
> **Audio:** TTS-based (Google TTS + industrial noise)
> **Tests:** 3 prompt versions, neutral prompt with 2 audio weight settings

---

## 1. NEUTRAL PROMPT TEST — RESULTS

### 1.1 First Run (Audio Weight: S2=0.35, S4=0.6, S5=0.40)

| Scene | Human | Score | Signal | Detail |
|-------|-------|-------|--------|--------|
| S1 | NO | **60/100** | 0 alarm | Perfect — zero FP |
| S2 | YES | 0/100 | 1 alarm (PRELIM) | Chunk 7: shouting_help, 0.85, [+5s] — HEARD but single isolated |
| S3 | NO | **60/100** | 0 alarm | Perfect — zero FP |
| S4 | YES | 0/100 | 2 filtered | Chunk 3: 0.65, Chunk 7: 0.50 — weak signal |
| S5 | YES | 0/100 | 0 alarm | Zero signal |

### 1.2 Second Run (Audio Weight Increased: S2=0.55, S4=0.8, S5=0.60)

| Scene | Human | Score | Signal | Detail |
|-------|-------|-------|--------|--------|
| S1 | NO | **60/100** | 1 filtered (0.60) | Debouncing correctly filtered |
| S2 | YES | 0/100 | 1 alarm (PRELIM) | Chunk 11: shouting_help, 0.90, [+25s] — HEARD but single isolated |
| S3 | NO | **60/100** | 3 filtered (0.30-0.50) | Debouncing filtered all |
| S4 | YES | 0/100 | 0 alarm | No signal this time (non-determinism) |
| S5 | YES | 0/100 | 3 filtered (0.50-0.55) | Chunk 6 [+5s], Chunk 11 [+30s] — HEARS but low confidence |

### 1.3 Neutral Prompt Analysis

Neutral prompt completely eliminated hallucinations — S1 and S3 showed zero confirmed FP in both runs. Debouncing successfully filters low-confidence sporadic alarms.

The model HEARS real human voice but inconsistently and with low confidence:
- S2: Both runs detected in a single chunk at high confidence (0.85-0.90)
- S5: Low confidence signals (0.50-0.55) arriving but debouncing filters them
- S4: Sometimes hears (0.50-0.65), sometimes nothing (non-determinism)

Core issue: the model notices the sound but cannot detect it with sufficient confidence and in enough chunks. This is the model's audio understanding limit — not solvable through prompt optimization alone.

---

## 2. THREE-PROMPT COMPARISON WITH TWO AUDIO LEVELS

### Best Results Per Scene

| Scene | Best Score | Configuration | Note |
|-------|-----------|---------------|------|
| S1 | 60/100 | Neutral prompt (both audio levels) | Zero FP |
| S2 | 0/100 | All failed | Best signal: Neutral, 0.90 but single chunk |
| S3 | 60/100 | Neutral prompt / Aggressive+debouncing | Zero confirmed FP |
| S4 | 5/100 | Aggressive prompt + TTS | 0.85-0.90 correct detection but with FPs |
| S5 | 5/100 | Aggressive prompt + TTS | Chunk 6 at 0.85, [+5s] but with FPs |

### Critical Observation: Aggressive vs Neutral Trade-off

With aggressive prompt, the model HEARS (S4: 0.85-0.90, S5: 0.85) but also hallucinates (S1: 7 FP).
With neutral prompt, the model DOESN'T HEAR (most chunks) but also doesn't hallucinate.
Finding a perfect balance is extremely difficult with this model's capacity.

This is a "wall" — the limit of the model's audio understanding capability has been reached. The solution is not in prompt or audio level adjustment, but in a different technical approach (spectrogram hybrid, multi-pass, temperature tuning, etc.)

---

## 3. LLM NON-DETERMINISM FINDING

Same audio, same prompt, different run — different results:
- S1 neutral: Run 1 = 0 alarms, Run 2 = 1 alarm (0.60, filtered)
- S3 neutral: Run 1 = 0 alarms, Run 2 = 3 alarms (0.30-0.50, all filtered)
- S4 neutral: Run 1 = 2 alarms (0.50-0.65), Run 2 = 0 alarms
- S2 neutral: Run 1 = detection at chunk 7, Run 2 = detection at chunk 11

This is stochastic inference — the LLM's internal sampling mechanism produces small variations between runs. The debouncing layer is critical for managing this uncertainty. Safety-critical systems with LLMs require a separate engineering layer to handle non-determinism.

---

## 4. THE WALL — AUDIO APPROACH LIMITS

Through three prompt versions and two audio weight settings, the maximum achievable performance via raw audio has been reached. To progress further, different technical approaches need to be explored:

- **Spectrogram hybrid approach** (audio → image → model's vision capability)
- **Multi-pass analysis** (send same chunk multiple times, majority vote)
- **Ollama temperature setting** (more deterministic output)
- **Audio pre-processing** (amplify human voice frequencies)

The key insight: the model's audio understanding hits a wall at ~95dB noise. But its vision capability is much stronger. Converting the problem from audio to visual (spectrograms) may unlock a path forward.

---

## 5. KEY FINDINGS SUMMARY

### Finding 1: The Prompt Engineering Spectrum
Aggressive → hallucinations but real detection. Passive → no hallucinations but no detection. Neutral → clean but insufficient detection. The sweet spot for raw audio does not exist with this model — a different modality is needed.

### Finding 2: Non-Determinism is a System-Level Risk
Same input, different output across runs. Debouncing catches most variance but cannot guarantee consistency. Temperature control may help.

### Finding 3: Model Hears Voice But Cannot Confirm It
S5 shows 0.50-0.55 signals — the model notices something but lacks confidence. This suggests the information exists in the audio but the model's audio encoder cannot extract it reliably at high noise levels.

### Finding 4: Vision May Be the Answer
The model's vision capability (image understanding) is significantly stronger than its audio capability. Converting audio to spectrograms and using few-shot visual classification is the next logical step.

---

*This document contains neutral prompt test results and the discovery of the audio approach wall.*
*The next step: spectrogram-based approach (findings/07).*
*Last updated: April 3, 2026*

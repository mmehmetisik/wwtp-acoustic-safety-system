# WWTP Acoustic Safety — Spectrogram Full Scene Test Findings
## 12-Chunk Few-Shot Spectrogram Results
> **Test Date:** April 4, 2026
> **Model:** Gemma 4 E4B (Ollama v0.20.0, RTX 3060 6GB)
> **Method:** Mel Spectrogram + Few-Shot Vision (2 examples: S1 clean, S4 human voice)

---

## 1. TEST RESULTS

| Scene | Human | Alarm | Confirmed | FP | Score | Time |
|-------|-------|-------|-----------|-----|-------|------|
| S1 — Pump | NO | 0/12 | 0 | 0 | **60/100** | 2.1 min |
| S2 — Construction | YES (25s) | 12/12 | 12 | 5 | 0/100 | 1.3 min |
| S3 — Pool | NO | 12/12 | 12 | 12 | 0/100 | 1.3 min |
| S4 — Manhole | YES (20s) | 12/12 | 12 | 4 | 0/100 | 1.3 min |
| S5 — Critical | YES (20s) | 12/12 | 12 | 4 | 5/100 | 1.4 min |

**Total time: 7.5 minutes (audio-based was 28 minutes)**
**Overall score: 2.7/100**

---

## 2. WHAT HAPPENED?

The model alarmed at 0.90 confidence on every chunk in every scene except S1 (pump). S1's spectrogram looks very different from the others — only steady low-frequency bands, upper section completely empty. The model correctly identified this.

But S2, S3, S4, S5 spectrograms look similar to each other — all have broadband energy distribution, vertical and horizontal patterns. The model is performing binary classification: "looks like S1 = clean, doesn't look like S1 = human voice." This is too coarse a distinction and doesn't work.

With only two few-shot examples, one very clean (S1 pump — low-frequency steady bands) and one very clearly human (S4 masked voice — obvious formant structures), the model learned these two extremes but cannot distinguish the nuances between them. It interprets the broadband spectrogram of construction noise as "formants."

---

## 3. POC TEST vs FULL TEST DIFFERENCE

In the proof-of-concept test (single chunk), 6 out of 7 were correct (85.7%). In the full 12-chunk test, everything except S1 was wrong. Why?

In the POC test, a single carefully selected chunk was tested per scene — the time segment showing the most distinctive difference. In the full test, 12 consecutive chunks include ambiguous ones (pre-distress construction noise). The model says "I'm not sure but it doesn't look like S1, so alarm."

Also, in the POC test, different time segments were selected for S2, S3, S4 (30-35s, 25-30s, 35-40s). In the full test, each scene's 0-5s chunk is included — these chunks have no human voice yet but have construction noise, and the model still alarms.

---

## 4. THE FUNDAMENTAL PROBLEM

With the few-shot approach, the model behaves like a binary classifier: "Does it look like S1?" If not, it automatically says "human voice present." This approach is insufficient because industrial environments have many different noise types, all looking different from S1 but none containing human voice.

The solution may be to add more few-shot examples (construction noise clean, metallic sound clean, etc.) but this requires a new example for each new noise type — not scalable.

---

## 5. SPEED IMPROVEMENT (The One Positive Result)

The spectrogram approach is 4-6x faster than audio-based:

| Method | Chunk time | 5 scenes total |
|--------|-----------|----------------|
| Audio + Aggressive prompt | ~37 seconds | 37.1 minutes |
| Audio + Neutral prompt | ~25 seconds | 25-28 minutes |
| Spectrogram few-shot | ~6 seconds | 7.5 minutes |

---

## 6. BEST RESULTS ACROSS ALL TESTS

Best per-scene results achieved across all tests:

| Scene | Best Score | Configuration | Note |
|-------|-----------|---------------|------|
| S1 | 60/100 | Neutral prompt + TTS or Spectrogram | Zero FP |
| S2 | 0/100 | No configuration succeeded | Best signal: Neutral prompt, single chunk 0.90 |
| S3 | 60/100 | Neutral prompt + TTS or Passive + TTS | Zero FP |
| S4 | 5/100 | Aggressive prompt + TTS | 0.85-0.90 correct detection but with FPs |
| S5 | 5-15/100 | Aggressive prompt + TTS | Chunk 6 at 0.85 but FPs lowered score |

Best overall: Neutral prompt + TTS = 12.0 WGT AVG (S1:60, S2:0, S3:60, S4:0, S5:0)
Aggressive prompt + TTS = 3.0 WGT AVG (S1:0, S2:0, S3:60, S4:5, S5:5) — but has real detections

No configuration achieved a satisfactory overall score.

---

## 7. HONEST ASSESSMENT

### What Worked
- TTS audio generation (model recognizes real speech better than formant)
- Debouncing layer (filters sporadic FPs)
- Distress timing calculation (works correctly)
- Engine infrastructure (reliable, no errors)
- Spectrogram speed improvement (6x faster)
- Prompt engineering findings (aggressive vs passive vs neutral)

### What Didn't Work
- Reliable detection via audio approach (model can't hear most chunks)
- Correct classification via spectrogram few-shot (model acts as binary classifier)
- Finding balance between hallucination and detection (fixing one breaks the other)
- Overall score (best case 12/100)

### Core Limitation
Gemma 4 E4B is a small edge model (4B parameters). Human voice detection under industrial noise may be beyond this model's capacity with only 2 examples. The model can sometimes notice the sound but cannot reliably and consistently distinguish it. This is not the model's fault — the task is outside the model's training scope with insufficient calibration.

---

*This document honestly records the spectrogram full scene test results and overall project status.*
*Next step: add more few-shot examples and frequency filtering (findings/09).*
*Last updated: April 4, 2026*

# WWTP Acoustic Safety — Feature-Text Approach Findings
## Audio Features → Text → LLM Reasoning Test
> **Test Date:** April 4, 2026
> **Model:** Gemma 4 E4B (Ollama v0.20.0, RTX 3060 6GB)
> **Method:** librosa feature extraction → text to model (no audio/image)

---

## 1. APPROACH

Instead of sending audio or images to the model, numerical features were extracted from each 5-second chunk using librosa and sent as text. The model read the numbers and reasoned to make decisions.

Extracted features: RMS energy (loudness), zero-crossing rate (noise vs tonal), spectral centroid (frequency center of mass), spectral bandwidth and rolloff, MFCC total variance (speech fingerprint), voice band energy ratio (300-3000Hz), low band energy ratio (<300Hz), F1 band ratio (400-600Hz), F2 band ratio (1200-1800Hz), formant presence (YES if both F1 and F2 present), dominant frequency peaks.

---

## 2. TEST RESULTS

| Chunk | Human | Formant | Model Decision | Correct? | Conf | Time |
|-------|-------|---------|---------------|----------|------|------|
| S1 (15-20s) | NO | NO | NO HUMAN | CORRECT | 0.95 | 23.1s |
| S2_pre (10-15s) | NO | NO | NO HUMAN | CORRECT | 0.60 | 9.4s |
| S2_post (30-35s) | YES | NO | NO HUMAN | WRONG | 0.60 | 9.9s |
| S3 (25-30s) | NO | YES | HUMAN | WRONG | 0.95 | 9.0s |
| S4_pre (10-15s) | NO | NO | NO HUMAN | CORRECT | 0.95 | 8.9s |
| S4_post (25-30s) | YES | YES | HUMAN | CORRECT | 0.95 | 8.3s |
| S5_pre (10-15s) | NO | NO | NO HUMAN | CORRECT | 0.60 | 8.9s |
| S5_post (30-35s) | YES | NO | NO HUMAN | WRONG | 0.60 | 9.7s |

**Accuracy: 5/8 (62.5%)**
**Average time: 10.9 seconds/chunk**

---

## 3. ANALYSIS

### The Model Reasoned Perfectly

The model's logic chain was consistent and correct in every case:

S1: "Formant NO, F1 0.012, F2 0.003, low band 0.89 → definitely machine" → CORRECT
S4_post: "Formant YES, MFCC variance 959.65, very high → human voice" → CORRECT
S2_pre: "Formant NO, ZCR 0.33 high → construction noise" → CORRECT
S3: "Formant YES, MFCC variance 1420, ZCR 0.11 → human voice" → CORRECT GIVEN THE NUMBERS (but wrong in reality)

The model made zero logical errors — every decision was logically correct based on the given numbers. The problem is not in the model.

### The Problem is in Feature Extraction

All three wrong results share the same root cause: feature extraction does not reflect reality.

**S2_post (human YES but formant NO):** Human voice (TTS "Help!") is buried under construction noise. F1 ratio 0.0262 — below threshold (0.05). librosa computes simple energy ratios, cannot find weak formants under noise. The human voice is physically lost in the signal.

**S5_post (human YES but formant NO):** Same issue — drowning scream (intermittent, with water effects) under construction noise. F1 0.0262, formant NO. Drowning effects (random interruption, water sounds) further distort formant structure.

**S3 (human NO but formant YES):** Metal scraping in 300-3000Hz range with irregular rhythm — intentionally designed to resemble human voice. F1 0.0605 and F2 0.1834 — above thresholds. MFCC variance 1420 — very high (from metallic impact irregularity). Numerically indistinguishable from human voice.

### Core Finding: The Problem is in the Signal, Not the Method

Four different approaches were tried and all had the same problematic scenes:

| Scene | Audio-Based | Spectrogram | Feature-Text | Common Issue |
|-------|-------------|-------------|--------------|-------------|
| S2 post | Failed (most) | Detected (filtered!) | Failed | Voice buried in noise |
| S3 | Mixed | Failed | Failed | Metallic sound resembles voice |
| S5 post | Failed (most) | Detected (filtered!) | Failed | Drowning voice buried in noise |

Notable: Spectrogram approach correctly detected S2_post and S5 while feature-text could not. This means visual pattern recognition (spectrogram) carries more information than individual numbers. The human eye (and vision model) can see curved formant lines in an image, but these lines disappear when reduced to simple energy ratios.

---

## 4. METHOD COMPARISON

| Metric | Audio-Based | Spectrogram (filtered) | Feature-Text |
|--------|-------------|------------------------|--------------|
| S2 best score | 0/100 | **95/100** | Missed |
| S5 detection | Sometimes 0.85 | Detection (with FP) | Missed |
| S1 FP | Prompt-dependent | 0 | 0 |
| S3 FP | Prompt-dependent | Present | Present |
| S4 detection | Sometimes 0.85 | Detection (with FP) | 0.95 correct |
| Speed (chunk) | 25-37s | 6-7s | 9-10s |
| Determinism | Low | Medium | High |
| Hallucination | High (aggressive) | Medium | Low |

**Best overall: Frequency-filtered spectrogram (S2: 95/100)**
**Most reliable "no human" detection: Feature-text (formant NO → definitive)**
**Fastest: Spectrogram (6-7s/chunk)**

---

## 5. KEY INSIGHTS

### Insight 1: Each Method Excels at Different Things
Audio-based: Sometimes hears real speech but inconsistent.
Spectrogram: Good at visual pattern recognition but prone to FP.
Feature-text: Perfectly follows numerical rules but misses subtle signal details.

None is sufficient alone. But each has a different strength.

### Insight 2: Human Voice Detection in Noise is an Inherently Hard Problem
This is not a Gemma 4 limitation — it's the nature of the problem. Human voice at 95dB construction noise is physically masked. Simple feature extraction (librosa energy ratios) cannot overcome this masking. Spectrogram visual approach partially overcomes it because formant lines can be visually selected even within noise.

### Insight 3: The Model Reasons Correctly on Given Data
In 8 tests, the model made zero logical errors. In S3, saying "formant YES + high MFCC → human" was correct given the numbers — the problem was that the numbers didn't reflect reality. This supports the finding: "LLM reasoning works but input quality is critical."

---

*This document records the feature-text approach POC results.*
*Core finding: The problem is not in the model — it is in the signal.*
*Last updated: April 4, 2026*

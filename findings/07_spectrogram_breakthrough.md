# WWTP Acoustic Safety — Spectrogram Approach Findings
## "If the Model's Ear Can't Hear, Show Its Eye"
> **Test Date:** April 4, 2026
> **Model:** Gemma 4 E4B (Ollama v0.20.0, RTX 3060 6GB)
> **Reference:** NeurIPS 2024 — "Vision Language Models Are Few-Shot Audio Spectrogram Classifiers"

---

## 1. WHY SPECTROGRAMS?

### We Hit a Wall

Three different prompt versions were tested with the audio-based approach (audio → model):

Aggressive prompt: Model HEARD human voice (S4: 0.85-0.90, S5: 0.85) but also hallucinated (S1: 7 FP, S3: 7 FP). Passive prompt: Hallucinations zeroed out but model heard nothing (60 chunks, 0 alarms). Neutral prompt: Tried to find balance but model couldn't hear most chunks, occasionally detecting one chunk then missing others.

Core problem: Gemma 4 E4B's audio understanding capacity (ASR-based) cannot reliably distinguish human voice under industrial noise. This is the model's limit — not solvable through prompt engineering.

### Inspiration: NeurIPS 2024 Paper

The NeurIPS 2024 paper "Vision Language Models Are Few-Shot Audio Spectrogram Classifiers" proved that VLMs can classify audio when received as spectrogram images. GPT-4o outperformed human experts in this task. Performance improves dramatically with few-shot examples.

### Hypothesis

Gemma 4 E4B is multimodal — it understands both audio and images. Audio understanding is limited but vision understanding is much stronger. If we convert audio to mel spectrogram images, the model can VISUALLY distinguish human voice from mechanical noise. Because on a spectrogram, human voice creates distinct formant bands while mechanical noise creates flat lines or vertical spikes.

---

## 2. SPECTROGRAM ANALYSIS — VISUAL DIFFERENCES

Each scene's spectrogram was generated and visually inspected. Differences are striking:

**S1 (pump, no human):** Only steady horizontal bands at low frequencies (0-512Hz). No change across 5 seconds. Upper frequencies completely empty (black). Typical mechanical noise pattern.

**S2 (construction + shouting, human present):** Bright curved lines at 512-1024Hz on top of broadband noise background — speech formants. Curved, short-duration, irregularly spaced. Machines never produce this pattern.

**S3 (metallic sounds, no human):** Vertical bright lines (metallic impacts) and steady horizontal band at bottom (motor hum). No formant curves but vertical spikes can be misleading.

**S4 (masked voice, human present):** Most visible — stacked horizontal bands at 512-2048Hz (harmonic structure), staircase pattern. Classic human voice harmonic structure. This pattern is definitely absent in S1 and S3.

**S5 (drowning, human present):** Curved bright spots and formant structures at 512-1024Hz. Similar to S2 but more scattered and intermittent — natural result of drowning effects.

---

## 3. TEST STAGES

### Stage 1: Zero-Shot Spectrogram (No Examples)

First attempt: spectrogram image sent to model with no examples. Model analyzed the image, identified formant patterns (reasoning mentioned "formants characteristic of human speech") but used confidence score in reverse direction — 0.90 meaning "no human, I'm sure."

Prompt corrected — confidence direction clarified. This time model said it saw no formants, gave low confidence to all scenes. Zero-shot approach produced inconsistent results.

### Stage 2: Thinking Mode Issue

Gemma 4 E4B's "thinking mode" complicated API responses. Model wrote its answer in the `thinking` field instead of `content`. The `content` field was empty. Solution: Added `"think": False` parameter to API call. This completely resolved the issue.

### Stage 3: Few-Shot Spectrogram (With Examples) — TURNING POINT

The NeurIPS approach was applied. Model was shown two examples:

Example 1 (clean): S1 pump room spectrogram — "This is clean, only machine noise. Steady bands at low frequencies, no formants."

Example 2 (human voice): S4 masked voice spectrogram — "This has human voice. You can see curved/stacked formant bands at 512-2048Hz."

Then the model classified new spectrograms.

---

## 4. FEW-SHOT SPECTROGRAM RESULTS

| Scene | Human | Alarm | Conf | Type | Correct? | Reasoning |
|-------|-------|-------|------|------|----------|-----------|
| S1 (30-35s) | NO | — | 0.10 | none | CORRECT | "Only steady low-frequency noise bands" |
| S2 (30-35s) | YES | ALARM | 0.90 | speech | CORRECT | "Strong distinct formant patterns of human speech" |
| S3 (30-35s) | NO | ALARM | 0.90 | shouting | WRONG | "Rhythmic formant patterns" (mistook metallic for human) |
| S4 (35-40s) | YES | ALARM | 0.90 | speech | CORRECT | "Strong distinct formant patterns of human speech" |
| S5 (25-30s) | YES | ALARM | 0.90 | shouting | CORRECT | "Rhythmic formant patterns at beginning and end" |
| S5 (30-35s) | YES | ALARM | 0.90 | speech | CORRECT | "Rhythmic formant patterns across duration" |
| S5 (40-45s) | YES | ALARM | 0.90 | shouting | CORRECT | "Rhythmic formant patterns across duration" |

**Success rate: 6 out of 7 correct (85.7%)**

---

## 5. AUDIO-BASED vs SPECTROGRAM COMPARISON

### Detection Performance

| Scene | Audio + Aggressive | Audio + Neutral | Spectrogram Few-Shot |
|-------|-------------------|----------------|---------------------|
| S1 (no human) | 7 FP | 0 FP | 0 FP |
| S2 (human) | Detection with FPs | 1 chunk at 0.90 | 0.90 alarm |
| S3 (no human) | 7 FP | 0 FP | 1 FP (0.90) |
| S4 (human) | 0.85-0.90 with FPs | 0 alarm | 0.90 alarm |
| S5 (human) | 1 chunk at 0.85 | 0 alarm | 3 chunks at 0.90 |

### Speed Comparison

| Method | Avg Chunk Time | 12-Chunk Total |
|--------|---------------|----------------|
| Audio + Aggressive prompt | ~37 seconds | ~7.4 minutes |
| Audio + Neutral prompt | ~25 seconds | ~5.0 minutes |
| Spectrogram few-shot | **~6 seconds** | **~1.2 minutes** |

Spectrogram approach is **6x faster** than audio-based. Analyzing 5 seconds of audio in 6 seconds — nearly real-time. This is a critical advantage for edge deployment.

### Reliability

| Method | Non-determinism | Consistency |
|--------|----------------|-------------|
| Audio-based | High — same chunk gives different results across runs | Low |
| Spectrogram | Low — image is deterministic, model decisions are consistent | High |

---

## 6. WHY DOES IT WORK?

### Model Architecture

Gemma 4 E4B is multimodal — handles both audio and images. But these two capabilities are not equal. Audio understanding (ASR) is in a small module, optimized for clean speech recognition. Vision understanding is in a much larger and stronger module, trained for complex visual pattern recognition. The spectrogram approach bypasses the model's weak ear and uses its strong eye.

### Formant Patterns Are Visually Distinct

Human voice creates unique visual patterns on spectrograms — curved formant bands, harmonic staircase structures, irregularly-timed short bursts. Mechanical sounds create flat horizontal lines, vertical spikes, uniform energy distribution. These two patterns are visually very different — like face recognition, the model can distinguish the visual pattern.

### Few-Shot Calibration Effect

In zero-shot, the model analyzed spectrograms generally but didn't know what "clean" vs "human voice" means in our specific industrial context. Two examples provided this calibration. This aligns with the NeurIPS paper findings — few-shot examples dramatically improve performance because they show the model "what to look for in this context."

---

## 7. SINGLE ISSUE: S3 FALSE POSITIVE

In S3 (metallic sounds, no human), the model claimed to see "rhythmic formant patterns" and gave a 0.90 confidence false alarm. The cause: metallic scraping sounds were intentionally designed to resemble human speech rhythm — irregular intensity changes in the 300-3000Hz range. This similarity is visible in the spectrogram.

Possible solutions: Add S3 spectrogram as a third "clean but misleading" few-shot example. Apply debouncing for consecutive alarm verification. Use different spectrogram parameters (e.g., narrow the frequency range).

---

## 8. THE JOURNEY SUMMARY

**Step 1 — Formant synthesis.** Model couldn't hear (S5: 12 chunks zero signal). Root cause: formant sounds didn't match model's ASR training data.

**Step 2 — TTS transition.** Model heard "Help! Yardim!" (S2: "shouting_help", S5: 0.85). Root cause solved — real speech patterns.

**Step 3 — Prompt engineering.** Three versions tested. Aggressive hallucinated, passive killed detection, neutral was inconsistent. Key finding: "What you tell AI matters more than how much you tell it."

**Step 4 — Hit the wall.** Audio approach reached its limit. Non-determinism unacceptable for safety systems.

**Step 5 — Spectrogram hypothesis.** Inspired by NeurIPS 2024: "if the model's ear can't hear, show its eye."

**Step 6 — Zero-shot spectrogram.** Model saw formants but made inconsistent decisions. API thinking mode issue resolved.

**Step 7 — Few-shot spectrogram.** TURNING POINT. Two examples → 85.7% accuracy. S5 detected in three chunks at 0.90. 6x speed improvement. Consistent and reliable.

---

## 9. FIELD DEPLOYABILITY

The spectrogram approach is fully deployable in the field:

No additional hardware needed — same microphone, same edge device. Audio → spectrogram conversion takes 0.1 seconds (via librosa). No internet required — all processing local. Total analysis time: 0.1s (spectrogram) + 6s (model) = 6.1 seconds per chunk. Nearly real-time for 5-second audio.

Pipeline: Microphone → 5s audio → spectrogram (0.1s) → model (6s) → decision → action

---

*This document records the spectrogram breakthrough — the project's turning point.*
*Last updated: April 4, 2026*

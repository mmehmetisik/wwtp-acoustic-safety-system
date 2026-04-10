# WWTP Acoustic Safety — Engine Test Findings
## 12-Chunk Full Scene Evaluation Results
> **Test Date:** April 3, 2026
> **Model:** Gemma 4 E4B (Ollama v0.20.0, RTX 3060 6GB)

---

## 1. TEST HISTORY

### Test 1: Single-Chunk Tests (BARE/CONTEXT/PROTOCOL)
One critical chunk (5 seconds) sent per scene.

| Scene | BARE | CONTEXT | PROTOCOL |
|-------|------|---------|----------|
| S1 | Correct | Correct | Correct |
| S2 | Missed | Detected | Detected |
| S3 | Correct | Correct | False Alarm |
| S4 | Missed | Missed | Detected (0.98) |
| S5 | Missed | Missed* | Detected (0.98) |

*S5 CONTEXT: Model did not hear the voice but triggered alarm from context text (not deployable behavior).

**Result:** Single-chunk PROTOCOL mode achieved 4/5. The model can understand audio.

---

### Test 2: First 12-Chunk Full Run (PROTOCOL)
Original engine, no debouncing, distress timing bug present.

| Scene | Score | First Alarm | Issue |
|-------|-------|-------------|-------|
| S1 | 0/100 | 5s (chunk 2) — FP | 5 false alarms, distress onset "Nones" |
| S2 | 70/100 | 40s (chunk 9) | Late detection but correct |
| S3 | 0/100 | 15s (chunk 4) — FP | 4 false alarms |
| S4 | 70/100 | 25s (chunk 6) | Correct detection |
| S5 | 65/100 | 10s (chunk 3) — FP | Alarm BEFORE fall (false positive) |

**Bugs found:**
- Distress onset timing unreadable ("Nones") — engine looking at wrong source
- Too many false positives — PROTOCOL prompt too sensitive
- S5 alarm at 10s = before fall (20s) = actually a false positive

---

### Test 3: Fix v1 — Distress Timing Fix + Prompt Balancing
Distress timing corrected. Mechanical vs human sound distinction added to prompt.

| Scene | Score | First Alarm | Change |
|-------|-------|-------------|--------|
| S1 | 0/100 | 15s (chunk 4) — FP | Slightly improved (5→3 FP) |
| S2 | 5/100 | 5s (chunk 2) — FP | Worsened (alarm before distress) |
| S3 | 0/100 | 15s (chunk 4) — FP | Same |
| S4 | 5/100 | 10s (chunk 3) — FP | FP increased |
| S5 | 15/100 | 5s (chunk 2) — FP | FP present but also alarm at 25s |

**Finding:** Distress timing now works correctly but FP problem persists.

---

### Test 4: Fix v2 — Audio Generator Improvement + Alarm Debouncing
Motor drone frequency range 100-500Hz → 50-250Hz. Alarm confirmation layer added.

| Scene | Score | Confirmed | Filtered | Result |
|-------|-------|-----------|----------|--------|
| S1 | 0/100 | 5 confirmed | 0 filtered, 1 prelim | Debouncing insufficient — consecutive FPs |
| S2 | 5/100 | 4 confirmed (1 FP) | 1 filtered | FP still present (chunk 4, before distress) |
| S3 | **60/100** | **0 confirmed** | 1 filtered, 3 prelim | **MAJOR IMPROVEMENT!** All FPs filtered |
| S4 | 5/100 | 4 confirmed (2 FP) | 1 filtered | Correct detection exists but FPs lower score |
| S5 | **0/100** | **0 confirmed** | 2 filtered | **CRITICAL ISSUE** — model barely heard the scream |

**Critical Findings:**
1. Debouncing worked perfectly on S3 (0 → 60 points!)
2. In S5, model could not hear the scream across 12 chunks (only very weak alarm at 50-60s)
3. In S1, model still hallucinating "muffled_call" on pump noise

---

## 2. ROOT CAUSE ANALYSIS

### Why does single-chunk work but 12-chunk fail?

**Difference 1 — Prompt Length:**
In single-chunk test, prompt was short and focused. In 12-chunk mode, the PROTOCOL prompt is very long — the model struggles to focus on audio while processing extensive text. This is a known LLM issue: attention degrades in long contexts.

**Difference 2 — Synthetic Audio Quality:**
Formant synthesis produces mathematically plausible human-like tones but NOT real human speech patterns. The model was trained on real human speech via ASR — "HELP!", "YARDIM!", crying, screaming. Synthetic formant sounds do not match these patterns.

This is why the model:
- Hallucinates "muffled_call" on pump noise (harmonics are similar)
- Cannot recognize synthetic screams (no natural speech patterns)

### Is this our fault or the model's?

Both, in different proportions:
- **Our fault (fixable):** Audio generator uses formant synthesis, not real human speech patterns. Does not match the model's training data.
- **Model limitation (can be worked around):** E4B is a small edge model optimized for ASR but not industrial acoustic analysis. Attention loss in long contexts.

---

## 3. SOLUTION PATH

### Priority 1: Switch Audio Generator to TTS
Replace formant synthesis with real TTS (Text-to-Speech) engine to generate "HELP!", "YARDIM!" voices. Then add industrial degradation (noise, distance, reverb, mask). The model should recognize real speech patterns.

### Priority 2: Shorten and Simplify Prompt
Adapt the successful short prompt structure from single-chunk tests to the 12-chunk flow. Shorten PROTOCOL information, help the model focus on audio.

### Priority 3 (if needed): Spectrogram Hybrid Approach
Convert audio chunks to spectrogram images, send both audio and image to model. Gemma 4 is much stronger in visual understanding.

---

## 4. PROJECT STATUS

- Engine runs without errors ✅
- Alarm debouncing layer works ✅ (proven on S3)
- Distress timing calculated correctly ✅
- JSON parsing reliable (57/60+ success) ✅
- Audio generator needs improvement ⚠️ (TTS-based)
- Prompt optimization needed ⚠️
- S5 survival verdict not yet achieved ❌

**Project NOT cancelled.** Core infrastructure is solid. When audio quality improves, results will change dramatically — single-chunk tests prove this.

---

*This document contains all engine test findings in chronological order.*
*Last updated: April 3, 2026*

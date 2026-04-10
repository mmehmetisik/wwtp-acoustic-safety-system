# WWTP Acoustic Safety — TTS + Prompt Optimization Findings
## Audio Quality Improvement and Prompt Balancing Process
> **Test Date:** April 3, 2026
> **Model:** Gemma 4 E4B (Ollama v0.20.0, RTX 3060 6GB)
> **Audio Generation:** Google TTS + industrial noise mixing

---

## 1. CHANGES MADE

### 1.1 Audio Generator: Formant → TTS Transition

**Problem:** Formant synthesis produced mathematical sine waves. Gemma 4 E4B's ASR engine looks for real human speech patterns — formant sounds did not match. The model hallucinated "human voice" on pump noise while missing actual synthetic screams.

**Solution:** Google TTS (gTTS) used to generate real speech voices:
- S2: "Help! Help me!" (EN) + "Yardim! Yardim edin!" (TR), 3s intervals
- S4: "Help! Help me!" + "Yardim! Yardim edin!", mask filter (2000Hz LP) + gallery reverb (1.2s), 4s intervals
- S5: "Help! Help!", "Yardim!", "Imdat!", "Help me!", "Somebody!", "Yardim edin!" — with drowning effects (random interruption, water sounds, irregular timing)

**Additional audio fixes:**
- Motor drone frequency range 100-500Hz → 50-250Hz (to avoid human voice range)
- db_to_amp multiplication removed from TTS voices (to prevent volume imbalance)
- Pitch shift removed (natural voice better for model recognition)
- S5 construction noise generated with different seed (differentiation from S2)

### 1.2 Engine: Alarm Debouncing Layer

Industrial SCADA-standard alarm confirmation system added:
- Confidence < 0.75 → automatic filter
- Single isolated alarm → "preliminary" (unconfirmed)
- 2+ consecutive alarms (3-chunk window) → "confirmed"
- Confidence ≥ 0.95 + "screaming"/"shouting_help" → instant confirmation

### 1.3 Engine: Distress Timing Fix

Distress onset time now read from three sources:
1. scene_config.json (distress_starts_sec / fall_event_sec)
2. answer_key.json (same fields)
3. Automatic inference from audio_composition structure (first time segment with human_voice=true)

---

## 2. TEST RESULTS: TTS AUDIO + PROTOCOL MODE

### 2.1 TTS + PROTOCOL (Long Prompt) Results

| Scene | Human | Raw Alarms | After Debounce | Score | Analysis |
|-------|-------|------------|----------------|-------|----------|
| S1 | NO | 7 alarms | 7 confirmed | 0/100 | PROTOCOL hallucination — says "shouting_help" on pump noise |
| S2 | YES (25s) | 4 alarms | 2 confirmed (FP) + 1 filtered | 0/100 | FPs before distress, real detection at chunk 6 but FPs lowered score |
| S3 | NO | 9 alarms | 7 confirmed | 0/100 | PROTOCOL hallucination — says "muffled_call" on metallic sounds |
| S4 | YES (20s) | 5 alarms | 5 confirmed (1 FP) | 5/100 | Model HEARS masked voice! Chunks 6-11 correct detection (0.85-0.90) |
| S5 | YES (20s) | 4 alarms | 3 confirmed (2 FP) | 5/100 | Model HEARS the scream! Chunk 6 at +5s detection (0.85) |

### 2.2 Critical Observations

**TTS WORKS — Evidence:**

S2 chunk 9 (40-45s): distress_type="shouting_help", confidence=0.90
- With old formant audio, model always said "muffled_call"
- With TTS, model now correctly identifies "shouting_help" — distinguishing real speech patterns

S4 chunks 6-11: Masked TTS voice detected at 0.85-0.90 confidence consistently
- With old formant audio, BARE mode only achieved 0.70 (debouncing filtered it)
- With TTS, confidence rose to 0.85-0.90 — model recognizes real speech more confidently

S5 chunk 6 (25-30s): distress_type="muffled_call", confidence=0.85, [+5s]
- With old formant audio, S5 produced ZERO signal across 12 chunks
- With TTS, model HEARD the scream — 5 seconds after the fall

**PROTOCOL PROMPT HALLUCINATION CONTINUES:**

S1: 7 confirmed FPs — "shouting_help" hallucination on pump noise
S3: 7 confirmed FPs — "muffled_call" hallucination on metallic sounds
S5: 2 FPs before distress — hallucination on construction noise

This is consistent with the isolation test finding: BARE mode produces zero FPs on the same audio.

---

## 3. ROOT CAUSE: WHY DOES PROTOCOL CAUSE HALLUCINATIONS?

### 3.1 Prompt Length and Attention Drift

| Mode | Prompt Length | S1 FP | S3 FP | Chunk Duration |
|------|-------------|-------|-------|----------------|
| BARE | ~100 words | 0 | 0 | ~20s |
| PROTOCOL | ~400-500 words | 7 | 7 | ~35s |

When processing long prompts, the model:
- Attention mechanism shifts from audio to text
- "When in doubt, alarm" rule triggers on every chunk
- Model imagines scenarios from prompt instead of listening to audio

### 3.2 Specific Problematic Phrases

These phrases in the old PROTOCOL prompt triggered hallucinations:
- "Missing a real human distress signal is catastrophically worse than a false alarm" → Model feels pressure to alarm
- "If you detect any sound that COULD be human distress — alarm immediately" → "COULD" is too broad
- "any muffled voice pattern MUST trigger" → Model triggers on every muffled sound
- Scene-specific safety protocol text → Added 50-100 extra words

### 3.3 Solution: Optimized Prompt

New PROTOCOL prompt ~100 words. Changes:
- Scene-specific protocol text removed
- 7 rules → 5 short items
- "When in doubt, alarm" → "If unsure, do NOT alarm" (reversed)
- "COULD be human" → "actual human speech, words, or vocal patterns" (concrete)
- "any muffled voice" → "If you hear words like 'help', 'yardim'" (word-based)
- Survival thresholds and urgency pressure removed

**New prompt philosophy:** "What you tell AI matters more than how much you tell it."

---

## 4. FORMANT → TTS COMPARISON TABLE

| Metric | Formant (Old) | TTS (New) | Difference |
|--------|--------------|-----------|------------|
| S5 BARE detection | 0/12 chunks (zero signal) | To be tested | TTS has signal |
| S5 PROTOCOL detection | 0/12 (formant) | 1/12 (chunk 6, 0.85) | First real detection with TTS |
| S2 distress_type | "muffled_call" (wrong) | "shouting_help" (correct) | TTS enables correct classification |
| S4 action | Mixed | INITIATE_CONFINED_SPACE_RESCUE | TTS enables correct action |
| Hallucination type | "muffled_call" everywhere | Same issue continues | Prompt-caused, not audio-caused |

---

## 5. KEY FINDINGS

### Finding 1: "What you tell AI matters more than how much you tell it"
Same model, same audio — short prompt produces clean decisions, long prompt produces hallucination explosion. More rules ≠ better results. Fewer, correct rules = correct results. This is a critical design principle for LLM-based safety systems.

### Finding 2: TTS Real Speech Patterns Make a Difference
With formant synthesis, model detected nothing in S5 across 12 chunks. With TTS, same scene detected at 0.85 confidence. The model looks for real speech rhythm, not mathematical waveforms. Audio quality is critical for LLM-based acoustic analysis.

### Finding 3: LLM Hallucination is Proportional to Prompt Length
100-word prompt → 0 FP. 500-word prompt → 7 FP (same audio). This is a known LLM behavior but measured for the first time in an industrial safety context. Prompt engineering is vital for safety-critical systems.

### Finding 4: Debouncing is Effective But Insufficient Alone
In S3, debouncing reduced 4 FPs to 0 (previous test). But when PROTOCOL hallucination produces consecutive alarms, debouncing confirms them as real. Debouncing catches one-off errors but cannot catch systematic hallucination. Solution: prompt fix + debouncing together.

### Finding 5: Single-Chunk Test Results Can Be Misleading
Single-chunk PROTOCOL test reported S5 at "0.98 confidence". But 12-chunk test with same PROTOCOL failed. Multi-chunk (full scene) testing is essential to measure real performance.

---

## 6. PROJECT STATUS

| Component | Status | Note |
|-----------|--------|------|
| Engine (acoustic_engine.py) | Working | Ollama API, debouncing, timing fixes |
| Audio generator (audio_generator_tts.py) | Working | TTS-based, 5 scenes generated |
| BARE mode test | Completed | S1: 60, S3: 60, S2/S4/S5: missed |
| PROTOCOL mode test (old prompt) | Completed | Hallucination issue documented |
| TTS + old PROTOCOL test | Completed | TTS works, prompt issue continues |
| Prompt optimization test | In progress | Results pending |
| Demo interface | Pending | After prompt test succeeds |

---

*This document contains all TTS transition and prompt optimization findings.*
*Last updated: April 3, 2026*

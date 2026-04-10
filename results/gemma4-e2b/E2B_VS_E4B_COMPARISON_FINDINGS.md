# WWTP Acoustic Safety — Gemma 4 E2B vs E4B Model Comparison
## 2 Billion vs 4 Billion? Minimum Model Size for Edge AI Safety
> **Test Date:** April 6, 2026
> **Models:** Gemma 4 E2B (2B parameters) vs Gemma 4 E4B (4B parameters)
> **Runtime:** Ollama v0.20.0, RTX 3060 6GB, fully local
> **Conditions:** Same audio files, same spectrograms, same few-shot examples, same CoT prompt, same debouncing, same temperature=0. Only difference: model size.

---

## 1. WHY THIS TEST?

The competition (Gemma 4 Good Hackathon) specifically mentions "E2B and E4B models for edge-based solutions." We optimized everything on E4B and reached 91.0/100. But a critical question remained: "Does the same pipeline work with a smaller model?"

This question is not just academic — it's practical. E2B is smaller (2B vs 4B parameters), faster (~6s vs ~7s per chunk), uses less RAM. If E2B also worked, it could be deployed on much cheaper hardware like Raspberry Pi Zero. But it didn't work — and why it failed is one of the project's most instructive findings.

---

## 2. RESULTS — CATASTROPHIC DIFFERENCE

### Main Score Table

| Scene | Description | Human | E4B Score | E4B FP | E2B Score | E2B FP |
|-------|------------|-------|----------|--------|----------|--------|
| S1 | Pump room (quiet, no human) | NO | **60** | 0 | **0** | 12 |
| S2 | Construction + shouting | YES | **95** | 0 | **0** | 5 |
| S3 | Metallic sound (no human) | NO | **60** | 0 | **0** | 12 |
| S4 | Masked worker (weak signal) | YES | **100** | 0 | **0** | 4 |
| S5 | REAL INCIDENT (drowning) | YES | **100** | 0 | **5** | 4 |
| **WGT AVG** | | | **91.0** | **0** | **2.0** | **37** |

### Detailed Comparison

| Metric | E2B (2B) | E4B (4B) | Difference |
|--------|----------|----------|------------|
| Weighted Average | 2.0 | 91.0 | **45.5x** |
| Total False Positives | 37/60 | 0/60 | **Infinite improvement** |
| Total Correct Detections | Meaningless (alarms everywhere) | 8/60 (targeted) | — |
| S5 Survival Verdict | "CERTAIN" but fake | CERTAIN (real) | — |
| CoT Reasoning | Not functional | Functional | Critical difference |
| Time per Chunk | ~6.2s | ~7.0s | E2B 12% faster |
| Consistency | Consistent (but consistently wrong) | 7/7 consistently correct | — |

---

## 3. WHAT DID E2B DO? (Detailed Analysis)

### E2B's Behavior: "Alarm on Everything"

E2B analyzed 60 chunks across 5 scenes. It alarmed on **all 60**. Every scene, every chunk, human or not, noise or not — it claimed to detect "speech" at 0.90-0.95 confidence.

This is the exact equivalent of the "naive baseline — always alarm" scenario in the benchmark design. According to `answer_key.json` calculations, the naive always-alarm baseline estimated score is 20. E2B scored below even that: **2.0**.

### Per-Scene Analysis

**S1 — Pump Room (No Human):**
E4B: 12 chunks, 0 alarms, 0 FP → 60/100.
E2B: 12 chunks, 12 alarms, 12 FP → 0/100.
E2B said "speech" 12 times on a scene with only pump noise. It completely ignored the CoT instruction ("vertical lines = mechanical, horizontal bands = formant").

**S2 — Construction + Human Voice:**
E4B: Silent on 5 non-human chunks, alarm at chunk 6 (correct), alarm at chunk 12 (correct) → 95/100.
E2B: Alarm on all 12 chunks. Also alarmed on chunks 1-5 with no human (5 FP). Human or not makes no difference → 0/100.

**S3 — Metallic Sound (No Human):**
E4B: 12 chunks, 0 alarms, 0 FP → 60/100. CoT applied "vertical lines = metallic impact" rule.
E2B: 12 chunks, 12 alarms, 12 FP → 0/100. Mistook metallic for human. CoT rule did not work.

**S4 — Masked Worker:**
E4B: Silent on 5 non-human chunks, 5 correct alarms on chunks 6-12 → 100/100.
E2B: Alarm on all 12. Pre-human 4 chunks had FP. Detection exists but unreliable due to FPs → 0/100.

**S5 — Real Incident:**
E4B: Single correct alarm at chunk 6 with 0.75, CERTAIN SURVIVAL → 100/100.
E2B: Alarm on all 12. Pre-human 4 chunks had FP. Detection exists but unreliable → 5/100.
E2B's "CERTAIN SURVIVAL" is misleading — it was already alarming from chunk 1, so it would alarm even without a fall. This is not detection, it's random alarm.

---

## 4. WHY DID E2B FAIL?

### 4.1 Insufficient CoT Reasoning Capacity

E4B's success relies on Chain-of-Thought 3-step reasoning: (1) look for vertical lines → mechanical, don't alarm; (2) look for curved horizontal bands → formant; (3) only alarm if formant present. This three-step logic chain works in E4B but not in E2B. E2B cannot follow prompt instructions — it cannot understand "ONLY alarm if you see formants."

2 billion parameters are insufficient for this level of instruction following. E2B likely only captures keywords like "alarm", "human", "speech" from the prompt and responds "speech detected" to every spectrogram.

### 4.2 Few-Shot Calibration Doesn't Work

When E4B is shown 4 reference spectrograms (3 clean + 1 human), it learns from these examples and distinguishes different patterns. E2B sees the same examples but lacks the capacity to differentiate — it classifies every spectrogram as "human present."

### 4.3 Insufficient Vision Analysis Capacity

Distinguishing visual patterns in spectrograms (vertical lines vs curved bands vs flat noise) requires sophisticated visual analysis. E2B's vision module cannot capture this subtlety. E4B's extra 2 billion parameters provide exactly this visual reasoning capacity.

---

## 5. VALUE FOR THE WRITEUP

This comparison is one of the writeup's strongest technical arguments:

### 5.1 Proves Model Selection Was Deliberate
When the jury asks "why E4B?", the answer is ready: "Because we tested both. E2B scores 2.0 with the same pipeline, E4B scores 91.0. The gap is 45.5x. E2B cannot do CoT reasoning."

### 5.2 Disproves "Smaller Model = Better" Misconception
In edge AI, "smaller model = better" is a common assumption. This test proves that task complexity determines minimum model size. For simple classification E2B may suffice, but for rule-based reasoning (CoT), E4B is the minimum.

### 5.3 Aligns Perfectly with Competition Criteria
The competition mentions "E2B and E4B models for edge-based solutions." Testing both models exactly matches expectations. Also for the Ollama special track: "best project that utilizes and showcases the capabilities of Gemma 4 running locally via Ollama" — comparing two models showcases Ollama's capabilities.

---

## 6. SPEED COMPARISON

| Metric | E2B | E4B |
|--------|-----|-----|
| First chunk (cold start) | 26.4s | 26.3s |
| Normal chunk | ~6.2s | ~7.0s |
| Total (5 scenes) | 398s (6.6 min) | 524s (8.7 min) |

E2B is 12% faster — but this speed advantage is meaningless because the model doesn't work. Giving the wrong answer fast is worse than giving the right answer slow. In a safety system, 0.8 seconds difference doesn't save lives, but false alarms destroy trust.

---

## 7. COMPARISON MATRIX

| Criterion | E2B | E4B | Winner |
|-----------|-----|-----|--------|
| Score (WGT AVG) | 2.0 | 91.0 | **E4B** (45.5x) |
| False Positives | 37/60 | 0/60 | **E4B** |
| CoT Reasoning | Not functional | Functional | **E4B** |
| Few-Shot Learning | Not functional | Functional | **E4B** |
| Speed (chunk) | 6.2s | 7.0s | E2B (12%) |
| RAM Usage | ~1.5GB | ~3GB | E2B |
| Reliability | Unreliable | 7/7 consistent | **E4B** |
| Edge Compatibility | RPi Zero possible | RPi 4+ required | E2B |
| Safety System Use | **Unusable** | **Usable** | **E4B** |

**Conclusion:** Despite E2B's speed and size advantages, it is completely inadequate for this task. E4B is the minimum viable model for edge deployment.

---

## 8. KEY INSIGHT

This test confirmed the project's core philosophy once again: **"Performance gains were achieved not by scaling the model, but by aligning input representation with the model's strengths."** But this statement has a prerequisite — the model must have a minimum reasoning capacity. E2B does not meet this prerequisite. E4B does.

In other words: the spectrogram + CoT + debouncing pipeline is the right tool, but the minimum intelligence to use this tool is at the E4B level. E2B cannot use this tool — it cannot follow instructions, cannot learn from examples, cannot distinguish visual patterns.

---

## 9. CONCLUSION

| Model | WGT AVG | FP | Verdict |
|-------|---------|-----|---------|
| Gemma 4 E2B | 2.0 | 37 | Unusable — alarms on everything |
| Gemma 4 E4B | 91.0 | 0 | CERTAIN SURVIVAL — 7/7 consistent |

The difference between E2B and E4B is not just parameter count — it's reasoning capacity. E4B can "think" (CoT), E2B cannot. In safety-critical systems, this difference is a matter of life and death.

"Giving the wrong answer fast is worse than giving the right answer slow." This sentence summarizes edge AI model selection.

---

*This document contains Gemma 4 E2B vs E4B comparison test findings.*
*E4B: 91.0/100, 0 FP, CERTAIN SURVIVAL | E2B: 2.0/100, 37 FP, unusable*
*Last updated: April 6, 2026*

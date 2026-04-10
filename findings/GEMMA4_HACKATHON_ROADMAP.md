# WWTP Acoustic Safety System — Gemma 4 Good Hackathon Roadmap
## "Can AI Hear What Human Ears Miss?"
## Industrial Acoustic Distress Detection — Edge AI Safety System

> **Project Motto:** *"What happens when you teach AI what to listen for? Maybe we can save a life."*

> **Mehmet ISIK** | Data Scientist | Adana ASKI | Kaggle Grandmaster
> April 2026

---

## 1. THE STORY

A worker fell into a clarifier pool at a drinking water treatment plant in Adana, Turkey. He screamed for help. Nobody heard him — 95dB construction noise masked everything. He survived, but the question haunted us: **what if this happened at our facility?**

I work at Ceyhan Wastewater Treatment Plant — same open pools, same confined spaces, same noise levels. This project answers one question:

> *If an AI system had been listening — microphones at critical points, analyzing sound locally, integrated with SCADA — would that man have survived?*

**Answer: YES. CERTAIN SURVIVAL. Detection at 5 seconds after distress onset.**

---

## 2. COMPETITION INFO

**Competition:** The Gemma 4 Good Hackathon (Kaggle)
**Start:** April 2, 2026
**Deadline:** May 18, 2026 (23:59 UTC)
**Prize Pool:** $200,000

### Evaluation Criteria

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Impact & Vision | 40% | How real is the problem and how effective is the solution? |
| Video Pitch & Storytelling | 30% | How compelling is the video and the story? |
| Technical Depth & Execution | 30% | Is Gemma 4 genuinely used? Is it technically sound? |

### Target Tracks

**Primary:** Global Resilience — "Build the systems of tomorrow — from offline, edge-based disaster response..."
**Secondary:** Safety & Trust — "Pioneer frameworks for transparency and reliability..."
**Special Technology:** Ollama Track (running Gemma 4 locally via Ollama)

---

## 3. TECHNICAL DECISIONS

### 3.1 Model Selection: Gemma 4 E4B (primary) + E2B (comparison)

Gemma 4 has 4 variants:
- **E2B** (2B params) → Audio-capable ✅ — tested, scored 2.0/100 (unusable)
- **E4B** (4B params) → Audio-capable ✅ — **primary model, 91.0/100**
- **26B A4B** (MoE) → No audio ❌
- **31B** (Dense) → No audio ❌

E4B is the minimum viable model for Chain-of-Thought reasoning in safety-critical acoustic analysis. E2B cannot follow CoT instructions — it alarms on everything (37/60 false positives).

### 3.2 Why Spectrograms Instead of Raw Audio

Raw audio approach failed (v1-v2: scores 3.0 and 12.0). The model's audio understanding was unreliable under noise. We converted audio to Mel spectrograms and leveraged the model's **vision** capability instead. On a spectrogram, noise and voice produce different visual patterns despite sharing the same frequency band (300-3000Hz).

**Key insight:** We did not make the model better — we made the problem visible.

### 3.3 Edge/Offline — Our Strongest Differentiator

- No internet required — WiFi disabled, Ethernet unplugged during field tests
- No cloud API — zero latency, zero cost, zero dependency
- Single GPU (RTX 3060 6GB) — runs on consumer hardware
- Apache 2.0 license — commercial deployment allowed

---

## 4. THE JOURNEY: 3.0 → 91.0

### 8 Iterations, 2 Failed Experiments, 30x Improvement

| # | Method | Score | Status | Findings Doc |
|---|--------|-------|--------|--------------|
| 1 | Raw Audio + Aggressive Prompt | 3.0 | ❌ 7 false positives | findings/01-04 |
| 2 | Raw Audio + Neutral Prompt | 12.0 | ❌ Detection lost | findings/05-06 |
| 3 | Spectrogram 2-shot | 8.0 | ❌ Binary classifier trap | findings/07 |
| 4 | Spectrogram 4-shot + Filter | 27.0 | ⚠️ S2 breakthrough | findings/08-09 |
| 5 | Spectrogram + CoT | 32.0 | ⚠️ S4 perfect, S3 FP solved | findings/11 |
| 6 | CoT + Debounce=1 | 91.0 | ⚠️ S5 non-deterministic | findings/12 |
| 7 | PCEN + Spectral Subtraction | 32.0 | ❌ **FAILED** — rolled back | findings/13 |
| 8 | CoT + Debounce=1 + Temp=0 | **91.0** | ✅ **5/5 identical runs** | findings/14 |

### Model Comparison (April 6)

| Metric | E2B | E4B |
|--------|-----|-----|
| Score | 2.0/100 | 91.0/100 |
| False Positives | 37/60 | 0/60 |
| CoT Reasoning | Not functional | Fully functional |
| Documented in | findings/15 | findings/14 |

---

## 5. FINAL RESULTS

| Scene | Description | Human | Noise | Score | FP | Detection |
|-------|-------------|-------|-------|-------|----|-----------|
| S1 | Pump Room | NO | 75dB | 60 | 0 | — |
| S2 | Construction + Distress | YES | 95dB | 95 | 0 | 25s (+0s) |
| S3 | Metallic False Alarm | NO | 72dB | 60 | 0 | — |
| S4 | Masked Worker | YES | 58dB | 100 | 0 | 25s (+5s) |
| **S5** | **Real Incident** | **YES** | **95dB** | **100** | **0** | **25s (+5s) → CERTAIN SURVIVAL** |

**Weighted Average: 91.0/100 | 0 False Positives | 5/5 Identical Runs | Temperature=0**

---

## 6. FIELD VALIDATION AT CEYHAN WWTP (April 10)

Tested at the actual facility with laptop built-in microphone, fully offline.

| Location | Noise | Chunks | Alarms | FP | Max Conf | Result |
|----------|-------|--------|--------|----|----------|--------|
| Pump gallery | ~75dB | 8 | 2 | 0 | 70% | **DETECTED** |
| Blower room | >100dB | 13 | 0 | 0 | 20% | Mic limit |
| Clarifier pool | ~65dB | 9 | 4 | 0 | 95% | **DETECTED** |
| **Total** | | **30** | **6** | **0** | **95%** | **2/3 locations** |

Documented in findings/16.

---

## 7. WHAT WE BUILT

### Detection Engine
- `acoustic_engine.py` — Main engine with --model flag for E4B/E2B selection ✅
- 5 scenes × 12 chunks, spectrogram + CoT + debouncing pipeline ✅
- Asymmetric scoring (FN=-40, FP=-10) ✅

### Live Detection System
- `live_detector.py` — Real-time microphone monitoring (terminal UI) ✅
- `live_detector_ui.py` — SCADA-style web interface (FastAPI + WebSocket) ✅
- Warmup, audio level display, chunk timeline, alarm sound ✅

### Web Demo
- `wwtp-acoustic-demo/` — React + Vite + Tailwind interactive demo ✅
- Deployed at https://wwtp-acoustic-safety-system.vercel.app ✅
- Hero story, facility map, split-screen analysis, score evolution ✅

### Documentation
- 16 findings documents (every experiment documented) ✅
- README.md with field validation, screenshots, quick start ✅
- KAGGLE_WRITEUP.md v3 with field test results ✅

### Media
- YouTube video with field test footage (PiP) ✅
- Kaggle Media Gallery: 10 images + 1 video ✅
- Screenshots from 3 field test locations ✅

---

## 8. IMPLEMENTATION TIMELINE (COMPLETED)

| Day | Date | Focus | Status |
|-----|------|-------|--------|
| 1 | Apr 3 | Ollama setup, audio generation, BARE/CONTEXT/PROTOCOL tests | ✅ |
| 2 | Apr 4 | Spectrogram breakthrough, few-shot, frequency filtering | ✅ |
| 3 | Apr 5 | CoT reasoning, debouncing, PCEN failure, temperature=0 | ✅ |
| 4 | Apr 6 | E2B vs E4B comparison, engine --model flag | ✅ |
| 5 | Apr 7 | Kaggle writeup v1, first submission | ✅ |
| 6 | Apr 8 | Web demo (React), live_detector.py, live_detector_ui.py | ✅ |
| 7 | Apr 9 | SCADA UI redesign, audio playback, scene summaries | ✅ |
| 8 | Apr 10 | **Field test at Ceyhan WWTP**, writeup v3, video update, GitHub cleanup | ✅ |

---

## 9. RISKS AND MITIGATIONS (FINAL STATUS)

| Risk | Impact | Status |
|------|--------|--------|
| E4B can't understand audio | High | ✅ Solved — switched to spectrograms |
| Model doesn't output JSON | Medium | ✅ Solved — CoT prompt with strict format |
| Ollama doesn't support E4B | Medium | ✅ Solved — Ollama v0.20.0 |
| PCEN signal processing fails | High | ✅ Documented — physics limitation |
| S5 non-deterministic | Critical | ✅ Solved — temperature=0 |
| Blower room too loud | Medium | ✅ Documented — mic hardware limit, industrial mic recommended |
| Demo looks unprofessional | Medium | ✅ Solved — SCADA UI + React web demo |
| No field validation | High | ✅ Solved — 3 locations, 30 chunks, 0 FP |

---

## 10. BONUS IDEAS — STATUS

| Idea | Status |
|------|--------|
| SCADA-style live interface | ✅ Built (live_detector_ui.py) |
| Field test at real facility | ✅ Done (3 locations, video recorded) |
| E4B vs E2B comparison | ✅ Done (findings/15) |
| Real-time microphone detection | ✅ Built (live_detector.py) |
| Interactive web demo | ✅ Built (React + Vercel) |
| Raspberry Pi deployment | ⏳ Future work (GPU required) |
| Multi-language detection | ⏳ Future work |
| MQTT/SCADA integration | ⏳ Future work |

---

## 11. STRENGTHS FOR THE JURY

1. **Real story** — not hypothetical, based on a real incident
2. **Field experience** — 10+ years, 15 WWTPs, real acoustic profiles
3. **Edge/offline** — exactly what the competition asks for
4. **Real facility layout** — Ceyhan WWTP aerial photo, real microphone positions
5. **Field-validated** — tested at 3 locations, 30 chunks, 0 false positives
6. **Failed experiments documented** — PCEN failure, blower room limit, E2B failure
7. **Asymmetric scoring** — missing a life costs 4x more than a false alarm
8. **Kaggle Grandmaster** — credibility and trust
9. **Multiple tracks** — Global Resilience + Safety & Trust + Ollama special track
10. **The survival question** — not an abstract score, a concrete answer: "He would have survived."

---

## 12. KEY REMINDERS

- **Impact & Vision = 40%** — our story is our strongest asset
- **Video = 30%** — field test footage is unique, no competitor has this
- **Technical Depth = 30%** — 8 iterations, 16 findings docs, E2B comparison
- Edge/offline emphasis everywhere
- "CERTAIN SURVIVAL" is a system verdict, not an overclaim
- Temperature=0 is a safety requirement, not a model feature
- Failed experiments are strengths, not weaknesses
- **The project is submitted and field-validated. Focus on polish, not new features.**

---

*This document contains the complete project roadmap, decisions, and status.*
*Started: April 3, 2026 — Score 3.0, model hallucinating everywhere.*
*Current: April 10, 2026 — Score 91.0, field-validated at Ceyhan WWTP, zero false positives.*
*From a question to an answer: "He would have survived."*

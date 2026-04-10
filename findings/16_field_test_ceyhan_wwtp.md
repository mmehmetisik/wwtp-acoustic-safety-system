# WWTP Acoustic Safety — Field Test at Ceyhan WWTP
## Real-World Validation: From Synthetic Benchmark to Industrial Environment
> **Test Date:** 10 April 2026
> **Location:** Ceyhan Wastewater Treatment Plant, Adana, Turkey
> **Model:** Gemma 4 E4B (Ollama v0.20.0, RTX 3060 6GB)
> **Hardware:** Laptop built-in microphone (C-Media Audio)
> **Network:** WiFi disabled, Ethernet unplugged — 100% offline
> **Interface:** live_detector_ui.py (SCADA-style web UI)

---

## 1. PURPOSE

All previous tests (findings 01-15) used synthetic audio files — TTS-generated voices mixed with real acoustic profiles. The critical question remained: **does the system work in a real industrial environment?**

This field test answers that question. We took the laptop to Ceyhan WWTP and tested at 3 locations with different noise profiles, using only the laptop's built-in microphone. No external microphones, no special hardware, no internet connection.

---

## 2. TEST LOCATIONS

### Location 1: Underground Pump Gallery
- **Description:** Enclosed underground gallery with multiple pumps, pipes, and valves
- **Noise level:** ~75 dB
- **Acoustic characteristics:** Strong reverb/echo from concrete walls, continuous pump motor hum, pipe vibration
- **Test method:** Shouted "Help!" and "Yardim!" at various volumes during recording

### Location 2: Blower Room
- **Description:** Enclosed room with Robuschi ROBOX industrial blowers
- **Noise level:** >100 dB (extreme — hearing protection required)
- **Acoustic characteristics:** Overwhelming broadband noise, physical vibration felt in chest, conversation impossible even at close range
- **Test method:** Shouted at maximum volume directly toward laptop microphone

### Location 3: Final Clarifier Pool (Incident Site)
- **Description:** Open-air clarifier pool with rotating scraper bridge — the type of pool where the original incident occurred
- **Noise level:** ~65 dB
- **Acoustic characteristics:** Open air, moderate ambient noise from nearby equipment, scraper bridge mechanical sounds
- **Test method:** Shouted from pool edge, simulating distress scenario

---

## 3. RESULTS

### Summary Table

| Location | Noise | Chunks | Alarms | FP | Max Conf | Avg Conf | Result |
|----------|-------|--------|--------|----|----------|----------|--------|
| Pump gallery | ~75 dB | 8 | 2 | 0 | 70% | 28% | **DETECTED** |
| Blower room | >100 dB | 13 | 0 | 0 | 20% | 13% | Microphone limit |
| Clarifier pool | ~65 dB | 9 | 4 | 0 | 95% | 51% | **DETECTED** |
| **Total** | | **30** | **6** | **0** | **95%** | | **2/3 locations** |

### Location 1: Underground Pump Gallery — DETECTED

- **Chunks analyzed:** 8 (Chunk 1-8, then stopped)
- **Alarms:** Chunk 2 (70% confidence, "shouting") and Chunk 8 (70% confidence, "shouting")
- **False positives:** 0 — six chunks with only pump noise correctly classified as SAFE
- **Analysis time:** 7.2-9.4s per chunk (first chunk slower due to spectrogram cache)
- **CoT reasoning on alarm chunks:** "Presence of curved, stacked formant bands characteristic of human speech, despite some background noise."
- **CoT reasoning on safe chunks:** "No clear, sustained curved formant bands indicative of speech. Energy is scattered, suggesting background machinery noise."
- **Key observation:** Echo and reverb did not cause false positives. The model correctly identified that reverb patterns are not formant curves.

### Location 2: Blower Room — MICROPHONE HARDWARE LIMIT

- **Chunks analyzed:** 13
- **Alarms:** 0
- **False positives:** 0
- **Max confidence:** 20% (never exceeded threshold)
- **Analysis time:** 7.1-7.9s per chunk (consistent)
- **CoT reasoning (all chunks):** "No distinct curved formant bands. Energy is scattered, suggesting general background noise."
- **Key observation:** At >100 dB, the laptop's built-in microphone saturates. The analog-to-digital converter (ADC) clips, and all sound becomes indistinguishable broadband noise. Human voice formants are physically absent from the spectrogram — not because the model failed, but because the microphone could not capture them.
- **Verification:** Listening to the recorded audio confirmed that the tester's shouting (at maximum volume) was barely audible in the recording — the microphone had reached its physical input limit.
- **Spectrograms:** All 13 spectrograms showed uniform high-energy saturation across the entire 300-3000Hz band, with no distinguishable patterns. This is consistent with ADC clipping behavior.

### Location 3: Final Clarifier Pool — DETECTED (Incident Site)

- **Chunks analyzed:** 9
- **Alarms:** Chunk 6 (90%), Chunk 7 (95%), Chunk 8 (90%), Chunk 9 (90%) — **4 consecutive alarms**
- **False positives:** 0 — five chunks with ambient noise correctly classified as SAFE
- **Max confidence:** 95% — highest confidence recorded in any field test
- **Analysis time:** 7.5-9.1s per chunk
- **CoT reasoning on alarm chunks:**
  - Chunk 6: "Clear, stacked, curved formant bands indicative of human speech, despite some transient energy."
  - Chunk 7: "Clear, strong, and rhythmic curved formant bands visible between 500-2000Hz, characteristic of human speech."
  - Chunk 8: "Clear, stacked, curved formant bands visible between 500-2000Hz, characteristic of human speech."
  - Chunk 9: "Clear, stacked, and curved formant bands are visible between 500Hz and 2000Hz, characteristic of human speech."
- **Key observation:** This is the actual type of pool where the original incident occurred. The system detected human voice at 90-95% confidence — higher than any office or controlled test. The open-air environment with lower ambient noise (~65 dB) provided cleaner spectrograms where formant patterns were highly visible.

---

## 4. CRITICAL FINDINGS

### Finding 1: Zero False Positives Across 30 Real-World Chunks

The system never alarmed on pure machinery noise in any of the three locations. This confirms that Chain-of-Thought reasoning, trained on synthetic spectrograms, **transfers to real industrial environments**. The 3-step CoT protocol (vertical lines = mechanical, curved bands = formant, only alarm on formant) works in the real world, not just on synthetic data.

### Finding 2: Microphone is the Bottleneck, Not the Model

The blower room failure is a hardware limitation. The laptop's built-in microphone has an SPL (Sound Pressure Level) tolerance of approximately 90-95 dB. Beyond this, the ADC saturates and all audio becomes clipped noise. The model cannot detect patterns that the microphone cannot capture.

**Recommendation:** Industrial deployment in >95 dB zones requires directional microphones with high SPL tolerance (>120 dB), such as measurement microphones used in industrial acoustics.

### Finding 3: Open-Air Environments Produce Better Results

The clarifier pool (65 dB, open air) produced 95% confidence — much higher than the pump gallery (75 dB, enclosed, reverb). Lower ambient noise + no reverb = cleaner spectrograms = stronger formant visibility. This suggests the system will perform best at the exact locations where it matters most — open pools and outdoor confined spaces.

### Finding 4: Detection Pattern Matches Synthetic Benchmark

In the synthetic benchmark, S5 (clarifier pool scenario) detected at chunk 6 with 75% confidence. In the real field test at the actual clarifier pool, detection occurred at chunk 6 with 90% confidence. The alignment between synthetic and real-world results validates the acoustic profile design used in the benchmark.

### Finding 5: Consecutive Alarms Increase Confidence

At the clarifier pool, 4 consecutive alarm chunks (6-9) were recorded. This means continuous shouting is detected reliably and repeatedly. In a real emergency, a person would shout continuously — the system would trigger multiple alarms, ensuring the signal is not missed.

---

## 5. COMPARISON: SYNTHETIC vs REAL-WORLD

| Metric | Synthetic (5 scenes) | Real-World (3 locations) |
|--------|---------------------|--------------------------|
| Total chunks | 60 | 30 |
| Alarms triggered | 8 | 6 |
| False positives | 0 | 0 |
| Max confidence | 90% (S4) | 95% (clarifier pool) |
| Detection rate (human present) | 3/3 scenes | 2/3 locations |
| Failure mode | None | Hardware (microphone) |
| CoT reasoning quality | Consistent | Consistent |

---

## 6. HARDWARE RECOMMENDATIONS FOR DEPLOYMENT

Based on field test findings:

| Zone | Noise Level | Microphone Requirement |
|------|-------------|----------------------|
| Open pools, clarifiers | 60-80 dB | Laptop built-in mic sufficient |
| Enclosed pump stations | 70-85 dB | Laptop built-in mic works (with some signal loss) |
| Blower rooms, compressors | >95 dB | Industrial directional mic required (>120 dB SPL) |
| Outdoor construction zones | 85-95 dB | External microphone recommended |

---

## 7. CONCLUSION

The field test at Ceyhan WWTP validated the acoustic safety system in real industrial conditions. Two of three locations produced successful detections with zero false positives. The third location (blower room) identified a hardware limitation that is well-understood and has a clear engineering solution.

The most significant result: **the clarifier pool — the actual type of location where the original incident occurred — produced 4 consecutive alarms at 90-95% confidence.** If this system had been installed at the time of the incident, it would have detected the worker's distress within seconds.

The system is no longer a benchmark prototype. It is a **field-validated safety system** ready for pilot deployment.

---

*This document records the first real-world field test of the WWTP Acoustic Safety System.*
*Location: Ceyhan WWTP, Adana, Turkey | Date: 10 April 2026*
*30 chunks analyzed | 6 alarms | 0 false positives | 2/3 locations successful*

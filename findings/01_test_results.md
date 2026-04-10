# WWTP Acoustic Safety — Gemma 4 E4B Test Results
## BARE vs CONTEXT vs PROTOCOL Comparison
> **Test Date:** April 3, 2026
> **Model:** Gemma 4 E4B (Ollama, local inference, RTX 3060 6GB)
> **Method:** Single-chunk test per scene (5-second critical segment)

---

## 1. RESULTS TABLE

| Scene | Human | BARE | CONTEXT | PROTOCOL |
|-------|-------|------|---------|----------|
| S1 — Pump Room | NO | Correct | Correct | Correct |
| S2 — Construction + Shouting | YES | Missed | Detected | Detected |
| S3 — Pool Metallic Sound | NO | Correct | Correct | False Alarm |
| S4 — Manhole Masked Voice | YES | Missed | Missed | Detected |
| S5 — Pool CRITICAL | YES | Missed | Missed* | Detected |
| **Success** | | **2/5** | **3/5** | **4/5** |
| **Critical Scenes (S2,S4,S5)** | | **0/3** | **1/3** | **3/3** |

*S5 CONTEXT note: Model returned human_detected=false BUT alarm=true with ESTOP_POOL_BRIDGE action. It did not hear the voice but inferred danger from context text ("worker climbing pool wall"). Interesting but unreliable — in a real system, no text context would be available.

---

## 2. S5 SURVIVAL VERDICT

| Mode | Human Detected | Alarm | Action | Verdict |
|------|----------------|-------|--------|---------|
| BARE | No | No | CONTINUE_MONITORING | WOULD NOT HAVE SURVIVED |
| CONTEXT | No | Yes | ESTOP_POOL_BRIDGE | Alarm triggered but voice not detected |
| PROTOCOL | Yes (0.98) | Yes | ESTOP_POOL_BRIDGE | PROBABLE SURVIVAL |

**PROTOCOL mode:** Confidence 0.98, distress type "screaming", action ESTOP_POOL_BRIDGE, notify Operator + Emergency Services. Detection time 25-30s (fall at 20s, delay ~5-10s). Strong swimmer (30s threshold) would be saved.

---

## 3. MODE-BY-MODE ANALYSIS

### BARE Mode — "Listen with no context"
- Success: 2/5
- Correct: S1 (pump = mechanical), S3 (metallic = mechanical)
- Missed: S2, S4, S5 — all human voices
- Observation: Model identifies quiet environments correctly but cannot hear human voice under noise. Same result as human ears on that day.

### CONTEXT Mode — "Listen with location awareness"
- Success: 3/5
- Improvement over BARE: S2 now detected (+1)
- Still missed: S4, S5
- Interesting finding (S5): human_detected=false but alarm=true. Model did not hear the voice but read "worker climbing pool wall" in the context and triggered ESTOP. It used text reasoning instead of audio reasoning. Clever but unreliable — no such text context would exist in a real deployment.
- Observation: Context helped with medium-difficulty scene (S2) but was insufficient for hardest scenes (S4 masked voice, S5 screaming under noise).

### PROTOCOL Mode — "Listen with full safety protocol"
- Success: 4/5 (best)
- All critical scenes: 3/3
- S4 saved: distress_type "muffled_call", action INITIATE_CONFINED_SPACE_RESCUE, confidence 0.98
- S5 saved: distress_type "screaming", action ESTOP_POOL_BRIDGE, confidence 0.98
- S3 false alarm: Model applied "when in doubt, alarm" rule too aggressively — classified metallic sound as potential human voice.
- Observation: Safety protocol fundamentally changed model behavior. "When in doubt, alarm" made the model more sensitive. This saved lives in S4 and S5 but caused a false alarm in S3. This trade-off is expected and acceptable: false alarm cost (-10) is much lower than missing a human (-40).

---

## 4. KEY FINDINGS

### Finding 1: Context and Protocol Save Lives
BARE mode detected 0/3 critical scenes. PROTOCOL mode detected 3/3. The only difference is the safety protocol added to the prompt. Same audio, same model, different instructions — different outcome: death vs survival.

### Finding 2: False Alarm vs Missing a Human Trade-off
PROTOCOL mode produced a false alarm on S3. This is consistent with our asymmetric scoring system: false alarm costs -10 points, missing a human costs -40 points. The model applied "when in doubt, alarm" and this saved two lives in S4 and S5. One false alarm in exchange for two lives saved is an acceptable trade-off.

### Finding 3: S5 CONTEXT — Interesting Intermediate Behavior
The model did not hear the voice but inferred danger from context text. This demonstrates LLMs' multimodal reasoning capacity — when audio channel fails, the model used text channel for inference. However, this is not reliable for real-world deployment where such text context would not exist.

### Finding 4: S4 — Hardest Scene, Only PROTOCOL Succeeded
Masked/muffled voice + gallery reverb combination was the hardest scene. BARE and CONTEXT completely missed it. Only PROTOCOL with "any muffled voice pattern MUST trigger confined space rescue" instruction achieved detection. This proves that correct safety instructions can make a difference even in extremely difficult signal conditions.

### Finding 5: Model Output Quality
- PROTOCOL S4: confidence 0.98, distress_type "muffled_call", action "INITIATE_CONFINED_SPACE_RESCUE" — perfect JSON output
- PROTOCOL S5: confidence 0.98, distress_type "screaming", action "ESTOP_POOL_BRIDGE", notify ["Operator", "Emergency Services"] — perfect SCADA integration output
- Model not only detected distress but recommended the correct action and correct personnel

---

## 5. IMPLEMENTATION DECISIONS

Based on these test results:

1. **Application will run in PROTOCOL mode** — highest success rate (4/5, critical 3/3)
2. **False alarm risk accepted** — S3 trade-off documented explicitly
3. **JSON output format works** — suitable for SCADA integration
4. **Detection time ~25-30 seconds** — within probable survival threshold
5. **Demo will show three-mode comparison** — the story's power lies in this progression

---

## 6. THE NARRATIVE

"Without context, AI is as helpless as the human ear.
But with the right safety protocol, AI can hear what humans cannot.

BARE mode: The model could not hear. He would not have survived.
CONTEXT mode: The model partially understood. But it was not enough.
PROTOCOL mode: The model heard. Alarm triggered. ESTOP activated.
He would have survived.

Just placing a microphone is not enough.
Teaching AI what to listen for is the difference between saving a life and not."

---

*This document is the reference record of initial test results.*
*Last updated: April 3, 2026*

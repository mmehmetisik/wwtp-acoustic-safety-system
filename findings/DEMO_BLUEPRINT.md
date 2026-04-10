# WWTP Acoustic Safety System — Web Demo Blueprint
## Web Demo Development Plan

> **Purpose:** Interactive web demo for Gemma 4 Good Hackathon. Jury clicks the link, sees the facility map, selects a scene, watches split-screen waveform vs spectrogram comparison, alarm triggers, survival verdict appears.
> **Deploy:** Vercel (automatic deploy from GitHub repo)
> **Technology:** React 18 + Vite + Tailwind CSS
> **Note:** All results are pre-computed. No live inference — does not require Ollama.

---

## 1. PROJECT STRUCTURE

```
wwtp-acoustic-demo/
├── public/
│   ├── images/
│   │   └── wwtp-aerial.png          # Aerial facility photo
│   ├── audio/                        # Scene audio files (WAV → MP3 converted)
│   │   ├── S1_pump_room_normal.mp3
│   │   ├── S2_construction_human.mp3
│   │   ├── S3_pool_false_alarm.mp3
│   │   ├── S4_manhole_masked.mp3
│   │   └── S5_pool_critical.mp3
│   └── spectrograms/                # Spectrogram PNGs per chunk
├── src/
│   ├── App.jsx                       # Main app — all sections here
│   ├── main.jsx                      # React entry point
│   ├── index.css                     # Global styles, Tailwind imports, CSS variables
│   ├── components/
│   │   ├── HeroSection.jsx           # Section 1: Hero banner
│   │   ├── FacilityMap.jsx           # Section 2: Facility map + microphone points
│   │   ├── SplitScreenDemo.jsx       # Section 3: Main demo — waveform vs spectrogram
│   │   ├── ScoreEvolution.jsx        # Section 4: 3.0 → 91.0 animated chart
│   │   ├── TechFooter.jsx            # Section 5: Architecture, links, signature
│   │   ├── ChunkTimeline.jsx         # Sub-component: 12 chunk progress bar
│   │   ├── CoTOverlay.jsx            # Sub-component: CoT steps text flow
│   │   ├── AlarmBanner.jsx           # Sub-component: Red banner on alarm
│   │   └── SurvivalVerdict.jsx       # Sub-component: CERTAIN SURVIVAL animation
│   └── data/
│       └── precomputed.js            # All 5 scenes × 12 chunks pre-computed results
├── package.json
├── vite.config.js
├── vercel.json
└── README.md
```

---

## 2. PRE-COMPUTED DATA STRUCTURE (precomputed.js)

This file is the heart of the project. All results for 5 scenes × 12 chunks are here. With temperature=0, 5 consecutive runs produced identical results — this data is verified and reliable.

*(JavaScript data structure omitted for brevity — see src/data/precomputed.js in the web demo)*

---

## 3. SECTION DESIGNS

### Section 1: HeroSection.jsx
Full-screen height (100vh). Aerial facility photo as background with semi-transparent dark overlay. Centered white text. Main headline large and bold: "Can AI Hear What Human Ears Miss?" Subtitle smaller: "An acoustic safety system for wastewater treatment plants — powered by Gemma 4 E4B, running entirely offline." Below: three stat boxes side by side: "91.0/100 Score", "0 False Positives", "CERTAIN SURVIVAL". Scroll indicator at bottom with chevron animation.

### Section 2: FacilityMap.jsx
Title: "Ceyhan WWTP — Microphone Placement". Aerial photo shown full width. 5 microphone points overlaid, each pulsing (CSS animation). MIC_05 (S5) pulses red and larger. Others green or amber. Hover tooltips: scene name, difficulty, score. Click scrolls to Section 3 with that scene selected. Info box: "5 microphones, 5 scenes, 60 seconds each. 12 chunks × 5 seconds. Model: Gemma 4 E4B via Ollama. Zero internet dependency."

### Section 3: SplitScreenDemo.jsx (MAIN SHOWCASE)
Scene selector at top (5 buttons: S1-S5). Scene info card below. Split-screen in the middle:

LEFT HALF — "Raw Audio (What Humans Hear)": Waveform visualization with animated wave. Gray text: "No detection possible in 95dB noise."

RIGHT HALF — "Voice-Range Spectrogram (What AI Sees)": Spectrogram PNG for current chunk. Red border on alarm chunks. CoT steps appear line by line. Red pulse on alarm.

Below split-screen: "Run Analysis" button. Advances chunk by chunk (2-second intervals). Timeline progress bar fills as chunks advance. Alarm chunk triggers red flash. S5 shows CERTAIN SURVIVAL verdict after chunk 6.

Disclaimer always visible: "Pre-computed results from 5 verified identical runs (temperature=0)."

### Section 4: ScoreEvolution.jsx
Title: "The Journey — 3.0 → 91.0". Vertical timeline on left. Animated bar chart on right (intersection observer triggers animation). Final bar (91.0) gold colored. Summary: "8 iterations, 2 failed experiments, 30x improvement."

### Section 5: TechFooter.jsx
Dark background. Architecture flow diagram: WAV → Mel Spectrogram (300-3000Hz) → 4 Few-Shot Examples → Chain-of-Thought (3-step) → Debouncing (min=1) → SCADA Action. Technology list. GitHub and Kaggle links. Signature: "Mehmet ISIK — Data Scientist, Adana ASKI, Kaggle Grandmaster" and "Gemma 4 Good Hackathon 2026".

---

## 4. DESIGN SYSTEM

### Colors (CSS variables)
```css
:root {
  --bg-primary: #0a0f1e;        /* Dark navy — main background */
  --bg-secondary: #111827;      /* Slightly lighter — card background */
  --bg-card: #1a2332;           /* Card inner */
  --text-primary: #f1f5f9;      /* White-gray — main text */
  --text-secondary: #94a3b8;    /* Gray — secondary text */
  --text-muted: #64748b;        /* Dark gray — note text */
  --accent-green: #22c55e;      /* Green — safe, CERTAIN SURVIVAL */
  --accent-red: #ef4444;        /* Red — alarm, danger */
  --accent-amber: #f59e0b;      /* Amber — warning */
  --accent-blue: #3b82f6;       /* Blue — info, links */
  --accent-gold: #fbbf24;       /* Gold — 91.0 score, success */
  --spectrogram-border: #6366f1; /* Purple — spectrogram border */
}
```

### Typography
Google Fonts: Barlow Condensed for headings (industrial, condensed, serious). Barlow for body text. JetBrains Mono for code/data. Monospace feel — industrial SCADA terminal aesthetic.

### Animations
Hero text fade-in (staggered). Microphone pulse animation (CSS keyframes). Smooth chunk transitions. Red flash on alarm (0.3s). Survival verdict scale-in. Score bars rise with intersection observer. All CSS-based — no external libraries.

---

## 5. SPECTROGRAM IMAGES

Spectrogram PNGs in `spectrogram_test/` directory. Copied to `public/spectrograms/`. If not all 12 chunks available, use existing ones as placeholders. Demo works without images — data structure and animations are sufficient.

---

## 6. AUDIO FILES

Optional. WAV files large (~1MB each). Converted to MP3 for smaller size. Audio playback via HTML5 Audio API. Demo works without audio — animated waveform shown instead.

---

## 7. DEPLOYMENT (Vercel)

```json
{
  "framework": "vite",
  "buildCommand": "npm run build",
  "outputDirectory": "dist"
}
```

Deployed at: https://wwtp-acoustic-safety-system.vercel.app

---

## 8. IMPLEMENTATION STEPS

1. Create Vite + React project
2. Install Tailwind CSS
3. Create precomputed.js data file
4. Build components: HeroSection, FacilityMap, SplitScreenDemo, ScoreEvolution, TechFooter
5. Render all sections in App.jsx
6. Add CSS variables and Google Fonts
7. Create vercel.json
8. Copy spectrogram images and audio files

Priority: SplitScreenDemo first (main showcase), then other sections, animations last.

---

## 9. IMPORTANT NOTES

This is a hackathon demo — it doesn't need to be perfect, it needs to be impressive. The jury decides in 3 minutes. First impression (hero + facility map) + main demo (split-screen alarm animation) + result (CERTAIN SURVIVAL) — these three moments win or lose the project.

Demo must work even without spectrogram images. Results are real — verified with 5/5 consistent runs.

The aerial photo is a real Ceyhan WWTP photograph. This tells the jury "real facility, real problem."

---

*This blueprint contains all information needed to build the WWTP Acoustic Safety System web demo.*
*Author: Mehmet ISIK | Date: April 5, 2026*

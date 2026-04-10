# WWTP Acoustic Safety System — Web Demo Blueprint
## Web Demo Development Plan

> **Amaç:** Gemma 4 Good Hackathon için interaktif web demo. Jüri linke tıklar, tesis haritasını görür, sahne seçer, split-screen'de waveform vs spektrogram karşılaştırması izler, alarm tetiklenir, survival verdict görünür.
> **Deploy:** Vercel (GitHub repo'dan otomatik deploy)
> **Teknoloji:** React 18 + Vite + Tailwind CSS
> **Not:** Tüm sonuçlar önceden hesaplanmış (pre-computed). Canlı inference YOK — Ollama gerektirmez.

---

## 1. PROJE YAPISI

```
wwtp-acoustic-demo/
├── public/
│   ├── images/
│   │   ├── wwtp-aerial.png          # Havadan çekim (kullanıcı sağlayacak)
│   │   └── gemma4-logo.svg          # Gemma 4 logosu (basit SVG)
│   ├── audio/                        # Sahne ses dosyaları (WAV → MP3 dönüştürülmüş, küçük boyut)
│   │   ├── S1_pump_room_normal.mp3
│   │   ├── S2_construction_human.mp3
│   │   ├── S3_pool_false_alarm.mp3
│   │   ├── S4_manhole_masked.mp3
│   │   └── S5_pool_critical.mp3
│   └── spectrograms/                # Her chunk'ın spektrogram PNG'si
│       ├── S1_chunk_01.png ... S1_chunk_12.png
│       ├── S2_chunk_01.png ... S2_chunk_12.png
│       ├── S3_chunk_01.png ... S3_chunk_12.png
│       ├── S4_chunk_01.png ... S4_chunk_12.png
│       └── S5_chunk_01.png ... S5_chunk_12.png
├── src/
│   ├── App.jsx                       # Ana uygulama — tüm bölümler burada
│   ├── main.jsx                      # React entry point
│   ├── index.css                     # Global stiller, Tailwind imports, CSS variables
│   ├── components/
│   │   ├── HeroSection.jsx           # Bölüm 1: Hero banner
│   │   ├── FacilityMap.jsx           # Bölüm 2: Tesis haritası + mikrofon noktaları
│   │   ├── SplitScreenDemo.jsx       # Bölüm 3: Ana demo — waveform vs spektrogram
│   │   ├── ScoreEvolution.jsx        # Bölüm 4: 3.0 → 91.0 animasyonlu grafik
│   │   ├── TechFooter.jsx            # Bölüm 5: Mimari, linkler, imza
│   │   ├── ChunkTimeline.jsx         # Alt komponent: 12 chunk progress bar
│   │   ├── CoTOverlay.jsx            # Alt komponent: CoT adımları metin akışı
│   │   ├── AlarmBanner.jsx           # Alt komponent: Alarm tetiklendiğinde kırmızı banner
│   │   └── SurvivalVerdict.jsx       # Alt komponent: CERTAIN SURVIVAL animasyonu
│   └── data/
│       └── precomputed.js            # Tüm 5 sahne × 12 chunk önceden hesaplanmış sonuçlar
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── vercel.json
└── README.md
```

---

## 2. ÖNCEDEN HESAPLANMIŞ VERİ YAPISI (precomputed.js)

Bu dosya projenin kalbi. 5 sahne × 12 chunk'ın tüm sonuçları burada. Temperature=0 ile 5 ardışık çalıştırmada birebir aynı sonuç elde edildi — bu veriler doğrulanmış ve güvenilir.

```javascript
export const SCENES = {
  S1: {
    id: "S1",
    title: "Pump Room — Normal Operation",
    subtitle: "Pompa Dairesi — Normal Çalışma",
    location: "Pump station, basement level",
    mic: "MIC_01",
    mic_coords: { x: 15, y: 55 },  // Havadan görüntü üzerinde yüzde (%)
    human_present: false,
    distress_onset: null,
    difficulty: "easy",
    noise_level: "75 dB",
    score: 60,
    false_positives: 0,
    first_alarm_sec: null,
    survival_verdict: null,
    description: "Baseline scene. Only mechanical pump noise. No human present. Model must correctly report NO human distress.",
    icon: "⚙️",
    zone_color: "#22c55e",  // green — safe
    chunks: [
      { idx: 1,  time: "00-05s", conf: 0.10, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" },
      { idx: 2,  time: "05-10s", conf: 0.10, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" },
      { idx: 3,  time: "10-15s", conf: 0.10, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" },
      { idx: 4,  time: "15-20s", conf: 0.10, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" },
      { idx: 5,  time: "20-25s", conf: 0.10, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" },
      { idx: 6,  time: "25-30s", conf: 0.10, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" },
      { idx: 7,  time: "30-35s", conf: 0.10, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" },
      { idx: 8,  time: "35-40s", conf: 0.10, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" },
      { idx: 9,  time: "40-45s", conf: 0.10, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" },
      { idx: 10, time: "45-50s", conf: 0.10, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" },
      { idx: 11, time: "50-55s", conf: 0.10, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" },
      { idx: 12, time: "55-60s", conf: 0.10, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" }
    ]
  },

  S2: {
    id: "S2",
    title: "Construction Zone — Human Distress Under Noise",
    subtitle: "İnşaat Alanı — Gürültü Altında İnsan Sesi",
    location: "Construction site adjacent to aeration tanks",
    mic: "MIC_02",
    mic_coords: { x: 40, y: 30 },
    human_present: true,
    distress_onset: 25,
    difficulty: "medium",
    noise_level: "95 dB",
    score: 95,
    false_positives: 0,
    first_alarm_sec: 25,
    first_alarm_chunk: 6,
    survival_verdict: null,
    description: "Heavy construction noise throughout. Human starts shouting for help at second 25. 95dB noise masks the signal.",
    icon: "🏗️",
    zone_color: "#f59e0b",  // amber — warning
    chunks: [
      { idx: 1,  time: "00-05s", conf: 0.10, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 2,  time: "05-10s", conf: 0.10, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 3,  time: "10-15s", conf: 0.10, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 4,  time: "15-20s", conf: 0.10, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 5,  time: "20-25s", conf: 0.10, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 6,  time: "25-30s", conf: 0.75, alarm: true,  type: "speech_call", action: "INITIATE_CONFINED_SPACE_RESCUE", status: "confirmed_alarm", delay: "+0s" },
      { idx: 7,  time: "30-35s", conf: 0.20, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 8,  time: "35-40s", conf: 0.20, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 9,  time: "40-45s", conf: 0.20, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 10, time: "45-50s", conf: 0.20, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 11, time: "50-55s", conf: 0.20, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 12, time: "55-60s", conf: 0.90, alarm: true,  type: "speech_call", action: "INITIATE_CONFINED_SPACE_RESCUE", status: "confirmed_alarm", delay: "+30s" }
    ]
  },

  S3: {
    id: "S3",
    title: "Pool Edge — Metallic Sound (False Alarm Test)",
    subtitle: "Havuz Kenarı — Metalik Ses (Yanlış Alarm Testi)",
    location: "Secondary clarifier pool edge",
    mic: "MIC_03",
    mic_coords: { x: 72, y: 65 },
    human_present: false,
    distress_onset: null,
    difficulty: "medium",
    noise_level: "72 dB",
    score: 60,
    false_positives: 0,
    first_alarm_sec: null,
    survival_verdict: null,
    description: "Metallic scraping and banging from scraper bridge mechanism. Sounds resemble human distress but are mechanical. Model must NOT alarm.",
    icon: "🔩",
    zone_color: "#22c55e",  // green — safe
    chunks: [
      { idx: 1,  time: "00-05s", conf: 0.10, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" },
      { idx: 2,  time: "05-10s", conf: 0.20, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" },
      { idx: 3,  time: "10-15s", conf: 0.20, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" },
      { idx: 4,  time: "15-20s", conf: 0.20, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" },
      { idx: 5,  time: "20-25s", conf: 0.10, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" },
      { idx: 6,  time: "25-30s", conf: 0.20, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" },
      { idx: 7,  time: "30-35s", conf: 0.10, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" },
      { idx: 8,  time: "35-40s", conf: 0.20, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" },
      { idx: 9,  time: "40-45s", conf: 0.10, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" },
      { idx: 10, time: "45-50s", conf: 0.20, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" },
      { idx: 11, time: "50-55s", conf: 0.20, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" },
      { idx: 12, time: "55-60s", conf: 0.20, alarm: false, type: "none", action: "CONTINUE_MONITORING", status: "confirmed_safe" }
    ]
  },

  S4: {
    id: "S4",
    title: "Manhole Gallery — Masked Worker, Weak Signal",
    subtitle: "Menhol Galerisi — Maskeli İşçi, Zayıf Sinyal",
    location: "Underground sewer gallery, manhole MH-07",
    mic: "MIC_04",
    mic_coords: { x: 50, y: 50 },
    human_present: true,
    distress_onset: 20,
    difficulty: "hard",
    noise_level: "58 dB",
    score: 100,
    false_positives: 0,
    first_alarm_sec: 25,
    first_alarm_chunk: 6,
    survival_verdict: null,
    description: "Confined space. Worker wearing respirator mask. Voice muffled by mask + 6m deep gallery reverb. Model must detect the weak signal.",
    icon: "🕳️",
    zone_color: "#f59e0b",  // amber
    chunks: [
      { idx: 1,  time: "00-05s", conf: 0.10, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 2,  time: "05-10s", conf: 0.20, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 3,  time: "10-15s", conf: 0.20, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 4,  time: "15-20s", conf: 0.10, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 5,  time: "20-25s", conf: 0.20, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 6,  time: "25-30s", conf: 0.90, alarm: true,  type: "speech_call", action: "INITIATE_CONFINED_SPACE_RESCUE", status: "confirmed_alarm", delay: "+5s" },
      { idx: 7,  time: "30-35s", conf: 0.90, alarm: true,  type: "speech_call", action: "INITIATE_CONFINED_SPACE_RESCUE", status: "confirmed_alarm", delay: "+10s" },
      { idx: 8,  time: "35-40s", conf: 0.20, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 9,  time: "40-45s", conf: 0.90, alarm: true,  type: "shouting",    action: "INITIATE_CONFINED_SPACE_RESCUE", status: "confirmed_alarm", delay: "+20s" },
      { idx: 10, time: "45-50s", conf: 0.20, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 11, time: "50-55s", conf: 0.90, alarm: true,  type: "speech_call", action: "INITIATE_CONFINED_SPACE_RESCUE", status: "confirmed_alarm", delay: "+30s" },
      { idx: 12, time: "55-60s", conf: 0.90, alarm: true,  type: "shouting",    action: "INITIATE_CONFINED_SPACE_RESCUE", status: "confirmed_alarm", delay: "+35s" }
    ]
  },

  S5: {
    id: "S5",
    title: "Clarifier Pool — REAL INCIDENT SCENARIO",
    subtitle: "Durultma Havuzu — GERÇEK KAZA SENARYOSU",
    location: "Primary clarifier pool — INCIDENT LOCATION",
    mic: "MIC_05",
    mic_coords: { x: 30, y: 65 },
    human_present: true,
    distress_onset: 20,
    difficulty: "critical",
    noise_level: "95 dB",
    score: 100,
    false_positives: 0,
    first_alarm_sec: 25,
    first_alarm_chunk: 6,
    detection_delay_sec: 5,
    survival_verdict: "CERTAIN SURVIVAL",
    survival_color: "#22c55e",
    survival_reason: "Detection at 5s ≤ 15s — both weak and strong swimmers saved",
    score_weight: 0.40,
    description: "The real incident. Worker fell into clarifier pool during construction. 95dB noise masked screams. This scene answers: Would he have survived?",
    icon: "🚨",
    zone_color: "#ef4444",  // red — critical
    chunks: [
      { idx: 1,  time: "00-05s", conf: 0.10, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 2,  time: "05-10s", conf: 0.10, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 3,  time: "10-15s", conf: 0.10, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 4,  time: "15-20s", conf: 0.10, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 5,  time: "20-25s", conf: 0.10, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 6,  time: "25-30s", conf: 0.75, alarm: true,  type: "speech_call", action: "INITIATE_CONFINED_SPACE_RESCUE", status: "confirmed_alarm", delay: "+5s" },
      { idx: 7,  time: "30-35s", conf: 0.20, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 8,  time: "35-40s", conf: 0.10, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 9,  time: "40-45s", conf: 0.20, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 10, time: "45-50s", conf: 0.20, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 11, time: "50-55s", conf: 0.10, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" },
      { idx: 12, time: "55-60s", conf: 0.20, alarm: false, type: "none",        action: "CONTINUE_MONITORING",            status: "confirmed_safe" }
    ]
  }
};

export const SCORE_EVOLUTION = [
  { step: 1, label: "Raw Audio + Aggressive Prompt",   score: 3.0,  status: "fail",    detail: "Model hallucinated — 7 false positives" },
  { step: 2, label: "Raw Audio + Neutral Prompt",      score: 12.0, status: "fail",    detail: "FP cleaned but detection lost" },
  { step: 3, label: "Spectrogram 2-shot",              score: 8.0,  status: "fail",    detail: "Binary classifier trap" },
  { step: 4, label: "Spectrogram 4-shot + Filter",     score: 27.0, status: "weak",    detail: "S2 breakthrough (95/100)" },
  { step: 5, label: "Spectrogram + CoT",               score: 32.0, status: "weak",    detail: "S4 perfect (100/100), S3 FP solved" },
  { step: 6, label: "CoT + Debounce=1",                score: 91.0, status: "excellent",detail: "S5 detected but non-deterministic" },
  { step: 7, label: "PCEN + Spectral Subtraction",     score: 32.0, status: "fail",    detail: "Failed — noise and signal same band" },
  { step: 8, label: "CoT + Debounce=1 + Temp=0",       score: 91.0, status: "excellent",detail: "5/5 identical runs — STABLE" }
];

export const FINAL_STATS = {
  weighted_avg: 91.0,
  total_chunks: 300,  // 5 runs × 60 chunks
  false_positives: 0,
  consistency: "5/5 identical runs",
  s5_verdict: "CERTAIN SURVIVAL",
  s5_delay: "5 seconds",
  model: "Gemma 4 E4B",
  runtime: "Ollama (local, offline)",
  chunk_speed: "~7 seconds per chunk",
  temperature: 0.0
};

export const COT_STEPS = {
  no_alarm: [
    { step: 1, text: "Step 1: Scanning for vertical bright lines (metallic impacts)...", result: "Found: steady horizontal energy bands only" },
    { step: 2, text: "Step 2: Searching for curved horizontal bands (human formants)...", result: "Not found: no formant-like patterns detected" },
    { step: 3, text: "Step 3: Decision — no human voice signature.", result: "→ CONTINUE MONITORING" }
  ],
  alarm: [
    { step: 1, text: "Step 1: Scanning for vertical bright lines (metallic impacts)...", result: "Found: some vertical energy, but not dominant" },
    { step: 2, text: "Step 2: Searching for curved horizontal bands (human formants)...", result: "FOUND: curved bands at 500-2000Hz consistent with human speech" },
    { step: 3, text: "Step 3: Formant pattern confirmed — HUMAN DISTRESS DETECTED", result: "→ 🚨 ALARM — INITIATE RESCUE" }
  ]
};
```

---

## 3. BÖLÜM TASARIMLARI

### Bölüm 1: HeroSection.jsx
Tam ekran yükseklik (100vh). Arka planda havadan tesis çekimi (wwtp-aerial.png), üstüne yarı saydam koyu overlay (rgba(10, 15, 30, 0.75)). Ortada dikey hizalı beyaz metin. Ana başlık büyük ve bold: "Can AI Hear What Human Ears Miss?" (font: serif veya condensed sans-serif, çok büyük, tracking geniş). Alt başlık daha küçük: "An acoustic safety system for wastewater treatment plants — powered by Gemma 4 E4B, running entirely offline." Altında üç istatistik kutusu yan yana: "91.0/100 Score", "0 False Positives", "CERTAIN SURVIVAL". En altta aşağı kaydırma ikonu (chevron animasyonlu). Arka plandaki tesis görüntüsü hafif paralaks efektiyle kayar.

### Bölüm 2: FacilityMap.jsx
Başlık: "Ceyhan WWTP — Microphone Placement". Havadan tesis çekimi tam genişlikte gösterilir. Üzerinde 5 mikrofon noktası, her biri daire şeklinde, yanıp söner (CSS pulse animation). MIC_05 (S5) kırmızı ve daha büyük yanıp söner. Diğerleri yeşil veya turuncu. Her mikrofona hover'da tooltip: sahne adı, zorluk, skor. Tıklayınca sayfa Bölüm 3'e (SplitScreenDemo) kaydırılır ve o sahne seçilmiş olur. Sağ tarafta veya altta kısa bilgi kutusu: "5 microphones, 5 scenes, 60 seconds each. 12 chunks × 5 seconds. Model: Gemma 4 E4B via Ollama. Zero internet dependency."

### Bölüm 3: SplitScreenDemo.jsx (ANA GÖSTERİ)
Bu bölüm sayfanın kalbi. Üstte sahne seçici (5 buton: S1, S2, S3, S4, S5 — her biri kendi rengiyle, seçili olan vurgulu). Altında sahne bilgi kartı (başlık, açıklama, zorluk, gürültü seviyesi, insan var mı).

Ortada split-screen: sol yarı ve sağ yarı, aralarında dikey çizgi.

SOL YARI — "Raw Audio (What Humans Hear)": Üstte "RAW AUDIO" etiketi. Ortada waveform görselleştirmesi — ses dosyasının mevcut chunk'ına karşılık gelen dalga formu. Basit bir sinüs benzeri animasyon yeterli (gerçek waveform datası gerekmez, görsel temsil). Altta gri metin: "Audio encoder: No detection possible in 95dB noise." İnsan olarak bu sesi duyduğunuzda hiçbir şey ayırt edemezsiniz mesajı.

SAĞ YARI — "PCEN Spectrogram (What AI Sees)": Üstte "SPECTROGRAM [300-3000Hz]" etiketi. Ortada o chunk'ın spektrogram PNG görseli (public/spectrograms/ klasöründen). Alarm chunk'ında kırmızı çerçeve belirsin. Altta CoT adımları satır satır belirir (CoTOverlay komponenti). Alarm tetiklendiğinde sağ yarının arka planı kırmızı pulse yapar.

SPLIT-SCREEN ALTINDA: "Run Analysis" butonu. Basıldığında chunk chunk ilerler (2 saniye aralıklarla). Her chunk'ta sol ve sağ güncellenir. 12 chunk'lık progress bar (ChunkTimeline) chunk ilerledikçe dolar. Her chunk'ın sonucu progress bar'da renk olarak görünür (yeşil = güvenli, kırmızı = alarm). Alarm chunk'ında ekranın tamamı kısa bir kırmızı flash yapar. S5'te chunk 6'dan sonra SurvivalVerdict komponenti belirir — büyük yeşil "CERTAIN SURVIVAL" yazısı, altında "Detection at 5s — both weak and strong swimmers saved."

ÖNEMLİ NOT — split-screen altında her zaman görünür: "Pre-computed results from 5 verified identical runs (temperature=0). Live inference requires local Ollama + Gemma 4 E4B installation."

### Bölüm 4: ScoreEvolution.jsx
Başlık: "The Journey — 3.0 → 91.0". Sol tarafta dikey timeline — her adım bir daire, başarılı adımlar yeşil, başarısız adımlar kırmızı. Her daireye hover'da detay tooltip. Sağ tarafta animasyonlu bar chart — sayfa görünür olduğunda (intersection observer) barlar yükseliyor. Son bar (91.0) altın rengi ve parlak. Altında tek satır özet: "8 iterations, 2 failed experiments, 30x improvement. From guessing to saving lives."

### Bölüm 5: TechFooter.jsx
Koyu arka plan. Üstte mimari akış şeması (basit kutular ve oklar, CSS/SVG ile): WAV → Mel Spectrogram (300-3000Hz) → 4 Few-Shot Examples → Chain-of-Thought (3-step) → Debouncing (min=1) → SCADA Action. Altında teknoloji listesi: Gemma 4 E4B, Ollama, librosa, Python, React, Tailwind. Altında GitHub repo linki ve Kaggle writeup linki (placeholder URL'ler, sonra güncellenecek). En altta: "Mehmet ISIK — Data Scientist, Adana ASKI, Kaggle Grandmaster" imzası ve "Gemma 4 Good Hackathon 2026".

---

## 4. TASARIM SİSTEMİ

### Renkler (CSS variables)
```css
:root {
  --bg-primary: #0a0f1e;        /* Koyu lacivert — ana arka plan */
  --bg-secondary: #111827;      /* Biraz daha açık — kart arka planı */
  --bg-card: #1a2332;           /* Kart iç */
  --text-primary: #f1f5f9;      /* Beyaz-gri — ana metin */
  --text-secondary: #94a3b8;    /* Gri — ikincil metin */
  --text-muted: #64748b;        /* Koyu gri — not metinleri */
  --accent-green: #22c55e;      /* Yeşil — güvenli, CERTAIN SURVIVAL */
  --accent-red: #ef4444;        /* Kırmızı — alarm, tehlike */
  --accent-amber: #f59e0b;      /* Turuncu — dikkat, uyarı */
  --accent-blue: #3b82f6;       /* Mavi — bilgi, link */
  --accent-gold: #fbbf24;       /* Altın — 91.0 skoru, başarı */
  --spectrogram-border: #6366f1; /* Mor — spektrogram çerçevesi */
}
```

### Tipografi
Google Fonts'tan: başlıklar için "JetBrains Mono" veya "Space Grotesk" DEĞİL, "IBM Plex Sans Condensed" veya "Barlow Condensed" (endüstriyel, condensed, ciddi). Gövde metni için "IBM Plex Sans" veya "Barlow". Kod/veri için "JetBrains Mono". Monospace his — endüstriyel SCADA terminali estetiği.

### Animasyonlar
Sayfa yüklendiğinde hero metni fade-in (staggered). Mikrofon noktaları pulse animasyonu (CSS keyframes). Split-screen'de chunk geçişleri smooth transition. Alarm tetiklendiğinde kırmızı flash (0.3s). Survival verdict büyük yazıyla scale-in (transform: scale). Skor evrimi barları intersection observer ile yükseliyor. Tüm animasyonlar CSS veya React state ile — harici kütüphane gerekmez (framer-motion KULLANMA, CSS yeterli).

---

## 5. SPEKTrogram GÖRSELLERİ

Spektrogram PNG dosyaları senin bilgisayarında `spectrogram_test/` klasöründe zaten var (S1-S5 chunk'ları). Bunları `public/spectrograms/` klasörüne kopyalaman lazım. Eğer tüm 12 chunk için yoksa, mevcut olanları kullan ve geri kalanlar için placeholder (aynı görsel tekrarı) kullanılabilir. Blueprint'te dosya isimleri: `S1_chunk_01.png` ... `S5_chunk_12.png`.

Alternatif olarak: spektrogram görseli olmadan da çalışır — sağ tarafta sadece confidence değeri, CoT metni ve alarm durumu gösterilir. Görseller sonra eklenir.

---

## 6. SES DOSYALARI

Opsiyonel. WAV dosyaları büyük (~1MB her biri). MP3'e dönüştürülürse küçülür. Sol taraftaki waveform bölümünde ses çalınabilir (HTML5 Audio API). Ama ses dosyaları olmadan da demo çalışır — waveform yerine animasyonlu dalga görseli gösterilir. Ses dosyaları sonra eklenebilir.

---

## 7. DEPLOY (Vercel)

GitHub repo oluştur: `wwtp-acoustic-demo`. Kodu push et. Vercel'e bağla (GitHub entegrasyonu). `vercel.json` içinde framework: vite. Her push'ta otomatik deploy. URL: `wwtp-acoustic-demo.vercel.app` veya custom domain.

```json
{
  "framework": "vite",
  "buildCommand": "npm run build",
  "outputDirectory": "dist"
}
```

---

## 8. IMPLEMENTATION STEPS

Development steps for the web demo:

1. `npm create vite@latest wwtp-acoustic-demo -- --template react` ile proje oluştur.
2. `npm install -D tailwindcss @tailwindcss/vite` ile Tailwind kur.
3. Tailwind config dosyasını oluştur.
4. `src/data/precomputed.js` dosyasını yukarıdaki veri yapısıyla oluştur.
5. Her komponenti sırayla oluştur: HeroSection, FacilityMap, SplitScreenDemo, ScoreEvolution, TechFooter.
6. `src/App.jsx`'de tüm bölümleri sırayla render et.
7. CSS variables'ı `src/index.css`'e ekle.
8. Google Fonts'u import et (Barlow Condensed + IBM Plex Mono veya benzeri endüstriyel font).
9. `vercel.json` ve `README.md` oluştur.
10. Spektrogram görselleri ve ses dosyaları placeholder olarak bırakılabilir — kullanıcı sonra ekler.

ÖNCELİK SIRASI: Önce SplitScreenDemo çalışsın (ana gösteri). Sonra diğer bölümler. En son animasyonlar ve detaylar.

---

## 9. ÖNEMLİ NOTLAR

Bu proje bir yarışma demosu — mükemmel olmak zorunda değil, etkileyici olmak zorunda. Jüri 3 dakikada karar verir. İlk izlenim (hero + tesis haritası) + ana demo (split-screen alarm animasyonu) + sonuç (CERTAIN SURVIVAL) — bu üç an projeyi kazandırır veya kaybettirir.

Spektrogram görselleri olmasa bile demo çalışmalı — veri yapısı ve animasyonlar yeterli. Görseller bonus.

Web sitesinde hiçbir yerde "bu sahte" veya "simülasyon" yazmamalı. Ama "pre-computed" ve "verified results" açıkça belirtilmeli. Sonuçlar gerçek — 5/5 tutarlı run ile doğrulanmış.

Havadan tesis çekimi gerçek Ceyhan WWTP fotoğrafı. Bu jüriye "gerçek bir tesis, gerçek bir problem" mesajı verir.

---

*Bu blueprint WWTP Acoustic Safety System web demo projesini oluşturmak için gerekli tüm bilgileri içerir.*
*Author: Mehmet ISIK | Date: April 5, 2026*

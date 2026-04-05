export const SCENES = {
  S1: {
    id: "S1",
    title: "Pump Room — Normal Operation",
    subtitle: "Pompa Dairesi — Normal Calısma",
    location: "Pump station, basement level",
    mic: "MIC_01",
    mic_coords: { x: 33, y: 18 },
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
    zone_color: "#22c55e",
    audio: "/audio/S1_pump_room_normal.mp3",
    spectrogram: "/spectrograms/S1_chunk_15s.png",
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
    subtitle: "Insaat Alanı — Gurultu Altında Insan Sesi",
    location: "Construction site adjacent to aeration tanks",
    mic: "MIC_02",
    mic_coords: { x: 82, y: 15 },
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
    zone_color: "#f59e0b",
    audio: "/audio/S2_construction_human.mp3",
    spectrogram: "/spectrograms/S2_chunk_30s.png",
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
    subtitle: "Havuz Kenarı — Metalik Ses (Yanlıs Alarm Testi)",
    location: "Secondary clarifier pool edge",
    mic: "MIC_03",
    mic_coords: { x: 28, y: 42 },
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
    zone_color: "#22c55e",
    audio: "/audio/S3_pool_false_alarm.mp3",
    spectrogram: "/spectrograms/S3_chunk_25s.png",
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
    subtitle: "Menhol Galerisi — Maskeli Isci, Zayıf Sinyal",
    location: "Underground sewer gallery, manhole MH-07",
    mic: "MIC_04",
    mic_coords: { x: 22, y: 28 },
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
    zone_color: "#f59e0b",
    audio: "/audio/S4_manhole_masked.mp3",
    spectrogram: "/spectrograms/S4_chunk_25s.png",
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
    subtitle: "Durultma Havuzu — GERCEK KAZA SENARYOSU",
    location: "Primary clarifier pool — INCIDENT LOCATION",
    mic: "MIC_05",
    mic_coords: { x: 62, y: 65 },
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
    zone_color: "#ef4444",
    audio: "/audio/S5_pool_critical.mp3",
    spectrogram: "/spectrograms/S5_chunk_25s.png",
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

export const SCENE_ORDER = ["S1", "S2", "S3", "S4", "S5"];

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
  total_chunks: 300,
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
    { step: 3, text: "Step 3: Formant pattern confirmed — HUMAN DISTRESS DETECTED", result: "→ ALARM — INITIATE RESCUE" }
  ]
};

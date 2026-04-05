import { useState, useEffect, useCallback, useRef } from 'react';
import { SCENES, SCENE_ORDER } from '../data/precomputed';
import ChunkTimeline from './ChunkTimeline';
import CoTOverlay from './CoTOverlay';
import AlarmBanner from './AlarmBanner';
import SurvivalVerdict from './SurvivalVerdict';
import SceneTable from './SceneTable';

const SCENE_SUMMARIES = {
  S1: "All 12 chunks clean — no human voice patterns detected. Zero false positives. System correctly identified mechanical pump noise only.",
  S2: "Alarm at chunks 6 and 12. Human voice formants clearly visible in these chunks. Other chunks: construction noise masked the voice — CoT reasoning correctly withheld alarm when formant pattern was not visible. First detection: 25s (zero delay).",
  S3: "All 12 chunks clean — metallic scraping sounds correctly filtered by CoT reasoning. Step 1 identified vertical bright lines as mechanical impacts, not human voice. Zero false positives.",
  S4: "Alarm at chunks 6, 7, 9, 11, 12. Masked worker's voice detected in multiple chunks. Chunks 8 and 10: mask + reverb temporarily obscured formants. First detection: 25s (+5s delay).",
  S5: "Alarm at chunk 6. Drowning scream detected at 25s — just 5 seconds after the fall. Other chunks: fragmented voice masked by 95dB construction noise. One confirmed detection was enough to save a life. CERTAIN SURVIVAL.",
};

/* ── Animated Waveform (Canvas) ── */
function AnimatedWaveform({ isPlaying, isAlarm }) {
  const canvasRef = useRef(null);
  const animRef = useRef(null);
  const phaseRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;

    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      const midY = H / 2, barCount = 64, barW = W / barCount - 1;
      for (let i = 0; i < barCount; i++) {
        const x = i * (barW + 1);
        let amp = isPlaying
          ? (Math.sin(i * 0.25 + phaseRef.current) * 0.35 + Math.sin(i * 0.4 + phaseRef.current * 1.3) * 0.25 + Math.cos(i * 0.15 + phaseRef.current * 0.7) * 0.2 + 0.15) * midY
          : (Math.sin(i * 0.3) * 0.08 + 0.06) * midY;
        const h = Math.max(2, Math.abs(amp));
        if (isAlarm && isPlaying) {
          ctx.fillStyle = `rgba(239,68,68,${0.6 + Math.sin(phaseRef.current + i) * 0.3})`;
        } else if (isPlaying) {
          const g = ctx.createLinearGradient(x, midY - h, x, midY + h);
          g.addColorStop(0, 'rgba(59,130,246,0.9)');
          g.addColorStop(0.5, 'rgba(99,102,241,0.7)');
          g.addColorStop(1, 'rgba(59,130,246,0.9)');
          ctx.fillStyle = g;
        } else {
          ctx.fillStyle = 'rgba(100,116,139,0.25)';
        }
        ctx.beginPath(); ctx.roundRect(x, midY - h, barW, h * 2, 2); ctx.fill();
      }
      if (isPlaying) phaseRef.current += 0.08;
      animRef.current = requestAnimationFrame(draw);
    };
    draw();
    return () => { if (animRef.current) cancelAnimationFrame(animRef.current); };
  }, [isPlaying, isAlarm]);

  return <canvas ref={canvasRef} width={500} height={140} className="w-full h-[140px]" />;
}

/* ── Scan Line over spectrogram ── */
function ScanLine({ isActive, isAlarm }) {
  if (!isActive) return null;
  const color = isAlarm ? '#ef4444' : '#22c55e';
  const opacity = isAlarm ? 0.7 : 0.5;
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden z-10">
      <div
        className="absolute top-0 bottom-0 w-[2px]"
        style={{
          background: `linear-gradient(to bottom, transparent 0%, ${color} 20%, ${color} 80%, transparent 100%)`,
          opacity,
          boxShadow: `0 0 12px ${color}, 0 0 24px ${color}`,
          animation: 'scanline 2s linear infinite',
        }}
      />
    </div>
  );
}

/* ── Live Status Indicator ── */
function LiveStatus({ chunk, isRunning, isComplete }) {
  if (isComplete) return (
    <div className="flex items-center justify-center gap-3 py-3 px-6 bg-accent-green/10 border border-accent-green/20 rounded-full">
      <span className="w-2.5 h-2.5 rounded-full bg-accent-green" />
      <span className="mono text-sm text-accent-green font-bold">ANALYSIS COMPLETE</span>
    </div>
  );
  if (!isRunning) return (
    <div className="flex items-center justify-center gap-3 py-3 px-6 bg-bg-card border border-white/5 rounded-full">
      <span className="w-2.5 h-2.5 rounded-full bg-text-muted" />
      <span className="mono text-sm text-text-muted">STANDBY</span>
    </div>
  );
  if (chunk?.alarm) return (
    <div className="flex items-center justify-center gap-3 py-3 px-6 bg-accent-red/15 border border-accent-red/30 rounded-full animate-pulse">
      <span className="w-2.5 h-2.5 rounded-full bg-accent-red" />
      <span className="mono text-sm text-accent-red font-bold">ALARM — HUMAN DISTRESS DETECTED</span>
    </div>
  );
  return (
    <div className="flex items-center justify-center gap-3 py-3 px-6 bg-accent-green/5 border border-accent-green/10 rounded-full">
      <span className="w-2.5 h-2.5 rounded-full bg-accent-green animate-pulse" />
      <span className="mono text-sm text-accent-green">MONITORING — Chunk {chunk?.idx}/12</span>
    </div>
  );
}

/* ── Call to Action (after S5) ── */
function DeployCTA() {
  return (
    <div className="animate-fade-in-up mt-8 bg-gradient-to-r from-accent-green/10 via-accent-green/5 to-accent-green/10 border border-accent-green/20 rounded-2xl p-8 text-center">
      <div className="text-2xl md:text-3xl font-extrabold text-white mb-3">
        Deploy-ready. Any WWTP. Any noise level. Zero internet.
      </div>
      <p className="text-text-secondary text-sm max-w-lg mx-auto mb-4">
        This system can be installed at any wastewater treatment plant with standard microphones and a single GPU.
        No cloud, no API, no subscription — just local inference saving lives.
      </p>
      <div className="inline-flex items-center gap-2 text-xs mono text-accent-green/70">
        <span>Powered by Gemma 4 E4B + Ollama</span>
      </div>
    </div>
  );
}

/* ── Main Component ── */
export default function SplitScreenDemo({ initialScene = 'S5' }) {
  const [selectedScene, setSelectedScene] = useState(initialScene);
  const [isRunning, setIsRunning] = useState(false);
  const [currentChunkIdx, setCurrentChunkIdx] = useState(0);
  const [showVerdict, setShowVerdict] = useState(false);
  const [showCTA, setShowCTA] = useState(false);
  const [flashRed, setFlashRed] = useState(false);
  const [scanKey, setScanKey] = useState(0);
  const [audioMuted, setAudioMuted] = useState(true);
  const timerRef = useRef(null);
  const audioRef = useRef(null);

  const scene = SCENES[selectedScene];
  const currentChunk = currentChunkIdx > 0 ? scene.chunks[currentChunkIdx - 1] : null;
  const isComplete = currentChunkIdx >= 12;

  // Load audio when scene changes
  useEffect(() => {
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
    if (scene.audio) {
      const audio = new Audio(scene.audio);
      audio.muted = audioMuted;
      audio.preload = 'auto';
      audioRef.current = audio;
    }
    return () => { if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; } };
  }, [selectedScene]);

  // Sync mute state
  useEffect(() => {
    if (audioRef.current) audioRef.current.muted = audioMuted;
  }, [audioMuted]);

  useEffect(() => { setSelectedScene(initialScene); }, [initialScene]);

  const resetDemo = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (audioRef.current) { audioRef.current.pause(); audioRef.current.currentTime = 0; }
    setIsRunning(false); setCurrentChunkIdx(0); setShowVerdict(false); setShowCTA(false); setFlashRed(false);
  }, []);

  const runAnalysis = useCallback(() => {
    resetDemo();
    setIsRunning(true);
    // Start audio
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
      audioRef.current.play().catch(() => {});
    }
    let idx = 0;
    timerRef.current = setInterval(() => {
      idx++;
      setCurrentChunkIdx(idx);
      setScanKey(prev => prev + 1);
      // Sync audio to chunk time
      if (audioRef.current) audioRef.current.currentTime = (idx - 1) * 5;
      const chunk = scene.chunks[idx - 1];
      if (chunk?.alarm) {
        setFlashRed(true);
        setTimeout(() => setFlashRed(false), 400);
      }
      if (idx >= 12) {
        clearInterval(timerRef.current);
        if (audioRef.current) audioRef.current.pause();
        setIsRunning(false);
        if (scene.survival_verdict) {
          setTimeout(() => setShowVerdict(true), 500);
          setTimeout(() => setShowCTA(true), 1500);
        }
      }
    }, 2000);
  }, [scene, resetDemo]);

  const handleSceneChange = (key) => { resetDemo(); setSelectedScene(key); };

  useEffect(() => { return () => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
  }; }, []);

  // Noise label for INAUDIBLE overlay
  const noiseNum = parseInt(scene.noise_level);
  const inaudibleText = noiseNum >= 90 ? 'INAUDIBLE' : noiseNum >= 70 ? 'BARELY AUDIBLE' : 'LOW NOISE';

  return (
    <section id="split-screen-demo" className={`py-20 px-6 transition-colors duration-300 ${flashRed ? 'bg-accent-red/5' : ''}`}>
      <div className="max-w-6xl mx-auto">

        {/* Header */}
        <div className="text-center mb-14">
          <div className="inline-flex items-center gap-2 bg-accent-amber/10 border border-accent-amber/20 rounded-full px-5 py-1.5 mb-6">
            <span className="w-2 h-2 rounded-full bg-accent-amber animate-pulse" />
            <span className="text-xs text-accent-amber uppercase tracking-widest font-medium mono">Interactive Demo</span>
          </div>
          <h2 className="text-4xl md:text-6xl font-extrabold tracking-wide mb-4">
            Live Analysis Demo
          </h2>
          <p className="text-text-secondary text-lg max-w-2xl mx-auto">
            Select a scene and watch the AI analyze 5-second audio chunks. The model reads spectrograms
            like a doctor reads an X-ray — looking for human voice patterns hidden in noise.
          </p>
        </div>

        {/* Scene overview table */}
        <SceneTable />

        {/* Scene selector */}
        <div className="grid grid-cols-5 gap-2 md:gap-3 mb-8">
          {SCENE_ORDER.map((key) => {
            const s = SCENES[key];
            const isSelected = key === selectedScene;
            const isCritical = s.difficulty === 'critical';
            return (
              <button
                key={key}
                onClick={() => handleSceneChange(key)}
                className={`relative rounded-xl p-3 md:p-4 text-center transition-all cursor-pointer border-2 ${
                  isSelected
                    ? isCritical
                      ? 'bg-accent-red/10 border-accent-red/50 shadow-lg shadow-accent-red/10'
                      : 'bg-white/8 border-white/30 shadow-lg'
                    : 'bg-bg-card border-transparent hover:border-white/10'
                }`}
              >
                {isCritical && (
                  <div className="absolute -top-2 left-1/2 -translate-x-1/2 bg-accent-red text-white text-[8px] font-bold uppercase px-2 py-0.5 rounded-full tracking-wider">
                    Real Incident
                  </div>
                )}
                <div className="text-xl md:text-2xl mb-1">{s.icon}</div>
                <div className="text-xs md:text-sm font-bold text-white">{key}</div>
                <div className="text-[9px] md:text-[10px] text-text-muted mt-1 leading-tight line-clamp-2 hidden md:block">{s.title}</div>
              </button>
            );
          })}
        </div>

        {/* Scene info bar */}
        <div className="bg-bg-card/80 border border-white/5 rounded-xl px-5 py-3 mb-6 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm">
          <span className="text-lg">{scene.icon}</span>
          <span className="font-bold text-white">{scene.title}</span>
          <span className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase border ${
            scene.difficulty === 'critical' ? 'bg-accent-red/15 text-accent-red border-accent-red/20'
            : scene.difficulty === 'hard' ? 'bg-accent-amber/15 text-accent-amber border-accent-amber/20'
            : scene.difficulty === 'medium' ? 'bg-accent-amber/15 text-accent-amber border-accent-amber/20'
            : 'bg-accent-green/15 text-accent-green border-accent-green/20'
          }`}>{scene.difficulty}</span>
          <span className="text-text-muted ml-auto mono text-xs hidden md:flex items-center gap-4">
            <span>{scene.noise_level}</span>
            <span className={scene.human_present ? 'text-accent-red' : 'text-accent-green'}>
              Human: {scene.human_present ? 'YES' : 'NO'}
            </span>
            <span>Score: <span className="text-accent-gold font-bold">{scene.score}/100</span></span>
          </span>
        </div>

        {/* Live status */}
        <div className="flex justify-center mb-6">
          <LiveStatus chunk={currentChunk} isRunning={isRunning} isComplete={isComplete} />
        </div>

        {/* ══ SPLIT SCREEN ══ */}
        <div className="grid grid-cols-1 lg:grid-cols-[2fr_3fr] gap-0 rounded-2xl overflow-hidden border border-white/10 mb-6">

          {/* LEFT — Raw Audio (smaller) */}
          <div className="bg-bg-secondary p-6 lg:border-r border-white/10 flex flex-col">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-text-muted" />
                <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted">What Humans Hear</span>
              </div>
              {/* Audio toggle */}
              <button
                onClick={() => setAudioMuted(!audioMuted)}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 transition-all cursor-pointer border border-white/5"
                title={audioMuted ? 'Unmute audio' : 'Mute audio'}
              >
                <span className="text-sm">{audioMuted ? '🔇' : '🔊'}</span>
                <span className="text-[9px] mono text-text-muted">{audioMuted ? 'MUTED' : 'AUDIO ON'}</span>
              </button>
            </div>
            <p className="text-[11px] text-text-muted/60 mb-5">{scene.noise_level} industrial noise</p>

            {/* Waveform + INAUDIBLE overlay */}
            <div className="bg-bg-primary rounded-xl p-4 flex-1 flex flex-col items-center justify-center min-h-[180px] relative">
              <AnimatedWaveform isPlaying={isRunning} isAlarm={currentChunk?.alarm} />

              {/* INAUDIBLE overlay */}
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <div className="text-4xl md:text-5xl font-extrabold text-white/[0.07] tracking-widest select-none">
                  {inaudibleText}
                </div>
                <div className="text-sm text-white/[0.05] mono mt-1 select-none">
                  {scene.noise_level} — HUMAN EARS CANNOT DETECT
                </div>
              </div>

              {currentChunkIdx > 0 ? (
                <div className="mt-3 mono text-xs text-text-muted relative z-10">
                  Chunk <span className="text-white font-bold">{currentChunk?.idx}</span>/12 — {currentChunk?.time}
                </div>
              ) : (
                <div className="mt-3 text-[11px] text-text-muted/50 italic relative z-10">Waiting for analysis...</div>
              )}
            </div>

            <div className="mt-4 bg-accent-red/5 border border-accent-red/10 rounded-lg px-4 py-3 text-center">
              <div className="text-[11px] text-accent-red/70 font-medium">No detection possible</div>
              <div className="text-[10px] text-text-muted/50 mt-0.5">Human distress signals completely masked by noise</div>
            </div>
          </div>

          {/* RIGHT — Spectrogram (larger) */}
          <div className={`bg-bg-secondary p-6 flex flex-col transition-all duration-300 ${currentChunk?.alarm ? 'bg-accent-red/5' : ''}`}>
            <div className="flex items-center gap-2 mb-1">
              <span className={`w-1.5 h-1.5 rounded-full ${currentChunk?.alarm ? 'bg-accent-red animate-pulse' : 'bg-spectrogram-border'}`} />
              <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted">What AI Sees</span>
            </div>
            <p className="text-[11px] text-text-muted/60 mb-5">Voice-range spectrogram 300-3000Hz</p>

            {/* Spectrogram + scan line */}
            <div className={`relative bg-bg-primary rounded-xl overflow-hidden flex items-center justify-center min-h-[180px] ${
              currentChunk?.alarm ? 'ring-2 ring-accent-red' : 'ring-1 ring-spectrogram-border/20'
            }`}>
              {scene.spectrogram ? (
                <img src={scene.spectrogram} alt={`${scene.id} spectrogram`} className="w-full h-auto object-contain" />
              ) : (
                <div className="text-text-muted text-sm mono p-8 text-center">Spectrogram</div>
              )}
              <ScanLine key={scanKey} isActive={isRunning || (currentChunkIdx > 0)} isAlarm={currentChunk?.alarm} />
            </div>

            {/* Confidence + CoT */}
            {currentChunk ? (
              <div className="mt-4 grid grid-cols-1 md:grid-cols-[1fr_1.5fr] gap-4">
                <div className="bg-bg-primary/50 rounded-lg p-4">
                  <div className="flex justify-between text-xs mono mb-2">
                    <span className="text-text-muted">Confidence</span>
                    <span className={`font-bold ${currentChunk.alarm ? 'text-accent-red' : 'text-accent-green'}`}>
                      {(currentChunk.conf * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="w-full h-3 bg-bg-card rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all duration-500"
                      style={{ width: `${currentChunk.conf * 100}%`, backgroundColor: currentChunk.alarm ? '#ef4444' : '#22c55e' }} />
                  </div>
                  <div className="mt-3 text-[10px] mono text-text-muted">
                    Action: <span className={currentChunk.alarm ? 'text-accent-red' : 'text-text-secondary'}>
                      {currentChunk.action.replace(/_/g, ' ')}
                    </span>
                  </div>
                </div>
                <div className="bg-bg-primary/50 rounded-lg p-4">
                  <CoTOverlay isAlarm={currentChunk?.alarm} isActive={currentChunkIdx > 0} />
                </div>
              </div>
            ) : (
              <div className="mt-4 text-center text-[11px] text-text-muted/50 py-6">
                AI will scan for human voice patterns: curved horizontal bands (formants) in the spectrogram
              </div>
            )}
          </div>
        </div>

        {/* Timeline */}
        <div className="bg-bg-card/50 rounded-xl p-4 mb-6">
          <div className="text-[10px] text-text-muted uppercase tracking-widest mb-3 mono">Analysis Progress — 60 seconds</div>
          <ChunkTimeline chunks={scene.chunks} currentChunkIdx={currentChunkIdx} />

          {/* Scene summary note — after analysis completes */}
          {isComplete && (
            <div className="mt-4 pt-3 border-t border-white/5 animate-fade-in-up">
              <p className="text-xs text-text-secondary italic leading-relaxed">
                {SCENE_SUMMARIES[selectedScene]}
              </p>
            </div>
          )}
        </div>

        {/* Alarm */}
        {currentChunk?.alarm && <div className="mb-6"><AlarmBanner chunk={currentChunk} /></div>}

        {/* Survival Verdict */}
        {showVerdict && <SurvivalVerdict scene={scene} />}

        {/* Call to Action — only after S5 completes */}
        {showCTA && selectedScene === 'S5' && <DeployCTA />}

        {/* Button */}
        <div className="text-center mt-8">
          {!isRunning && !isComplete && (
            <button onClick={runAnalysis}
              className="group px-12 py-4 bg-accent-blue hover:bg-accent-blue/80 text-white text-lg font-bold rounded-xl transition-all cursor-pointer tracking-wide shadow-lg shadow-accent-blue/20">
              <span className="mr-2">▶</span> Run Analysis
            </button>
          )}
          {isRunning && (
            <div className="inline-flex items-center gap-3 bg-accent-amber/10 border border-accent-amber/20 rounded-full px-6 py-3">
              <span className="w-3 h-3 rounded-full bg-accent-amber animate-pulse" />
              <span className="mono text-sm text-accent-amber">Analyzing chunk {currentChunkIdx}/12...</span>
            </div>
          )}
          {isComplete && (
            <button onClick={resetDemo}
              className="px-8 py-3 bg-bg-card border border-white/10 hover:border-white/20 text-text-secondary rounded-xl transition-all cursor-pointer">
              Reset & Run Again
            </button>
          )}
        </div>

        <p className="text-center text-[10px] text-text-muted/40 mt-6 mono">
          Pre-computed results from 5 verified identical runs (temperature=0). Live inference requires local Ollama + Gemma 4 E4B.
        </p>
      </div>
    </section>
  );
}

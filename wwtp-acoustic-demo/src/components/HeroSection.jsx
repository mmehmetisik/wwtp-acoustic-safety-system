import { useEffect, useState, useRef } from 'react';

function useCountUp(target, duration = 1500, startTrigger = false) {
  const [value, setValue] = useState(0);
  const rafRef = useRef(null);

  useEffect(() => {
    if (!startTrigger) return;
    const start = performance.now();
    const animate = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      setValue(Math.round(eased * target));
      if (progress < 1) rafRef.current = requestAnimationFrame(animate);
    };
    rafRef.current = requestAnimationFrame(animate);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [target, duration, startTrigger]);

  return value;
}

export default function HeroSection() {
  const [visible, setVisible] = useState(false);
  const [storyVisible, setStoryVisible] = useState(false);
  const [statsVisible, setStatsVisible] = useState(false);

  useEffect(() => {
    setTimeout(() => setVisible(true), 300);
    setTimeout(() => setStoryVisible(true), 1200);
    setTimeout(() => setStatsVisible(true), 2200);
  }, []);

  return (
    <section id="hero" className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-cover bg-center" style={{ backgroundImage: 'url(/images/wwtp-aerial.png)' }} />
      <div className="absolute inset-0 bg-gradient-to-b from-[rgba(10,15,30,0.85)] via-[rgba(10,15,30,0.80)] to-[rgba(10,15,30,0.95)]" />

      {/* Content */}
      <div className="relative z-10 text-center px-6 max-w-4xl mx-auto">
        {/* Main headline */}
        <h1
          className={`text-5xl md:text-7xl lg:text-8xl font-extrabold tracking-wide text-white leading-[1.1] mb-10 transition-all duration-1000 ${
            visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          Can AI Hear What<br />Human Ears Miss?
        </h1>

        {/* Story block */}
        <div
          className={`max-w-2xl mx-auto mb-12 transition-all duration-1000 ${
            storyVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'
          }`}
        >
          <p className="text-text-secondary text-lg md:text-xl leading-relaxed mb-4">
            A worker fell into a clarifier pool at a drinking water treatment plant in Adana, Turkey.
            The 95dB construction noise masked his screams. <span className="text-white font-semibold">Nobody heard him.</span>
          </p>
          <p className="text-accent-blue text-lg md:text-xl font-medium">
            We asked: What if this happened at our plant?<br />Could an AI have saved him?
          </p>
        </div>

        {/* Answer line */}
        <div
          className={`mb-12 transition-all duration-1000 delay-300 ${
            storyVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'
          }`}
        >
          <p className="text-text-muted text-sm tracking-wider uppercase mb-3">The answer</p>
          <div className="inline-block bg-accent-green/10 border border-accent-green/30 rounded-2xl px-8 py-4">
            <span className="text-accent-green text-3xl md:text-4xl font-extrabold tracking-wider">
              CERTAIN SURVIVAL
            </span>
          </div>
        </div>

        {/* Stats with count-up */}
        <HeroStats statsVisible={statsVisible} />

        {/* 3-Day Timeline */}
        <div
          className={`max-w-2xl mx-auto mb-12 transition-all duration-1000 ${
            statsVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'
          }`}
        >
          <div className="grid grid-cols-3 gap-3">
            {[
              { day: 'v1', score: '3.0', note: 'Model hallucinated everywhere', color: 'border-accent-red/30', scoreColor: 'text-accent-red' },
              { day: 'v4', score: '32.0', note: 'Switched audio → spectrograms', color: 'border-accent-amber/30', scoreColor: 'text-accent-amber' },
              { day: 'v8', score: '91.0', note: '5/5 identical runs. CERTAIN SURVIVAL.', color: 'border-accent-green/30', scoreColor: 'text-accent-green' },
            ].map((d, i) => (
              <div key={i} className={`bg-white/[0.03] border ${d.color} rounded-xl px-4 py-3 text-center`}>
                <div className="text-[10px] text-text-muted uppercase tracking-widest mb-1">{d.day}</div>
                <div className={`text-2xl font-extrabold mono ${d.scoreColor}`}>{d.score}</div>
                <div className="text-[10px] text-text-muted mt-1 leading-tight">{d.note}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Powered by */}
        <div
          className={`transition-all duration-1000 ${
            statsVisible ? 'opacity-100' : 'opacity-0'
          }`}
        >
          <p className="text-text-muted text-sm mb-6">
            Powered by <span className="text-accent-blue font-semibold">Gemma 4 E4B</span> — running 100% offline via Ollama
          </p>
        </div>

        {/* Scroll indicator */}
        <div className={`animate-chevron transition-all duration-1000 delay-500 ${statsVisible ? 'opacity-60' : 'opacity-0'}`}>
          <svg className="w-7 h-7 mx-auto text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
    </section>
  );
}

function HeroStats({ statsVisible }) {
  const detDelay = useCountUp(5, 1200, statsVisible);
  const score = useCountUp(91, 1800, statsVisible);
  const fp = useCountUp(0, 800, statsVisible);
  const runs = useCountUp(5, 1000, statsVisible);

  return (
    <div
      className={`flex flex-wrap justify-center gap-8 md:gap-14 mb-16 transition-all duration-1000 ${
        statsVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'
      }`}
    >
      <div className="text-center">
        <div className="text-3xl md:text-4xl font-bold mono text-accent-green">{detDelay}s</div>
        <div className="text-text-muted text-xs mt-1 uppercase tracking-wider">Detection Delay</div>
      </div>
      <div className="text-center">
        <div className="text-3xl md:text-4xl font-bold mono text-accent-gold">{score}/100</div>
        <div className="text-text-muted text-xs mt-1 uppercase tracking-wider">Weighted Score</div>
      </div>
      <div className="text-center">
        <div className="text-3xl md:text-4xl font-bold mono text-white">{fp}</div>
        <div className="text-text-muted text-xs mt-1 uppercase tracking-wider">False Positives</div>
      </div>
      <div className="text-center">
        <div className="text-3xl md:text-4xl font-bold mono text-accent-blue">{runs}/5</div>
        <div className="text-text-muted text-xs mt-1 uppercase tracking-wider">Identical Runs</div>
      </div>
    </div>
  );
}

import { useEffect, useRef, useState } from 'react';
import { SCORE_EVOLUTION } from '../data/precomputed';

const statusConfig = {
  fail:      { color: '#ef4444', bg: 'bg-accent-red/10',  text: 'text-accent-red',  label: 'FAILED' },
  weak:      { color: '#f59e0b', bg: 'bg-accent-amber/10', text: 'text-accent-amber', label: 'PARTIAL' },
  excellent: { color: '#fbbf24', bg: 'bg-accent-gold/10',  text: 'text-accent-gold',  label: 'SUCCESS' },
};

const storyNotes = {
  1: "First attempt. Fed raw audio to the model with an aggressive safety prompt. Result: 7 false alarms on pure machinery noise.",
  2: "Toned down the prompt. False positives disappeared — but so did real detections.",
  3: "Switched to spectrograms. Model treated it as binary classification — alarm or not. Lost all nuance.",
  4: "Added 4 reference examples. S2 breakthrough: first real detection through 95dB noise.",
  5: "Chain-of-Thought reasoning. Model now explains what it sees. S4 perfect score, S3 false alarm eliminated.",
  6: "Reduced debounce threshold. S5 finally detected — but results varied between runs.",
  7: "We tried to subtract noise from the signal — but removed the human voice too. Noise and speech live in the same 300-3000Hz band. Signal processing can't separate what spectrograms can visually distinguish. Rolled back. Key lesson: the solution is visual pattern recognition, not frequency filtering.",
  8: "Set temperature=0. Deterministic output. 5 consecutive runs, identical results. Final configuration frozen.",
};

export default function ScoreEvolution() {
  const [isVisible, setIsVisible] = useState(false);
  const [expandedStep, setExpandedStep] = useState(null);
  const ref = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setIsVisible(true); observer.disconnect(); } },
      { threshold: 0.15 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return (
    <section id="score-evolution" ref={ref} className="py-20 px-6 bg-bg-secondary">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-14">
          <div className="inline-flex items-center gap-2 bg-accent-gold/10 border border-accent-gold/20 rounded-full px-5 py-1.5 mb-6">
            <span className="text-xs text-accent-gold uppercase tracking-widest font-medium mono">Development Journey</span>
          </div>
          <h2 className="text-4xl md:text-6xl font-extrabold tracking-wide mb-4">
            3.0 → 91.0
          </h2>
          <p className="text-text-secondary text-lg max-w-xl mx-auto">
            8 iterations. 2 failed experiments. 30x improvement.
            <br />
            <span className="text-text-muted">From guessing to saving lives.</span>
          </p>
        </div>

        {/* Timeline */}
        <div className="space-y-3">
          {SCORE_EVOLUTION.map((step, i) => {
            const cfg = statusConfig[step.status];
            const width = isVisible ? Math.max(3, (step.score / 100) * 100) : 0;
            const isFinal = step.step === 8;
            const isExpanded = expandedStep === i;
            const isFailed = step.status === 'fail';

            return (
              <div
                key={step.step}
                className={`rounded-xl border transition-all cursor-pointer ${
                  isFinal
                    ? 'bg-accent-gold/5 border-accent-gold/20'
                    : isExpanded
                    ? 'bg-bg-card border-white/10'
                    : 'bg-bg-card/50 border-white/5 hover:border-white/10'
                }`}
                onClick={() => setExpandedStep(isExpanded ? null : i)}
              >
                {/* Main row */}
                <div className="p-4 flex items-center gap-4">
                  {/* Step number */}
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold mono flex-shrink-0 ${
                    isFinal ? 'bg-accent-gold text-bg-primary' : isFailed ? 'bg-accent-red/20 text-accent-red' : 'bg-white/5 text-text-muted'
                  }`}>
                    {step.step}
                  </div>

                  {/* Label + bar */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className={`text-sm font-medium truncate ${isFinal ? 'text-accent-gold' : 'text-text-primary'}`}>
                        {step.label}
                      </span>
                      <span className={`mono text-sm font-bold ml-3 ${cfg.text}`}>
                        {step.score}
                      </span>
                    </div>
                    <div className="w-full h-2 bg-bg-primary rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${isFinal ? 'shadow-[0_0_12px_rgba(251,191,36,0.4)]' : ''}`}
                        style={{
                          width: `${width}%`,
                          backgroundColor: cfg.color,
                          transition: `width ${600 + i * 100}ms ease-out ${i * 80}ms`,
                        }}
                      />
                    </div>
                  </div>

                  {/* Status badge */}
                  <span className={`text-[9px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider flex-shrink-0 ${cfg.bg} ${cfg.text} border border-current/10`}>
                    {cfg.label}
                  </span>

                  {/* Expand icon */}
                  <svg className={`w-4 h-4 text-text-muted flex-shrink-0 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                    fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>

                {/* Expanded story */}
                {isExpanded && (
                  <div className="px-4 pb-4 pt-0">
                    <div className="ml-12 border-l-2 border-white/5 pl-4">
                      <p className="text-sm text-text-secondary leading-relaxed">
                        {storyNotes[step.step]}
                      </p>
                      <p className="text-xs mono text-text-muted mt-2">{step.detail}</p>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Final stat */}
        <div className="mt-12 text-center">
          <div className="inline-flex items-center gap-4 bg-bg-card border border-accent-gold/20 rounded-2xl px-8 py-5">
            <div className="text-5xl font-extrabold text-accent-gold mono">91.0</div>
            <div className="text-left">
              <div className="text-sm text-white font-bold">Final Score</div>
              <div className="text-xs text-text-muted">5/5 identical runs — temperature=0</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

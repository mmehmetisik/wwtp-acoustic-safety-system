import { useEffect, useState } from 'react';
import { COT_STEPS } from '../data/precomputed';

export default function CoTOverlay({ isAlarm, isActive }) {
  const [visibleSteps, setVisibleSteps] = useState(0);
  const steps = isAlarm ? COT_STEPS.alarm : COT_STEPS.no_alarm;

  useEffect(() => {
    setVisibleSteps(0);
    if (!isActive) return;

    const timers = steps.map((_, i) =>
      setTimeout(() => setVisibleSteps(i + 1), (i + 1) * 400)
    );
    return () => timers.forEach(clearTimeout);
  }, [isActive, isAlarm]);

  return (
    <div className="space-y-2 mt-3">
      <div className="text-[10px] text-text-muted uppercase tracking-widest mb-2">
        Chain-of-Thought Reasoning
      </div>
      {steps.map((step, i) => {
        const show = i < visibleSteps;
        const isLast = i === steps.length - 1;
        return (
          <div
            key={step.step}
            className={`transition-all duration-500 ${
              show ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'
            }`}
          >
            <div className="text-xs mono text-text-secondary">{step.text}</div>
            {show && (
              <div
                className={`text-xs mono mt-0.5 font-medium ${
                  isLast && isAlarm
                    ? 'text-accent-red'
                    : isLast
                    ? 'text-accent-green'
                    : 'text-text-muted'
                }`}
              >
                {step.result}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

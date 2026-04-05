import { useState } from 'react';
import { SCENES, SCENE_ORDER } from '../data/precomputed';

export default function FacilityMap({ onSelectScene }) {
  const [hoveredScene, setHoveredScene] = useState(null);

  const difficultyColors = {
    easy: 'text-accent-green',
    medium: 'text-accent-amber',
    hard: 'text-accent-amber',
    critical: 'text-accent-red',
  };

  return (
    <section id="facility-map" className="py-20 px-6">
      <div className="w-full max-w-full mx-auto">
        {/* Section header */}
        <div className="text-center mb-14">
          <div className="inline-flex items-center gap-2 bg-accent-blue/10 border border-accent-blue/20 rounded-full px-5 py-1.5 mb-6">
            <span className="w-2 h-2 rounded-full bg-accent-blue animate-pulse" />
            <span className="text-xs text-accent-blue uppercase tracking-widest font-medium mono">Facility Overview</span>
          </div>
          <h2 className="text-4xl md:text-6xl font-extrabold text-center mb-5 tracking-wide">
            Ceyhan WWTP — Microphone Placement
          </h2>
          <p className="text-text-secondary text-center max-w-2xl mx-auto text-lg leading-relaxed">
            5 microphones across the facility, each recording 60-second scenes.
          </p>
          <div className="flex flex-wrap justify-center gap-6 mt-6 text-sm mono">
            <span className="text-text-muted"><span className="text-accent-gold font-bold">12</span> chunks x 5s</span>
            <span className="text-white/10">|</span>
            <span className="text-text-muted">Model: <span className="text-accent-blue font-bold">Gemma 4 E4B</span></span>
            <span className="text-white/10">|</span>
            <span className="text-text-muted"><span className="text-accent-green font-bold">100%</span> Offline</span>
          </div>
        </div>

        {/* Map container */}
        <div className="relative overflow-hidden border border-white/10 shadow-2xl rounded-2xl">
          <img
            src="/images/wwtp-aerial.png"
            alt="Ceyhan WWTP Aerial View"
            className="w-full h-auto block max-w-none"
          />

          {/* Microphone points */}
          {SCENE_ORDER.map((key) => {
            const scene = SCENES[key];
            const isCritical = scene.difficulty === 'critical';
            const dotSize = isCritical ? 'w-5 h-5' : 'w-3.5 h-3.5';
            const ringSize = isCritical ? 'w-12 h-12' : 'w-9 h-9';

            return (
              <button
                key={key}
                className="absolute group cursor-pointer"
                style={{
                  left: `${scene.mic_coords.x}%`,
                  top: `${scene.mic_coords.y}%`,
                  transform: 'translate(-50%, -50%)',
                }}
                onClick={() => onSelectScene(key)}
                onMouseEnter={() => setHoveredScene(key)}
                onMouseLeave={() => setHoveredScene(null)}
              >
                {/* Pulse ring */}
                <span
                  className={`absolute inset-0 ${ringSize} rounded-full -translate-x-1/2 -translate-y-1/2 left-1/2 top-1/2`}
                  style={{
                    backgroundColor: scene.zone_color,
                    animation: isCritical
                      ? 'pulse-ring-critical 1.5s ease-out infinite'
                      : 'pulse-ring 2s ease-out infinite',
                    opacity: 0.4,
                  }}
                />
                {/* Dot */}
                <span
                  className={`relative block ${dotSize} rounded-full border-2 border-white shadow-lg z-10`}
                  style={{ backgroundColor: scene.zone_color }}
                />

                {/* Tooltip */}
                {hoveredScene === key && (
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 bg-bg-card border border-white/10 rounded-lg px-4 py-3 min-w-[220px] z-50 shadow-2xl text-left">
                    <div className="text-sm font-bold text-white flex items-center gap-2">
                      <span>{scene.icon}</span> {scene.id}: {scene.title}
                    </div>
                    <div className="text-xs text-text-secondary mt-1">{scene.location}</div>
                    <div className="flex items-center gap-3 mt-2 text-xs">
                      <span className={difficultyColors[scene.difficulty]}>
                        {scene.difficulty.toUpperCase()}
                      </span>
                      <span className="text-text-muted">|</span>
                      <span className="text-accent-gold mono">{scene.score}/100</span>
                      <span className="text-text-muted">|</span>
                      <span className="text-text-muted">{scene.noise_level}</span>
                    </div>
                    {scene.survival_verdict && (
                      <div className="mt-2 text-xs text-accent-green font-bold">
                        {scene.survival_verdict}
                      </div>
                    )}
                    {/* Arrow */}
                    <div className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-t-[6px] border-t-bg-card" />
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* Scene cards grid */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 mt-8">
          {SCENE_ORDER.map((key) => {
            const scene = SCENES[key];
            return (
              <button
                key={key}
                onClick={() => onSelectScene(key)}
                className="bg-bg-card border border-white/5 rounded-lg p-4 text-left hover:border-white/20 transition-all cursor-pointer group"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: scene.zone_color }}
                  />
                  <span className="text-sm font-bold text-white">{scene.icon} {scene.id}</span>
                </div>
                <div className="text-xs text-text-secondary leading-relaxed line-clamp-2">
                  {scene.title}
                </div>
                <div className="text-xs mono text-accent-gold mt-2">{scene.score}/100</div>
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
}

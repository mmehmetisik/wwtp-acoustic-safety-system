import { SCENES, SCENE_ORDER } from '../data/precomputed';

const diffColors = {
  easy: 'text-accent-green',
  medium: 'text-accent-amber',
  hard: 'text-accent-amber',
  critical: 'text-accent-red',
};

export default function SceneTable() {
  return (
    <div className="max-w-4xl mx-auto mb-12">
      <div className="text-center mb-6">
        <h3 className="text-xl font-bold tracking-wide mb-1">5 Scenes at a Glance</h3>
        <p className="text-text-muted text-xs">Each scene is a 60-second recording from a different location in the facility</p>
      </div>

      <div className="bg-bg-card/50 border border-white/5 rounded-xl overflow-hidden">
        {/* Header */}
        <div className="grid grid-cols-[2.5fr_1fr_1fr_1fr_1fr_1fr] gap-0 text-[10px] mono uppercase tracking-widest text-text-muted border-b border-white/5 px-4 py-3">
          <span>Scene</span>
          <span className="text-center">Difficulty</span>
          <span className="text-center">Noise</span>
          <span className="text-center">Human</span>
          <span className="text-center">Score</span>
          <span className="text-center">Detection</span>
        </div>

        {/* Rows */}
        {SCENE_ORDER.map((key) => {
          const s = SCENES[key];
          const isCritical = s.difficulty === 'critical';
          return (
            <div
              key={key}
              className={`grid grid-cols-[2.5fr_1fr_1fr_1fr_1fr_1fr] gap-0 items-center px-4 py-3 border-b border-white/[0.03] text-sm ${
                isCritical ? 'bg-accent-red/[0.03]' : ''
              }`}
            >
              <div className="flex items-center gap-2">
                <span>{s.icon}</span>
                <span className="font-medium text-white">{key}</span>
                <span className="text-text-muted text-xs hidden md:inline truncate">{s.title}</span>
              </div>
              <span className={`text-center text-xs font-bold uppercase ${diffColors[s.difficulty]}`}>
                {s.difficulty}
              </span>
              <span className="text-center text-xs mono text-text-secondary">{s.noise_level}</span>
              <span className={`text-center text-xs font-bold ${s.human_present ? 'text-accent-red' : 'text-accent-green'}`}>
                {s.human_present ? 'YES' : 'NO'}
              </span>
              <span className="text-center text-xs mono font-bold text-accent-gold">{s.score}</span>
              <span className={`text-center text-xs mono ${s.first_alarm_sec ? 'text-white font-bold' : 'text-text-muted'}`}>
                {s.first_alarm_sec ? `${s.detection_delay_sec || s.first_alarm_sec - (s.distress_onset || 0)}s` : '—'}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

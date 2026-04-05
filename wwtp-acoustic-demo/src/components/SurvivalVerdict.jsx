export default function SurvivalVerdict({ scene }) {
  if (!scene.survival_verdict) return null;

  return (
    <div className="animate-scale-in text-center py-8">
      {/* Big verdict */}
      <div
        className="text-5xl md:text-7xl font-extrabold tracking-wider mb-4"
        style={{ color: scene.survival_color }}
      >
        {scene.survival_verdict}
      </div>

      {/* Detection badge */}
      <div className="mb-8 inline-flex items-center gap-2 bg-accent-green/10 border border-accent-green/30 rounded-full px-6 py-2">
        <span className="w-2.5 h-2.5 rounded-full bg-accent-green animate-pulse" />
        <span className="text-accent-green mono text-sm font-medium">
          Detection delay: {scene.detection_delay_sec}s
        </span>
      </div>

      {/* Story card */}
      <div className="max-w-2xl mx-auto bg-bg-card border border-accent-green/10 rounded-2xl p-6 md:p-8 text-left">
        <div className="flex items-start gap-4">
          <div className="text-3xl flex-shrink-0 mt-1">🏊</div>
          <div>
            <p className="text-text-secondary leading-relaxed mb-4">
              Detection at second 25 — just <span className="text-white font-semibold">5 seconds after the fall</span>.
              Emergency stop triggered. Rescue team dispatched.
              Both weak and strong swimmers saved.
            </p>
            <p className="text-text-secondary leading-relaxed mb-4">
              The system heard what 95dB of construction noise made impossible for human ears.
              No human operator, no camera, no line of sight needed — <span className="text-white font-semibold">just sound, analyzed by AI</span>.
            </p>
            <div className="flex flex-wrap gap-3 text-[10px] mono text-text-muted">
              <span className="bg-white/5 rounded-full px-3 py-1">5s detection</span>
              <span className="bg-white/5 rounded-full px-3 py-1">0 false positives</span>
              <span className="bg-white/5 rounded-full px-3 py-1">5/5 identical runs</span>
              <span className="bg-white/5 rounded-full px-3 py-1">temperature=0</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

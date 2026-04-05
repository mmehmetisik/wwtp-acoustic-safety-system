const insights = [
  {
    quote: "If the model's ear can't hear, show its eye.",
    detail: "Audio-based detection failed at 95dB. We converted sound to spectrograms — visual images of frequency over time. The model's vision capability succeeded where its audio understanding could not. 6x faster, dramatically more accurate.",
    icon: "👁️",
    accent: 'accent-blue',
  },
  {
    quote: "One word killed all detection.",
    detail: "Writing 'do NOT alarm' in the prompt zeroed out all 60 chunks — the model heard nothing. A single negative instruction completely shut down detection. What you tell AI matters more than how much you tell it.",
    icon: "🔇",
    accent: 'accent-red',
  },
  {
    quote: "Same frequency band, different visual pattern.",
    detail: "Noise and human voice both live at 300-3000Hz. Signal processing can't separate them — we tried PCEN and spectral subtraction, it destroyed both signals. But on a spectrogram, they look different: flat bands vs curved formants. The AI sees what math can't split.",
    icon: "📊",
    accent: 'accent-amber',
  },
];

export default function KeyInsights() {
  return (
    <section id="key-insights" className="py-16 px-6">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-extrabold tracking-wide mb-3">
            Key Findings
          </h2>
          <p className="text-text-muted text-sm">
            Three discoveries that shaped the system
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {insights.map((ins, i) => (
            <div
              key={i}
              className={`bg-bg-card border border-white/5 rounded-2xl p-6 hover:border-white/10 transition-all`}
            >
              <div className="text-3xl mb-4">{ins.icon}</div>
              <blockquote className={`text-lg font-bold text-${ins.accent} leading-snug mb-4`}>
                "{ins.quote}"
              </blockquote>
              <p className="text-text-secondary text-sm leading-relaxed">
                {ins.detail}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

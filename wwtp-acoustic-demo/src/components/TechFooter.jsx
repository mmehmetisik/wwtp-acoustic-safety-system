import { FINAL_STATS } from '../data/precomputed';

const pipelineSteps = [
  { label: 'WAV Input', sub: '60s chunks', icon: '🎙️' },
  { label: 'Mel Spectrogram', sub: '300-3000Hz power_to_db', icon: '📊' },
  { label: '4 Few-Shot', sub: 'Reference examples', icon: '🎯' },
  { label: 'Chain-of-Thought', sub: '3-step reasoning', icon: '🧠' },
  { label: 'Debouncing', sub: 'CONFIRM_MIN_ALARMS=1', icon: '🔒' },
  { label: 'SCADA Action', sub: 'Alarm / Monitor', icon: '🚨' },
];

const techStack = [
  { name: 'Gemma 4 E4B', desc: 'Multimodal LLM', highlight: true },
  { name: 'Ollama', desc: 'Local inference', highlight: true },
  { name: 'librosa', desc: 'Audio processing', highlight: false },
  { name: 'Python', desc: 'Pipeline engine', highlight: false },
  { name: 'React', desc: 'Web demo UI', highlight: false },
  { name: 'Tailwind CSS', desc: 'Styling', highlight: false },
];

export default function TechFooter() {
  return (
    <footer id="tech-footer" className="bg-bg-primary border-t border-white/5 py-20 px-6">
      <div className="max-w-5xl mx-auto">

        {/* Header */}
        <div className="text-center mb-14">
          <div className="inline-flex items-center gap-2 bg-white/5 border border-white/10 rounded-full px-5 py-1.5 mb-6">
            <span className="text-xs text-text-secondary uppercase tracking-widest font-medium mono">Under The Hood</span>
          </div>
          <h3 className="text-3xl md:text-5xl font-extrabold tracking-wide">
            System Architecture
          </h3>
        </div>

        {/* Pipeline — large horizontal flow */}
        <div className="grid grid-cols-6 gap-1 mb-16">
          {pipelineSteps.map((step, i) => (
            <div key={i} className="relative">
              <div className="bg-bg-card border border-white/10 rounded-xl p-5 text-center h-full hover:border-white/20 transition-all">
                <div className="text-2xl mb-3">{step.icon}</div>
                <div className="text-sm font-bold text-white mono leading-tight">{step.label}</div>
                <div className="text-[10px] text-text-muted mt-2 leading-relaxed">{step.sub}</div>
              </div>
              {/* Arrow between steps */}
              {i < pipelineSteps.length - 1 && (
                <div className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 z-10 w-5 h-5 flex items-center justify-center">
                  <svg className="w-4 h-4 text-accent-blue/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Tech stack */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-16">
          {techStack.map((tech) => (
            <div
              key={tech.name}
              className={`rounded-xl p-4 text-center border transition-all ${
                tech.highlight
                  ? 'bg-accent-blue/5 border-accent-blue/20'
                  : 'bg-bg-card/50 border-white/5'
              }`}
            >
              <div className={`text-sm font-bold mono ${tech.highlight ? 'text-accent-blue' : 'text-text-primary'}`}>{tech.name}</div>
              <div className="text-[10px] text-text-muted mt-1">{tech.desc}</div>
            </div>
          ))}
        </div>

        {/* Why Offline Matters */}
        <div className="bg-gradient-to-r from-accent-blue/5 via-accent-blue/10 to-accent-blue/5 border border-accent-blue/15 rounded-2xl p-8 mb-16 text-center">
          <h4 className="text-xl md:text-2xl font-extrabold text-white mb-4">Why Offline Matters</h4>
          <p className="text-text-secondary text-lg leading-relaxed max-w-2xl mx-auto mb-4">
            When someone is drowning, you can't wait for a cloud API round trip.
            This system runs on a <span className="text-white font-semibold">single GPU at the pool's edge</span>.
          </p>
          <div className="flex flex-wrap justify-center gap-4 text-sm mono">
            <span className="bg-white/5 rounded-full px-4 py-1.5 text-text-muted">No internet</span>
            <span className="bg-white/5 rounded-full px-4 py-1.5 text-text-muted">No subscription</span>
            <span className="bg-white/5 rounded-full px-4 py-1.5 text-text-muted">No latency</span>
            <span className="bg-white/5 rounded-full px-4 py-1.5 text-text-muted">~7s per chunk</span>
          </div>
        </div>

        {/* Key stats — bigger */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-16">
          {[
            { label: 'Model', value: FINAL_STATS.model, color: 'text-accent-blue' },
            { label: 'Runtime', value: FINAL_STATS.runtime, color: 'text-accent-green' },
            { label: 'Temperature', value: FINAL_STATS.temperature, color: 'text-accent-amber' },
            { label: 'Consistency', value: FINAL_STATS.consistency, color: 'text-accent-gold' },
          ].map((stat) => (
            <div key={stat.label} className="bg-bg-card/30 rounded-xl p-5 text-center">
              <div className={`text-xl mono font-bold ${stat.color}`}>{String(stat.value)}</div>
              <div className="text-[10px] text-text-muted uppercase tracking-wider mt-2">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Closing message */}
        <div className="text-center mb-16 max-w-2xl mx-auto">
          <p className="text-xl md:text-2xl text-text-secondary leading-relaxed italic">
            "Same input, same output, every time.
            <br />
            Because when someone's life depends on it,
            <br />
            <span className="text-white font-semibold not-italic">'sometimes' is not good enough.</span>"
          </p>
        </div>

        {/* Signature */}
        <div className="text-center border-t border-white/5 pt-8">
          <div className="text-lg font-bold text-white mb-1">Mehmet ISIK</div>
          <div className="text-sm text-text-secondary mb-4">Data Scientist, Adana ASKI | Kaggle Grandmaster</div>
          <div className="text-xs text-text-muted mono mb-6">Gemma 4 Good Hackathon 2026</div>
          <div className="flex flex-wrap justify-center gap-4 mt-4">
            <a href="https://github.com/mmehmetisik/wwtp-acoustic-safety-system" target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-2 text-xs text-text-muted hover:text-text-secondary transition-colors">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
              GitHub
            </a>
            <span className="text-white/10">|</span>
            <a href="https://www.kaggle.com/code/mehmetisik/wwtp-acoustic-safety-system" target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-2 text-xs text-text-muted hover:text-text-secondary transition-colors">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M18.825 23.859c-.022.092-.117.141-.281.141h-3.139c-.187 0-.351-.082-.492-.248l-5.178-6.589-1.448 1.374v5.111c0 .235-.117.352-.351.352H5.505c-.236 0-.354-.117-.354-.352V.353c0-.233.118-.353.354-.353h2.431c.234 0 .351.12.351.353v14.343l6.203-6.272c.165-.165.33-.246.495-.246h3.239c.144 0 .236.06.281.18.046.149.034.238-.036.27l-6.555 6.344 6.836 8.507c.095.104.117.208.075.303z"/></svg>
              Kaggle
            </a>
            <span className="text-white/10">|</span>
            <a href="https://www.linkedin.com/in/mehmetisik4601/" target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-2 text-xs text-text-muted hover:text-text-secondary transition-colors">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
              LinkedIn
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}

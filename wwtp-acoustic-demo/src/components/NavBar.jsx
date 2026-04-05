import { useState, useEffect } from 'react';

const links = [
  { label: 'Story', target: 'hero' },
  { label: 'Map', target: 'facility-map' },
  { label: 'Insights', target: 'key-insights' },
  { label: 'Demo', target: 'split-screen-demo' },
  { label: 'Journey', target: 'score-evolution' },
  { label: 'Architecture', target: 'tech-footer' },
];

export default function NavBar() {
  const [scrolled, setScrolled] = useState(false);
  const [active, setActive] = useState('hero');

  useEffect(() => {
    const onScroll = () => {
      setScrolled(window.scrollY > 80);

      // Find which section is in view
      for (let i = links.length - 1; i >= 0; i--) {
        const el = document.getElementById(links[i].target);
        if (el) {
          const rect = el.getBoundingClientRect();
          if (rect.top <= 150) {
            setActive(links[i].target);
            break;
          }
        }
      }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const handleClick = (target) => {
    document.getElementById(target)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'bg-bg-primary/90 backdrop-blur-md border-b border-white/5 py-2'
          : 'bg-transparent py-4'
      }`}
    >
      <div className="max-w-5xl mx-auto px-6 flex items-center justify-between">
        {/* Logo / Title */}
        <button
          onClick={() => handleClick('hero')}
          className={`text-sm font-bold mono tracking-wider transition-all cursor-pointer ${
            scrolled ? 'text-white opacity-100' : 'text-white opacity-0'
          }`}
        >
          WWTP<span className="text-accent-blue">.</span>AI
        </button>

        {/* Nav links */}
        <div className="flex items-center gap-1">
          {links.map((link) => (
            <button
              key={link.target}
              onClick={() => handleClick(link.target)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                active === link.target
                  ? 'text-white bg-white/10'
                  : 'text-text-muted hover:text-text-secondary'
              }`}
            >
              {link.label}
            </button>
          ))}
        </div>
      </div>
    </nav>
  );
}

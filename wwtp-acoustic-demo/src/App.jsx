import { useState, useCallback, useEffect, useRef } from 'react';
import NavBar from './components/NavBar';
import HeroSection from './components/HeroSection';
import FacilityMap from './components/FacilityMap';
import KeyInsights from './components/KeyInsights';
import SplitScreenDemo from './components/SplitScreenDemo';
import ScoreEvolution from './components/ScoreEvolution';
import TechFooter from './components/TechFooter';

/* Wrapper that fades in when scrolled into view */
function FadeSection({ children, className = '' }) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setVisible(true); observer.disconnect(); } },
      { threshold: 0.08 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={ref} className={`section-fade ${visible ? 'visible' : ''} ${className}`}>
      {children}
    </div>
  );
}

export default function App() {
  const [selectedScene, setSelectedScene] = useState('S5');

  const handleSelectScene = useCallback((sceneKey) => {
    setSelectedScene(sceneKey);
    setTimeout(() => {
      document.getElementById('split-screen-demo')?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  }, []);

  return (
    <div className="min-h-screen bg-bg-primary">
      <NavBar />
      <HeroSection />
      <FadeSection>
        <FacilityMap onSelectScene={handleSelectScene} />
      </FadeSection>
      <FadeSection>
        <KeyInsights />
      </FadeSection>
      <FadeSection>
        <SplitScreenDemo initialScene={selectedScene} />
      </FadeSection>
      <FadeSection>
        <ScoreEvolution />
      </FadeSection>
      <FadeSection>
        <TechFooter />
      </FadeSection>
    </div>
  );
}

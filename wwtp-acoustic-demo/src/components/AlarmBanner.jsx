export default function AlarmBanner({ chunk }) {
  if (!chunk || !chunk.alarm) return null;

  return (
    <div className="animate-flash-red border border-accent-red/50 rounded-xl p-4 bg-accent-red/10 backdrop-blur-sm">
      <div className="flex items-center justify-center gap-3">
        <span className="text-3xl">🚨</span>
        <div className="text-center">
          <div className="text-accent-red font-bold text-lg mono tracking-wider">
            ALARM TRIGGERED — CHUNK {chunk.idx}
          </div>
          <div className="text-sm text-text-secondary mt-1">
            {chunk.action.replace(/_/g, ' ')} | Confidence: {(chunk.conf * 100).toFixed(0)}%
            {chunk.type !== 'none' && ` | Type: ${chunk.type.replace(/_/g, ' ')}`}
          </div>
        </div>
        <span className="text-3xl">🚨</span>
      </div>
    </div>
  );
}

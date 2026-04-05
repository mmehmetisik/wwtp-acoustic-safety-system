export default function ChunkTimeline({ chunks, currentChunkIdx }) {
  return (
    <div className="w-full">
      <div className="flex items-center gap-1">
        {chunks.map((chunk, i) => {
          const isActive = i < currentChunkIdx;
          const isCurrent = i === currentChunkIdx - 1;
          let bgColor = 'bg-bg-card';

          if (isActive) {
            bgColor = chunk.alarm ? 'bg-accent-red' : 'bg-accent-green';
          }

          return (
            <div key={chunk.idx} className="flex-1 flex flex-col items-center gap-1">
              <div
                className={`w-full h-3 rounded-sm transition-all duration-300 ${bgColor} ${
                  isCurrent ? 'ring-2 ring-white/50 scale-y-125' : ''
                }`}
              />
              <span className="text-[9px] text-text-muted mono hidden md:block">
                {chunk.idx}
              </span>
            </div>
          );
        })}
      </div>
      <div className="flex justify-between mt-1 text-[10px] text-text-muted mono">
        <span>0s</span>
        <span>30s</span>
        <span>60s</span>
      </div>
    </div>
  );
}

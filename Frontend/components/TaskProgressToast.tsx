'use client';

import React from 'react';

interface TaskProgressToastProps {
  runStatus: string;
  events: any[];
}

export const TaskProgressToast: React.FC<TaskProgressToastProps> = ({ runStatus, events }) => {
  if (runStatus !== 'running' && runStatus !== 'starting') return null;

  const latestEvent = events[events.length - 1];
  const message = latestEvent?.message || 'Initializing Celery task & agent pipeline...';

  return (
    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-zinc-950/95 backdrop-blur-2xl border border-blue-500/40 rounded-2xl px-5 py-3.5 shadow-[0_0_30px_rgba(59,130,246,0.25)] flex items-center space-x-3.5 z-40 animate-in fade-in slide-in-from-bottom-4 duration-300 ring-1 ring-white/10 max-w-lg w-full mx-4">
      <div className="w-4 h-4 rounded-full border-2 border-blue-500 border-t-transparent animate-spin shrink-0 shadow-md shadow-blue-500/50" />
      <div className="flex-1 min-w-0">
        <div className="text-[10px] uppercase font-mono tracking-wider text-blue-400 font-bold mb-0.5 flex items-center justify-between">
          <span>Celery Task & Agent Pipeline</span>
          {latestEvent?.seq && <span className="text-zinc-500 font-mono">#{latestEvent.seq}</span>}
        </div>
        <div className="text-xs text-zinc-200 font-medium truncate font-mono">
          {message}
        </div>
      </div>
    </div>
  );
};

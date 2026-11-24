'use client';

import React from 'react';
import { Handle, Position } from '@xyflow/react';

export const AgentNode = ({ data }: { data: any }) => {
  const { label, role, status, visitCount, activeTool, error } = data;

  let bgClass = 'bg-zinc-900/90 border-zinc-800 text-zinc-200';
  let shadowStyle = 'shadow-xl shadow-black/40';
  let statusDot = 'bg-zinc-500';

  if (status === 'active') {
    bgClass = 'bg-gradient-to-b from-indigo-950/90 via-zinc-900/95 to-zinc-950/95 border-blue-500 text-white';
    shadowStyle = 'shadow-[0_0_30px_rgba(59,130,246,0.35)] ring-2 ring-blue-500/80 animate-pulse';
    statusDot = 'bg-blue-500 animate-ping shadow-lg shadow-blue-500';
  } else if (status === 'completed') {
    bgClass = 'bg-gradient-to-b from-emerald-950/80 via-zinc-900/95 to-zinc-950/95 border-emerald-500/80 text-white';
    shadowStyle = 'shadow-xl shadow-emerald-950/50 ring-1 ring-emerald-500/30';
    statusDot = 'bg-emerald-400 shadow-sm shadow-emerald-400';
  } else if (status === 'error') {
    bgClass = 'bg-gradient-to-b from-red-950/90 via-zinc-900/95 to-zinc-950/95 border-red-500 text-white';
    shadowStyle = 'shadow-xl shadow-red-950/50 ring-2 ring-red-500';
    statusDot = 'bg-red-500 shadow-sm shadow-red-500';
  }

  return (
    <div className={`px-4 py-3.5 rounded-2xl border backdrop-blur-xl w-72 transition-all duration-300 ${bgClass} ${shadowStyle}`}>
      <Handle type="target" position={Position.Top} className="!bg-zinc-500 !w-2.5 !h-2.5 !border-2 !border-zinc-950" />

      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2.5">
          <span className={`w-2.5 h-2.5 rounded-full ${statusDot}`} />
          <span className="font-bold text-xs tracking-wider uppercase text-zinc-100">{role}</span>
        </div>
        {visitCount > 0 && (
          <span className="px-2 py-0.5 text-[11px] font-semibold bg-blue-500/15 text-blue-300 rounded-full border border-blue-500/30 font-mono">
            Visits: {visitCount}
          </span>
        )}
      </div>

      <div className="text-xs text-zinc-300 font-medium mb-3 leading-relaxed">{label}</div>

      {activeTool && (
        <div className="mt-2.5 p-2 bg-amber-500/10 border border-amber-500/30 rounded-xl text-[11px] text-amber-200 flex items-center justify-between shadow-lg backdrop-blur-md">
          <div className="flex items-center space-x-2 truncate">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-spin" />
            <span className="truncate font-mono font-bold tracking-tight">Tool: {activeTool}</span>
          </div>
        </div>
      )}

      {error && (
        <div className="mt-2.5 p-2 bg-red-500/15 border border-red-500/40 rounded-xl text-[11px] text-red-200 truncate font-mono">
          Error: {error}
        </div>
      )}

      <Handle type="source" position={Position.Bottom} className="!bg-zinc-500 !w-2.5 !h-2.5 !border-2 !border-zinc-950" />
    </div>
  );
};

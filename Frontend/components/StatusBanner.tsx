'use client';

import React from 'react';

interface StatusBannerProps {
  runStatus: string;
  ticker: string;
  maxRounds: number;
  capital: number;
  riskTolerance: string;
  taskId: string | null;
  events?: any[];
  currentState?: any;
  isSidebarCollapsed?: boolean;
  sidebarWidth?: number;
}

export const StatusBanner: React.FC<StatusBannerProps> = ({
  runStatus,
  ticker,
  maxRounds,
  capital,
  riskTolerance,
  taskId,
  events = [],
  currentState = {},
  isSidebarCollapsed = false,
}) => {
  const bullCount = currentState?.bull_case_outputs?.length || events.filter((e: any) => e.node_name === 'bull_analyst' && e.event === 'node_end').length;
  const bearCount = currentState?.bear_case_outputs?.length || events.filter((e: any) => e.node_name === 'bear_analyst' && e.event === 'node_end').length;

  return (
    <div
      className={`absolute top-6 left-6 transition-all duration-300 bg-zinc-950/90 backdrop-blur-2xl border border-zinc-800/90 rounded-2xl p-3.5 text-xs flex flex-wrap items-center gap-3.5 shadow-2xl z-10 ring-1 ring-white/5 ${
        isSidebarCollapsed ? 'right-6 md:right-auto' : 'right-[460px] max-w-[calc(100vw-480px)] md:right-auto'
      }`}
    >
      <div className="flex items-center space-x-2.5">
        <span
          className={`w-3 h-3 rounded-full shadow-md ${
            runStatus === 'running'
              ? 'bg-blue-500 animate-ping shadow-blue-500/50'
              : runStatus === 'completed'
              ? 'bg-emerald-500 shadow-emerald-500/50'
              : runStatus === 'error'
              ? 'bg-red-500 shadow-red-500/50'
              : 'bg-zinc-500'
          }`}
        />
        <span className="font-bold uppercase tracking-wider text-zinc-100">
          Status:{' '}
          <span
            className={
              runStatus === 'running'
                ? 'text-blue-400 font-extrabold'
                : runStatus === 'completed'
                ? 'text-emerald-400 font-extrabold'
                : runStatus === 'error'
                ? 'text-red-400 font-extrabold'
                : 'text-zinc-400 font-semibold'
            }
          >
            {runStatus}
          </span>
        </span>
      </div>

      <div className="h-4 w-px bg-zinc-800" />

      <div className="flex items-center space-x-2 font-mono">
        <span className="text-zinc-500">Target:</span>
        <span className="text-blue-400 font-bold bg-blue-500/10 px-2 py-0.5 rounded-lg border border-blue-500/20">{ticker}</span>
      </div>

      <div className="h-4 w-px bg-zinc-800" />

      <div className="flex items-center space-x-2 font-mono">
        <span className="text-zinc-500">Debate:</span>
        <span className="text-zinc-200 font-bold bg-zinc-900/90 px-2.5 py-0.5 rounded-lg border border-zinc-800">
          Bull: <span className="text-emerald-400 font-extrabold">{bullCount}</span> | Bear: <span className="text-amber-400 font-extrabold">{bearCount}</span>
        </span>
      </div>

      <div className="h-4 w-px bg-zinc-800" />

      <div className="flex items-center space-x-2 font-mono">
        <span className="text-zinc-500">Max Rounds:</span>
        <span className="text-amber-400 font-bold bg-amber-500/10 px-2 py-0.5 rounded-lg border border-amber-500/20">{maxRounds}</span>
      </div>

      <div className="h-4 w-px bg-zinc-800" />

      <div className="flex items-center space-x-2 font-mono">
        <span className="text-zinc-500">Capital:</span>
        <span className="text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded-lg border border-emerald-500/20">₦{capital.toLocaleString()}</span>
      </div>

      <div className="h-4 w-px bg-zinc-800" />

      <div className="flex items-center space-x-2 font-mono">
        <span className="text-zinc-500">Risk:</span>
        <span className="text-purple-300 font-bold bg-purple-500/10 px-2 py-0.5 rounded-lg border border-purple-500/20">{riskTolerance}</span>
      </div>

      {taskId && (
        <>
          <div className="h-4 w-px bg-zinc-800" />
          <span className="font-mono text-zinc-400 text-[11px] bg-zinc-900/90 px-2.5 py-1 rounded-lg border border-zinc-800 shadow-inner">ID: {taskId.slice(0, 8)}</span>
        </>
      )}
    </div>
  );
};

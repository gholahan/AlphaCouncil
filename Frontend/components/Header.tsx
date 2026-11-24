'use client';

import React from 'react';

interface HeaderProps {
  ticker: string;
  maxRounds: number;
  capital: number;
  runStatus: string;
  onOpenConfig: () => void;
  onStartRun: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  ticker,
  maxRounds,
  capital,
  runStatus,
  onOpenConfig,
  onStartRun,
}) => {
  return (
    <header className="flex items-center justify-between px-6 py-4 bg-zinc-950/90 backdrop-blur-2xl border-b border-zinc-800/80 shrink-0 shadow-2xl relative z-30">
      <div className="flex items-center space-x-3.5">
        <div>
          <h1 className="text-base font-bold tracking-tight text-white flex items-center space-x-3">
            <span className="bg-gradient-to-r from-white via-zinc-200 to-zinc-400 bg-clip-text text-transparent text-lg font-extrabold tracking-wide">AlphaCouncil</span>
          </h1>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="text-xs text-zinc-400 hidden lg:flex items-center space-x-3.5 bg-zinc-900/90 px-4 py-2 rounded-xl border border-zinc-800/80 shadow-inner">
          <div className="flex items-center space-x-1.5">
            <span className="text-zinc-500">Target:</span>
            <span className="font-mono text-white font-bold bg-zinc-800/90 px-2 py-0.5 rounded-lg text-[11px] border border-zinc-700/50">{ticker}</span>
          </div>
          <span className="text-zinc-700 font-light">|</span>
          <div className="flex items-center space-x-1.5">
            <span className="text-zinc-500">Rounds:</span>
            <span className="font-mono text-amber-400 font-bold">{maxRounds}</span>
          </div>
          <span className="text-zinc-700 font-light">|</span>
          <div className="flex items-center space-x-1.5">
            <span className="text-zinc-500">Capital:</span>
            <span className="font-mono text-emerald-400 font-bold">₦{capital.toLocaleString()}</span>
          </div>
        </div>

        <button
          onClick={onOpenConfig}
          disabled={runStatus === 'running'}
          className="px-4 py-2.5 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 rounded-xl text-xs font-semibold transition-all border border-zinc-800 hover:border-zinc-700 shadow-md hover:shadow-lg flex items-center space-x-2 cursor-pointer active:scale-95"
        >
          <svg className="w-4 h-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span>Configure Debate</span>
        </button>

        <button
          onClick={onStartRun}
          disabled={runStatus === 'running'}
          className={`px-4.5 py-2.5 rounded-xl text-xs font-semibold transition-all shadow-lg flex items-center space-x-2 active:scale-95 ${
            runStatus === 'running'
              ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed border border-zinc-700/50'
              : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/25 border border-emerald-500/40 cursor-pointer hover:shadow-emerald-500/40'
          }`}
        >
          {runStatus === 'running' ? (
            <>
              <div className="w-4 h-4 border-2 border-zinc-500 border-t-white rounded-full animate-spin" />
              <span>Celery Task Running...</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Start Analysis & Debate</span>
            </>
          )}
        </button>
      </div>
    </header>
  );
};

'use client';

import React from 'react';

interface ConfigModalProps {
  isOpen: boolean;
  ticker: string;
  userThesis: string;
  capital: number;
  riskTolerance: string;
  maxRounds: number;
  setTicker: (val: string) => void;
  setUserThesis: (val: string) => void;
  setCapital: (val: number) => void;
  setRiskTolerance: (val: string) => void;
  setMaxRounds: (val: number) => void;
  onClose: () => void;
  onStartRun: () => void;
}

export const ConfigModal: React.FC<ConfigModalProps> = ({
  isOpen,
  ticker,
  userThesis,
  capital,
  riskTolerance,
  maxRounds,
  setTicker,
  setUserThesis,
  setCapital,
  setRiskTolerance,
  setMaxRounds,
  onClose,
  onStartRun,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-zinc-950 border border-zinc-800 rounded-2xl p-6 w-[500px] shadow-2xl space-y-5">
        <div className="flex items-center justify-between border-b border-zinc-800/80 pb-4">
          <div className="flex items-center space-x-2.5">
            <div className="w-2.5 h-2.5 rounded-full bg-blue-500 shadow-md shadow-blue-500" />
            <h2 className="text-sm font-bold text-white tracking-wider uppercase">Configure /api/v1/analysis/debate</h2>
          </div>
          <button onClick={onClose} className="text-zinc-400 hover:text-white text-sm font-mono w-7 h-7 rounded-lg bg-zinc-900 flex items-center justify-center border border-zinc-800 hover:bg-zinc-800 transition-colors cursor-pointer">
            ✕
          </button>
        </div>

        <div className="space-y-4 text-xs">
          <div>
            <label className="block text-zinc-400 font-semibold mb-1.5 uppercase tracking-wider text-[11px]">Stock Ticker Symbol</label>
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-3.5 py-2.5 text-white font-mono uppercase focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all shadow-inner"
              placeholder="e.g. DANGCEM, GTCO, ZENITHBANK"
            />
          </div>

          <div>
            <label className="block text-zinc-400 font-semibold mb-1.5 uppercase tracking-wider text-[11px]">Investment Thesis / Prompt (Optional)</label>
            <textarea
              value={userThesis}
              onChange={(e) => setUserThesis(e.target.value)}
              rows={3}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-3.5 py-2.5 text-white focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all shadow-inner resize-none"
              placeholder="e.g. Robust cement market dominance and expansion justify a strong buy..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-zinc-400 font-semibold mb-1.5 uppercase tracking-wider text-[11px]">Capital to Deploy (NGN)</label>
              <input
                type="number"
                value={capital}
                onChange={(e) => setCapital(Number(e.target.value))}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-3.5 py-2.5 text-white font-mono focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all shadow-inner"
              />
            </div>

            <div>
              <label className="block text-zinc-400 font-semibold mb-1.5 uppercase tracking-wider text-[11px]">Risk Tolerance</label>
              <select
                value={riskTolerance}
                onChange={(e) => setRiskTolerance(e.target.value)}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-3.5 py-2.5 text-white focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all shadow-inner cursor-pointer"
              >
                <option value="Conservative">Conservative</option>
                <option value="Moderate">Moderate</option>
                <option value="Aggressive">Aggressive</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-zinc-400 font-semibold mb-1.5 uppercase tracking-wider text-[11px]">Max Debate Rounds</label>
            <select
              value={maxRounds}
              onChange={(e) => setMaxRounds(Number(e.target.value))}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-3.5 py-2.5 text-white focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all shadow-inner cursor-pointer"
            >
              <option value={1}>1 Round (Fast)</option>
              <option value={2}>2 Rounds</option>
              <option value={3}>3 Rounds (Standard)</option>
              <option value={5}>5 Rounds (Deep Debate)</option>
            </select>
          </div>
        </div>

        <div className="flex justify-end space-x-3 pt-3 border-t border-zinc-800/80">
          <button
            onClick={onClose}
            className="px-4 py-2.5 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 rounded-xl text-xs font-semibold border border-zinc-800 transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            onClick={onStartRun}
            className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-blue-600/30 border border-blue-500/30 transition-all cursor-pointer"
          >
            Dispatch Celery Task
          </button>
        </div>
      </div>
    </div>
  );
};

'use client';

import React from 'react';

interface SidebarProps {
  activeTab: 'timeline' | 'inspector';
  events: any[];
  currentState: any;
  selectedEvent: any;
  setActiveTab: (tab: 'timeline' | 'inspector') => void;
  setSelectedEvent: (event: any) => void;
  timelineEndRef: React.RefObject<HTMLDivElement | null>;
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
  sidebarWidth: number;
  setSidebarWidth: (width: number) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  events,
  currentState,
  selectedEvent,
  setActiveTab,
  setSelectedEvent,
  timelineEndRef,
  isCollapsed,
  setIsCollapsed,
  sidebarWidth,
  setSidebarWidth,
}) => {
  if (isCollapsed) {
    return (
      <div className="w-16 bg-zinc-950/90 backdrop-blur-xl border-l border-zinc-800/80 flex flex-col items-center py-4 shrink-0 shadow-2xl transition-all duration-300 z-20">
        <button
          onClick={() => setIsCollapsed(false)}
          className="w-10 h-10 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white border border-zinc-800 flex items-center justify-center transition-all shadow-md cursor-pointer mb-6 group relative"
          title="Expand Sidebar"
        >
          <svg className="w-5 h-5 transition-transform group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        </button>

        <div className="flex flex-col items-center space-y-4 my-auto">
          <button
            onClick={() => { setIsCollapsed(false); setActiveTab('timeline'); }}
            className="w-10 h-10 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-blue-400 border border-zinc-800 flex flex-col items-center justify-center transition-all shadow-sm cursor-pointer relative"
            title={`Timeline (${events.length})`}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="absolute -top-1 -right-1 px-1.5 py-0.2 rounded-full bg-blue-600 text-[9px] font-mono text-white font-bold">
              {events.length}
            </span>
          </button>

          <button
            onClick={() => { setIsCollapsed(false); setActiveTab('inspector'); }}
            className="w-10 h-10 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-emerald-400 border border-zinc-800 flex items-center justify-center transition-all shadow-sm cursor-pointer"
            title="State Inspector"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </button>
        </div>
      </div>
    );
  }

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    const startX = e.clientX;
    const startWidth = sidebarWidth;

    const onMouseMove = (moveEvent: MouseEvent) => {
      const delta = startX - moveEvent.clientX;
      const newWidth = Math.max(300, Math.min(850, startWidth + delta));
      setSidebarWidth(newWidth);
    };

    const onMouseUp = () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      document.body.style.cursor = 'default';
    };

    document.body.style.cursor = 'col-resize';
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  return (
    <div
      style={{ width: `${sidebarWidth}px` }}
      className="bg-zinc-950/90 backdrop-blur-xl border-l border-zinc-800/80 flex flex-col shrink-0 shadow-2xl transition-all duration-75 relative z-20 select-none"
    >
      {/* Draggable resize handle on left edge */}
      <div
        onMouseDown={handleMouseDown}
        className="absolute left-0 top-0 bottom-0 w-2 cursor-col-resize hover:bg-blue-500/80 transition-colors z-30 group flex items-center justify-center"
        title="Drag to resize sidebar"
      >
        <div className="w-0.5 h-8 bg-zinc-700 rounded-full group-hover:bg-white transition-colors" />
      </div>

      <div className="flex items-center justify-between border-b border-zinc-800/80 bg-zinc-900/50 p-1.5 pl-3">
        <div className="flex flex-1 gap-1.5">
          <button
            onClick={() => setActiveTab('timeline')}
            className={`flex-1 py-2.5 rounded-xl text-xs font-semibold tracking-wider uppercase transition-all flex items-center justify-center space-x-2 cursor-pointer ${
              activeTab === 'timeline'
                ? 'bg-gradient-to-r from-blue-600/20 to-indigo-600/20 text-blue-400 border border-blue-500/30 shadow-sm'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50 border border-transparent'
            }`}
          >
            <span>Event Timeline</span>
            <span className="px-1.5 py-0.2 rounded-full bg-zinc-800 text-[10px] font-mono text-zinc-300">
              {events.length}
            </span>
          </button>
          <button
            onClick={() => setActiveTab('inspector')}
            className={`flex-1 py-2.5 rounded-xl text-xs font-semibold tracking-wider uppercase transition-all flex items-center justify-center space-x-2 cursor-pointer ${
              activeTab === 'inspector'
                ? 'bg-gradient-to-r from-blue-600/20 to-indigo-600/20 text-blue-400 border border-blue-500/30 shadow-sm'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50 border border-transparent'
            }`}
          >
            <span>State Inspector</span>
          </button>
        </div>

        <button
          onClick={() => setIsCollapsed(true)}
          className="ml-2 w-9 h-9 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white border border-zinc-800 flex items-center justify-center transition-all shadow-sm cursor-pointer shrink-0"
          title="Collapse Sidebar"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
        {activeTab === 'timeline' ? (
          events.length === 0 ? (
            <div className="text-center text-zinc-500 py-16 px-4 text-xs bg-zinc-900/40 rounded-2xl border border-zinc-800/60">
              <svg className="w-8 h-8 mx-auto mb-3 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              No events recorded yet. Click &quot;Configure Debate&quot; or start the analysis above to watch agents execute in real-time.
            </div>
          ) : (
            events.map((ev, idx) => (
              <div
                key={idx}
                onClick={() => setSelectedEvent(ev)}
                className={`p-3.5 rounded-xl border text-xs cursor-pointer transition-all ${
                  selectedEvent === ev
                    ? 'bg-blue-950/50 border-blue-500/60 shadow-lg shadow-blue-950/50'
                    : 'bg-zinc-900/60 border-zinc-800 hover:border-zinc-700 hover:bg-zinc-900'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-mono text-zinc-400 font-semibold bg-zinc-800/80 px-2 py-0.5 rounded text-[11px]">#{ev.seq}</span>
                  <span className="text-[10px] text-zinc-500 font-mono">
                    {new Date(ev.timestamp).toLocaleTimeString()}
                  </span>
                </div>

                <div className="font-semibold text-zinc-200 capitalize flex items-center space-x-2">
                  <span
                    className={`w-2 h-2 rounded-full shadow-sm ${
                      ev.event.includes('start')
                        ? 'bg-blue-400 shadow-blue-400'
                        : ev.event.includes('end') || ev.event.includes('complete')
                        ? 'bg-emerald-400 shadow-emerald-400'
                        : ev.event.includes('error')
                        ? 'bg-red-400 shadow-red-400'
                        : 'bg-amber-400 shadow-amber-400'
                    }`}
                  />
                  <span>{ev.event.replace('_', ' ')}</span>
                  {ev.node_name && <span className="text-zinc-400 font-normal">({ev.node_name})</span>}
                </div>

                {ev.message && (
                  <div className="mt-1.5 text-zinc-300 text-[11px] font-mono truncate bg-zinc-950/50 p-1.5 rounded border border-zinc-800/50">
                    {ev.message}
                  </div>
                )}

                {ev.error && (
                  <div className="mt-1.5 text-red-300 font-mono text-[11px] truncate bg-red-950/50 p-1.5 rounded border border-red-500/30">
                    Error: {ev.error}
                  </div>
                )}
              </div>
            ))
          )
        ) : (
          <div className="space-y-4">
            <div className="bg-zinc-900/80 p-4 rounded-2xl border border-zinc-800 shadow-lg">
              <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-2.5 flex items-center justify-between">
                <span>Celery Task Result & State</span>
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              </h3>
              <pre className="text-[11px] font-mono text-emerald-400 whitespace-pre-wrap overflow-x-auto bg-zinc-950 p-3 rounded-xl border border-zinc-800/80 custom-scrollbar">
                {JSON.stringify(currentState, null, 2)}
              </pre>
            </div>

            {selectedEvent && (
              <div className="bg-zinc-900/80 p-4 rounded-2xl border border-zinc-800 shadow-lg">
                <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-2.5 flex items-center justify-between">
                  <span>Selected Event Details</span>
                  <span className="font-mono text-blue-400">#{selectedEvent.seq}</span>
                </h3>
                <pre className="text-[11px] font-mono text-blue-300 whitespace-pre-wrap overflow-x-auto bg-zinc-950 p-3 rounded-xl border border-zinc-800/80 custom-scrollbar">
                  {JSON.stringify(selectedEvent, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
        <div ref={timelineEndRef} />
      </div>
    </div>
  );
};

'use client';

import { useEffect, useRef, useState } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useDebateStore } from '@/store/useDebateStore';
import { AgentNode } from '@/components/AgentNode';
import { Header } from '@/components/Header';
import { StatusBanner } from '@/components/StatusBanner';
import { ConfigModal } from '@/components/ConfigModal';
import { Sidebar } from '@/components/Sidebar';
import { TaskProgressToast } from '@/components/TaskProgressToast';

const nodeTypes = { agentNode: AgentNode };

const INITIAL_NODES = [
  {
    id: 'supervisor',
    type: 'agentNode',
    position: { x: 350, y: 50 },
    data: { label: 'Supervisor Coordinator', role: 'Supervisor', status: 'idle', visitCount: 0, activeTool: null, error: null },
  },
  {
    id: 'bull_analyst',
    type: 'agentNode',
    position: { x: 100, y: 240 },
    data: { label: 'Bullish Investment Thesis & Valuation', role: 'Bull Analyst', status: 'idle', visitCount: 0, activeTool: null, error: null },
  },
  {
    id: 'bear_analyst',
    type: 'agentNode',
    position: { x: 600, y: 240 },
    data: { label: 'Risk Stress-Test & Counter-Thesis', role: 'Bear Analyst', status: 'idle', visitCount: 0, activeTool: null, error: null },
  },
  {
    id: 'arbitrator',
    type: 'agentNode',
    position: { x: 350, y: 430 },
    data: { label: 'CIO Arbitrator & Final Verdict', role: 'Arbitrator', status: 'idle', visitCount: 0, activeTool: null, error: null },
  },
];

const INITIAL_EDGES = [
  {
    id: 'sup-to-bull',
    source: 'supervisor',
    target: 'bull_analyst',
    animated: false,
    style: { stroke: '#3f3f46', strokeWidth: 2 },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#3f3f46' },
  },
  {
    id: 'sup-to-bear',
    source: 'supervisor',
    target: 'bear_analyst',
    animated: false,
    style: { stroke: '#3f3f46', strokeWidth: 2 },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#3f3f46' },
  },
  {
    id: 'bull-to-sup',
    source: 'bull_analyst',
    target: 'supervisor',
    animated: false,
    style: { stroke: '#3f3f46', strokeWidth: 2 },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#3f3f46' },
  },
  {
    id: 'bear-to-sup',
    source: 'bear_analyst',
    target: 'supervisor',
    animated: false,
    style: { stroke: '#3f3f46', strokeWidth: 2 },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#3f3f46' },
  },
  {
    id: 'sup-to-arb',
    source: 'supervisor',
    target: 'arbitrator',
    animated: false,
    style: { stroke: '#3f3f46', strokeWidth: 2 },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#3f3f46' },
  },
];

const getEdgeId = (source: string, target: string) => {
  if (source === 'supervisor' && target === 'bull_analyst') return 'sup-to-bull';
  if (source === 'supervisor' && target === 'bear_analyst') return 'sup-to-bear';
  if (source === 'bull_analyst' && target === 'supervisor') return 'bull-to-sup';
  if (source === 'bear_analyst' && target === 'supervisor') return 'bear-to-sup';
  if (source === 'supervisor' && target === 'arbitrator') return 'sup-to-arb';
  return null;
};

export default function VisualizationDashboard() {
  const {
    ticker,
    userThesis,
    capital,
    riskTolerance,
    maxRounds,
    showConfigModal,
    taskId,
    runStatus,
    events,
    currentState,
    selectedEvent,
    activeTab,
    setTicker,
    setUserThesis,
    setCapital,
    setRiskTolerance,
    setMaxRounds,
    setShowConfigModal,
    setTaskId,
    setRunStatus,
    addEvent,
    setCurrentState,
    setSelectedEvent,
    setActiveTab,
    resetRun,
  } = useDebateStore();

  const [nodes, setNodes, onNodesChange] = useNodesState(INITIAL_NODES);
  const [edges, setEdges, onEdgesChange] = useEdgesState(INITIAL_EDGES);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(420);

  useEffect(() => {
    if (typeof window !== 'undefined' && window.innerWidth < 1280) {
      setIsSidebarCollapsed(true);
    }
  }, []);

  const eventSourceRef = useRef<EventSource | null>(null);
  const timelineEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    timelineEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  const handleStartRun = async () => {
    setShowConfigModal(false);
    setIsSidebarCollapsed(true); // Auto-close sidebar on run start for immersive graph visualization
    try {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      resetRun();
      setRunStatus('starting');
      setNodes(INITIAL_NODES);

      const res = await fetch('http://localhost:8000/api/v1/analysis/debate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker,
          user_thesis: userThesis || null,
          capital_to_deploy: capital,
          risk_tolerance: riskTolerance.toLowerCase(),
          max_rounds: maxRounds,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Failed to start debate: ${res.statusText}`);
      }

      const data = await res.json();
      setTaskId(data.task_id);
      setRunStatus('running');

      addEvent({
        seq: 1,
        timestamp: new Date().toISOString(),
        event: 'run_start',
        node_name: 'supervisor',
        message: data.message,
      });

      const es = new EventSource(`http://localhost:8000/api/v1/analysis/debate/stream/${data.task_id}`);
      eventSourceRef.current = es;

      es.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          handleStreamEvent(parsed);
        } catch (e) {
          console.error('Failed to parse SSE event:', e);
        }
      };

      ['node_start', 'node_end', 'tool_start', 'tool_end', 'run_complete', 'run_error', 'system_status'].forEach((eventType) => {
        es.addEventListener(eventType, (event: any) => {
          try {
            const parsed = JSON.parse(event.data);
            handleStreamEvent(parsed);
          } catch (e) {
            console.error(`Failed to parse SSE ${eventType} event:`, e);
          }
        });
      });

      es.onerror = (err) => {
        console.error('SSE connection error:', err);
        if (es.readyState === EventSource.CLOSED) {
          setRunStatus('error');
          addEvent({
            seq: events.length + 1,
            timestamp: new Date().toISOString(),
            event: 'run_error',
            error: 'Connection to server lost (backend stopped or offline).',
          });
        }
      };

    } catch (err: any) {
      alert(err.message || 'Failed to start debate task');
      setRunStatus('error');
    }
  };

  const handleStreamEvent = (ev: any) => {
    addEvent({
      seq: ev.seq,
      timestamp: ev.timestamp,
      event: ev.event_type,
      node_name: ev.node_name,
      originating_node: ev.originating_node,
      tool_name: ev.tool_name,
      tool_args: ev.tool_args,
      tool_result: ev.tool_result,
      message: ev.event_type === 'node_start' ? `Node started: ${ev.node_name} (from ${ev.originating_node || 'start'})` :
               ev.event_type === 'node_end' ? `Node completed: ${ev.node_name}` :
               ev.event_type === 'tool_start' ? `Tool called: ${ev.tool_name}` :
               ev.event_type === 'tool_end' ? `Tool finished: ${ev.tool_name}` :
               ev.event_type === 'run_complete' ? `Debate run completed successfully!` :
               ev.event_type === 'run_error' ? `Error: ${ev.data?.error}` : JSON.stringify(ev.data),
      error: ev.data?.error,
    });

    if (ev.event_type === 'node_start') {
      const activeEdgeId = ev.originating_node ? getEdgeId(ev.originating_node, ev.node_name) : null;

      setNodes((nds) =>
        nds.map((n) => {
          const isActive = n.id === ev.node_name;
          return {
            ...n,
            data: {
              ...n.data,
              status: isActive ? 'active' : n.data.status === 'active' ? 'completed' : n.data.status,
              visitCount: isActive ? n.data.visitCount + 1 : n.data.visitCount,
            },
          };
        })
      );

      if (activeEdgeId) {
        setEdges((eds) =>
          eds.map((e) => {
            const isTargetEdge = e.id === activeEdgeId;
            return {
              ...e,
              animated: isTargetEdge,
              style: {
                ...e.style,
                stroke: isTargetEdge ? '#3b82f6' : '#3f3f46',
                strokeWidth: isTargetEdge ? 3 : 2,
              },
            };
          })
        );
      }
    } else if (ev.event_type === 'tool_start') {
      setNodes((nds) =>
        nds.map((n) => ({
          ...n,
          data: {
            ...n.data,
            activeTool: n.id === ev.node_name ? ev.tool_name : n.data.activeTool,
          },
        }))
      );
    } else if (ev.event_type === 'tool_end') {
      setNodes((nds) =>
        nds.map((n) => ({
          ...n,
          data: {
            ...n.data,
            activeTool: n.id === ev.node_name ? null : n.data.activeTool,
          },
        }))
      );
    } else if (ev.event_type === 'run_complete') {
      setRunStatus('completed');
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      fetch(`http://localhost:8000/api/v1/analysis/debate/state/${taskId || ev.run_id}`)
        .then((r) => r.json())
        .then((d) => setCurrentState(d.state || d))
        .catch(() => {});

      setNodes((nds) =>
        nds.map((n) => ({
          ...n,
          data: { ...n.data, status: 'completed', activeTool: null },
        }))
      );
    } else if (ev.event_type === 'run_error') {
      setRunStatus('error');
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      setNodes((nds) =>
        nds.map((n) => ({
          ...n,
          data: { ...n.data, status: n.data.status === 'active' ? 'error' : n.data.status },
        }))
      );
    }
  };

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return (
    <div className="flex flex-col h-screen w-screen bg-[#09090b] text-zinc-100 overflow-hidden font-sans">
      <Header
        ticker={ticker}
        maxRounds={maxRounds}
        capital={capital}
        runStatus={runStatus}
        onOpenConfig={() => setShowConfigModal(true)}
        onStartRun={handleStartRun}
      />

      <ConfigModal
        isOpen={showConfigModal}
        ticker={ticker}
        userThesis={userThesis}
        capital={capital}
        riskTolerance={riskTolerance}
        maxRounds={maxRounds}
        setTicker={setTicker}
        setUserThesis={setUserThesis}
        setCapital={setCapital}
        setRiskTolerance={setRiskTolerance}
        setMaxRounds={setMaxRounds}
        onClose={() => setShowConfigModal(false)}
        onStartRun={handleStartRun}
      />

      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 relative bg-[#09090b]">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            fitView
            className="w-full h-full"
          >
            <Background color="#27272a" gap={24} size={1} />
            <Controls className="bg-[#18181b] border-zinc-800 rounded-lg fill-zinc-200" />
            <MiniMap className="bg-[#121215] border-zinc-800 rounded-lg" zoomable pannable />
          </ReactFlow>

          <StatusBanner
            runStatus={runStatus}
            ticker={ticker}
            maxRounds={maxRounds}
            capital={capital}
            riskTolerance={riskTolerance}
            taskId={taskId}
            events={events}
            currentState={currentState}
            isSidebarCollapsed={isSidebarCollapsed}
            sidebarWidth={sidebarWidth}
          />

          <TaskProgressToast runStatus={runStatus} events={events} />
        </div>

        <Sidebar
          activeTab={activeTab}
          events={events}
          currentState={currentState}
          selectedEvent={selectedEvent}
          setActiveTab={setActiveTab}
          setSelectedEvent={setSelectedEvent}
          timelineEndRef={timelineEndRef}
          isCollapsed={isSidebarCollapsed}
          setIsCollapsed={setIsSidebarCollapsed}
          sidebarWidth={sidebarWidth}
          setSidebarWidth={setSidebarWidth}
        />
      </div>
    </div>
  );
}

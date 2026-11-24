'tsx'
import { create } from 'zustand';

interface DebateState {
  ticker: string;
  userThesis: string;
  capital: number;
  riskTolerance: string;
  maxRounds: number;
  showConfigModal: boolean;
  taskId: string | null;
  runStatus: string;
  events: any[];
  currentState: any;
  selectedEvent: any;
  activeTab: 'timeline' | 'inspector';

  setTicker: (ticker: string) => void;
  setUserThesis: (thesis: string) => void;
  setCapital: (capital: number) => void;
  setRiskTolerance: (risk: string) => void;
  setMaxRounds: (rounds: number) => void;
  setShowConfigModal: (show: boolean) => void;
  setTaskId: (taskId: string | null) => void;
  setRunStatus: (status: string) => void;
  setEvents: (events: any[] | ((prev: any[]) => any[])) => void;
  addEvent: (event: any) => void;
  setCurrentState: (state: any) => void;
  setSelectedEvent: (event: any) => void;
  setActiveTab: (tab: 'timeline' | 'inspector') => void;
  resetRun: () => void;
}

export const useDebateStore = create<DebateState>((set) => ({
  ticker: 'DANGCEM',
  userThesis: '',
  capital: 10000000,
  riskTolerance: 'Moderate',
  maxRounds: 3,
  showConfigModal: false,
  taskId: null,
  runStatus: 'idle',
  events: [],
  currentState: {},
  selectedEvent: null,
  activeTab: 'timeline',

  setTicker: (ticker) => set({ ticker }),
  setUserThesis: (userThesis) => set({ userThesis }),
  setCapital: (capital) => set({ capital }),
  setRiskTolerance: (riskTolerance) => set({ riskTolerance }),
  setMaxRounds: (maxRounds) => set({ maxRounds }),
  setShowConfigModal: (showConfigModal) => set({ showConfigModal }),
  setTaskId: (taskId) => set({ taskId }),
  setRunStatus: (runStatus) => set({ runStatus }),
  setEvents: (events) => set((state) => ({ events: typeof events === 'function' ? events(state.events) : events })),
  addEvent: (event) => set((state) => ({ events: [...state.events, event] })),
  setCurrentState: (currentState) => set({ currentState }),
  setSelectedEvent: (selectedEvent) => set({ selectedEvent }),
  setActiveTab: (activeTab) => set({ activeTab }),
  resetRun: () => set({ events: [], currentState: {}, taskId: null, runStatus: 'idle', selectedEvent: null }),
}));

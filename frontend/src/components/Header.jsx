import React from 'react';
import { 
  ShieldCheck, MessageSquare, BookOpen, Database, 
  Cpu 
} from 'lucide-react';

export default function Header({ activeTab, setActiveTab, health }) {
  const isHealthy = health?.status === 'healthy';

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-14 items-center">
          {/* Logo & Product Brand */}
          <div 
            className="flex items-center space-x-2.5 cursor-pointer select-none"
            onClick={() => setActiveTab('assistant')}
            title="PolicyPilot Home"
          >
            <div className="h-8 w-8 rounded-lg bg-slate-900 flex items-center justify-center text-white">
              <ShieldCheck className="w-4 h-4 text-blue-400" />
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="text-sm font-bold tracking-tight text-slate-900">PolicyPilot</span>
                <span className="text-[10px] font-semibold px-1.5 py-0.2 bg-slate-100 text-slate-600 rounded border border-slate-200">
                  Campus
                </span>
              </div>
            </div>
          </div>

          {/* Center Navigation: Primary Student Tabs */}
          <nav className="flex items-center space-x-1 bg-slate-100/70 p-1 rounded-lg border border-slate-200/80">
            <button
              onClick={() => setActiveTab('assistant')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                activeTab === 'assistant'
                  ? 'bg-white text-slate-900 shadow-xs border border-slate-200/70'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
              }`}
            >
              <MessageSquare className={`w-3.5 h-3.5 ${activeTab === 'assistant' ? 'text-blue-600' : 'text-slate-400'}`} />
              <span>Policy Assistant</span>
            </button>

            <button
              onClick={() => setActiveTab('library')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                activeTab === 'library'
                  ? 'bg-white text-slate-900 shadow-xs border border-slate-200/70'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
              }`}
            >
              <BookOpen className={`w-3.5 h-3.5 ${activeTab === 'library' ? 'text-blue-600' : 'text-slate-400'}`} />
              <span>Policy Library</span>
            </button>
          </nav>

          {/* Right Navigation: Secondary Utilities (Admin & Dev) + Health Status */}
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1 pl-2 border-l border-slate-200">
              <button
                onClick={() => setActiveTab('admin')}
                className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-all ${
                  activeTab === 'admin'
                    ? 'bg-slate-900 text-white font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
                title="Administrative Console (Document Ingestion & Management)"
              >
                <Database className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Admin</span>
                <span className={`text-[9px] font-bold px-1 py-0.2 rounded ${
                  activeTab === 'admin' ? 'bg-slate-800 text-amber-300' : 'bg-slate-100 text-slate-500 border border-slate-200'
                }`}>
                  PROTO
                </span>
              </button>

              <button
                onClick={() => setActiveTab('developer')}
                className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-all ${
                  activeTab === 'developer'
                    ? 'bg-slate-900 text-white font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
                title="Developer Workbench (Retrieval Benchmarks & FastMCP)"
              >
                <Cpu className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Dev Lab</span>
                <span className={`text-[9px] font-bold px-1 py-0.2 rounded ${
                  activeTab === 'developer' ? 'bg-slate-800 text-blue-300' : 'bg-slate-100 text-slate-500 border border-slate-200'
                }`}>
                  DEV
                </span>
              </button>
            </div>

            {/* Subtle Connectivity Dot */}
            <div 
              className="flex items-center space-x-1.5 pl-2 text-[11px] text-slate-500" 
              title={isHealthy ? "Backend API connected and healthy" : "Backend connection error"}
            >
              <div className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-emerald-500' : 'bg-rose-500'}`} />
              <span className="hidden md:inline text-[11px] font-medium text-slate-500">
                {isHealthy ? 'Connected' : 'Offline'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

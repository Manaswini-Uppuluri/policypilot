import React, { useState } from 'react';
import { 
  BarChart3, Wrench, Activity, Cpu, Database, 
  Terminal, Zap, RefreshCw, CheckCircle2, Clock
} from 'lucide-react';
import EvaluationTab from './EvaluationTab';
import McpTab from './McpTab';
import { getHealth } from '../services/api';

export default function DeveloperTab({ health, onRefreshHealth }) {
  const [subTab, setSubTab] = useState('benchmarks');
  const [pingResult, setPingResult] = useState(null);
  const [isPinging, setIsPinging] = useState(false);

  const handlePingTest = async () => {
    setIsPinging(true);
    setPingResult(null);
    const t0 = performance.now();
    try {
      const data = await getHealth();
      const t1 = performance.now();
      const latencyMs = Math.round((t1 - t0) * 10) / 10;
      setPingResult({
        status: 'success',
        latencyMs,
        data,
        timestamp: new Date().toLocaleTimeString()
      });
      if (onRefreshHealth) onRefreshHealth();
    } catch (e) {
      const t1 = performance.now();
      setPingResult({
        status: 'error',
        latencyMs: Math.round((t1 - t0) * 10) / 10,
        error: e.message,
        timestamp: new Date().toLocaleTimeString()
      });
    } finally {
      setIsPinging(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      {/* Sub-Navigation Header */}
      <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-2xs flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-slate-700" />
            <h1 className="text-sm font-bold text-slate-900">Developer & Engineering Workbench</h1>
            <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 border border-slate-200">
              Prototype Diagnostics
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Internal evaluation suite for testing retrieval strategies, FastMCP server actions, and API diagnostics.
          </p>
        </div>

        {/* Tab Buttons */}
        <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-lg border border-slate-200/80 shrink-0">
          {[
            { id: 'benchmarks', label: 'Retrieval Benchmarks', icon: BarChart3 },
            { id: 'mcp', label: 'FastMCP Tools', icon: Wrench },
            { id: 'diagnostics', label: 'System Diagnostics', icon: Activity },
          ].map((item) => {
            const Icon = item.icon;
            const isActive = subTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setSubTab(item.id)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-white text-slate-900 shadow-2xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-slate-900' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab 1: Retrieval Benchmarks */}
      {subTab === 'benchmarks' && (
        <div>
          <EvaluationTab />
        </div>
      )}

      {/* Tab 2: FastMCP Server Tools */}
      {subTab === 'mcp' && (
        <div>
          <McpTab />
        </div>
      )}

      {/* Tab 3: API & System Diagnostics */}
      {subTab === 'diagnostics' && (
        <div className="space-y-4">
          {/* System Status Overview */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs space-y-1.5">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[11px] font-bold uppercase tracking-wider">Service Status</span>
                <Activity className="w-3.5 h-3.5 text-emerald-600" />
              </div>
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${health?.status === 'healthy' ? 'bg-emerald-500' : 'bg-amber-500'}`} />
                <span className="text-base font-bold text-slate-900 capitalize">{health?.status || 'Connecting...'}</span>
              </div>
              <div className="text-[11px] text-slate-400">
                Service: <strong className="text-slate-700">{health?.service || 'PolicyPilot'}</strong> v{health?.version || '1.0.0'}
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs space-y-1.5">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[11px] font-bold uppercase tracking-wider">Database Engine</span>
                <Database className="w-3.5 h-3.5 text-slate-600" />
              </div>
              <div className="text-base font-bold text-slate-900 uppercase">
                {health?.database?.backend || 'SQLite'}
              </div>
              <div className="text-[11px] text-slate-500">
                pgvector extension: <span className="font-semibold text-slate-700">{health?.database?.pgvector_active ? 'Enabled' : 'Disabled (Local dense cosine)'}</span>
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs space-y-1.5">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[11px] font-bold uppercase tracking-wider">Inference & Vector</span>
                <Zap className="w-3.5 h-3.5 text-slate-600" />
              </div>
              <div className="text-base font-bold text-slate-900 capitalize">
                {health?.config?.llm_provider || 'Groq'} (LLM)
              </div>
              <div className="text-[11px] text-slate-500">
                Embedding: <span className="font-semibold text-slate-700">{health?.config?.embedding_provider || 'all-MiniLM-L6-v2 / dense'}</span>
              </div>
            </div>
          </div>

          {/* Interactive Ping Probe */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-2xs space-y-3">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-xs font-bold text-slate-900 flex items-center space-x-1.5 uppercase tracking-wider">
                  <Terminal className="w-3.5 h-3.5 text-slate-600" />
                  <span>Real-Time API Health & Latency Probe</span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Send a live request to <code>/api/health</code> to measure round-trip HTTP response time.
                </p>
              </div>

              <button
                onClick={handlePingTest}
                disabled={isPinging}
                className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 disabled:bg-slate-200 text-white font-medium text-xs transition-colors cursor-pointer"
              >
                {isPinging ? (
                  <span className="flex items-center space-x-1.5">
                    <RefreshCw className="w-3 h-3 animate-spin" />
                    <span>Measuring...</span>
                  </span>
                ) : (
                  <span className="flex items-center space-x-1.5">
                    <Clock className="w-3 h-3" />
                    <span>Send Ping Probe</span>
                  </span>
                )}
              </button>
            </div>

            {pingResult && (
              <div className={`p-3 rounded-lg text-xs space-y-2 border ${
                pingResult.status === 'success' ? 'bg-slate-50 border-slate-200 text-slate-900' : 'bg-rose-50 border-rose-200 text-rose-900'
              }`}>
                <div className="flex items-center justify-between font-semibold">
                  <span className="flex items-center space-x-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Response: HTTP 200 OK</span>
                  </span>
                  <span className="font-mono bg-white px-2 py-0.5 rounded border border-slate-200 text-slate-800 font-bold text-[11px]">
                    Round-Trip: {pingResult.latencyMs} ms
                  </span>
                </div>
                <pre className="text-[11px] text-slate-600 font-mono bg-white p-2 rounded border border-slate-200 overflow-x-auto">
                  {JSON.stringify(pingResult.data, null, 2)}
                </pre>
              </div>
            )}
          </div>

          {/* Pipeline Configuration Parameters */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-2xs">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2.5">
              RAG Architectural Parameters
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <tbody className="divide-y divide-slate-100">
                  <tr>
                    <td className="py-2 text-slate-500 font-medium w-1/3">Inference Engine</td>
                    <td className="py-2 font-mono text-slate-800">Groq API (openai/gpt-oss-120b with 20b fallback)</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-slate-500 font-medium">Text Chunking</td>
                    <td className="py-2 font-mono text-slate-800">Sliding Window (Size: {health?.config?.chunk_size || 600} chars, Overlap: {health?.config?.chunk_overlap || 100} chars)</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-slate-500 font-medium">Embedding Vector Dimension</td>
                    <td className="py-2 font-mono text-slate-800">384 Dimensions (Unit-Normalized)</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-slate-500 font-medium">Hybrid Rank Fusion Algorithm</td>
                    <td className="py-2 font-mono text-slate-800">Reciprocal Rank Fusion (RRF, k = {health?.config?.rrf_k || 60})</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-slate-500 font-medium">HyDE Implementation</td>
                    <td className="py-2 font-mono text-slate-800">Passage generation reused across semantic and hybrid pipelines</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

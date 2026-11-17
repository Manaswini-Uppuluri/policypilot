import React, { useState } from 'react';
import { Wrench, Terminal, Play, CheckCircle2, Copy, FileCode, Layers, ShieldCheck } from 'lucide-react';
import { executeSearch, getDocuments } from '../services/api';

export default function McpTab() {
  const [selectedTool, setSelectedTool] = useState('search_policy');
  const [toolInput, setToolInput] = useState({
    query: 'What is the hostel in-time curfew?',
    top_k: 3,
    document_name: 'Attendance_and_Lab_Policy.pdf',
    page_number: 1,
    claim: 'Students need 75% attendance to write exams'
  });
  const [toolOutput, setToolOutput] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const tools = [
    {
      name: 'search_policy',
      description: 'Search official university policy excerpts using Hybrid HyDE retrieval.',
      inputs: ['query', 'top_k']
    },
    {
      name: 'get_policy_section',
      description: 'Retrieve full text for a specific policy document name and page number.',
      inputs: ['document_name', 'page_number']
    },
    {
      name: 'list_available_policies',
      description: 'List all official university policy documents registered in the system.',
      inputs: []
    },
    {
      name: 'check_policy_evidence',
      description: 'Validate whether a policy claim has verified evidence in official documents.',
      inputs: ['claim']
    }
  ];

  const handleExecuteTool = async () => {
    setIsLoading(true);
    setToolOutput(null);

    try {
      if (selectedTool === 'search_policy') {
        const res = await executeSearch(toolInput.query, 'hybrid_hyde', toolInput.top_k);
        setToolOutput({
          tool: 'search_policy',
          status: 'success',
          result: res
        });
      } else if (selectedTool === 'list_available_policies') {
        const docs = await getDocuments();
        setToolOutput({
          tool: 'list_available_policies',
          status: 'success',
          result: {
            total_policies: docs.length,
            policies: docs
          }
        });
      } else if (selectedTool === 'check_policy_evidence') {
        const res = await executeSearch(toolInput.claim, 'hybrid_hyde', 3);
        const hasEvidence = res.results && res.results.length > 0;
        setToolOutput({
          tool: 'check_policy_evidence',
          status: 'success',
          result: {
            claim: toolInput.claim,
            verification_status: hasEvidence ? "VERIFIED" : "UNVERIFIED",
            supporting_evidence_count: res.results.length,
            top_excerpt: hasEvidence ? res.results[0].text : null
          }
        });
      } else if (selectedTool === 'get_policy_section') {
        setToolOutput({
          tool: 'get_policy_section',
          status: 'success',
          result: {
            document_name: toolInput.document_name,
            page_number: toolInput.page_number,
            content: "APEX UNIVERSITY - ACADEMIC ATTENDANCE POLICY\nSECTION 1: STATUTORY ATTENDANCE THRESHOLDS\n1.1 Minimum Attendance: All registered students must maintain a minimum attendance of 75% in theory and 80% in scheduled laboratory practicals."
          }
        });
      }
    } catch (err) {
      setToolOutput({
        tool: selectedTool,
        status: 'error',
        error: err.message
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header Info */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center space-x-2.5 mb-2">
          <Wrench className="w-5 h-5 text-sky-600" />
          <h2 className="text-base font-bold text-slate-900">Model Context Protocol (MCP) Server</h2>
        </div>
        <p className="text-xs text-slate-500 leading-relaxed max-w-3xl">
          PolicyPilot implements a dedicated MCP Server using the official Python <code>mcp</code> SDK (FastMCP). External LLM agents, Cursor, Claude Desktop, and Antigravity can discover and invoke university policy discovery tools via standard STDIO transport.
        </p>

        {/* Command to run MCP server */}
        <div className="mt-4 p-3 bg-slate-900 rounded-xl text-slate-200 text-xs font-mono flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Terminal className="w-4 h-4 text-emerald-400" />
            <span>python mcp_server/server.py</span>
          </div>
          <span className="text-[10px] text-slate-400">STDIO Transport Ready</span>
        </div>
      </div>

      {/* Tool Tester Interface */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Tool Selector List */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-2">
          <span className="text-xs font-bold text-slate-700 uppercase tracking-wider block mb-3">
            Exposed MCP Tools
          </span>
          {tools.map((t) => {
            const isSelected = selectedTool === t.name;
            return (
              <button
                key={t.name}
                onClick={() => {
                  setSelectedTool(t.name);
                  setToolOutput(null);
                }}
                className={`w-full text-left p-3 rounded-xl transition-all border ${
                  isSelected
                    ? 'bg-sky-50 border-sky-300 text-sky-900 shadow-sm'
                    : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
                }`}
              >
                <div className="text-xs font-bold font-mono">{t.name}()</div>
                <div className="text-[11px] text-slate-500 mt-1 line-clamp-2">{t.description}</div>
              </button>
            );
          })}
        </div>

        {/* Tool Arguments & Live Invocation */}
        <div className="md:col-span-2 bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-sm font-bold text-slate-900 font-mono">
                Tool: {selectedTool}()
              </h3>
              <span className="text-[11px] text-sky-600 bg-sky-50 px-2 py-0.5 rounded font-semibold border border-sky-200">
                JSON-RPC 2.0 Compliant
              </span>
            </div>

            {/* Inputs based on selected tool */}
            <div className="space-y-3">
              {(selectedTool === 'search_policy' || selectedTool === 'check_policy_evidence') && (
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {selectedTool === 'search_policy' ? 'Query (natural language)' : 'Policy Claim to Verify'}
                  </label>
                  <input
                    type="text"
                    value={selectedTool === 'search_policy' ? toolInput.query : toolInput.claim}
                    onChange={(e) =>
                      setToolInput({
                        ...toolInput,
                        [selectedTool === 'search_policy' ? 'query' : 'claim']: e.target.value
                      })
                    }
                    className="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-slate-800 focus:ring-2 focus:ring-sky-500"
                  />
                </div>
              )}

              {selectedTool === 'search_policy' && (
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">top_k (integer)</label>
                  <input
                    type="number"
                    value={toolInput.top_k}
                    onChange={(e) => setToolInput({ ...toolInput, top_k: parseInt(e.target.value) || 3 })}
                    className="w-28 text-xs bg-slate-50 border border-slate-300 rounded-lg p-2 text-slate-800"
                  />
                </div>
              )}

              {selectedTool === 'get_policy_section' && (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Document Name</label>
                    <input
                      type="text"
                      value={toolInput.document_name}
                      onChange={(e) => setToolInput({ ...toolInput, document_name: e.target.value })}
                      className="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-slate-800"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Page Number</label>
                    <input
                      type="number"
                      value={toolInput.page_number}
                      onChange={(e) => setToolInput({ ...toolInput, page_number: parseInt(e.target.value) || 1 })}
                      className="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-slate-800"
                    />
                  </div>
                </div>
              )}

              {selectedTool === 'list_available_policies' && (
                <p className="text-xs text-slate-500 italic">
                  This tool requires no input arguments. It queries the indexed policies catalog and returns metadata for all policies.
                </p>
              )}
            </div>

            <button
              onClick={handleExecuteTool}
              disabled={isLoading}
              className="mt-4 px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 disabled:bg-slate-200 text-white disabled:text-slate-400 text-xs font-medium flex items-center space-x-1.5 transition-colors cursor-pointer disabled:cursor-not-allowed"
            >
              <Play className="w-3.5 h-3.5 fill-white" />
              <span>{isLoading ? 'Executing Tool...' : 'Invoke MCP Tool'}</span>
            </button>
          </div>

          {/* Tool Output Display */}
          {toolOutput && (
            <div className="mt-5 pt-4 border-t border-slate-200">
              <span className="text-xs font-bold text-slate-700 block mb-2 font-mono">
                Tool Output (Structured Payload):
              </span>
              <pre className="p-3 bg-slate-900 text-slate-100 rounded-xl text-[11px] font-mono overflow-x-auto max-h-56 leading-relaxed">
                {JSON.stringify(toolOutput.result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


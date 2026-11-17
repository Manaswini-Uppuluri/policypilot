import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, BookOpen, AlertCircle, CheckCircle2, AlertTriangle, 
  ChevronDown, ChevronUp, FileText, RefreshCw, ArrowRight, ShieldCheck, CornerDownLeft
} from 'lucide-react';
import { sendChatMessage } from '../services/api';
import MarkdownRenderer from './MarkdownRenderer';

const SUGGESTED_QUERIES = [
  "What are the official consequences for ragging at MSRIT?",
  "What is the minimum attendance required to appear for exams?",
  "What happens if a student causes damage to college property?",
  "Can a student bring a mobile phone or study material during exams?",
  "What are the hostel in-time curfew rules?"
];

export default function ChatTab({ onDocumentView, initialQuery = '' }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: "PolicyPilot searches indexed official university policies and relevant statutory provisions to provide citation-grounded answers to campus inquiries. Ask a question below to consult verified regulations.",
      verification_status: 'VERIFIED',
      citations: [],
      evidence_trace: null,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [conversationId, setConversationId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [expandedTraceId, setExpandedTraceId] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (initialQuery) {
      setInput(initialQuery);
    }
  }, [initialQuery]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (queryText = input) => {
    const textToSend = queryText.trim();
    if (!textToSend || isLoading) return;

    const userMsgId = Date.now().toString();
    const newMessages = [
      ...messages,
      {
        id: userMsgId,
        role: 'user',
        content: textToSend,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ];

    setMessages(newMessages);
    setInput('');
    setIsLoading(true);

    try {
      const resp = await sendChatMessage(textToSend, conversationId, 'hybrid_hyde', 4);
      if (resp.conversation_id) {
        setConversationId(resp.conversation_id);
      }
      setMessages([
        ...newMessages,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: resp.answer,
          verification_status: resp.verification_status,
          citations: resp.citations || [],
          evidence_trace: resp.evidence_trace,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } catch (err) {
      setMessages([
        ...newMessages,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: "Encountered an issue communicating with the policy discovery backend. Please ensure the backend server is active.",
          verification_status: 'UNVERIFIED',
          citations: [],
          evidence_trace: null,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'VERIFIED':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            <span>VERIFIED EVIDENCE</span>
          </span>
        );
      case 'CONFLICTING':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200">
            <AlertTriangle className="w-3 h-3 text-amber-600" />
            <span>CONFLICTING POLICIES</span>
          </span>
        );
      case 'OUT_OF_SCOPE':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-200">
            <AlertCircle className="w-3 h-3 text-slate-500" />
            <span>OUT OF SCOPE</span>
          </span>
        );
      case 'UNVERIFIED':
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-200">
            <AlertCircle className="w-3 h-3 text-slate-500" />
            <span>UNVERIFIED / INSUFFICIENT INFO</span>
          </span>
        );
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-7.5rem)] max-w-4xl mx-auto">
      {/* Suggested Inquiries Toolbar */}
      <div className="bg-white border border-slate-200 rounded-xl px-3 py-2 mb-3 shadow-2xs flex items-center space-x-2">
        <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider shrink-0">
          Suggested:
        </span>
        <div className="flex items-center space-x-1.5 overflow-x-auto scrollbar-none py-0.5">
          {SUGGESTED_QUERIES.map((sq, i) => (
            <button
              key={i}
              onClick={() => handleSend(sq)}
              className="text-xs text-slate-600 bg-slate-50 hover:bg-slate-100 hover:text-slate-900 border border-slate-200/90 px-2.5 py-1 rounded-md whitespace-nowrap transition-colors shrink-0"
            >
              {sq.length > 40 ? sq.substring(0, 40) + '...' : sq}
            </button>
          ))}
        </div>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            {m.role === 'user' ? (
              // User Question Bubble
              <div className="max-w-2xl bg-slate-900 text-white rounded-xl rounded-tr-xs px-4 py-3 shadow-2xs">
                <p className="text-xs sm:text-sm font-medium leading-relaxed">{m.content}</p>
                <div className="text-[10px] text-slate-400 mt-1 text-right">{m.timestamp}</div>
              </div>
            ) : (
              // Assistant Response Card
              <div className="w-full max-w-3xl bg-white border border-slate-200 rounded-xl rounded-tl-xs p-4 sm:p-5 shadow-2xs">
                {/* Header: Name, Verification Badge, Timestamp */}
                <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 mb-3 border-b border-slate-100">
                  <div className="flex items-center space-x-2.5">
                    <div className="w-6 h-6 rounded bg-slate-900 flex items-center justify-center text-white text-[11px] font-bold">
                      P
                    </div>
                    <span className="text-xs font-bold text-slate-900 tracking-tight">PolicyPilot Assistant</span>
                    {getStatusBadge(m.verification_status)}
                  </div>
                  <span className="text-[11px] text-slate-400">{m.timestamp}</span>
                </div>

                {/* Markdown Rendered Content */}
                <MarkdownRenderer content={m.content} />

                {/* Citations List */}
                {m.citations && m.citations.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-slate-100">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider flex items-center space-x-1.5">
                        <BookOpen className="w-3.5 h-3.5 text-blue-600" />
                        <span>Referenced Policy Sources:</span>
                      </span>
                      <button
                        onClick={onDocumentView}
                        className="text-[11px] text-blue-600 hover:text-blue-800 font-medium flex items-center space-x-1"
                      >
                        <span>View Library</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {m.citations.map((c, idx) => (
                        <div
                          key={idx}
                          className="bg-slate-50 border border-slate-200 rounded-md px-2.5 py-1 text-xs text-slate-800 flex items-center space-x-1.5"
                        >
                          <FileText className="w-3 h-3 text-slate-400" />
                          <span className="font-semibold text-slate-900">{c.document_name}</span>
                          <span className="text-slate-400">•</span>
                          <span className="text-slate-600 text-[11px]">Page {c.page_number}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Evidence Trace Drawer */}
                {m.evidence_trace && m.evidence_trace.retrieved_chunks && m.evidence_trace.retrieved_chunks.length > 0 && (
                  <div className="mt-3 pt-2">
                    <button
                      onClick={() => setExpandedTraceId(expandedTraceId === m.id ? null : m.id)}
                      className="flex items-center space-x-1.5 text-xs text-slate-500 hover:text-slate-900 font-medium transition-colors"
                    >
                      <BookOpen className="w-3.5 h-3.5 text-slate-400" />
                      <span>
                        {expandedTraceId === m.id
                          ? 'Collapse Evidence Trace'
                          : `View Evidence Trace (${m.evidence_trace.retrieved_chunks.length} excerpts)`}
                      </span>
                      {expandedTraceId === m.id ? (
                        <ChevronUp className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5" />
                      )}
                    </button>

                    {expandedTraceId === m.id && (
                      <div className="mt-2.5 bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs space-y-2.5">
                        <div>
                          <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block">
                            Interpreted Campus Policy Topic:
                          </span>
                          <p className="text-slate-600 mt-0.5 text-xs">{m.evidence_trace.interpreted_intent}</p>
                        </div>

                        <div>
                          <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block mb-1.5">
                            Official Policy Excerpts Consulted:
                          </span>
                          <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
                            {m.evidence_trace.retrieved_chunks.map((chk, i) => (
                              <div key={i} className="bg-white border border-slate-200 rounded p-2.5 text-slate-700">
                                <div className="flex justify-between items-center text-[10px] text-slate-500 font-semibold mb-1 pb-1 border-b border-slate-100">
                                  <span className="text-slate-800 font-bold">{chk.document_name}</span>
                                  <span>
                                    Page {chk.page_number} • {chk.section_heading || 'General'}
                                  </span>
                                </div>
                                <p className="text-slate-600 leading-relaxed text-[11px]">{chk.text}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center space-x-2 text-slate-600 bg-white border border-slate-200 rounded-lg px-3 py-2 w-fit text-xs">
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-slate-500" />
            <span>Consulting official regulations and verifying clauses...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="mt-3">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="relative flex items-center bg-white border border-slate-300 focus-within:border-slate-800 focus-within:ring-1 focus-within:ring-slate-800 rounded-xl transition-all shadow-2xs"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about campus policies, attendance, exams, hostels or conduct..."
            className="w-full pl-4 pr-12 py-3 text-xs sm:text-sm bg-transparent border-none text-slate-900 placeholder-slate-400 focus:outline-none"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="absolute right-2 p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 disabled:bg-slate-100 text-white disabled:text-slate-400 transition-colors cursor-pointer disabled:cursor-not-allowed"
            title="Send query"
          >
            <CornerDownLeft className="w-4 h-4" />
          </button>
        </form>
        <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1.5 px-1">
          <span>Responses cite indexed university policy documents.</span>
          <button
            onClick={onDocumentView}
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            Open Policy Library →
          </button>
        </div>
      </div>
    </div>
  );
}

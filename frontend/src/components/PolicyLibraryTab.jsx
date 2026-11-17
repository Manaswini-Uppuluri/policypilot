import React, { useState } from 'react';
import { 
  BookOpen, Search, FileText, ArrowRight, Calendar, Layers, Tag
} from 'lucide-react';

export default function PolicyLibraryTab({ documents, onSelectPolicyForChat }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');

  const categories = ['All', 'Disciplinary & Conduct', 'Academic & Attendance', 'Examinations & Ethics', 'Student Affairs & Residence', 'General Administration'];

  const filteredDocs = (documents || []).filter((doc) => {
    const matchesSearch = doc.document_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (doc.category && doc.category.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesCat = selectedCategory === 'All' || doc.category === selectedCategory;
    return matchesSearch && matchesCat;
  });

  const getPolicySummary = (doc) => {
    const name = doc.document_name.toLowerCase();
    if (name.includes('conduct') || name.includes('msrit')) {
      return "Official Code of Conduct for students, establishing institutional guidelines on ragging, student demeanor, classroom decorum, campus ethics, and disciplinary actions.";
    }
    if (name.includes('attendance')) {
      return "Academic attendance regulations detailing minimum semester thresholds, condonation criteria, laboratory practicals requirements, and internal assessment eligibility.";
    }
    if (name.includes('hostel') || name.includes('residence')) {
      return "Hostel and residential guidelines covering curfew hours, room allotment, guest visitation policies, and premises safety standards.";
    }
    return `Official institutional regulations governing student affairs and campus policies under category: ${doc.category || 'General'}.`;
  };

  const totalPages = (documents || []).reduce((acc, d) => acc + (d.total_pages || 0), 0);
  const totalChunks = (documents || []).reduce((acc, d) => acc + (d.total_chunks || 0), 0);

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      {/* Page Header (Clean, professional, no giant gradients) */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-2xs">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
              <BookOpen className="w-3.5 h-3.5 text-blue-600" />
              <span>Official Repository</span>
            </div>
            <h1 className="text-xl font-bold tracking-tight text-slate-900">
              Policy Reference Library
            </h1>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
              Browse indexed official university policies and regulations consulted by PolicyPilot. Inquiries submitted in the Policy Assistant are grounded in excerpts from these documents.
            </p>
          </div>

          {/* Clean Metric Stats Chips */}
          <div className="flex items-center space-x-3 text-xs shrink-0 pt-2 sm:pt-0">
            <div className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-center">
              <div className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">Manuals</div>
              <div className="text-sm font-bold text-slate-900">{documents?.length || 0}</div>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-center">
              <div className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">Indexed Pages</div>
              <div className="text-sm font-bold text-slate-900">{totalPages}</div>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-center">
              <div className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">Total Chunks</div>
              <div className="text-sm font-bold text-slate-900">{totalChunks}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Search and Category Filter Toolbar */}
      <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-2xs space-y-2.5">
        <div className="flex flex-col sm:flex-row gap-2.5 items-center justify-between">
          <div className="relative w-full sm:w-80">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter by keyword or title..."
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-slate-400 focus:bg-white text-slate-900 transition-colors"
            />
          </div>

          <div className="text-[11px] text-slate-500">
            Showing <span className="font-semibold text-slate-900">{filteredDocs.length}</span> of {documents?.length || 0} documents
          </div>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 scrollbar-none">
          <span className="text-[11px] font-medium text-slate-400 mr-1 flex items-center space-x-1">
            <Tag className="w-3 h-3" />
            <span>Category:</span>
          </span>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium whitespace-nowrap transition-colors ${
                selectedCategory === cat
                  ? 'bg-slate-900 text-white shadow-2xs'
                  : 'bg-slate-100/80 text-slate-600 hover:bg-slate-200/80'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Policy Documents Grid */}
      {filteredDocs.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-10 text-center shadow-2xs">
          <BookOpen className="w-8 h-8 text-slate-300 mx-auto mb-2" />
          <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">No Matching Documents</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            {searchQuery
              ? `No policies match the keyword "${searchQuery}". Try a different search term or select another category.`
              : "No official policy documents are currently registered in the database."}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredDocs.map((doc) => (
            <div
              key={doc.id}
              className="bg-white border border-slate-200 hover:border-slate-300 rounded-xl p-5 shadow-2xs transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                {/* Header */}
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center space-x-2.5">
                    <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center text-slate-700 shrink-0">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-slate-900 leading-tight" title={doc.document_name}>
                        {doc.document_name}
                      </h3>
                      <div className="flex items-center space-x-1.5 mt-0.5">
                        <span className="text-[10px] font-semibold px-1.5 py-0.2 bg-slate-100 text-slate-700 rounded border border-slate-200">
                          {doc.category || 'General'}
                        </span>
                        <span className="text-[11px] text-slate-400 font-mono">
                          v{doc.version || '1.0'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Summary */}
                <p className="text-xs text-slate-600 leading-relaxed">
                  {getPolicySummary(doc)}
                </p>

                {/* Metadata Details (Displayed as recorded, not claimed as universal facts) */}
                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100 text-[11px] text-slate-500">
                  <div className="flex items-center space-x-1.5 bg-slate-50 rounded px-2 py-1">
                    <Calendar className="w-3 h-3 text-slate-400" />
                    <span>Effective: <strong className="text-slate-700 font-medium">{doc.effective_date || 'Recorded'}</strong></span>
                  </div>
                  <div className="flex items-center space-x-1.5 bg-slate-50 rounded px-2 py-1">
                    <Layers className="w-3 h-3 text-slate-400" />
                    <span>Scope: <strong className="text-slate-700 font-medium">{doc.total_pages} Pages ({doc.total_chunks} Chunks)</strong></span>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[11px] text-slate-500 font-medium">
                  Official Sources Indexed
                </span>
                <button
                  onClick={() => onSelectPolicyForChat && onSelectPolicyForChat(doc.document_name)}
                  className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-md bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium transition-colors"
                >
                  <span>Consult Assistant</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Repository Note */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 text-xs text-slate-500 flex items-center space-x-2.5">
        <FileText className="w-4 h-4 text-slate-400 shrink-0" />
        <div>
          <span className="font-semibold text-slate-700">Official Document Index: </span>
          Policies listed here are extracted via PyMuPDF and split into overlapping text chunks for dense vector embedding and keyword retrieval.
        </div>
      </div>
    </div>
  );
}

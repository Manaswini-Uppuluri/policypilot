import React, { useState } from 'react';
import { 
  Upload, FileText, Trash2, CheckCircle2, AlertCircle, 
  RefreshCw, FileCheck, ShieldAlert, Database, Layers, Hash
} from 'lucide-react';
import { uploadDocument, deleteDocument } from '../services/api';

export default function AdminTab({ documents, onRefresh }) {
  const [file, setFile] = useState(null);
  const [category, setCategory] = useState('Disciplinary & Conduct');
  const [version, setVersion] = useState('2026.1');
  const [effectiveDate, setEffectiveDate] = useState('2026-2027');
  const [isUploading, setIsUploading] = useState(false);
  const [notification, setNotification] = useState(null);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setIsUploading(true);
    setNotification(null);

    try {
      const resp = await uploadDocument(file, category, version, effectiveDate);
      setNotification({ type: 'success', text: resp.message || `Document '${file.name}' successfully ingested.` });
      setFile(null);
      const fileInput = document.getElementById('admin-pdf-upload-input');
      if (fileInput) fileInput.value = '';
      onRefresh();
    } catch (err) {
      setNotification({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to upload and ingest policy document.'
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (id, docName) => {
    if (!window.confirm(`Are you sure you want to delete '${docName}' from the university policy repository?`)) return;
    try {
      await deleteDocument(id);
      setNotification({ type: 'success', text: `Successfully deleted '${docName}'.` });
      onRefresh();
    } catch (err) {
      setNotification({ type: 'error', text: 'Failed to delete policy document.' });
    }
  };

  const totalPages = (documents || []).reduce((acc, d) => acc + (d.total_pages || 0), 0);
  const totalChunks = (documents || []).reduce((acc, d) => acc + (d.total_chunks || 0), 0);

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      {/* Refined Prototype Security Notice */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 shadow-2xs">
        <div className="flex items-start space-x-3">
          <ShieldAlert className="w-4 h-4 text-slate-500 mt-0.5 shrink-0" />
          <div className="space-y-1 text-xs text-slate-600">
            <div className="flex items-center space-x-2">
              <span className="font-bold text-slate-900 uppercase tracking-wider text-[11px]">
                Administrative Console — Prototype Access
              </span>
              <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded bg-slate-200 text-slate-700">
                Authentication Not Enforced
              </span>
            </div>
            <p className="leading-relaxed">
              This administration view is provided for prototype demonstration, document ingestion, and repository management. Authentication and backend role-based access control (RBAC) are not implemented in this demo build. Client-side view separation is an interface convenience and does not constitute backend security.
            </p>
          </div>
        </div>
      </div>

      {/* Repository Overview Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-2xs">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Manuals</span>
            <FileText className="w-3.5 h-3.5" />
          </div>
          <div className="text-xl font-bold text-slate-900">{documents?.length || 0}</div>
          <span className="text-[10px] text-slate-400">PDF documents</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-2xs">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Total Pages</span>
            <Database className="w-3.5 h-3.5" />
          </div>
          <div className="text-xl font-bold text-slate-900">{totalPages}</div>
          <span className="text-[10px] text-slate-400">Extracted with PyMuPDF</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-2xs">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Total Chunks</span>
            <Layers className="w-3.5 h-3.5" />
          </div>
          <div className="text-xl font-bold text-slate-900">{totalChunks}</div>
          <span className="text-[10px] text-slate-400">Sliding window (600/100)</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-2xs">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Deduplication</span>
            <Hash className="w-3.5 h-3.5 text-emerald-600" />
          </div>
          <div className="text-xl font-bold text-emerald-700">Active</div>
          <span className="text-[10px] text-slate-400">SHA-256 hash match</span>
        </div>
      </div>

      {/* Notification Toast */}
      {notification && (
        <div
          className={`p-3 rounded-lg flex items-center justify-between text-xs font-medium ${
            notification.type === 'success'
              ? 'bg-emerald-50 text-emerald-900 border border-emerald-200'
              : 'bg-rose-50 text-rose-900 border border-rose-200'
          }`}
        >
          <div className="flex items-center space-x-2">
            {notification.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            )}
            <span>{notification.text}</span>
          </div>
          <button
            onClick={() => setNotification(null)}
            className="text-[11px] font-bold hover:underline ml-3"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Document Ingestion Card */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-2xs space-y-4">
        <div>
          <h2 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
            <Upload className="w-4 h-4 text-slate-600" />
            <span>Ingest Policy Document</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Upload an official PDF manual. The backend extracts text per page using PyMuPDF, chunks text with sliding overlap, and generates vector embeddings.
          </p>
        </div>

        <form onSubmit={handleUpload} className="space-y-3.5">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-1">
                Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full text-xs bg-slate-50 border border-slate-200 rounded-lg p-2 text-slate-800 focus:outline-none focus:border-slate-400 focus:bg-white"
              >
                <option value="Disciplinary & Conduct">Disciplinary & Conduct</option>
                <option value="Academic & Attendance">Academic & Attendance</option>
                <option value="Examinations & Ethics">Examinations & Ethics</option>
                <option value="Student Affairs & Residence">Student Affairs & Residence</option>
                <option value="General Administration">General Administration</option>
              </select>
            </div>
            <div>
              <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-1">
                Version Identifier
              </label>
              <input
                type="text"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                placeholder="e.g. 2026.1"
                className="w-full text-xs bg-slate-50 border border-slate-200 rounded-lg p-2 text-slate-800 focus:outline-none focus:border-slate-400 focus:bg-white"
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-1">
                Effective Academic Year
              </label>
              <input
                type="text"
                value={effectiveDate}
                onChange={(e) => setEffectiveDate(e.target.value)}
                placeholder="e.g. 2026-2027"
                className="w-full text-xs bg-slate-50 border border-slate-200 rounded-lg p-2 text-slate-800 focus:outline-none focus:border-slate-400 focus:bg-white"
              />
            </div>
          </div>

          {/* PDF Selector Dropzone */}
          <div className="border border-dashed border-slate-300 hover:border-slate-400 rounded-lg p-5 text-center transition-colors bg-slate-50/50">
            <input
              id="admin-pdf-upload-input"
              type="file"
              accept=".pdf"
              onChange={(e) => setFile(e.target.files[0])}
              className="hidden"
            />
            <label htmlFor="admin-pdf-upload-input" className="cursor-pointer flex flex-col items-center">
              <FileCheck className="w-6 h-6 text-slate-500 mb-1.5" />
              <span className="text-xs font-semibold text-slate-800">
                {file ? file.name : "Select Official University Policy PDF"}
              </span>
              <span className="text-[11px] text-slate-400 mt-0.5">
                {file ? `${(file.size / 1024).toFixed(1)} KB selected` : "Click to select a file (.pdf)"}
              </span>
            </label>
          </div>

          <button
            type="submit"
            disabled={!file || isUploading}
            className="px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 disabled:bg-slate-200 text-white disabled:text-slate-400 font-medium text-xs flex items-center space-x-2 transition-colors cursor-pointer disabled:cursor-not-allowed"
          >
            {isUploading ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Extracting Text & Generating Embeddings...</span>
              </>
            ) : (
              <>
                <Upload className="w-3.5 h-3.5" />
                <span>Ingest Document</span>
              </>
            )}
          </button>
        </form>
      </div>

      {/* Indexed Documents Table */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-2xs">
        <div className="flex justify-between items-center mb-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900">
              Policy Repository ({documents?.length || 0})
            </h2>
            <p className="text-[11px] text-slate-400">Indexed policy documents available for RAG search</p>
          </div>
          <button
            onClick={onRefresh}
            className="text-xs text-slate-500 hover:text-slate-800 flex items-center space-x-1"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Refresh</span>
          </button>
        </div>

        {(!documents || documents.length === 0) ? (
          <div className="text-center py-8 text-slate-400 text-xs">
            No policy documents currently registered in the database.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase text-[10px] tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-3">Document Title</th>
                  <th className="py-2.5 px-3">Category</th>
                  <th className="py-2.5 px-3">Version</th>
                  <th className="py-2.5 px-3">Pages</th>
                  <th className="py-2.5 px-3">Chunks</th>
                  <th className="py-2.5 px-3">SHA-256 Hash</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-2.5 px-3 font-semibold text-slate-900 flex items-center space-x-2">
                      <FileText className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span className="truncate max-w-xs" title={doc.document_name}>{doc.document_name}</span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded text-[11px]">
                        {doc.category || 'General'}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-[11px]">{doc.version || '1.0'}</td>
                    <td className="py-2.5 px-3 text-slate-600">{doc.total_pages} pages</td>
                    <td className="py-2.5 px-3 font-semibold text-slate-900">{doc.total_chunks} chunks</td>
                    <td className="py-2.5 px-3 font-mono text-[10px] text-slate-400">
                      {doc.file_hash ? doc.file_hash.substring(0, 10) + '...' : '—'}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={() => handleDelete(doc.id, doc.document_name)}
                        className="text-rose-600 hover:text-rose-800 p-1 rounded hover:bg-rose-50 transition-colors"
                        title="Delete policy"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

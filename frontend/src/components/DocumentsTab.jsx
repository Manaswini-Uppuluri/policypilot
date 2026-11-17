import React, { useState } from 'react';
import { Upload, FileText, Trash2, CheckCircle2, AlertCircle, RefreshCw, FileCheck } from 'lucide-react';
import { uploadDocument, deleteDocument } from '../services/api';

export default function DocumentsTab({ documents, onRefresh }) {
  const [file, setFile] = useState(null);
  const [category, setCategory] = useState('Academic');
  const [version, setVersion] = useState('2026.1');
  const [effectiveDate, setEffectiveDate] = useState('Fall 2026');
  const [isUploading, setIsUploading] = useState(false);
  const [notification, setNotification] = useState(null);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setIsUploading(true);
    setNotification(null);

    try {
      const resp = await uploadDocument(file, category, version, effectiveDate);
      setNotification({ type: 'success', text: resp.message });
      setFile(null);
      // Reset file input value
      const fileInput = document.getElementById('pdf-upload-input');
      if (fileInput) fileInput.value = '';
      onRefresh();
    } catch (err) {
      setNotification({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to upload and ingest document.'
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (id, docName) => {
    if (!window.confirm(`Are you sure you want to delete '${docName}'?`)) return;
    try {
      await deleteDocument(id);
      setNotification({ type: 'success', text: `Deleted '${docName}'.` });
      onRefresh();
    } catch (err) {
      setNotification({ type: 'error', text: 'Failed to delete policy.' });
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Notification Banner */}
      {notification && (
        <div
          className={`p-4 rounded-xl flex items-center justify-between text-sm ${
            notification.type === 'success'
              ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
              : 'bg-rose-50 text-rose-800 border border-rose-200'
          }`}
        >
          <div className="flex items-center space-x-2">
            {notification.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-600" />
            )}
            <span>{notification.text}</span>
          </div>
          <button
            onClick={() => setNotification(null)}
            className="text-xs font-semibold hover:underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Upload Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center space-x-2.5 mb-4">
          <Upload className="w-5 h-5 text-sky-600" />
          <h2 className="text-base font-bold text-slate-900">Ingest New University Policy Document</h2>
        </div>
        <p className="text-xs text-slate-500 mb-6">
          Upload official PDF regulations. PyMuPDF extracts full-text per page, chunks content with sliding window overlap, and indexes vector embeddings with deduplication.
        </p>

        <form onSubmit={handleUpload} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Policy Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-slate-800 focus:ring-2 focus:ring-sky-500"
              >
                <option value="Academic & Attendance">Academic & Attendance</option>
                <option value="Examinations & Ethics">Examinations & Ethics</option>
                <option value="Student Affairs & Residence">Student Affairs & Residence</option>
                <option value="Disciplinary & Conduct">Disciplinary & Conduct</option>
                <option value="General Administration">General Administration</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Version Identifier</label>
              <input
                type="text"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                placeholder="e.g. 2026.1"
                className="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-slate-800 focus:ring-2 focus:ring-sky-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Effective Date</label>
              <input
                type="text"
                value={effectiveDate}
                onChange={(e) => setEffectiveDate(e.target.value)}
                placeholder="e.g. Fall 2026"
                className="w-full text-xs bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-slate-800 focus:ring-2 focus:ring-sky-500"
              />
            </div>
          </div>

          <div className="border-2 border-dashed border-slate-300 hover:border-sky-500 rounded-xl p-6 text-center transition-colors">
            <input
              id="pdf-upload-input"
              type="file"
              accept=".pdf"
              onChange={(e) => setFile(e.target.files[0])}
              className="hidden"
            />
            <label htmlFor="pdf-upload-input" className="cursor-pointer flex flex-col items-center">
              <FileCheck className="w-8 h-8 text-sky-600 mb-2" />
              <span className="text-sm font-semibold text-slate-800">
                {file ? file.name : "Select official university PDF document"}
              </span>
              <span className="text-xs text-slate-400 mt-1">
                {file ? `${(file.size / 1024).toFixed(1)} KB` : "Click to browse files (PDF only)"}
              </span>
            </label>
          </div>

          <button
            type="submit"
            disabled={!file || isUploading}
            className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-700 disabled:bg-slate-300 text-white font-medium text-sm flex items-center justify-center space-x-2 transition-colors shadow-sm"
          >
            {isUploading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Extracting, Chunking & Indexing Embeddings...</span>
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                <span>Upload & Index Document</span>
              </>
            )}
          </button>
        </form>
      </div>

      {/* Indexed Documents Table */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center space-x-2">
            <FileText className="w-5 h-5 text-sky-600" />
            <h2 className="text-base font-bold text-slate-900">
              Indexed Policy Catalog ({documents.length})
            </h2>
          </div>
          <button
            onClick={onRefresh}
            className="text-xs text-slate-500 hover:text-sky-600 flex items-center space-x-1"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>

        {documents.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-xs">
            No policy documents currently indexed. Upload a PDF or generate sample policies.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="bg-slate-50 text-slate-700 font-semibold uppercase text-[10px] tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Document Title</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Version</th>
                  <th className="py-3 px-4">Pages</th>
                  <th className="py-3 px-4">Indexed Chunks</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4 font-semibold text-slate-900 flex items-center space-x-2">
                      <FileText className="w-4 h-4 text-sky-600 shrink-0" />
                      <span className="truncate max-w-xs">{doc.document_name}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-medium">
                        {doc.category}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono">{doc.version}</td>
                    <td className="py-3 px-4">{doc.total_pages} pages</td>
                    <td className="py-3 px-4 font-semibold text-sky-700">{doc.total_chunks} chunks</td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleDelete(doc.id, doc.document_name)}
                        className="text-rose-600 hover:text-rose-800 p-1.5 rounded hover:bg-rose-50 transition-colors"
                        title="Delete policy"
                      >
                        <Trash2 className="w-4 h-4" />
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


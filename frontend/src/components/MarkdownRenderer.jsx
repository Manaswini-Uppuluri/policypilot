import React from 'react';

/**
 * Parses inline markdown: **bold**, *italic*, `code`, and clean bracketed document references.
 */
function renderInline(text) {
  if (!text) return null;

  // Tokenize by code, bold, italic
  // Regex matches: `code`, **bold**, *italic*
  const tokens = [];
  let remaining = text;
  let keyIndex = 0;

  // Split regex that preserves delimiters
  const regex = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g;
  const parts = remaining.split(regex);

  return parts.map((part, idx) => {
    if (!part) return null;

    if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
      return (
        <code
          key={idx}
          className="font-mono text-[11px] bg-slate-100 text-slate-800 px-1 py-0.5 rounded border border-slate-200"
        >
          {part.slice(1, -1)}
        </code>
      );
    }

    if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
      return (
        <strong key={idx} className="font-semibold text-slate-900">
          {part.slice(2, -2)}
        </strong>
      );
    }

    if (part.startsWith('*') && part.endsWith('*') && part.length > 2) {
      return (
        <em key={idx} className="italic text-slate-700">
          {part.slice(1, -1)}
        </em>
      );
    }

    // Check for inline bracketed citations like [code_conduct_MSRIT.pdf, Page 2]
    // Render clean subtle badge
    if (part.includes('[') && part.includes(']')) {
      const citeParts = part.split(/(\[[^\]]+\])/g);
      return citeParts.map((cp, cidx) => {
        if (cp.startsWith('[') && cp.endsWith(']')) {
          const content = cp.slice(1, -1);
          return (
            <span
              key={`${idx}-${cidx}`}
              className="inline-flex items-center text-[10px] font-medium text-slate-600 bg-slate-100/90 border border-slate-200/80 px-1.5 py-0.2 mx-0.5 rounded"
            >
              {content}
            </span>
          );
        }
        return cp;
      });
    }

    return part;
  });
}

/**
 * Robust markdown block parser for assistant responses.
 * Handles headings (#, ##, ###), bullet lists (- or *), numbered lists (1.),
 * blockquotes (>), horizontal rules (---), and regular paragraphs.
 */
export default function MarkdownRenderer({ content, className = '' }) {
  if (!content) return null;

  const rawLines = content.split('\n');
  const elements = [];
  let currentList = null; // { type: 'ul' | 'ol', items: [] }

  const flushList = () => {
    if (currentList) {
      if (currentList.type === 'ul') {
        elements.push(
          <ul key={`ul-${elements.length}`} className="my-2 space-y-1.5 pl-1">
            {currentList.items.map((it, idx) => (
              <li key={idx} className="flex items-start text-xs text-slate-700 leading-relaxed">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400 mt-1.5 mr-2 shrink-0" />
                <span className="flex-1">{renderInline(it)}</span>
              </li>
            ))}
          </ul>
        );
      } else if (currentList.type === 'ol') {
        elements.push(
          <ol key={`ol-${elements.length}`} className="my-2 space-y-1.5 pl-1 list-none counter-reset-list">
            {currentList.items.map((it, idx) => (
              <li key={idx} className="flex items-start text-xs text-slate-700 leading-relaxed">
                <span className="text-[11px] font-semibold text-slate-500 w-4 mt-0.5 mr-1.5 shrink-0">
                  {idx + 1}.
                </span>
                <span className="flex-1">{renderInline(it)}</span>
              </li>
            ))}
          </ol>
        );
      }
      currentList = null;
    }
  };

  for (let i = 0; i < rawLines.length; i++) {
    const line = rawLines[i];
    const trimmed = line.trim();

    // Empty line: flush list
    if (!trimmed) {
      flushList();
      continue;
    }

    // Horizontal Rule: --- or ***
    if (/^(\-{3,}|\*{3,})$/.test(trimmed)) {
      flushList();
      elements.push(<hr key={`hr-${elements.length}`} className="my-3 border-slate-200" />);
      continue;
    }

    // Headings
    if (trimmed.startsWith('### ')) {
      flushList();
      elements.push(
        <h3 key={`h3-${elements.length}`} className="text-xs font-bold text-slate-900 uppercase tracking-wider mt-3 mb-1.5">
          {renderInline(trimmed.slice(4))}
        </h3>
      );
      continue;
    }

    if (trimmed.startsWith('## ')) {
      flushList();
      elements.push(
        <h2 key={`h2-${elements.length}`} className="text-sm font-bold text-slate-900 mt-3.5 mb-1.5">
          {renderInline(trimmed.slice(3))}
        </h2>
      );
      continue;
    }

    if (trimmed.startsWith('# ')) {
      flushList();
      elements.push(
        <h1 key={`h1-${elements.length}`} className="text-base font-bold text-slate-900 mt-4 mb-2">
          {renderInline(trimmed.slice(2))}
        </h1>
      );
      continue;
    }

    // Blockquote
    if (trimmed.startsWith('> ')) {
      flushList();
      elements.push(
        <blockquote
          key={`bq-${elements.length}`}
          className="border-l-2 border-slate-300 pl-3 py-1 my-2 text-xs italic text-slate-600 bg-slate-50/70 rounded-r"
        >
          {renderInline(trimmed.slice(2))}
        </blockquote>
      );
      continue;
    }

    // Unordered List (- or *)
    const ulMatch = trimmed.match(/^[-*]\s+(.+)/);
    if (ulMatch) {
      if (!currentList || currentList.type !== 'ul') {
        flushList();
        currentList = { type: 'ul', items: [] };
      }
      currentList.items.push(ulMatch[1]);
      continue;
    }

    // Ordered List (1. 2.)
    const olMatch = trimmed.match(/^\d+\.\s+(.+)/);
    if (olMatch) {
      if (!currentList || currentList.type !== 'ol') {
        flushList();
        currentList = { type: 'ol', items: [] };
      }
      currentList.items.push(olMatch[1]);
      continue;
    }

    // Regular line / Paragraph
    flushList();
    elements.push(
      <p key={`p-${elements.length}`} className="text-xs text-slate-700 leading-relaxed my-1.5">
        {renderInline(trimmed)}
      </p>
    );
  }

  flushList();

  return <div className={`space-y-1 text-slate-800 ${className}`}>{elements}</div>;
}

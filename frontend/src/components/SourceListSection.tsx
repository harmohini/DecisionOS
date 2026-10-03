import React, { useState } from 'react';
import { ResearchResult } from '../types';
import { ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';

interface SourceListSectionProps {
  sources: { title?: string; url: string }[];
  rawResults?: ResearchResult[];
}

export const SourceListSection: React.FC<SourceListSectionProps> = ({ sources, rawResults }) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);

  const sourceMap = new Map<string, { title: string; url: string }>();

  if (sources && sources.length > 0) {
    sources.forEach((s) => {
      if (s.url) {
        sourceMap.set(s.url, {
          title: s.title || s.url,
          url: s.url,
        });
      }
    });
  }

  if (rawResults && rawResults.length > 0) {
    rawResults.forEach((r) => {
      if (r.url) {
        sourceMap.set(r.url, {
          title: r.title || r.url,
          url: r.url,
        });
      }
    });
  }

  const allSources = Array.from(sourceMap.values());

  if (allSources.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-2xl border border-sand-200 p-6 shadow-warm-md space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-serif text-2xl font-bold text-stone-900">Sources</h2>
          <p className="text-xs font-semibold text-stone-500 mt-0.5">{allSources.length} sources used</p>
        </div>

        <button
          onClick={() => setIsOpen(!isOpen)}
          className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-sand-100 hover:bg-sand-200 text-stone-800 text-xs font-medium border border-sand-200 transition-colors"
        >
          <span>{isOpen ? 'Hide sources' : 'View sources'}</span>
          {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {isOpen && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-3 border-t border-sand-100 animate-fadeIn">
          {allSources.map((source, idx) => {
            let domain = source.url;
            try {
              domain = new URL(source.url).hostname.replace('www.', '');
            } catch (e) {
              domain = source.url;
            }

            return (
              <a
                key={idx}
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="p-3 rounded-xl border border-sand-200 hover:border-sand-300 bg-sand-50/50 hover:bg-sand-100/70 transition-all flex items-center justify-between group space-x-3"
              >
                <div className="truncate space-y-0.5">
                  <h4 className="text-xs font-semibold text-stone-900 group-hover:text-amber-900 truncate">
                    {source.title}
                  </h4>
                  <span className="text-[11px] text-stone-400 block font-mono">
                    {domain}
                  </span>
                </div>
                <ExternalLink className="w-3.5 h-3.5 shrink-0 text-amber-800 opacity-70 group-hover:opacity-100" />
              </a>
            );
          })}
        </div>
      )}
    </div>
  );
};

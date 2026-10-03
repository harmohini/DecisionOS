import React from 'react';
import { EvidenceClaim } from '../types';
import { ShieldCheck, ExternalLink, Globe, ShoppingCart, Video } from 'lucide-react';

interface EvidenceSectionProps {
  claims: EvidenceClaim[];
}

export const EvidenceSection: React.FC<EvidenceSectionProps> = ({ claims }) => {
  if (!claims || claims.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-sand-200 p-8 shadow-warm-sm text-center space-y-2">
        <ShieldCheck className="w-8 h-8 text-stone-400 mx-auto" />
        <h3 className="font-serif font-bold text-stone-900 text-lg">No Factual Claims Extracted</h3>
        <p className="text-xs text-stone-500 max-w-md mx-auto">
          The evidence extraction agent did not return structured claims for this query.
        </p>
      </div>
    );
  }

  const getSourceTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'shopping':
        return <ShoppingCart className="w-3.5 h-3.5 text-blue-600" />;
      case 'youtube':
        return <Video className="w-3.5 h-3.5 text-red-600" />;
      case 'web':
      default:
        return <Globe className="w-3.5 h-3.5 text-amber-700" />;
    }
  };

  const getConfidenceBadge = (confidence: string) => {
    switch (confidence.toUpperCase()) {
      case 'HIGH':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'MEDIUM':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'LOW':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      default:
        return 'bg-sand-100 text-stone-700 border-sand-200';
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-sand-200 p-6 sm:p-8 shadow-warm-md space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-sand-100 pb-4">
        <div>
          <h2 className="font-serif text-2xl font-bold text-stone-900 flex items-center space-x-2">
            <ShieldCheck className="w-6 h-6 text-emerald-700 shrink-0" />
            <span>Evidence</span>
          </h2>
          <p className="text-xs text-stone-500 mt-0.5">
            Traceable factual claims extracted directly from real web search results
          </p>
        </div>

        <span className="text-xs font-semibold px-3 py-1 bg-sand-100 text-stone-800 rounded-full border border-sand-200 self-start sm:self-auto">
          {claims.length} Verified Claims
        </span>
      </div>

      {/* Claims List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {claims.map((claim, idx) => (
          <div
            key={claim.claim_id || idx}
            className="bg-sand-50/50 rounded-xl border border-sand-200 p-4 space-y-3 flex flex-col justify-between shadow-warm-xs"
          >
            {/* Top Meta */}
            <div className="space-y-1.5">
              <div className="flex items-start justify-between gap-2">
                <span className="text-[11px] font-bold text-amber-900 bg-amber-100/80 px-2 py-0.5 rounded border border-amber-200 truncate">
                  {claim.entity} — {claim.attribute}
                </span>
                <span
                  className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border shrink-0 ${getConfidenceBadge(
                    claim.confidence
                  )}`}
                >
                  {claim.confidence} Confidence
                </span>
              </div>

              {/* Claim & Value */}
              <div className="text-sm font-bold text-stone-900 pt-1">
                Value: <span className="text-amber-900">{claim.value}</span>
              </div>

              {/* Evidence Snippet */}
              {claim.evidence_text && (
                <p className="text-xs text-stone-600 bg-white p-2.5 rounded-lg border border-sand-200 italic leading-relaxed">
                  "{claim.evidence_text}"
                </p>
              )}
            </div>

            {/* Source Link */}
            <div className="pt-2 border-t border-sand-200/60 flex items-center justify-between text-xs">
              <div className="flex items-center space-x-1.5 text-stone-500">
                {getSourceTypeIcon(claim.source_type)}
                <span className="capitalize text-[11px] font-medium">{claim.source_type}</span>
              </div>

              <a
                href={claim.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center space-x-1 text-xs text-amber-800 hover:text-amber-900 font-medium hover:underline truncate max-w-[200px]"
                title={claim.source_title || claim.source_url}
              >
                <span className="truncate">{claim.source_title || 'Original Source'}</span>
                <ExternalLink className="w-3 h-3 shrink-0 text-amber-700" />
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

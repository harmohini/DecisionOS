import React from 'react';
import { ComparisonResult } from '../types';
import { CheckCircle2, AlertCircle } from 'lucide-react';

interface ComparisonTableSectionProps {
  comparison: ComparisonResult;
}

export const ComparisonTableSection: React.FC<ComparisonTableSectionProps> = ({ comparison }) => {
  if (!comparison || !comparison.option_comparisons || comparison.option_comparisons.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-2xl border border-sand-200 p-6 sm:p-8 shadow-warm-md space-y-6">
      <div className="border-b border-sand-100 pb-3">
        <h2 className="font-serif text-2xl font-bold text-stone-900">Trade-offs</h2>
        <p className="text-xs text-stone-500 mt-0.5">Side-by-side evaluation to help you decide</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {comparison.option_comparisons.map((opt, idx) => {
          const goodFor = opt.requirement_alignment
            ? opt.requirement_alignment.filter(a => a.status === 'satisfies').map(a => a.requirement)
            : [];

          return (
            <div key={idx} className="bg-sand-50/50 rounded-xl border border-sand-200 p-5 space-y-4">
              <div className="font-serif font-bold text-stone-900 text-lg border-b border-sand-200 pb-2 flex justify-between items-center">
                <span>{opt.option_name}</span>
                {opt.price && <span className="text-xs font-mono font-medium text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">{opt.price}</span>}
              </div>

              {/* Good for */}
              <div className="space-y-1.5">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 flex items-center space-x-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Good for</span>
                </span>
                {goodFor.length > 0 ? (
                  <ul className="space-y-1 text-xs text-stone-700">
                    {goodFor.map((gf, gIdx) => (
                      <li key={gIdx} className="flex items-start space-x-1.5">
                        <span className="text-emerald-600 font-bold shrink-0">•</span>
                        <span className="leading-snug">{gf}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs italic text-stone-400">Standard configuration</p>
                )}
              </div>

              {/* Watch out for */}
              <div className="space-y-1.5 pt-2 border-t border-sand-200/60">
                <span className="text-xs font-bold uppercase tracking-wider text-amber-900 flex items-center space-x-1">
                  <AlertCircle className="w-3.5 h-3.5 text-amber-700" />
                  <span>Watch out for</span>
                </span>
                {opt.known_tradeoffs && opt.known_tradeoffs.length > 0 ? (
                  <ul className="space-y-1 text-xs text-stone-700">
                    {opt.known_tradeoffs.map((to, tIdx) => (
                      <li key={tIdx} className="flex items-start space-x-1.5">
                        <span className="text-amber-700 font-bold shrink-0">•</span>
                        <span className="leading-snug">{to}</span>
                      </li>
                    ))}
                  </ul>
                ) : opt.uncertainties && opt.uncertainties.length > 0 ? (
                  <ul className="space-y-1 text-xs text-stone-600">
                    {opt.uncertainties.map((unc, uIdx) => (
                      <li key={uIdx} className="flex items-start space-x-1.5">
                        <span className="text-stone-400 font-bold shrink-0">•</span>
                        <span className="leading-snug">{unc}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs italic text-stone-400">No specific warnings reported</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

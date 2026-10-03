import React from 'react';
import { ReportOptionItem } from '../types';

interface OptionCardSectionProps {
  options: ReportOptionItem[];
}

export const OptionCardSection: React.FC<OptionCardSectionProps> = ({ options }) => {
  if (!options || options.length === 0) {
    return null;
  }

  // Cap at maximum 6 options (Section 2 & 10)
  const topOptions = options.slice(0, 6);

  const getBestForLabel = (option: ReportOptionItem): string => {
    if (option.requirement_alignment && option.requirement_alignment.length > 0) {
      const topFit = option.requirement_alignment.find(a => a.status === 'satisfies');
      if (topFit) {
        return `Fit for ${topFit.requirement}`;
      }
    }
    if (option.strengths && option.strengths.length > 0) {
      return option.strengths[0];
    }
    return "Balanced performance";
  };

  return (
    <div className="space-y-6">
      <div className="border-b border-sand-100 pb-3 flex items-center justify-between">
        <h2 className="font-serif text-2xl font-bold text-stone-900">Top Options</h2>
        <span className="text-xs text-stone-500 font-medium">Showing top {topOptions.length} recommendations</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {topOptions.map((option, idx) => {
          const bestFor = getBestForLabel(option);

          // Maximum 3 reasons why it fits
          const fits = option.requirement_alignment
            ? option.requirement_alignment.filter(a => a.status === 'satisfies' || a.status === 'partially_satisfies').slice(0, 3)
            : (option.strengths || []).slice(0, 3);

          // Maximum 1 trade-off
          const tradeoff = option.tradeoffs && option.tradeoffs.length > 0
            ? option.tradeoffs[0]
            : (option.uncertainties && option.uncertainties.length > 0 ? option.uncertainties[0] : null);

          return (
            <div
              key={idx}
              className="bg-white rounded-2xl border border-sand-200 p-5 shadow-warm-sm flex flex-col justify-between space-y-4"
            >
              {/* Option Name & Best For */}
              <div className="space-y-1 border-b border-sand-100 pb-3">
                <h3 className="font-serif text-lg font-bold text-stone-900">{option.name}</h3>
                <p className="text-xs font-semibold text-emerald-800 bg-emerald-50 inline-block px-2.5 py-0.5 rounded border border-emerald-200">
                  Best for: {bestFor}
                </p>
              </div>

              {/* Why it fits (Max 3 bullets) */}
              <div className="space-y-1.5">
                <span className="text-xs font-bold uppercase tracking-wider text-stone-700 block">
                  Why it fits
                </span>
                {fits.length > 0 ? (
                  <ul className="space-y-1 text-xs text-stone-800">
                    {fits.map((fitItem: any, fIdx) => (
                      <li key={fIdx} className="flex items-start space-x-1.5">
                        <span className="text-emerald-600 font-bold shrink-0">✓</span>
                        <span className="leading-snug">
                          {typeof fitItem === 'string' ? fitItem : `${fitItem.requirement}: ${fitItem.explanation}`}
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs italic text-stone-400">Standard configuration</p>
                )}
              </div>

              {/* Watch out (Max 1 trade-off line) */}
              {tradeoff && (
                <div className="pt-2 border-t border-sand-100 text-xs text-stone-700">
                  <span className="font-bold text-amber-900 block mb-0.5">Watch out</span>
                  <p className="text-stone-600 leading-snug">{tradeoff}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

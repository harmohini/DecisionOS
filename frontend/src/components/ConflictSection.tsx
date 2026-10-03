import React from 'react';
import { DetectedConflict } from '../types';

interface ConflictSectionProps {
  conflicts: DetectedConflict[];
}

export const ConflictSection: React.FC<ConflictSectionProps> = ({ conflicts }) => {
  if (!conflicts || conflicts.length === 0) {
    return null;
  }

  // Cap at maximum 3 conflicts (Section 5 & 10)
  const topConflicts = conflicts.slice(0, 3);

  return (
    <div className="bg-white rounded-2xl border border-sand-200 p-6 sm:p-8 shadow-warm-md space-y-4">
      <div className="border-b border-sand-100 pb-3">
        <h2 className="font-serif text-2xl font-bold text-stone-900">Check Before Buying</h2>
        <p className="text-xs text-stone-500 mt-0.5">Disagreements or mismatches found across sources</p>
      </div>

      <div className="space-y-3 pt-1">
        {topConflicts.map((conflict, idx) => (
          <div
            key={conflict.conflict_id || idx}
            className="bg-amber-50/50 rounded-xl border border-amber-200 p-4 space-y-1.5 text-xs text-stone-800"
          >
            <div className="font-bold text-stone-900 text-sm flex items-center space-x-1.5">
              <span className="text-amber-700">⚠</span>
              <span>{conflict.attribute} differs between sources ({conflict.entity})</span>
            </div>

            {conflict.conflicting_values && conflict.conflicting_values.length > 0 && (
              <p className="text-stone-700 leading-snug">
                Reported values: <span className="font-semibold">{conflict.conflicting_values.join(" vs ")}</span>.
              </p>
            )}

            {conflict.recommended_verification && (
              <p className="text-amber-900 pt-0.5">
                <span className="font-bold">Verify: </span>{conflict.recommended_verification}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

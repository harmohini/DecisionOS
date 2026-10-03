import React from 'react';

interface KeyFindingsSectionProps {
  findings: string[];
}

export const KeyFindingsSection: React.FC<KeyFindingsSectionProps> = ({ findings }) => {
  if (!findings || findings.length === 0) {
    return null;
  }

  // Cap at maximum 3 findings (Section 4 & 10)
  const topFindings = findings.slice(0, 3);

  return (
    <div className="bg-white rounded-2xl border border-sand-200 p-6 sm:p-8 shadow-warm-md space-y-4">
      <div className="border-b border-sand-100 pb-3">
        <h2 className="font-serif text-2xl font-bold text-stone-900">Key Findings</h2>
        <p className="text-xs text-stone-500 mt-0.5">Top evidence-backed insights</p>
      </div>

      <div className="space-y-2.5 pt-1">
        {topFindings.map((finding, idx) => (
          <div key={idx} className="flex items-start space-x-2.5 text-sm text-stone-800">
            <span className="text-emerald-600 font-bold shrink-0 mt-0.5">✓</span>
            <span className="leading-snug font-medium">{finding}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

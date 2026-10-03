import React from 'react';

interface VerificationSectionProps {
  items: string[];
}

export const VerificationSection: React.FC<VerificationSectionProps> = ({ items }) => {
  if (!items || items.length === 0) {
    return null;
  }

  // Cap at maximum 3 items (Section 7 & 10)
  const topItems = items.slice(0, 3);

  return (
    <div className="bg-white rounded-2xl border border-sand-200 p-6 sm:p-8 shadow-warm-md space-y-4">
      <div className="border-b border-sand-100 pb-3">
        <h2 className="font-serif text-2xl font-bold text-stone-900">Before You Decide</h2>
        <p className="text-xs text-stone-500 mt-0.5">Final checklist before purchasing</p>
      </div>

      <div className="space-y-2.5 pt-1">
        {topItems.map((item, idx) => (
          <div
            key={idx}
            className="bg-sand-50/70 p-3 rounded-xl border border-sand-200 flex items-center space-x-3 text-sm text-stone-800"
          >
            <span className="text-amber-800 font-bold shrink-0 text-base">☐</span>
            <span className="leading-snug font-medium">{item}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

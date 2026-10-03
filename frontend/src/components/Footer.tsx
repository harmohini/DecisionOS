import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="mt-auto border-t border-sand-200/60 bg-sand-100/40 py-6 text-xs text-stone-500">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <span className="font-serif font-bold text-stone-800">DecisionOS</span>
          <span>&mdash; Decision Research Assistant</span>
        </div>
        <span>Evidence-Backed Insights</span>
      </div>
    </footer>
  );
};

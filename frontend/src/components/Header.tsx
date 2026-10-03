import React from 'react';
import { Compass } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-sand-200/60 shadow-warm-sm bg-white/80 backdrop-blur-md">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-stone-900 text-sand-50 flex items-center justify-center shadow-md">
            <Compass className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <span className="font-serif text-xl font-bold tracking-tight text-stone-900">
              Decision<span className="text-amber-700">OS</span>
            </span>
          </div>
        </div>

        <span className="text-xs text-stone-500 font-medium">
          Evidence-Based Decision Research
        </span>
      </div>
    </header>
  );
};

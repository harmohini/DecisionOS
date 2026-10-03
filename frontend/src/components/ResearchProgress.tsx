import React from 'react';
import { Loader2, CheckCircle2, Circle } from 'lucide-react';

export const ResearchProgress: React.FC = () => {
  const steps = [
    { title: 'Finding relevant information', completed: true },
    { title: 'Comparing the options', completed: true },
    { title: 'Checking important details', completed: true },
    { title: 'Preparing your answer', completed: false },
  ];

  return (
    <div className="bg-white rounded-2xl border border-sand-200 p-6 sm:p-8 shadow-warm-md space-y-6 max-w-2xl mx-auto">
      <div className="flex items-center space-x-3 border-b border-sand-100 pb-4">
        <div className="w-9 h-9 rounded-xl bg-amber-500 text-stone-900 flex items-center justify-center font-bold shadow-warm-xs">
          <Loader2 className="w-5 h-5 text-stone-900 animate-spin" />
        </div>
        <div>
          <h3 className="font-serif font-bold text-stone-900 text-xl">Researching your decision…</h3>
          <p className="text-xs text-stone-500">Evaluating web evidence and trade-offs</p>
        </div>
      </div>

      <div className="space-y-3 pt-1">
        {steps.map((step, idx) => (
          <div key={idx} className="flex items-center space-x-3 text-sm text-stone-800">
            {step.completed ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            ) : (
              <Circle className="w-5 h-5 text-amber-500 animate-pulse shrink-0" />
            )}
            <span className={step.completed ? 'font-medium text-stone-900' : 'text-stone-500 font-normal'}>
              {step.title}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

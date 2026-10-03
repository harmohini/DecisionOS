import React from 'react';
import { FinalDecisionReport, ResearchPlan } from '../types';

interface DecisionSummarySectionProps {
  report: FinalDecisionReport;
  plan?: ResearchPlan;
}

export const DecisionSummarySection: React.FC<DecisionSummarySectionProps> = ({ report, plan }) => {
  // Extract key-value lines (Max 4 lines safely)
  const purpose = plan?.user_goal || (report?.title ? report.title.replace("Decision Support Report: ", "") : "Decision Research");
  const budget = plan?.budget || (report?.user_requirements ? report.user_requirements.find(r => r && typeof r === 'string' && r.toLowerCase().includes("budget"))?.replace("Budget: ", "") : undefined);
  
  const mustHaves = plan?.hard_constraints && plan.hard_constraints.length > 0 
    ? plan.hard_constraints.slice(0, 3).join(" · ")
    : (report?.user_requirements && report.user_requirements.length > 0 ? report.user_requirements.slice(0, 3).join(" · ") : "");

  const mainTradeoff = report?.trade_offs && report.trade_offs.length > 0
    ? report.trade_offs[0].replace(/^Comparing \d+ options[^:]*:\s*/i, "")
    : "Performance vs Battery life";

  return (
    <div className="bg-white rounded-2xl border border-sand-200 p-6 sm:p-8 shadow-warm-md space-y-4">
      <h2 className="font-serif text-2xl font-bold text-stone-900 border-b border-sand-100 pb-3">
        Your Decision
      </h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm font-sans pt-1">
        {purpose && (
          <div className="bg-sand-50/70 p-3.5 rounded-xl border border-sand-200 space-y-0.5">
            <span className="text-xs font-bold text-stone-500 uppercase tracking-wider block">Looking for</span>
            <span className="font-semibold text-stone-900 line-clamp-1">{purpose}</span>
          </div>
        )}

        {budget && (
          <div className="bg-sand-50/70 p-3.5 rounded-xl border border-sand-200 space-y-0.5">
            <span className="text-xs font-bold text-stone-500 uppercase tracking-wider block">Budget</span>
            <span className="font-semibold text-emerald-800">{budget}</span>
          </div>
        )}

        {mustHaves && (
          <div className="bg-sand-50/70 p-3.5 rounded-xl border border-sand-200 space-y-0.5">
            <span className="text-xs font-bold text-stone-500 uppercase tracking-wider block">Must have</span>
            <span className="font-semibold text-stone-900 line-clamp-1">{mustHaves}</span>
          </div>
        )}

        {mainTradeoff && (
          <div className="bg-sand-50/70 p-3.5 rounded-xl border border-sand-200 space-y-0.5">
            <span className="text-xs font-bold text-stone-500 uppercase tracking-wider block">Main trade-off</span>
            <span className="font-semibold text-amber-900 line-clamp-1">{mainTradeoff}</span>
          </div>
        )}
      </div>
    </div>
  );
};

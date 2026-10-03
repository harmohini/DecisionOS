import React, { useState } from 'react';
import { SystemHealth, FullResearchResponse } from '../types';
import { submitDecisionResearch } from '../services/api';
import { ResearchProgress } from '../components/ResearchProgress';
import { DecisionSummarySection } from '../components/DecisionSummarySection';
import { OptionCardSection } from '../components/OptionCardSection';
import { KeyFindingsSection } from '../components/KeyFindingsSection';
import { ConflictSection } from '../components/ConflictSection';
import { VerificationSection } from '../components/VerificationSection';
import { SourceListSection } from '../components/SourceListSection';
import { ArrowRight, RotateCcw, AlertCircle } from 'lucide-react';

interface HomeProps {
  health?: SystemHealth | null;
  loading?: boolean;
  error?: string | null;
  onRefreshHealth?: () => void;
}

export const Home: React.FC<HomeProps> = () => {
  const defaultPlaceholder = "Example: I need a laptop for AI/ML, programming and occasional gaming under ₹1,20,000.";

  const examplePrompts = [
    "Which laptop should I buy under ₹1,20,000 for AI/ML and gaming?",
    "Which phone is better for photography and battery life?",
    "Which software is better for a small business?",
  ];

  const [query, setQuery] = useState<string>("");
  const [isResearching, setIsResearching] = useState<boolean>(false);
  const [researchResult, setResearchResult] = useState<FullResearchResponse | null>(null);
  const [researchError, setResearchError] = useState<boolean>(false);

  const handleStartResearch = async () => {
    if (!query.trim()) return;

    setIsResearching(true);
    setResearchError(false);
    setResearchResult(null);

    try {
      const response = await submitDecisionResearch(query.trim());
      setResearchResult(response);
    } catch (err: any) {
      console.error("[DecisionOS Error]", err);
      setResearchError(true);
    } finally {
      setIsResearching(false);
    }
  };

  const handleReset = () => {
    setQuery("");
    setResearchResult(null);
    setResearchError(false);
  };

  return (
    <div className="space-y-10 pb-16 max-w-4xl mx-auto">
      {/* Hero Section */}
      <section className="text-center space-y-3 pt-4">
        <h1 className="font-serif text-4xl sm:text-5xl font-bold tracking-tight text-stone-900 leading-tight">
          What are you trying to decide?
        </h1>
        
        <p className="text-stone-600 text-base sm:text-lg max-w-2xl mx-auto leading-relaxed">
          Tell DecisionOS what you’re considering. We’ll research the options, compare the evidence, and highlight anything you should verify.
        </p>
      </section>

      {/* Main Decision Input Shell */}
      {!researchResult && !isResearching && (
        <div className="bg-white rounded-2xl border border-sand-200 p-6 sm:p-8 shadow-warm-sm space-y-6">
          <div className="space-y-2">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={isResearching}
              rows={4}
              className="w-full rounded-xl border border-sand-300 p-4 text-base text-stone-900 placeholder-stone-400 focus:border-stone-800 focus:ring-1 focus:ring-stone-800 transition-all shadow-inner bg-sand-50/30 font-sans disabled:opacity-60"
              placeholder={defaultPlaceholder}
            />
          </div>

          <div className="flex justify-end pt-1">
            <button
              onClick={handleStartResearch}
              disabled={isResearching || !query.trim()}
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-stone-900 text-sand-50 font-medium text-base flex items-center justify-center space-x-2 hover:bg-stone-800 transition-all shadow-warm-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span>Research my decision</span>
              <ArrowRight className="w-4 h-4 text-amber-400" />
            </button>
          </div>

          {/* Try an Example */}
          <div className="border-t border-sand-100 pt-4 space-y-2">
            <span className="text-xs font-semibold text-stone-500 uppercase tracking-wider">
              Try an example
            </span>
            <div className="flex flex-col sm:flex-row flex-wrap gap-2">
              {examplePrompts.map((promptText, pIdx) => (
                <button
                  key={pIdx}
                  type="button"
                  onClick={() => setQuery(promptText)}
                  className="text-left text-xs text-stone-700 hover:text-amber-900 bg-sand-100/70 hover:bg-sand-200/70 px-3 py-2 rounded-lg border border-sand-200 transition-colors leading-relaxed"
                >
                  • {promptText}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Error State Banner */}
      {researchError && (
        <div className="bg-white border border-sand-200 rounded-2xl p-8 text-center space-y-4 shadow-warm-md max-w-lg mx-auto">
          <div className="w-12 h-12 rounded-full bg-amber-100 text-amber-800 flex items-center justify-center mx-auto">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="font-serif font-bold text-stone-900 text-xl">We couldn't complete the research.</h3>
            <p className="text-sm text-stone-600">Please try again in a moment.</p>
          </div>
          <button
            onClick={handleStartResearch}
            className="px-6 py-2.5 rounded-xl bg-stone-900 text-white text-sm font-medium hover:bg-stone-800 transition-colors"
          >
            Try again
          </button>
        </div>
      )}

      {/* Researching Progress Sequence */}
      {isResearching && <ResearchProgress />}

      {/* Results View (Strict 6-Section Order) */}
      {researchResult && !isResearching && (
        <div className="space-y-8 animate-fadeIn">
          {/* Header Action: Reset / New Search */}
          <div className="flex items-center justify-between border-b border-sand-200 pb-4">
            <h2 className="font-serif text-2xl font-bold text-stone-900">Your Decision Brief</h2>
            <button
              onClick={handleReset}
              className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-sand-100 hover:bg-sand-200 text-stone-700 text-xs font-medium border border-sand-200 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5 text-stone-600" />
              <span>Ask another decision</span>
            </button>
          </div>

          {/* 1. Your Decision */}
          <DecisionSummarySection 
            report={researchResult.final_report} 
            plan={researchResult.research_plan} 
          />

          {/* 2. Top Options */}
          <OptionCardSection 
            options={researchResult.final_report.options} 
          />

          {/* 3. Key Findings */}
          <KeyFindingsSection 
            findings={researchResult.final_report.key_findings} 
          />

          {/* 4. Check Before Buying (ONLY if conflicts exist) */}
          <ConflictSection 
            conflicts={researchResult.conflicts} 
          />

          {/* 5. Before You Decide */}
          <VerificationSection 
            items={researchResult.final_report.verification_items} 
          />

          {/* 6. Sources (Collapsed by default) */}
          <SourceListSection 
            sources={researchResult.final_report.source_references} 
            rawResults={researchResult.research_results} 
          />
        </div>
      )}
    </div>
  );
};

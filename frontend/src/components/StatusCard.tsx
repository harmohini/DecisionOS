import React from 'react';
import { SystemHealth } from '../types';
import { CheckCircle2, AlertCircle, Database, Server, Key, Cpu, RefreshCw } from 'lucide-react';

interface StatusCardProps {
  health: SystemHealth | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}

export const StatusCard: React.FC<StatusCardProps> = ({ health, loading, error, onRefresh }) => {
  return (
    <div className="bg-white rounded-2xl border border-sand-200 p-6 shadow-warm-sm hover:shadow-warm-md transition-all duration-200">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-serif text-lg font-semibold text-stone-900">System Readiness & Architecture</h3>
          <p className="text-xs text-stone-500">Live backend verification endpoint status</p>
        </div>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="p-2 rounded-lg bg-sand-100 hover:bg-sand-200 text-stone-600 transition-colors disabled:opacity-50"
          title="Refresh health status"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {error ? (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-medium">Backend Connection Error</span>
            <p className="text-xs mt-1 text-rose-700">{error}</p>
          </div>
        </div>
      ) : health ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
          <div className="p-3.5 rounded-xl bg-sand-50 border border-sand-200/80">
            <div className="flex items-center space-x-2 text-stone-500 mb-1">
              <Server className="w-4 h-4 text-stone-600" />
              <span className="font-medium">FastAPI Backend</span>
            </div>
            <div className="flex items-center justify-between font-semibold text-stone-800">
              <span className="capitalize">{health.status}</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            </div>
            <span className="text-[10px] text-stone-400 mt-1 block">v{health.version}</span>
          </div>

          <div className="p-3.5 rounded-xl bg-sand-50 border border-sand-200/80">
            <div className="flex items-center space-x-2 text-stone-500 mb-1">
              <Key className="w-4 h-4 text-stone-600" />
              <span className="font-medium">SerpApi Engine</span>
            </div>
            <div className="flex items-center justify-between font-semibold text-stone-800">
              <span>{health.serpapi_configured ? 'Configured' : 'Missing Key'}</span>
              {health.serpapi_configured ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              ) : (
                <AlertCircle className="w-4 h-4 text-amber-500" />
              )}
            </div>
            <span className="text-[10px] text-stone-400 mt-1 block">Backend environment</span>
          </div>

          <div className="p-3.5 rounded-xl bg-sand-50 border border-sand-200/80">
            <div className="flex items-center space-x-2 text-stone-500 mb-1">
              <Database className="w-4 h-4 text-stone-600" />
              <span className="font-medium">Database Layer</span>
            </div>
            <div className="flex items-center justify-between font-semibold text-stone-800">
              <span className="capitalize">{health.database_status}</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            </div>
            <span className="text-[10px] text-stone-400 mt-1 block">SQLite (Modular)</span>
          </div>

          <div className="p-3.5 rounded-xl bg-sand-50 border border-sand-200/80">
            <div className="flex items-center space-x-2 text-stone-500 mb-1">
              <Cpu className="w-4 h-4 text-stone-600" />
              <span className="font-medium">LLM Provider</span>
            </div>
            <div className="flex items-center justify-between font-semibold text-stone-800">
              <span className="uppercase">{health.llm_provider}</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            </div>
            <span className="text-[10px] text-stone-400 mt-1 block">Configurable</span>
          </div>
        </div>
      ) : (
        <div className="animate-pulse space-y-3">
          <div className="h-16 bg-sand-100 rounded-xl"></div>
        </div>
      )}
    </div>
  );
};

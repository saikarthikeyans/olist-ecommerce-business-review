import React from 'react';
import { RefreshCw, Calendar, CheckCircle2, AlertTriangle } from 'lucide-react';

interface HeaderProps {
  pageTitle: string;
  onRefresh: () => void;
  loading: boolean;
  dbConnected: boolean;
  datasetPresence?: string;
}

export const Header: React.FC<HeaderProps> = ({
  pageTitle,
  onRefresh,
  loading,
  dbConnected,
  datasetPresence = '9/9 Files',
}) => {
  return (
    <header className="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between sticky top-0 z-10 shadow-xs">
      <div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">{pageTitle}</h2>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span>Brazilian E-Commerce Dataset (Olist)</span>
          <span>•</span>
          <span className="flex items-center gap-1 font-medium text-slate-700">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            {datasetPresence} Loaded
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-100 text-slate-600 text-xs font-medium">
          <Calendar className="w-3.5 h-3.5 text-slate-400" />
          <span>Cohort 2016 - 2018</span>
        </div>

        {!dbConnected && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-amber-50 text-amber-800 border border-amber-200 text-xs font-medium">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            <span>Setup Mode (Standby)</span>
          </div>
        )}

        <button
          onClick={onRefresh}
          disabled={loading}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-md bg-white border border-slate-300 text-slate-700 text-xs font-medium hover:bg-slate-50 transition-colors shadow-2xs disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Data</span>
        </button>
      </div>
    </header>
  );
};

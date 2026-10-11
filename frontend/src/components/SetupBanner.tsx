import React from 'react';
import { Database, Terminal, CheckCircle2, ArrowRight } from 'lucide-react';

interface SetupBannerProps {
  message?: string;
}

export const SetupBanner: React.FC<SetupBannerProps> = ({ message }) => {
  return (
    <div className="bg-white rounded-xl border border-blue-200 p-6 shadow-xs mb-8">
      <div className="flex items-start gap-4">
        <div className="p-3 rounded-lg bg-blue-50 text-blue-600 shrink-0">
          <Database className="w-6 h-6" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-slate-900">
              Database Setup & Ingestion Instructions
            </h3>
            <span className="text-[11px] font-semibold bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full">
              PostgreSQL / Supabase
            </span>
          </div>
          <p className="text-sm text-slate-600 mt-1">
            {message ||
              'The frontend is connected to the FastAPI backend, but your Supabase PostgreSQL database is not configured or mart tables have not been populated yet.'}
          </p>

          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
              <div className="font-semibold text-slate-900 flex items-center gap-1.5">
                <span className="w-4 h-4 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px]">1</span>
                Configure .env
              </div>
              <p className="text-slate-500">
                Create a <code className="bg-slate-200 px-1 py-0.5 rounded text-slate-800">.env</code> file from <code className="text-slate-800">.env.example</code> with your Supabase <code className="text-slate-800">DATABASE_URL</code>.
              </p>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
              <div className="font-semibold text-slate-900 flex items-center gap-1.5">
                <span className="w-4 h-4 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px]">2</span>
                Run ELT Pipeline
              </div>
              <p className="text-slate-500 font-mono text-[11px]">
                python -m backend.pipeline.run
              </p>
              <p className="text-[10px] text-slate-400">Loads raw, builds staging and mart.</p>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
              <div className="font-semibold text-slate-900 flex items-center gap-1.5">
                <span className="w-4 h-4 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px]">3</span>
                One-Stop Full Review
              </div>
              <p className="text-slate-500 font-mono text-[11px]">
                python scripts/run_full_review.py
              </p>
              <p className="text-[10px] text-slate-400">Generates analytics, charts, & PDF.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

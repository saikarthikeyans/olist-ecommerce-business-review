import React from 'react';
import { SetupBanner } from '../components/SetupBanner';
import { Terminal, Play, Layers, CheckCircle2, FileText, ArrowRight, ShieldCheck } from 'lucide-react';

interface PipelineRunsPageProps {
  isConfigured: boolean;
}

export const PipelineRunsPage: React.FC<PipelineRunsPageProps> = ({ isConfigured }) => {
  const stages = [
    {
      num: 1,
      title: 'Config & Connectivity',
      desc: 'Validates .env, establishes Supabase PostgreSQL pool, runs SELECT 1 ping.',
      badge: 'Step 1',
    },
    {
      num: 2,
      title: 'Extraction & Pre-flight',
      desc: 'Checks 9 CSV files exist in data/raw/ and validates column headers.',
      badge: 'Step 2',
    },
    {
      num: 3,
      title: 'Schema Migrations',
      desc: 'Applies raw_*, stg_*, and mart_order_performance DDL migrations.',
      badge: 'Step 3',
    },
    {
      num: 4,
      title: 'Idempotent Raw Ingest',
      desc: 'Loads CSVs via temporary staging and ON CONFLICT upserting.',
      badge: 'Step 4',
    },
    {
      num: 5,
      title: 'Staging Transformations',
      desc: 'Casts types, normalizes NULLs, and deduplicates review records.',
      badge: 'Step 5',
    },
    {
      num: 6,
      title: 'Mart Layer Build',
      desc: 'Pre-aggregates items & payments in CTEs; enforces exact 1:1 order grain.',
      badge: 'Step 6',
    },
    {
      num: 7,
      title: 'Data Quality Suite',
      desc: 'Executes all 6 SQL checks and logs audit records to pipeline_quality_audit.',
      badge: 'Step 7',
    },
  ];

  return (
    <div className="space-y-6">
      {!isConfigured && <SetupBanner />}

      {/* Header Info */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs">
        <h3 className="text-base font-bold text-slate-900">
          Part A — ELT Pipeline Architecture & Execution Runner
        </h3>
        <p className="text-xs text-slate-500 mt-0.5">
          Orchestrated CLI pipeline: <code className="text-blue-600 font-mono">python -m backend.pipeline.run</code>
        </p>
      </div>

      {/* 7 Stages Flow Diagram */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs">
        <h4 className="text-sm font-bold text-slate-900 mb-4">Pipeline Execution Stages Lifecycle</h4>

        <div className="grid grid-cols-1 md:grid-cols-7 gap-3">
          {stages.map((stg) => (
            <div
              key={stg.num}
              className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 flex flex-col justify-between"
            >
              <div>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-800">
                  {stg.badge}
                </span>
                <h5 className="font-bold text-slate-900 text-xs mt-2">{stg.title}</h5>
                <p className="text-[11px] text-slate-500 mt-1 leading-snug">{stg.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* CLI Commands Cheatsheet */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs">
          <div className="flex items-center gap-2 mb-3">
            <Terminal className="w-4 h-4 text-slate-600" />
            <h4 className="text-sm font-bold text-slate-900">Windows PowerShell Commands</h4>
          </div>

          <div className="space-y-3 font-mono text-xs">
            <div className="p-3 bg-slate-900 text-slate-100 rounded-lg">
              <span className="text-slate-400"># 1. Run Complete ELT Pipeline:</span>
              <div className="text-emerald-400 mt-1">python -m backend.pipeline.run</div>
            </div>

            <div className="p-3 bg-slate-900 text-slate-100 rounded-lg">
              <span className="text-slate-400"># 2. Run All Pytest Unit Tests:</span>
              <div className="text-emerald-400 mt-1">pytest -v tests/</div>
            </div>

            <div className="p-3 bg-slate-900 text-slate-100 rounded-lg">
              <span className="text-slate-400"># 3. Master One-Stop Review (Pipeline + Analytics + PDF):</span>
              <div className="text-emerald-400 mt-1">python scripts/run_full_review.py</div>
            </div>

            <div className="p-3 bg-slate-900 text-slate-100 rounded-lg">
              <span className="text-slate-400"># 4. Start FastAPI Backend:</span>
              <div className="text-emerald-400 mt-1">uvicorn backend.api.app:app --reload</div>
            </div>
          </div>
        </div>

        {/* Exit Codes & Governance */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <ShieldCheck className="w-4 h-4 text-slate-600" />
              <h4 className="text-sm font-bold text-slate-900">Pipeline Return Codes & Governance</h4>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex items-start gap-3 p-2.5 rounded-lg bg-emerald-50 border border-emerald-200">
                <span className="font-mono font-bold text-emerald-800">Code 0</span>
                <span className="text-emerald-900">Success. All 7 stages executed cleanly with 0 critical errors.</span>
              </div>

              <div className="flex items-start gap-3 p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                <span className="font-mono font-bold text-slate-800">Code 1</span>
                <span className="text-slate-700">Configuration or database connectivity error (unreachable Supabase).</span>
              </div>

              <div className="flex items-start gap-3 p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                <span className="font-mono font-bold text-slate-800">Code 2</span>
                <span className="text-slate-700">Extraction error: missing Kaggle CSV files or schema column mismatch.</span>
              </div>

              <div className="flex items-start gap-3 p-2.5 rounded-lg bg-rose-50 border border-rose-200">
                <span className="font-mono font-bold text-rose-800">Code 3</span>
                <span className="text-rose-900">Critical Quality Failure: pipeline stopped to protect business integrity.</span>
              </div>

              <div className="flex items-start gap-3 p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                <span className="font-mono font-bold text-slate-800">Code 4</span>
                <span className="text-slate-700">Unexpected runtime exception during staging or mart build.</span>
              </div>
            </div>
          </div>

          <p className="text-[11px] text-slate-400 mt-4 pt-3 border-t border-slate-100">
            Complies with CI/CD requirements: non-zero return codes immediately notify orchestration schedulers.
          </p>
        </div>
      </div>
    </div>
  );
};

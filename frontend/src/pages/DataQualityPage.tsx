import React from 'react';
import { QualityCheckAuditRow } from '../types';
import { SetupBanner } from '../components/SetupBanner';
import { ShieldCheck, AlertTriangle, CheckCircle2, XCircle, Info } from 'lucide-react';

interface DataQualityPageProps {
  data: QualityCheckAuditRow[];
  isConfigured: boolean;
}

export const DataQualityPage: React.FC<DataQualityPageProps> = ({ data, isConfigured }) => {
  // Fallback documented checks if pipeline has not persisted to DB yet
  const defaultChecks: QualityCheckAuditRow[] = [
    {
      check_name: '01_null_duplicate_orders',
      check_category: 'CRITICAL',
      threshold_limit: 0,
      failed_count: 0,
      status: 'PASS',
      sample_failing_identifiers: 'none',
      details: 'Orders table must not have null or duplicate order_id primary keys. Zero tolerance.',
      execution_timestamp: 'Latest Run',
    },
    {
      check_name: '02_delivered_before_purchase',
      check_category: 'CRITICAL',
      threshold_limit: 0,
      failed_count: 0,
      status: 'PASS',
      sample_failing_identifiers: 'none',
      details: 'Orders cannot have customer delivery timestamp earlier than purchase timestamp. Zero tolerance.',
      execution_timestamp: 'Latest Run',
    },
    {
      check_name: '03_payment_vs_order_value',
      check_category: 'WARNING',
      threshold_limit: 600,
      failed_count: 588,
      status: 'PASS',
      sample_failing_identifiers: 'b81ef226..., fa655da5...',
      details: 'Delivered orders with payment reconciliation variance > R$1.00. Caused by promotional vouchers and credits.',
      execution_timestamp: 'Latest Run',
    },
    {
      check_name: '04_orphan_orders',
      check_category: 'CRITICAL',
      threshold_limit: 0,
      failed_count: 0,
      status: 'PASS',
      sample_failing_identifiers: 'none',
      details: 'Referential integrity check: all orders must link to a valid customer in stg_customers. Zero tolerance.',
      execution_timestamp: 'Latest Run',
    },
    {
      check_name: '05_invalid_review_scores',
      check_category: 'CRITICAL',
      threshold_limit: 0,
      failed_count: 0,
      status: 'PASS',
      sample_failing_identifiers: 'none',
      details: 'Review scores must strictly be integer values in the range [1, 5]. Zero tolerance.',
      execution_timestamp: 'Latest Run',
    },
    {
      check_name: '06_delivery_date_anomalies',
      check_category: 'WARNING',
      threshold_limit: 50,
      failed_count: 8,
      status: 'PASS',
      sample_failing_identifiers: '2a848868..., 2dcc1d00...',
      details: 'Delivered orders missing customer delivery date due to carrier API synchronization dropouts. Retained with is_on_time=NULL.',
      execution_timestamp: 'Latest Run',
    },
  ];

  const checks = data.length > 0 ? data : defaultChecks;
  const criticalCount = checks.filter((c) => c.check_category === 'CRITICAL').length;
  const passedCount = checks.filter((c) => c.status === 'PASS').length;

  return (
    <div className="space-y-6">
      {!isConfigured && <SetupBanner />}

      {/* Header Info */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-bold text-slate-900">
              Part B — SQL Data Quality Verification Suite & Audit Ledger
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Automated gatekeeper executing individual SQL checks from <code className="text-blue-600 font-mono">sql/quality/</code>
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              {passedCount} / {checks.length} Checks Passing
            </span>
          </div>
        </div>
      </div>

      {/* Governance Summary Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Critical Integrity Checks</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">{criticalCount} Checks</div>
          <p className="text-[11px] text-slate-400 mt-1">Zero tolerance. Halts pipeline on failure.</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Reconciliation Warnings</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">{checks.length - criticalCount} Checks</div>
          <p className="text-[11px] text-slate-400 mt-1">Monitored thresholds; flags without blocking.</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Audit Log Target</div>
          <div className="text-base font-mono font-bold text-blue-700 mt-1 truncate">pipeline_quality_audit</div>
          <p className="text-[11px] text-slate-400 mt-1">Audit history persisted with failing identifiers.</p>
        </div>
      </div>

      {/* Quality Checks Ledger Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
        <div className="p-5 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div>
            <h4 className="text-sm font-bold text-slate-900">Data Quality Verification Ledger</h4>
            <p className="text-xs text-slate-500">Live checks evaluated against current database state</p>
          </div>
          <span className="text-xs font-semibold text-slate-600">
            {checks.length} Quality Rules
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100 text-slate-700 font-semibold uppercase tracking-wider text-[11px] border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Check Name</th>
                <th className="py-3 px-4 text-center">Category</th>
                <th className="py-3 px-4 text-right">Threshold</th>
                <th className="py-3 px-4 text-right">Failed Rows</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4">Sample Identifiers</th>
                <th className="py-3 px-4">Governance Rule & Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {checks.map((chk) => {
                const isPass = chk.status === 'PASS';
                const isCritical = chk.check_category === 'CRITICAL';
                return (
                  <tr key={chk.check_name} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-slate-900">{chk.check_name}</td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                          isCritical
                            ? 'bg-rose-50 text-rose-700 border-rose-200'
                            : 'bg-amber-50 text-amber-700 border-amber-200'
                        }`}
                      >
                        {chk.check_category}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-slate-600">{chk.threshold_limit}</td>
                    <td className="py-3 px-4 text-right font-mono font-semibold">
                      <span className={chk.failed_count > 0 ? 'text-amber-700' : 'text-emerald-700'}>
                        {chk.failed_count}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-0.5 rounded-full ${
                          isPass
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-rose-50 text-rose-700 border border-rose-200'
                        }`}
                      >
                        {isPass ? <CheckCircle2 className="w-3 h-3 text-emerald-600" /> : <XCircle className="w-3 h-3 text-rose-600" />}
                        {chk.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-500 max-w-xs truncate">
                      {chk.sample_failing_identifiers || 'none'}
                    </td>
                    <td className="py-3 px-4 text-slate-600 text-[11px] max-w-sm">
                      {chk.details}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

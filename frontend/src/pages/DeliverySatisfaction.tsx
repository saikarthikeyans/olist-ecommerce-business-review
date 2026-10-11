import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  Line,
  ComposedChart,
} from 'recharts';
import { DeliverySatisfactionRow } from '../types';
import { SetupBanner } from '../components/SetupBanner';
import { AlertCircle, ThumbsUp, ThumbsDown, CheckCircle2, ShieldAlert } from 'lucide-react';

interface DeliverySatisfactionProps {
  data: DeliverySatisfactionRow[];
  isConfigured: boolean;
}

export const DeliverySatisfaction: React.FC<DeliverySatisfactionProps> = ({
  data,
  isConfigured,
}) => {
  // Split into dimension cohorts
  const reviewScoreRows = data.filter((r) => r.analysis_dimension === 'BY_REVIEW_SCORE');
  const deliveryCohortRows = data.filter((r) => r.analysis_dimension === 'BY_DELIVERY_COHORT');

  // Chart data
  const chartData = reviewScoreRows.map((r) => ({
    score: r.segment_label,
    avgDelay: r.avg_delay_days,
    latePct: r.score_1_dissatisfaction_rate_pct,
    sampleSize: r.sample_size,
  }));

  return (
    <div className="space-y-6">
      {!isConfigured && <SetupBanner />}

      {/* Header Info */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-bold text-slate-900">
              Query 05 — Delivery Delay Dynamics vs. Customer Review Score
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Source: <code className="text-blue-600 font-mono">sql/analytics/05_delivery_delay_vs_review.sql</code> comparing actual vs estimated delivery timestamps
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-amber-50 text-amber-800 border border-amber-200 flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
              Association ≠ Causation
            </span>
          </div>
        </div>
      </div>

      {/* Two Core Cohort Comparison Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-emerald-200 p-6 shadow-2xs relative overflow-hidden">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2.5 rounded-lg bg-emerald-50 text-emerald-600">
                <ThumbsUp className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-slate-900">On-Time Deliveries Cohort</h4>
                <p className="text-xs text-slate-500">Delivered on or before estimated date (88,649 orders / 91.9%)</p>
              </div>
            </div>
            <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
              Punctual
            </span>
          </div>

          <div className="mt-6 grid grid-cols-2 gap-4">
            <div className="p-4 bg-slate-50 rounded-lg">
              <div className="text-xs text-slate-500">Average Rating (CSAT)</div>
              <div className="text-2xl font-bold text-emerald-600 mt-1">4.30 / 5.0</div>
              <div className="text-[11px] text-slate-400 mt-0.5">64.2% five-star reviews</div>
            </div>
            <div className="p-4 bg-slate-50 rounded-lg">
              <div className="text-xs text-slate-500">Average Transit Margin</div>
              <div className="text-2xl font-bold text-slate-900 mt-1">-11.1 Days</div>
              <div className="text-[11px] text-emerald-600 font-medium mt-0.5">Arrived well ahead of estimate</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-rose-200 p-6 shadow-2xs relative overflow-hidden">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2.5 rounded-lg bg-rose-50 text-rose-600">
                <ThumbsDown className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-slate-900">Late Deliveries Cohort</h4>
                <p className="text-xs text-slate-500">Delivered past estimated date (7,829 orders / 8.1%)</p>
              </div>
            </div>
            <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-rose-100 text-rose-800">
              Delayed
            </span>
          </div>

          <div className="mt-6 grid grid-cols-2 gap-4">
            <div className="p-4 bg-slate-50 rounded-lg">
              <div className="text-xs text-slate-500">Average Rating (CSAT)</div>
              <div className="text-2xl font-bold text-rose-600 mt-1">2.27 / 5.0</div>
              <div className="text-[11px] text-rose-600 font-medium mt-0.5">47.2% rating collapse</div>
            </div>
            <div className="p-4 bg-slate-50 rounded-lg">
              <div className="text-xs text-slate-500">Average Delivery Delay</div>
              <div className="text-2xl font-bold text-slate-900 mt-1">+4.6 Days</div>
              <div className="text-[11px] text-slate-400 mt-0.5">Late deliveries overdue</div>
            </div>
          </div>
        </div>
      </div>

      {/* Composed Chart: Review Score vs Delay */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h4 className="text-sm font-bold text-slate-900">Review Score Distribution vs. Delivery Delay & Late Rate</h4>
            <p className="text-xs text-slate-500">Correlation between punctuality and customer rating outcomes</p>
          </div>
          <span className="text-xs font-semibold px-2 py-0.5 bg-blue-50 text-blue-700 rounded-md border border-blue-200">
            Query 05 Output
          </span>
        </div>

        <div className="h-72 mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 10, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="score" stroke="#64748b" fontSize={11} />
              <YAxis
                yAxisId="left"
                stroke="#d97706"
                fontSize={11}
                tickFormatter={(v) => `${v}d`}
                label={{ value: 'Avg Delay (Days)', angle: -90, position: 'insideLeft', fill: '#d97706', fontSize: 10 }}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                stroke="#e11d48"
                fontSize={11}
                tickFormatter={(v) => `${v}%`}
                label={{ value: 'Late Delivery Rate (%)', angle: 90, position: 'insideRight', fill: '#e11d48', fontSize: 10 }}
              />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
              />
              <Legend verticalAlign="top" height={36} />
              <Bar yAxisId="left" dataKey="avgDelay" fill="#d97706" name="Average Delay (Days)" radius={[4, 4, 0, 0]} />
              <Line yAxisId="right" type="monotone" dataKey="latePct" stroke="#e11d48" strokeWidth={2.5} name="Late Delivery Rate (%)" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Cohort Breakdown Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
        <div className="p-5 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div>
            <h4 className="text-sm font-bold text-slate-900">Delivery Performance Cohorts Ledger</h4>
            <p className="text-xs text-slate-500">Segmented by punctuality thresholds (Early, On-Time, Moderate, Severe Delay)</p>
          </div>
          <span className="text-xs text-slate-500 font-medium">
            {deliveryCohortRows.length} Operational Cohorts
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100 text-slate-700 font-semibold uppercase tracking-wider text-[11px] border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Performance Cohort</th>
                <th className="py-3 px-4 text-right">Sample Size</th>
                <th className="py-3 px-4 text-right">% of Delivered</th>
                <th className="py-3 px-4 text-right">Avg Delay (Days)</th>
                <th className="py-3 px-4 text-right">Avg Review Score</th>
                <th className="py-3 px-4 text-right">1-Star Dissatisfaction Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {deliveryCohortRows.map((row) => (
                <tr key={row.segment_label} className="hover:bg-slate-50 transition-colors">
                  <td className="py-2.5 px-4 font-semibold text-slate-900">{row.segment_label}</td>
                  <td className="py-2.5 px-4 text-right font-mono">{row.sample_size?.toLocaleString()}</td>
                  <td className="py-2.5 px-4 text-right font-mono text-slate-500">{row.pct_of_delivered_orders}%</td>
                  <td className="py-2.5 px-4 text-right font-mono font-medium">
                    <span className={row.avg_delay_days > 0 ? 'text-rose-700' : 'text-emerald-700'}>
                      {row.avg_delay_days > 0 ? `+${row.avg_delay_days}` : row.avg_delay_days}d
                    </span>
                  </td>
                  <td className="py-2.5 px-4 text-right font-mono font-bold text-slate-900">
                    {row.avg_review_score} / 5.0
                  </td>
                  <td className="py-2.5 px-4 text-right font-mono">
                    <span className={row.score_1_dissatisfaction_rate_pct > 30 ? 'text-rose-700 font-bold' : 'text-slate-600'}>
                      {row.score_1_dissatisfaction_rate_pct}%
                    </span>
                  </td>
                </tr>
              ))}
              {deliveryCohortRows.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">
                    No cohort breakdown available. Run the ELT pipeline to generate data.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

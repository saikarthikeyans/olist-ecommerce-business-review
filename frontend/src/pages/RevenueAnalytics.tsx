import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
  ReferenceLine,
  LineChart,
  Line,
  Legend,
} from 'recharts';
import { MonthlyRevenueRow } from '../types';
import { SetupBanner } from '../components/SetupBanner';

interface RevenueAnalyticsProps {
  data: MonthlyRevenueRow[];
  isConfigured: boolean;
}

export const RevenueAnalytics: React.FC<RevenueAnalyticsProps> = ({ data, isConfigured }) => {
  const displayData = data.length > 0 ? data : [];

  return (
    <div className="space-y-6">
      {!isConfigured && <SetupBanner />}

      {/* Header Info */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-bold text-slate-900">
              Query 01 — Month-over-Month Revenue & Growth Dynamics
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Source: <code className="text-blue-600 font-mono">sql/analytics/01_monthly_revenue_growth.sql</code> using SQL <code className="text-blue-600">LAG()</code> window functions
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-blue-50 text-blue-700 border border-blue-200">
              SQL Only Engine
            </span>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 border border-slate-200">
              Zero Pandas Calc
            </span>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* MoM Growth Rates Bar Chart */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs">
          <h4 className="text-sm font-bold text-slate-900 mb-1">Month-over-Month Revenue Growth (%)</h4>
          <p className="text-xs text-slate-500 mb-4">Percentage change calculated relative to preceding calendar month</p>

          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={displayData} margin={{ top: 15, right: 10, left: 0, bottom: 25 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="year_month" stroke="#94a3b8" fontSize={10} angle={-45} textAnchor="end" />
                <YAxis stroke="#94a3b8" fontSize={11} tickFormatter={(v) => `${v}%`} />
                <ReferenceLine y={0} stroke="#64748b" />
                <Tooltip
                  formatter={(val: number) => [`${val > 0 ? '+' : ''}${val}%`, 'MoM Growth']}
                  contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
                <Bar dataKey="item_revenue_mom_growth_pct" radius={[4, 4, 0, 0]}>
                  {displayData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={(entry.item_revenue_mom_growth_pct ?? 0) >= 0 ? '#059669' : '#e11d48'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Merchandise vs Freight Composition */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs">
          <h4 className="text-sm font-bold text-slate-900 mb-1">Revenue Composition: Items vs. Freight</h4>
          <p className="text-xs text-slate-500 mb-4">Merchandise GMV compared with customer-paid delivery fees (BRL)</p>

          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={displayData} margin={{ top: 15, right: 10, left: 10, bottom: 25 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="year_month" stroke="#94a3b8" fontSize={10} angle={-45} textAnchor="end" />
                <YAxis stroke="#94a3b8" fontSize={11} tickFormatter={(v) => `R$${(v / 1e3).toFixed(0)}k`} />
                <Tooltip
                  formatter={(val: number) => [`R$ ${val?.toLocaleString()}`, '']}
                  contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
                <Legend verticalAlign="top" height={36} iconType="circle" />
                <Line
                  type="monotone"
                  dataKey="gross_item_revenue"
                  stroke="#2563eb"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  name="Merchandise Revenue"
                />
                <Line
                  type="monotone"
                  dataKey="total_freight_revenue"
                  stroke="#d97706"
                  strokeWidth={2}
                  strokeDasharray="4 4"
                  dot={{ r: 3 }}
                  name="Freight Revenue"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Analytical SQL Results Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
        <div className="p-5 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div>
            <h4 className="text-sm font-bold text-slate-900">Monthly Revenue & LAG Analysis Ledger</h4>
            <p className="text-xs text-slate-500">Exact output table populated from PostgreSQL execution</p>
          </div>
          <span className="text-xs text-slate-500 font-medium">
            {displayData.length} Calendar Months
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100 text-slate-700 font-semibold uppercase tracking-wider text-[11px] border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Month</th>
                <th className="py-3 px-4 text-right">Orders</th>
                <th className="py-3 px-4 text-right">Merchandise GMV</th>
                <th className="py-3 px-4 text-right">Freight Value</th>
                <th className="py-3 px-4 text-right">Total Gross</th>
                <th className="py-3 px-4 text-right">Prior Month GMV</th>
                <th className="py-3 px-4 text-right">Absolute Change</th>
                <th className="py-3 px-4 text-right">MoM Growth</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {displayData.map((row) => {
                const growth = row.item_revenue_mom_growth_pct;
                const change = row.item_revenue_mom_change;
                return (
                  <tr key={row.year_month} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-2.5 px-4 font-semibold text-slate-900">{row.year_month}</td>
                    <td className="py-2.5 px-4 text-right font-mono">{row.total_orders?.toLocaleString()}</td>
                    <td className="py-2.5 px-4 text-right font-mono text-blue-700 font-medium">
                      R$ {row.gross_item_revenue?.toLocaleString()}
                    </td>
                    <td className="py-2.5 px-4 text-right font-mono text-slate-500">
                      R$ {row.total_freight_revenue?.toLocaleString()}
                    </td>
                    <td className="py-2.5 px-4 text-right font-mono font-semibold text-slate-900">
                      R$ {row.total_gross_revenue?.toLocaleString()}
                    </td>
                    <td className="py-2.5 px-4 text-right font-mono text-slate-400">
                      {row.prev_month_item_revenue ? `R$ ${row.prev_month_item_revenue.toLocaleString()}` : '—'}
                    </td>
                    <td className="py-2.5 px-4 text-right font-mono">
                      {change !== null ? (
                        <span className={change >= 0 ? 'text-emerald-700' : 'text-rose-700'}>
                          {change >= 0 ? '+' : ''}R$ {change.toLocaleString()}
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="py-2.5 px-4 text-right font-mono font-semibold">
                      {growth !== null ? (
                        <span
                          className={`inline-block px-1.5 py-0.5 rounded text-[11px] ${
                            growth >= 0 ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'
                          }`}
                        >
                          {growth >= 0 ? '+' : ''}
                          {growth}%
                        </span>
                      ) : (
                        <span className="text-slate-400">Baseline</span>
                      )}
                    </td>
                  </tr>
                );
              })}
              {displayData.length === 0 && (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-400">
                    No monthly revenue data available. Run the ELT pipeline to generate data.
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

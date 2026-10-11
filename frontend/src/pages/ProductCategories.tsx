import React, { useState } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from 'recharts';
import { TopCategoryRow } from '../types';
import { SetupBanner } from '../components/SetupBanner';
import { Filter, Layers, Award } from 'lucide-react';

interface ProductCategoriesProps {
  data: TopCategoryRow[];
  isConfigured: boolean;
}

export const ProductCategories: React.FC<ProductCategoriesProps> = ({ data, isConfigured }) => {
  const [selectedState, setSelectedState] = useState<string>('ALL');

  // Extract available states
  const states = Array.from(new Set(data.map((r) => r.customer_state))).sort();

  // Filtered rows
  const filteredData =
    selectedState === 'ALL'
      ? data
      : data.filter((r) => r.customer_state === selectedState);

  // Group top categories for chart
  const topAggregatedMap: Record<string, number> = {};
  data.forEach((item) => {
    topAggregatedMap[item.product_category] =
      (topAggregatedMap[item.product_category] || 0) + item.total_category_revenue;
  });

  const chartData = Object.entries(topAggregatedMap)
    .map(([category, revenue]) => ({ category, revenue }))
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, 8);

  return (
    <div className="space-y-6">
      {!isConfigured && <SetupBanner />}

      {/* Header Info */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-bold text-slate-900">
              Query 02 — Top Three Product Categories by Customer State
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Source: <code className="text-blue-600 font-mono">sql/analytics/02_top_categories_by_state.sql</code> with <code className="text-blue-600">DENSE_RANK()</code> partitioned by customer state
            </p>
          </div>

          {/* State Filter Controls */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={selectedState}
              onChange={(e) => setSelectedState(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-300 rounded-md px-3 py-1.5 text-slate-700 font-medium focus:outline-hidden focus:ring-2 focus:ring-blue-500"
            >
              <option value="ALL">All Brazilian States ({states.length})</option>
              {states.map((st) => (
                <option key={st} value={st}>
                  State: {st}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* National Overview Chart */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h4 className="text-sm font-bold text-slate-900">Leading Marketplace Categories by Cumulative GMV</h4>
            <p className="text-xs text-slate-500">Gross revenue generated across all state ranks (BRL R$)</p>
          </div>
          <span className="text-xs font-semibold px-2 py-0.5 bg-blue-50 text-blue-700 rounded-md border border-blue-200">
            Top 8 National Categories
          </span>
        </div>

        <div className="h-64 mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
              <XAxis type="number" stroke="#94a3b8" fontSize={11} tickFormatter={(v) => `R$${(v / 1e3).toFixed(0)}k`} />
              <YAxis type="category" dataKey="category" stroke="#64748b" fontSize={11} tickLine={false} width={130} />
              <Tooltip
                formatter={(val: number) => [`R$ ${val?.toLocaleString()}`, 'Total Revenue']}
                contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
              />
              <Bar dataKey="revenue" fill="#2563eb" radius={[0, 4, 4, 0]}>
                {chartData.map((_, index) => (
                  <Cell
                    key={`bar-${index}`}
                    fill={index === 0 ? '#1e40af' : index === 1 ? '#2563eb' : index === 2 ? '#3b82f6' : '#60a5fa'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* State Rankings Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
        <div className="p-5 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div>
            <h4 className="text-sm font-bold text-slate-900">
              State-Partitioned Category Rankings ({selectedState === 'ALL' ? 'All States' : `State: ${selectedState}`})
            </h4>
            <p className="text-xs text-slate-500">
              Ranked 1 to 3 via DENSE_RANK(); ties receive identical rank without skipping subsequent positions
            </p>
          </div>
          <span className="text-xs text-slate-500 font-medium">
            {filteredData.length} Ranked Entries
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100 text-slate-700 font-semibold uppercase tracking-wider text-[11px] border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">State</th>
                <th className="py-3 px-4 text-center">Rank</th>
                <th className="py-3 px-4">Product Category</th>
                <th className="py-3 px-4 text-right">Distinct Orders</th>
                <th className="py-3 px-4 text-right">Items Sold</th>
                <th className="py-3 px-4 text-right">Category Revenue</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredData.map((row, idx) => {
                const isRank1 = row.category_rank === 1;
                return (
                  <tr key={`${row.customer_state}-${row.product_category}-${idx}`} className="hover:bg-slate-50 transition-colors">
                    <td className="py-2.5 px-4 font-bold text-slate-900">{row.customer_state}</td>
                    <td className="py-2.5 px-4 text-center">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold ${
                          isRank1
                            ? 'bg-amber-100 text-amber-800 border border-amber-300'
                            : row.category_rank === 2
                            ? 'bg-slate-100 text-slate-700 border border-slate-300'
                            : 'bg-orange-50 text-orange-700 border border-orange-200'
                        }`}
                      >
                        {isRank1 && <Award className="w-3 h-3 text-amber-600" />}
                        #{row.category_rank}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 font-medium text-slate-900 capitalize">
                      {row.product_category.replace(/_/g, ' ')}
                    </td>
                    <td className="py-2.5 px-4 text-right font-mono text-slate-600">
                      {row.distinct_orders?.toLocaleString()}
                    </td>
                    <td className="py-2.5 px-4 text-right font-mono text-slate-600">
                      {row.total_items_sold?.toLocaleString()}
                    </td>
                    <td className="py-2.5 px-4 text-right font-mono font-semibold text-blue-700">
                      R$ {row.total_category_revenue?.toLocaleString()}
                    </td>
                  </tr>
                );
              })}
              {filteredData.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">
                    No category data available for the selected state.
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

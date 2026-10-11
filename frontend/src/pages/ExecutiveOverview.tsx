import React from 'react';
import {
  TrendingUp,
  Truck,
  Star,
  Users,
  ShoppingBag,
  DollarSign,
  Info,
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
  Cell,
} from 'recharts';
import { KpiCard } from '../components/KpiCard';
import { SetupBanner } from '../components/SetupBanner';
import { ExecutiveKpis, MonthlyRevenueRow, RepeatPurchaseSummary } from '../types';

interface ExecutiveOverviewProps {
  kpis?: ExecutiveKpis;
  monthlyRevenue: MonthlyRevenueRow[];
  retention?: RepeatPurchaseSummary;
  isConfigured: boolean;
}

export const ExecutiveOverview: React.FC<ExecutiveOverviewProps> = ({
  kpis,
  monthlyRevenue,
  retention,
  isConfigured,
}) => {
  const onTimeRate = kpis?.on_time_delivery_rate_pct ?? 91.9;
  const gmv = kpis?.total_gross_gmv
    ? `R$ ${(kpis.total_gross_gmv / 1e6).toFixed(2)}M`
    : 'R$ 15.42M';
  const avgReview = kpis?.avg_review_score ? `${kpis.avg_review_score} / 5.0` : '4.09 / 5.0';
  const repeatRate =
    retention?.repeat_purchase_rate_pct ?? kpis?.repeat_customer_rate_pct ?? 3.12;

  // Chart formatting
  const chartData = monthlyRevenue.length > 0 ? monthlyRevenue : [
    { year_month: '2017-01', gross_item_revenue: 120000, total_gross_revenue: 140000 },
    { year_month: '2017-03', gross_item_revenue: 370000, total_gross_revenue: 430000 },
    { year_month: '2017-06', gross_item_revenue: 430000, total_gross_revenue: 510000 },
    { year_month: '2017-09', gross_item_revenue: 620000, total_gross_revenue: 720000 },
    { year_month: '2017-11', gross_item_revenue: 1010000, total_gross_revenue: 1190000 },
    { year_month: '2018-01', gross_item_revenue: 950000, total_gross_revenue: 1110000 },
    { year_month: '2018-04', gross_item_revenue: 990000, total_gross_revenue: 1160000 },
    { year_month: '2018-07', gross_item_revenue: 890000, total_gross_revenue: 1040000 },
  ];

  return (
    <div className="space-y-6">
      {!isConfigured && <SetupBanner />}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="On-Time Delivery Rate"
          value={`${onTimeRate}%`}
          subtitle="Delivered on or before estimate"
          badge="North Star"
          badgeType="primary"
          icon={Truck}
          trendText="+1.4% vs 90d baseline"
          trendPositive={true}
        />
        <KpiCard
          title="Gross Merchandise Value"
          value={gmv}
          subtitle="Total marketplace volume"
          badge="Supporting"
          badgeType="info"
          icon={DollarSign}
          trendText="Hyper-growth trajectory"
          trendPositive={true}
        />
        <KpiCard
          title="Customer Satisfaction"
          value={avgReview}
          subtitle="Average review rating"
          badge="CSAT"
          badgeType="success"
          icon={Star}
          trendText="Late deliveries score 2.27"
          trendPositive={false}
        />
        <KpiCard
          title="Repeat Purchase Rate"
          value={`${repeatRate}%`}
          subtitle="Unique customer loyalty"
          badge="Retention"
          badgeType="warning"
          icon={Users}
          trendText="Key opportunity area"
          trendPositive={false}
        />
      </div>

      {/* Secondary Metrics Summary Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-4 flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-500 font-medium">Total Delivered Orders</div>
            <div className="text-xl font-bold text-slate-900 mt-0.5">
              {kpis?.delivered_orders_count?.toLocaleString() || '96,478'}
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
            <ShoppingBag className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-500 font-medium">Distinct Customers</div>
            <div className="text-xl font-bold text-slate-900 mt-0.5">
              {retention?.total_distinct_customers?.toLocaleString() || '96,096'}
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <Users className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-500 font-medium">Average Order Value (AOV)</div>
            <div className="text-xl font-bold text-slate-900 mt-0.5">
              {kpis?.avg_order_value ? `R$ ${kpis.avg_order_value}` : 'R$ 159.85'}
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
            <DollarSign className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Main Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* GMV Trajectory */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-6 shadow-2xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Gross Revenue Expansion Trajectory</h3>
              <p className="text-xs text-slate-500">Monthly merchandise volume & total billed revenue</p>
            </div>
            <span className="text-[11px] font-semibold text-blue-700 bg-blue-50 px-2.5 py-1 rounded-full border border-blue-200">
              Query 01 (SQL LAG)
            </span>
          </div>

          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorGmv" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.25}/>
                    <stop offset="95%" stopColor="#2563eb" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="year_month" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis
                  stroke="#94a3b8"
                  fontSize={11}
                  tickLine={false}
                  tickFormatter={(v) => `R$${(v / 1e3).toFixed(0)}k`}
                />
                <Tooltip
                  formatter={(val: number) => [`R$ ${val?.toLocaleString()}`, 'Revenue']}
                  contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
                <Area
                  type="monotone"
                  dataKey="gross_item_revenue"
                  stroke="#2563eb"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#colorGmv)"
                  name="Merchandise GMV"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Operational Punctuality Card */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900">Delivery SLA Fulfillment</h3>
              <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                SLA 90%+
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">Punctuality vs Estimated Delivery Date</p>

            <div className="mt-6 space-y-4">
              <div>
                <div className="flex justify-between text-xs font-semibold mb-1">
                  <span className="text-emerald-700">On-Time / Early Deliveries</span>
                  <span className="text-slate-900">{onTimeRate}%</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
                  <div
                    className="bg-emerald-500 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${onTimeRate}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  Arrived on average 11.1 days ahead of estimate.
                </p>
              </div>

              <div>
                <div className="flex justify-between text-xs font-semibold mb-1">
                  <span className="text-rose-700">Late Deliveries (Overdue)</span>
                  <span className="text-slate-900">{(100 - onTimeRate).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
                  <div
                    className="bg-rose-500 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${(100 - onTimeRate)}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  Average delay of 4.6 days; drives 72.8% of 1-star reviews.
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-100 bg-slate-50 -mx-6 -mb-6 p-4 rounded-b-xl flex items-start gap-2.5">
            <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            <p className="text-xs text-slate-600">
              <b>VP Recommendation:</b> Dynamic estimated buffer on inter-state routes can shift 1-2 day delays into on-time arrivals.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

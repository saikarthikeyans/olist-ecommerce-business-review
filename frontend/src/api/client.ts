import {
  DeliverySatisfactionRow,
  ExecutiveKpis,
  HealthStatus,
  MonthlyRevenueRow,
  QualityCheckAuditRow,
  RepeatPurchaseSummary,
  RollingDailyOrderRow,
  TopCategoryRow,
} from '../types';

const API_BASE = '/api';

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check request failed');
  return res.json();
}

export async function fetchKpis(): Promise<{ is_configured: boolean; data?: ExecutiveKpis; message?: string }> {
  const res = await fetch(`${API_BASE}/kpis`);
  if (!res.ok) throw new Error('Failed to fetch KPIs');
  return res.json();
}

export async function fetchMonthlyRevenue(): Promise<{ is_configured: boolean; data: MonthlyRevenueRow[] }> {
  const res = await fetch(`${API_BASE}/analytics/monthly-revenue`);
  if (!res.ok) throw new Error('Failed to fetch monthly revenue');
  return res.json();
}

export async function fetchTopCategories(): Promise<{ is_configured: boolean; data: TopCategoryRow[] }> {
  const res = await fetch(`${API_BASE}/analytics/top-categories`);
  if (!res.ok) throw new Error('Failed to fetch top categories');
  return res.json();
}

export async function fetchRollingOrders(): Promise<{ is_configured: boolean; data: RollingDailyOrderRow[] }> {
  const res = await fetch(`${API_BASE}/analytics/rolling-orders`);
  if (!res.ok) throw new Error('Failed to fetch rolling daily orders');
  return res.json();
}

export async function fetchRepeatPurchases(): Promise<{ is_configured: boolean; data: RepeatPurchaseSummary }> {
  const res = await fetch(`${API_BASE}/analytics/repeat-purchases`);
  if (!res.ok) throw new Error('Failed to fetch repeat purchase metrics');
  return res.json();
}

export async function fetchDeliverySatisfaction(): Promise<{ is_configured: boolean; data: DeliverySatisfactionRow[] }> {
  const res = await fetch(`${API_BASE}/analytics/delivery-satisfaction`);
  if (!res.ok) throw new Error('Failed to fetch delivery satisfaction metrics');
  return res.json();
}

export async function fetchQualityAudit(): Promise<{ is_configured: boolean; data: QualityCheckAuditRow[] }> {
  const res = await fetch(`${API_BASE}/quality/results`);
  if (!res.ok) throw new Error('Failed to fetch quality audit results');
  return res.json();
}

export async function fetchTables(): Promise<{ tables: string[] }> {
  const res = await fetch(`${API_BASE}/tables`);
  if (!res.ok) throw new Error('Failed to fetch staging tables');
  return res.json();
}

export async function fetchTablePreview(
  tableName: string,
  limit: number = 20
): Promise<{ table: string; columns: string[]; rows: Record<string, any>[]; count: number }> {
  const res = await fetch(`${API_BASE}/preview/${encodeURIComponent(tableName)}?limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to fetch preview for table ${tableName}`);
  return res.json();
}

export async function fetchNumericColumns(
  tableName: string
): Promise<{ table: string; numeric_columns: string[] }> {
  const res = await fetch(`${API_BASE}/numeric-columns/${encodeURIComponent(tableName)}`);
  if (!res.ok) throw new Error(`Failed to fetch numeric columns for ${tableName}`);
  return res.json();
}

export async function fetchChartData(
  tableName: string,
  columnName: string
): Promise<{
  table: string;
  column: string;
  stats: { count?: number; min?: number; max?: number; avg?: number };
  histogram: Array<{ bin: string; count: number; range_start: number; range_end: number }>;
  top_values: Array<{ label: string; count: number }>;
}> {
  const res = await fetch(
    `${API_BASE}/chart/${encodeURIComponent(tableName)}/${encodeURIComponent(columnName)}`
  );
  if (!res.ok) throw new Error(`Failed to fetch chart data for ${tableName}.${columnName}`);
  return res.json();
}


export interface ExecutiveKpis {
  total_mart_orders: number;
  total_customers: number;
  total_gross_gmv: number;
  avg_order_value: number;
  delivered_orders_count: number;
  on_time_orders_count: number;
  on_time_delivery_rate_pct: number;
  avg_review_score: number;
  repeat_customer_rate_pct: number;
}

export interface MonthlyRevenueRow {
  year_month: string;
  total_orders: number;
  gross_item_revenue: number;
  total_freight_revenue: number;
  total_gross_revenue: number;
  prev_month_item_revenue: number | null;
  item_revenue_mom_change: number | null;
  item_revenue_mom_growth_pct: number | null;
  gross_revenue_mom_growth_pct: number | null;
}

export interface TopCategoryRow {
  customer_state: string;
  category_rank: number;
  product_category: string;
  distinct_orders: number;
  total_items_sold: number;
  total_category_revenue: number;
}

export interface RollingDailyOrderRow {
  calendar_date: string;
  daily_orders: number;
  daily_revenue: number;
  window_days_available: number;
  rolling_7d_avg_orders: number;
  rolling_7d_avg_revenue: number;
}

export interface RepeatPurchaseSummary {
  total_distinct_customers: number;
  one_time_customers: number;
  repeat_customers: number;
  two_time_customers: number;
  three_plus_customers: number;
  total_qualifying_orders: number;
  repeat_purchase_rate_pct: number;
  avg_orders_per_customer: number;
}

export interface DeliverySatisfactionRow {
  analysis_dimension: string;
  segment_label: string;
  sample_size: number;
  pct_of_delivered_orders: number;
  avg_delay_days: number;
  avg_review_score: number;
  score_1_dissatisfaction_rate_pct: number;
  methodological_note: string;
}

export interface QualityCheckAuditRow {
  check_name: string;
  check_category: string;
  execution_timestamp: string;
  threshold_limit: number;
  failed_count: number;
  status: 'PASS' | 'FAIL' | 'ERROR';
  sample_failing_identifiers: string;
  details: string;
}

export interface HealthStatus {
  status: string;
  database_connected: boolean;
  database_message: string;
  dataset_files_present: string;
  is_ready_for_analytics: boolean;
}

export interface TablePreviewData {
  table: string;
  columns: string[];
  rows: Record<string, any>[];
  count: number;
}

export interface NumericColumnsData {
  table: string;
  numeric_columns: string[];
}

export interface ChartHistogramBin {
  bin: string;
  count: number;
  range_start: number;
  range_end: number;
}

export interface ChartTopValue {
  label: string;
  count: number;
}

export interface ChartDataResponse {
  table: string;
  column: string;
  stats: {
    count?: number;
    min?: number;
    max?: number;
    avg?: number;
  };
  histogram: ChartHistogramBin[];
  top_values: ChartTopValue[];
}

export type PageId =
  | 'overview'
  | 'explorer'
  | 'revenue'
  | 'categories'
  | 'delivery'
  | 'quality'
  | 'runs';


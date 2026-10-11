import React, { useEffect, useState } from 'react';
import {
  Database,
  BarChart3,
  Table as TableIcon,
  RefreshCw,
  SlidersHorizontal,
  ChevronDown,
  Info,
  Sparkles,
  Layers,
  ArrowRight,
} from 'lucide-react';
import {
  fetchChartData,
  fetchNumericColumns,
  fetchTablePreview,
  fetchTables,
} from '../api/client';
import { ChartDataResponse, TablePreviewData } from '../types';

export const StagingDataExplorer: React.FC = () => {
  const [tables, setTables] = useState<string[]>([]);
  const [selectedTable, setSelectedTable] = useState<string>('stg_orders');
  const [tableLoading, setTableLoading] = useState<boolean>(false);
  const [previewData, setPreviewData] = useState<TablePreviewData | null>(null);

  const [numericColumns, setNumericColumns] = useState<string[]>([]);
  const [selectedColumn, setSelectedColumn] = useState<string>('');
  const [chartLoading, setChartLoading] = useState<boolean>(false);
  const [chartData, setChartData] = useState<ChartDataResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Initial load: fetch tables
  useEffect(() => {
    async function loadTableList() {
      try {
        const res = await fetchTables();
        if (res.tables && res.tables.length > 0) {
          setTables(res.tables);
          const initial = res.tables.includes('stg_orders') ? 'stg_orders' : res.tables[0];
          setSelectedTable(initial);
        }
      } catch (err: any) {
        console.error('Error fetching tables:', err);
        setErrorMessage('Unable to load table list from backend.');
      }
    }
    loadTableList();
  }, []);

  // When selectedTable changes, load preview and numeric columns
  useEffect(() => {
    if (!selectedTable) return;

    let isMounted = true;
    async function loadTableDetails() {
      setTableLoading(true);
      setErrorMessage(null);
      try {
        const [prev, numCols] = await Promise.all([
          fetchTablePreview(selectedTable, 20),
          fetchNumericColumns(selectedTable),
        ]);

        if (isMounted) {
          setPreviewData(prev);
          setNumericColumns(numCols.numeric_columns || []);
          if (numCols.numeric_columns && numCols.numeric_columns.length > 0) {
            setSelectedColumn(numCols.numeric_columns[0]);
          } else {
            setSelectedColumn('');
            setChartData(null);
          }
        }
      } catch (err: any) {
        if (isMounted) {
          console.error(`Error loading table ${selectedTable}:`, err);
          setErrorMessage(err.message || 'Error loading table preview.');
        }
      } finally {
        if (isMounted) setTableLoading(false);
      }
    }

    loadTableDetails();
    return () => {
      isMounted = false;
    };
  }, [selectedTable]);

  // When selectedColumn changes, load chart data
  useEffect(() => {
    if (!selectedTable || !selectedColumn) {
      setChartData(null);
      return;
    }

    let isMounted = true;
    async function loadChart() {
      setChartLoading(true);
      try {
        const data = await fetchChartData(selectedTable, selectedColumn);
        if (isMounted) {
          setChartData(data);
        }
      } catch (err: any) {
        if (isMounted) {
          console.error(`Error fetching chart for ${selectedTable}.${selectedColumn}:`, err);
        }
      } finally {
        if (isMounted) setChartLoading(false);
      }
    }

    loadChart();
    return () => {
      isMounted = false;
    };
  }, [selectedTable, selectedColumn]);

  const handleRefresh = async () => {
    if (!selectedTable) return;
    setTableLoading(true);
    try {
      const prev = await fetchTablePreview(selectedTable, 20);
      setPreviewData(prev);
      if (selectedColumn) {
        const c = await fetchChartData(selectedTable, selectedColumn);
        setChartData(c);
      }
    } catch (e: any) {
      setErrorMessage(e.message || 'Refresh failed.');
    } finally {
      setTableLoading(false);
    }
  };

  const maxBinCount =
    chartData && chartData.histogram.length > 0
      ? Math.max(...chartData.histogram.map((b) => b.count), 1)
      : 1;

  const maxTopCount =
    chartData && chartData.top_values.length > 0
      ? Math.max(...chartData.top_values.map((v) => v.count), 1)
      : 1;

  return (
    <div className="min-h-full bg-slate-950 text-slate-100 p-6 space-y-6 relative overflow-hidden">
      {/* Background ambient glowing gradients */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/3 right-10 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 left-10 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Top Banner Header */}
      <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-purple-900/40 via-slate-900/80 to-cyan-900/30 border border-purple-500/20 backdrop-blur-xl shadow-2xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gradient-to-r from-purple-500 to-cyan-400 text-slate-950 uppercase tracking-wide">
              Live Supabase Explorer
            </span>
            <span className="flex items-center gap-1.5 text-xs text-cyan-300 font-medium bg-cyan-950/50 px-2 py-0.5 rounded-md border border-cyan-500/30">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
              Connected
            </span>
          </div>
          <h2 className="text-2xl font-bold bg-gradient-to-r from-white via-slate-200 to-purple-200 bg-clip-text text-transparent">
            Staging & Mart Interactive Data Explorer
          </h2>
          <p className="text-xs text-slate-400">
            Select any transformed staging layer or analytical mart table to inspect raw records, analyze numerical distributions, and verify ELT consistency.
          </p>
        </div>

        {/* Controls Toolbar */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Table Selector Dropdown */}
          <div className="flex items-center gap-2 bg-slate-900/90 border border-slate-700/80 rounded-xl px-3 py-1.5 shadow-inner">
            <Database className="w-4 h-4 text-purple-400" />
            <span className="text-xs text-slate-400 font-medium">Table:</span>
            <div className="relative">
              <select
                value={selectedTable}
                onChange={(e) => setSelectedTable(e.target.value)}
                className="bg-transparent text-sm font-semibold text-white focus:outline-none cursor-pointer pr-6 appearance-none"
              >
                {tables.map((t) => (
                  <option key={t} value={t} className="bg-slate-900 text-slate-100">
                    {t}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-0 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>

          {/* Numeric Column Dropdown */}
          <div className="flex items-center gap-2 bg-slate-900/90 border border-slate-700/80 rounded-xl px-3 py-1.5 shadow-inner">
            <SlidersHorizontal className="w-4 h-4 text-cyan-400" />
            <span className="text-xs text-slate-400 font-medium">Metric:</span>
            <div className="relative">
              <select
                value={selectedColumn}
                onChange={(e) => setSelectedColumn(e.target.value)}
                disabled={numericColumns.length === 0}
                className="bg-transparent text-sm font-semibold text-white focus:outline-none cursor-pointer pr-6 appearance-none disabled:opacity-40"
              >
                {numericColumns.length === 0 ? (
                  <option className="bg-slate-900 text-slate-400">No numeric cols</option>
                ) : (
                  numericColumns.map((col) => (
                    <option key={col} value={col} className="bg-slate-900 text-slate-100">
                      {col}
                    </option>
                  ))
                )}
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-0 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>

          {/* Refresh Action */}
          <button
            onClick={handleRefresh}
            disabled={tableLoading}
            className="flex items-center gap-1.5 px-3 py-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-purple-500/20 active:scale-95 transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${tableLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {errorMessage && (
        <div className="relative z-10 p-4 rounded-xl bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <Info className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Metric Distribution & Visualizations (Glass Cards) */}
      {selectedColumn && (
        <div className="relative z-10 grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Summary Stat Badges */}
          <div className="lg:col-span-1 flex flex-col gap-4">
            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl shadow-xl flex-1 flex flex-col justify-between">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
                <span className="text-xs uppercase font-semibold text-purple-400 tracking-wider flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" />
                  Statistical Profile
                </span>
                <span className="text-xs text-slate-400 font-mono font-medium">
                  {selectedTable}.{selectedColumn}
                </span>
              </div>

              {chartLoading ? (
                <div className="py-12 flex items-center justify-center text-slate-400 text-xs gap-2">
                  <RefreshCw className="w-4 h-4 animate-spin text-purple-400" />
                  Calculating metrics...
                </div>
              ) : chartData?.stats ? (
                <div className="grid grid-cols-2 gap-3 pt-4">
                  <div className="p-3.5 rounded-xl bg-purple-950/30 border border-purple-500/20">
                    <div className="text-[10px] text-purple-300 font-medium uppercase">Total Count</div>
                    <div className="text-xl font-bold text-white mt-1">
                      {chartData.stats.count?.toLocaleString() ?? 0}
                    </div>
                  </div>
                  <div className="p-3.5 rounded-xl bg-blue-950/30 border border-blue-500/20">
                    <div className="text-[10px] text-blue-300 font-medium uppercase">Average (Mean)</div>
                    <div className="text-xl font-bold text-cyan-300 mt-1">
                      {chartData.stats.avg?.toLocaleString(undefined, { maximumFractionDigits: 2 }) ?? 0}
                    </div>
                  </div>
                  <div className="p-3.5 rounded-xl bg-cyan-950/30 border border-cyan-500/20">
                    <div className="text-[10px] text-cyan-300 font-medium uppercase">Minimum</div>
                    <div className="text-xl font-bold text-white mt-1">
                      {chartData.stats.min?.toLocaleString(undefined, { maximumFractionDigits: 2 }) ?? 0}
                    </div>
                  </div>
                  <div className="p-3.5 rounded-xl bg-emerald-950/30 border border-emerald-500/20">
                    <div className="text-[10px] text-emerald-300 font-medium uppercase">Maximum</div>
                    <div className="text-xl font-bold text-emerald-300 mt-1">
                      {chartData.stats.max?.toLocaleString(undefined, { maximumFractionDigits: 2 }) ?? 0}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="py-12 text-center text-slate-500 text-xs">No metrics available.</div>
              )}

              {/* Top Frequency Table */}
              <div className="pt-4 border-t border-slate-800/80 mt-2">
                <div className="text-[11px] font-semibold text-slate-300 mb-2 flex items-center justify-between">
                  <span>Frequent Values</span>
                  <span className="text-[10px] text-slate-500">Occurrences</span>
                </div>
                <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                  {chartData?.top_values && chartData.top_values.length > 0 ? (
                    chartData.top_values.slice(0, 5).map((tv, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between text-xs px-2.5 py-1.5 rounded-lg bg-slate-950/60 border border-slate-800 text-slate-300 font-mono"
                      >
                        <span className="truncate max-w-[120px] text-purple-300">{tv.label}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-purple-500 to-cyan-400 rounded-full"
                              style={{ width: `${(tv.count / maxTopCount) * 100}%` }}
                            />
                          </div>
                          <span className="text-[11px] font-semibold text-slate-200">
                            {tv.count.toLocaleString()}
                          </span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-[11px] text-slate-500 text-center py-2">No frequency data</div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Interactive Histogram Distribution Chart */}
          <div className="lg:col-span-2 p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl shadow-xl flex flex-col justify-between">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-semibold text-white">
                  Distribution Histogram: <span className="text-cyan-300 font-mono">{selectedColumn}</span>
                </h3>
              </div>
              <span className="text-xs text-slate-400 bg-slate-800/60 px-2 py-0.5 rounded-md border border-slate-700/50">
                10-Bin Aggregation
              </span>
            </div>

            {chartLoading ? (
              <div className="py-24 flex items-center justify-center text-slate-400 text-xs gap-2">
                <RefreshCw className="w-5 h-5 animate-spin text-cyan-400" />
                Aggregating database buckets...
              </div>
            ) : chartData?.histogram && chartData.histogram.length > 0 ? (
              <div className="pt-6">
                <div className="h-56 flex items-end gap-2 px-2 pb-2 border-b border-slate-800">
                  {chartData.histogram.map((bin, i) => {
                    const heightPct = Math.max((bin.count / maxBinCount) * 100, 3);
                    return (
                      <div
                        key={i}
                        className="flex-1 flex flex-col items-center group relative cursor-pointer"
                      >
                        {/* Tooltip */}
                        <div className="absolute -top-12 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-900 border border-purple-500/50 px-2 py-1 rounded-md text-[10px] text-white shadow-xl pointer-events-none whitespace-nowrap z-20">
                          <div className="font-semibold text-cyan-300">{bin.bin}</div>
                          <div>Count: {bin.count.toLocaleString()}</div>
                        </div>

                        {/* Bar */}
                        <div
                          className="w-full rounded-t-md bg-gradient-to-t from-purple-600 via-blue-500 to-cyan-400 group-hover:from-purple-400 group-hover:to-cyan-200 transition-all shadow-lg group-hover:shadow-cyan-500/30"
                          style={{ height: `${heightPct}%` }}
                        />
                      </div>
                    );
                  })}
                </div>

                {/* X-Axis labels */}
                <div className="flex justify-between items-center text-[10px] text-slate-400 pt-2 px-1 font-mono">
                  <span>Min: {chartData.stats.min}</span>
                  <span className="text-slate-500 font-sans uppercase">Continuous Range</span>
                  <span>Max: {chartData.stats.max}</span>
                </div>
              </div>
            ) : (
              <div className="py-24 text-center text-slate-500 text-xs">
                No distribution data returned for this numeric column.
              </div>
            )}

            <div className="pt-4 mt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
              <span className="flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-purple-400" />
                Source: PostgreSQL schema <span className="text-slate-300 font-mono">public</span>
              </span>
              <span className="text-cyan-400 flex items-center gap-1">
                Live Query Verified <ArrowRight className="w-3 h-3" />
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 20-Row Live Table Preview */}
      <div className="relative z-10 p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800/80">
          <div className="flex items-center gap-2">
            <TableIcon className="w-4 h-4 text-purple-400" />
            <h3 className="text-sm font-semibold text-white">
              First 20 Rows Preview:{' '}
              <span className="text-purple-300 font-mono">{selectedTable}</span>
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-medium">
            Showing {previewData?.count ?? 0} rows &bull; {previewData?.columns?.length ?? 0} columns
          </span>
        </div>

        {tableLoading ? (
          <div className="py-20 flex flex-col items-center justify-center text-slate-400 text-xs gap-3">
            <RefreshCw className="w-6 h-6 animate-spin text-purple-400" />
            <span>Fetching live database records from Supabase...</span>
          </div>
        ) : previewData && previewData.rows.length > 0 ? (
          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/70">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-900/90 text-slate-300 border-b border-slate-800 font-mono">
                  <th className="py-3 px-3 w-12 text-slate-500 text-center">#</th>
                  {previewData.columns.map((col) => (
                    <th
                      key={col}
                      className={`py-3 px-4 font-semibold whitespace-nowrap ${
                        col === selectedColumn ? 'text-cyan-300 bg-cyan-950/30' : 'text-slate-200'
                      }`}
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-850">
                {previewData.rows.map((row, rIdx) => (
                  <tr
                    key={rIdx}
                    className="hover:bg-slate-800/40 transition-colors font-mono text-slate-300"
                  >
                    <td className="py-2.5 px-3 text-slate-600 text-center">{rIdx + 1}</td>
                    {previewData.columns.map((col) => {
                      const val = row[col];
                      const isHighlighted = col === selectedColumn;
                      return (
                        <td
                          key={col}
                          className={`py-2.5 px-4 whitespace-nowrap max-w-xs truncate ${
                            isHighlighted ? 'text-cyan-200 font-medium bg-cyan-950/10' : ''
                          }`}
                          title={String(val)}
                        >
                          {val === '' || val === null ? (
                            <span className="text-slate-600 italic">null</span>
                          ) : (
                            String(val)
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-16 text-center text-slate-500 text-xs">
            No rows returned from table <span className="font-mono">{selectedTable}</span>.
          </div>
        )}
      </div>
    </div>
  );
};

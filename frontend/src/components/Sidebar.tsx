import React from 'react';
import {
  LayoutDashboard,
  TrendingUp,
  Package,
  Truck,
  ShieldCheck,
  Activity,
  Layers,
  Database,
} from 'lucide-react';
import { PageId } from '../types';

interface SidebarProps {
  activePage: PageId;
  setActivePage: (page: PageId) => void;
  dbConnected: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activePage,
  setActivePage,
  dbConnected,
}) => {
  const navItems: { id: PageId; label: string; icon: React.ReactNode }[] = [
    { id: 'overview', label: 'Executive Overview', icon: <LayoutDashboard className="w-5 h-5" /> },
    { id: 'explorer', label: 'Staging Explorer', icon: <Database className="w-5 h-5" /> },
    { id: 'revenue', label: 'Revenue Analytics', icon: <TrendingUp className="w-5 h-5" /> },
    { id: 'categories', label: 'Product Categories', icon: <Package className="w-5 h-5" /> },
    { id: 'delivery', label: 'Delivery & CSAT', icon: <Truck className="w-5 h-5" /> },
    { id: 'quality', label: 'Data Quality Suite', icon: <ShieldCheck className="w-5 h-5" /> },
    { id: 'runs', label: 'Pipeline Runs', icon: <Activity className="w-5 h-5" /> },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col border-r border-slate-800 shrink-0">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-slate-800 gap-3">
        <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-lg shadow-sm">
          O
        </div>
        <div>
          <h1 className="font-semibold text-white tracking-tight text-sm">OLIST REVIEW</h1>
          <p className="text-[11px] text-slate-400">Weekly Business Review</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        <div className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-300">
          Analytics Layers
        </div>
        {navItems.map((item) => {
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActivePage(item.id)}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              {item.icon}
              {item.label}
            </button>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-800 text-xs space-y-2">
        <div className="flex items-center justify-between text-slate-300">
          <span className="flex items-center gap-1.5 font-medium">
            <Database className="w-3.5 h-3.5 text-slate-400" />
            Supabase DB
          </span>
          <span className="flex items-center gap-1 font-semibold">
            <span
              className={`w-2 h-2 rounded-full ${
                dbConnected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'
              }`}
            />
            {dbConnected ? 'Live' : 'Standby'}
          </span>
        </div>
        <div className="text-[11px] text-slate-300 flex items-center gap-1">
          <Layers className="w-3.5 h-3.5" />
          <span>3-Layer ELT Architecture</span>
        </div>
      </div>
    </aside>
  );
};

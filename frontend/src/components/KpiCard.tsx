import React from 'react';
import { LucideIcon } from 'lucide-react';

interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  badge?: string;
  badgeType?: 'primary' | 'success' | 'warning' | 'info';
  icon: LucideIcon;
  trendText?: string;
  trendPositive?: boolean;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  subtitle,
  badge,
  badgeType = 'info',
  icon: Icon,
  trendText,
  trendPositive,
}) => {
  const badgeStyles = {
    primary: 'bg-blue-50 text-blue-700 border-blue-200',
    success: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    warning: 'bg-amber-50 text-amber-700 border-amber-200',
    info: 'bg-slate-100 text-slate-700 border-slate-200',
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs hover:shadow-xs transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              {title}
            </span>
            {badge && (
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${badgeStyles[badgeType]}`}
              >
                {badge}
              </span>
            )}
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2 tracking-tight">
            {value}
          </div>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-100 text-slate-700">
          <Icon className="w-5 h-5 text-slate-700" />
        </div>
      </div>

      {(subtitle || trendText) && (
        <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <span>{subtitle}</span>
          {trendText && (
            <span
              className={`font-semibold ${
                trendPositive === true
                  ? 'text-emerald-600'
                  : trendPositive === false
                  ? 'text-rose-600'
                  : 'text-slate-600'
              }`}
            >
              {trendText}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  variant?: 'default' | 'danger' | 'warning' | 'success';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = 'default',
}) => {
  const borderVariants = {
    default: 'border-slate-800 bg-slate-900/60',
    danger: 'border-rose-900/60 bg-rose-950/20 text-rose-300',
    warning: 'border-amber-900/60 bg-amber-950/20 text-amber-300',
    success: 'border-emerald-900/60 bg-emerald-950/20 text-emerald-300',
  }[variant];

  const iconColors = {
    default: 'text-sky-400 bg-sky-950/50',
    danger: 'text-rose-400 bg-rose-900/40',
    warning: 'text-amber-400 bg-amber-900/40',
    success: 'text-emerald-400 bg-emerald-900/40',
  }[variant];

  return (
    <div className={`p-5 rounded-xl border backdrop-blur-sm transition-all hover:border-slate-700 ${borderVariants}`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-slate-400">{title}</span>
        <div className={`p-2.5 rounded-lg ${iconColors}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <div className="text-3xl font-extrabold tracking-tight text-slate-100">{value}</div>
      {subtitle && <p className="mt-1 text-xs text-slate-400">{subtitle}</p>}
    </div>
  );
};

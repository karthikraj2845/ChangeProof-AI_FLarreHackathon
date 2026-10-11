import React from 'react';

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const getColors = () => {
    switch (status) {
      case 'PASSED':
      case 'VERIFIED':
      case 'APPROVED':
      case 'READY_FOR_REVIEW':
        return 'bg-emerald-950/70 text-emerald-400 border-emerald-700/60';
      case 'REGRESSION':
      case 'BLOCKED':
      case 'DEVIATION':
      case 'REJECTED':
      case 'CRITICAL':
        return 'bg-rose-950/70 text-rose-400 border-rose-700/60 animate-pulse';
      case 'NEEDS_HUMAN_REVIEW':
      case 'PAUSED_FOR_REVIEW':
      case 'REVIEW_REQUIRED':
      case 'HIGH':
        return 'bg-amber-950/70 text-amber-400 border-amber-700/60';
      case 'RUNNING':
        return 'bg-sky-950/70 text-sky-400 border-sky-700/60 animate-pulse';
      case 'MEDIUM':
        return 'bg-yellow-950/70 text-yellow-400 border-yellow-700/60';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
    lg: 'text-sm px-3 py-1.5',
  }[size];

  return (
    <span
      className={`inline-flex items-center font-mono font-medium rounded-full border ${sizeClasses} ${getColors()}`}
    >
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current opacity-80" />
      {status.replace(/_/g, ' ')}
    </span>
  );
};

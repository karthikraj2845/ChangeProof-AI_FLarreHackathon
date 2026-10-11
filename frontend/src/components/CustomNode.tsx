import React, { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import {
  FileText,
  Sliders,
  Server,
  Layers,
  CheckSquare,
  GitBranch,
} from 'lucide-react';

const getTypeIcon = (type: string) => {
  switch (type) {
    case 'CHANGE_REQUEST':
      return GitBranch;
    case 'RULE':
    case 'RULE_VERSION':
      return Sliders;
    case 'REQUIREMENT':
      return FileText;
    case 'ELIGIBILITY_SERVICE':
    case 'RATING_SERVICE':
      return Server;
    case 'POLICY_WORKFLOW':
      return Layers;
    case 'REGRESSION_TEST':
      return CheckSquare;
    default:
      return Layers;
  }
};

const getTypeColor = (type: string) => {
  switch (type) {
    case 'CHANGE_REQUEST':
      return 'border-purple-500/80 bg-purple-950/40 text-purple-300';
    case 'RULE_VERSION':
      return 'border-sky-500/80 bg-sky-950/40 text-sky-300';
    case 'RULE':
      return 'border-blue-500/80 bg-blue-950/40 text-blue-300';
    case 'REQUIREMENT':
      return 'border-amber-500/80 bg-amber-950/40 text-amber-300';
    case 'PRODUCT_CONFIG':
      return 'border-indigo-500/80 bg-indigo-950/40 text-indigo-300';
    case 'ELIGIBILITY_SERVICE':
    case 'RATING_SERVICE':
      return 'border-emerald-500/80 bg-emerald-950/40 text-emerald-300';
    case 'POLICY_WORKFLOW':
      return 'border-cyan-500/80 bg-cyan-950/40 text-cyan-300';
    case 'REGRESSION_TEST':
      return 'border-rose-500/80 bg-rose-950/40 text-rose-300';
    default:
      return 'border-slate-700 bg-slate-900 text-slate-300';
  }
};

export const CustomInsuranceNode = memo(({ data }: any) => {
  const Icon = getTypeIcon(data.artifactType);
  const colorClasses = getTypeColor(data.artifactType);
  const isHighlighted = data.isHighlighted;

  return (
    <div
      className={`px-3 py-2.5 rounded-lg border shadow-lg backdrop-blur-md transition-all min-w-[210px] max-w-[240px] ${colorClasses} ${
        isHighlighted ? 'ring-2 ring-sky-400 ring-offset-2 ring-offset-slate-950 shadow-sky-500/30' : ''
      }`}
    >
      <Handle type="target" position={Position.Left} className="w-2 h-2 !bg-sky-400" />

      <div className="flex items-center space-x-2 mb-1">
        <Icon className="w-4 h-4 shrink-0" />
        <span className="text-[10px] font-mono uppercase tracking-wider opacity-80 truncate">
          {data.artifactType?.replace(/_/g, ' ')}
        </span>
      </div>

      <div className="text-xs font-semibold text-slate-100 truncate">{data.label}</div>
      <div className="text-[10px] text-slate-400 truncate mt-0.5">{data.description}</div>

      <div className="mt-2 flex items-center justify-between text-[9px] font-mono text-slate-400 pt-1.5 border-t border-slate-800/80">
        <span>ID: {data.id}</span>
        <span>v{data.version}</span>
      </div>

      <Handle type="source" position={Position.Right} className="w-2 h-2 !bg-sky-400" />
    </div>
  );
});

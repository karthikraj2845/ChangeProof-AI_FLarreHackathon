import React, { useEffect, useState } from 'react';
import {
  CheckSquare,
  AlertTriangle,
  Play,
  RotateCcw,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import { apiClient } from '../../api/client';
import { TestResultItem } from '../../types';
import { StatusBadge } from '../../components/StatusBadge';

export const RegressionPage: React.FC = () => {
  const [results, setResults] = useState<TestResultItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);

  const runTests = async () => {
    try {
      setExecuting(true);
      const data = await apiClient.runTests('CR-2026-001');
      setResults(data.results || []);
    } catch (err) {
      console.error(err);
    } finally {
      setExecuting(false);
      setLoading(false);
    }
  };

  useEffect(() => {
    runTests();
  }, []);

  const regressionsCount = results.filter((r) => r.is_regression).length;
  const passedCount = results.filter((r) => r.status === 'PASSED').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight flex items-center">
            <CheckSquare className="w-6 h-6 mr-2 text-emerald-400" />
            Deterministic Regression Matrix
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Side-by-side behavioral verification between Approved Baseline v1.0 and Proposed v1.1.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={runTests}
            disabled={executing}
            className="inline-flex items-center px-4 py-2 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition-colors shadow-sm disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 mr-1.5" />
            {executing ? 'Executing Tests...' : 'Run Regression Suite'}
          </button>
        </div>
      </div>

      {/* Regression Alert Banner */}
      {regressionsCount > 0 && (
        <div className="p-5 rounded-2xl border border-rose-800 bg-rose-950/40 text-rose-200 shadow-xl backdrop-blur-sm space-y-2">
          <div className="flex items-center space-x-2 font-bold text-sm text-rose-400">
            <AlertTriangle className="w-5 h-5 shrink-0" />
            <span>CRITICAL BEHAVIORAL REGRESSION DETECTED</span>
          </div>
          <p className="text-xs leading-relaxed max-w-4xl">
            Test <strong>TEST-SD-002</strong> detected that a driver from an unsupported regulatory jurisdiction (Nevada / NV)
            was correctly rejected by Baseline v1.0 (0% discount), but was <strong>incorrectly awarded 10% discount</strong> under
            Proposed v1.1 because the jurisdiction eligibility condition was omitted!
          </p>
        </div>
      )}

      {/* Summary KPI Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono text-xs">
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 flex items-center justify-between">
          <span className="text-slate-400">Total Scenarios:</span>
          <span className="font-bold text-slate-100 text-sm">{results.length}</span>
        </div>
        <div className="p-4 rounded-xl border border-emerald-900/60 bg-emerald-950/20 flex items-center justify-between">
          <span className="text-emerald-400">Passing Tests:</span>
          <span className="font-bold text-emerald-300 text-sm">{passedCount}</span>
        </div>
        <div className="p-4 rounded-xl border border-rose-900/60 bg-rose-950/20 flex items-center justify-between">
          <span className="text-rose-400">Regressions Flagged:</span>
          <span className="font-bold text-rose-300 text-sm">{regressionsCount}</span>
        </div>
      </div>

      {/* Side-by-Side Matrix Table */}
      <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/40 backdrop-blur-sm space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200">Test Execution Results</h3>
          <span className="text-xs font-mono text-slate-400">Deterministic Engine &bull; Zero Hallucination</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 font-mono uppercase border-b border-slate-800">
              <tr>
                <th className="py-3 px-3">Test ID</th>
                <th className="py-3 px-3">Scenario & Category</th>
                <th className="py-3 px-3">Input Parameters</th>
                <th className="py-3 px-3">Baseline v1.0 Outcome</th>
                <th className="py-3 px-3">Proposed v1.1 Outcome</th>
                <th className="py-3 px-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-sans">
              {results.map((r) => (
                <tr
                  key={r.test_id}
                  className={`transition-colors ${
                    r.is_regression
                      ? 'bg-rose-950/30 hover:bg-rose-950/40 border-l-4 border-l-rose-500'
                      : 'hover:bg-slate-800/30'
                  }`}
                >
                  <td className="py-3 px-3 font-mono font-bold text-sky-400">{r.test_id}</td>
                  <td className="py-3 px-3">
                    <div className="font-semibold text-slate-200">{r.name}</div>
                    <span className="inline-block mt-0.5 text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                      {r.category}
                    </span>
                  </td>
                  <td className="py-3 px-3 font-mono text-[11px] text-slate-400">
                    <div>State: {r.input_data.jurisdiction || 'N/A'}</div>
                    <div>Score: {r.input_data.driver_risk_score ?? 'N/A'}</div>
                    <div>Vehicle: {r.input_data.vehicle_category || 'N/A'}</div>
                  </td>
                  <td className="py-3 px-3 font-mono text-xs">
                    <span
                      className={`font-semibold ${
                        r.baseline_outcome.eligible ? 'text-emerald-400' : 'text-slate-400'
                      }`}
                    >
                      {r.baseline_outcome.discount_percentage}% discount
                    </span>
                    <div className="text-[10px] text-slate-400 mt-0.5">
                      {r.baseline_outcome.eligible ? 'Eligible' : 'Rejected'}
                    </div>
                  </td>
                  <td className="py-3 px-3 font-mono text-xs">
                    <span
                      className={`font-semibold ${
                        r.proposed_outcome.eligible
                          ? r.is_regression
                            ? 'text-rose-400 font-bold underline'
                            : 'text-emerald-400'
                          : 'text-slate-400'
                      }`}
                    >
                      {r.proposed_outcome.discount_percentage}% discount
                    </span>
                    <div className="text-[10px] text-slate-400 mt-0.5">
                      {r.proposed_outcome.eligible ? 'Eligible' : 'Rejected'}
                    </div>
                  </td>
                  <td className="py-3 px-3 text-right">
                    <StatusBadge status={r.status} size="sm" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

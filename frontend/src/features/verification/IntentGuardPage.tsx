import React, { useState } from 'react';
import {
  Radio,
  Play,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  ArrowRight,
  Server,
  Layers,
  FileSearch,
} from 'lucide-react';
import { apiClient } from '../../api/client';
import { StatusBadge } from '../../components/StatusBadge';

export const IntentGuardPage: React.FC = () => {
  const [jurisdiction, setJurisdiction] = useState('NV');
  const [riskScore, setRiskScore] = useState(15);
  const [vehicle, setVehicle] = useState('SEDAN');
  const [policyActive, setPolicyActive] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      const res = await apiClient.simulateTransaction({
        jurisdiction,
        driver_risk_score: Number(riskScore),
        vehicle_category: vehicle,
        policy_active: policyActive,
      });
      setResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight flex items-center">
            <Radio className="w-6 h-6 mr-2 text-sky-400" />
            IntentGuard Runtime Verification
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Simulate and monitor deployed insurance transactions against explicitly approved reference rule versions.
          </p>
        </div>

        <span className="text-xs font-mono px-3 py-1.5 rounded-lg bg-sky-950 text-sky-400 border border-sky-800">
          Post-Deployment Verification
        </span>
      </div>

      {/* Simulator Form and Result */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Simulator Form (1 col) */}
        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/40 backdrop-blur-sm space-y-4">
          <div className="pb-3 border-b border-slate-800">
            <h3 className="text-sm font-bold text-white flex items-center">
              <Server className="w-4 h-4 mr-2 text-sky-400" />
              Transaction Simulator
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Submit synthetic quote payload processed by candidate deployed version.
            </p>
          </div>

          <form onSubmit={handleSimulate} className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">State Jurisdiction</label>
              <select
                value={jurisdiction}
                onChange={(e) => setJurisdiction(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:border-sky-500"
              >
                <option value="NV">NV (Nevada - Unsupported State)</option>
                <option value="CA">CA (California - Supported State)</option>
                <option value="TX">TX (Texas - Supported State)</option>
                <option value="FL">FL (Florida - Supported State)</option>
                <option value="OR">OR (Oregon - Unsupported State)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Driver Telematics Risk Score (1-100)
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={riskScore}
                onChange={(e) => setRiskScore(Number(e.target.value))}
                className="w-full px-3 py-2 text-xs rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:border-sky-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Vehicle Classification</label>
              <select
                value={vehicle}
                onChange={(e) => setVehicle(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:border-sky-500"
              >
                <option value="SEDAN">SEDAN (Eligible)</option>
                <option value="SUV">SUV (Eligible)</option>
                <option value="COMMERCIAL_TRUCK">COMMERCIAL_TRUCK (Ineligible)</option>
              </select>
            </div>

            <div className="flex items-center space-x-2 pt-1">
              <input
                type="checkbox"
                id="policyActive"
                checked={policyActive}
                onChange={(e) => setPolicyActive(e.target.checked)}
                className="rounded bg-slate-950 border-slate-700 text-sky-500 focus:ring-0"
              />
              <label htmlFor="policyActive" className="text-xs text-slate-300 font-medium cursor-pointer">
                Policy Active (in force)
              </label>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold bg-sky-500 hover:bg-sky-400 text-slate-950 transition-colors shadow-md shadow-sky-500/20 disabled:opacity-50"
              >
                {loading ? 'Evaluating Transaction...' : 'Simulate & Run IntentGuard'}
              </button>
            </div>
          </form>
        </div>

        {/* Verification Results Panel (2 cols) */}
        <div className="lg:col-span-2 p-5 rounded-2xl border border-slate-800 bg-slate-900/40 backdrop-blur-sm space-y-5">
          {result ? (
            <div className="space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
                <div>
                  <span className="text-xs font-mono text-slate-400">Transaction ID: {result.transaction_id}</span>
                  <div className="flex items-center space-x-2 mt-1">
                    <span className="text-lg font-bold text-white">IntentGuard Verification Status</span>
                    <StatusBadge status={result.status} size="md" />
                  </div>
                </div>

                {result.is_deviation && (
                  <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-rose-950 text-rose-400 border border-rose-800 animate-pulse">
                    CRITICAL DEVIATION DETECTED
                  </span>
                )}
              </div>

              {/* Side-by-Side: Approved Reference Version vs Observed Deployed Version */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl border border-emerald-900/70 bg-emerald-950/20 space-y-2">
                  <span className="text-xs font-bold uppercase text-emerald-400 font-mono flex items-center">
                    <CheckCircle2 className="w-4 h-4 mr-1.5" />
                    Approved Reference Version
                  </span>
                  <div className="text-xs font-mono text-slate-300">
                    <div>Version: <strong className="text-emerald-300">{result.approved_reference_version}</strong></div>
                    <div className="mt-1">
                      Expected Discount: <strong className="text-emerald-300 text-sm">{result.expected_outcome?.discount_percentage}%</strong>
                    </div>
                    <div>Eligible: <span className="text-slate-200">{String(result.expected_outcome?.eligible)}</span></div>
                  </div>
                </div>

                <div className="p-4 rounded-xl border border-rose-900/70 bg-rose-950/20 space-y-2">
                  <span className="text-xs font-bold uppercase text-rose-400 font-mono flex items-center">
                    <AlertTriangle className="w-4 h-4 mr-1.5" />
                    Simulated Deployed Version
                  </span>
                  <div className="text-xs font-mono text-slate-300">
                    <div>Version: <strong className="text-rose-300">{result.reported_version}</strong></div>
                    <div className="mt-1">
                      Observed Discount: <strong className="text-rose-300 text-sm">{result.observed_outcome?.discount_percentage}%</strong>
                    </div>
                    <div>Eligible: <span className="text-slate-200">{String(result.observed_outcome?.eligible)}</span></div>
                  </div>
                </div>
              </div>

              {/* Explanation Summary */}
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-slate-300 space-y-1">
                <span className="font-bold text-slate-400 font-mono uppercase block">Verification Analysis</span>
                <p className="leading-relaxed">{result.summary}</p>
              </div>

              {/* Auto-created Finding Card */}
              {result.finding && (
                <div className="p-4 rounded-xl border border-rose-800 bg-rose-950/30 text-rose-200 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-rose-400 flex items-center">
                      <ShieldAlert className="w-4 h-4 mr-1.5" />
                      Auto-Generated Linked Finding: {result.finding.id}
                    </span>
                    <StatusBadge status="CRITICAL" size="sm" />
                  </div>
                  <div className="text-xs font-semibold text-slate-100">{result.finding.title}</div>
                  <p className="text-xs text-slate-300 leading-relaxed">{result.finding.description}</p>
                  <div className="pt-2 text-[11px] font-mono text-slate-400 flex flex-wrap gap-4 border-t border-rose-900/50">
                    <span>Linked Change: {result.finding.linked_change_id}</span>
                    <span>Predictive Test Evidence: {result.finding.linked_test_id}</span>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-72 text-center text-slate-400 space-y-3">
              <Radio className="w-10 h-10 opacity-30 text-sky-400" />
              <p className="text-xs max-w-sm">
                Submit a transaction on the left to execute IntentGuard runtime verification against the approved reference version.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

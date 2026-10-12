import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  FileCheck,
  UserCheck,
  RotateCcw,
} from 'lucide-react';
import { apiClient } from '../../api/client';
import { ReadinessResult } from '../../types';
import { StatusBadge } from '../../components/StatusBadge';

export const ReadinessPage: React.FC = () => {
  const [readiness, setReadiness] = useState<ReadinessResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [reviewer, setReviewer] = useState('Chief Underwriting Officer');
  const [justification, setJustification] = useState('Rejected: Seeded defect exposes carrier to unfiled rate violations in NV.');
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadReadiness = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getReadiness('CR-2026-001');
      setReadiness(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReadiness();
  }, []);

  const handleApprove = async () => {
    try {
      setIsSubmitting(true);
      const res = await apiClient.approveChange('CR-2026-001', reviewer, justification);
      setActionMessage(`Approved: ${res.message}`);
      loadReadiness();
    } catch (err: any) {
      setActionMessage(`Approval Blocked: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    try {
      setIsSubmitting(true);
      const res = await apiClient.rejectChange('CR-2026-001', reviewer, justification);
      setActionMessage(`Rejected: ${res.message}`);
      loadReadiness();
    } catch (err: any) {
      setActionMessage(`Error: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight flex items-center">
            <ShieldAlert className="w-6 h-6 mr-2 text-rose-400" />
            Deterministic Release Readiness & Governance
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Deterministic policy enforcement prevents unverified releases from deploying into core insurance environments.
          </p>
        </div>

        <button
          onClick={loadReadiness}
          className="inline-flex items-center px-3.5 py-2 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
        >
          <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
          Re-evaluate Policy
        </button>
      </div>

      {/* Main Readiness Verdict Card */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 backdrop-blur-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <span className="text-xs font-mono uppercase tracking-wider text-slate-400 block mb-1">
              Current Release Verdict
            </span>
            <div className="flex items-center space-x-3">
              <span className="text-2xl font-black text-white">Change Request CR-2026-001</span>
              <StatusBadge status={readiness?.status || 'BLOCKED'} size="lg" />
            </div>
          </div>

          <div className="text-right">
            <span className="text-xs text-slate-400 block">Evidence Completeness</span>
            <span className="text-xl font-bold font-mono text-amber-400">
              {readiness?.evidence_completeness_pct ?? 0}%
            </span>
          </div>
        </div>

        {/* Cryptographic Evidence Snapshot Card */}
        {((readiness as any)?.snapshot_id || (readiness as any)?.snapshot_hash) && (
          <div className="p-4 rounded-xl border border-sky-900/60 bg-sky-950/20 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
            <div>
              <span className="text-sky-400 font-bold block uppercase tracking-wider">
                Cryptographic Evidence Snapshot Bound
              </span>
              <span className="text-slate-300">
                Snapshot ID: <span className="text-white font-bold">{(readiness as any)?.snapshot_id}</span>
              </span>
            </div>
            <div className="text-left sm:text-right">
              <span className="text-slate-400 block text-[10px] uppercase">SHA-256 State Fingerprint</span>
              <span className="text-sky-300 text-[11px] break-all font-mono">
                {(readiness as any)?.snapshot_hash ? `${(readiness as any)?.snapshot_hash.slice(0, 24)}...` : 'VERIFIED'}
              </span>
            </div>
          </div>
        )}

        {/* Hard Blockers List */}
        <div className="p-5 rounded-xl border border-rose-900/80 bg-rose-950/30 space-y-3">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-rose-400 font-mono">
            <XCircle className="w-4 h-4" />
            <span>Deterministic Policy Blockers ({readiness?.blockers.length || 0})</span>
          </div>
          <ul className="space-y-2 text-xs text-rose-200">
            {(readiness?.blockers || []).map((b, i) => (
              <li key={i} className="flex items-start">
                <span className="text-rose-400 font-bold mr-2">&bull;</span>
                <span className="font-mono">{b}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Governance Guidelines Box */}
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/70 text-xs text-slate-400 space-y-1">
          <span className="font-bold text-slate-300 font-mono uppercase tracking-wider block">
            Underwriting Governance Constraint
          </span>
          <p className="leading-relaxed">
            {readiness?.governance_note} AI reasoning agents assist with dependency synthesis and explanation, but do not possess the authority to override deterministic policy blockers or fabricate passing test results.
          </p>
        </div>

        {/* Human Governance Action Form */}
        <div className="p-5 rounded-xl border border-slate-800 bg-slate-950/60 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono flex items-center">
            <UserCheck className="w-4 h-4 mr-1.5 text-sky-400" />
            Human Review Decision Submission
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Reviewer Name & Role</label>
              <input
                type="text"
                value={reviewer}
                onChange={(e) => setReviewer(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-lg bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-sky-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Decision Justification</label>
              <input
                type="text"
                value={justification}
                onChange={(e) => setJustification(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-lg bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-sky-500"
              />
            </div>
          </div>

          {actionMessage && (
            <div className="p-3 rounded-lg text-xs font-mono bg-slate-900 border border-slate-700 text-slate-200">
              {actionMessage}
            </div>
          )}

          <div className="flex items-center justify-end space-x-3 pt-2">
            <button
              onClick={handleReject}
              disabled={isSubmitting}
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-rose-600 hover:bg-rose-500 text-white transition-colors"
            >
              Reject Change (Preserve Production Safety)
            </button>
            <button
              onClick={handleApprove}
              disabled={isSubmitting || readiness?.is_blocked}
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              title={readiness?.is_blocked ? 'Strictly blocked by policy: cannot approve release with regressions.' : ''}
            >
              Approve Release
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

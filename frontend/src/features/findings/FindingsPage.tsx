import React, { useEffect, useState } from 'react';
import {
  FileSearch,
  ShieldAlert,
  Clock,
  Filter,
  CheckCircle2,
  AlertCircle,
  FileText,
  User,
} from 'lucide-react';
import { apiClient } from '../../api/client';
import { Finding, AuditEvent } from '../../types';
import { StatusBadge } from '../../components/StatusBadge';

export const FindingsPage: React.FC = () => {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [activeTab, setActiveTab] = useState<'findings' | 'audit'>('findings');
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const [fData, aData] = await Promise.all([
        apiClient.getFindings(),
        apiClient.getAuditEvents(),
      ]);
      setFindings(fData);
      setAuditEvents(aData);
      if (fData.length > 0 && !selectedFinding) {
        setSelectedFinding(fData[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleStatusUpdate = async (findingId: string, newStatus: string) => {
    try {
      await apiClient.updateFindingStatus(findingId, newStatus);
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight flex items-center">
            <FileSearch className="w-6 h-6 mr-2 text-sky-400" />
            Audit Trail & Traceable Findings
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Complete continuous evidence chain connecting proposals, regression evidence, human approvals, and post-deployment deviations.
          </p>
        </div>

        {/* View Toggle */}
        <div className="flex items-center space-x-1 p-1 bg-slate-900 border border-slate-800 rounded-xl">
          <button
            onClick={() => setActiveTab('findings')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
              activeTab === 'findings'
                ? 'bg-sky-500 text-slate-950 shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Findings ({findings.length})
          </button>
          <button
            onClick={() => setActiveTab('audit')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
              activeTab === 'audit'
                ? 'bg-sky-500 text-slate-950 shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Immutable Audit Stream ({auditEvents.length})
          </button>
        </div>
      </div>

      {/* Main Content */}
      {activeTab === 'findings' ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Findings List (2 cols) */}
          <div className="lg:col-span-2 space-y-3">
            {findings.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400 rounded-2xl border border-slate-800 bg-slate-900/40">
                No open findings recorded yet. Run IntentGuard simulation to generate verification findings.
              </div>
            ) : (
              findings.map((f) => (
                <div
                  key={f.id}
                  onClick={() => setSelectedFinding(f)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer ${
                    selectedFinding?.id === f.id
                      ? 'border-sky-500 bg-slate-900 ring-1 ring-sky-500'
                      : 'border-slate-800 bg-slate-900/40 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs font-bold text-sky-400">{f.id}</span>
                      <StatusBadge status={f.severity} size="sm" />
                      <StatusBadge status={f.status} size="sm" />
                    </div>
                    <span className="text-[10px] text-slate-400">
                      {new Date(f.created_at).toLocaleTimeString()}
                    </span>
                  </div>

                  <h4 className="text-xs font-bold text-white mb-1">{f.title}</h4>
                  <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">{f.description}</p>

                  <div className="mt-3 flex flex-wrap items-center gap-3 text-[10px] font-mono text-slate-400 pt-2 border-t border-slate-800/80">
                    <span>Change: {f.linked_change_id}</span>
                    <span>Rule: {f.linked_rule_id}</span>
                    <span>Test: {f.linked_test_id}</span>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Finding Detail Inspector (1 col) */}
          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm space-y-4">
            {selectedFinding ? (
              <div className="space-y-4">
                <div className="pb-3 border-b border-slate-800">
                  <span className="text-[10px] font-mono text-slate-400">Finding Details</span>
                  <h3 className="text-sm font-bold text-white mt-1">{selectedFinding.title}</h3>
                  <div className="flex items-center space-x-2 mt-2">
                    <StatusBadge status={selectedFinding.severity} size="sm" />
                    <StatusBadge status={selectedFinding.status} size="sm" />
                  </div>
                </div>

                <div className="text-xs text-slate-300 leading-relaxed">
                  {selectedFinding.description}
                </div>

                {/* Evidence Payload */}
                <div className="space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono">
                    Structured Evidence Payload
                  </span>
                  <pre className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] font-mono text-slate-300 overflow-x-auto max-h-48">
                    {JSON.stringify(selectedFinding.evidence, null, 2)}
                  </pre>
                </div>

                {/* Actions */}
                <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
                  <span className="text-xs text-slate-400">Update Status:</span>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleStatusUpdate(selectedFinding.id, 'ACKNOWLEDGED')}
                      className="px-2.5 py-1 text-xs font-semibold rounded bg-amber-950 text-amber-400 border border-amber-800 hover:bg-amber-900/50"
                    >
                      Acknowledge
                    </button>
                    <button
                      onClick={() => handleStatusUpdate(selectedFinding.id, 'RESOLVED')}
                      className="px-2.5 py-1 text-xs font-semibold rounded bg-emerald-950 text-emerald-400 border border-emerald-800 hover:bg-emerald-900/50"
                    >
                      Resolve
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-16 text-slate-400 text-xs">
                Select a finding on the left to inspect evidence provenance.
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Immutable Audit Stream View */
        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/40 backdrop-blur-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h3 className="text-sm font-semibold text-slate-200">Continuous Event Audit Stream</h3>
              <p className="text-xs text-slate-400">Cryptographically ordered, tamper-evident governance log</p>
            </div>
            <span className="text-xs font-mono text-slate-400">{auditEvents.length} Events Logged</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950 text-slate-400 uppercase border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Timestamp</th>
                  <th className="py-2.5 px-3">Event Type</th>
                  <th className="py-2.5 px-3">Actor</th>
                  <th className="py-2.5 px-3">Entity ID</th>
                  <th className="py-2.5 px-3">Payload Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {auditEvents.map((evt) => (
                  <tr key={evt.id} className="hover:bg-slate-800/30">
                    <td className="py-3 px-3 font-mono text-slate-400 whitespace-nowrap">
                      {new Date(evt.timestamp).toLocaleString()}
                    </td>
                    <td className="py-3 px-3 font-mono font-semibold text-sky-400 whitespace-nowrap">
                      {evt.event_type}
                    </td>
                    <td className="py-3 px-3 text-slate-300 whitespace-nowrap flex items-center">
                      <User className="w-3.5 h-3.5 mr-1 text-slate-400" />
                      {evt.actor}
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-400">{evt.entity_id}</td>
                    <td className="py-3 px-3 font-mono text-[11px] text-slate-400 max-w-xs truncate">
                      {JSON.stringify(evt.details)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

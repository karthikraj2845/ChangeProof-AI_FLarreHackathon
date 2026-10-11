import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  GitPullRequest,
  Plus,
  ArrowRight,
  Play,
  Shield,
  Layers,
  Sparkles,
} from 'lucide-react';
import { apiClient } from '../../api/client';
import { ChangeRequest } from '../../types';
import { StatusBadge } from '../../components/StatusBadge';

export const ChangesPage: React.FC = () => {
  const [changes, setChanges] = useState<ChangeRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const navigate = useNavigate();

  const loadChanges = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getChanges();
      setChanges(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadChanges();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle || !newDesc) return;
    try {
      await apiClient.createChange({
        title: newTitle,
        description: newDesc,
        creator: 'underwriting_analyst',
      });
      setShowModal(false);
      setNewTitle('');
      setNewDesc('');
      loadChanges();
    } catch (err) {
      console.error(err);
    }
  };

  const handleRunWorkflow = async (crId: string, desc: string) => {
    try {
      await apiClient.startChangeAssurance(crId, desc);
      navigate('/workflow');
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight flex items-center">
            <GitPullRequest className="w-6 h-6 mr-2 text-sky-400" />
            Insurance Change Requests
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Proposals for modifications to underwriting rules, rating logic, and policy constraints.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center px-3.5 py-2 rounded-lg text-xs font-semibold bg-sky-500 hover:bg-sky-400 text-slate-950 transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4 mr-1.5" />
            New Change Request
          </button>
        </div>
      </div>

      {/* Changes list */}
      <div className="space-y-4">
        {loading && changes.length === 0 ? (
          <div className="text-center py-12 text-slate-400">Loading change requests...</div>
        ) : (
          changes.map((cr) => (
            <div
              key={cr.id}
              className="p-5 rounded-xl border border-slate-800 bg-slate-900/40 hover:border-slate-700 transition-all backdrop-blur-sm"
            >
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs font-semibold text-sky-400 bg-sky-950/60 px-2 py-0.5 rounded border border-sky-800">
                      {cr.id}
                    </span>
                    <StatusBadge status={cr.status} size="sm" />
                    <StatusBadge status={cr.readiness_status} size="sm" />
                  </div>

                  <h3 className="text-base font-bold text-slate-100">{cr.title}</h3>
                  <p className="text-xs text-slate-400 leading-relaxed max-w-3xl">{cr.description}</p>

                  <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-slate-400 pt-2">
                    <div className="flex items-center space-x-1">
                      <span className="text-slate-400">Target Rule:</span>
                      <span className="text-slate-200">{cr.target_rule_id}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <span className="text-slate-400">Baseline:</span>
                      <span className="text-emerald-400">{cr.baseline_version_id}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <span className="text-slate-400">Proposed:</span>
                      <span className="text-amber-400">{cr.proposed_version_id}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <span className="text-slate-400">Creator:</span>
                      <span className="text-slate-300">{cr.creator}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2 shrink-0">
                  <button
                    onClick={() => handleRunWorkflow(cr.id, cr.description)}
                    className="inline-flex items-center px-4 py-2 text-xs font-semibold rounded-lg bg-sky-600 hover:bg-sky-500 text-white transition-colors shadow-sm"
                  >
                    <Play className="w-3.5 h-3.5 mr-1.5" />
                    Run Assurance Workflow
                  </button>
                  <button
                    onClick={() => navigate('/impact')}
                    className="inline-flex items-center px-3 py-2 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
                  >
                    View Graph
                    <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* New Change Request Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl">
            <h2 className="text-lg font-bold text-white mb-2">Create Insurance Change Proposal</h2>
            <p className="text-xs text-slate-400 mb-4">
              Enter a natural language request describing the intended rule modification.
            </p>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Title</label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g., Adjust telematics risk score threshold"
                  className="w-full px-3 py-2 text-xs rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Natural Language Description
                </label>
                <textarea
                  required
                  rows={4}
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="Describe what conditions should change..."
                  className="w-full px-3 py-2 text-xs rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setNewTitle('Expand safe-driver discount nationwide');
                    setNewDesc('Remove the jurisdiction restriction from the safe-driver discount eligibility rule.');
                  }}
                  className="text-xs text-sky-400 hover:underline"
                >
                  Load Seed Scenario Preset
                </button>

                <div className="flex space-x-2">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-3.5 py-2 text-xs rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 text-xs font-semibold rounded-lg bg-sky-500 text-slate-950 hover:bg-sky-400"
                  >
                    Submit Proposal
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

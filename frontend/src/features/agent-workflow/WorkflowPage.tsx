import React, { useEffect, useState } from 'react';
import {
  Bot,
  CheckCircle,
  AlertCircle,
  FileText,
  Sliders,
  Network,
  CheckSquare,
  ShieldAlert,
  UserCheck,
  Play,
  RotateCcw,
  Sparkles,
} from 'lucide-react';
import { apiClient } from '../../api/client';
import { WorkflowState } from '../../types';
import { StatusBadge } from '../../components/StatusBadge';

export const WorkflowPage: React.FC = () => {
  const [workflowState, setWorkflowState] = useState<WorkflowState | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeStep, setActiveStep] = useState(0);

  // Review modal / form state
  const [reviewer, setReviewer] = useState('Senior Underwriting Lead');
  const [justification, setJustification] = useState('Rejected: Seeded jurisdiction defect allows unapproved discounts in Nevada (NV).');
  const [isSubmittingReview, setIsSubmittingReview] = useState(false);

  const startWorkflow = async () => {
    try {
      setLoading(true);
      const res = await apiClient.startChangeAssurance(
        'CR-2026-001',
        'Remove the jurisdiction restriction from the safe-driver discount eligibility rule.'
      );
      setWorkflowState(res.state);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    startWorkflow();
  }, []);

  const handleReviewDecision = async (action: 'APPROVE' | 'REJECT' | 'REQUEST_MORE_TESTS') => {
    if (!workflowState?.workflow_id) return;
    try {
      setIsSubmittingReview(true);
      const res = await apiClient.resumeWorkflow(workflowState.workflow_id, {
        reviewer,
        action,
        justification,
      });
      setWorkflowState(res.state);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmittingReview(false);
    }
  };

  const steps = [
    { id: 'change_understanding', name: 'Change Understanding Agent', icon: Bot },
    { id: 'insurance_context', name: 'Insurance Context Agent', icon: FileText },
    { id: 'impact_analysis', name: 'RuleRipple Impact Agent', icon: Network },
    { id: 'test_planning', name: 'Test Planning Agent', icon: Sliders },
    { id: 'test_execution', name: 'Deterministic Test Engine', icon: CheckSquare },
    { id: 'readiness_assessment', name: 'Evidence & Risk Agent', icon: ShieldAlert },
    { id: 'human_review_gate', name: 'Human Governance Gate', icon: UserCheck },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight flex items-center">
              <Bot className="w-6 h-6 mr-2 text-sky-400" />
              LangGraph Multi-Agent Change Assurance
            </h1>
            {workflowState?.workflow_id && (
              <span className="font-mono text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-sky-400 border border-slate-700">
                {workflowState.workflow_id}
              </span>
            )}
          </div>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Typed LangGraph pipeline executing specialized agents, graph reachability, deterministic testing, and human review gates.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={startWorkflow}
            disabled={loading}
            className="inline-flex items-center px-3.5 py-2 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors disabled:opacity-50"
          >
            <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
            {loading ? 'Executing...' : 'Re-run Workflow'}
          </button>
        </div>
      </div>

      {/* Stepper / Timeline */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          const isCurrent = activeStep === idx;
          const isDone = Boolean(workflowState);

          return (
            <button
              key={step.id}
              onClick={() => setActiveStep(idx)}
              className={`p-3 rounded-xl border text-left transition-all ${
                isCurrent
                  ? 'border-sky-500 bg-sky-950/40 text-sky-300 ring-1 ring-sky-500'
                  : 'border-slate-800 bg-slate-900/40 text-slate-400 hover:border-slate-700 hover:text-slate-200'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono opacity-80">Stage {idx + 1}</span>
                {isDone ? (
                  <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <div className="w-2 h-2 rounded-full bg-slate-700" />
                )}
              </div>
              <div className="flex items-center space-x-1.5 font-semibold text-xs text-slate-100 truncate">
                <Icon className="w-3.5 h-3.5 shrink-0 opacity-80" />
                <span className="truncate">{step.name.split(' ')[0]}</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Main Inspection View for Selected Stage */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-sm space-y-6">
        {/* Stage 1: Change Understanding */}
        {activeStep === 0 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="text-base font-bold text-white flex items-center">
                  <Bot className="w-5 h-5 mr-2 text-sky-400" />
                  Agent 1: Change Understanding Agent
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Parses natural language requirements into validated structured insurance operations.
                </p>
              </div>
              <span className="text-xs font-mono px-2.5 py-1 rounded bg-sky-950 text-sky-400 border border-sky-800">
                Mode: {workflowState?.parsed_change?.provider_mode || 'OFFLINE_HEURISTIC'}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
                <span className="text-xs font-semibold text-slate-400">Raw User Request</span>
                <p className="text-sm font-sans text-slate-200 italic">
                  "{workflowState?.user_request}"
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
                <span className="text-xs font-semibold text-slate-400">Validated Structured Proposal</span>
                <div className="space-y-1 text-xs font-mono">
                  <div><strong className="text-slate-400">Target Rule:</strong> <span className="text-sky-400">{workflowState?.parsed_change?.target_rule}</span></div>
                  <div><strong className="text-slate-400">Operation:</strong> <span className="text-amber-400">{workflowState?.parsed_change?.operation}</span></div>
                  <div><strong className="text-slate-400">Field Affected:</strong> <span className="text-emerald-400">{workflowState?.parsed_change?.condition_field}</span></div>
                  <div><strong className="text-slate-400">Confidence:</strong> <span className="text-slate-200">{(workflowState?.parsed_change?.confidence ?? 1) * 100}%</span></div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Stage 2: Insurance Context */}
        {activeStep === 1 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="text-base font-bold text-white flex items-center">
                  <FileText className="w-5 h-5 mr-2 text-amber-400" />
                  Agent 2: Insurance Context Agent
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Retrieves authoritative database records, product specifications, and version references.
                </p>
              </div>
              <span className="text-xs font-mono px-2.5 py-1 rounded bg-amber-950 text-amber-400 border border-amber-800">
                Source: Database Records
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
                <span className="text-slate-400 block mb-1">Target Rule</span>
                <span className="text-sm font-bold text-white block">{workflowState?.domain_context?.rule_name}</span>
                <span className="text-slate-400 block mt-2">Type: {workflowState?.domain_context?.rule_type}</span>
              </div>
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
                <span className="text-slate-400 block mb-1">Baseline Version (Immutable)</span>
                <span className="text-sm font-bold text-emerald-400 block">{workflowState?.domain_context?.baseline_version}</span>
                <span className="text-slate-400 block mt-2">Status: APPROVED & IN FORCE</span>
              </div>
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
                <span className="text-slate-400 block mb-1">Proposed Version</span>
                <span className="text-sm font-bold text-amber-400 block">{workflowState?.domain_context?.proposed_version}</span>
                <span className="text-slate-400 block mt-2">Status: PROPOSED CANDIDATE</span>
              </div>
            </div>
          </div>
        )}

        {/* Stage 3: RuleRipple Impact Analysis */}
        {activeStep === 2 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="text-base font-bold text-white flex items-center">
                  <Network className="w-5 h-5 mr-2 text-sky-400" />
                  Agent 3: RuleRipple Impact Agent
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Traverses NetworkX graph to identify all directly and transitively affected insurance artifacts.
                </p>
              </div>
              <span className="text-xs font-mono px-2.5 py-1 rounded bg-sky-950 text-sky-400 border border-sky-800">
                {workflowState?.impacted_artifacts?.length || 0} Artifacts Impacted
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 text-slate-400 font-mono uppercase border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Artifact ID</th>
                    <th className="py-2.5 px-3">Name</th>
                    <th className="py-2.5 px-3">Type</th>
                    <th className="py-2.5 px-3">Traversed Path</th>
                    <th className="py-2.5 px-3">Evidence Source</th>
                    <th className="py-2.5 px-3 text-right">Impact Score</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-sans">
                  {(workflowState?.impacted_artifacts || []).map((art) => (
                    <tr key={art.artifact_id} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3 font-mono font-medium text-sky-400">{art.artifact_id}</td>
                      <td className="py-2.5 px-3 font-semibold text-slate-200">{art.name}</td>
                      <td className="py-2.5 px-3 font-mono text-slate-400">{art.artifact_type}</td>
                      <td className="py-2.5 px-3 font-mono text-[11px] text-slate-400">
                        {art.dependency_path.join(' → ')}
                      </td>
                      <td className="py-2.5 px-3 text-slate-300">{art.evidence_source}</td>
                      <td className="py-2.5 px-3 font-mono font-bold text-right text-amber-400">
                        {art.impact_score}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Stage 4: Test Planning */}
        {activeStep === 3 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="text-base font-bold text-white flex items-center">
                  <Sliders className="w-5 h-5 mr-2 text-indigo-400" />
                  Agent 4: Test Planning Agent
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Selects existing regression test suites and synthesizes candidate edge-case proposals.
                </p>
              </div>
              <span className="text-xs font-mono px-2.5 py-1 rounded bg-indigo-950 text-indigo-400 border border-indigo-800">
                8 Selected &bull; 2 Proposed
              </span>
            </div>

            <div className="space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono">
                AI Suggested Test Cases (Unvalidated Proposals)
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {(workflowState?.suggested_tests || []).map((sug) => (
                  <div key={sug.id} className="p-4 rounded-xl border border-indigo-900/50 bg-indigo-950/20 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs text-indigo-400 font-bold">{sug.id}</span>
                      <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800">
                        {sug.status}
                      </span>
                    </div>
                    <div className="font-semibold text-xs text-slate-200">{sug.name}</div>
                    <p className="text-xs text-slate-400">{sug.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Stage 5: Deterministic Test Execution */}
        {activeStep === 4 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="text-base font-bold text-white flex items-center">
                  <CheckSquare className="w-5 h-5 mr-2 text-emerald-400" />
                  Deterministic Regression Test Engine
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Side-by-side execution of baseline v1.0 vs proposed v1.1 rules without LLM hallucinations.
                </p>
              </div>
              <span className="text-xs font-mono px-2.5 py-1 rounded bg-rose-950 text-rose-400 border border-rose-800">
                1 Regression Detected
              </span>
            </div>

            {/* Regression Banner */}
            <div className="p-4 rounded-xl border border-rose-800/80 bg-rose-950/40 text-rose-200 space-y-1">
              <div className="flex items-center space-x-2 font-bold text-xs uppercase text-rose-400">
                <AlertCircle className="w-4 h-4" />
                <span>Behavioral Regression Flagged in TEST-SD-002</span>
              </div>
              <p className="text-xs leading-relaxed">
                Driver in unsupported state 'NV' was rejected with 0% discount under baseline v1.0, but incorrectly received 10% discount under proposed v1.1! The jurisdiction condition omission causes unauthorized rate rollout.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 text-slate-400 font-mono uppercase border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Test ID</th>
                    <th className="py-2.5 px-3">Scenario</th>
                    <th className="py-2.5 px-3">Category</th>
                    <th className="py-2.5 px-3">Baseline v1.0</th>
                    <th className="py-2.5 px-3">Proposed v1.1</th>
                    <th className="py-2.5 px-3 text-right">Verdict</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-sans">
                  {(workflowState?.test_results || []).map((t) => (
                    <tr
                      key={t.test_id}
                      className={t.is_regression ? 'bg-rose-950/20 hover:bg-rose-950/30' : 'hover:bg-slate-800/30'}
                    >
                      <td className="py-2.5 px-3 font-mono font-medium text-sky-400">{t.test_id}</td>
                      <td className="py-2.5 px-3 font-medium text-slate-200">{t.name}</td>
                      <td className="py-2.5 px-3 font-mono text-slate-400">{t.category}</td>
                      <td className="py-2.5 px-3 font-mono text-slate-300">
                        {t.baseline_outcome.discount_percentage}% discount ({t.baseline_outcome.eligible ? 'Eligible' : 'Rejected'})
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-300">
                        {t.proposed_outcome.discount_percentage}% discount ({t.proposed_outcome.eligible ? 'Eligible' : 'Rejected'})
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <StatusBadge status={t.status} size="sm" />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Stage 6: Evidence & Risk Readiness Assessment */}
        {activeStep === 5 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="text-base font-bold text-white flex items-center">
                  <ShieldAlert className="w-5 h-5 mr-2 text-rose-400" />
                  Agent 5: Evidence & Risk Assessment Agent
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Deterministic readiness evaluation. LLM agents have NO authority to override policy blockers.
                </p>
              </div>
              <StatusBadge status={workflowState?.readiness_result?.status || 'BLOCKED'} size="md" />
            </div>

            <div className="space-y-3">
              <div className="p-4 rounded-xl border border-rose-900 bg-rose-950/30 space-y-2">
                <span className="text-xs font-bold uppercase tracking-wider text-rose-400 font-mono">
                  Hard Policy Blockers ({workflowState?.readiness_result?.blockers.length || 0})
                </span>
                <ul className="space-y-1.5 text-xs text-rose-200">
                  {(workflowState?.readiness_result?.blockers || []).map((b, i) => (
                    <li key={i} className="flex items-start">
                      <span className="text-rose-400 mr-2">&bull;</span>
                      <span>{b}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1">
                <span className="text-xs font-semibold text-slate-400">Formal Readiness Recommendation</span>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {workflowState?.readiness_result?.recommendation}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Stage 7: Human Governance Gate */}
        {activeStep === 6 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="text-base font-bold text-white flex items-center">
                  <UserCheck className="w-5 h-5 mr-2 text-emerald-400" />
                  Stage 7: Human Governance Review Gate
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Workflow pauses here. Human underwriter or release manager submits formal governance decision.
                </p>
              </div>
              <StatusBadge status={workflowState?.status || 'PAUSED_FOR_REVIEW'} size="md" />
            </div>

            {workflowState?.human_review_decision ? (
              <div className="p-5 rounded-xl border border-emerald-900 bg-emerald-950/30 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-emerald-400 uppercase font-mono">
                    Human Review Submitted & Recorded
                  </span>
                  <span className="text-xs text-slate-400">
                    {new Date(workflowState.human_review_decision.timestamp).toLocaleString()}
                  </span>
                </div>
                <div className="text-xs font-mono space-y-1 text-slate-200">
                  <div><strong>Reviewer:</strong> {workflowState.human_review_decision.reviewer}</div>
                  <div><strong>Action:</strong> {workflowState.human_review_decision.action}</div>
                  <div><strong>Justification:</strong> {workflowState.human_review_decision.justification}</div>
                </div>
              </div>
            ) : (
              <div className="p-5 rounded-xl border border-slate-800 bg-slate-950/70 space-y-4">
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Reviewer Identity / Role
                    </label>
                    <input
                      type="text"
                      value={reviewer}
                      onChange={(e) => setReviewer(e.target.value)}
                      className="w-full px-3 py-2 text-xs rounded-lg bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-sky-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Governance Decision Justification
                    </label>
                    <textarea
                      rows={3}
                      value={justification}
                      onChange={(e) => setJustification(e.target.value)}
                      className="w-full px-3 py-2 text-xs rounded-lg bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-sky-500"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-end space-x-3 pt-2 border-t border-slate-800">
                  <button
                    onClick={() => handleReviewDecision('REJECT')}
                    disabled={isSubmittingReview}
                    className="px-4 py-2 text-xs font-semibold rounded-lg bg-rose-600 hover:bg-rose-500 text-white transition-colors"
                  >
                    Reject Change (Recommended)
                  </button>
                  <button
                    onClick={() => handleReviewDecision('REQUEST_MORE_TESTS')}
                    disabled={isSubmittingReview}
                    className="px-4 py-2 text-xs font-semibold rounded-lg bg-amber-600 hover:bg-amber-500 text-white transition-colors"
                  >
                    Request More Tests
                  </button>
                  <button
                    onClick={() => handleReviewDecision('APPROVE')}
                    disabled={isSubmittingReview || workflowState?.readiness_result?.status === 'BLOCKED'}
                    className="px-4 py-2 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                    title={workflowState?.readiness_result?.status === 'BLOCKED' ? 'Disabled: Blocked by critical regression' : ''}
                  >
                    Override & Approve
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

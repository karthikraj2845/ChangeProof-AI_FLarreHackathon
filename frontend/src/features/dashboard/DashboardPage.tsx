import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  GitPullRequest,
  AlertOctagon,
  Clock,
  ShieldCheck,
  Sparkles,
  ArrowRight,
  TrendingDown,
  Layers,
  Radio,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { apiClient } from '../../api/client';
import { DashboardSummary } from '../../types';
import { MetricCard } from '../../components/MetricCard';
import { StatusBadge } from '../../components/StatusBadge';

export const DashboardPage: React.FC = () => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [demoLaunching, setDemoLaunching] = useState(false);
  const navigate = useNavigate();

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getDashboardSummary();
      setSummary(data);
    } catch (err) {
      console.error('Error fetching dashboard summary:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleLaunchDemo = async () => {
    try {
      setDemoLaunching(true);
      await apiClient.launchDemo();
      navigate('/workflow');
    } catch (err) {
      console.error(err);
    } finally {
      setDemoLaunching(false);
    }
  };

  if (loading && !summary) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-400 mr-3"></div>
        Loading ChangeProof AI metrics...
      </div>
    );
  }

  // Chart data
  const testResultsData = [
    { name: 'Passing Tests', count: 7, color: '#22c55e' },
    { name: 'Behavioral Regressions', count: 1, color: '#f43f5e' },
    { name: 'Execution Errors', count: 0, color: '#f59e0b' },
  ];

  const artifactDistribution = [
    { name: 'Rules & Versions', count: 3, color: '#38bdf8' },
    { name: 'Requirements', count: 1, color: '#f59e0b' },
    { name: 'Core Services', count: 2, color: '#10b981' },
    { name: 'Configurations', count: 1, color: '#6366f1' },
    { name: 'Policy Workflows', count: 1, color: '#06b6d4' },
    { name: 'Regression Tests', count: 8, color: '#ec4899' },
  ];

  return (
    <div className="space-y-6">
      {/* Banner / Hero */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-sky-950/60 border border-slate-800 p-6 sm:p-8">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-950/80 border border-sky-800 text-sky-400 text-xs font-semibold mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Flarre.AI Innovation Challenge 2026 Core Workflow</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Insurance Change Assurance & IntentGuard Verification
          </h1>
          <p className="mt-2 text-sm sm:text-base text-slate-300 leading-relaxed">
            Every business rule change carries hidden transitive blast radiuses. ChangeProof AI combines
            LangGraph multi-agent orchestration, an authoritative NetworkX dependency graph, deterministic rule evaluation, and post-deployment event verification into a continuous evidence chain.
          </p>

          <div className="mt-6 flex flex-wrap gap-3">
            <button
              onClick={handleLaunchDemo}
              disabled={demoLaunching}
              className="inline-flex items-center px-5 py-2.5 rounded-xl font-semibold text-sm bg-gradient-to-r from-sky-400 to-emerald-400 text-slate-950 hover:from-sky-300 hover:to-emerald-300 transition-all shadow-lg shadow-sky-500/25 disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              {demoLaunching ? 'Executing LangGraph Workflow...' : 'Launch Seeded 3-Minute Demo'}
            </button>
            <button
              onClick={() => navigate('/workflow')}
              className="inline-flex items-center px-4 py-2.5 rounded-xl text-sm font-medium bg-slate-800/80 text-slate-200 hover:bg-slate-700 border border-slate-700 transition-all"
            >
              View Active Workflow
              <ArrowRight className="w-4 h-4 ml-1.5" />
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Change Requests"
          value={summary?.total_change_requests ?? 0}
          subtitle="Proposals in governance pipeline"
          icon={GitPullRequest}
          variant="default"
        />
        <MetricCard
          title="Seeded Regressions"
          value={summary?.seeded_regressions_detected ?? 0}
          subtitle="Behavioral regressions detected"
          icon={AlertOctagon}
          variant="danger"
        />
        <MetricCard
          title="Blocked Releases"
          value={summary?.blocked_releases ?? 0}
          subtitle="Deterministic policy gates active"
          icon={TrendingDown}
          variant="warning"
        />
        <MetricCard
          title="Open Findings (IntentGuard)"
          value={summary?.open_findings ?? 0}
          subtitle="Post-deployment verification findings"
          icon={Radio}
          variant="danger"
        />
      </div>

      {/* Visual Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Test Outcomes Chart */}
        <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/40 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-200">Regression Test Suite Verification</h3>
              <p className="text-xs text-slate-400">Baseline v1.0 vs Proposed v1.1 side-by-side execution</p>
            </div>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
              Deterministic
            </span>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={testResultsData} layout="vertical" margin={{ top: 10, right: 30, left: 40, bottom: 5 }}>
                <XAxis type="number" stroke="#64748b" fontSize={11} />
                <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={12} width={130} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {testResultsData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="text-xs text-slate-400 mt-2 text-center">
            7 tests passed specifications &bull; <strong className="text-rose-400">1 deliberate seeded regression detected in TEST-SD-002</strong>
          </p>
        </div>

        {/* Artifact Distribution Chart */}
        <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/40 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-200">Insurance Dependency Graph Coverage</h3>
              <p className="text-xs text-slate-400">NetworkX managed multi-tier artifacts</p>
            </div>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800">
              10 Total Nodes
            </span>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={artifactDistribution} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={10} angle={-20} textAnchor="end" />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {artifactDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="text-xs text-slate-400 mt-2 text-center">
            Requirements, Rules, Services, Configs & Test Suites fully connected with verified evidence edges
          </p>
        </div>
      </div>

      {/* Recent Workflows Table */}
      <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/40 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-200">Recent Change Assurance Executions</h3>
            <p className="text-xs text-slate-400">Persisted LangGraph workflow runs and audit state</p>
          </div>
          <button
            onClick={() => navigate('/changes')}
            className="text-xs font-medium text-sky-400 hover:text-sky-300 flex items-center"
          >
            View all change requests <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/60 text-slate-400 font-mono uppercase border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Workflow ID</th>
                <th className="py-2.5 px-3">Change Request</th>
                <th className="py-2.5 px-3">Current Node</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Started</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {(summary?.recent_workflows || []).map((wf) => (
                <tr key={wf.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 px-3 font-mono font-medium text-sky-400">{wf.id}</td>
                  <td className="py-3 px-3 font-medium text-slate-300">{wf.change_request_id}</td>
                  <td className="py-3 px-3 font-mono text-slate-400">{wf.current_node}</td>
                  <td className="py-3 px-3">
                    <StatusBadge status={wf.status} size="sm" />
                  </td>
                  <td className="py-3 px-3 text-slate-400">
                    {new Date(wf.start_time).toLocaleTimeString()}
                  </td>
                  <td className="py-3 px-3 text-right">
                    <button
                      onClick={() => navigate('/workflow')}
                      className="px-2.5 py-1 text-xs font-medium rounded bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700"
                    >
                      Inspect
                    </button>
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

import axios from 'axios';
import {
  HealthData,
  DashboardSummary,
  ChangeRequest,
  WorkflowState,
  Finding,
  AuditEvent,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiClient = {
  // Health & Dashboard
  getHealth: async (): Promise<HealthData> => {
    const res = await api.get('/health');
    return res.data;
  },

  getDashboardSummary: async (): Promise<DashboardSummary> => {
    const res = await api.get('/dashboard/summary');
    return res.data;
  },

  launchDemo: async (): Promise<{ message: string; change_request_id: string; workflow_result: WorkflowState }> => {
    const res = await api.post('/demo/launch');
    return res.data;
  },

  // Changes
  getChanges: async (): Promise<ChangeRequest[]> => {
    const res = await api.get('/changes');
    return res.data;
  },

  createChange: async (payload: { title: string; description: string; creator: string }): Promise<ChangeRequest> => {
    const res = await api.post('/changes', payload);
    return res.data;
  },

  getChange: async (changeId: string): Promise<any> => {
    const res = await api.get(`/changes/${changeId}`);
    return res.data;
  },

  // Workflows
  startChangeAssurance: async (changeRequestId: string, userRequest?: string): Promise<{ workflow_id: string; state: WorkflowState }> => {
    const res = await api.post('/workflows/change-assurance', {
      change_request_id: changeRequestId,
      user_request: userRequest,
    });
    return res.data;
  },

  getWorkflow: async (workflowId: string): Promise<{ id: string; status: string; current_node: string; state: WorkflowState }> => {
    const res = await api.get(`/workflows/${workflowId}`);
    return res.data;
  },

  resumeWorkflow: async (workflowId: string, payload: { reviewer: string; action: string; justification: string; snapshot_id?: string; snapshot_hash?: string }): Promise<any> => {
    const res = await api.post(`/workflows/${workflowId}/resume`, payload);
    return res.data;
  },

  // Impact & Tests
  getImpact: async (changeId: string): Promise<any> => {
    const res = await api.get(`/changes/${changeId}/impact`);
    return res.data;
  },

  runTests: async (changeId: string): Promise<any> => {
    const res = await api.post(`/changes/${changeId}/run-tests`);
    return res.data;
  },

  getReadiness: async (changeId: string): Promise<any> => {
    const res = await api.get(`/changes/${changeId}/readiness`);
    return res.data;
  },

  approveChange: async (changeId: string, reviewer: string, justification: string, snapshot_id?: string, snapshot_hash?: string): Promise<any> => {
    const res = await api.post(`/changes/${changeId}/approve`, { reviewer, justification, snapshot_id, snapshot_hash });
    return res.data;
  },

  rejectChange: async (changeId: string, reviewer: string, justification: string, snapshot_id?: string, snapshot_hash?: string): Promise<any> => {
    const res = await api.post(`/changes/${changeId}/reject`, { reviewer, justification, snapshot_id, snapshot_hash });
    return res.data;
  },

  // Graph
  getGraph: async (highlight?: string): Promise<{ nodes: any[]; edges: any[]; total_nodes: number; total_edges: number }> => {
    const res = await api.get('/graph', { params: { highlight } });
    return res.data;
  },

  getArtifactDetails: async (artifactId: string): Promise<any> => {
    const res = await api.get(`/graph/artifacts/${artifactId}`);
    return res.data;
  },

  // IntentGuard Verification
  simulateTransaction: async (payload: {
    transaction_id?: string;
    jurisdiction: string;
    driver_risk_score: number;
    vehicle_category: string;
    policy_active: boolean;
    approved_reference_version_id?: string;
    simulated_deployed_version_id?: string;
  }): Promise<any> => {
    const res = await api.post('/verification/simulate', {
      ...payload,
      approved_reference_version_id: payload.approved_reference_version_id || 'RULE-SAFE-DRIVER-v1.0',
      simulated_deployed_version_id: payload.simulated_deployed_version_id || 'RULE-SAFE-DRIVER-v1.1-proposed',
      linked_change_id: 'CR-2026-001',
    });
    return res.data;
  },

  // Findings & Audit
  getFindings: async (): Promise<Finding[]> => {
    const res = await api.get('/findings');
    return res.data;
  },

  updateFindingStatus: async (findingId: string, status: string): Promise<any> => {
    const res = await api.patch(`/findings/${findingId}`, { status });
    return res.data;
  },

  getAuditEvents: async (): Promise<AuditEvent[]> => {
    const res = await api.get('/audit');
    return res.data;
  },
};

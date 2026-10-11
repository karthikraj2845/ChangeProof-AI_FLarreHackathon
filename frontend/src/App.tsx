import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './layouts/AppLayout';
import { DashboardPage } from './features/dashboard/DashboardPage';
import { ChangesPage } from './features/changes/ChangesPage';
import { WorkflowPage } from './features/agent-workflow/WorkflowPage';
import { ImpactAnalysisPage } from './features/impact-analysis/ImpactAnalysisPage';
import { RegressionPage } from './features/regression/RegressionPage';
import { ReadinessPage } from './features/readiness/ReadinessPage';
import { IntentGuardPage } from './features/verification/IntentGuardPage';
import { FindingsPage } from './features/findings/FindingsPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="changes" element={<ChangesPage />} />
          <Route path="workflow" element={<WorkflowPage />} />
          <Route path="impact" element={<ImpactAnalysisPage />} />
          <Route path="regression" element={<RegressionPage />} />
          <Route path="readiness" element={<ReadinessPage />} />
          <Route path="intentguard" element={<IntentGuardPage />} />
          <Route path="findings" element={<FindingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;

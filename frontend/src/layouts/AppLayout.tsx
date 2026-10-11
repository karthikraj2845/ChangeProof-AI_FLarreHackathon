import React, { useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { apiClient } from '../api/client';

export const AppLayout: React.FC = () => {
  const [isLaunching, setIsLaunching] = useState(false);
  const navigate = useNavigate();

  const handleLaunchDemo = async () => {
    try {
      setIsLaunching(true);
      await apiClient.launchDemo();
      navigate('/workflow');
    } catch (err) {
      console.error('Failed to launch demo:', err);
    } finally {
      setIsLaunching(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      <Navbar onLaunchDemo={handleLaunchDemo} isLaunchingDemo={isLaunching} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Outlet />
      </main>

      <footer className="border-t border-slate-900 bg-slate-950/80 py-4 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>ChangeProof AI &bull; Flarre.AI Innovation Challenge 2026</span>
          <span className="font-mono text-[11px] text-slate-400">
            Deterministic Rule Engine &bull; NetworkX Graph &bull; LangGraph Agents &bull; IntentGuard
          </span>
        </div>
      </footer>
    </div>
  );
};

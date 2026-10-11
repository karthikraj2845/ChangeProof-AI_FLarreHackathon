import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  ShieldAlert,
  GitPullRequest,
  Bot,
  Network,
  CheckCircle2,
  AlertTriangle,
  Radio,
  FileSearch,
  Sparkles,
} from 'lucide-react';

interface NavbarProps {
  onLaunchDemo?: () => void;
  isLaunchingDemo?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ onLaunchDemo, isLaunchingDemo }) => {
  const navItems = [
    { name: 'Dashboard', path: '/', icon: Sparkles },
    { name: 'Changes', path: '/changes', icon: GitPullRequest },
    { name: 'Agent Workflow', path: '/workflow', icon: Bot },
    { name: 'RuleRipple Impact', path: '/impact', icon: Network },
    { name: 'Regression Tests', path: '/regression', icon: CheckCircle2 },
    { name: 'Release Readiness', path: '/readiness', icon: AlertTriangle },
    { name: 'IntentGuard', path: '/intentguard', icon: Radio },
    { name: 'Findings & Audit', path: '/findings', icon: FileSearch },
  ];

  return (
    <header className="sticky top-0 z-50 bg-slate-900/90 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-emerald-400 flex items-center justify-center shadow-lg shadow-sky-500/20">
              <ShieldAlert className="w-6 h-6 text-slate-950 font-bold" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-sky-400 bg-clip-text text-transparent">
                  ChangeProof AI
                </span>
                <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800">
                  Flarre Hackathon 2026
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">
                Every Insurance Change. Traced, Tested, Verified.
              </p>
            </div>
          </div>

          {/* Quick Demo Launch Button */}
          {onLaunchDemo && (
            <div className="flex items-center space-x-3">
              <button
                onClick={onLaunchDemo}
                disabled={isLaunchingDemo}
                className="inline-flex items-center px-4 py-2 text-xs font-semibold rounded-lg bg-gradient-to-r from-sky-500 to-emerald-500 text-slate-950 hover:from-sky-400 hover:to-emerald-400 transition-all shadow-md shadow-sky-500/20 disabled:opacity-50"
              >
                <Sparkles className="w-4 h-4 mr-1.5" />
                {isLaunchingDemo ? 'Executing Demo...' : 'Launch Demo Scenario'}
              </button>
            </div>
          )}
        </div>

        {/* Tab Navigation */}
        <nav className="flex space-x-1 overflow-x-auto pb-2 scrollbar-none">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center px-3 py-1.5 text-xs font-medium rounded-lg whitespace-nowrap transition-colors ${
                    isActive
                      ? 'bg-slate-800 text-sky-400 border border-slate-700 font-semibold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`
                }
              >
                <Icon className="w-3.5 h-3.5 mr-1.5 opacity-80" />
                {item.name}
              </NavLink>
            );
          })}
        </nav>
      </div>
    </header>
  );
};

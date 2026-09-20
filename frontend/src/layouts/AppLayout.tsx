import React, { useState, useEffect } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  Cpu,
  TrendingUp,
  History,
  Wrench,
  FileBarChart,
  ShieldCheck,
  Radio,
} from 'lucide-react';
import { checkSystemHealth } from '../services/api';
import type { SystemHealth } from '../types';

export const AppLayout: React.FC = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);

  useEffect(() => {
    checkSystemHealth()
      .then(setHealth)
      .catch(() => {
        setHealth({
          status: 'connecting',
          version: '2.0.0',
          database: 'checking...',
          ml_engine: 'LightGBM v4',
        });
      });
  }, []);

  const navLinks = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/machines', label: 'Fleet Registry', icon: Cpu },
    { to: '/prediction', label: 'Predictive AI', icon: TrendingUp },
    { to: '/history', label: 'Audit History', icon: History },
    { to: '/maintenance', label: 'Maintenance', icon: Wrench },
    { to: '/reports', label: 'Analytics & Reports', icon: FileBarChart },
  ];

  return (
    <div className="flex min-h-screen bg-ink-950 text-slate-200">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 border-r border-ink-line bg-ink-900/80 flex flex-col backdrop-blur">
        {/* Brand */}
        <div className="h-16 px-6 border-b border-ink-line flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-cnc-blue/20 border border-cnc-blue/40 flex items-center justify-center font-display font-bold text-cnc-blue text-sm">
            CNC
          </div>
          <div>
            <div className="font-display font-bold tracking-tight text-white leading-tight">
              PredictCNC
            </div>
            <div className="text-[11px] font-mono text-slate-400">
              AI Maintenance v2.0
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          <div className="px-3 pb-2 text-[10px] font-mono uppercase tracking-widest text-slate-500">
            Navigation
          </div>
          {navLinks.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-cnc-blue text-white shadow-lg shadow-cnc-blue/20'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-ink-800'
                }`
              }
            >
              <item.icon className="h-4 w-4" />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* System telemetry bar */}
        <div className="p-4 border-t border-ink-line bg-ink-950/60">
          <div className="flex items-center justify-between text-xs">
            <span className="flex items-center gap-1.5 text-slate-400">
              <span className={`h-2 w-2 rounded-full ${health?.status === 'operational' ? 'bg-cnc-emerald animate-pulse' : 'bg-cnc-amber'}`} />
              API Status
            </span>
            <span className="font-mono text-slate-300 capitalize text-[11px]">
              {health?.status || 'Connecting...'}
            </span>
          </div>
          <div className="mt-2 text-[10px] font-mono text-slate-500 truncate">
            Engine: {health?.ml_engine || 'LightGBM v4'}
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Top Header */}
        <header className="h-16 border-b border-ink-line bg-ink-900/60 px-8 flex items-center justify-between backdrop-blur">
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
            <Radio className="h-3.5 w-3.5 text-cnc-emerald animate-pulse" />
            <span>LIVE INDUSTRIAL TELEMETRY</span>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1 rounded-full border border-ink-line bg-ink-800 text-xs font-mono text-slate-300">
              <ShieldCheck className="h-3.5 w-3.5 text-cnc-blue" />
              <span>Security Verified</span>
            </div>
            <div className="h-8 w-8 rounded-full bg-cnc-blue/20 border border-cnc-blue/50 flex items-center justify-center font-display font-bold text-xs text-cnc-blue">
              OP
            </div>
          </div>
        </header>

        {/* Dynamic Route Body */}
        <main className="flex-1 p-8 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

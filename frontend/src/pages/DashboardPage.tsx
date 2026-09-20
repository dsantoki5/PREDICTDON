import React, { useEffect, useState } from 'react';
import { GaugeCard } from '../components/GaugeCard';
import { MachineStatusBadge } from '../components/MachineStatusBadge';
import {
  Cpu,
  ShieldCheck,
  AlertTriangle,
  AlertOctagon,
  Activity,
  ArrowUpRight,
  TrendingUp,
  Wrench,
  Sparkles,
  RefreshCw,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { getDashboardSummary } from '../services/api';
import type { DashboardSummary } from '../types';

export const DashboardPage: React.FC = () => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchSummary = async () => {
    setLoading(true);
    try {
      const data = await getDashboardSummary();
      setSummary(data);
    } catch (err) {
      console.error('Failed to load dashboard summary:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-mono uppercase tracking-wider text-cnc-blue">Fleet Overview</span>
          <h1 className="text-2xl font-display font-bold text-white tracking-tight">System Dashboard</h1>
          <p className="text-sm text-slate-400 mt-0.5">Real-time telemetry, fleet health monitoring, and AI predictive maintenance.</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchSummary}
            className="p-2.5 rounded-lg border border-ink-line bg-ink-800 text-slate-400 hover:text-white hover:border-slate-600 transition-colors"
            title="Refresh statistics"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin text-cnc-blue' : ''}`} />
          </button>
          <Link
            to="/prediction"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-cnc-blue text-white text-sm font-medium hover:bg-blue-600 transition-colors shadow-lg shadow-cnc-blue/20"
          >
            <Sparkles className="h-4 w-4" />
            <span>Run New Prediction</span>
          </Link>
        </div>
      </div>

      {/* KPI Gauges */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <GaugeCard
          label="Total Fleet"
          value={summary?.total_machines ?? '--'}
          sublabel="CNC Units Active"
          icon={<Cpu className="h-5 w-5" />}
          tone="primary"
        />
        <GaugeCard
          label="Healthy Units"
          value={summary?.healthy ?? '--'}
          sublabel="Nominal State"
          icon={<ShieldCheck className="h-5 w-5" />}
          tone="success"
        />
        <GaugeCard
          label="Warning State"
          value={summary?.warning ?? '--'}
          sublabel="Inspection Advised"
          icon={<AlertTriangle className="h-5 w-5" />}
          tone="warning"
        />
        <GaugeCard
          label="Critical Risk"
          value={summary?.critical ?? '--'}
          sublabel="Immediate Action"
          icon={<AlertOctagon className="h-5 w-5" />}
          tone="danger"
        />
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-xl border border-ink-line bg-ink-800/60 p-4 flex items-center justify-between">
          <div>
            <div className="text-xs font-mono text-slate-400">Total Predictions</div>
            <div className="text-xl font-display font-bold text-white mt-1">
              {summary?.total_predictions ?? '--'}
            </div>
          </div>
          <div className="h-10 w-10 rounded-lg bg-cnc-sky/10 border border-cnc-sky/30 flex items-center justify-center text-cnc-sky">
            <TrendingUp className="h-5 w-5" />
          </div>
        </div>

        <div className="rounded-xl border border-ink-line bg-ink-800/60 p-4 flex items-center justify-between">
          <div>
            <div className="text-xs font-mono text-slate-400">Average Fleet Health</div>
            <div className="text-xl font-display font-bold text-cnc-emerald mt-1">
              {summary ? `${summary.avg_health}%` : '--'}
            </div>
          </div>
          <div className="h-10 w-10 rounded-lg bg-cnc-emerald/10 border border-cnc-emerald/30 flex items-center justify-center text-cnc-emerald">
            <ShieldCheck className="h-5 w-5" />
          </div>
        </div>

        <div className="rounded-xl border border-ink-line bg-ink-800/60 p-4 flex items-center justify-between">
          <div>
            <div className="text-xs font-mono text-slate-400">Pending Work Tickets</div>
            <div className="text-xl font-display font-bold text-cnc-amber mt-1">
              {summary?.pending_maintenance ?? '--'}
            </div>
          </div>
          <div className="h-10 w-10 rounded-lg bg-cnc-amber/10 border border-cnc-amber/30 flex items-center justify-center text-cnc-amber">
            <Wrench className="h-5 w-5" />
          </div>
        </div>
      </div>

      {/* Recent Tables Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Predictions */}
        <div className="rounded-xl border border-ink-line bg-ink-800/80 p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-ink-line pb-4 mb-4">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-cnc-blue" />
                <h2 className="font-display font-semibold text-white">Recent Prediction Runs</h2>
              </div>
              <Link to="/history" className="text-xs font-mono text-cnc-blue hover:underline flex items-center gap-1">
                <span>View Full Log</span>
                <ArrowUpRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-ink-line/60 text-slate-400 font-mono">
                    <th className="pb-2">Machine</th>
                    <th className="pb-2">Prediction</th>
                    <th className="pb-2">Probability</th>
                    <th className="pb-2">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ink-line/40 text-slate-300">
                  {summary?.recent_predictions.map((p) => (
                    <tr key={p.id} className="hover:bg-ink-750/50">
                      <td className="py-2.5 font-mono font-medium text-white">{p.machine_code || `ID #${p.machine_id}`}</td>
                      <td className="py-2.5">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${
                            p.prediction === 'Machine Failure'
                              ? 'bg-cnc-rose/15 text-cnc-rose border border-cnc-rose/30'
                              : 'bg-cnc-emerald/15 text-cnc-emerald border border-cnc-emerald/30'
                          }`}
                        >
                          {p.prediction}
                        </span>
                      </td>
                      <td className="py-2.5 font-mono">{Number(p.probability).toFixed(1)}%</td>
                      <td className="py-2.5 text-slate-500 font-mono text-[11px]">
                        {new Date(p.predicted_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                  {(!summary?.recent_predictions || summary.recent_predictions.length === 0) && (
                    <tr>
                      <td colSpan={4} className="py-4 text-center text-slate-500 font-mono">
                        No recent predictions recorded.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Fleet Machines Overview */}
        <div className="rounded-xl border border-ink-line bg-ink-800/80 p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-ink-line pb-4 mb-4">
              <div className="flex items-center gap-2">
                <Cpu className="h-4 w-4 text-cnc-blue" />
                <h2 className="font-display font-semibold text-white">Registered Fleet</h2>
              </div>
              <Link to="/machines" className="text-xs font-mono text-cnc-blue hover:underline flex items-center gap-1">
                <span>Manage Fleet</span>
                <ArrowUpRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-ink-line/60 text-slate-400 font-mono">
                    <th className="pb-2">Code</th>
                    <th className="pb-2">Machine Name</th>
                    <th className="pb-2">Department</th>
                    <th className="pb-2">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ink-line/40 text-slate-300">
                  {summary?.recent_machines.map((m) => (
                    <tr key={m.id} className="hover:bg-ink-750/50">
                      <td className="py-2.5 font-mono font-bold text-cnc-blue">{m.machine_code}</td>
                      <td className="py-2.5 text-white">{m.machine_name}</td>
                      <td className="py-2.5 text-slate-400">{m.department || '--'}</td>
                      <td className="py-2.5">
                        <MachineStatusBadge status={m.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

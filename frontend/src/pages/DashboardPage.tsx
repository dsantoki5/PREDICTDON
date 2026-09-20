import React from 'react';
import { GaugeCard } from '../components/GaugeCard';
import { Cpu, ShieldCheck, AlertTriangle, AlertOctagon, Activity, ArrowUpRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export const DashboardPage: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-xs font-mono uppercase tracking-wider text-cnc-blue">Fleet Overview</span>
          <h1 className="text-2xl font-display font-bold text-white tracking-tight">System Dashboard</h1>
          <p className="text-sm text-slate-400 mt-0.5">Real-time machine health and AI predictive failure telemetry.</p>
        </div>
        <Link
          to="/prediction"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-cnc-blue text-white text-sm font-medium hover:bg-blue-600 transition-colors shadow-lg shadow-cnc-blue/20"
        >
          <Activity className="h-4 w-4" />
          <span>Run New Prediction</span>
        </Link>
      </div>

      {/* KPI Gauges */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <GaugeCard
          label="Total Fleet"
          value="12"
          sublabel="CNC Units Active"
          icon={<Cpu className="h-5 w-5" />}
          tone="primary"
        />
        <GaugeCard
          label="Healthy"
          value="9"
          sublabel="Nominal State"
          icon={<ShieldCheck className="h-5 w-5" />}
          tone="success"
        />
        <GaugeCard
          label="Warning"
          value="2"
          sublabel="Maintenance Advised"
          icon={<AlertTriangle className="h-5 w-5" />}
          tone="warning"
        />
        <GaugeCard
          label="Critical Risk"
          value="1"
          sublabel="Immediate Action"
          icon={<AlertOctagon className="h-5 w-5" />}
          tone="danger"
        />
      </div>

      {/* Overview Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-xl border border-ink-line bg-ink-800/80 p-6">
          <div className="flex items-center justify-between border-b border-ink-line pb-4 mb-4">
            <h2 className="font-display font-semibold text-white">AI Diagnostic Engine</h2>
            <span className="text-xs font-mono text-cnc-emerald bg-cnc-emerald/10 px-2 py-0.5 rounded border border-cnc-emerald/30">
              Model Online
            </span>
          </div>
          <div className="space-y-4 text-sm text-slate-300 leading-relaxed">
            <p>
              PredictCNC utilizes a high-precision <strong>LightGBM binary classifier</strong> tuned on the UCI AI4I 2020 Predictive Maintenance benchmark, achieving an authentic <strong>99.60% accuracy</strong> and <strong>94.22% F1-score</strong>.
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
              <div className="p-3 rounded-lg border border-ink-line bg-ink-900/60">
                <div className="text-[11px] font-mono text-slate-400">Accuracy</div>
                <div className="text-lg font-display font-bold text-cnc-emerald">99.60%</div>
              </div>
              <div className="p-3 rounded-lg border border-ink-line bg-ink-900/60">
                <div className="text-[11px] font-mono text-slate-400">Precision</div>
                <div className="text-lg font-display font-bold text-cnc-blue">92.35%</div>
              </div>
              <div className="p-3 rounded-lg border border-ink-line bg-ink-900/60">
                <div className="text-[11px] font-mono text-slate-400">Recall</div>
                <div className="text-lg font-display font-bold text-cnc-amber">96.17%</div>
              </div>
              <div className="p-3 rounded-lg border border-ink-line bg-ink-900/60">
                <div className="text-[11px] font-mono text-slate-400">ROC-AUC</div>
                <div className="text-lg font-display font-bold text-cnc-sky">99.86%</div>
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-ink-line bg-ink-800/80 p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-ink-line pb-4 mb-4">
              <h2 className="font-display font-semibold text-white">Quick Shortcuts</h2>
            </div>
            <div className="space-y-2">
              <Link
                to="/machines"
                className="flex items-center justify-between p-3 rounded-lg border border-ink-line bg-ink-900/40 hover:bg-ink-700/50 transition-colors text-sm text-slate-300 group"
              >
                <span>Manage Fleet Machines</span>
                <ArrowUpRight className="h-4 w-4 text-slate-500 group-hover:text-white transition-colors" />
              </Link>
              <Link
                to="/history"
                className="flex items-center justify-between p-3 rounded-lg border border-ink-line bg-ink-900/40 hover:bg-ink-700/50 transition-colors text-sm text-slate-300 group"
              >
                <span>View Prediction Log</span>
                <ArrowUpRight className="h-4 w-4 text-slate-500 group-hover:text-white transition-colors" />
              </Link>
              <Link
                to="/maintenance"
                className="flex items-center justify-between p-3 rounded-lg border border-ink-line bg-ink-900/40 hover:bg-ink-700/50 transition-colors text-sm text-slate-300 group"
              >
                <span>Active Work Tickets</span>
                <ArrowUpRight className="h-4 w-4 text-slate-500 group-hover:text-white transition-colors" />
              </Link>
            </div>
          </div>
          <div className="pt-4 text-xs font-mono text-slate-500 border-t border-ink-line mt-4">
            Backend API: v2.0.0 FastREST
          </div>
        </div>
      </div>
    </div>
  );
};

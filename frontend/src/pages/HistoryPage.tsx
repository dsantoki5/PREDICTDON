import React, { useState, useEffect } from 'react';
import { Trash2, RefreshCw } from 'lucide-react';
import { getPredictionHistory, deletePredictionHistoryItem, getMachines } from '../services/api';
import type { PredictionHistoryItem, Machine } from '../types';

export const HistoryPage: React.FC = () => {
  const [history, setHistory] = useState<PredictionHistoryItem[]>([]);
  const [machines, setMachines] = useState<Machine[]>([]);
  const [selectedMachine, setSelectedMachine] = useState<number | ''>('');
  const [loading, setLoading] = useState(true);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await getPredictionHistory({
        machine_id: selectedMachine ? Number(selectedMachine) : undefined,
      });
      setHistory(data);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getMachines().then(setMachines);
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [selectedMachine]);

  const handleDelete = async (id: number) => {
    if (window.confirm('Delete this historical prediction record?')) {
      try {
        await deletePredictionHistoryItem(id);
        fetchHistory();
      } catch (err) {
        alert('Failed to delete history item.');
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-mono uppercase tracking-wider text-cnc-blue">Audit Trail</span>
          <h1 className="text-2xl font-display font-bold text-white tracking-tight">Prediction History</h1>
          <p className="text-sm text-slate-400 mt-0.5">Comprehensive audit log of all AI machine evaluations and sensor inputs.</p>
        </div>
        <button
          onClick={fetchHistory}
          className="p-2.5 rounded-lg border border-ink-line bg-ink-800 text-slate-400 hover:text-white transition-colors self-start"
          title="Refresh Log"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin text-cnc-blue' : ''}`} />
        </button>
      </div>

      {/* Filter Bar */}
      <div className="rounded-xl border border-ink-line bg-ink-800/70 p-4 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <label className="text-xs font-mono text-slate-400">Filter by Machine:</label>
          <select
            value={selectedMachine}
            onChange={(e) => setSelectedMachine(e.target.value ? Number(e.target.value) : '')}
            className="rounded-lg border border-ink-line bg-ink-900 px-3 py-1.5 text-xs text-white font-mono focus:border-cnc-blue focus:outline-none"
          >
            <option value="">All Machines ({history.length} runs)</option>
            {machines.map((m) => (
              <option key={m.id} value={m.id}>
                {m.machine_code} — {m.machine_name}
              </option>
            ))}
          </select>
        </div>
        <span className="text-xs font-mono text-slate-400">
          Showing {history.length} Recorded Runs
        </span>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-ink-line bg-ink-800/80 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-ink-line bg-ink-900/60 text-slate-400 uppercase tracking-wider text-[11px]">
                <th className="py-3 px-4">Run ID</th>
                <th className="py-3 px-4">Machine</th>
                <th className="py-3 px-4">Air Temp</th>
                <th className="py-3 px-4">Proc Temp</th>
                <th className="py-3 px-4">RPM</th>
                <th className="py-3 px-4">Torque</th>
                <th className="py-3 px-4">Tool Wear</th>
                <th className="py-3 px-4">Prediction</th>
                <th className="py-3 px-4">Probability</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-line/40 text-slate-300">
              {history.map((row) => (
                <tr key={row.id} className="hover:bg-ink-750/50 transition-colors">
                  <td className="py-3 px-4 text-slate-500 font-bold">#{row.id}</td>
                  <td className="py-3 px-4 font-bold text-white font-sans">{row.machine_code || `ID #${row.machine_id}`}</td>
                  <td className="py-3 px-4 text-slate-400">{Number(row.air_temperature).toFixed(1)} K</td>
                  <td className="py-3 px-4 text-slate-400">{Number(row.process_temperature).toFixed(1)} K</td>
                  <td className="py-3 px-4 font-bold text-slate-200">{Number(row.rotational_speed).toFixed(0)}</td>
                  <td className="py-3 px-4 text-slate-400">{Number(row.torque).toFixed(1)} Nm</td>
                  <td className="py-3 px-4 text-slate-400">{Number(row.tool_wear).toFixed(0)} m</td>
                  <td className="py-3 px-4 font-sans">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold ${
                        row.prediction === 'Machine Failure'
                          ? 'bg-cnc-rose/20 text-cnc-rose border border-cnc-rose/30'
                          : 'bg-cnc-emerald/20 text-cnc-emerald border border-cnc-emerald/30'
                      }`}
                    >
                      {row.prediction}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-bold">
                    {Number(row.probability).toFixed(1)}%
                  </td>
                  <td className="py-3 px-4 text-slate-500 text-[11px]">
                    {new Date(row.predicted_at).toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => handleDelete(row.id)}
                      className="p-1 rounded text-slate-500 hover:text-cnc-rose transition-colors"
                      title="Delete Record"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
              {history.length === 0 && !loading && (
                <tr>
                  <td colSpan={11} className="py-8 text-center text-slate-500">
                    No prediction history recorded.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

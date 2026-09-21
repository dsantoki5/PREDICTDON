import React, { useState, useEffect } from 'react';
import { useLocation, Link } from 'react-router-dom';
import {
  Sparkles,
  Cpu,
  Thermometer,
  Zap,
  RotateCw,
  Clock,
  ShieldCheck,
  AlertOctagon,
  Wrench,
  CheckCircle2,
  Activity,
} from 'lucide-react';
import { getMachines, runPrediction } from '../services/api';
import type { Machine, PredictionResult } from '../types';

export const PredictionPage: React.FC = () => {
  const location = useLocation();
  const preSelectedId = (location.state as any)?.machine_id;

  const [machines, setMachines] = useState<Machine[]>([]);
  const [selectedMachineId, setSelectedMachineId] = useState<number | ''>(preSelectedId || '');
  
  // Sensor parameters - Manual input
  const [inputs, setInputs] = useState({
    air_temperature: '',
    process_temperature: '',
    rotational_speed: '',
    torque: '',
    tool_wear: '',
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getMachines().then((data) => {
      setMachines(data);
      if (data.length > 0 && !selectedMachineId) {
        setSelectedMachineId(data[0].id);
      }
    });
  }, []);

  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMachineId) {
      setError('Please select a CNC machine.');
      return;
    }
    if (
      inputs.air_temperature === '' ||
      inputs.process_temperature === '' ||
      inputs.rotational_speed === '' ||
      inputs.torque === '' ||
      inputs.tool_wear === ''
    ) {
      setError('Please enter all sensor parameters manually.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const res = await runPrediction({
        machine_id: Number(selectedMachineId),
        air_temperature: Number(inputs.air_temperature),
        process_temperature: Number(inputs.process_temperature),
        rotational_speed: Number(inputs.rotational_speed),
        torque: Number(inputs.torque),
        tool_wear: Number(inputs.tool_wear),
      });
      setResult(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Prediction failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <span className="text-xs font-mono uppercase tracking-wider text-cnc-blue">AI Inference Engine</span>
        <h1 className="text-2xl font-display font-bold text-white tracking-tight">Predict Machine Condition</h1>
        <p className="text-sm text-slate-400 mt-0.5">Enter live sensor readings manually to evaluate failure probabilities and physics-based root cause diagnostics.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Input Parameters Form */}
        <div className="lg:col-span-5 space-y-4">
          <div className="rounded-xl border border-ink-line bg-ink-800/80 p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-ink-line pb-3">
              <div className="flex items-center gap-2 font-display font-semibold text-white text-base">
                <Cpu className="h-4 w-4 text-cnc-blue" />
                <span>Manual Telemetry Input</span>
              </div>
              <span className="text-[10px] font-mono text-slate-500 uppercase">LightGBM v4</span>
            </div>

            <form onSubmit={handlePredict} className="space-y-4 text-xs">
              {/* Machine Selection */}
              <div>
                <label className="block text-slate-400 font-mono mb-1">Target CNC Machine *</label>
                <select
                  value={selectedMachineId}
                  onChange={(e) => setSelectedMachineId(Number(e.target.value))}
                  required
                  className="w-full rounded-lg border border-ink-line bg-ink-900 p-2.5 text-white text-xs font-mono focus:border-cnc-blue focus:outline-none"
                >
                  {machines.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.machine_code} — {m.machine_name} ({m.department})
                    </option>
                  ))}
                </select>
              </div>

              {/* Air Temperature */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-slate-400 font-mono flex items-center gap-1.5">
                    <Thermometer className="h-3.5 w-3.5 text-cnc-sky" />
                    Air Temperature [K]
                  </label>
                  <span className="font-mono text-slate-500 text-[11px]">{inputs.air_temperature ? `${inputs.air_temperature} K` : 'Kelvin [K]'}</span>
                </div>
                <input
                  type="number"
                  step="0.01"
                  required
                  placeholder="e.g. 298.15"
                  value={inputs.air_temperature}
                  onChange={(e) => setInputs({ ...inputs, air_temperature: e.target.value })}
                  className="w-full rounded border border-ink-line bg-ink-900 p-2.5 text-white font-mono text-xs focus:border-cnc-blue focus:outline-none"
                />
              </div>

              {/* Process Temperature */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-slate-400 font-mono flex items-center gap-1.5">
                    <Thermometer className="h-3.5 w-3.5 text-cnc-rose" />
                    Process Temperature [K]
                  </label>
                  <span className="font-mono text-slate-500 text-[11px]">{inputs.process_temperature ? `${inputs.process_temperature} K` : 'Kelvin [K]'}</span>
                </div>
                <input
                  type="number"
                  step="0.01"
                  required
                  placeholder="e.g. 308.65"
                  value={inputs.process_temperature}
                  onChange={(e) => setInputs({ ...inputs, process_temperature: e.target.value })}
                  className="w-full rounded border border-ink-line bg-ink-900 p-2.5 text-white font-mono text-xs focus:border-cnc-blue focus:outline-none"
                />
              </div>

              {/* Rotational Speed */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-slate-400 font-mono flex items-center gap-1.5">
                    <RotateCw className="h-3.5 w-3.5 text-cnc-amber" />
                    Spindle Speed [RPM]
                  </label>
                  <span className="font-mono text-slate-500 text-[11px]">{inputs.rotational_speed ? `${inputs.rotational_speed} RPM` : 'Revolutions/min'}</span>
                </div>
                <input
                  type="number"
                  step="1"
                  required
                  placeholder="e.g. 1500"
                  value={inputs.rotational_speed}
                  onChange={(e) => setInputs({ ...inputs, rotational_speed: e.target.value })}
                  className="w-full rounded border border-ink-line bg-ink-900 p-2.5 text-white font-mono text-xs focus:border-cnc-blue focus:outline-none"
                />
              </div>

              {/* Torque */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-slate-400 font-mono flex items-center gap-1.5">
                    <Zap className="h-3.5 w-3.5 text-cnc-blue" />
                    Cutting Torque [Nm]
                  </label>
                  <span className="font-mono text-slate-500 text-[11px]">{inputs.torque ? `${inputs.torque} Nm` : 'Newton-meters [Nm]'}</span>
                </div>
                <input
                  type="number"
                  step="0.1"
                  required
                  placeholder="e.g. 40.0"
                  value={inputs.torque}
                  onChange={(e) => setInputs({ ...inputs, torque: e.target.value })}
                  className="w-full rounded border border-ink-line bg-ink-900 p-2.5 text-white font-mono text-xs focus:border-cnc-blue focus:outline-none"
                />
              </div>

              {/* Tool Wear */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-slate-400 font-mono flex items-center gap-1.5">
                    <Clock className="h-3.5 w-3.5 text-purple-400" />
                    Tool Wear [Minutes]
                  </label>
                  <span className="font-mono text-slate-500 text-[11px]">{inputs.tool_wear ? `${inputs.tool_wear} min` : 'Cumulative min'}</span>
                </div>
                <input
                  type="number"
                  step="1"
                  required
                  placeholder="e.g. 80"
                  value={inputs.tool_wear}
                  onChange={(e) => setInputs({ ...inputs, tool_wear: e.target.value })}
                  className="w-full rounded border border-ink-line bg-ink-900 p-2.5 text-white font-mono text-xs focus:border-cnc-blue focus:outline-none"
                />
              </div>

              {error && <div className="text-xs text-cnc-rose font-mono">{error}</div>}

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 rounded-lg bg-cnc-blue text-white font-medium text-xs hover:bg-blue-600 transition-all flex items-center justify-center gap-2 shadow-lg shadow-cnc-blue/20"
              >
                {loading ? (
                  <>
                    <Activity className="h-4 w-4 animate-spin" />
                    <span>Running AI Model...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    <span>Execute Failure Prediction</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Prediction Results & RCA Panel */}
        <div className="lg:col-span-7 space-y-4">
          {result ? (
            <div className="space-y-4 animate-fadeIn">
              {/* Top Banner */}
              <div
                className={`rounded-xl border p-5 flex items-center justify-between ${
                  result.is_failure
                    ? 'border-cnc-rose/40 bg-cnc-rose/10 text-cnc-rose'
                    : 'border-cnc-emerald/40 bg-cnc-emerald/10 text-cnc-emerald'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`h-12 w-12 rounded-xl flex items-center justify-center ${
                      result.is_failure ? 'bg-cnc-rose/20 text-cnc-rose' : 'bg-cnc-emerald/20 text-cnc-emerald'
                    }`}
                  >
                    {result.is_failure ? <AlertOctagon className="h-7 w-7" /> : <ShieldCheck className="h-7 w-7" />}
                  </div>
                  <div>
                    <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400">Model Outcome</span>
                    <h2 className="text-xl font-display font-bold text-white tracking-tight">{result.prediction}</h2>
                    <div className="text-xs text-slate-300 mt-0.5">
                      Target Machine: <strong className="text-white">{result.machine_code}</strong> ({result.machine_name})
                    </div>
                  </div>
                </div>

                <div className="text-right">
                  <span
                    className={`inline-block px-3 py-1 rounded-full text-xs font-mono font-bold uppercase ${
                      result.risk_level === 'High'
                        ? 'bg-cnc-rose text-white'
                        : result.risk_level === 'Medium'
                        ? 'bg-cnc-amber text-black'
                        : 'bg-cnc-emerald text-black'
                    }`}
                  >
                    {result.risk_level} Risk
                  </span>
                  <div className="text-[11px] font-mono text-slate-400 mt-1">
                    Risk Score: {result.root_cause_analysis.risk_score}/100
                  </div>
                </div>
              </div>

              {/* Model Version Tag */}
              <div className="flex items-center justify-between px-1 text-xs font-mono text-slate-400">
                <span>Model: <strong className="text-blue-400">{result.model_version || 'LightGBM_No_SMOTE_Final v4.2'}</strong> (44 Features)</span>
                <span className="text-emerald-400 font-semibold">Multi-Class Ingestion Active</span>
              </div>

              {/* 3-Class Probability Breakdown */}
              {result.class_probabilities && (
                <div className="rounded-xl border border-slate-800 bg-[#0B0F1D] p-4 space-y-3">
                  <div className="text-[11px] font-mono uppercase text-slate-400 font-semibold flex items-center justify-between">
                    <span>Multi-Class Probability Distribution</span>
                    <span className="text-blue-400">Class {result.predicted_class ?? 0} Dominant</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {/* Class 0 */}
                    <div className="p-3 rounded-lg bg-[#070A13] border border-slate-800/80">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-slate-300 font-medium">Class 0: Nominal</span>
                        <span className="font-mono text-emerald-400 font-bold">{result.class_probabilities.normal.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                        <div className="bg-emerald-500 h-full rounded-full transition-all duration-500" style={{ width: `${result.class_probabilities.normal}%` }} />
                      </div>
                    </div>

                    {/* Class 1 */}
                    <div className="p-3 rounded-lg bg-[#070A13] border border-slate-800/80">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-slate-300 font-medium">Class 1: Anomaly</span>
                        <span className="font-mono text-amber-400 font-bold">{result.class_probabilities.warning.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                        <div className="bg-amber-500 h-full rounded-full transition-all duration-500" style={{ width: `${result.class_probabilities.warning}%` }} />
                      </div>
                    </div>

                    {/* Class 2 */}
                    <div className="p-3 rounded-lg bg-[#070A13] border border-slate-800/80">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-slate-300 font-medium">Class 2: Failure</span>
                        <span className="font-mono text-rose-400 font-bold">{result.class_probabilities.critical.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                        <div className="bg-rose-500 h-full rounded-full transition-all duration-500" style={{ width: `${result.class_probabilities.critical}%` }} />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Gauges Breakdown */}
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-xl border border-slate-800 bg-[#0B0F1D] p-4">
                  <div className="text-[11px] font-mono uppercase text-slate-400">Machine Health Score</div>
                  <div className="text-2xl font-display font-bold text-emerald-400 mt-1">
                    {result.machine_health.toFixed(1)}%
                  </div>
                  <div className="w-full bg-slate-900 rounded-full h-2 mt-2 overflow-hidden border border-slate-800">
                    <div
                      className="bg-emerald-500 h-full transition-all duration-500"
                      style={{ width: `${result.machine_health}%` }}
                    />
                  </div>
                </div>

                <div className="rounded-xl border border-slate-800 bg-[#0B0F1D] p-4">
                  <div className="text-[11px] font-mono uppercase text-slate-400">Failure Risk Probability</div>
                  <div className="text-2xl font-display font-bold text-rose-400 mt-1">
                    {result.failure_probability.toFixed(1)}%
                  </div>
                  <div className="w-full bg-slate-900 rounded-full h-2 mt-2 overflow-hidden border border-slate-800">
                    <div
                      className="bg-rose-500 h-full transition-all duration-500"
                      style={{ width: `${result.failure_probability}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Automated Ticket Banner */}
              {result.ticket_created && (
                <div className="p-4 rounded-xl border border-cnc-amber/40 bg-cnc-amber/10 text-cnc-amber flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <Wrench className="h-4 w-4" />
                    <span>
                      Automated Maintenance Ticket Created (Priority: <strong>{result.ticket_priority}</strong>).
                    </span>
                  </div>
                  <Link to="/maintenance" className="font-mono text-white underline hover:text-cnc-amber">
                    View Tickets &rarr;
                  </Link>
                </div>
              )}

              {/* AI Root Cause Analysis Diagnostics */}
              <div className="rounded-xl border border-ink-line bg-ink-800/90 p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-ink-line pb-3">
                  <h3 className="font-display font-semibold text-white text-sm">AI Root Cause Analysis (RCA)</h3>
                  <span className="text-[11px] font-mono text-cnc-blue bg-cnc-blue/10 px-2 py-0.5 rounded border border-cnc-blue/30">
                    Physics-Informed Diagnostics
                  </span>
                </div>

                {/* Causes & Components */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="font-mono text-slate-400 uppercase text-[10px] block mb-1">Identified Causes</span>
                    {result.root_cause_analysis.causes.length > 0 ? (
                      <ul className="space-y-1">
                        {result.root_cause_analysis.causes.map((c, i) => (
                          <li key={i} className="text-slate-200 flex items-start gap-1.5">
                            <span className="text-cnc-amber font-bold">&bull;</span>
                            <span>{c}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <span className="text-slate-500">No abnormal stress factors identified.</span>
                    )}
                  </div>

                  <div>
                    <span className="font-mono text-slate-400 uppercase text-[10px] block mb-1">Affected Components</span>
                    <div className="flex flex-wrap gap-1.5">
                      {result.root_cause_analysis.components.length > 0 ? (
                        result.root_cause_analysis.components.map((comp, i) => (
                          <span
                            key={i}
                            className="px-2 py-0.5 rounded bg-ink-900 border border-ink-line text-slate-300 font-mono text-[11px]"
                          >
                            {comp}
                          </span>
                        ))
                      ) : (
                        <span className="text-slate-500">All mechanical components operating nominal.</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Recommended Actions */}
                <div>
                  <span className="font-mono text-slate-400 uppercase text-[10px] block mb-1">Corrective Maintenance Actions</span>
                  {result.root_cause_analysis.maintenance.length > 0 ? (
                    <div className="space-y-1 text-xs">
                      {result.root_cause_analysis.maintenance.map((m, i) => (
                        <div key={i} className="p-2 rounded bg-ink-900/60 border border-ink-line text-slate-200 flex items-center gap-2">
                          <CheckCircle2 className="h-3.5 w-3.5 text-cnc-blue flex-shrink-0" />
                          <span>{m}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <span className="text-slate-500 text-xs">Routine scheduled inspection is sufficient.</span>
                  )}
                </div>

                {/* Parameter Table */}
                <div>
                  <span className="font-mono text-slate-400 uppercase text-[10px] block mb-2">Parameter Baseline Comparison</span>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs font-mono">
                      <thead>
                        <tr className="border-b border-ink-line text-slate-500">
                          <th className="pb-1.5">Parameter</th>
                          <th className="pb-1.5">Current</th>
                          <th className="pb-1.5">Normal Baseline</th>
                          <th className="pb-1.5">Status</th>
                          <th className="pb-1.5">Diagnostic Effect</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-ink-line/40 text-slate-300">
                        {result.root_cause_analysis.analysis_table.map((row, i) => (
                          <tr key={i}>
                            <td className="py-2 text-white">{row.parameter}</td>
                            <td className="py-2 font-bold">{row.current}</td>
                            <td className="py-2 text-slate-400">{row.normal}</td>
                            <td className="py-2">
                              <span
                                className={`px-1.5 py-0.5 rounded text-[10px] ${
                                  row.status === 'Critical'
                                    ? 'bg-cnc-rose/20 text-cnc-rose font-bold'
                                    : row.status === 'High'
                                    ? 'bg-cnc-amber/20 text-cnc-amber'
                                    : 'bg-cnc-emerald/20 text-cnc-emerald'
                                }`}
                              >
                                {row.status}
                              </span>
                            </td>
                            <td className="py-2 text-slate-400 font-sans text-[11px]">{row.effect}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-ink-line bg-ink-800/30 p-12 text-center text-slate-500 space-y-2">
              <Sparkles className="h-8 w-8 mx-auto text-slate-600" />
              <div className="font-display font-medium text-slate-400">Awaiting Sensor Telemetry</div>
              <p className="text-xs max-w-sm mx-auto">
                Configure your sensor parameters on the left and click <strong>"Execute Failure Prediction"</strong> to view real-time diagnostics.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

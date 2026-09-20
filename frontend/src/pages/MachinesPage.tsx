import React, { useState, useEffect } from 'react';
import { MachineStatusBadge } from '../components/MachineStatusBadge';
import {
  Cpu,
  Plus,
  Search,
  Edit2,
  Trash2,
  TrendingUp,
  X,
  AlertCircle,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { getMachines, createMachine, updateMachine, deleteMachine } from '../services/api';
import type { Machine, MachineStatus } from '../types';

export const MachinesPage: React.FC = () => {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  
  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingMachine, setEditingMachine] = useState<Machine | null>(null);
  const [formData, setFormData] = useState({
    machine_code: '',
    machine_name: '',
    department: '',
    manufacturer: '',
    installation_date: '',
    status: 'Healthy' as MachineStatus,
  });
  const [formError, setFormError] = useState('');

  const fetchMachines = async () => {
    setLoading(true);
    try {
      const data = await getMachines({
        search: search || undefined,
        status: statusFilter || undefined,
      });
      setMachines(data);
    } catch (err) {
      console.error('Failed to load machines:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMachines();
  }, [search, statusFilter]);

  const openAddModal = () => {
    setEditingMachine(null);
    setFormData({
      machine_code: `CNC0${machines.length + 1}`.padStart(6, 'CNC00'),
      machine_name: '',
      department: 'Workshop A',
      manufacturer: 'Haas',
      installation_date: new Date().toISOString().split('T')[0],
      status: 'Healthy',
    });
    setFormError('');
    setIsModalOpen(true);
  };

  const openEditModal = (m: Machine) => {
    setEditingMachine(m);
    setFormData({
      machine_code: m.machine_code,
      machine_name: m.machine_name,
      department: m.department || '',
      manufacturer: m.manufacturer || '',
      installation_date: m.installation_date || '',
      status: m.status,
    });
    setFormError('');
    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.machine_code.trim() || !formData.machine_name.trim()) {
      setFormError('Machine Code and Machine Name are required.');
      return;
    }

    try {
      if (editingMachine) {
        await updateMachine(editingMachine.id, formData);
      } else {
        await createMachine(formData);
      }
      setIsModalOpen(false);
      fetchMachines();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to save machine.');
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this machine? All linked predictions will also be deleted.')) {
      try {
        await deleteMachine(id);
        fetchMachines();
      } catch (err) {
        alert('Failed to delete machine.');
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-mono uppercase tracking-wider text-cnc-blue">Fleet Registry</span>
          <h1 className="text-2xl font-display font-bold text-white tracking-tight">Machine Management</h1>
          <p className="text-sm text-slate-400 mt-0.5">Register, inspect, and maintain CNC machines on the plant floor.</p>
        </div>
        <button
          onClick={openAddModal}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-cnc-blue text-white text-sm font-medium hover:bg-blue-600 transition-colors shadow-lg shadow-cnc-blue/20"
        >
          <Plus className="h-4 w-4" />
          <span>Add New Machine</span>
        </button>
      </div>

      {/* Search & Filters */}
      <div className="rounded-xl border border-ink-line bg-ink-800/70 p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search code, name, dept..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-ink-line bg-ink-900 py-2 pl-9 pr-4 text-xs text-white placeholder-slate-500 focus:border-cnc-blue focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          {['', 'Healthy', 'Warning', 'Critical'].map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                statusFilter === s
                  ? 'bg-cnc-blue text-white'
                  : 'border border-ink-line bg-ink-900 text-slate-400 hover:text-white'
              }`}
            >
              {s || 'All Status'}
            </button>
          ))}
        </div>
      </div>

      {/* Fleet Table */}
      <div className="rounded-xl border border-ink-line bg-ink-800/80 overflow-hidden shadow-xl">
        <div className="px-6 py-4 border-b border-ink-line flex items-center justify-between bg-ink-900/40">
          <div className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-cnc-blue" />
            <h2 className="font-display font-semibold text-white">Registered Fleet Machines</h2>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {machines.length} Units Found
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-ink-line bg-ink-900/60 text-slate-400 font-mono text-xs uppercase tracking-wider">
                <th className="py-3 px-6">Machine Code</th>
                <th className="py-3 px-6">Machine Name</th>
                <th className="py-3 px-6">Department</th>
                <th className="py-3 px-6">Manufacturer</th>
                <th className="py-3 px-6">Install Date</th>
                <th className="py-3 px-6">Status</th>
                <th className="py-3 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-line/50 text-slate-300">
              {machines.map((m) => (
                <tr key={m.id} className="hover:bg-ink-750/60 transition-colors group">
                  <td className="py-3 px-6 font-mono font-bold text-cnc-blue">{m.machine_code}</td>
                  <td className="py-3 px-6 font-medium text-white">{m.machine_name}</td>
                  <td className="py-3 px-6 text-slate-400">{m.department || '--'}</td>
                  <td className="py-3 px-6 text-slate-400">{m.manufacturer || '--'}</td>
                  <td className="py-3 px-6 font-mono text-xs text-slate-400">{m.installation_date || '--'}</td>
                  <td className="py-3 px-6">
                    <MachineStatusBadge status={m.status} />
                  </td>
                  <td className="py-3 px-6 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Link
                        to="/prediction"
                        state={{ machine_id: m.id }}
                        className="p-1.5 rounded bg-ink-900 border border-ink-line text-cnc-blue hover:bg-cnc-blue hover:text-white transition-colors"
                        title="Run AI Prediction"
                      >
                        <TrendingUp className="h-3.5 w-3.5" />
                      </Link>
                      <button
                        onClick={() => openEditModal(m)}
                        className="p-1.5 rounded bg-ink-900 border border-ink-line text-slate-400 hover:text-white hover:border-slate-500 transition-colors"
                        title="Edit Machine"
                      >
                        <Edit2 className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => handleDelete(m.id)}
                        className="p-1.5 rounded bg-ink-900 border border-ink-line text-cnc-rose/70 hover:text-cnc-rose hover:border-cnc-rose/50 transition-colors"
                        title="Delete Machine"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {machines.length === 0 && !loading && (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500 font-mono text-sm">
                    No CNC machines found matching your criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Dialog */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-xl border border-ink-line bg-ink-900 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-ink-line pb-3">
              <h3 className="font-display font-semibold text-lg text-white">
                {editingMachine ? 'Edit CNC Machine' : 'Register New CNC Machine'}
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-1 rounded text-slate-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {formError && (
              <div className="p-3 rounded-lg border border-cnc-rose/30 bg-cnc-rose/10 text-cnc-rose text-xs flex items-center gap-2">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleSave} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-400 font-mono mb-1">Machine Code *</label>
                  <input
                    type="text"
                    required
                    value={formData.machine_code}
                    onChange={(e) => setFormData({ ...formData, machine_code: e.target.value })}
                    className="w-full rounded border border-ink-line bg-ink-800 p-2.5 text-white focus:border-cnc-blue focus:outline-none"
                    placeholder="e.g. CNC012"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-mono mb-1">Machine Name *</label>
                  <input
                    type="text"
                    required
                    value={formData.machine_name}
                    onChange={(e) => setFormData({ ...formData, machine_name: e.target.value })}
                    className="w-full rounded border border-ink-line bg-ink-800 p-2.5 text-white focus:border-cnc-blue focus:outline-none"
                    placeholder="e.g. 5-Axis Milling"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-400 font-mono mb-1">Department</label>
                  <input
                    type="text"
                    value={formData.department}
                    onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                    className="w-full rounded border border-ink-line bg-ink-800 p-2.5 text-white focus:border-cnc-blue focus:outline-none"
                    placeholder="e.g. Workshop A"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-mono mb-1">Manufacturer</label>
                  <input
                    type="text"
                    value={formData.manufacturer}
                    onChange={(e) => setFormData({ ...formData, manufacturer: e.target.value })}
                    className="w-full rounded border border-ink-line bg-ink-800 p-2.5 text-white focus:border-cnc-blue focus:outline-none"
                    placeholder="e.g. Haas, Mazak, DMG"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-400 font-mono mb-1">Installation Date</label>
                  <input
                    type="date"
                    value={formData.installation_date}
                    onChange={(e) => setFormData({ ...formData, installation_date: e.target.value })}
                    className="w-full rounded border border-ink-line bg-ink-800 p-2.5 text-white focus:border-cnc-blue focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-mono mb-1">Machine Status</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value as MachineStatus })}
                    className="w-full rounded border border-ink-line bg-ink-800 p-2.5 text-white focus:border-cnc-blue focus:outline-none"
                  >
                    <option value="Healthy">Healthy</option>
                    <option value="Warning">Warning</option>
                    <option value="Critical">Critical</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-ink-line">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg border border-ink-line bg-ink-800 text-slate-300 hover:bg-ink-700 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-lg bg-cnc-blue text-white text-xs font-medium hover:bg-blue-600 shadow-md shadow-cnc-blue/20"
                >
                  {editingMachine ? 'Update Machine' : 'Register Machine'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

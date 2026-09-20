import React, { useState, useEffect } from 'react';
import { Trash2, Edit2, X } from 'lucide-react';
import { getMaintenanceTickets, updateMaintenanceTicket, deleteMaintenanceTicket } from '../services/api';
import type { MaintenanceTicket, TicketStatus } from '../types';

export const MaintenancePage: React.FC = () => {
  const [tickets, setTickets] = useState<MaintenanceTicket[]>([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  
  // Edit modal
  const [editingTicket, setEditingTicket] = useState<MaintenanceTicket | null>(null);
  const [editStatus, setEditStatus] = useState<TicketStatus>('Pending');
  const [editRemarks, setEditRemarks] = useState('');

  const fetchTickets = async () => {
    setLoading(true);
    try {
      const data = await getMaintenanceTickets({
        status: statusFilter || undefined,
      });
      setTickets(data);
    } catch (err) {
      console.error('Failed to load tickets:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, [statusFilter]);

  const openEdit = (ticket: MaintenanceTicket) => {
    setEditingTicket(ticket);
    setEditStatus(ticket.status);
    setEditRemarks(ticket.remarks || '');
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingTicket) return;
    try {
      await updateMaintenanceTicket(editingTicket.id, {
        status: editStatus,
        remarks: editRemarks,
      });
      setEditingTicket(null);
      fetchTickets();
    } catch (err) {
      alert('Failed to update ticket.');
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Delete this maintenance ticket?')) {
      try {
        await deleteMaintenanceTicket(id);
        fetchTickets();
      } catch (err) {
        alert('Failed to delete ticket.');
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-mono uppercase tracking-wider text-cnc-blue">Operations</span>
          <h1 className="text-2xl font-display font-bold text-white tracking-tight">Maintenance Work Orders</h1>
          <p className="text-sm text-slate-400 mt-0.5">Track, resolve, and audit maintenance tickets raised by the AI prediction engine.</p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-ink-line pb-3">
        {['', 'Pending', 'In Progress', 'Completed'].map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              statusFilter === s
                ? 'bg-cnc-blue text-white shadow'
                : 'border border-ink-line bg-ink-900/60 text-slate-400 hover:text-white'
            }`}
          >
            {s || 'All Tickets'}
          </button>
        ))}
      </div>

      {/* Ticket Table */}
      <div className="rounded-xl border border-ink-line bg-ink-800/80 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-ink-line bg-ink-900/60 text-slate-400 font-mono uppercase tracking-wider text-[11px]">
                <th className="py-3 px-6">Ticket ID</th>
                <th className="py-3 px-6">Machine</th>
                <th className="py-3 px-6">Priority</th>
                <th className="py-3 px-6">Status</th>
                <th className="py-3 px-6">Diagnostic Remarks</th>
                <th className="py-3 px-6">Created</th>
                <th className="py-3 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-line/40 text-slate-300">
              {tickets.map((t) => (
                <tr key={t.id} className="hover:bg-ink-750/50 transition-colors">
                  <td className="py-3 px-6 font-mono font-bold text-slate-500">#{t.id}</td>
                  <td className="py-3 px-6 font-mono font-bold text-white">{t.machine_code || `Machine #${t.machine_id}`}</td>
                  <td className="py-3 px-6">
                    <span
                      className={`inline-block px-2 py-0.5 rounded font-mono text-[10px] font-bold uppercase ${
                        t.priority === 'High'
                          ? 'bg-cnc-rose/20 text-cnc-rose border border-cnc-rose/40'
                          : t.priority === 'Medium'
                          ? 'bg-cnc-amber/20 text-cnc-amber border border-cnc-amber/40'
                          : 'bg-cnc-blue/20 text-cnc-blue border border-cnc-blue/40'
                      }`}
                    >
                      {t.priority}
                    </span>
                  </td>
                  <td className="py-3 px-6 font-sans">
                    <span
                      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                        t.status === 'Completed'
                          ? 'bg-cnc-emerald/15 text-cnc-emerald border-cnc-emerald/30'
                          : t.status === 'In Progress'
                          ? 'bg-cnc-sky/15 text-cnc-sky border-cnc-sky/30'
                          : 'bg-cnc-amber/15 text-cnc-amber border-cnc-amber/30'
                      }`}
                    >
                      <span
                        className={`h-1.5 w-1.5 rounded-full ${
                          t.status === 'Completed'
                            ? 'bg-cnc-emerald'
                            : t.status === 'In Progress'
                            ? 'bg-cnc-sky'
                            : 'bg-cnc-amber animate-pulse'
                        }`}
                      />
                      {t.status}
                    </span>
                  </td>
                  <td className="py-3 px-6 text-slate-300 max-w-xs truncate">{t.remarks || '--'}</td>
                  <td className="py-3 px-6 font-mono text-slate-500 text-[11px]">
                    {new Date(t.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-6 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => openEdit(t)}
                        className="p-1.5 rounded bg-ink-900 border border-ink-line text-slate-300 hover:text-white hover:border-slate-500"
                        title="Update Ticket"
                      >
                        <Edit2 className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => handleDelete(t.id)}
                        className="p-1.5 rounded bg-ink-900 border border-ink-line text-cnc-rose/70 hover:text-cnc-rose"
                        title="Delete Ticket"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {tickets.length === 0 && !loading && (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500 font-mono">
                    No maintenance tickets found for this filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Edit Modal */}
      {editingTicket && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-xl border border-ink-line bg-ink-900 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-ink-line pb-3">
              <h3 className="font-display font-semibold text-lg text-white">
                Update Ticket #{editingTicket.id}
              </h3>
              <button onClick={() => setEditingTicket(null)} className="p-1 text-slate-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleUpdate} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 font-mono mb-1">Ticket Status</label>
                <select
                  value={editStatus}
                  onChange={(e) => setEditStatus(e.target.value as TicketStatus)}
                  className="w-full rounded border border-ink-line bg-ink-800 p-2.5 text-white font-medium focus:border-cnc-blue focus:outline-none"
                >
                  <option value="Pending">Pending</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Completed">Completed</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 font-mono mb-1">Technician Remarks</label>
                <textarea
                  rows={3}
                  value={editRemarks}
                  onChange={(e) => setEditRemarks(e.target.value)}
                  className="w-full rounded border border-ink-line bg-ink-800 p-2.5 text-white focus:border-cnc-blue focus:outline-none"
                  placeholder="Notes on tool replacement, bearing inspection, or verification prediction..."
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-ink-line">
                <button
                  type="button"
                  onClick={() => setEditingTicket(null)}
                  className="px-4 py-2 rounded bg-ink-800 text-slate-300 hover:bg-ink-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded bg-cnc-blue text-white hover:bg-blue-600"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

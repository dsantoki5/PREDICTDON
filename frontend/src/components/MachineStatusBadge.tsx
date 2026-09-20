import React from 'react';
import type { MachineStatus } from '../types';

interface Props {
  status: MachineStatus;
}

export const MachineStatusBadge: React.FC<Props> = ({ status }) => {
  const config = {
    Healthy: {
      bg: 'bg-cnc-emerald/15 text-cnc-emerald border-cnc-emerald/30',
      dot: 'bg-cnc-emerald',
    },
    Warning: {
      bg: 'bg-cnc-amber/15 text-cnc-amber border-cnc-amber/30',
      dot: 'bg-cnc-amber',
    },
    Critical: {
      bg: 'bg-cnc-rose/15 text-cnc-rose border-cnc-rose/30',
      dot: 'bg-cnc-rose',
    },
  }[status] || {
    bg: 'bg-slate-700/50 text-slate-300 border-slate-600',
    dot: 'bg-slate-400',
  };

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${config.bg}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${config.dot}`} />
      {status}
    </span>
  );
};

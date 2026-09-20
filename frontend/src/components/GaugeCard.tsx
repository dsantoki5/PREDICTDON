import React from 'react';

interface Props {
  label: string;
  value: string | number;
  sublabel?: string;
  icon: React.ReactNode;
  tone?: 'primary' | 'success' | 'warning' | 'danger' | 'info';
}

export const GaugeCard: React.FC<Props> = ({
  label,
  value,
  sublabel,
  icon,
  tone = 'primary',
}) => {
  const toneMap = {
    primary: 'from-cnc-blue to-transparent text-cnc-blue',
    success: 'from-cnc-emerald to-transparent text-cnc-emerald',
    warning: 'from-cnc-amber to-transparent text-cnc-amber',
    danger: 'from-cnc-rose to-transparent text-cnc-rose',
    info: 'from-cnc-sky to-transparent text-cnc-sky',
  };

  return (
    <div className="gauge-card group">
      <div className={`gauge-signal bg-gradient-to-r ${toneMap[tone]}`} />
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span className="font-mono uppercase tracking-wider">{label}</span>
        <div className="text-slate-400 group-hover:text-slate-200 transition-colors">
          {icon}
        </div>
      </div>
      <div className="mt-3 text-3xl font-display font-semibold tracking-tight text-white">
        {value}
      </div>
      {sublabel && (
        <div className="mt-1 text-xs font-mono uppercase tracking-wider text-slate-500">
          {sublabel}
        </div>
      )}
    </div>
  );
};

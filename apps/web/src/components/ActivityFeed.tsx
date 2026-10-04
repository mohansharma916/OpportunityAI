'use client';

import React from 'react';
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  Send,
  FileText,
  UserCheck,
  Search,
} from 'lucide-react';

interface ActivityFeedProps {
  activities: any[];
}

export function ActivityFeed({ activities }: ActivityFeedProps) {
  const getActionBadge = (action: string) => {
    if (action.includes('SUBMITTED')) {
      return { color: 'text-emerald-400 bg-emerald-950/40 border-emerald-800/40', icon: Send };
    }
    if (action.includes('PREPARED') || action.includes('RESUME')) {
      return { color: 'text-cyan-400 bg-cyan-950/40 border-cyan-800/40', icon: FileText };
    }
    if (action.includes('DISCOVERED')) {
      return { color: 'text-brand-400 bg-brand-950/40 border-brand-800/40', icon: Search };
    }
    if (action.includes('CONTACT') || action.includes('OUTREACH')) {
      return { color: 'text-purple-400 bg-purple-950/40 border-purple-800/40', icon: UserCheck };
    }
    return { color: 'text-zinc-400 bg-zinc-800/40 border-zinc-700/40', icon: Activity };
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-white/5">
        <div>
          <h2 className="text-base font-semibold text-white tracking-tight flex items-center gap-2">
            <Activity className="w-4 h-4 text-brand-400" />
            Immutable Audit Trail & Real-Time Automation Activity
          </h2>
          <p className="text-xs text-zinc-400 mt-0.5">
            Transparent cryptographic log of all external inquiries, scoring decisions, and submissions.
          </p>
        </div>
        <span className="text-[11px] font-mono text-zinc-500 bg-surface-200 px-2.5 py-1 rounded border border-white/5">
          {activities.length} Recorded Events
        </span>
      </div>

      <div className="space-y-2.5">
        {activities.map((act) => {
          const badge = getActionBadge(act.action);
          const Icon = badge.icon;
          const time = new Date(act.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
          });

          return (
            <div
              key={act.id}
              className="p-3.5 rounded-xl bg-surface-300/40 border border-white/5 hover:border-white/10 transition-colors flex items-start justify-between gap-4"
            >
              <div className="flex items-start gap-3">
                <div className={`p-2 rounded-lg border ${badge.color} shrink-0 mt-0.5`}>
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-semibold text-white font-mono">
                      {act.action}
                    </span>
                    <span className="text-[10px] text-zinc-500 font-mono">
                      Entity: {act.entity_type} ({act.entity_id?.slice(0, 8)})
                    </span>
                    <span className="text-[10px] text-zinc-400 bg-white/5 px-1.5 py-0.2 rounded font-mono">
                      {act.actor}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-300 leading-relaxed font-sans">
                    {act.reason || 'Executed background operation successfully.'}
                  </p>
                </div>
              </div>

              <div className="text-right shrink-0">
                <span className="text-[11px] font-mono text-zinc-500 flex items-center gap-1">
                  <Clock className="w-3 h-3 text-zinc-600" />
                  {time}
                </span>
                <span className="text-[10px] font-mono text-emerald-400 block mt-1">
                  {act.status}
                </span>
              </div>
            </div>
          );
        })}

        {activities.length === 0 && (
          <div className="p-12 text-center text-zinc-500 text-xs border border-dashed border-white/5 rounded-xl">
            No audit events recorded yet.
          </div>
        )}
      </div>
    </div>
  );
}

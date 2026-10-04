'use client';

import React from 'react';
import {
  Compass,
  Briefcase,
  Send,
  Users,
  Code2,
  FileText,
  Activity,
  BarChart3,
  User,
  Sliders,
  Sparkles,
  Zap,
  LogOut,
  Globe,
  Share2,
} from 'lucide-react';

interface NavigationProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  automationLevel: number;
  user?: any;
  onLogout?: () => void;
}

export function Navigation({ currentTab, onSelectTab, automationLevel, user, onLogout }: NavigationProps) {
  const primaryWorkspaces = [
    { id: 'dashboard', label: 'Command Center', icon: Compass },
    { id: 'opportunities', label: 'Opportunity Engine', icon: Briefcase },
    { id: 'applications', label: 'Applications Tracker', icon: Send },
    { id: 'linkedin', label: 'LinkedIn AI Agent', icon: Share2 },
    { id: 'profile', label: 'Knowledge Base', icon: User },
  ];

  const secondaryTools = [
    { id: 'resumes', label: 'Tailored Resumes', icon: FileText },
    { id: 'contacts', label: 'Contacts & CRM', icon: Users },
    { id: 'analytics', label: 'Performance Analytics', icon: BarChart3 },
    { id: 'activity', label: 'Audit Activity Log', icon: Activity },
  ];

  const automationLabels: Record<number, { name: string; color: string }> = {
    0: { name: 'L0: Discovery', color: 'text-zinc-400 bg-zinc-800/40 border-zinc-700/50' },
    1: { name: 'L1: Recommend', color: 'text-blue-400 bg-blue-950/40 border-blue-800/50' },
    2: { name: 'L2: Prepare', color: 'text-cyan-400 bg-cyan-950/40 border-cyan-800/50' },
    3: { name: 'L3: Approval Gate', color: 'text-indigo-400 bg-indigo-950/40 border-indigo-800/50' },
    4: { name: 'L4: High-Fit Auto', color: 'text-emerald-400 bg-emerald-950/40 border-emerald-800/50' },
    5: { name: 'L5: Autonomous', color: 'text-purple-400 bg-purple-950/40 border-purple-800/50' },
  };

  const currentLevelBadge = automationLabels[automationLevel] || automationLabels[3];

  return (
    <aside className="w-64 border-r border-white/5 bg-surface-300 flex flex-col justify-between h-screen fixed left-0 top-0 select-none z-30">
      <div className="overflow-y-auto flex-1">
        {/* Brand Header */}
        <div className="p-5 flex items-center justify-between border-b border-white/5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-500 to-cyan-400 flex items-center justify-center shadow-glow">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <div>
              <span className="font-semibold text-sm tracking-tight text-white flex items-center gap-1.5">
                OpportunityOS
              </span>
              <span className="text-[10px] text-zinc-500 uppercase tracking-widest block font-mono">
                Agentic Suite
              </span>
            </div>
          </div>
        </div>

        {/* Automation Level Badge */}
        <div className="px-4 py-2.5 border-b border-white/5 bg-surface-400/40">
          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-400 text-[10px] font-medium flex items-center gap-1">
              <Sliders className="w-3 h-3 text-zinc-400" /> Policy:
            </span>
            <span className={`px-2 py-0.5 rounded-full text-[9px] font-mono border ${currentLevelBadge.color}`}>
              {currentLevelBadge.name}
            </span>
          </div>
        </div>

        {/* Primary Workspaces Navigation Links */}
        <div className="p-3 space-y-1">
          <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-bold px-3 py-1 block">
            Workspaces
          </span>
          {primaryWorkspaces.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id || (item.id === 'opportunities' && currentTab === 'crawler');
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-brand-500/10 text-brand-300 border border-brand-500/30 shadow-sm'
                    : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-brand-400' : 'text-zinc-500'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* Secondary Tools Navigation Links */}
        <div className="p-3 pt-1 space-y-1 border-t border-white/5">
          <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-bold px-3 py-1 block">
            Tools & Insights
          </span>
          {secondaryTools.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-brand-500/10 text-brand-300 border border-brand-500/30 shadow-sm'
                    : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-brand-400' : 'text-zinc-500'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* User Footer */}
      <div className="p-4 border-t border-white/5 bg-surface-400/60 flex items-center justify-between">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-600 to-violet-700 flex items-center justify-center font-bold text-xs text-white shrink-0">
            {user?.full_name ? user.full_name.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase() : 'OP'}
          </div>
          <div className="overflow-hidden">
            <p className="text-xs font-medium text-white truncate">{user?.full_name || 'Candidate'}</p>
            <p className="text-[11px] text-zinc-500 truncate">{user?.email || 'Active Account'}</p>
          </div>
        </div>

        {onLogout && (
          <button
            onClick={onLogout}
            title="Sign Out of OpportunityOS"
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-zinc-400 hover:text-rose-400 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20 text-xs font-medium shrink-0 transition-all group"
          >
            <LogOut className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
            <span>Sign Out</span>
          </button>
        )}
      </div>
    </aside>
  );
}

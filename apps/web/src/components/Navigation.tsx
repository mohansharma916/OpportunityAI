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
} from 'lucide-react';

interface NavigationProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  automationLevel: number;
  user?: any;
  onLogout?: () => void;
}

export function Navigation({ currentTab, onSelectTab, automationLevel, user, onLogout }: NavigationProps) {
  const navItems = [
    { id: 'dashboard', label: 'Command Center', icon: Compass },
    { id: 'opportunities', label: 'Opportunities', icon: Briefcase },
    { id: 'applications', label: 'Applications', icon: Send },
    { id: 'contacts', label: 'Contacts & CRM', icon: Users },
    { id: 'contributions', label: 'Open Source', icon: Code2 },
    { id: 'resumes', label: 'Resume Engine', icon: FileText },
    { id: 'activity', label: 'Audit Activity', icon: Activity },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'profile', label: 'Knowledge Base', icon: User },
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
      <div>
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
                Agent v1.0
              </span>
            </div>
          </div>
        </div>

        {/* Automation Level Badge */}
        <div className="px-4 py-3 border-b border-white/5 bg-surface-400/40">
          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-400 text-[11px] font-medium flex items-center gap-1">
              <Sliders className="w-3 h-3 text-zinc-400" /> Policy:
            </span>
            <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono border ${currentLevelBadge.color}`}>
              {currentLevelBadge.name}
            </span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-brand-500/10 text-brand-400 border border-brand-500/20 shadow-sm'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.03]'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-brand-400' : 'text-zinc-500'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* User Footer */}
      <div className="p-4 border-t border-white/5 bg-surface-400/60 flex items-center justify-between">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-600 to-violet-700 flex items-center justify-center font-bold text-xs text-white shrink-0">
            {user?.full_name ? user.full_name.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase() : 'AM'}
          </div>
          <div className="overflow-hidden">
            <p className="text-xs font-medium text-white truncate">{user?.full_name || 'Alex Morgan'}</p>
            <p className="text-[11px] text-zinc-500 truncate">{user?.email || 'Staff Systems Architect'}</p>
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

'use client';

import React from 'react';
import {
  Globe,
  Share2,
  Send,
  Zap,
  Sliders,
  User,
  LogOut,
  KeyRound,
  ShieldCheck,
} from 'lucide-react';

interface NavigationProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  automationLevel?: number;
  user?: any;
  onLogout?: () => void;
  onOpenProfile?: () => void;
}

export function Navigation({
  currentTab,
  onSelectTab,
  automationLevel = 4,
  user,
  onLogout,
  onOpenProfile,
}: NavigationProps) {
  const threeMainFeatures = [
    {
      id: 'scraper',
      label: 'Job & Project Scraper',
      description: 'Platform list, Date tracker & Human apply',
      icon: Globe,
      number: '1',
      badgeColor: 'from-blue-500 to-cyan-400',
    },
    {
      id: 'linkedin',
      label: 'LinkedIn Scraper & Bot',
      description: 'Jobs scrape, Selenium bot & Post studio',
      icon: Share2,
      number: '2',
      badgeColor: 'from-indigo-500 to-purple-400',
    },
    {
      id: 'crm',
      label: 'Outreach & Networking CRM',
      description: 'Recruiter cadences & Auto follow-ups',
      icon: Send,
      number: '3',
      badgeColor: 'from-emerald-500 to-teal-400',
    },
  ];

  return (
    <aside className="w-72 border-r border-white/5 bg-surface-300 flex flex-col justify-between h-screen fixed left-0 top-0 select-none z-30">
      <div className="overflow-y-auto flex-1">
        {/* Brand Header */}
        <div className="p-5 border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-500 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-glow">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-sm tracking-tight text-white flex items-center gap-1.5">
                OpportunityOS
              </span>
              <span className="text-[10px] text-zinc-400 uppercase tracking-widest block font-mono">
                3 Core Pillars
              </span>
            </div>
          </div>
        </div>

        {/* Feature Navigation Title */}
        <div className="px-5 pt-5 pb-2">
          <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400 font-bold block">
            Core Features
          </span>
        </div>

        {/* Three Main Feature Navigation Links */}
        <div className="p-3 space-y-2">
          {threeMainFeatures.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full text-left p-3.5 rounded-xl transition-all border ${
                  isActive
                    ? 'bg-brand-500/15 border-brand-500/40 shadow-lg shadow-brand-500/5 text-white'
                    : 'bg-surface-400/30 border-white/5 text-zinc-300 hover:text-white hover:bg-white/[0.04]'
                }`}
              >
                <div className="flex items-center gap-3 mb-1">
                  <div
                    className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold text-white shadow-sm ${
                      isActive
                        ? `bg-gradient-to-tr ${item.badgeColor}`
                        : 'bg-surface-200 text-zinc-400'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold truncate">{item.label}</span>
                      <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-zinc-400 font-semibold">
                        #{item.number}
                      </span>
                    </div>
                  </div>
                </div>
                <p className="text-[11px] text-zinc-400 pl-10 leading-snug">
                  {item.description}
                </p>
              </button>
            );
          })}
        </div>

        {/* Credentials & Automation Status Chip */}
        <div className="mx-3 mt-4 p-3.5 rounded-xl bg-surface-400/40 border border-white/5">
          <div className="flex items-center gap-2 mb-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-[11px] font-bold text-white">Human Automation Ready</span>
          </div>
          <p className="text-[10px] text-zinc-400 leading-relaxed">
            Platform logins & credentials enabled for human-like typing delays, form filling, and connection invitations.
          </p>
        </div>
      </div>

      {/* User Footer & Quick Settings */}
      <div className="p-4 border-t border-white/5 bg-surface-400/60 space-y-2">
        <button
          onClick={onOpenProfile}
          className="w-full flex items-center justify-between p-2 rounded-lg bg-white/[0.02] hover:bg-white/[0.06] border border-white/5 transition-all text-left"
        >
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-600 to-violet-700 flex items-center justify-center font-bold text-[10px] text-white shrink-0">
              {user?.full_name ? user.full_name.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase() : 'ME'}
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-medium text-white truncate">{user?.full_name || 'Candidate'}</p>
              <p className="text-[10px] text-zinc-400 flex items-center gap-1">
                <KeyRound className="w-2.5 h-2.5" /> Identity & Vault
              </p>
            </div>
          </div>
          <span className="text-[10px] text-zinc-400 font-mono">Edit</span>
        </button>

        {onLogout && (
          <button
            onClick={onLogout}
            className="w-full flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-[11px] font-medium text-zinc-400 hover:text-rose-400 hover:bg-rose-500/10 transition-all"
          >
            <LogOut className="w-3 h-3" />
            <span>Sign Out</span>
          </button>
        )}
      </div>
    </aside>
  );
}

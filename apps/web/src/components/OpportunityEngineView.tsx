'use client';

import React, { useState } from 'react';
import {
  Globe,
  Briefcase,
  Code2,
  Sparkles,
  Plus,
  Play,
  Clock,
  Filter,
  Layers,
  CheckCircle2,
  Sliders,
  ArrowRight,
} from 'lucide-react';
import { KanbanBoard } from '@/components/KanbanBoard';
import { AutonomousCrawlerView } from '@/components/AutonomousCrawlerView';
import { ContributionsView } from '@/components/ContributionsView';

interface OpportunityEngineViewProps {
  opportunities: any[];
  onSelectOpportunity: (opp: any) => void;
  onOpenImport: () => void;
  onAutoApply?: any;
  onRefreshAllData: () => void;
  profile?: any;
}

export function OpportunityEngineView({
  opportunities,
  onSelectOpportunity,
  onOpenImport,
  onAutoApply,
  onRefreshAllData,
  profile,
}: OpportunityEngineViewProps) {
  const [subView, setSubView] = useState<'pipeline' | 'crawler' | 'opensource'>('pipeline');

  // Compute key metrics
  const totalCount = opportunities.length;
  const highFitCount = opportunities.filter(
    (o) => (o.matching_score?.overall_match_score || 0) >= 80
  ).length;
  const preparedCount = opportunities.filter((o) => o.application).length;
  const openSourceCount = opportunities.filter(
    (o) =>
      o.opportunity_type === 'OPEN_SOURCE' ||
      o.opportunity_type === 'PROJECT_CONTRIBUTION' ||
      o.opportunity_type === 'BUG_BOUNTY'
  ).length;

  return (
    <div className="space-y-6 animate-in fade-in duration-300 pb-12">
      {/* Unified Engine Hero Bar */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-surface-300 via-surface-300/90 to-surface-200 border border-white/10 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2.5 mb-2">
            <span className="px-2.5 py-0.5 rounded-full bg-brand-500/20 text-brand-300 text-[10px] font-mono font-bold border border-brand-500/30 flex items-center gap-1">
              <Sparkles className="w-3 h-3" />
              Unified Opportunity Engine
            </span>
            <span className="px-2 py-0.5 rounded-full bg-emerald-950/60 text-emerald-400 text-[10px] font-mono border border-emerald-800/40">
              Multi-Platform Discovery Active
            </span>
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight">
            Autonomous Discovery & Opportunity Pipeline
          </h1>
          <p className="text-xs text-zinc-400 mt-1 max-w-2xl leading-relaxed">
            Continuously crawls global boards, tech feeds, remote portals, and GitHub repositories.
            Automatically scores semantic fit against your salary floor and verified skills.
          </p>
        </div>

        {/* Engine KPI Chips */}
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl bg-surface-400/80 border border-white/5 text-center min-w-[90px]">
            <span className="text-[10px] font-mono text-zinc-400 uppercase font-bold block">Discovered</span>
            <span className="text-xl font-black text-white">{totalCount}</span>
          </div>
          <div className="p-3 rounded-xl bg-surface-400/80 border border-brand-500/20 text-center min-w-[90px]">
            <span className="text-[10px] font-mono text-brand-400 uppercase font-bold block">High Fit (≥80%)</span>
            <span className="text-xl font-black text-brand-300">{highFitCount}</span>
          </div>
          <div className="p-3 rounded-xl bg-surface-400/80 border border-emerald-500/20 text-center min-w-[90px]">
            <span className="text-[10px] font-mono text-emerald-400 uppercase font-bold block">Prepared</span>
            <span className="text-xl font-black text-emerald-300">{preparedCount}</span>
          </div>
        </div>
      </div>

      {/* Control Navigation & Mode Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/5 pb-3">
        {/* View Switcher Pills */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-surface-300 border border-white/10">
          <button
            onClick={() => setSubView('pipeline')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
              subView === 'pipeline'
                ? 'bg-brand-600 text-white shadow-glow'
                : 'text-zinc-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Briefcase className="w-3.5 h-3.5" />
            <span>Pipeline Matrix</span>
            <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded ${subView === 'pipeline' ? 'bg-white/20' : 'bg-white/5'}`}>
              {totalCount}
            </span>
          </button>

          <button
            onClick={() => setSubView('crawler')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
              subView === 'crawler'
                ? 'bg-brand-600 text-white shadow-glow'
                : 'text-zinc-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            <span>Autonomous Web Crawler</span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
          </button>

          <button
            onClick={() => setSubView('opensource')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
              subView === 'opensource'
                ? 'bg-brand-600 text-white shadow-glow'
                : 'text-zinc-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Code2 className="w-3.5 h-3.5" />
            <span>Open Source & Contracts</span>
            <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded ${subView === 'opensource' ? 'bg-white/20' : 'bg-white/5'}`}>
              {openSourceCount}
            </span>
          </button>
        </div>

        {/* Global Engine Actions */}
        <div className="flex items-center gap-2">
          {subView === 'pipeline' && (
            <button
              onClick={() => setSubView('crawler')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-500/10 hover:bg-brand-500/20 text-xs font-semibold text-brand-300 border border-brand-500/30 transition-all shadow-sm"
            >
              <Globe className="w-3.5 h-3.5 text-brand-400" />
              <span>Launch Live Crawl</span>
            </button>
          )}

          <button
            onClick={onOpenImport}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-300 hover:bg-surface-200 text-xs font-semibold text-zinc-300 hover:text-white border border-white/10 transition-all shadow-sm"
          >
            <Plus className="w-3.5 h-3.5 text-brand-400" />
            <span>Import Job URL / Text</span>
          </button>
        </div>
      </div>

      {/* SUBVIEW RENDERING */}
      {subView === 'pipeline' && (
        <div className="space-y-4">
          <KanbanBoard
            opportunities={opportunities}
            onSelectOpportunity={onSelectOpportunity}
            onOpenImport={onOpenImport}
            onAutoApply={typeof onAutoApply === 'function' ? () => onAutoApply('') : undefined}
          />
        </div>
      )}

      {subView === 'crawler' && (
        <AutonomousCrawlerView
          onRefreshAllData={onRefreshAllData}
          profile={profile}
        />
      )}

      {subView === 'opensource' && (
        <ContributionsView
          opportunities={opportunities}
          onSelectOpportunity={onSelectOpportunity}
        />
      )}
    </div>
  );
}

'use client';

import React from 'react';
import {
  Sparkles,
  Compass,
  CheckCircle,
  FileCheck,
  Send,
  AlertCircle,
  ArrowUpRight,
  RefreshCw,
} from 'lucide-react';

interface DailyBriefingCardProps {
  briefing: any;
  onRefreshDiscovery: () => void;
  onSelectOpportunity: (id: string) => void;
  loadingDiscovery?: boolean;
}

export function DailyBriefingCard({
  briefing,
  onRefreshDiscovery,
  onSelectOpportunity,
  loadingDiscovery,
}: DailyBriefingCardProps) {
  if (!briefing) return null;

  return (
    <div className="bg-gradient-to-b from-surface-100 to-surface-200 border border-white/10 rounded-xl p-6 glass-panel relative overflow-hidden mb-6 shadow-glow">
      <div className="absolute top-0 right-0 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-brand-500/10 border border-brand-500/20 text-brand-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-semibold text-white tracking-tight">
                Daily AI Briefing
              </h2>
              <span className="text-[11px] font-mono text-zinc-400 bg-white/5 px-2 py-0.5 rounded border border-white/5">
                {briefing.date}
              </span>
            </div>
            <p className="text-xs text-zinc-400 mt-0.5">
              Personal Opportunity Acquisition & Intelligence Summary
            </p>
          </div>
        </div>

        <button
          onClick={onRefreshDiscovery}
          disabled={loadingDiscovery}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-medium text-zinc-200 border border-white/10 hover:border-white/20 transition-all self-start md:self-center"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-brand-400 ${loadingDiscovery ? 'animate-spin' : ''}`} />
          <span>{loadingDiscovery ? 'Scanning Global Sources...' : 'Run Discovery Cycle'}</span>
        </button>
      </div>

      {/* Executive Summary Text */}
      <div className="my-5 bg-surface-300/60 border border-white/5 rounded-lg p-4">
        <p className="text-xs leading-relaxed text-zinc-300 font-sans whitespace-pre-line">
          {briefing.summary_text}
        </p>
      </div>

      {/* Metric Counters */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-2">
        <div className="p-3 rounded-lg bg-white/[0.02] border border-white/5">
          <div className="flex items-center justify-between text-zinc-400 mb-1">
            <span className="text-[11px] font-medium">Discovered</span>
            <Compass className="w-3.5 h-3.5 text-zinc-400" />
          </div>
          <span className="text-xl font-bold font-mono text-white">
            {briefing.opportunities_discovered_count}
          </span>
        </div>

        <div className="p-3 rounded-lg bg-brand-500/[0.04] border border-brand-500/20">
          <div className="flex items-center justify-between text-brand-400 mb-1">
            <span className="text-[11px] font-medium">Strong Match</span>
            <CheckCircle className="w-3.5 h-3.5" />
          </div>
          <span className="text-xl font-bold font-mono text-brand-300">
            {briefing.strong_matches_count}
          </span>
        </div>

        <div className="p-3 rounded-lg bg-cyan-500/[0.04] border border-cyan-500/20">
          <div className="flex items-center justify-between text-cyan-400 mb-1">
            <span className="text-[11px] font-medium">Prepared</span>
            <FileCheck className="w-3.5 h-3.5" />
          </div>
          <span className="text-xl font-bold font-mono text-cyan-300">
            {briefing.applications_prepared_count}
          </span>
        </div>

        <div className="p-3 rounded-lg bg-emerald-500/[0.04] border border-emerald-500/20">
          <div className="flex items-center justify-between text-emerald-400 mb-1">
            <span className="text-[11px] font-medium">Submitted</span>
            <Send className="w-3.5 h-3.5" />
          </div>
          <span className="text-xl font-bold font-mono text-emerald-300">
            {briefing.applications_submitted_count}
          </span>
        </div>

        <div className="p-3 rounded-lg bg-amber-500/[0.04] border border-amber-500/20">
          <div className="flex items-center justify-between text-amber-400 mb-1">
            <span className="text-[11px] font-medium">Needs Attention</span>
            <AlertCircle className="w-3.5 h-3.5" />
          </div>
          <span className="text-xl font-bold font-mono text-amber-300">
            {briefing.needs_attention_count}
          </span>
        </div>

        <div className="p-3 rounded-lg bg-purple-500/[0.04] border border-purple-500/20">
          <div className="flex items-center justify-between text-purple-400 mb-1">
            <span className="text-[11px] font-medium">Interviews</span>
            <Sparkles className="w-3.5 h-3.5" />
          </div>
          <span className="text-xl font-bold font-mono text-purple-300">
            {briefing.interviews_detected_count}
          </span>
        </div>
      </div>

      {/* Top High-Yield Opportunities */}
      {briefing.top_recommended_opportunities && briefing.top_recommended_opportunities.length > 0 && (
        <div className="mt-5 pt-4 border-t border-white/5">
          <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2.5 font-mono">
            High-Yield Target Recommendations
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {briefing.top_recommended_opportunities.map((item: any, idx: number) => (
              <div
                key={idx}
                onClick={() => onSelectOpportunity(item.id)}
                className="p-3 rounded-lg bg-surface-300/80 border border-white/5 hover:border-brand-500/40 hover:bg-surface-300 cursor-pointer transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold text-white truncate max-w-[70%]">
                      {item.company}
                    </span>
                    <span className="text-[11px] font-mono font-bold text-emerald-400 bg-emerald-950/40 px-1.5 py-0.5 rounded border border-emerald-800/40">
                      {item.score}% Match
                    </span>
                  </div>
                  <p className="text-[11px] text-zinc-400 line-clamp-1 mb-2">
                    {item.title}
                  </p>
                  <p className="text-[10px] text-zinc-500 line-clamp-2 italic">
                    "{item.rationale}"
                  </p>
                </div>
                <div className="flex items-center justify-end mt-2 pt-2 border-t border-white/5 text-[11px] text-brand-400">
                  <span className="flex items-center gap-1 font-medium">
                    Review <ArrowUpRight className="w-3 h-3" />
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

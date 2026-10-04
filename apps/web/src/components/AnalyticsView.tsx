'use client';

import React from 'react';
import { BarChart3, TrendingUp, Compass, Send, CheckCircle2, Award, Users } from 'lucide-react';

interface AnalyticsViewProps {
  analytics: any;
}

export function AnalyticsView({ analytics }: AnalyticsViewProps) {
  if (!analytics) return null;

  const funnel = analytics.funnel || [];
  const maxFunnelCount = Math.max(...funnel.map((f: any) => f.count), 1);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="pb-3 border-b border-white/5">
        <h2 className="text-base font-semibold text-white tracking-tight flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-brand-400" />
          Acquisition Performance & Conversion Funnel
        </h2>
        <p className="text-xs text-zinc-400 mt-0.5">
          End-to-end telemetry tracking discovery, qualification, submission, and interview yield.
        </p>
      </div>

      {/* Top Level Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-surface-300/60 border border-white/5">
          <span className="text-[11px] font-medium text-zinc-400 block mb-1">
            Global Opportunities Ingested
          </span>
          <span className="text-2xl font-bold font-mono text-white">
            {analytics.total_discovered}
          </span>
          <span className="text-[10px] text-zinc-500 block mt-1">Across 3 external connectors</span>
        </div>

        <div className="p-4 rounded-xl bg-surface-300/60 border border-white/5">
          <span className="text-[11px] font-medium text-zinc-400 block mb-1">
            Average Candidate Fit Score
          </span>
          <span className="text-2xl font-bold font-mono text-brand-300">
            {analytics.average_match_score}%
          </span>
          <span className="text-[10px] text-emerald-400 block mt-1">Transferable skills included</span>
        </div>

        <div className="p-4 rounded-xl bg-surface-300/60 border border-white/5">
          <span className="text-[11px] font-medium text-zinc-400 block mb-1">
            Applications Submitted
          </span>
          <span className="text-2xl font-bold font-mono text-emerald-300">
            {analytics.applications_submitted}
          </span>
          <span className="text-[10px] text-zinc-500 block mt-1">Verified & user approved</span>
        </div>

        <div className="p-4 rounded-xl bg-surface-300/60 border border-white/5">
          <span className="text-[11px] font-medium text-zinc-400 block mb-1">
            Response / Interview Conversion
          </span>
          <span className="text-2xl font-bold font-mono text-purple-300">
            {analytics.conversion_rate}%
          </span>
          <span className="text-[10px] text-purple-400 block mt-1">High signal personalized outreach</span>
        </div>
      </div>

      {/* Pipeline Funnel Visualizer */}
      <div className="p-6 rounded-xl bg-surface-300/40 border border-white/5 space-y-4">
        <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider font-mono">
          Stage-by-Stage Opportunity Pipeline Funnel
        </h3>

        <div className="space-y-3">
          {funnel.map((item: any, idx: number) => {
            const widthPct = Math.max(8, (item.count / maxFunnelCount) * 100);
            return (
              <div key={idx} className="space-y-1">
                <div className="flex items-center justify-between text-xs font-medium">
                  <span className="text-zinc-300 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
                    {item.stage}
                  </span>
                  <span className="font-mono text-white">{item.count} items</span>
                </div>
                <div className="w-full bg-white/5 h-2.5 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${widthPct}%`,
                      backgroundColor: item.color,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Sources Performance */}
      <div className="p-6 rounded-xl bg-surface-300/40 border border-white/5 space-y-4">
        <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider font-mono">
          Opportunity Source Distribution
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {(analytics.sources || []).map((s: any, idx: number) => (
            <div key={idx} className="p-3.5 rounded-lg bg-surface-200 border border-white/5">
              <span className="text-[11px] font-mono text-brand-400 block mb-1">{s.source}</span>
              <span className="text-xl font-bold font-mono text-white">{s.count}</span>
              <span className="text-[10px] text-zinc-500 block mt-0.5">Active listings parsed</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

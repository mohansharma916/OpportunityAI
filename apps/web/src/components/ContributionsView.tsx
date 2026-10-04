'use client';

import React from 'react';
import { Code2, GitPullRequest, DollarSign, ExternalLink, Sparkles, CheckCircle2 } from 'lucide-react';

interface ContributionsViewProps {
  opportunities: any[];
  onSelectOpportunity: (opp: any) => void;
}

export function ContributionsView({
  opportunities,
  onSelectOpportunity,
}: ContributionsViewProps) {
  const osOpps = opportunities.filter((o) =>
    o.employment_type?.includes('OPEN_SOURCE') || o.source?.includes('GITHUB')
  );

  return (
    <div className="space-y-6">
      <div className="pb-3 border-b border-white/5">
        <h2 className="text-base font-semibold text-white tracking-tight flex items-center gap-2">
          <Code2 className="w-4 h-4 text-emerald-400" />
          Open Source Contributions & Paid Engineering Bounties
        </h2>
        <p className="text-xs text-zinc-400 mt-0.5">
          High-impact GitHub issues, Algora bounties, and maintainer requests matched to your core stack.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {osOpps.map((opp) => {
          const score = opp.matching_score?.overall_match_score || 85;
          const isPaid = opp.hourly_rate && opp.hourly_rate > 0;

          return (
            <div
              key={opp.id}
              onClick={() => onSelectOpportunity(opp)}
              className="glass-card p-5 rounded-xl cursor-pointer space-y-3"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-mono text-purple-400 bg-purple-950/40 px-2 py-0.5 rounded border border-purple-800/40">
                      {opp.company_name}
                    </span>
                    {isPaid && (
                      <span className="text-[10px] font-mono font-bold text-emerald-300 bg-emerald-950/50 px-2 py-0.5 rounded border border-emerald-500/40">
                        Bounty: ${opp.hourly_rate}
                      </span>
                    )}
                  </div>
                  <h3 className="text-sm font-bold text-white hover:text-brand-300 transition-colors">
                    {opp.title}
                  </h3>
                </div>

                <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40 shrink-0">
                  {score.toFixed(0)}% Fit
                </span>
              </div>

              <p className="text-xs text-zinc-300 line-clamp-3 leading-relaxed font-sans">
                {opp.description}
              </p>

              <div className="flex flex-wrap gap-1">
                {(opp.required_skills || []).map((sk: string, idx: number) => (
                  <span
                    key={idx}
                    className="text-[10px] font-mono bg-white/5 text-zinc-300 px-2 py-0.5 rounded border border-white/5"
                  >
                    {sk}
                  </span>
                ))}
              </div>

              <div className="pt-3 border-t border-white/5 flex items-center justify-between text-xs text-zinc-400">
                <span className="flex items-center gap-1 font-mono text-[11px]">
                  <GitPullRequest className="w-3.5 h-3.5 text-zinc-500" />
                  Grounded Workflow Ready
                </span>
                <span className="text-brand-400 flex items-center gap-1 font-medium text-[11px]">
                  View Plan <ExternalLink className="w-3 h-3" />
                </span>
              </div>
            </div>
          );
        })}

        {osOpps.length === 0 && (
          <div className="col-span-full p-12 text-center text-zinc-500 text-xs border border-dashed border-white/5 rounded-xl">
            No open-source items currently in view. Run a discovery cycle to scan GitHub.
          </div>
        )}
      </div>
    </div>
  );
}

'use client';

import React, { useState } from 'react';
import {
  Briefcase,
  ExternalLink,
  ChevronRight,
  Filter,
  Search,
  Sparkles,
  Building,
  DollarSign,
  MapPin,
  CheckCircle2,
  Clock,
  ArrowRight,
} from 'lucide-react';

interface KanbanBoardProps {
  opportunities: any[];
  onSelectOpportunity: (opportunity: any) => void;
  onOpenImport: () => void;
  onAutoApply?: () => void;
}

export function KanbanBoard({
  opportunities,
  onSelectOpportunity,
  onOpenImport,
  onAutoApply,
}: KanbanBoardProps) {
  const [filterType, setFilterType] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Primary Kanban stages
  const columns = [
    { id: 'DISCOVERED', title: 'Discovered', color: 'border-zinc-700' },
    { id: 'AI_REVIEWING', title: 'AI Reviewing', color: 'border-blue-500/50' },
    { id: 'STRONG_MATCH', title: 'Strong Match', color: 'border-brand-500' },
    { id: 'PREPARED', title: 'Prepared', color: 'border-cyan-500' },
    { id: 'NEEDS_APPROVAL', title: 'Needs Approval', color: 'border-amber-500' },
    { id: 'NEEDS_ATTENTION', title: 'Needs Attention', color: 'border-rose-500' },
    { id: 'APPLIED', title: 'Applied', color: 'border-emerald-500' },
    { id: 'INTERVIEW', title: 'Interviewing', color: 'border-purple-500' },
  ];

  // Filter opportunities
  const filteredOpps = opportunities.filter((opp) => {
    if (filterType === 'HIGH_FIT') {
      const score = opp.matching_score?.overall_match_score || 0;
      if (score < 80) return false;
    } else if (filterType === 'CONTRACT') {
      if (opp.employment_type !== 'CONTRACT' && !opp.hourly_rate) return false;
    } else if (filterType === 'OPEN_SOURCE') {
      if (!opp.employment_type?.includes('OPEN_SOURCE')) return false;
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = opp.title?.toLowerCase().includes(q);
      const matchComp = opp.company_name?.toLowerCase().includes(q);
      const matchSkills = (opp.required_skills || []).some((s: string) => s.toLowerCase().includes(q));
      if (!matchTitle && !matchComp && !matchSkills) return false;
    }

    return true;
  });

  return (
    <div className="flex flex-col h-full">
      {/* Control / Filter Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 mb-5">
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search roles, companies, tech..."
              className="bg-surface-200 border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-500/50 w-64"
            />
          </div>

          <div className="flex items-center bg-surface-200 border border-white/5 rounded-lg p-0.5 text-xs">
            {['ALL', 'HIGH_FIT', 'CONTRACT', 'OPEN_SOURCE'].map((type) => (
              <button
                key={type}
                onClick={() => setFilterType(type)}
                className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all ${
                  filterType === type
                    ? 'bg-brand-500 text-white shadow-sm'
                    : 'text-zinc-400 hover:text-zinc-200'
                }`}
              >
                {type === 'ALL'
                  ? 'All'
                  : type === 'HIGH_FIT'
                  ? 'High Match (≥80%)'
                  : type === 'CONTRACT'
                  ? 'Contracts'
                  : 'Open Source'}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {onAutoApply && (
            <button
              onClick={onAutoApply}
              className="flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 text-xs font-medium transition-all"
              title="Runs autonomous application engine for eligible high-fit listings (Level 4/5)"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Auto-Apply (L4/L5)</span>
            </button>
          )}

          <button
            onClick={onOpenImport}
            className="flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-xs font-medium text-white shadow-glow transition-all"
          >
            <span>+ Import Opportunity</span>
          </button>
        </div>
      </div>

      {/* Horizontal Scrollable Kanban Columns */}
      <div className="flex gap-4 overflow-x-auto pb-6 flex-1 min-h-[600px]">
        {columns.map((col) => {
          const colOpps = filteredOpps.filter((opp) => {
            if (col.id === 'DISCOVERED') {
              return opp.status === 'DISCOVERED' || !opp.status;
            }
            if (col.id === 'INTERVIEW') {
              return opp.status === 'INTERVIEW' || opp.status === 'OFFER';
            }
            return opp.status === col.id;
          });

          return (
            <div
              key={col.id}
              className="w-80 shrink-0 bg-surface-300/40 border border-white/5 rounded-xl flex flex-col max-h-[calc(100vh-280px)] overflow-hidden"
            >
              {/* Column Header */}
              <div
                className={`p-3 border-b border-white/5 flex items-center justify-between border-t-2 ${col.color} bg-surface-200/50`}
              >
                <span className="text-xs font-semibold text-white tracking-tight flex items-center gap-2">
                  {col.title}
                </span>
                <span className="text-[11px] font-mono text-zinc-400 bg-white/5 px-2 py-0.5 rounded">
                  {colOpps.length}
                </span>
              </div>

              {/* Cards list */}
              <div className="p-2 space-y-2.5 overflow-y-auto flex-1">
                {colOpps.map((opp) => {
                  const score = opp.matching_score?.overall_match_score || 0;
                  const isHighFit = score >= 85;

                  return (
                    <div
                      key={opp.id}
                      onClick={() => onSelectOpportunity(opp)}
                      className="glass-card p-3 rounded-lg cursor-pointer group"
                    >
                      {/* Company & Score */}
                      <div className="flex items-start justify-between gap-2 mb-1.5">
                        <div className="flex items-center gap-1.5 overflow-hidden">
                          <Building className="w-3.5 h-3.5 text-zinc-500 shrink-0" />
                          <span className="text-xs font-semibold text-white truncate">
                            {opp.company_name}
                          </span>
                        </div>
                        {score > 0 && (
                          <span
                            className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border shrink-0 ${
                              isHighFit
                                ? 'text-emerald-400 bg-emerald-950/40 border-emerald-800/40'
                                : score >= 70
                                ? 'text-brand-300 bg-brand-950/40 border-brand-800/40'
                                : 'text-zinc-400 bg-zinc-800/40 border-zinc-700/40'
                            }`}
                          >
                            {score.toFixed(0)}%
                          </span>
                        )}
                      </div>

                      {/* Title */}
                      <p className="text-xs text-zinc-300 font-medium line-clamp-2 mb-2 group-hover:text-brand-300 transition-colors">
                        {opp.title}
                      </p>

                      {/* Metadata Pills */}
                      <div className="flex flex-wrap items-center gap-1 mb-2.5 text-[10px] text-zinc-400">
                        {opp.hourly_rate ? (
                          <span className="bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-500/20 font-mono">
                            ${opp.hourly_rate}/hr
                          </span>
                        ) : opp.salary_min ? (
                          <span className="bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-500/20 font-mono">
                            ${(opp.salary_min / 1000).toFixed(0)}k - ${(opp.salary_max / 1000).toFixed(0)}k
                          </span>
                        ) : null}

                        <span className="bg-white/5 px-1.5 py-0.5 rounded border border-white/5 truncate max-w-[120px]">
                          {opp.location || 'Remote'}
                        </span>

                        <span className="bg-white/5 px-1.5 py-0.5 rounded border border-white/5 font-mono text-zinc-500">
                          {opp.source}
                        </span>
                      </div>

                      {/* Skills Chips */}
                      {opp.required_skills && opp.required_skills.length > 0 && (
                        <div className="flex flex-wrap gap-1 mb-2">
                          {opp.required_skills.slice(0, 3).map((s: string, idx: number) => (
                            <span
                              key={idx}
                              className="text-[9px] bg-brand-500/10 text-brand-300 px-1.5 py-0.5 rounded border border-brand-500/20 font-mono"
                            >
                              {s}
                            </span>
                          ))}
                          {opp.required_skills.length > 3 && (
                            <span className="text-[9px] text-zinc-500 self-center">
                              +{opp.required_skills.length - 3}
                            </span>
                          )}
                        </div>
                      )}

                      {/* Footer Actions */}
                      <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[11px] text-zinc-500">
                        <span>Click for details</span>
                        <ArrowRight className="w-3 h-3 text-zinc-500 group-hover:text-brand-400 group-hover:translate-x-0.5 transition-all" />
                      </div>
                    </div>
                  );
                })}

                {colOpps.length === 0 && (
                  <div className="h-32 flex items-center justify-center border border-dashed border-white/5 rounded-lg text-zinc-600 text-[11px]">
                    No opportunities
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

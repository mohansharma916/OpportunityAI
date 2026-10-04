'use client';

import React, { useState } from 'react';
import {
  X,
  ExternalLink,
  Building,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Sparkles,
  DollarSign,
  MapPin,
  Clock,
  Send,
  FileCheck,
  UserCheck,
  ShieldCheck,
  ChevronRight,
  RefreshCw,
} from 'lucide-react';
import { fetchApi } from '@/lib/api';

interface OpportunityDetailModalProps {
  opportunity: any;
  onClose: () => void;
  onRefresh: () => void;
  onOpenReview: (app: any) => void;
}

export function OpportunityDetailModal({
  opportunity,
  onClose,
  onRefresh,
  onOpenReview,
}: OpportunityDetailModalProps) {
  const [activeTab, setActiveTab] = useState<'match' | 'description' | 'contacts'>('match');
  const [preparing, setPreparing] = useState(false);
  const [coverStyle, setCoverStyle] = useState('TECHNICAL');

  if (!opportunity) return null;

  const score = opportunity.matching_score;
  const overall = score?.overall_match_score || 0;
  const isHighFit = overall >= 85;

  const handlePrepareApplication = async () => {
    setPreparing(true);
    try {
      const app = await fetchApi<any>(`/api/opportunities/${opportunity.id}/prepare`, {
        method: 'POST',
        body: JSON.stringify({ style: coverStyle }),
      });
      onRefresh();
      onOpenReview(app);
    } catch (err: any) {
      alert(`Preparation error: ${err.message}`);
    } finally {
      setPreparing(false);
    }
  };

  const handleUpdateStatus = async (newStatus: string) => {
    try {
      await fetchApi(`/api/opportunities/${opportunity.id}/status`, {
        method: 'PUT',
        body: JSON.stringify({ status: newStatus, reason: `User moved to ${newStatus}` }),
      });
      onRefresh();
      onClose();
    } catch (err: any) {
      alert(`Status update failed: ${err.message}`);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="w-full max-w-4xl max-h-[90vh] bg-surface-200 border border-white/10 rounded-2xl shadow-2xl flex flex-col overflow-hidden glass-panel animate-in fade-in zoom-in-95 duration-150">
        {/* Top Header */}
        <div className="p-6 border-b border-white/5 flex items-start justify-between gap-4 bg-surface-300/40">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-xs font-mono font-semibold text-brand-400 bg-brand-500/10 px-2 py-0.5 rounded border border-brand-500/20">
                {opportunity.source}
              </span>
              <span className="text-xs text-zinc-500 font-mono">
                ID: {opportunity.external_id || opportunity.id?.slice(0, 8)}
              </span>
              <span className="text-xs font-medium text-zinc-400 bg-white/5 px-2 py-0.5 rounded">
                Status: {opportunity.status}
              </span>
            </div>
            <h1 className="text-lg font-bold text-white tracking-tight">
              {opportunity.title}
            </h1>
            <div className="flex items-center gap-3 text-xs text-zinc-400 mt-1">
              <span className="flex items-center gap-1 text-zinc-300 font-medium">
                <Building className="w-3.5 h-3.5 text-zinc-500" />
                {opportunity.company_name}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-zinc-500" />
                {opportunity.location || 'Remote'}
              </span>
              {opportunity.hourly_rate ? (
                <>
                  <span>•</span>
                  <span className="text-emerald-400 font-mono font-medium">
                    ${opportunity.hourly_rate}/hr
                  </span>
                </>
              ) : opportunity.salary_min ? (
                <>
                  <span>•</span>
                  <span className="text-emerald-400 font-mono font-medium">
                    ${(opportunity.salary_min / 1000).toFixed(0)}k - ${(opportunity.salary_max / 1000).toFixed(0)}k
                  </span>
                </>
              ) : null}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <a
              href={opportunity.url}
              target="_blank"
              rel="noreferrer"
              className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-zinc-400 hover:text-white transition-colors"
              title="Open Original Listing"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
            <button
              onClick={onClose}
              className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-zinc-400 hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-white/5 bg-surface-400/40 px-6">
          <button
            onClick={() => setActiveTab('match')}
            className={`py-3 px-4 text-xs font-medium border-b-2 transition-all ${
              activeTab === 'match'
                ? 'border-brand-500 text-brand-400'
                : 'border-transparent text-zinc-400 hover:text-zinc-200'
            }`}
          >
            Match Evaluation & Rationale
          </button>
          <button
            onClick={() => setActiveTab('description')}
            className={`py-3 px-4 text-xs font-medium border-b-2 transition-all ${
              activeTab === 'description'
                ? 'border-brand-500 text-brand-400'
                : 'border-transparent text-zinc-400 hover:text-zinc-200'
            }`}
          >
            Role Requirements & Details
          </button>
          <button
            onClick={() => setActiveTab('contacts')}
            className={`py-3 px-4 text-xs font-medium border-b-2 transition-all ${
              activeTab === 'contacts'
                ? 'border-brand-500 text-brand-400'
                : 'border-transparent text-zinc-400 hover:text-zinc-200'
            }`}
          >
            Hiring Contacts & Outreach
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {activeTab === 'match' && (
            <div className="space-y-6">
              {/* Overall Score Banner */}
              <div className="p-4 rounded-xl bg-gradient-to-r from-brand-950/40 via-surface-100 to-surface-100 border border-brand-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div
                    className={`w-16 h-16 rounded-xl flex flex-col items-center justify-center font-mono font-bold border ${
                      isHighFit
                        ? 'bg-emerald-950/50 border-emerald-500/40 text-emerald-300'
                        : 'bg-brand-950/50 border-brand-500/40 text-brand-300'
                    }`}
                  >
                    <span className="text-xl">{overall.toFixed(0)}</span>
                    <span className="text-[10px] text-zinc-400 uppercase tracking-wider">Score</span>
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-white">
                      {isHighFit ? 'Exceptional Candidate Fit' : 'Qualified Match with Transferable Strengths'}
                    </h3>
                    <p className="text-xs text-zinc-400 mt-0.5">
                      Confidence: {score?.confidence_score}% • Evaluated by Multi-Dimensional Matching Engine
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <select
                    value={coverStyle}
                    onChange={(e) => setCoverStyle(e.target.value)}
                    className="bg-surface-300 border border-white/10 rounded-lg text-xs text-zinc-300 px-2 py-1.5 focus:outline-none"
                  >
                    <option value="TECHNICAL">Technical Cover Letter</option>
                    <option value="STARTUP">Startup High-Velocity Style</option>
                    <option value="CONSULTING">Consulting Engagement Style</option>
                  </select>
                  <button
                    onClick={handlePrepareApplication}
                    disabled={preparing}
                    className="px-4 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-xs font-semibold text-white shadow-glow transition-all flex items-center gap-1.5 shrink-0"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>{preparing ? 'Tailoring Package...' : 'Prepare Application'}</span>
                  </button>
                </div>
              </div>

              {/* Natural Language Rationale */}
              <div className="p-4 rounded-lg bg-surface-300/40 border border-white/5">
                <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5 font-mono">
                  Evaluation Rationale & Fit Analysis
                </h4>
                <p className="text-xs leading-relaxed text-zinc-200">
                  {score?.match_rationale || 'Calculating detailed rationale...'}
                </p>
              </div>

              {/* Dimensional Breakdown Grid */}
              <div>
                <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3 font-mono">
                  Dimensional Evaluation Matrix
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {[
                    { label: 'Technical Skills', val: score?.technical_match },
                    { label: 'Experience Depth', val: score?.experience_match },
                    { label: 'Remote Alignment', val: score?.remote_match },
                    { label: 'Timezone Overlap', val: score?.timezone_match },
                    { label: 'Compensation Floor', val: score?.compensation_match },
                    { label: 'Role Alignment', val: score?.role_match },
                  ].map((dim, idx) => (
                    <div key={idx} className="p-3 rounded-lg bg-surface-300/60 border border-white/5">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-zinc-400">{dim.label}</span>
                        <span className="font-mono font-bold text-white">{dim.val ?? 80}%</span>
                      </div>
                      <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
                        <div
                          className="bg-brand-400 h-full rounded-full"
                          style={{ width: `${dim.val ?? 80}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Transferable Skills & Gaps */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Transferable map */}
                <div className="p-4 rounded-lg bg-surface-300/40 border border-white/5">
                  <h4 className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5 mb-2 font-mono">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Transferable Experience Recognized
                  </h4>
                  {score?.transferable_skills && Object.keys(score.transferable_skills).length > 0 ? (
                    <div className="space-y-1.5">
                      {Object.entries(score.transferable_skills).map(([req, cand]: any, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between text-xs p-1.5 rounded bg-white/[0.02]"
                        >
                          <span className="text-zinc-300 font-mono">{req}</span>
                          <span className="text-zinc-500 text-[10px]">transfers from</span>
                          <span className="text-brand-300 font-mono font-medium">{cand}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-zinc-500">
                      Direct matches identified across all primary requirements.
                    </p>
                  )}
                </div>

                {/* Primary gaps */}
                <div className="p-4 rounded-lg bg-surface-300/40 border border-white/5">
                  <h4 className="text-xs font-semibold text-amber-400 flex items-center gap-1.5 mb-2 font-mono">
                    <AlertTriangle className="w-3.5 h-3.5" /> Identified Skill Deltas
                  </h4>
                  {score?.primary_gaps && score.primary_gaps.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {score.primary_gaps.map((gap: string, idx: number) => (
                        <span
                          key={idx}
                          className="text-[11px] font-mono text-amber-300 bg-amber-950/30 px-2 py-0.5 rounded border border-amber-800/30"
                        >
                          {gap}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-zinc-500">
                      No structural blockers or missing critical skills.
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'description' && (
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-surface-300/40 border border-white/5">
                <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2 font-mono">
                  Full Listing Description
                </h4>
                <div className="text-xs text-zinc-300 leading-relaxed whitespace-pre-line font-sans">
                  {opportunity.description}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'contacts' && (
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-surface-300/40 border border-white/5">
                <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3 font-mono">
                  Identified Team & Hiring Contacts
                </h4>
                {opportunity.contacts && opportunity.contacts.length > 0 ? (
                  <div className="space-y-2">
                    {opportunity.contacts.map((c: any) => (
                      <div
                        key={c.id}
                        className="p-3 rounded-lg bg-surface-200 border border-white/5 flex items-center justify-between"
                      >
                        <div>
                          <p className="text-xs font-semibold text-white">{c.full_name}</p>
                          <p className="text-[11px] text-zinc-400">
                            {c.role} • {c.company_name}
                          </p>
                          {c.email && (
                            <p className="text-[10px] font-mono text-zinc-500 mt-0.5">{c.email}</p>
                          )}
                        </div>
                        <span className="text-[10px] font-mono text-brand-300 bg-brand-950/40 px-2 py-0.5 rounded border border-brand-800/40">
                          {c.relationship_status}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-zinc-500">
                    No contacts mapped yet. Preparing an application will initiate contact discovery.
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer Actions */}
        <div className="p-4 border-t border-white/5 bg-surface-300/40 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleUpdateStatus('ARCHIVED')}
              className="px-3 py-1.5 rounded-lg text-xs font-medium text-zinc-400 hover:text-zinc-200 hover:bg-white/5 transition-colors"
            >
              Archive
            </button>
            <button
              onClick={() => handleUpdateStatus('STRONG_MATCH')}
              className="px-3 py-1.5 rounded-lg text-xs font-medium text-zinc-400 hover:text-zinc-200 hover:bg-white/5 transition-colors"
            >
              Star / Save
            </button>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded-lg text-xs font-medium text-zinc-400 hover:text-zinc-200 transition-colors"
            >
              Close
            </button>
            <button
              onClick={handlePrepareApplication}
              disabled={preparing}
              className="px-4 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-xs font-semibold text-white shadow-glow transition-all"
            >
              {preparing ? 'Synthesizing Package...' : 'Prepare Application'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

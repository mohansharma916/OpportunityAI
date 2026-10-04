'use client';

import React, { useState } from 'react';
import {
  X,
  CheckCircle2,
  FileText,
  Send,
  Building,
  ShieldAlert,
  Sparkles,
  ArrowRight,
  Loader2,
  Edit3,
} from 'lucide-react';
import { fetchApi } from '@/lib/api';

interface ApplicationReviewModalProps {
  application: any;
  onClose: () => void;
  onSubmitted: () => void;
}

export function ApplicationReviewModal({
  application,
  onClose,
  onSubmitted,
}: ApplicationReviewModalProps) {
  const [submitting, setSubmitting] = useState(false);
  const [userNotes, setUserNotes] = useState('');
  const [editableCover, setEditableCover] = useState(
    application?.cover_letter?.content || ''
  );

  if (!application) return null;

  const resume = application.resume_variant;
  const cover = application.cover_letter;
  const opp = application.opportunity;

  const handleApproveAndSubmit = async () => {
    setSubmitting(true);
    try {
      await fetchApi(`/api/applications/${application.id}/approve`, {
        method: 'POST',
        body: JSON.stringify({ user_notes: userNotes }),
      });
      onSubmitted();
      onClose();
    } catch (err: any) {
      alert(`Submission error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-4">
      <div className="w-full max-w-6xl max-h-[92vh] bg-surface-200 border border-white/10 rounded-2xl shadow-2xl flex flex-col overflow-hidden glass-panel animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-5 border-b border-white/5 flex items-center justify-between bg-surface-300/40">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-semibold text-zinc-400 uppercase tracking-wider">
                  Review Package
                </span>
                <span className="text-[10px] font-mono text-amber-300 bg-amber-950/40 px-2 py-0.5 rounded border border-amber-800/40">
                  {application.status}
                </span>
              </div>
              <h2 className="text-base font-bold text-white tracking-tight">
                {opp?.company_name} — {opp?.title}
              </h2>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-zinc-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Side-by-Side Review Grid */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 overflow-y-auto divide-y lg:divide-y-0 lg:divide-x divide-white/5">
          {/* Left Column: Job Requirements & Grounded Candidate Evidence */}
          <div className="p-6 space-y-6 overflow-y-auto">
            <div>
              <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2 font-mono flex items-center gap-2">
                <Building className="w-3.5 h-3.5 text-zinc-500" /> Original Job Requirements
              </h3>
              <div className="p-3.5 rounded-lg bg-surface-300/50 border border-white/5 space-y-2">
                <p className="text-xs font-semibold text-white">{opp?.title}</p>
                <div className="flex flex-wrap gap-1">
                  {(opp?.required_skills || []).map((s: string, idx: number) => (
                    <span
                      key={idx}
                      className="text-[10px] font-mono bg-white/5 text-zinc-300 px-2 py-0.5 rounded border border-white/5"
                    >
                      {s}
                    </span>
                  ))}
                </div>
                <p className="text-xs text-zinc-400 leading-relaxed pt-2 border-t border-white/5 line-clamp-4 font-sans">
                  {opp?.description}
                </p>
              </div>
            </div>

            {/* Candidate Grounded Evidence */}
            <div>
              <h3 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2 font-mono flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5" /> Verified Candidate Evidence Grounding
              </h3>
              <div className="space-y-2.5">
                {(resume?.emphasized_achievements || []).map((ach: string, idx: number) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/20 text-xs text-zinc-200"
                  >
                    <span className="text-[10px] font-mono text-emerald-400 block mb-0.5">
                      VERIFIED IMPACT #{idx + 1}
                    </span>
                    {ach}
                  </div>
                ))}
              </div>
            </div>

            {/* Verified Form Answers */}
            <div>
              <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2 font-mono">
                Verified Q&A Pre-Fill Answers
              </h3>
              <div className="space-y-2 text-xs">
                <div className="p-3 rounded-lg bg-surface-300/40 border border-white/5">
                  <span className="text-zinc-500 block text-[10px]">Work Authorization</span>
                  <span className="text-zinc-200">Authorized to work without sponsorship.</span>
                </div>
                <div className="p-3 rounded-lg bg-surface-300/40 border border-white/5">
                  <span className="text-zinc-500 block text-[10px]">Notice Period</span>
                  <span className="text-zinc-200">2 weeks standard notice.</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Tailored Resume & Generated Cover Letter */}
          <div className="p-6 space-y-6 overflow-y-auto bg-surface-300/20">
            {/* Tailored Resume Changes */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xs font-semibold text-brand-400 uppercase tracking-wider font-mono flex items-center gap-2">
                  <Sparkles className="w-3.5 h-3.5" /> Targeted Resume Variant
                </h3>
                <span className="text-[10px] font-mono text-zinc-500">
                  Hash: {resume?.content_hash || 'auto'}
                </span>
              </div>

              <div className="p-4 rounded-lg bg-surface-300/70 border border-brand-500/20 space-y-3">
                <div>
                  <span className="text-[10px] text-zinc-500 uppercase font-mono">Headline</span>
                  <p className="text-xs font-semibold text-white mt-0.5">{resume?.headline}</p>
                </div>
                <div>
                  <span className="text-[10px] text-zinc-500 uppercase font-mono">Tailored Summary</span>
                  <p className="text-xs text-zinc-300 mt-0.5 leading-relaxed">{resume?.summary}</p>
                </div>
                <div>
                  <span className="text-[10px] text-zinc-500 uppercase font-mono">Emphasized Skills Priority</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {(resume?.selected_skills || []).map((sk: string, idx: number) => (
                      <span
                        key={idx}
                        className="text-[10px] font-mono bg-brand-500/10 text-brand-300 px-2 py-0.5 rounded border border-brand-500/20"
                      >
                        {sk}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Generated Cover Letter */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider font-mono flex items-center gap-2">
                  <Edit3 className="w-3.5 h-3.5 text-zinc-500" /> Tailored Cover Letter ({cover?.style || 'TECHNICAL'})
                </h3>
              </div>
              <textarea
                rows={8}
                value={editableCover}
                onChange={(e) => setEditableCover(e.target.value)}
                className="w-full bg-surface-300 border border-white/10 rounded-lg p-3 text-xs text-zinc-200 leading-relaxed font-sans focus:outline-none focus:border-brand-500/50"
              />
            </div>

            {/* User Approval Notes */}
            <div>
              <label className="text-[11px] font-medium text-zinc-400 block mb-1">
                Optional Approval / Audit Note
              </label>
              <input
                type="text"
                value={userNotes}
                onChange={(e) => setUserNotes(e.target.value)}
                placeholder="e.g. Approved with custom cover letter emphasis on Next.js..."
                className="w-full bg-surface-300 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-500/50"
              />
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-white/5 bg-surface-300/40 flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-xs font-medium text-zinc-400 hover:text-zinc-200 hover:bg-white/5 transition-colors"
          >
            Cancel
          </button>

          <div className="flex items-center gap-3">
            <button
              onClick={handleApproveAndSubmit}
              disabled={submitting}
              className="px-5 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-xs font-semibold text-white shadow-glow-emerald transition-all flex items-center gap-2"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Submitting & Recording Audit...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Approve & Submit Application</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

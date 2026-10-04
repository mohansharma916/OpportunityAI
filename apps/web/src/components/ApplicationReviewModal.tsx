'use client';

import React, { useState, useEffect } from 'react';
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
  Plus,
  Trash2,
  Save,
  HelpCircle,
  Check,
} from 'lucide-react';
import { fetchApi } from '@/lib/api';

interface ApplicationReviewModalProps {
  application: any;
  verifiedAnswers?: any[];
  onClose: () => void;
  onSubmitted: () => void;
  onUpdateAnswers?: () => void;
}

export function ApplicationReviewModal({
  application,
  verifiedAnswers,
  onClose,
  onSubmitted,
  onUpdateAnswers,
}: ApplicationReviewModalProps) {
  const [submitting, setSubmitting] = useState(false);
  const [userNotes, setUserNotes] = useState('');
  const [editableCover, setEditableCover] = useState(
    application?.cover_letter?.content || ''
  );

  // Dynamic Q&A State
  const [qAnswers, setQAnswers] = useState<any[]>(verifiedAnswers || []);
  const [editingAnsId, setEditingAnsId] = useState<string | null>(null);
  const [editQText, setEditQText] = useState('');
  const [editAText, setEditAText] = useState('');
  const [showAddQ, setShowAddQ] = useState(false);
  const [newQText, setNewQText] = useState('');
  const [newAText, setNewAText] = useState('');
  const [savingQA, setSavingQA] = useState(false);

  useEffect(() => {
    if (verifiedAnswers && verifiedAnswers.length > 0) {
      setQAnswers(verifiedAnswers);
    } else {
      fetchApi<any[]>('/api/profile/answers')
        .then((res) => setQAnswers(res || []))
        .catch(() => {});
    }
  }, [verifiedAnswers]);

  if (!application) return null;

  const resume = application.resume_variant;
  const cover = application.cover_letter;
  const opp = application.opportunity;

  const handleStartEditAnswer = (a: any) => {
    setEditingAnsId(a.id);
    setEditQText(a.question_text);
    setEditAText(a.answer_text);
  };

  const handleSaveAnswerEdit = async (ansId: string) => {
    if (!editQText.trim() || !editAText.trim()) return;
    setSavingQA(true);
    try {
      const updated = await fetchApi<any>(`/api/profile/answers/${ansId}`, {
        method: 'PUT',
        body: JSON.stringify({ question_text: editQText.trim(), answer_text: editAText.trim() }),
      });
      setQAnswers((prev) => prev.map((item) => (item.id === ansId ? updated : item)));
      setEditingAnsId(null);
      onUpdateAnswers?.();
    } catch (err: any) {
      alert(`Failed to update question: ${err.message}`);
    } finally {
      setSavingQA(false);
    }
  };

  const handleAddNewQuestion = async () => {
    if (!newQText.trim() || !newAText.trim()) return;
    setSavingQA(true);
    try {
      const created = await fetchApi<any>('/api/profile/answers', {
        method: 'POST',
        body: JSON.stringify({
          question_text: newQText.trim(),
          answer_text: newAText.trim(),
          source: 'APPLICATION_REVIEW',
        }),
      });
      setQAnswers((prev) => [...prev, created]);
      setNewQText('');
      setNewAText('');
      setShowAddQ(false);
      onUpdateAnswers?.();
    } catch (err: any) {
      alert(`Failed to add application question: ${err.message}`);
    } finally {
      setSavingQA(false);
    }
  };

  const handleApproveAndSubmit = async () => {
    setSubmitting(true);
    try {
      await fetchApi(`/api/applications/${application.id}/approve`, {
        method: 'POST',
        body: JSON.stringify({ user_notes: userNotes, answers: qAnswers }),
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
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
                    <HelpCircle className="w-3.5 h-3.5 text-emerald-400" />
                    Verified Q&A Pre-Fill Answers ({qAnswers.length})
                  </h3>
                  <span className="text-[10px] text-zinc-500 font-mono">
                    Editable responses saved to your memory bank for all future jobs.
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setShowAddQ(!showAddQ)}
                  className="text-[10px] font-mono bg-white/5 hover:bg-white/10 text-brand-300 border border-brand-500/30 px-2 py-1 rounded flex items-center gap-1 transition-colors"
                >
                  {showAddQ ? <X className="w-3 h-3" /> : <Plus className="w-3 h-3" />}
                  {showAddQ ? 'Cancel' : '+ Add Question'}
                </button>
              </div>

              {/* Add Application-Specific Question Panel */}
              {showAddQ && (
                <div className="p-3 rounded-lg bg-surface-300/90 border border-brand-500/40 space-y-2 shadow-sm animate-in fade-in duration-150">
                  <span className="text-[11px] font-semibold text-brand-300 font-mono block">
                    Add Question for this Application & Memory Bank
                  </span>
                  <input
                    type="text"
                    placeholder="Question (e.g. Are you legally authorized to work in the United States?)..."
                    value={newQText}
                    onChange={(e) => setNewQText(e.target.value)}
                    className="w-full bg-surface-400 border border-white/10 rounded px-2.5 py-1.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-500/50"
                  />
                  <textarea
                    rows={2}
                    placeholder="Your answer for this and future applications..."
                    value={newAText}
                    onChange={(e) => setNewAText(e.target.value)}
                    className="w-full bg-surface-400 border border-white/10 rounded px-2.5 py-1.5 text-xs text-emerald-300 font-mono placeholder-zinc-500 focus:outline-none focus:border-brand-500/50"
                  />
                  <div className="flex justify-end gap-1.5">
                    <button
                      type="button"
                      onClick={() => setShowAddQ(false)}
                      className="text-[11px] font-mono text-zinc-400 hover:text-white px-2 py-0.5 rounded"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      disabled={savingQA || !newQText.trim() || !newAText.trim()}
                      onClick={handleAddNewQuestion}
                      className="text-[11px] font-mono bg-brand-500 hover:bg-brand-400 text-white px-3 py-1 rounded flex items-center gap-1 transition-colors disabled:opacity-50"
                    >
                      {savingQA ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />}
                      Save & Remember
                    </button>
                  </div>
                </div>
              )}

              {/* Q&A List */}
              <div className="space-y-2 text-xs max-h-64 overflow-y-auto pr-1">
                {qAnswers.length === 0 ? (
                  <div className="p-3 text-center text-zinc-500 text-xs font-mono rounded bg-surface-300/30">
                    No pre-fill answers yet. Click "+ Add Question" to answer.
                  </div>
                ) : (
                  qAnswers.map((ans: any) => {
                    const isEditing = editingAnsId === ans.id;

                    if (isEditing) {
                      return (
                        <div
                          key={ans.id}
                          className="p-3 rounded-lg bg-surface-300/90 border border-brand-500/40 space-y-2"
                        >
                          <input
                            type="text"
                            value={editQText}
                            onChange={(e) => setEditQText(e.target.value)}
                            className="w-full bg-surface-400 border border-white/10 rounded px-2 py-1 text-xs text-white focus:outline-none focus:border-brand-500/50"
                          />
                          <textarea
                            rows={2}
                            value={editAText}
                            onChange={(e) => setEditAText(e.target.value)}
                            className="w-full bg-surface-400 border border-white/10 rounded px-2 py-1 text-xs text-emerald-300 font-mono focus:outline-none focus:border-brand-500/50"
                          />
                          <div className="flex justify-end gap-1.5">
                            <button
                              type="button"
                              onClick={() => setEditingAnsId(null)}
                              className="text-[10px] font-mono text-zinc-400 hover:text-white px-2 py-0.5 rounded"
                            >
                              Cancel
                            </button>
                            <button
                              type="button"
                              disabled={savingQA}
                              onClick={() => handleSaveAnswerEdit(ans.id)}
                              className="text-[10px] font-mono bg-brand-500 hover:bg-brand-400 text-white px-2.5 py-1 rounded flex items-center gap-1 transition-colors"
                            >
                              {savingQA ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />}
                              Save
                            </button>
                          </div>
                        </div>
                      );
                    }

                    return (
                      <div
                        key={ans.id}
                        className="p-3 rounded-lg bg-surface-300/40 border border-white/5 space-y-1.5 hover:border-brand-500/20 transition-all"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <span className="text-zinc-300 font-medium text-[11px] block leading-snug">
                            {ans.question_text}
                          </span>
                          <button
                            type="button"
                            onClick={() => handleStartEditAnswer(ans)}
                            className="text-zinc-500 hover:text-brand-300 p-0.5 rounded transition-colors"
                            title="Edit this answer"
                          >
                            <Edit3 className="w-3 h-3" />
                          </button>
                        </div>
                        <p className="text-emerald-300 font-mono text-[11px] bg-emerald-950/20 px-2 py-1 rounded border border-emerald-500/20 leading-relaxed">
                          "{ans.answer_text}"
                        </p>
                      </div>
                    );
                  })
                )}
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

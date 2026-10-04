'use client';

import React, { useState, useEffect } from 'react';
import {
  User,
  ShieldCheck,
  CheckCircle2,
  Award,
  Clock,
  Briefcase,
  DollarSign,
  MapPin,
  Sparkles,
  HelpCircle,
  FileCheck,
  Plus,
  Trash2,
  Edit3,
  Save,
  X,
  Loader2,
  Check,
} from 'lucide-react';
import { fetchApi } from '@/lib/api';

interface ProfileViewProps {
  profile: any;
  verifiedAnswers: any[];
  onRestartOnboarding?: () => void;
  onUpdateAnswers?: () => void;
}

export function ProfileView({
  profile,
  verifiedAnswers,
  onRestartOnboarding,
  onUpdateAnswers,
}: ProfileViewProps) {
  const [activeSection, setActiveSection] = useState<'skills' | 'knowledge' | 'answers' | 'experience'>('skills');

  // Answers State & Management
  const [answersList, setAnswersList] = useState<any[]>(verifiedAnswers || []);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editQuestion, setEditQuestion] = useState('');
  const [editAnswer, setEditAnswer] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);

  const [showAddAnswer, setShowAddAnswer] = useState(false);
  const [newQuestion, setNewQuestion] = useState('');
  const [newAnswer, setNewAnswer] = useState('');
  const [savingNew, setSavingNew] = useState(false);

  useEffect(() => {
    setAnswersList(verifiedAnswers || []);
  }, [verifiedAnswers]);

  const handleStartEdit = (ans: any) => {
    setEditingId(ans.id);
    setEditQuestion(ans.question_text);
    setEditAnswer(ans.answer_text);
  };

  const handleSaveEdit = async (ansId: string) => {
    if (!editQuestion.trim() || !editAnswer.trim()) return;
    setSavingEdit(true);
    try {
      const updated = await fetchApi<any>(`/api/profile/answers/${ansId}`, {
        method: 'PUT',
        body: JSON.stringify({
          question_text: editQuestion.trim(),
          answer_text: editAnswer.trim(),
        }),
      });
      setAnswersList((prev) => prev.map((a) => (a.id === ansId ? updated : a)));
      setEditingId(null);
      onUpdateAnswers?.();
    } catch (err: any) {
      alert(`Failed to save question: ${err.message}`);
    } finally {
      setSavingEdit(false);
    }
  };

  const handleDeleteAnswer = async (ansId: string) => {
    if (!confirm('Are you sure you want to remove this question from your application memory?')) return;
    try {
      await fetchApi(`/api/profile/answers/${ansId}`, { method: 'DELETE' });
      setAnswersList((prev) => prev.filter((a) => a.id !== ansId));
      onUpdateAnswers?.();
    } catch (err: any) {
      alert(`Failed to delete answer: ${err.message}`);
    }
  };

  const handleCreateAnswer = async () => {
    if (!newQuestion.trim() || !newAnswer.trim()) return;
    setSavingNew(true);
    try {
      const created = await fetchApi<any>('/api/profile/answers', {
        method: 'POST',
        body: JSON.stringify({
          question_text: newQuestion.trim(),
          answer_text: newAnswer.trim(),
          source: 'USER_PROFILE',
        }),
      });
      setAnswersList((prev) => [created, ...prev.filter((a) => a.id !== created.id)]);
      setNewQuestion('');
      setNewAnswer('');
      setShowAddAnswer(false);
      onUpdateAnswers?.();
    } catch (err: any) {
      alert(`Failed to add answer: ${err.message}`);
    } finally {
      setSavingNew(false);
    }
  };

  if (!profile) return null;

  const currCode = profile.salary_currency || profile.preferred_currencies?.[0] || 'USD';
  const currencySymbol = currCode === 'INR' ? '₹' : currCode === 'GBP' ? '£' : currCode === 'EUR' ? '€' : '$';

  return (
    <div className="space-y-6">
      {/* Profile Overview Card */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-surface-100 to-surface-200 border border-white/10 glass-panel">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-brand-600 to-cyan-500 flex items-center justify-center text-white font-bold text-xl shadow-glow">
              {profile.full_name ? profile.full_name.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase() : 'CP'}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-white tracking-tight">
                  {profile.full_name}
                </h2>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40 flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3" /> Grounded & Verified
                </span>
              </div>
              <p className="text-xs text-brand-300 font-medium mt-0.5">{profile.headline}</p>
              <div className="flex flex-wrap items-center gap-3 text-xs text-zinc-400 mt-2">
                <span className="flex items-center gap-1">
                  <MapPin className="w-3 h-3 text-zinc-500" /> {profile.location}
                </span>
                <span>•</span>
                <span className="font-mono text-emerald-400">
                  Floor: {currencySymbol}{profile.minimum_salary_annual?.toLocaleString()}/yr or {currencySymbol}{profile.minimum_hourly_rate}/hr
                </span>
                <span>•</span>
                <span className="font-mono text-brand-300 bg-brand-500/10 px-2 py-0.5 rounded border border-brand-500/20 text-[10px]">
                  {currCode} ({currencySymbol})
                </span>
                <span>•</span>
                <span className="font-mono text-zinc-400">
                  Timezone: {profile.timezone}
                </span>
              </div>
            </div>
          </div>

          <div className="flex flex-col items-end gap-2 self-start sm:self-center">
            <div className="p-3 rounded-xl bg-surface-300/80 border border-white/5 text-right">
              <span className="text-[10px] text-zinc-500 uppercase font-mono block">Automation Guardrail</span>
              <span className="text-xs font-semibold text-brand-300 font-mono">
                Level {profile.automation_level}: Human Approval Gate
              </span>
            </div>
            {onRestartOnboarding && (
              <button
                onClick={onRestartOnboarding}
                className="text-[11px] font-mono text-brand-300 hover:text-brand-200 bg-brand-500/10 hover:bg-brand-500/20 px-3 py-1.5 rounded-lg border border-brand-500/30 transition-all flex items-center gap-1.5 shadow-sm"
              >
                <Sparkles className="w-3.5 h-3.5 text-brand-400" /> Re-run Resume Onboarding
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-white/5 bg-surface-400/40 px-4">
        {[
          { id: 'skills', label: 'Verified Skills & Evidence' },
          { id: 'knowledge', label: 'Career Knowledge Base' },
          { id: 'answers', label: 'Application Q&A Memory' },
          { id: 'experience', label: 'Work History' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveSection(tab.id as any)}
            className={`py-3 px-4 text-xs font-medium border-b-2 transition-all ${
              activeSection === tab.id
                ? 'border-brand-500 text-brand-400'
                : 'border-transparent text-zinc-400 hover:text-zinc-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content Panels */}
      {activeSection === 'skills' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {(profile.skills || []).map((skill: any) => (
            <div
              key={skill.id || skill.skill_name}
              className="p-4 rounded-xl bg-surface-300/50 border border-white/5 space-y-2 hover:border-brand-500/30 transition-all"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white">{skill.skill_name}</span>
                <span className="text-[10px] font-mono text-brand-400 bg-brand-500/10 px-1.5 py-0.5 rounded border border-brand-500/20">
                  {skill.proficiency}
                </span>
              </div>
              <p className="text-[11px] text-zinc-400 font-mono">
                {skill.experience_years} Years • {skill.last_used}
              </p>
              {skill.related_projects && skill.related_projects.length > 0 && (
                <div className="pt-2 border-t border-white/5">
                  <span className="text-[10px] text-zinc-500 uppercase font-mono block mb-1">
                    Related Projects:
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {skill.related_projects.map((p: string, idx: number) => (
                      <span
                        key={idx}
                        className="text-[9px] bg-white/5 text-zinc-300 px-1.5 py-0.5 rounded border border-white/5"
                      >
                        {p}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {activeSection === 'knowledge' && (
        <div className="space-y-3">
          {(profile.knowledge_items || []).map((item: any) => (
            <div
              key={item.id}
              className="p-4 rounded-xl bg-surface-300/40 border border-white/5 space-y-2"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white flex items-center gap-2">
                  <Award className="w-3.5 h-3.5 text-emerald-400" />
                  {item.title}
                </span>
                {item.quantified_impact && (
                  <span className="text-[10px] font-mono font-bold text-emerald-300 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40">
                    {item.quantified_impact}
                  </span>
                )}
              </div>
              <p className="text-xs text-zinc-300 leading-relaxed font-sans">{item.raw_content}</p>
              <div className="flex flex-wrap gap-1 pt-1">
                {(item.associated_skills || []).map((s: string, idx: number) => (
                  <span
                    key={idx}
                    className="text-[9px] font-mono bg-brand-500/10 text-brand-300 px-1.5 py-0.5 rounded border border-brand-500/20"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {activeSection === 'answers' && (
        <div className="space-y-4">
          {/* Header & Add Button */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl bg-surface-300/30 border border-white/5">
            <div>
              <h3 className="text-xs font-bold text-white font-mono flex items-center gap-2">
                <HelpCircle className="w-4 h-4 text-emerald-400" />
                Application Screening Q&A Memory ({answersList.length})
              </h3>
              <p className="text-[11px] text-zinc-400 font-mono mt-0.5">
                Every response saved here is remembered by the autonomous agent to pre-fill future applications & ATS screening forms.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowAddAnswer(!showAddAnswer)}
              className="text-xs font-mono bg-brand-500/20 hover:bg-brand-500/30 text-brand-300 border border-brand-500/40 px-3 py-1.5 rounded-lg flex items-center gap-1.5 self-start sm:self-auto transition-colors"
            >
              {showAddAnswer ? <X className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
              {showAddAnswer ? 'Cancel' : '+ Add Question & Answer'}
            </button>
          </div>

          {/* Add New Question & Answer Panel */}
          {showAddAnswer && (
            <div className="p-4 rounded-xl bg-surface-300/80 border border-brand-500/40 space-y-3 shadow-glow animate-in fade-in duration-200">
              <span className="text-xs font-semibold text-brand-300 font-mono block">
                Add Screening Question & Reusable Response
              </span>
              <div className="space-y-2">
                <input
                  type="text"
                  placeholder="Question (e.g. Are you legally authorized to work in the United States?)..."
                  value={newQuestion}
                  onChange={(e) => setNewQuestion(e.target.value)}
                  className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-500/50"
                />
                <textarea
                  rows={3}
                  placeholder="Your verified answer (e.g. Yes, I am legally authorized to work in the United States without restrictions.)..."
                  value={newAnswer}
                  onChange={(e) => setNewAnswer(e.target.value)}
                  className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-xs text-emerald-300 font-mono placeholder-zinc-500 focus:outline-none focus:border-brand-500/50"
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddAnswer(false)}
                  className="text-xs font-mono text-zinc-400 hover:text-white px-3 py-1 rounded"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={savingNew || !newQuestion.trim() || !newAnswer.trim()}
                  onClick={handleCreateAnswer}
                  className="text-xs font-mono bg-brand-500 hover:bg-brand-400 text-white font-medium px-4 py-1.5 rounded-lg flex items-center gap-1.5 disabled:opacity-50 transition-colors shadow-sm"
                >
                  {savingNew ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                  Save to Knowledge Bank
                </button>
              </div>
            </div>
          )}

          {/* Answers List */}
          <div className="space-y-3">
            {answersList.length === 0 ? (
              <div className="p-8 text-center text-zinc-500 text-xs font-mono rounded-xl bg-surface-300/20 border border-white/5">
                No screening questions saved yet. Click "+ Add Question & Answer" to seed your bank.
              </div>
            ) : (
              answersList.map((ans: any) => {
                const isEditing = editingId === ans.id;

                if (isEditing) {
                  return (
                    <div
                      key={ans.id}
                      className="p-4 rounded-xl bg-surface-300/80 border border-brand-500/40 space-y-3"
                    >
                      <span className="text-[10px] font-mono text-brand-400 uppercase tracking-wider block">
                        Edit Question & Response
                      </span>
                      <input
                        type="text"
                        value={editQuestion}
                        onChange={(e) => setEditQuestion(e.target.value)}
                        className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-brand-500/50"
                      />
                      <textarea
                        rows={3}
                        value={editAnswer}
                        onChange={(e) => setEditAnswer(e.target.value)}
                        className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-xs text-emerald-300 font-mono focus:outline-none focus:border-brand-500/50"
                      />
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => setEditingId(null)}
                          className="text-xs font-mono text-zinc-400 hover:text-white px-3 py-1 rounded"
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          disabled={savingEdit}
                          onClick={() => handleSaveEdit(ans.id)}
                          className="text-xs font-mono bg-brand-500 hover:bg-brand-400 text-white px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-colors"
                        >
                          {savingEdit ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                          Save Changes
                        </button>
                      </div>
                    </div>
                  );
                }

                return (
                  <div
                    key={ans.id}
                    className="p-4 rounded-xl bg-surface-300/40 border border-white/5 space-y-2 hover:border-brand-500/20 transition-all group"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-0.5">
                        <span className="text-xs font-semibold text-zinc-200 font-sans leading-relaxed">
                          {ans.question_text}
                        </span>
                        <div className="flex items-center gap-2 pt-0.5">
                          <span className="text-[9px] font-mono text-zinc-500">
                            ID: {ans.question_canonical || 'custom'}
                          </span>
                          {ans.source && (
                            <span className="text-[9px] font-mono text-zinc-500 bg-white/5 px-1 rounded">
                              {ans.source}
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40 flex items-center gap-1">
                          <ShieldCheck className="w-3 h-3" /> Verified
                        </span>
                        <button
                          type="button"
                          onClick={() => handleStartEdit(ans)}
                          className="text-zinc-400 hover:text-brand-300 p-1 rounded hover:bg-white/5 transition-colors"
                          title="Edit question & answer"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteAnswer(ans.id)}
                          className="text-zinc-500 hover:text-rose-400 p-1 rounded hover:bg-white/5 transition-colors"
                          title="Delete from memory"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <p className="text-xs text-emerald-300 font-mono bg-emerald-950/20 p-2.5 rounded-lg border border-emerald-500/20 leading-relaxed">
                      "{ans.answer_text}"
                    </p>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}

      {activeSection === 'experience' && (
        <div className="space-y-3">
          {(profile.work_experiences || []).map((exp: any) => (
            <div
              key={exp.id || exp.company}
              className="p-4 rounded-xl bg-surface-300/40 border border-white/5 space-y-2"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-white">{exp.role}</h4>
                  <p className="text-[11px] text-zinc-400">{exp.company} • {exp.location}</p>
                </div>
                <span className="text-[10px] font-mono text-zinc-400 bg-white/5 px-2 py-0.5 rounded">
                  {exp.start_date} → {exp.is_current ? 'Present' : exp.end_date}
                </span>
              </div>
              <p className="text-xs text-zinc-300 leading-relaxed font-sans">{exp.summary}</p>
              <ul className="list-disc list-inside space-y-1 text-xs text-zinc-400 pl-1">
                {(exp.key_achievements || []).map((ach: string, idx: number) => (
                  <li key={idx}>{ach}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

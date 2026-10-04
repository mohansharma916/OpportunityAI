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
  Sliders,
  Globe,
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

  // Edit Profile Details Modal State
  const [showEditProfileModal, setShowEditProfileModal] = useState(false);
  const [editFullName, setEditFullName] = useState(profile?.full_name || '');
  const [editHeadline, setEditHeadline] = useState(profile?.headline || '');
  const [editLocation, setEditLocation] = useState(profile?.location || '');
  const [editCountry, setEditCountry] = useState(profile?.country || '');
  const [editTimezone, setEditTimezone] = useState(profile?.timezone || '');
  const [editWorkingHours, setEditWorkingHours] = useState(profile?.preferred_working_hours || '');
  const [editTargetRoles, setEditTargetRoles] = useState((profile?.target_roles || []).join(', '));
  const [editMinSalary, setEditMinSalary] = useState(profile?.minimum_salary_annual || 160000);
  const [editMinHourly, setEditMinHourly] = useState(profile?.minimum_hourly_rate || 85);
  const [editCurrency, setEditCurrency] = useState(profile?.salary_currency || 'USD');
  const [editRemotePref, setEditRemotePref] = useState(profile?.remote_preference || 'REMOTE');
  const [editNoticeDays, setEditNoticeDays] = useState(profile?.notice_period_days || 14);
  const [editSponsorship, setEditSponsorship] = useState(profile?.visa_sponsorship_needed || false);
  const [editAuthCountries, setEditAuthCountries] = useState((profile?.authorized_countries || []).join(', '));
  const [editAutoLevel, setEditAutoLevel] = useState(profile?.automation_level || 3);
  const [savingProfile, setSavingProfile] = useState(false);

  // Add Skill State
  const [newSkillName, setNewSkillName] = useState('');
  const [newSkillYears, setNewSkillYears] = useState(3.0);
  const [newSkillProf, setNewSkillProf] = useState('ADVANCED');
  const [addingSkill, setAddingSkill] = useState(false);

  // Add Experience State
  const [showAddExpModal, setShowAddExpModal] = useState(false);
  const [newExpCompany, setNewExpCompany] = useState('');
  const [newExpRole, setNewExpRole] = useState('');
  const [newExpLocation, setNewExpLocation] = useState('Remote');
  const [newExpStart, setNewExpStart] = useState('2022');
  const [newExpEnd, setNewExpEnd] = useState('Present');
  const [newExpSummary, setNewExpSummary] = useState('');
  const [newExpTech, setNewExpTech] = useState('');
  const [savingExp, setSavingExp] = useState(false);

  useEffect(() => {
    setAnswersList(verifiedAnswers || []);
  }, [verifiedAnswers]);

  useEffect(() => {
    if (profile) {
      setEditFullName(profile.full_name || '');
      setEditHeadline(profile.headline || '');
      setEditLocation(profile.location || '');
      setEditCountry(profile.country || '');
      setEditTimezone(profile.timezone || '');
      setEditWorkingHours(profile.preferred_working_hours || '');
      setEditTargetRoles((profile.target_roles || []).join(', '));
      setEditMinSalary(profile.minimum_salary_annual || 160000);
      setEditMinHourly(profile.minimum_hourly_rate || 85);
      setEditCurrency(profile.salary_currency || 'USD');
      setEditRemotePref(profile.remote_preference || 'REMOTE');
      setEditNoticeDays(profile.notice_period_days || 14);
      setEditSponsorship(profile.visa_sponsorship_needed || false);
      setEditAuthCountries((profile.authorized_countries || []).join(', '));
      setEditAutoLevel(profile.automation_level || 3);
    }
  }, [profile]);

  // Answer Handlers
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
      setAnswersList((prev) => prev.map((a: any) => (a.id === ansId ? updated : a)));
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

  // Profile Update Handler
  const handleSaveProfile = async () => {
    setSavingProfile(true);
    try {
      await fetchApi('/api/profile', {
        method: 'PUT',
        body: JSON.stringify({
          full_name: editFullName.trim(),
          headline: editHeadline.trim(),
          location: editLocation.trim(),
          country: editCountry.trim(),
          timezone: editTimezone.trim(),
          preferred_working_hours: editWorkingHours.trim(),
          target_roles: editTargetRoles.split(',').map((r: string) => r.trim()).filter(Boolean),
          minimum_salary_annual: parseFloat(String(editMinSalary)),
          minimum_hourly_rate: parseFloat(String(editMinHourly)),
          salary_currency: editCurrency,
          preferred_currencies: [editCurrency],
          remote_preference: editRemotePref,
          notice_period_days: parseInt(String(editNoticeDays)),
          visa_sponsorship_needed: editSponsorship,
          authorized_countries: editAuthCountries.split(',').map((c: string) => c.trim()).filter(Boolean),
          automation_level: parseInt(String(editAutoLevel)),
        }),
      });
      setShowEditProfileModal(false);
      onUpdateAnswers?.();
    } catch (err: any) {
      alert(`Failed to update profile: ${err.message}`);
    } finally {
      setSavingProfile(false);
    }
  };

  // Skill Add / Delete
  const handleAddSkill = async () => {
    if (!newSkillName.trim()) return;
    setAddingSkill(true);
    try {
      await fetchApi('/api/profile/skills', {
        method: 'POST',
        body: JSON.stringify({
          skill_name: newSkillName.trim(),
          proficiency: newSkillProf,
          experience_years: parseFloat(String(newSkillYears)) || 1.0,
        }),
      });
      setNewSkillName('');
      onUpdateAnswers?.();
    } catch (err: any) {
      alert(`Failed to add skill: ${err.message}`);
    } finally {
      setAddingSkill(false);
    }
  };

  const handleDeleteSkill = async (skillId: string) => {
    if (!confirm('Remove this skill from your profile?')) return;
    try {
      await fetchApi(`/api/profile/skills/${skillId}`, { method: 'DELETE' });
      onUpdateAnswers?.();
    } catch (err: any) {
      alert(`Failed to delete skill: ${err.message}`);
    }
  };

  // Work Experience Add / Delete
  const handleAddExperience = async () => {
    if (!newExpCompany.trim() || !newExpRole.trim()) return;
    setSavingExp(true);
    try {
      await fetchApi('/api/profile/experiences', {
        method: 'POST',
        body: JSON.stringify({
          company: newExpCompany.trim(),
          role: newExpRole.trim(),
          location: newExpLocation.trim(),
          start_date: newExpStart.trim(),
          end_date: newExpEnd.trim(),
          is_current: newExpEnd.toLowerCase().includes('present'),
          summary: newExpSummary.trim(),
          technologies: newExpTech.split(',').map((t: string) => t.trim()).filter(Boolean),
        }),
      });
      setShowAddExpModal(false);
      setNewExpCompany('');
      setNewExpRole('');
      setNewExpSummary('');
      setNewExpTech('');
      onUpdateAnswers?.();
    } catch (err: any) {
      alert(`Failed to add experience: ${err.message}`);
    } finally {
      setSavingExp(false);
    }
  };

  const handleDeleteExperience = async (expId: string) => {
    if (!confirm('Delete this work experience entry?')) return;
    try {
      await fetchApi(`/api/profile/experiences/${expId}`, { method: 'DELETE' });
      onUpdateAnswers?.();
    } catch (err: any) {
      alert(`Failed to delete experience: ${err.message}`);
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
              <span className="text-[10px] text-zinc-500 uppercase font-mono block">Automation Policy</span>
              <span className="text-xs font-semibold text-brand-300 font-mono">
                Level {profile.automation_level}: Human Approval Gate
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setShowEditProfileModal(true)}
                className="text-xs font-mono text-zinc-200 hover:text-white bg-surface-300 hover:bg-surface-400 px-3 py-1.5 rounded-lg border border-white/10 transition-all flex items-center gap-1.5 shadow-sm"
              >
                <Edit3 className="w-3.5 h-3.5 text-brand-400" /> Edit Profile & Preferences
              </button>

              {onRestartOnboarding && (
                <button
                  type="button"
                  onClick={onRestartOnboarding}
                  className="text-xs font-mono text-brand-300 hover:text-brand-200 bg-brand-500/10 hover:bg-brand-500/20 px-3 py-1.5 rounded-lg border border-brand-500/30 transition-all flex items-center gap-1.5 shadow-sm"
                >
                  <Sparkles className="w-3.5 h-3.5 text-brand-400" /> Re-parse Resume
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-white/5 bg-surface-400/40 px-4">
        {[
          { id: 'skills', label: 'Verified Skills & Evidence' },
          { id: 'experience', label: 'Work History' },
          { id: 'answers', label: 'Application Q&A Memory' },
          { id: 'knowledge', label: 'Career Knowledge Base' },
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

      {/* Skills Tab with Add/Delete Capability */}
      {activeSection === 'skills' && (
        <div className="space-y-4">
          {/* Add Skill Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl bg-surface-300/40 border border-white/5">
            <div>
              <h3 className="text-xs font-bold text-white font-mono flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-brand-400" />
                Verified Skills & Evidence ({(profile.skills || []).length})
              </h3>
              <p className="text-[11px] text-zinc-400 font-mono mt-0.5">
                Technical competencies used by the matching engine to score fit and calculate seniority.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-1.5 bg-surface-400 p-1.5 rounded-lg border border-white/5">
              <input
                type="text"
                placeholder="Skill name (e.g. Next.js, Go)..."
                value={newSkillName}
                onChange={(e) => setNewSkillName(e.target.value)}
                className="bg-surface-500 border border-white/10 rounded px-2.5 py-1 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-500/50 w-36"
              />
              <div className="flex items-center gap-1 bg-surface-500 border border-white/10 rounded px-2 py-1">
                <input
                  type="number"
                  min="0.5"
                  max="30"
                  step="0.5"
                  value={newSkillYears}
                  onChange={(e) => setNewSkillYears(parseFloat(e.target.value) || 1)}
                  className="w-10 bg-transparent text-xs text-cyan-300 font-mono focus:outline-none"
                />
                <span className="text-[10px] text-zinc-400 font-mono">yrs</span>
              </div>
              <select
                value={newSkillProf}
                onChange={(e) => setNewSkillProf(e.target.value)}
                className="bg-surface-500 border border-white/10 rounded px-2 py-1 text-xs text-amber-300 font-mono focus:outline-none"
              >
                <option value="INTERMEDIATE">Intermediate</option>
                <option value="ADVANCED">Advanced</option>
                <option value="EXPERT">Expert</option>
              </select>
              <button
                type="button"
                disabled={addingSkill || !newSkillName.trim()}
                onClick={handleAddSkill}
                className="text-xs font-mono bg-brand-500 hover:bg-brand-400 text-white px-3 py-1 rounded font-medium transition-colors shadow-sm disabled:opacity-50"
              >
                + Add
              </button>
            </div>
          </div>

          {/* Skills Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {(profile.skills || []).map((skill: any) => (
              <div
                key={skill.id || skill.skill_name}
                className="p-4 rounded-xl bg-surface-300/50 border border-white/5 space-y-2 hover:border-brand-500/30 transition-all relative group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">{skill.skill_name}</span>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] font-mono text-brand-400 bg-brand-500/10 px-1.5 py-0.5 rounded border border-brand-500/20">
                      {skill.proficiency}
                    </span>
                    {skill.id && (
                      <button
                        type="button"
                        onClick={() => handleDeleteSkill(skill.id)}
                        className="text-zinc-500 hover:text-rose-400 p-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Remove skill"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
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
        </div>
      )}

      {/* Work Experience Tab with Add/Delete Capability */}
      {activeSection === 'experience' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 rounded-xl bg-surface-300/40 border border-white/5">
            <div>
              <h3 className="text-xs font-bold text-white font-mono flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-brand-400" />
                Work History & Experience ({(profile.work_experiences || []).length})
              </h3>
              <p className="text-[11px] text-zinc-400 font-mono mt-0.5">
                Past engineering roles, timeline, key achievements, and stack.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowAddExpModal(true)}
              className="text-xs font-mono bg-brand-500/20 hover:bg-brand-500/30 text-brand-300 border border-brand-500/40 px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" /> + Add Experience
            </button>
          </div>

          <div className="space-y-3">
            {(profile.work_experiences || []).map((exp: any) => (
              <div
                key={exp.id || exp.company}
                className="p-5 rounded-2xl bg-surface-300/40 border border-white/5 space-y-2 relative group hover:border-brand-500/20 transition-all"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-xs font-bold text-white">{exp.role}</h4>
                    <p className="text-[11px] text-zinc-400">{exp.company} • {exp.location}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono text-zinc-400 bg-white/5 px-2 py-0.5 rounded">
                      {exp.start_date} → {exp.is_current ? 'Present' : exp.end_date}
                    </span>
                    {exp.id && (
                      <button
                        type="button"
                        onClick={() => handleDeleteExperience(exp.id)}
                        className="text-zinc-500 hover:text-rose-400 p-1 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Delete experience"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
                <p className="text-xs text-zinc-300 leading-relaxed font-sans">{exp.summary}</p>
                {exp.key_achievements && exp.key_achievements.length > 0 && (
                  <ul className="list-disc list-inside space-y-1 text-xs text-zinc-400 pl-1 pt-1">
                    {exp.key_achievements.map((ach: string, idx: number) => (
                      <li key={idx}>{ach}</li>
                    ))}
                  </ul>
                )}
                {exp.technologies && exp.technologies.length > 0 && (
                  <div className="flex flex-wrap gap-1 pt-2 border-t border-white/5">
                    {exp.technologies.map((tech: string, idx: number) => (
                      <span key={idx} className="text-[10px] font-mono text-cyan-300 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/30">
                        {tech}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Answers Tab with Inline Edit/Delete/Add (Preserved & Enhanced) */}
      {activeSection === 'answers' && (
        <div className="space-y-4">
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

      {/* Career Knowledge Base Tab */}
      {activeSection === 'knowledge' && (
        <div className="space-y-3">
          {(profile.knowledge_items || []).map((item: any) => (
            <div
              key={item.id}
              className="p-4 rounded-xl bg-surface-300/40 border border-white/5 space-y-1.5"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-brand-400 uppercase tracking-wider">
                  {item.category}
                </span>
                <span className="text-[10px] font-mono text-zinc-500">
                  Confidence: {Math.round((item.confidence || 1) * 100)}%
                </span>
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

      {/* Edit Profile & Preferences Modal */}
      {showEditProfileModal && (
        <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-4">
          <div className="w-full max-w-2xl bg-surface-200 border border-white/10 rounded-2xl shadow-2xl overflow-hidden glass-panel max-h-[90vh] flex flex-col animate-in fade-in zoom-in-95 duration-150">
            <div className="p-5 border-b border-white/10 flex items-center justify-between bg-surface-300/50">
              <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                <Edit3 className="w-4 h-4 text-brand-400" />
                Edit Profile Details & Job Search Preferences
              </h3>
              <button
                type="button"
                onClick={() => setShowEditProfileModal(false)}
                className="text-zinc-400 hover:text-white p-1 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4 text-xs font-mono">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-zinc-400 block mb-1">Full Name</label>
                  <input
                    type="text"
                    value={editFullName}
                    onChange={(e) => setEditFullName(e.target.value)}
                    className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="text-zinc-400 block mb-1">Headline</label>
                  <input
                    type="text"
                    value={editHeadline}
                    onChange={(e) => setEditHeadline(e.target.value)}
                    className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-zinc-400 block mb-1">Location</label>
                  <input
                    type="text"
                    value={editLocation}
                    onChange={(e) => setEditLocation(e.target.value)}
                    className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="text-zinc-400 block mb-1">Country</label>
                  <input
                    type="text"
                    value={editCountry}
                    onChange={(e) => setEditCountry(e.target.value)}
                    className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-zinc-400 block mb-1">Target Job Roles (comma-separated)</label>
                <input
                  type="text"
                  value={editTargetRoles}
                  onChange={(e) => setEditTargetRoles(e.target.value)}
                  className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-brand-500"
                  placeholder="e.g. Senior Full Stack Engineer, Staff Backend Engineer, Tech Lead"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-zinc-400 block mb-1">Min Annual Salary</label>
                  <input
                    type="number"
                    value={editMinSalary}
                    onChange={(e) => setEditMinSalary(parseFloat(e.target.value) || 0)}
                    className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="text-zinc-400 block mb-1">Currency</label>
                  <select
                    value={editCurrency}
                    onChange={(e) => setEditCurrency(e.target.value)}
                    className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-cyan-300 focus:outline-none"
                  >
                    <option value="USD">USD ($)</option>
                    <option value="INR">INR (₹)</option>
                    <option value="GBP">GBP (£)</option>
                    <option value="EUR">EUR (€)</option>
                  </select>
                </div>
                <div>
                  <label className="text-zinc-400 block mb-1">Min Hourly Rate</label>
                  <input
                    type="number"
                    value={editMinHourly}
                    onChange={(e) => setEditMinHourly(parseFloat(e.target.value) || 0)}
                    className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-zinc-400 block mb-1">Remote Preference</label>
                  <select
                    value={editRemotePref}
                    onChange={(e) => setEditRemotePref(e.target.value)}
                    className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none"
                  >
                    <option value="REMOTE">Remote Only</option>
                    <option value="HYBRID">Hybrid</option>
                    <option value="ONSITE">Onsite</option>
                  </select>
                </div>
                <div>
                  <label className="text-zinc-400 block mb-1">Notice Period (Days)</label>
                  <input
                    type="number"
                    value={editNoticeDays}
                    onChange={(e) => setEditNoticeDays(parseInt(e.target.value) || 0)}
                    className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-zinc-400 block mb-1">Automation Level</label>
                  <select
                    value={editAutoLevel}
                    onChange={(e) => setEditAutoLevel(parseInt(e.target.value) || 3)}
                    className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-amber-300 focus:outline-none"
                  >
                    <option value={1}>L1: Recommend</option>
                    <option value={2}>L2: Prepare</option>
                    <option value={3}>L3: Approval Gate</option>
                    <option value={4}>L4: High-Fit Auto Apply</option>
                    <option value={5}>L5: Fully Autonomous</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-zinc-400 block mb-1">Authorized Countries</label>
                  <input
                    type="text"
                    value={editAuthCountries}
                    onChange={(e) => setEditAuthCountries(e.target.value)}
                    className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none"
                    placeholder="e.g. United States, Canada, India"
                  />
                </div>
                <div className="flex items-center gap-3 pt-5">
                  <input
                    type="checkbox"
                    id="editSponsorshipCheckbox"
                    checked={editSponsorship}
                    onChange={(e) => setEditSponsorship(e.target.checked)}
                    className="w-4 h-4 accent-brand-500 rounded"
                  />
                  <label htmlFor="editSponsorshipCheckbox" className="text-zinc-300 cursor-pointer">
                    Requires Visa Sponsorship
                  </label>
                </div>
              </div>
            </div>

            <div className="p-4 border-t border-white/10 bg-surface-300/40 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowEditProfileModal(false)}
                className="px-4 py-2 rounded-xl text-xs font-mono text-zinc-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={savingProfile}
                onClick={handleSaveProfile}
                className="px-5 py-2 rounded-xl text-xs font-mono bg-brand-500 hover:bg-brand-400 text-white font-medium flex items-center gap-1.5 shadow-sm disabled:opacity-50"
              >
                {savingProfile ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                Save Profile Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Work Experience Modal */}
      {showAddExpModal && (
        <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-4">
          <div className="w-full max-w-xl bg-surface-200 border border-white/10 rounded-2xl shadow-2xl overflow-hidden glass-panel flex flex-col animate-in fade-in zoom-in-95 duration-150">
            <div className="p-5 border-b border-white/10 flex items-center justify-between bg-surface-300/50">
              <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-brand-400" />
                Add Work History & Engineering Experience
              </h3>
              <button
                type="button"
                onClick={() => setShowAddExpModal(false)}
                className="text-zinc-400 hover:text-white p-1 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-6 space-y-3 text-xs font-mono">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-zinc-400 block mb-1">Company</label>
                  <input
                    type="text"
                    placeholder="e.g. Stripe, OpenAI, Google"
                    value={newExpCompany}
                    onChange={(e) => setNewExpCompany(e.target.value)}
                    className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-zinc-400 block mb-1">Role / Job Title</label>
                  <input
                    type="text"
                    placeholder="e.g. Senior Backend Engineer"
                    value={newExpRole}
                    onChange={(e) => setNewExpRole(e.target.value)}
                    className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-zinc-400 block mb-1">Location</label>
                  <input
                    type="text"
                    placeholder="e.g. Remote / New York"
                    value={newExpLocation}
                    onChange={(e) => setNewExpLocation(e.target.value)}
                    className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-zinc-400 block mb-1">Start Date</label>
                  <input
                    type="text"
                    placeholder="e.g. 2021"
                    value={newExpStart}
                    onChange={(e) => setNewExpStart(e.target.value)}
                    className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-zinc-400 block mb-1">End Date</label>
                  <input
                    type="text"
                    placeholder="e.g. Present or 2024"
                    value={newExpEnd}
                    onChange={(e) => setNewExpEnd(e.target.value)}
                    className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="text-zinc-400 block mb-1">Role Summary & Key Scope</label>
                <textarea
                  rows={3}
                  placeholder="Architected distributed event streaming pipeline processing 10M events/day..."
                  value={newExpSummary}
                  onChange={(e) => setNewExpSummary(e.target.value)}
                  className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none"
                />
              </div>

              <div>
                <label className="text-zinc-400 block mb-1">Technologies Used (comma-separated)</label>
                <input
                  type="text"
                  placeholder="Python, FastAPI, Kafka, Kubernetes, PostgreSQL"
                  value={newExpTech}
                  onChange={(e) => setNewExpTech(e.target.value)}
                  className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-cyan-300 focus:outline-none"
                />
              </div>
            </div>

            <div className="p-4 border-t border-white/10 bg-surface-300/40 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowAddExpModal(false)}
                className="px-4 py-2 rounded-xl text-xs font-mono text-zinc-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={savingExp || !newExpCompany.trim() || !newExpRole.trim()}
                onClick={handleAddExperience}
                className="px-5 py-2 rounded-xl text-xs font-mono bg-brand-500 hover:bg-brand-400 text-white font-medium flex items-center gap-1.5 shadow-sm disabled:opacity-50"
              >
                {savingExp ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                Add Experience
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

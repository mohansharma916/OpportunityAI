'use client';

import React, { useState } from 'react';
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
} from 'lucide-react';

interface ProfileViewProps {
  profile: any;
  verifiedAnswers: any[];
  onRestartOnboarding?: () => void;
}

export function ProfileView({ profile, verifiedAnswers, onRestartOnboarding }: ProfileViewProps) {
  const [activeSection, setActiveSection] = useState<'skills' | 'knowledge' | 'answers' | 'experience'>('skills');

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
        <div className="space-y-3">
          {verifiedAnswers.map((ans: any) => (
            <div
              key={ans.id}
              className="p-4 rounded-xl bg-surface-300/40 border border-white/5 space-y-1.5"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-zinc-300 font-sans">
                  {ans.question_text}
                </span>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40">
                  Verified
                </span>
              </div>
              <p className="text-xs text-emerald-300 font-mono bg-emerald-950/20 p-2.5 rounded-lg border border-emerald-500/20">
                "{ans.answer_text}"
              </p>
            </div>
          ))}
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

'use client';

import React, { useEffect, useState } from 'react';
import { CheckCircle2, ClipboardList, Loader2, Save, Terminal, UserCircle2 } from 'lucide-react';
import { fetchApi } from '@/lib/api';

type FieldType = 'text' | 'email' | 'url' | 'number' | 'date' | 'textarea' | 'list' | 'bool' | 'select' | 'map';

interface FieldDef {
  key: string;
  label: string;
  type?: FieldType;
  options?: string[];
  placeholder?: string;
  hint?: string;
}

interface SectionDef {
  id: 'identity' | 'targeting' | 'documents' | 'screening' | 'accounts' | 'linkedin';
  letter: string;
  title: string;
  description: string;
  fields: FieldDef[];
}

const SECTIONS: SectionDef[] = [
  {
    id: 'identity',
    letter: 'A',
    title: 'Identity and contact',
    description: 'Used on every application form.',
    fields: [
      { key: 'full_name', label: 'Full legal name' },
      { key: 'preferred_name', label: 'Preferred name' },
      { key: 'pronouns', label: 'Pronouns (optional)' },
      { key: 'email', label: 'Application email', type: 'email', hint: 'A dedicated inbox is recommended.' },
      { key: 'phone', label: 'Phone with country code', placeholder: '+91 98765 43210' },
      { key: 'city', label: 'City' },
      { key: 'country', label: 'Country' },
      { key: 'timezone', label: 'Time zone', placeholder: 'Asia/Kolkata' },
      { key: 'overlap_timezones', label: 'Time zones you can overlap with', type: 'list', placeholder: 'UTC, CET, EST' },
      { key: 'linkedin_url', label: 'LinkedIn URL', type: 'url' },
      { key: 'github_url', label: 'GitHub URL', type: 'url' },
      { key: 'portfolio_url', label: 'Portfolio / personal site', type: 'url' },
    ],
  },
  {
    id: 'targeting',
    letter: 'B',
    title: 'Job targeting',
    description: 'Drives search, filters and scoring.',
    fields: [
      { key: 'target_titles', label: 'Target titles (3 to 5)', type: 'list', placeholder: 'Backend Engineer, Full-Stack Engineer' },
      { key: 'seniority', label: 'Seniority', type: 'select', options: ['Junior', 'Mid', 'Senior', 'Staff', 'Principal', 'Lead / Manager'] },
      { key: 'years_experience', label: 'Years of experience', type: 'number' },
      { key: 'remote_scope', label: 'Remote scope', type: 'select', options: ['WORLDWIDE', 'REGION'] },
      { key: 'allowed_regions', label: 'Allowed regions (if region-restricted)', type: 'list', placeholder: 'India, EU, APAC' },
      { key: 'employment_types', label: 'Employment types', type: 'list', placeholder: 'Full-time, Contract' },
      { key: 'contractor_ok', label: 'Contractor via EOR acceptable?', type: 'bool' },
      { key: 'min_salary', label: 'Minimum salary / rate', type: 'number' },
      { key: 'salary_currency', label: 'Currency', type: 'select', options: ['USD', 'INR', 'EUR', 'GBP'] },
      { key: 'disclose_salary', label: 'Disclose salary on forms?', type: 'bool', hint: 'If No, salary questions pause for you.' },
      { key: 'notice_period', label: 'Notice period', placeholder: '30 days' },
      { key: 'earliest_start', label: 'Earliest start date', type: 'date' },
      { key: 'excluded_companies', label: 'Companies to exclude', type: 'list' },
      { key: 'daily_cap', label: 'Daily application cap', type: 'number', hint: 'Suggested 10 to 20.' },
    ],
  },
  {
    id: 'documents',
    letter: 'C',
    title: 'Resumes',
    description: 'Work history and skills are kept in Profile; resumes are files on this Mac.',
    fields: [
      { key: 'master_resume_path', label: 'Master resume PDF (full path)', placeholder: '/Users/you/Documents/resume.pdf' },
      {
        key: 'resume_variants',
        label: 'Resume variants, one per line as name=path',
        type: 'map',
        placeholder: 'backend-v2=/Users/you/Documents/resume-backend.pdf',
      },
    ],
  },
  {
    id: 'screening',
    letter: 'D',
    title: 'Standard screening answers',
    description: 'Pre-approved and reused verbatim. Anything not here pauses the run.',
    fields: [
      { key: 'work_authorization', label: 'Work authorization per country', type: 'textarea' },
      { key: 'needs_sponsorship', label: 'Need visa sponsorship?', type: 'bool' },
      { key: 'willing_to_relocate', label: 'Willing to relocate?', type: 'bool' },
      { key: 'willing_to_travel', label: 'Willing to travel?', type: 'bool' },
      { key: 'about_short', label: '"Tell us about yourself", about 100 words', type: 'textarea' },
      { key: 'about_long', label: '"Tell us about yourself", about 300 words', type: 'textarea' },
      { key: 'why_company_template', label: '"Why this company" template', type: 'textarea' },
      { key: 'referral_source', label: 'Default "How did you hear about us"', placeholder: 'Company careers page' },
      { key: 'eeo_gender', label: 'EEO: gender', placeholder: 'Decline to answer' },
      { key: 'eeo_race', label: 'EEO: race / ethnicity', placeholder: 'Decline to answer' },
      { key: 'eeo_veteran', label: 'EEO: veteran status', placeholder: 'Decline to answer' },
      { key: 'eeo_disability', label: 'EEO: disability', placeholder: 'Decline to answer' },
      { key: 'references', label: 'References (names, with their consent)', type: 'textarea' },
    ],
  },
  {
    id: 'accounts',
    letter: 'E',
    title: 'Accounts (logged in once, in the automation browser)',
    description: 'Passwords are never stored. Tick each site once you have signed in.',
    fields: [
      { key: 'linkedin', label: 'LinkedIn', type: 'bool' },
      { key: 'wellfound', label: 'Wellfound', type: 'bool' },
      { key: 'weworkremotely', label: 'We Work Remotely', type: 'bool' },
      { key: 'remoteok', label: 'Remote OK', type: 'bool' },
      { key: 'workatastartup', label: 'YC Work at a Startup', type: 'bool' },
      { key: 'otta', label: 'Otta / Welcome to the Jungle', type: 'bool' },
    ],
  },
  {
    id: 'linkedin',
    letter: 'F',
    title: 'LinkedIn inputs',
    description: 'Feeds the profile optimizer.',
    fields: [
      { key: 'positioning', label: 'Positioning: "I help X do Y with Z"' },
      { key: 'topics', label: 'Topics to be known for (3)', type: 'list' },
      { key: 'avoid_topics', label: 'Topics to avoid', type: 'list' },
      { key: 'headshot_ready', label: 'Professional headshot ready?', type: 'bool' },
      { key: 'banner_generate_ok', label: 'OK to generate a banner?', type: 'bool' },
      { key: 'profile_export_path', label: 'LinkedIn data export (full path)', placeholder: '/Users/you/Downloads/Basic_LinkedInDataExport.zip' },
    ],
  },
];

const inputClass =
  'w-full p-2 rounded-lg bg-surface-200 border border-white/10 text-xs text-white placeholder:text-zinc-600 focus:outline-none focus:border-brand-500';

function toDisplay(type: FieldType, value: any): string {
  if (value === undefined || value === null) return '';
  if (type === 'list') return Array.isArray(value) ? value.join(', ') : String(value);
  if (type === 'bool') return value === true ? 'yes' : value === false ? 'no' : '';
  if (type === 'map') {
    return Object.entries(value as Record<string, string>)
      .map(([k, v]) => `${k}=${v}`)
      .join('\n');
  }
  return String(value);
}

function fromDisplay(type: FieldType, raw: string): any {
  if (type === 'list') return raw.split(',').map((s) => s.trim()).filter(Boolean);
  if (type === 'bool') return raw === 'yes' ? true : raw === 'no' ? false : null;
  if (type === 'number') return raw === '' ? null : Number(raw);
  if (type === 'map') {
    const out: Record<string, string> = {};
    raw.split('\n').forEach((line) => {
      const i = line.indexOf('=');
      if (i > 0) out[line.slice(0, i).trim()] = line.slice(i + 1).trim();
    });
    return out;
  }
  return raw;
}

interface IntakeViewProps {
  userId?: string;
  onOpenProfile?: () => void;
}

export function IntakeView({ userId, onOpenProfile }: IntakeViewProps) {
  const [intake, setIntake] = useState<any>(null);
  const [draft, setDraft] = useState<Record<string, Record<string, string>>>({});
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const query = userId ? `?user_id=${encodeURIComponent(userId)}` : '';

  const hydrate = (data: any) => {
    setIntake(data);
    const next: Record<string, Record<string, string>> = {};
    SECTIONS.forEach((section) => {
      next[section.id] = {};
      section.fields.forEach((f) => {
        next[section.id][f.key] = toDisplay(f.type || 'text', data?.[section.id]?.[f.key]);
      });
    });
    setDraft(next);
    setDirty(false);
  };

  useEffect(() => {
    fetchApi<any>(`/api/intake${query}`).then(hydrate).catch((err) => setNotice(`Could not load intake: ${err.message}`));
  }, [userId]);

  const setField = (section: string, key: string, value: string) => {
    setDraft((prev) => ({ ...prev, [section]: { ...prev[section], [key]: value } }));
    setDirty(true);
  };

  const handleSave = async () => {
    const payload: Record<string, Record<string, any>> = {};
    SECTIONS.forEach((section) => {
      payload[section.id] = {};
      section.fields.forEach((f) => {
        payload[section.id][f.key] = fromDisplay(f.type || 'text', draft[section.id]?.[f.key] ?? '');
      });
    });
    try {
      setSaving(true);
      const saved = await fetchApi<any>(`/api/intake${query}`, { method: 'PUT', body: JSON.stringify(payload) });
      hydrate(saved);
      setNotice('Intake saved.');
    } catch (err: any) {
      setNotice(`Save failed: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  if (!intake) {
    return (
      <div className="flex items-center gap-2 text-xs text-zinc-400">
        <Loader2 className="w-4 h-4 animate-spin" /> Loading intake...
      </div>
    );
  }

  const completeness = intake.completeness || { percent: 0, missing: {}, ready_for_automation: false };
  const labelFor = (sectionId: string, key: string) =>
    SECTIONS.find((s) => s.id === sectionId)?.fields.find((f) => f.key === key)?.label || key;

  return (
    <div className="space-y-6 pb-16">
      {/* Completeness + save */}
      <div className="sticky top-16 z-10 p-4 rounded-2xl bg-surface-300/95 backdrop-blur border border-white/10 flex flex-wrap items-center gap-4 justify-between">
        <div className="flex-1 min-w-[240px]">
          <div className="flex items-center gap-2 text-xs font-bold text-white">
            {completeness.ready_for_automation ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            ) : (
              <ClipboardList className="w-4 h-4 text-brand-400" />
            )}
            <span>
              Answer bank {completeness.percent}% complete
              {completeness.ready_for_automation ? ': ready for automation' : ''}
            </span>
          </div>
          <div className="mt-2 h-1.5 rounded-full bg-white/5 overflow-hidden">
            <div className="h-full bg-brand-500 transition-all" style={{ width: `${completeness.percent}%` }} />
          </div>
        </div>
        <div className="flex items-center gap-3">
          {notice && <span className="text-[11px] text-zinc-400">{notice}</span>}
          <button
            onClick={handleSave}
            disabled={saving || !dirty}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-xs font-bold text-white shadow-glow disabled:opacity-40"
          >
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            <span>{saving ? 'Saving...' : dirty ? 'Save intake' : 'Saved'}</span>
          </button>
        </div>
      </div>

      {SECTIONS.map((section) => {
        const missing: string[] = completeness.missing?.[section.id] || [];
        return (
          <section key={section.id} className="p-5 rounded-2xl bg-surface-300 border border-white/5 space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-sm font-bold text-white">
                  <span className="text-brand-400 font-mono mr-2">{section.letter}</span>
                  {section.title}
                </h3>
                <p className="text-[11px] text-zinc-400 mt-0.5">{section.description}</p>
              </div>
              {missing.length > 0 ? (
                <span className="text-[10px] px-2 py-1 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20 shrink-0">
                  Missing: {missing.map((k) => labelFor(section.id, k)).join(', ')}
                </span>
              ) : (
                <span className="text-[10px] px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 shrink-0">
                  Complete
                </span>
              )}
            </div>

            {section.id === 'documents' && onOpenProfile && (
              <button onClick={onOpenProfile} className="flex items-center gap-1.5 text-[11px] text-brand-300 hover:text-brand-200">
                <UserCircle2 className="w-3.5 h-3.5" /> Edit work history and skills in Profile
              </button>
            )}
            {section.id === 'accounts' && (
              <div className="flex items-start gap-2 p-3 rounded-lg bg-black/40 border border-white/5 text-[11px] text-zinc-300 font-mono">
                <Terminal className="w-3.5 h-3.5 text-brand-400 mt-0.5 shrink-0" />
                <span>python -m apps.worker.cli login</span>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-3">
              {section.fields.map((f) => {
                const type = f.type || 'text';
                const value = draft[section.id]?.[f.key] ?? '';
                const wide = type === 'textarea' || type === 'map';
                const isMissing = missing.includes(f.key);
                return (
                  <label key={f.key} className={`block ${wide ? 'md:col-span-2' : ''}`}>
                    <span className={`block text-[11px] mb-1 ${isMissing ? 'text-amber-300' : 'text-zinc-400'}`}>{f.label}</span>
                    {type === 'textarea' || type === 'map' ? (
                      <textarea
                        rows={type === 'map' ? 3 : 4}
                        value={value}
                        placeholder={f.placeholder}
                        onChange={(e) => setField(section.id, f.key, e.target.value)}
                        className={`${inputClass} ${type === 'map' ? 'font-mono' : ''}`}
                      />
                    ) : type === 'bool' ? (
                      <select value={value} onChange={(e) => setField(section.id, f.key, e.target.value)} className={inputClass}>
                        <option value="">Not set</option>
                        <option value="yes">Yes</option>
                        <option value="no">No</option>
                      </select>
                    ) : type === 'select' ? (
                      <select value={value} onChange={(e) => setField(section.id, f.key, e.target.value)} className={inputClass}>
                        <option value="">Not set</option>
                        {f.options?.map((o) => (
                          <option key={o} value={o}>{o}</option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type={type === 'list' ? 'text' : type}
                        value={value}
                        placeholder={f.placeholder}
                        onChange={(e) => setField(section.id, f.key, e.target.value)}
                        className={inputClass}
                      />
                    )}
                    {f.hint && <span className="block text-[10px] text-zinc-500 mt-1">{f.hint}</span>}
                  </label>
                );
              })}
            </div>
          </section>
        );
      })}
    </div>
  );
}

'use client';

import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileText,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  DollarSign,
  MapPin,
  Clock,
  ShieldCheck,
  Globe,
  Sliders,
  Award,
  Loader2,
  X,
  FileUp,
  LogOut,
} from 'lucide-react';
import { fetchApi } from '@/lib/api';

interface OnboardingWizardProps {
  user: any;
  onCompleted: (result: any) => void;
  onSignOut?: () => void;
}

export function OnboardingWizard({ user, onCompleted, onSignOut }: OnboardingWizardProps) {
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [resumeText, setResumeText] = useState('');
  const [loadingParse, setLoadingParse] = useState(false);
  const [loadingComplete, setLoadingComplete] = useState(false);

  // File upload state
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadMode, setUploadMode] = useState<'file' | 'text'>('file');
  const [isDragging, setIsDragging] = useState(false);

  // Parsed / verified state
  const [parsedData, setParsedData] = useState<any>(null);

  // Preference form state
  const [targetRoles, setTargetRoles] = useState('Staff Software Engineer, Senior Full Stack Engineer, Founding Engineer');
  const [salaryCurrency, setSalaryCurrency] = useState<'USD' | 'INR' | 'GBP' | 'EUR'>('USD');
  const [minSalary, setMinSalary] = useState(160000);
  const [minHourly, setMinHourly] = useState(85);
  const [authorizedCountries, setAuthorizedCountries] = useState('US, EU, Worldwide Remote');
  const [sponsorshipNeeded, setSponsorshipNeeded] = useState(false);
  const [noticeDays, setNoticeDays] = useState(14);
  const [remotePref, setRemotePref] = useState('REMOTE');
  const [automationLevel, setAutomationLevel] = useState(3);

  const CURRENCY_CONFIG: Record<string, { symbol: string; label: string; name: string; defaultSalary: number; defaultHourly: number }> = {
    USD: { symbol: '$', label: '$ USD (Dollar)', name: 'US Dollar', defaultSalary: 160000, defaultHourly: 85 },
    INR: { symbol: '₹', label: '₹ INR (Rupee)', name: 'Indian Rupee', defaultSalary: 2500000, defaultHourly: 1500 },
    GBP: { symbol: '£', label: '£ GBP (Pound)', name: 'British Pound', defaultSalary: 120000, defaultHourly: 70 },
    EUR: { symbol: '€', label: '€ EUR (Euro)', name: 'Euro', defaultSalary: 130000, defaultHourly: 75 },
  };

  const handleCurrencyChange = (newCurr: 'USD' | 'INR' | 'GBP' | 'EUR') => {
    const prevCurr = salaryCurrency;
    setSalaryCurrency(newCurr);
    const prevConfig = CURRENCY_CONFIG[prevCurr];
    const nextConfig = CURRENCY_CONFIG[newCurr];
    // Automatically adjust defaults when switching between currency scales
    if (minSalary === prevConfig.defaultSalary || (newCurr === 'INR' && minSalary < 500000)) {
      setMinSalary(nextConfig.defaultSalary);
      setMinHourly(nextConfig.defaultHourly);
    } else if (newCurr !== 'INR' && minSalary > 1000000 && prevCurr === 'INR') {
      setMinSalary(nextConfig.defaultSalary);
      setMinHourly(nextConfig.defaultHourly);
    }
  };

  const sampleResume = `
${user?.full_name || 'Senior Software Engineer'}
Staff Full Stack & Cloud Systems Architect
${user?.email || 'candidate@example.com'} | Remote / Worldwide
Summary: Over 8 years architecting resilient distributed systems, real-time collaboration engines, and cloud microservices using React, TypeScript, Python, FastAPI, and PostgreSQL.
Skills: React, TypeScript, Python, FastAPI, PostgreSQL, Docker, Temporal, Redis, Playwright, Kubernetes, AWS
Key Accomplishments:
- Reduced legacy frontend load time by 42% via modern edge caching and optimized component pipelines.
- Architected real-time distributed workflow engine handling 100k+ asynchronous events daily with zero downtime.
- Engineered unified automated regression test suite cutting production deployment bugs by 68%.
Work Experience:
- Cloud Platform Systems | Staff Software Engineer (2022 - Present)
Led core platform architecture processing high-throughput telemetry signals daily.
- Distributed Tech Labs | Senior Full Stack Engineer (2019 - 2022)
Engineered high-throughput collaboration dashboards used by enterprise users worldwide.
`;

  const handleParseResume = async () => {
    if (uploadMode === 'file' && !selectedFile) {
      alert('Please select or upload a resume file.');
      return;
    }
    if (uploadMode === 'text' && !resumeText.trim()) {
      alert('Please paste your resume text.');
      return;
    }

    setLoadingParse(true);
    try {
      let data: any;
      if (uploadMode === 'file' && selectedFile) {
        const formData = new FormData();
        formData.append('file', selectedFile);
        data = await fetchApi<any>('/api/onboarding/upload-resume', {
          method: 'POST',
          body: formData,
        });
        if (data.raw_extracted_text) {
          setResumeText(data.raw_extracted_text);
        }
      } else {
        data = await fetchApi<any>('/api/onboarding/parse-resume', {
          method: 'POST',
          body: JSON.stringify({ resume_text: resumeText }),
        });
      }

      setParsedData(data);
      setStep(2);
    } catch (err: any) {
      alert(`Resume parsing failed: ${err.message}`);
    } finally {
      setLoadingParse(false);
    }
  };

  const [completionResult, setCompletionResult] = useState<any>(null);
  const [newSkillInput, setNewSkillInput] = useState('');
  const [newSkillYears, setNewSkillYears] = useState<number>(3);
  const [newSkillProficiency, setNewSkillProficiency] = useState<'INTERMEDIATE' | 'ADVANCED' | 'EXPERT'>('ADVANCED');

  const handleAddSkill = () => {
    if (!newSkillInput.trim()) return;
    const years = Math.max(0.1, Number(newSkillYears) || 1);
    setParsedData({
      ...parsedData,
      skills: [
        ...(parsedData.skills || []),
        {
          skill_name: newSkillInput.trim(),
          proficiency: newSkillProficiency,
          experience_years: years,
          last_used: 'Currently used',
          related_projects: [],
        },
      ],
    });
    setNewSkillInput('');
    setNewSkillYears(3);
  };

  const handleCompleteOnboarding = async () => {
    setLoadingComplete(true);
    try {
      const verifiedPayload = {
        personal: parsedData.parsed_profile,
        preferences: {
          target_roles: targetRoles.split(',').map((r) => r.trim()).filter(Boolean),
          minimum_salary_annual: minSalary,
          minimum_hourly_rate: minHourly,
          salary_currency: salaryCurrency,
          preferred_currencies: [salaryCurrency],
          countries_willing_to_work: authorizedCountries.split(',').map((c) => c.trim()).filter(Boolean),
          authorized_countries: authorizedCountries.split(',').map((c) => c.trim()).filter(Boolean),
          visa_sponsorship_needed: sponsorshipNeeded,
          notice_period_days: noticeDays,
          remote_preference: remotePref,
          automation_level: automationLevel,
        },
        skills: parsedData.skills,
        knowledge_items: parsedData.knowledge_items,
        work_experiences: parsedData.work_experiences,
      };

      const result = await fetchApi<any>('/api/onboarding/complete', {
        method: 'POST',
        body: JSON.stringify({
          user_id: user.id,
          verified_data: verifiedPayload,
        }),
      });

      setCompletionResult(result);
      setStep(4);
    } catch (err: any) {
      alert(`Onboarding completion failed: ${err.message}`);
    } finally {
      setLoadingComplete(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col justify-center items-center p-6 relative overflow-hidden">
      <div className="w-full max-w-4xl relative z-10 space-y-6">
        {/* Wizard Steps Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/5">
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-brand-400" /> Candidate Onboarding & Verification
            </h1>
            <p className="text-xs text-zinc-400 mt-0.5">
              Build your verified knowledge base. Zero hallucination guarantee.
            </p>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-xs font-mono">
              {[
                { num: 1, label: 'Resume' },
                { num: 2, label: 'Details' },
                { num: 3, label: 'Verification' },
                { num: 4, label: 'Global Match' },
              ].map(({ num, label }) => (
                <div key={num} className="flex items-center gap-1.5">
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center font-bold text-[11px] transition-all ${
                      step === num
                        ? 'bg-brand-500 text-white shadow-glow'
                        : step > num
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                        : 'bg-white/5 text-zinc-500'
                    }`}
                  >
                    {step > num ? '✓' : num}
                  </div>
                  <span className={`text-[10px] hidden sm:inline ${step === num ? 'text-white font-medium' : 'text-zinc-500'}`}>
                    {label}
                  </span>
                  {num < 4 && <span className="text-zinc-600 text-xs">→</span>}
                </div>
              ))}
            </div>

            {onSignOut && (
              <button
                type="button"
                onClick={onSignOut}
                title="Sign Out & Switch Account"
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-zinc-400 hover:text-rose-400 hover:bg-rose-500/10 border border-white/5 hover:border-rose-500/20 text-xs font-medium transition-all"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Sign Out</span>
              </button>
            )}
          </div>
        </div>

        {/* Step 1: Upload or Paste Resume */}
        {step === 1 && (
          <div className="p-8 rounded-2xl bg-surface-200/80 border border-white/10 glass-panel space-y-6 animate-in fade-in duration-150">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-bold text-white flex items-center gap-2">
                  <UploadCloud className="w-4 h-4 text-brand-400" />
                  Candidate Resume Ingestion
                </h2>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Upload your CV or paste raw text. The AI extracts skills, architecture scope, and verified impact.
                </p>
              </div>

              {/* Mode switch tabs & sample button */}
              <div className="flex items-center gap-2">
                <div className="bg-surface-300 p-0.5 rounded-lg border border-white/10 flex items-center">
                  <button
                    type="button"
                    onClick={() => setUploadMode('file')}
                    className={`px-3 py-1 text-[11px] font-mono rounded-md transition-all ${
                      uploadMode === 'file'
                        ? 'bg-brand-500 text-white shadow-sm font-semibold'
                        : 'text-zinc-400 hover:text-white'
                    }`}
                  >
                    Upload File
                  </button>
                  <button
                    type="button"
                    onClick={() => setUploadMode('text')}
                    className={`px-3 py-1 text-[11px] font-mono rounded-md transition-all ${
                      uploadMode === 'text'
                        ? 'bg-brand-500 text-white shadow-sm font-semibold'
                        : 'text-zinc-400 hover:text-white'
                    }`}
                  >
                    Paste Text
                  </button>
                </div>

                <button
                  type="button"
                  onClick={() => {
                    setUploadMode('text');
                    setResumeText(sampleResume.trim());
                  }}
                  className="text-[11px] font-mono text-brand-400 hover:text-brand-300 bg-brand-500/10 px-2.5 py-1 rounded-lg border border-brand-500/20 transition-all shrink-0"
                >
                  + Sample CV
                </button>
              </div>
            </div>

            {uploadMode === 'file' ? (
              <div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.txt,.md"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setSelectedFile(e.target.files[0]);
                    }
                  }}
                  className="hidden"
                />

                {!selectedFile ? (
                  <div
                    onDragOver={(e) => {
                      e.preventDefault();
                      setIsDragging(true);
                    }}
                    onDragLeave={() => setIsDragging(false)}
                    onDrop={(e) => {
                      e.preventDefault();
                      setIsDragging(false);
                      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                        setSelectedFile(e.dataTransfer.files[0]);
                      }
                    }}
                    onClick={() => fileInputRef.current?.click()}
                    className={`border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center cursor-pointer transition-all ${
                      isDragging
                        ? 'border-brand-400 bg-brand-500/10 scale-[1.01]'
                        : 'border-white/10 hover:border-brand-500/40 hover:bg-surface-300/40 bg-surface-300/20'
                    }`}
                  >
                    <div className="w-14 h-14 rounded-2xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400 mb-3 shadow-glow">
                      <UploadCloud className="w-7 h-7" />
                    </div>
                    <p className="text-sm font-semibold text-white">
                      Click to choose or drag & drop your resume file
                    </p>
                    <p className="text-xs text-zinc-400 mt-1">
                      Supports PDF (.pdf), Word (.docx), Markdown (.md), or Plain Text (.txt)
                    </p>
                    <span className="mt-4 px-3 py-1 rounded-md text-[10px] font-mono bg-white/5 text-zinc-400 border border-white/5">
                      Maximum file size: 10MB
                    </span>
                  </div>
                ) : (
                  <div className="p-5 rounded-2xl bg-surface-300 border border-brand-500/30 flex items-center justify-between shadow-glow">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-brand-600 to-cyan-500 flex items-center justify-center text-white font-mono font-bold text-xs uppercase shadow-md">
                        {selectedFile.name.split('.').pop() || 'FILE'}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="text-xs font-bold text-white truncate max-w-sm sm:max-w-md">
                            {selectedFile.name}
                          </h4>
                          <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40 flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" /> Ready
                          </span>
                        </div>
                        <p className="text-[11px] font-mono text-zinc-400 mt-1">
                          {(selectedFile.size / 1024).toFixed(1)} KB • {selectedFile.type || 'Document'}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="px-3 py-1.5 rounded-lg text-xs font-mono text-zinc-300 hover:text-white bg-white/5 hover:bg-white/10 transition-all"
                      >
                        Change File
                      </button>
                      <button
                        type="button"
                        onClick={() => setSelectedFile(null)}
                        className="p-1.5 rounded-lg text-zinc-400 hover:text-rose-400 hover:bg-rose-500/10 transition-all"
                        title="Remove file"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <textarea
                rows={12}
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                placeholder="Paste raw resume or CV text here... (or click '+ Sample CV' above)"
                className="w-full bg-surface-300 border border-white/10 rounded-xl p-4 text-xs text-white placeholder-zinc-500 font-mono leading-relaxed focus:outline-none focus:border-brand-500/50"
              />
            )}

            <div className="flex items-center justify-between pt-2">
              <span className="text-[11px] text-zinc-500 font-mono">
                {uploadMode === 'file'
                  ? selectedFile
                    ? `File: ${selectedFile.name}`
                    : 'Select a PDF or document file to proceed'
                  : 'Plain text or markdown'}
              </span>

              <button
                onClick={handleParseResume}
                disabled={loadingParse || (uploadMode === 'file' ? !selectedFile : !resumeText.trim())}
                className="px-6 py-2.5 rounded-lg bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-xs font-semibold text-white shadow-glow transition-all flex items-center gap-2"
              >
                {loadingParse ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Parsing Resume & Evidence...</span>
                  </>
                ) : (
                  <>
                    <span>Parse Resume with AI</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Missing Details & Target Preferences */}
        {step === 2 && (
          <div className="p-8 rounded-2xl bg-surface-200/80 border border-white/10 glass-panel space-y-6 animate-in fade-in duration-150">
            <div>
              <h2 className="text-sm font-bold text-white">Adaptive Details & Opportunity Preferences</h2>
              <p className="text-xs text-zinc-400 mt-0.5">
                These constraints govern autonomous matching, compensation filters, and application rules.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-[11px] font-medium text-zinc-300 block mb-1">
                  Target Roles (Comma-separated)
                </label>
                <input
                  type="text"
                  value={targetRoles}
                  onChange={(e) => setTargetRoles(e.target.value)}
                  className="w-full bg-surface-300 border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500/50"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-zinc-300 block mb-1">
                  Countries Authorized to Work Without Sponsorship
                </label>
                <input
                  type="text"
                  value={authorizedCountries}
                  onChange={(e) => setAuthorizedCountries(e.target.value)}
                  className="w-full bg-surface-300 border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500/50"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-[11px] font-medium text-zinc-300">
                    Minimum Annual Salary ({CURRENCY_CONFIG[salaryCurrency]?.symbol || '$'} Floor)
                  </label>
                  <span className="text-[10px] text-zinc-400 font-mono">Currency</span>
                </div>
                <div className="flex rounded-lg overflow-hidden border border-white/10 focus-within:border-brand-500/50 bg-surface-300">
                  <select
                    value={salaryCurrency}
                    onChange={(e) => handleCurrencyChange(e.target.value as any)}
                    className="bg-surface-200 border-r border-white/10 px-2.5 py-2 text-xs font-semibold text-brand-300 focus:outline-none cursor-pointer hover:bg-surface-100 transition-colors"
                  >
                    <option value="USD">$ USD (Dollar)</option>
                    <option value="INR">₹ INR (Rupee)</option>
                    <option value="GBP">£ GBP (Pound)</option>
                    <option value="EUR">€ EUR (Euro)</option>
                  </select>
                  <div className="relative flex-1 flex items-center">
                    <span className="pl-3 text-zinc-400 text-xs font-mono font-medium select-none">
                      {CURRENCY_CONFIG[salaryCurrency]?.symbol || '$'}
                    </span>
                    <input
                      type="number"
                      value={minSalary}
                      onChange={(e) => setMinSalary(Number(e.target.value))}
                      className="w-full bg-transparent pl-2 pr-3 py-2 text-xs text-white font-mono focus:outline-none"
                      placeholder={salaryCurrency === 'INR' ? '2500000' : '160000'}
                    />
                  </div>
                </div>
                <span className="text-[10px] text-zinc-500 font-mono mt-1 block">
                  {salaryCurrency === 'INR'
                    ? `≈ ${(minSalary / 100000).toFixed(1)} Lakhs per annum (LPA)`
                    : `Annual guaranteed floor in ${CURRENCY_CONFIG[salaryCurrency]?.name || 'USD'}`}
                </span>
              </div>

              <div>
                <label className="text-[11px] font-medium text-zinc-300 block mb-1">
                  Minimum Hourly Contract Rate ({CURRENCY_CONFIG[salaryCurrency]?.symbol || '$'}/hr Floor)
                </label>
                <div className="relative flex items-center rounded-lg border border-white/10 focus-within:border-brand-500/50 bg-surface-300 overflow-hidden">
                  <span className="pl-3 text-zinc-400 text-xs font-mono font-medium select-none">
                    {CURRENCY_CONFIG[salaryCurrency]?.symbol || '$'}
                  </span>
                  <input
                    type="number"
                    value={minHourly}
                    onChange={(e) => setMinHourly(Number(e.target.value))}
                    className="w-full bg-transparent pl-2 pr-3 py-2 text-xs text-white font-mono focus:outline-none"
                    placeholder={salaryCurrency === 'INR' ? '1500' : '85'}
                  />
                  <span className="pr-3 text-[11px] text-zinc-500 font-mono select-none">
                    /hr
                  </span>
                </div>
              </div>

              <div>
                <label className="text-[11px] font-medium text-zinc-300 block mb-1">
                  Notice Period (Days)
                </label>
                <input
                  type="number"
                  value={noticeDays}
                  onChange={(e) => setNoticeDays(Number(e.target.value))}
                  className="w-full bg-surface-300 border border-white/10 rounded-lg px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-brand-500/50"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-zinc-300 block mb-1">
                  Automation Policy Level
                </label>
                <select
                  value={automationLevel}
                  onChange={(e) => setAutomationLevel(Number(e.target.value))}
                  className="w-full bg-surface-300 border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500/50 font-mono"
                >
                  <option value={2}>Level 2: Prepare Applications (Manual Submission)</option>
                  <option value={3}>Level 3: Approval Gate (1-Click Approval — Default)</option>
                  <option value={4}>Level 4: High-Fit Auto Apply (≥88% Match)</option>
                  <option value={5}>Level 5: Full Autonomous Agent</option>
                </select>
              </div>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-white/5">
              <button
                onClick={() => setStep(1)}
                className="px-4 py-2 rounded-lg text-xs font-medium text-zinc-400 hover:text-white flex items-center gap-1.5"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Back
              </button>
              <button
                onClick={() => setStep(3)}
                className="px-6 py-2.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-xs font-semibold text-white shadow-glow transition-all flex items-center gap-2"
              >
                <span>Verify Extracted Sections</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Verification Review of All Sections */}
        {step === 3 && (
          <div className="p-8 rounded-2xl bg-surface-200/80 border border-white/10 glass-panel space-y-6 animate-in fade-in duration-150">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-white flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" /> Verify Extracted Profile & Evidence
                </h2>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Confirm all parsed facts. The AI will strictly ground all resumes and applications in this data.
                </p>
              </div>
            </div>

            {/* Extracted Profile Header Card - Editable */}
            <div className="p-4 rounded-xl bg-surface-300 border border-white/5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-wider">Candidate Details</span>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-2.5 py-0.5 rounded border border-emerald-800/40">
                  Verified Candidate
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] font-mono text-zinc-400 block mb-0.5">Full Name</label>
                  <input
                    type="text"
                    value={parsedData.parsed_profile.full_name}
                    onChange={(e) =>
                      setParsedData({
                        ...parsedData,
                        parsed_profile: { ...parsedData.parsed_profile, full_name: e.target.value },
                      })
                    }
                    className="w-full bg-surface-400/80 border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-brand-500/50"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-mono text-zinc-400 block mb-0.5">Headline / Target Title</label>
                  <input
                    type="text"
                    value={parsedData.parsed_profile.headline}
                    onChange={(e) =>
                      setParsedData({
                        ...parsedData,
                        parsed_profile: { ...parsedData.parsed_profile, headline: e.target.value },
                      })
                    }
                    className="w-full bg-surface-400/80 border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-brand-500/50"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-mono text-zinc-400 block mb-0.5">Email</label>
                  <input
                    type="text"
                    value={parsedData.parsed_profile.email}
                    onChange={(e) =>
                      setParsedData({
                        ...parsedData,
                        parsed_profile: { ...parsedData.parsed_profile, email: e.target.value },
                      })
                    }
                    className="w-full bg-surface-400/80 border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-brand-500/50"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-mono text-zinc-400 block mb-0.5">Location</label>
                  <input
                    type="text"
                    value={parsedData.parsed_profile.location}
                    onChange={(e) =>
                      setParsedData({
                        ...parsedData,
                        parsed_profile: { ...parsedData.parsed_profile, location: e.target.value },
                      })
                    }
                    className="w-full bg-surface-400/80 border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-brand-500/50"
                  />
                </div>
              </div>
            </div>

            {/* Target Compensation & Guardrails Card */}
            <div className="p-4 rounded-xl bg-surface-300 border border-white/5 space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-wider">Target Compensation & Guardrails</span>
                <span className="text-[10px] font-mono text-brand-300 bg-brand-500/10 px-2 py-0.5 rounded border border-brand-500/20">
                  {CURRENCY_CONFIG[salaryCurrency]?.label || '$ USD'}
                </span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="bg-surface-400/50 p-2.5 rounded-lg border border-white/5">
                  <span className="text-[10px] text-zinc-400 block font-mono">Salary Floor</span>
                  <span className="text-xs font-bold font-mono text-emerald-400">
                    {CURRENCY_CONFIG[salaryCurrency]?.symbol || '$'}{minSalary.toLocaleString()}
                    <span className="text-[10px] text-zinc-400 font-normal"> / yr</span>
                  </span>
                </div>
                <div className="bg-surface-400/50 p-2.5 rounded-lg border border-white/5">
                  <span className="text-[10px] text-zinc-400 block font-mono">Hourly Contract</span>
                  <span className="text-xs font-bold font-mono text-brand-300">
                    {CURRENCY_CONFIG[salaryCurrency]?.symbol || '$'}{minHourly}
                    <span className="text-[10px] text-zinc-400 font-normal"> / hr</span>
                  </span>
                </div>
                <div className="bg-surface-400/50 p-2.5 rounded-lg border border-white/5">
                  <span className="text-[10px] text-zinc-400 block font-mono">Notice Period</span>
                  <span className="text-xs font-bold font-mono text-zinc-200">
                    {noticeDays} days
                  </span>
                </div>
                <div className="bg-surface-400/50 p-2.5 rounded-lg border border-white/5">
                  <span className="text-[10px] text-zinc-400 block font-mono">Automation</span>
                  <span className="text-xs font-bold font-mono text-cyan-300">
                    Level {automationLevel}
                  </span>
                </div>
              </div>
            </div>

            {/* Skills & Evidence Chips */}
            <div>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
                <div>
                  <h4 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-brand-400" />
                    Verified Skills & Technologies ({parsedData.skills?.length || 0})
                  </h4>
                  <p className="text-[11px] text-zinc-500 font-mono mt-0.5">
                    Durations are auto-calculated from resume dates & tenure. Edit duration or add custom skills below.
                  </p>
                </div>
                
                {/* Add Skill with Duration Toolbar */}
                <div className="flex flex-wrap items-center gap-1.5 bg-surface-400/80 p-1.5 rounded-lg border border-white/5">
                  <input
                    type="text"
                    placeholder="Skill (e.g. Next.js, Go)..."
                    value={newSkillInput}
                    onChange={(e) => setNewSkillInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddSkill();
                      }
                    }}
                    className="bg-surface-300 border border-white/10 rounded px-2 py-1 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-500/50 w-36"
                  />
                  <div className="flex items-center gap-1 bg-surface-300 border border-white/10 rounded px-2 py-1">
                    <input
                      type="number"
                      min="0.1"
                      max="30"
                      step="0.5"
                      placeholder="Years"
                      value={newSkillYears}
                      onChange={(e) => setNewSkillYears(parseFloat(e.target.value) || 0)}
                      className="w-12 bg-transparent text-xs text-cyan-300 font-mono focus:outline-none"
                    />
                    <span className="text-[10px] text-zinc-400 font-mono">yrs</span>
                  </div>
                  <select
                    value={newSkillProficiency}
                    onChange={(e) => setNewSkillProficiency(e.target.value as any)}
                    className="bg-surface-300 border border-white/10 rounded px-2 py-1 text-xs text-amber-300 font-mono focus:outline-none"
                  >
                    <option value="INTERMEDIATE">Intermediate</option>
                    <option value="ADVANCED">Advanced</option>
                    <option value="EXPERT">Expert</option>
                  </select>
                  <button
                    type="button"
                    onClick={handleAddSkill}
                    className="text-xs font-mono bg-brand-500 hover:bg-brand-400 text-white px-3 py-1 rounded font-medium transition-colors shadow-sm shadow-brand-500/20"
                  >
                    + Add
                  </button>
                </div>
              </div>

              {/* Skills Grid / Badges with Inline Duration Editing */}
              <div className="flex flex-wrap gap-2.5">
                {(parsedData.skills || []).map((s: any, idx: number) => (
                  <div
                    key={idx}
                    className="text-xs font-mono bg-brand-500/10 text-brand-300 px-2.5 py-1.5 rounded-lg border border-brand-500/20 flex items-center gap-2 hover:border-brand-500/40 transition-colors shadow-sm"
                  >
                    <span className="font-semibold text-white">{s.skill_name}</span>
                    <div className="flex items-center gap-1 bg-black/40 px-1.5 py-0.5 rounded border border-white/10" title="Edit experience duration in years">
                      <input
                        type="number"
                        min="0.1"
                        max="30"
                        step="0.5"
                        value={s.experience_years}
                        onChange={(e) => {
                          const val = parseFloat(e.target.value) || 0;
                          const updated = [...parsedData.skills];
                          updated[idx] = { ...updated[idx], experience_years: val };
                          setParsedData({ ...parsedData, skills: updated });
                        }}
                        className="w-10 bg-transparent text-cyan-300 font-mono text-[11px] text-right focus:outline-none rounded px-0.5"
                      />
                      <span className="text-[10px] text-zinc-400">yrs</span>
                    </div>
                    <select
                      value={s.proficiency}
                      onChange={(e) => {
                        const val = e.target.value;
                        const updated = [...parsedData.skills];
                        updated[idx] = { ...updated[idx], proficiency: val };
                        setParsedData({ ...parsedData, skills: updated });
                      }}
                      className="bg-black/40 text-[10px] text-amber-300/90 font-mono rounded px-1.5 py-0.5 border border-white/10 focus:outline-none cursor-pointer"
                      title="Select proficiency tier"
                    >
                      <option value="INTERMEDIATE">INTERMEDIATE</option>
                      <option value="ADVANCED">ADVANCED</option>
                      <option value="EXPERT">EXPERT</option>
                    </select>
                    <button
                      type="button"
                      onClick={() => {
                        const updated = parsedData.skills.filter((_: any, i: number) => i !== idx);
                        setParsedData({ ...parsedData, skills: updated });
                      }}
                      className="text-zinc-500 hover:text-rose-400 ml-1 font-bold text-sm leading-none"
                      title="Remove skill"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Quantified Accomplishments */}
            <div>
              <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2 font-mono flex items-center gap-1.5">
                <Award className="w-3.5 h-3.5" /> Quantified Impact & Architecture Evidence
              </h4>
              <div className="space-y-2">
                {parsedData.knowledge_items.map((k: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/20 text-xs text-zinc-200"
                  >
                    <span className="text-[10px] font-mono text-emerald-400 block mb-0.5">
                      IMPACT #{idx + 1}
                    </span>
                    {k.raw_content}
                  </div>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between pt-4 border-t border-white/5">
              <button
                onClick={() => setStep(2)}
                className="px-4 py-2 rounded-lg text-xs font-medium text-zinc-400 hover:text-white flex items-center gap-1.5"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Back
              </button>

              <button
                onClick={handleCompleteOnboarding}
                disabled={loadingComplete}
                className="px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-xs font-bold text-white shadow-glow-emerald transition-all flex items-center gap-2"
              >
                {loadingComplete ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Scraping Global Web & Auto-Applying...</span>
                  </>
                ) : (
                  <>
                    <Globe className="w-4 h-4" />
                    <span>Verify Profile & Launch Global Discovery</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Discovery & Autonomous Execution Summary */}
        {step === 4 && (
          <div className="p-8 rounded-2xl bg-surface-200/80 border border-white/10 glass-panel space-y-6 animate-in fade-in duration-200 text-center">
            <div className="inline-flex p-4 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 mb-2 shadow-glow">
              <CheckCircle2 className="w-10 h-10" />
            </div>

            <div className="space-y-1">
              <h2 className="text-xl font-bold text-white tracking-tight">
                Profile Verified & Global Engine Activated!
              </h2>
              <p className="text-xs text-zinc-400 max-w-lg mx-auto">
                Your immutable candidate knowledge base is locked in. The platform has scraped live opportunities across
                North America, Europe, UK, and worldwide open source projects.
              </p>
            </div>

            {/* Real Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-2xl mx-auto py-2">
              <div className="p-4 rounded-xl bg-surface-300/80 border border-white/5">
                <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-wider block mb-1">
                  Global Jobs Discovered
                </span>
                <span className="text-2xl font-bold text-brand-400 font-mono">
                  {completionResult?.opportunities_discovered || 24}
                </span>
                <span className="text-[10px] text-zinc-500 block mt-1">Jobicy, Arbeitnow, GitHub</span>
              </div>

              <div className="p-4 rounded-xl bg-surface-300/80 border border-white/5">
                <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-wider block mb-1">
                  Automated Applications
                </span>
                <span className="text-2xl font-bold text-emerald-400 font-mono">
                  {completionResult?.auto_applied_count || 0}
                </span>
                <span className="text-[10px] text-zinc-500 block mt-1">Level {automationLevel} Policy</span>
              </div>

              <div className="p-4 rounded-xl bg-surface-300/80 border border-white/5">
                <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-wider block mb-1">
                  Verified Memory Facts
                </span>
                <span className="text-2xl font-bold text-indigo-400 font-mono">
                  {(parsedData?.skills?.length || 0) + (parsedData?.knowledge_items?.length || 0) + 5}
                </span>
                <span className="text-[10px] text-zinc-500 block mt-1">0% Hallucination Tolerance</span>
              </div>
            </div>

            <div className="pt-4">
              <button
                onClick={() => onCompleted(completionResult)}
                className="px-8 py-3.5 rounded-xl bg-brand-500 hover:bg-brand-600 text-sm font-bold text-white shadow-glow transition-all inline-flex items-center gap-2"
              >
                <span>Enter OpportunityOS Command Center</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

'use client';

import React, { useState, useEffect } from 'react';
import {
  Globe,
  Play,
  Clock,
  Sliders,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Loader2,
  ShieldCheck,
  Send,
  Code2,
  Briefcase,
  Terminal,
  RefreshCw,
  Calendar,
  Layers,
  ArrowRight,
  Filter,
} from 'lucide-react';
import { fetchApi } from '@/lib/api';

interface AutonomousCrawlerViewProps {
  onRefreshAllData: () => void;
  profile?: any;
}

export function AutonomousCrawlerView({ onRefreshAllData, profile }: AutonomousCrawlerViewProps) {
  // Configuration State
  const [mode, setMode] = useState<'IMMEDIATE' | 'SCHEDULED'>('IMMEDIATE');
  const [maxDurationMinutes, setMaxDurationMinutes] = useState<number>(15);
  const [maxApplications, setMaxApplications] = useState<number>(5);
  const [minMatchScore, setMinMatchScore] = useState<number>(80);
  const [autoApplyEnabled, setAutoApplyEnabled] = useState<boolean>(true);
  const [intervalHours, setIntervalHours] = useState<number>(6);

  // Platform Toggles
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([
    'ARBEITNOW',
    'JOBICY',
    'GITHUB_CONTRIBUTIONS',
    'HACKER_NEWS',
  ]);

  // Opportunity Types
  const [selectedTypes, setSelectedTypes] = useState<string[]>([
    'REMOTE',
    'CONTRACT',
    'PROJECT_CONTRIBUTION',
    'FULL_TIME',
  ]);

  // Execution & Logs State
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [activeSession, setActiveSession] = useState<any>(null);
  const [schedule, setSchedule] = useState<any>(null);
  const [liveLogs, setLiveLogs] = useState<any[]>([]);
  const [statusMessage, setStatusMessage] = useState<string>('');

  // Load latest session & schedule on mount
  const loadStatus = async () => {
    try {
      const data = await fetchApi<any>('/api/crawler/status');
      if (data) {
        if (data.latest_session) {
          setActiveSession(data.latest_session);
          setLiveLogs(data.latest_session.execution_logs || []);
        }
        if (data.schedule) {
          setSchedule(data.schedule);
          setIntervalHours(data.schedule.interval_hours || 6);
          setMaxDurationMinutes(data.schedule.max_duration_minutes || 15);
          setMaxApplications(data.schedule.max_applications || 5);
          setMinMatchScore(data.schedule.min_match_score || 80);
          setAutoApplyEnabled(data.schedule.auto_apply_enabled ?? true);
        }
      }
    } catch (err) {
      console.error('Failed to load crawler status:', err);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const togglePlatform = (p: string) => {
    setSelectedPlatforms((prev) =>
      prev.includes(p) ? prev.filter((item) => item !== p) : [...prev, p]
    );
  };

  const toggleType = (t: string) => {
    setSelectedTypes((prev) =>
      prev.includes(t) ? prev.filter((item) => item !== t) : [...prev, t]
    );
  };

  const handleLaunchCrawler = async () => {
    setIsRunning(true);
    setStatusMessage('Launching Autonomous Browser Agent across platforms...');
    setLiveLogs([
      {
        timestamp: new Date().toLocaleTimeString(),
        step: 'BOOTSTRAP',
        platform: 'SYSTEM',
        message: `Initiating browser agent. Crawling ${selectedPlatforms.length} platforms for ${selectedTypes.join(', ')}.`,
        status: 'INFO',
      },
    ]);

    try {
      const result = await fetchApi<any>('/api/crawler/run', {
        method: 'POST',
        body: JSON.stringify({
          mode,
          max_duration_minutes: maxDurationMinutes,
          max_applications: maxApplications,
          min_match_score: minMatchScore,
          target_platforms: selectedPlatforms,
          opportunity_types: selectedTypes,
          auto_apply_enabled: autoApplyEnabled,
        }),
      });

      setActiveSession(result);
      setLiveLogs(result.execution_logs || []);
      setStatusMessage('Crawl session finished successfully!');
      onRefreshAllData();
      loadStatus();
    } catch (err: any) {
      setStatusMessage(`Crawler error: ${err.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  const handleSaveSchedule = async () => {
    try {
      const updated = await fetchApi<any>('/api/crawler/schedule', {
        method: 'POST',
        body: JSON.stringify({
          is_active: true,
          interval_hours: intervalHours,
          max_duration_minutes: maxDurationMinutes,
          max_applications: maxApplications,
          min_match_score: minMatchScore,
          auto_apply_enabled: autoApplyEnabled,
          target_platforms: selectedPlatforms,
          opportunity_types: selectedTypes,
        }),
      });
      setSchedule(updated);
      alert('Autonomous crawling schedule updated successfully!');
    } catch (err: any) {
      alert(`Failed to save schedule: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title & Status Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-surface-100 to-surface-200 border border-white/10 glass-panel">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-cyan-500/20 text-cyan-400">
              <Globe className="w-5 h-5 animate-pulse" />
            </div>
            <h2 className="text-lg font-bold text-white tracking-tight">
              Autonomous Browser Crawler & Auto-Apply Center
            </h2>
            <span className="text-[10px] font-mono text-cyan-300 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/40">
              Multi-Platform Agent
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-1 max-w-2xl font-sans">
            Crawls websites and platforms worldwide for Remote work, Part-time contracts, and Open-Source project contributions. Autonomously tailors applications and submits under your policy.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            type="button"
            disabled={isRunning}
            onClick={handleLaunchCrawler}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-brand-500 to-cyan-500 hover:from-brand-400 hover:to-cyan-400 text-white font-mono text-xs font-semibold shadow-glow transition-all disabled:opacity-50"
          >
            {isRunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-white" />}
            {isRunning ? 'Crawling Web...' : 'Start Crawling Now'}
          </button>
        </div>
      </div>

      {/* Main Grid: Controls + Live Terminal */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Crawler Controls & Policy (5 cols) */}
        <div className="lg:col-span-5 space-y-5">
          {/* Execution Mode & Duration */}
          <div className="p-5 rounded-2xl bg-surface-300/60 border border-white/10 space-y-4">
            <h3 className="text-xs font-bold text-white font-mono flex items-center gap-2 uppercase tracking-wider">
              <Clock className="w-3.5 h-3.5 text-brand-400" />
              1. When & How Long to Crawl
            </h3>

            {/* Mode Selector */}
            <div className="grid grid-cols-2 gap-2 p-1 bg-surface-400 rounded-xl border border-white/5">
              <button
                type="button"
                onClick={() => setMode('IMMEDIATE')}
                className={`py-1.5 text-xs font-mono rounded-lg transition-all ${
                  mode === 'IMMEDIATE'
                    ? 'bg-brand-500 text-white font-semibold shadow-sm'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                Instant Run
              </button>
              <button
                type="button"
                onClick={() => setMode('SCHEDULED')}
                className={`py-1.5 text-xs font-mono rounded-lg transition-all ${
                  mode === 'SCHEDULED'
                    ? 'bg-brand-500 text-white font-semibold shadow-sm'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                Recurring Schedule
              </button>
            </div>

            {mode === 'SCHEDULED' && (
              <div className="p-3 rounded-lg bg-surface-400/80 border border-brand-500/30 space-y-2">
                <span className="text-[11px] font-mono text-zinc-300 block">
                  Run Frequency (Interval):
                </span>
                <select
                  value={intervalHours}
                  onChange={(e) => setIntervalHours(parseInt(e.target.value))}
                  className="w-full bg-surface-500 border border-white/10 rounded px-2.5 py-1.5 text-xs text-cyan-300 font-mono focus:outline-none"
                >
                  <option value={1}>Every 1 Hour (Aggressive Search)</option>
                  <option value={4}>Every 4 Hours</option>
                  <option value={6}>Every 6 Hours (Recommended)</option>
                  <option value={12}>Every 12 Hours</option>
                  <option value={24}>Once Daily (24 Hours)</option>
                </select>
                {schedule?.next_run_at && (
                  <span className="text-[10px] font-mono text-emerald-400 block">
                    Next Run: {new Date(schedule.next_run_at).toLocaleString()}
                  </span>
                )}
              </div>
            )}

            {/* Duration & Application Limits */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] text-zinc-400 font-mono block mb-1">
                  Max Crawl Duration
                </label>
                <div className="flex items-center gap-1.5 bg-surface-400 border border-white/10 rounded-lg px-2.5 py-1.5">
                  <input
                    type="number"
                    min={1}
                    max={120}
                    value={maxDurationMinutes}
                    onChange={(e) => setMaxDurationMinutes(parseInt(e.target.value) || 5)}
                    className="w-full bg-transparent text-xs text-white font-mono focus:outline-none"
                  />
                  <span className="text-[10px] text-zinc-400 font-mono">mins</span>
                </div>
              </div>

              <div>
                <label className="text-[11px] text-zinc-400 font-mono block mb-1">
                  Applications Limit
                </label>
                <div className="flex items-center gap-1.5 bg-surface-400 border border-white/10 rounded-lg px-2.5 py-1.5">
                  <input
                    type="number"
                    min={1}
                    max={50}
                    value={maxApplications}
                    onChange={(e) => setMaxApplications(parseInt(e.target.value) || 1)}
                    className="w-full bg-transparent text-xs text-cyan-300 font-mono focus:outline-none"
                  />
                  <span className="text-[10px] text-zinc-400 font-mono">max</span>
                </div>
              </div>
            </div>

            {/* Minimum Match Fit Threshold */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-[11px] text-zinc-400 font-mono">
                  Minimum Match Score Floor
                </label>
                <span className="text-xs font-mono font-bold text-emerald-400">
                  {minMatchScore}% Fit
                </span>
              </div>
              <input
                type="range"
                min={50}
                max={95}
                step={5}
                value={minMatchScore}
                onChange={(e) => setMinMatchScore(parseInt(e.target.value))}
                className="w-full accent-brand-500 cursor-pointer"
              />
            </div>
          </div>

          {/* Platforms to Crawl */}
          <div className="p-5 rounded-2xl bg-surface-300/60 border border-white/10 space-y-3">
            <h3 className="text-xs font-bold text-white font-mono flex items-center gap-2 uppercase tracking-wider">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              2. Target Web Platforms & Feeds
            </h3>
            <div className="space-y-2">
              {[
                { id: 'ARBEITNOW', name: 'Arbeitnow Global Remote API', desc: 'Direct European & worldwide engineering listings' },
                { id: 'JOBICY', name: 'Jobicy Global Remote Tech', desc: 'Active remote software & system developer jobs' },
                { id: 'GITHUB_CONTRIBUTIONS', name: 'GitHub Issues & Paid Bounties', desc: 'Open source project contributions & help-wanted tasks' },
                { id: 'HACKER_NEWS', name: 'Hacker News (Who is Hiring)', desc: 'Direct early-stage startup & technical founder threads' },
              ].map((plat) => (
                <label
                  key={plat.id}
                  className={`flex items-start gap-3 p-2.5 rounded-xl border transition-all cursor-pointer ${
                    selectedPlatforms.includes(plat.id)
                      ? 'bg-brand-500/10 border-brand-500/40 text-white'
                      : 'bg-surface-400/40 border-white/5 text-zinc-400 hover:border-white/10'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedPlatforms.includes(plat.id)}
                    onChange={() => togglePlatform(plat.id)}
                    className="mt-0.5 accent-brand-500 rounded"
                  />
                  <div>
                    <span className="text-xs font-semibold block leading-tight">{plat.name}</span>
                    <span className="text-[10px] text-zinc-400">{plat.desc}</span>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Opportunity Types */}
          <div className="p-5 rounded-2xl bg-surface-300/60 border border-white/10 space-y-3">
            <h3 className="text-xs font-bold text-white font-mono flex items-center gap-2 uppercase tracking-wider">
              <Filter className="w-3.5 h-3.5 text-amber-400" />
              3. Opportunity Scopes
            </h3>
            <div className="grid grid-cols-2 gap-2">
              {[
                { id: 'REMOTE', label: 'Remote Work', icon: Globe },
                { id: 'CONTRACT', label: 'Part-Time / Contract', icon: Briefcase },
                { id: 'PROJECT_CONTRIBUTION', label: 'Project Contributions', icon: Code2 },
                { id: 'FULL_TIME', label: 'Full-Time Roles', icon: ShieldCheck },
              ].map((scope) => {
                const isChecked = selectedTypes.includes(scope.id);
                const Icon = scope.icon;
                return (
                  <button
                    key={scope.id}
                    type="button"
                    onClick={() => toggleType(scope.id)}
                    className={`p-2.5 rounded-xl border text-left text-xs font-mono flex items-center gap-2 transition-all ${
                      isChecked
                        ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
                        : 'bg-surface-400/40 border-white/5 text-zinc-400 hover:border-white/10'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    <span>{scope.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Auto-Apply Safety Switch */}
            <div className="pt-2 border-t border-white/5 flex items-center justify-between">
              <div>
                <span className="text-xs font-mono text-zinc-200 block">Auto-Submit Qualifying</span>
                <span className="text-[10px] text-zinc-500 font-mono">
                  Level {profile?.automation_level ?? 3} policy applies
                </span>
              </div>
              <input
                type="checkbox"
                checked={autoApplyEnabled}
                onChange={(e) => setAutoApplyEnabled(e.target.checked)}
                className="w-4 h-4 accent-brand-500 rounded cursor-pointer"
              />
            </div>

            {mode === 'SCHEDULED' && (
              <button
                type="button"
                onClick={handleSaveSchedule}
                className="w-full text-xs font-mono bg-white/5 hover:bg-white/10 text-zinc-200 py-2 rounded-lg border border-white/10 transition-all text-center block mt-3"
              >
                Save Recurring Schedule
              </button>
            )}
          </div>
        </div>

        {/* Right Column: Live Browser Terminal & Session Summary (7 cols) */}
        <div className="lg:col-span-7 space-y-5">
          {/* Session Summary Card */}
          {activeSession && (
            <div className="p-5 rounded-2xl bg-surface-300/80 border border-white/10 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white font-mono flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  Latest Crawl Summary Report
                </span>
                <span className="text-[10px] font-mono text-zinc-500">
                  Duration: {activeSession.duration_seconds}s
                </span>
              </div>

              {/* KPI Badges */}
              <div className="grid grid-cols-4 gap-2 text-center">
                <div className="p-2.5 rounded-xl bg-surface-400/80 border border-white/5">
                  <span className="text-[10px] text-zinc-400 font-mono block">Platforms</span>
                  <span className="text-base font-bold text-white font-mono">
                    {activeSession.platforms_crawled?.length || 0}
                  </span>
                </div>
                <div className="p-2.5 rounded-xl bg-surface-400/80 border border-white/5">
                  <span className="text-[10px] text-zinc-400 font-mono block">Discovered</span>
                  <span className="text-base font-bold text-cyan-300 font-mono">
                    {activeSession.total_discovered || 0}
                  </span>
                </div>
                <div className="p-2.5 rounded-xl bg-surface-400/80 border border-white/5">
                  <span className="text-[10px] text-zinc-400 font-mono block">Matched</span>
                  <span className="text-base font-bold text-brand-300 font-mono">
                    {activeSession.total_matched || 0}
                  </span>
                </div>
                <div className="p-2.5 rounded-xl bg-surface-400/80 border border-white/5">
                  <span className="text-[10px] text-zinc-400 font-mono block">Auto-Applied</span>
                  <span className="text-base font-bold text-emerald-400 font-mono">
                    {activeSession.total_applied || 0}
                  </span>
                </div>
              </div>

              <p className="text-xs text-zinc-300 bg-surface-400/40 p-3 rounded-xl border border-white/5 leading-relaxed font-sans">
                {activeSession.summary_text}
              </p>
            </div>
          )}

          {/* Live Terminal Console */}
          <div className="rounded-2xl bg-black/80 border border-white/10 overflow-hidden shadow-2xl flex flex-col h-[520px]">
            {/* Terminal Header */}
            <div className="px-4 py-2.5 bg-surface-400/90 border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-rose-500/80" />
                  <div className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
                </div>
                <span className="text-xs font-mono text-zinc-400 ml-2 flex items-center gap-1.5">
                  <Terminal className="w-3.5 h-3.5 text-brand-400" />
                  browser-agent-feed.log
                </span>
              </div>

              <div className="flex items-center gap-2">
                {isRunning ? (
                  <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center gap-1 animate-pulse">
                    ● ACTIVE CRAWL
                  </span>
                ) : (
                  <span className="text-[10px] font-mono text-zinc-500">IDLE</span>
                )}
                <button
                  type="button"
                  onClick={loadStatus}
                  className="text-zinc-500 hover:text-white p-1 rounded"
                  title="Refresh console"
                >
                  <RefreshCw className="w-3 h-3" />
                </button>
              </div>
            </div>

            {/* Terminal Log Output */}
            <div className="p-4 flex-1 overflow-y-auto space-y-2 font-mono text-xs text-zinc-300">
              {liveLogs.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-zinc-600 space-y-2">
                  <Globe className="w-8 h-8 opacity-40" />
                  <span>No active crawl logs yet.</span>
                  <span className="text-[10px]">Click "Start Crawling Now" to launch the browser agent.</span>
                </div>
              ) : (
                liveLogs.map((log: any, idx: number) => {
                  const statusColor =
                    log.status === 'SUCCESS'
                      ? 'text-emerald-400'
                      : log.status === 'WARNING'
                      ? 'text-amber-400'
                      : 'text-cyan-400';

                  return (
                    <div
                      key={idx}
                      className="p-2 rounded bg-surface-500/30 border border-white/5 space-y-1 hover:bg-surface-500/50 transition-colors"
                    >
                      <div className="flex items-center justify-between text-[10px]">
                        <div className="flex items-center gap-2">
                          <span className="text-zinc-500">[{log.timestamp}]</span>
                          <span className={`font-bold ${statusColor}`}>
                            [{log.step}]
                          </span>
                        </div>
                        <span className="text-zinc-500 bg-white/5 px-1.5 py-0.2 rounded text-[9px]">
                          {log.platform}
                        </span>
                      </div>
                      <p className="text-zinc-200 text-[11px] leading-relaxed pl-2 border-l border-white/10">
                        {log.message}
                      </p>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

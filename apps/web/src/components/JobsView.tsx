'use client';

import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  Building2,
  ExternalLink,
  Globe,
  Loader2,
  Lock,
  Pause,
  Play,
  Plus,
  RefreshCw,
  Search,
  Terminal,
  Trash2,
  X,
} from 'lucide-react';
import { fetchApi } from '@/lib/api';

const TABS = [
  { id: 'MATCH', label: 'Matches (70+)', hint: 'Waiting for a slot in today’s apply queue.' },
  { id: 'MAYBE', label: 'Maybe (50–69)', hint: 'Worth a look; queue the ones you want.' },
  { id: 'QUEUED', label: 'Queued', hint: 'In the Applications tracker; the worker fills them.' },
  { id: 'DISMISSED', label: 'Dismissed', hint: '' },
];

const BREAKDOWN_MAX: Record<string, number> = { skills: 40, title: 25, salary: 15, employer: 10, freshness: 10 };

// The API stores UTC; some fields arrive without a zone suffix
const parseUtc = (iso: string) => new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`);

const ago = (iso?: string | null) => {
  if (!iso) return 'never';
  const mins = Math.max(0, Math.round((Date.now() - parseUtc(iso).getTime()) / 60000));
  if (mins < 60) return `${mins}m ago`;
  if (mins < 60 * 24) return `${Math.round(mins / 60)}h ago`;
  return `${Math.round(mins / 1440)}d ago`;
};

export function JobsView() {
  const [tab, setTab] = useState('MATCH');
  const [jobs, setJobs] = useState<any[]>([]);
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [platforms, setPlatforms] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState<string | null>(null);
  const [summary, setSummary] = useState<any>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [companyFilter, setCompanyFilter] = useState('');
  const [showAdd, setShowAdd] = useState(false);
  const [newName, setNewName] = useState('');
  const [newUrl, setNewUrl] = useState('');

  const loadJobs = async () => {
    setLoading(true);
    try {
      const all = await Promise.all(TABS.map((t) => fetchApi<any[]>(`/api/opportunities?status=${t.id}`)));
      setCounts(Object.fromEntries(TABS.map((t, i) => [t.id, all[i].length])));
      setJobs(all[TABS.findIndex((t) => t.id === tab)]);
    } catch (err: any) {
      setNotice(`Could not load jobs: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const loadPlatforms = async () => {
    try {
      setPlatforms(await fetchApi<any[]>('/api/platforms'));
    } catch (err: any) {
      setNotice(`Could not load sources: ${err.message}`);
    }
  };

  useEffect(() => {
    loadPlatforms();
  }, []);
  useEffect(() => {
    loadJobs();
  }, [tab]);

  const runDiscovery = async (platformId?: string) => {
    setRunning(platformId || 'all');
    setNotice(null);
    try {
      const res = await fetchApi<any>(
        platformId ? `/api/platforms/${platformId}/scrape` : '/api/discovery/run?force=true',
        { method: 'POST' },
      );
      setSummary(res);
      await Promise.all([loadJobs(), loadPlatforms()]);
    } catch (err: any) {
      setNotice(`Discovery failed: ${err.message}`);
    } finally {
      setRunning(null);
    }
  };

  const setStatus = async (opp: any, status: string) => {
    await fetchApi(`/api/opportunities/${opp.id}/user-status`, {
      method: 'PUT',
      body: JSON.stringify({ status, reason: `Candidate moved it to ${status}` }),
    });
    await loadJobs();
  };

  const queue = async (opp: any) => {
    try {
      await fetchApi(`/api/opportunities/${opp.id}/human-apply`, { method: 'POST' });
      setNotice(`Queued ${opp.company_name} — ${opp.title}. Nothing is submitted until you approve it.`);
    } catch (err: any) {
      setNotice(String(err.message).includes('Already tracked') ? 'Already in your tracker.' : err.message);
    }
    await loadJobs();
  };

  const togglePlatform = async (p: any) => {
    await fetchApi(`/api/platforms/${p.id}`, {
      method: 'PUT',
      body: JSON.stringify({ status: p.status === 'ACTIVE' ? 'PAUSED' : 'ACTIVE' }),
    });
    await loadPlatforms();
  };

  const removePlatform = async (p: any) => {
    if (!confirm(`Remove ${p.name} from your sources?`)) return;
    await fetchApi(`/api/platforms/${p.id}`, { method: 'DELETE' });
    await loadPlatforms();
  };

  const addPlatform = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await fetchApi('/api/platforms', { method: 'POST', body: JSON.stringify({ name: newName, url: newUrl }) });
      setNewName('');
      setNewUrl('');
      setShowAdd(false);
      await loadPlatforms();
    } catch (err: any) {
      setNotice(err.message);
    }
  };

  const filteredJobs = useMemo(() => {
    const q = search.toLowerCase();
    return jobs
      .filter((j) => !q || `${j.title} ${j.company_name}`.toLowerCase().includes(q))
      .sort((a, b) => (b.matching_score?.overall_match_score || 0) - (a.matching_score?.overall_match_score || 0));
  }, [jobs, search]);

  const boards = platforms.filter((p) => p.category !== 'COMPANY_BOARD');
  const companies = platforms.filter(
    (p) => p.category === 'COMPANY_BOARD' && (!companyFilter || p.name.toLowerCase().includes(companyFilter.toLowerCase())),
  );
  const companyCount = platforms.filter((p) => p.category === 'COMPANY_BOARD').length;

  return (
    <div className="space-y-8 pb-16">
      {/* Run */}
      <div className="p-5 rounded-2xl bg-surface-300 border border-white/5 flex flex-wrap items-center gap-4">
        <div className="flex-1 min-w-[260px]">
          <h2 className="text-sm font-bold text-white">Find remote roles</h2>
          <p className="text-[11px] text-zinc-400 mt-1">
            Searches {boards.filter((b) => b.status === 'ACTIVE' && b.category === 'JOB_BOARD').length} job boards and{' '}
            {companyCount} company job boards, filters by your intake (remote from your country, salary, title, last 14
            days on boards / 60 on company pages), and scores each role. 70+ goes to the apply queue up to your daily cap.
          </p>
        </div>
        <button
          onClick={() => runDiscovery()}
          disabled={!!running}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-xs font-bold text-white shadow-glow disabled:opacity-50"
        >
          {running === 'all' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
          {running === 'all' ? 'Searching…' : 'Search all sources now'}
        </button>
      </div>

      {summary && (
        <div className="p-4 rounded-xl bg-surface-300 border border-white/5 text-xs text-zinc-300 space-y-1">
          <div className="font-semibold text-white">
            Last search: {summary.fetched ?? 0} roles read, {summary.eligible ?? 0} passed your filters,{' '}
            {summary.new ?? 0} new ({summary.match ?? 0} matches, {summary.maybe ?? 0} maybe), {summary.queued ?? 0} queued.
          </div>
          {(summary.platforms || []).filter((p: any) => p.error).map((p: any) => (
            <div key={p.platform} className="text-amber-300 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" /> {p.platform}: {p.error}
            </div>
          ))}
        </div>
      )}

      {notice && (
        <div className="flex items-center justify-between p-3 rounded-lg bg-surface-300 border border-white/10 text-xs text-zinc-200">
          <span>{notice}</span>
          <button onClick={() => setNotice(null)}>
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Jobs */}
      <section className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border ${
                tab === t.id ? 'bg-brand-500 text-white border-brand-500' : 'bg-surface-300 text-zinc-300 border-white/10 hover:text-white'
              }`}
            >
              {t.label} <span className="opacity-70">({counts[t.id] ?? 0})</span>
            </button>
          ))}
          <div className="relative ml-auto">
            <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-2.5 top-2.5" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter title or company"
              className="pl-8 p-2 rounded-lg bg-surface-300 border border-white/10 text-xs text-white focus:outline-none focus:border-brand-500"
            />
          </div>
        </div>
        <p className="text-[11px] text-zinc-500">{TABS.find((t) => t.id === tab)?.hint}</p>

        {loading ? (
          <div className="flex items-center gap-2 text-xs text-zinc-400">
            <Loader2 className="w-4 h-4 animate-spin" /> Loading…
          </div>
        ) : filteredJobs.length === 0 ? (
          <div className="p-10 text-center text-xs text-zinc-500 border border-dashed border-white/10 rounded-2xl">
            Nothing here yet. Run a search, and make sure your intake has target titles and your country.
          </div>
        ) : (
          <div className="space-y-2">
            {filteredJobs.map((j) => {
              const score = Math.round(j.matching_score?.overall_match_score ?? 0);
              const breakdown = j.raw_metadata?.score_breakdown || {};
              const notes: string[] = j.raw_metadata?.notes || [];
              return (
                <div key={j.id} className="p-4 rounded-xl bg-surface-300 border border-white/5 flex flex-wrap gap-4">
                  <div className="w-12 text-center">
                    <div className={`text-lg font-bold ${score >= 70 ? 'text-emerald-400' : 'text-amber-300'}`}>{score}</div>
                    <div className="text-[9px] text-zinc-500">score</div>
                  </div>
                  <div className="flex-1 min-w-[260px] space-y-1">
                    <div className="flex items-center gap-2">
                      <a href={j.raw_metadata?.listing_url || j.url} target="_blank" rel="noreferrer" className="text-sm font-bold text-white hover:text-brand-300">
                        {j.title}
                      </a>
                      <ExternalLink className="w-3 h-3 text-zinc-500" />
                    </div>
                    <div className="text-xs text-zinc-300">
                      {j.company_name} · <span className="text-zinc-400">{j.location}</span>
                      {j.country && j.country !== 'Not stated' && <span className="text-zinc-500"> · {j.country}</span>}
                    </div>
                    <div className="text-[11px] text-zinc-500">
                      {j.source}
                      {j.raw_metadata?.attribution ? ` (${j.raw_metadata.attribution})` : ''} · posted {ago(j.date_posted)}
                      {j.raw_metadata?.how_to_apply ? ` · ${j.raw_metadata.how_to_apply}` : ''}
                    </div>
                    <div className="flex flex-wrap gap-1 pt-1">
                      {Object.entries(breakdown).map(([k, v]) => (
                        <span key={k} className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-zinc-400">
                          {k} {String(v)}/{BREAKDOWN_MAX[k]}
                        </span>
                      ))}
                      {(j.required_skills || []).slice(0, 6).map((s: string) => (
                        <span key={s} className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300">
                          {s}
                        </span>
                      ))}
                      {notes.filter((n) => n.startsWith('Region')).map((n) => (
                        <span key={n} className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300">
                          {n}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    {(tab === 'MATCH' || tab === 'MAYBE' || tab === 'DISMISSED') && (
                      <button
                        onClick={() => queue(j)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-xs font-bold text-white"
                      >
                        <Play className="w-3 h-3" /> Queue to apply
                      </button>
                    )}
                    {tab !== 'DISMISSED' && tab !== 'QUEUED' && (
                      <button
                        onClick={() => setStatus(j, 'DISMISSED')}
                        className="px-3 py-1.5 rounded-lg bg-surface-200 border border-white/10 text-xs text-zinc-400 hover:text-white"
                      >
                        Dismiss
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Sources */}
      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mr-auto">Sources</h3>
          <button
            onClick={() => setShowAdd((v) => !v)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-300 border border-white/10 text-xs text-zinc-200 hover:text-white"
          >
            {showAdd ? <X className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />} Add a source
          </button>
        </div>

        {showAdd && (
          <form onSubmit={addPlatform} className="flex flex-wrap gap-2 p-4 rounded-xl bg-surface-300 border border-white/10">
            <input required value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Name, e.g. Stripe"
              className="p-2 rounded-lg bg-surface-200 border border-white/10 text-xs text-white w-48" />
            <input required value={newUrl} onChange={(e) => setNewUrl(e.target.value)}
              placeholder="Job board URL, e.g. https://jobs.ashbyhq.com/company"
              className="flex-1 min-w-[280px] p-2 rounded-lg bg-surface-200 border border-white/10 text-xs text-white" />
            <button type="submit" className="px-4 py-2 rounded-lg bg-brand-500 text-xs font-bold text-white">Add</button>
            <p className="w-full text-[10px] text-zinc-500">
              Supported: company boards on Greenhouse, Lever and Ashby, plus We Work Remotely, Remote OK, Himalayas, Remotive, Jobicy.
            </p>
          </form>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {boards.map((p) => (
            <div key={p.id} className="p-4 rounded-xl bg-surface-300 border border-white/5 space-y-2">
              <div className="flex items-center gap-2">
                {p.status === 'NEEDS_LOGIN' || p.category === 'LINKEDIN_POSTS' ? (
                  <Lock className="w-3.5 h-3.5 text-amber-400" />
                ) : (
                  <Globe className="w-3.5 h-3.5 text-brand-400" />
                )}
                <span className="text-xs font-bold text-white mr-auto">{p.name}</span>
                <span className={`text-[10px] px-1.5 py-0.5 rounded ${p.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-300' : 'bg-white/5 text-zinc-400'}`}>
                  {p.status.replace('_', ' ').toLowerCase()}
                </span>
              </div>
              {p.auth_notes && <p className="text-[11px] text-zinc-400">{p.auth_notes}</p>}
              <p className="text-[11px] text-zinc-500">
                Last run {ago(p.last_scraped_at)}
                {p.last_run && !p.last_run.error && ` · ${p.last_run.fetched} read, ${p.last_run.eligible} passed, ${p.last_run.new} new`}
              </p>
              {p.last_run?.error && <p className="text-[11px] text-amber-300">{p.last_run.error}</p>}
              <div className="flex items-center gap-2">
                {p.category === 'LINKEDIN_POSTS' ? (
                  <code className="text-[10px] text-brand-300 flex items-center gap-1">
                    <Terminal className="w-3 h-3" /> python -m apps.worker.cli linkedin-posts
                  </code>
                ) : p.status === 'ACTIVE' || p.status === 'PAUSED' ? (
                  <>
                    <button onClick={() => runDiscovery(p.id)} disabled={!!running}
                      className="flex items-center gap-1 text-[11px] text-zinc-300 hover:text-white disabled:opacity-40">
                      {running === p.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />} Run now
                    </button>
                    <button onClick={() => togglePlatform(p)} className="flex items-center gap-1 text-[11px] text-zinc-400 hover:text-white">
                      {p.status === 'ACTIVE' ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                      {p.status === 'ACTIVE' ? 'Pause' : 'Resume'}
                    </button>
                  </>
                ) : null}
                <button onClick={() => removePlatform(p)} className="ml-auto text-zinc-500 hover:text-rose-400">
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="rounded-2xl border border-white/5 overflow-hidden">
          <div className="flex items-center gap-2 p-3 bg-surface-300">
            <Building2 className="w-4 h-4 text-brand-400" />
            <span className="text-xs font-bold text-white mr-auto">Company job boards ({companyCount})</span>
            <input value={companyFilter} onChange={(e) => setCompanyFilter(e.target.value)} placeholder="Filter companies"
              className="p-1.5 rounded-lg bg-surface-200 border border-white/10 text-xs text-white" />
          </div>
          <div className="max-h-80 overflow-y-auto divide-y divide-white/5">
            {companies.map((p) => (
              <div key={p.id} className="flex items-center gap-3 px-3 py-2 text-xs bg-surface-200/40">
                <a href={p.url} target="_blank" rel="noreferrer" className="text-zinc-200 hover:text-white w-40 truncate">{p.name}</a>
                {p.remote_first && <span className="text-[10px] px-1.5 py-0.5 rounded bg-brand-500/10 text-brand-300">remote-first</span>}
                <span className="text-[11px] text-zinc-500 flex-1 truncate">
                  {p.last_run?.error
                    ? p.last_run.error
                    : p.last_run
                    ? `${p.last_run.fetched} open roles, ${p.last_run.eligible} passed your filters · ${ago(p.last_scraped_at)}`
                    : 'Not searched yet'}
                </span>
                <button onClick={() => togglePlatform(p)} className="text-[11px] text-zinc-400 hover:text-white">
                  {p.status === 'ACTIVE' ? 'Pause' : 'Resume'}
                </button>
                <button onClick={() => removePlatform(p)} className="text-zinc-500 hover:text-rose-400">
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

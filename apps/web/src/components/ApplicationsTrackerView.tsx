'use client';

import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  CalendarClock,
  Check,
  Copy,
  ExternalLink,
  Loader2,
  Plus,
  RefreshCw,
  Search,
  Terminal,
  Trash2,
  X,
} from 'lucide-react';
import { fetchApi } from '@/lib/api';

const STATUS_STYLE: Record<string, string> = {
  QUEUED: 'bg-zinc-500/10 text-zinc-300 border-zinc-500/20',
  PAUSED: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
  AWAITING_APPROVAL: 'bg-brand-500/15 text-brand-300 border-brand-500/30',
  SUBMITTED: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30',
  VIEWED: 'bg-cyan-500/10 text-cyan-200 border-cyan-500/20',
  REPLIED: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
  INTERVIEW: 'bg-emerald-500/15 text-emerald-200 border-emerald-500/40',
  OFFER: 'bg-emerald-500/25 text-emerald-100 border-emerald-500/50',
  REJECTED: 'bg-rose-500/10 text-rose-300 border-rose-500/20',
  GHOSTED: 'bg-zinc-700/30 text-zinc-500 border-white/5',
};

const label = (s: string) => s.replace(/_/g, ' ').toLowerCase().replace(/^\w/, (c) => c.toUpperCase());
const day = (iso?: string | null) => (iso ? new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : '—');

const emptyForm = { company: '', role: '', job_url: '', source_platform: '', apply_channel: '', post_url: '', notes: '' };

export function ApplicationsTrackerView() {
  const [rows, setRows] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [sourceFilter, setSourceFilter] = useState('');
  const [search, setSearch] = useState('');
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [notice, setNotice] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const load = async () => {
    const params = new URLSearchParams();
    if (statusFilter) params.set('status', statusFilter);
    if (sourceFilter) params.set('source_platform', sourceFilter);
    if (search) params.set('search', search);
    try {
      setLoading(true);
      const [list, st] = await Promise.all([
        fetchApi<any[]>(`/api/tracker?${params.toString()}`),
        fetchApi<any>('/api/tracker/stats'),
      ]);
      setRows(list);
      setStats(st);
    } catch (err: any) {
      setNotice(`Could not load tracker: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [statusFilter, sourceFilter]);

  const update = async (id: string, patch: Record<string, any>) => {
    try {
      await fetchApi(`/api/tracker/${id}`, { method: 'PUT', body: JSON.stringify(patch) });
      await load();
    } catch (err: any) {
      setNotice(`Update failed: ${err.message}`);
    }
  };

  const remove = async (row: any) => {
    if (!confirm(`Remove ${row.company} — ${row.role} from the tracker?`)) return;
    await fetchApi(`/api/tracker/${row.id}`, { method: 'DELETE' });
    await load();
  };

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = Object.fromEntries(Object.entries(form).filter(([, v]) => v !== ''));
    try {
      await fetchApi('/api/tracker', { method: 'POST', body: JSON.stringify(payload) });
      setForm(emptyForm);
      setShowAdd(false);
      setNotice(`Tracking ${form.company} — ${form.role}.`);
      await load();
    } catch (err: any) {
      setNotice(err.message);
    }
  };

  const copyCommand = (row: any, submit: boolean) => {
    const cmd = `python -m apps.worker.cli fill --tracker-id ${row.id}${submit ? ' --submit' : ' --keep-open'}`;
    navigator.clipboard.writeText(cmd);
    setCopiedId(row.id + (submit ? '-s' : ''));
    setTimeout(() => setCopiedId(null), 1500);
  };

  const sources: string[] = stats ? Object.keys(stats.by_source || {}) : [];
  const now = Date.now();

  return (
    <div className="space-y-6 pb-16">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[
          { k: 'Tracked', v: stats?.total ?? '—' },
          { k: 'Awaiting your approval', v: stats?.by_status?.AWAITING_APPROVAL ?? '—' },
          { k: 'Submitted today', v: stats?.submitted_today ?? '—' },
          { k: 'Follow-ups due', v: stats?.follow_ups_due ?? '—' },
          { k: 'Response rate', v: stats?.response_rate != null ? `${stats.response_rate}%` : '—' },
        ].map((s) => (
          <div key={s.k} className="p-4 rounded-xl bg-surface-300 border border-white/5">
            <div className="text-[11px] text-zinc-400">{s.k}</div>
            <div className="text-xl font-bold text-white mt-1">{s.v}</div>
          </div>
        ))}
      </div>

      {/* Worker hint */}
      <div className="flex items-start gap-2 p-3 rounded-xl bg-black/40 border border-white/5 text-[11px] text-zinc-300">
        <Terminal className="w-3.5 h-3.5 text-brand-400 mt-0.5 shrink-0" />
        <span>
          Fill everything queued in your own browser (no submit):{' '}
          <code className="text-brand-300">python -m apps.worker.cli queue</code>. Review rows marked “Awaiting approval”,
          then copy their submit command.
        </span>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-2.5 top-2.5" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && load()}
            placeholder="Search company or role, press Enter"
            className="w-full pl-8 p-2 rounded-lg bg-surface-300 border border-white/10 text-xs text-white focus:outline-none focus:border-brand-500"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="p-2 rounded-lg bg-surface-300 border border-white/10 text-xs text-white"
        >
          <option value="">All statuses</option>
          {(stats?.statuses || []).map((s: string) => (
            <option key={s} value={s}>
              {label(s)} ({stats?.by_status?.[s] ?? 0})
            </option>
          ))}
        </select>
        <select
          value={sourceFilter}
          onChange={(e) => setSourceFilter(e.target.value)}
          className="p-2 rounded-lg bg-surface-300 border border-white/10 text-xs text-white"
        >
          <option value="">All sources</option>
          {sources.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <button onClick={load} className="p-2 rounded-lg bg-surface-300 border border-white/10 text-zinc-300 hover:text-white">
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => setShowAdd((v) => !v)}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-xs font-bold text-white shadow-glow"
        >
          {showAdd ? <X className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
          <span>{showAdd ? 'Cancel' : 'Add application'}</span>
        </button>
      </div>

      {notice && (
        <div className="flex items-center justify-between p-3 rounded-lg bg-surface-300 border border-white/10 text-xs text-zinc-200">
          <span>{notice}</span>
          <button onClick={() => setNotice(null)} className="text-zinc-500 hover:text-white">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {showAdd && (
        <form onSubmit={create} className="grid grid-cols-1 md:grid-cols-3 gap-3 p-4 rounded-xl bg-surface-300 border border-white/10">
          {[
            ['company', 'Company *'],
            ['role', 'Role *'],
            ['job_url', 'Job URL'],
            ['source_platform', 'Source (e.g. We Work Remotely, LinkedIn post)'],
            ['apply_channel', 'Channel (e.g. GREENHOUSE, EMAIL, LINKEDIN_DM)'],
            ['post_url', 'LinkedIn post URL'],
          ].map(([k, l]) => (
            <input
              key={k}
              required={k === 'company' || k === 'role'}
              placeholder={l}
              value={(form as any)[k]}
              onChange={(e) => setForm({ ...form, [k]: e.target.value })}
              className="p-2 rounded-lg bg-surface-200 border border-white/10 text-xs text-white focus:outline-none focus:border-brand-500"
            />
          ))}
          <input
            placeholder="Notes"
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            className="md:col-span-2 p-2 rounded-lg bg-surface-200 border border-white/10 text-xs text-white focus:outline-none focus:border-brand-500"
          />
          <button type="submit" className="px-4 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-xs font-bold text-white">
            Track it
          </button>
        </form>
      )}

      {/* Table */}
      <div className="rounded-2xl border border-white/5 overflow-x-auto">
        <table className="w-full text-xs">
          <thead className="bg-surface-300 text-zinc-400 text-[11px]">
            <tr>
              <th className="text-left font-medium p-3">Company / role</th>
              <th className="text-left font-medium p-3">Source</th>
              <th className="text-right font-medium p-3">Score</th>
              <th className="text-left font-medium p-3">Status</th>
              <th className="text-left font-medium p-3">Submitted</th>
              <th className="text-left font-medium p-3">Next action</th>
              <th className="text-left font-medium p-3">Worker</th>
              <th className="p-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {loading && rows.length === 0 && (
              <tr>
                <td colSpan={8} className="p-8 text-center text-zinc-500">
                  <Loader2 className="w-4 h-4 animate-spin inline mr-2" /> Loading...
                </td>
              </tr>
            )}
            {!loading && rows.length === 0 && (
              <tr>
                <td colSpan={8} className="p-8 text-center text-zinc-500">
                  Nothing tracked yet. Queue roles from Jobs, track LinkedIn hiring posts, or add one by hand.
                </td>
              </tr>
            )}
            {rows.map((r) => {
              const overdue = r.next_action_due && new Date(r.next_action_due).getTime() <= now;
              return (
                <tr key={r.id} className="bg-surface-200/40 hover:bg-white/[0.02] align-top">
                  <td className="p-3">
                    <div className="font-semibold text-white">{r.company}</div>
                    <div className="text-zinc-400 flex items-center gap-1">
                      {r.role}
                      {r.job_url && (
                        <a href={r.job_url} target="_blank" rel="noreferrer" className="text-brand-400 hover:text-brand-300">
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                    {r.last_error && (
                      <div className="mt-1 text-[10px] text-amber-300 flex items-start gap-1 max-w-sm">
                        <AlertCircle className="w-3 h-3 mt-0.5 shrink-0" /> {r.last_error}
                      </div>
                    )}
                  </td>
                  <td className="p-3 text-zinc-300">
                    {r.source_platform}
                    {r.apply_channel && <div className="text-[10px] text-zinc-500 font-mono">{r.apply_channel}</div>}
                    {r.post_url && (
                      <a href={r.post_url} target="_blank" rel="noreferrer" className="text-[10px] text-brand-400 hover:text-brand-300">
                        post
                      </a>
                    )}
                  </td>
                  <td className="p-3 text-right font-mono text-zinc-300">{r.match_score != null ? Math.round(r.match_score) : '—'}</td>
                  <td className="p-3">
                    <select
                      value={r.status}
                      onChange={(e) => update(r.id, { status: e.target.value })}
                      className={`px-2 py-1 rounded-md border text-[11px] font-semibold bg-transparent ${STATUS_STYLE[r.status] || ''}`}
                    >
                      {(stats?.statuses || [r.status]).map((s: string) => (
                        <option key={s} value={s} className="bg-surface-300 text-white">
                          {label(s)}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="p-3 text-zinc-300">{day(r.submitted_at)}</td>
                  <td className="p-3">
                    {r.next_action ? (
                      <div className={overdue ? 'text-amber-300' : 'text-zinc-300'}>
                        <div>{r.next_action}</div>
                        {r.next_action_due && (
                          <div className="text-[10px] flex items-center gap-1">
                            <CalendarClock className="w-3 h-3" /> {day(r.next_action_due)}
                          </div>
                        )}
                      </div>
                    ) : (
                      <span className="text-zinc-600">—</span>
                    )}
                  </td>
                  <td className="p-3 space-y-1">
                    {r.job_url && ['QUEUED', 'PAUSED'].includes(r.status) && (
                      <button onClick={() => copyCommand(r, false)} className="flex items-center gap-1 text-[11px] text-zinc-300 hover:text-white">
                        {copiedId === r.id ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />} Fill command
                      </button>
                    )}
                    {r.status === 'AWAITING_APPROVAL' && (
                      <button onClick={() => copyCommand(r, true)} className="flex items-center gap-1 text-[11px] text-brand-300 hover:text-brand-200 font-semibold">
                        {copiedId === `${r.id}-s` ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />} Approve: submit command
                      </button>
                    )}
                    {r.evidence?.length > 0 && <div className="text-[10px] text-zinc-500">{r.evidence.length} screenshot(s)</div>}
                  </td>
                  <td className="p-3">
                    <button onClick={() => remove(r)} className="text-zinc-500 hover:text-rose-400">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

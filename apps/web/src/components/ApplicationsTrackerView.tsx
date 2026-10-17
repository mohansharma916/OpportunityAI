'use client';

import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  CalendarClock,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Copy,
  ExternalLink,
  Loader2,
  MessageSquare,
  Plus,
  RefreshCw,
  Search,
  Sparkles,
  Terminal,
  Trash2,
  X,
} from 'lucide-react';
import { fetchApi } from '@/lib/api';

const STATUS_STYLE: Record<string, string> = {
  QUEUED: 'bg-zinc-500/10 text-zinc-300 border-zinc-500/20',
  PAUSED: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
  AWAITING_APPROVAL: 'bg-brand-500/15 text-brand-300 border-brand-500/30',
  APPROVED: 'bg-brand-500/25 text-brand-200 border-brand-500/40',
  SUBMITTED: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30',
  VIEWED: 'bg-cyan-500/10 text-cyan-200 border-cyan-500/20',
  REPLIED: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
  INTERVIEW: 'bg-emerald-500/15 text-emerald-200 border-emerald-500/40',
  OFFER: 'bg-emerald-500/25 text-emerald-100 border-emerald-500/50',
  REJECTED: 'bg-rose-500/10 text-rose-300 border-rose-500/20',
  GHOSTED: 'bg-zinc-700/30 text-zinc-500 border-white/5',
};

const WORKER_HINT: Record<string, string> = {
  QUEUED: 'The worker fills it on its next run (dry run).',
  PAUSED: 'Answer the open questions below; the worker then fills it again.',
  AWAITING_APPROVAL: 'Check the fill and screenshot, then approve.',
  APPROVED: 'The worker submits it on its next run.',
};

const label = (s: string) => s.replace(/_/g, ' ').toLowerCase().replace(/^\w/, (c) => c.toUpperCase());
const day = (iso?: string | null) => (iso ? new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : '—');

const emptyForm = { company: '', role: '', job_url: '', source_platform: '', apply_channel: '', post_url: '', notes: '' };

function ReviewPanel({ row, onChanged }: { row: any; onChanged: () => Promise<void> }) {
  const form = row.form || {};
  const questions: any[] = form.unanswered || [];
  const [answers, setAnswers] = useState<Record<string, string>>(() =>
    Object.fromEntries(questions.map((q) => [q.canonical, q.suggestion?.answer || ''])),
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const shots: string[] = row.evidence || [];

  const act = async (fn: () => Promise<any>) => {
    setBusy(true);
    setError(null);
    try {
      await fn();
      await onChanged();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="p-4 space-y-4 bg-black/20 border-t border-white/5">
      <div className="text-[11px] text-zinc-400">
        {WORKER_HINT[row.status] || ''}
        {form.run_at && (
          <span className="text-zinc-500">
            {' '}Last run {new Date(form.run_at).toLocaleString()} · {form.adapter || 'GENERIC'} form · {form.details}
          </span>
        )}
      </div>

      {questions.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs font-bold text-white">Open questions ({questions.length})</h4>
          {questions.map((q) => (
            <div key={q.canonical} className="space-y-1">
              <div className="text-xs text-zinc-200">{q.label}</div>
              {q.options?.length ? (
                <select
                  value={answers[q.canonical] || ''}
                  onChange={(e) => setAnswers({ ...answers, [q.canonical]: e.target.value })}
                  className="w-full max-w-md p-2 rounded-lg bg-surface-200 border border-white/10 text-xs text-white"
                >
                  <option value="">Choose…</option>
                  {q.options.map((o: string) => (
                    <option key={o} value={o}>{o}</option>
                  ))}
                </select>
              ) : (
                <textarea
                  rows={2}
                  value={answers[q.canonical] || ''}
                  onChange={(e) => setAnswers({ ...answers, [q.canonical]: e.target.value })}
                  className="w-full p-2 rounded-lg bg-surface-200 border border-white/10 text-xs text-white"
                />
              )}
              {q.suggestion && (
                <div className="flex items-center gap-1 text-[10px] text-purple-300">
                  <Sparkles className="w-3 h-3" /> {q.suggestion.generated_by === 'OPENAI' ? 'OpenAI' : 'Claude'} suggested this ({q.suggestion.confidence}): {q.suggestion.basis}. Check it before saving.
                </div>
              )}
            </div>
          ))}
          <button
            disabled={busy || !Object.values(answers).some((v) => v.trim())}
            onClick={() => act(() => fetchApi(`/api/tracker/${row.id}/answers`, { method: 'POST', body: JSON.stringify({ answers }) }))}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-xs font-bold text-white disabled:opacity-40"
          >
            {busy ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />} Save answers & re-fill
          </button>
          <p className="text-[10px] text-zinc-500">Saved answers go into your answer bank and are reused on future forms.</p>
        </div>
      )}

      {form.fields?.length > 0 && (
        <div>
          <h4 className="text-xs font-bold text-white mb-1">What the worker filled</h4>
          <div className="rounded-lg border border-white/5 divide-y divide-white/5">
            {form.fields.map((f: any, i: number) => (
              <div key={i} className="flex gap-3 px-3 py-1.5 text-[11px]">
                <span className="w-1/2 text-zinc-400 truncate">{f.label}</span>
                <span className="flex-1 text-zinc-100 truncate">{String(f.value)}</span>
                <span className="text-[10px] text-zinc-500">{f.source === 'custom' ? 'saved answer' : 'intake'}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {shots.length > 0 && (
        <div className="flex gap-2 overflow-x-auto">
          {shots.slice(-3).map((_, i) => {
            const idx = shots.length - Math.min(3, shots.length) + i;
            return (
              <a key={idx} href={`/api/tracker/${row.id}/evidence/${idx}`} target="_blank" rel="noreferrer">
                <img src={`/api/tracker/${row.id}/evidence/${idx}`} alt="Form screenshot"
                  className="h-40 rounded-lg border border-white/10 object-cover object-top" />
              </a>
            );
          })}
        </div>
      )}

      {error && <p className="text-[11px] text-rose-300">{error}</p>}

      {row.status === 'AWAITING_APPROVAL' && (
        <button
          disabled={busy}
          onClick={() => act(() => fetchApi(`/api/tracker/${row.id}/approve`, { method: 'POST' }))}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white"
        >
          <CheckCircle2 className="w-3.5 h-3.5" /> Approve submission
        </button>
      )}
    </div>
  );
}

export function ApplicationsTrackerView() {
  const [rows, setRows] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [followUps, setFollowUps] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [sourceFilter, setSourceFilter] = useState('');
  const [search, setSearch] = useState('');
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [notice, setNotice] = useState<string | null>(null);
  const [openId, setOpenId] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const load = async () => {
    const params = new URLSearchParams();
    if (statusFilter) params.set('status', statusFilter);
    if (sourceFilter) params.set('source_platform', sourceFilter);
    if (search) params.set('search', search);
    try {
      setLoading(true);
      const [list, st, fu] = await Promise.all([
        fetchApi<any[]>(`/api/tracker?${params.toString()}`),
        fetchApi<any>('/api/tracker/stats'),
        fetchApi<any[]>('/api/tracker/follow-ups'),
      ]);
      setRows(list);
      setStats(st);
      setFollowUps(fu);
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

  const markFollowedUp = async (id: string) => {
    await fetchApi(`/api/tracker/${id}/follow-up`, { method: 'POST', body: JSON.stringify({}) });
    await load();
  };

  const sources: string[] = stats ? Object.keys(stats.by_source || {}) : [];
  const now = Date.now();

  return (
    <div className="space-y-6 pb-16">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[
          { k: 'Tracked', v: stats?.total ?? '—' },
          { k: 'Awaiting your review', v: (stats?.by_status?.AWAITING_APPROVAL ?? 0) + (stats?.by_status?.PAUSED ?? 0) },
          { k: 'Submitted today', v: stats?.submitted_today ?? '—' },
          { k: 'Follow-ups due', v: followUps.length },
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
          On your Mac, <code className="text-brand-300">python -m apps.worker.cli run</code> fills queued applications in your
          browser, submits the ones you approved (within your daily cap), and lists follow-ups.
          {stats?.clean_submits && Object.keys(stats.clean_submits).length > 0 && (
            <span className="text-zinc-500">
              {' '}Clean approvals toward auto-submit ({stats.trusted_after} needed, opt in under Intake):{' '}
              {Object.entries(stats.clean_submits).map(([k, v]) => `${k} ${v}`).join(', ')}.
            </span>
          )}
        </span>
      </div>

      {/* Follow-ups */}
      {followUps.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400">Follow-ups due</h3>
          {followUps.map((f) => (
            <div key={f.id} className="p-3 rounded-xl bg-surface-300 border border-amber-500/20 space-y-2">
              <div className="flex items-center gap-2 text-xs">
                <MessageSquare className="w-3.5 h-3.5 text-amber-300" />
                <span className="font-semibold text-white">{f.company} — {f.role}</span>
                <span className="text-zinc-500">submitted {day(f.submitted_at)}{f.follow_ups ? ` · ${f.follow_ups} follow-up(s) sent` : ''}</span>
              </div>
              <p className="text-[11px] text-zinc-300 whitespace-pre-wrap">{f.message}</p>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(f.message);
                    setCopiedId(f.id);
                    setTimeout(() => setCopiedId(null), 1500);
                  }}
                  className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-surface-200 border border-white/10 text-[11px] text-zinc-200"
                >
                  {copiedId === f.id ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />} Copy message
                </button>
                <button onClick={() => markFollowedUp(f.id)}
                  className="px-2.5 py-1 rounded-lg bg-amber-600/80 hover:bg-amber-500 text-[11px] font-semibold text-white">
                  I've followed up
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

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
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}
          className="p-2 rounded-lg bg-surface-300 border border-white/10 text-xs text-white">
          <option value="">All statuses</option>
          {(stats?.statuses || []).map((s: string) => (
            <option key={s} value={s}>{label(s)} ({stats?.by_status?.[s] ?? 0})</option>
          ))}
        </select>
        <select value={sourceFilter} onChange={(e) => setSourceFilter(e.target.value)}
          className="p-2 rounded-lg bg-surface-300 border border-white/10 text-xs text-white">
          <option value="">All sources</option>
          {sources.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <button onClick={load} className="p-2 rounded-lg bg-surface-300 border border-white/10 text-zinc-300 hover:text-white">
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
        <button onClick={() => setShowAdd((v) => !v)}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-xs font-bold text-white shadow-glow">
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
            <input key={k} required={k === 'company' || k === 'role'} placeholder={l} value={(form as any)[k]}
              onChange={(e) => setForm({ ...form, [k]: e.target.value })}
              className="p-2 rounded-lg bg-surface-200 border border-white/10 text-xs text-white focus:outline-none focus:border-brand-500" />
          ))}
          <input placeholder="Notes" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })}
            className="md:col-span-2 p-2 rounded-lg bg-surface-200 border border-white/10 text-xs text-white focus:outline-none focus:border-brand-500" />
          <button type="submit" className="px-4 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-xs font-bold text-white">
            Track it
          </button>
        </form>
      )}

      {/* Table */}
      <div className="rounded-2xl border border-white/5 overflow-hidden">
        {loading && rows.length === 0 && (
          <div className="p-8 text-center text-xs text-zinc-500">
            <Loader2 className="w-4 h-4 animate-spin inline mr-2" /> Loading...
          </div>
        )}
        {!loading && rows.length === 0 && (
          <div className="p-8 text-center text-xs text-zinc-500">
            Nothing tracked yet. Queue roles from Remote Jobs, track LinkedIn hiring posts, or add one by hand.
          </div>
        )}
        <div className="divide-y divide-white/5">
          {rows.map((r) => {
            const overdue = r.next_action_due && new Date(r.next_action_due).getTime() <= now;
            const open = openId === r.id;
            const openQs = r.form?.unanswered?.length || 0;
            return (
              <div key={r.id} className="bg-surface-200/40">
                <div className="flex flex-wrap items-start gap-4 p-3 text-xs">
                  <div className="flex-1 min-w-[220px]">
                    <div className="font-semibold text-white">{r.company}</div>
                    <div className="text-zinc-400 flex items-center gap-1">
                      {r.role}
                      {r.job_url && (
                        <a href={r.job_url} target="_blank" rel="noreferrer" className="text-brand-400 hover:text-brand-300">
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                    <div className="text-[10px] text-zinc-500">
                      {r.source_platform}{r.apply_channel ? ` · ${r.apply_channel}` : ''}
                      {r.match_score != null ? ` · score ${Math.round(r.match_score)}` : ''}
                    </div>
                    {r.last_error && (
                      <div className="mt-1 text-[10px] text-amber-300 flex items-start gap-1 max-w-md">
                        <AlertCircle className="w-3 h-3 mt-0.5 shrink-0" /> {r.last_error}
                      </div>
                    )}
                  </div>
                  <select value={r.status} onChange={(e) => update(r.id, { status: e.target.value })}
                    className={`px-2 py-1 rounded-md border text-[11px] font-semibold bg-transparent ${STATUS_STYLE[r.status] || ''}`}>
                    {(stats?.statuses || [r.status]).map((s: string) => (
                      <option key={s} value={s} className="bg-surface-300 text-white">{label(s)}</option>
                    ))}
                  </select>
                  <div className="w-24 text-zinc-300">{day(r.submitted_at)}</div>
                  <div className="w-40">
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
                  </div>
                  <button onClick={() => setOpenId(open ? null : r.id)}
                    className={`flex items-center gap-1 px-2.5 py-1 rounded-lg border text-[11px] ${
                      openQs || r.status === 'AWAITING_APPROVAL'
                        ? 'border-brand-500/40 text-brand-200 bg-brand-500/10'
                        : 'border-white/10 text-zinc-300'
                    }`}>
                    {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                    {openQs ? `Review (${openQs} open)` : 'Review'}
                  </button>
                  <button onClick={() => remove(r)} className="text-zinc-500 hover:text-rose-400">
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
                {open && <ReviewPanel key={`${r.id}-${r.form?.run_at || ''}`} row={r} onChanged={load} />}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

'use client';

import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  Bot,
  Check,
  CheckCircle2,
  Copy,
  FileUp,
  Gauge,
  Hand,
  Loader2,
  RefreshCw,
  RotateCcw,
  Sparkles,
  Terminal,
  X,
} from 'lucide-react';
import { fetchApi } from '@/lib/api';

const STATUS_ORDER = ['PENDING', 'APPROVED', 'FAILED', 'APPLIED', 'REJECTED'];
const STATUS_LABEL: Record<string, string> = {
  PENDING: 'To review',
  APPROVED: 'Approved',
  FAILED: 'Needs attention',
  APPLIED: 'Done',
  REJECTED: 'Rejected',
};

const scoreColor = (s: number | null) =>
  s === null ? 'bg-zinc-600' : s >= 80 ? 'bg-emerald-500' : s >= 50 ? 'bg-amber-500' : 'bg-rose-500';

function DraftCard({ draft, onDecide }: { draft: any; onDecide: (id: string, decision: string, value?: string) => Promise<void> }) {
  const [value, setValue] = useState(draft.proposed_value);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const [showCurrent, setShowCurrent] = useState(false);
  const editable = draft.status === 'PENDING' || draft.status === 'FAILED';
  const over = draft.char_limit && value.length > draft.char_limit;

  useEffect(() => setValue(draft.proposed_value), [draft.proposed_value]);

  const act = async (decision: string, withValue = false) => {
    setBusy(true);
    try {
      await onDecide(draft.id, decision, withValue && value !== draft.proposed_value ? value : undefined);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="p-4 rounded-xl bg-surface-300 border border-white/5 space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <h4 className="text-sm font-bold text-white mr-auto">{draft.title}</h4>
        <span
          className={`flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full border ${
            draft.apply_mode === 'AGENT'
              ? 'bg-brand-500/10 text-brand-300 border-brand-500/30'
              : 'bg-white/5 text-zinc-300 border-white/10'
          }`}
        >
          {draft.apply_mode === 'AGENT' ? <Bot className="w-3 h-3" /> : <Hand className="w-3 h-3" />}
          {draft.apply_mode === 'AGENT' ? 'Agent applies after approval' : 'You apply'}
        </span>
        {draft.generated_by === 'CLAUDE' && (
          <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/30">
            <Sparkles className="w-3 h-3" /> Claude
          </span>
        )}
      </div>

      {draft.rationale && <p className="text-[11px] text-zinc-400">{draft.rationale}</p>}

      {draft.current_value && (
        <button onClick={() => setShowCurrent((v) => !v)} className="text-[11px] text-zinc-500 hover:text-zinc-300">
          {showCurrent ? 'Hide' : 'Show'} current text
        </button>
      )}
      {showCurrent && (
        <div className="p-3 rounded-lg bg-black/30 border border-white/5 text-xs text-zinc-400 whitespace-pre-wrap">
          {draft.current_value}
        </div>
      )}

      <div>
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          readOnly={!editable}
          rows={Math.min(14, Math.max(2, value.split('\n').length + Math.floor(value.length / 90)))}
          className={`w-full p-3 rounded-lg bg-surface-200 border text-xs text-white whitespace-pre-wrap focus:outline-none ${
            over ? 'border-rose-500' : 'border-white/10 focus:border-brand-500'
          }`}
        />
        {draft.char_limit && (
          <div className={`text-[10px] text-right ${over ? 'text-rose-400' : 'text-zinc-500'}`}>
            {value.length} / {draft.char_limit}
          </div>
        )}
      </div>

      {editable && draft.alternatives?.length > 0 && (
        <div className="space-y-1">
          <div className="text-[10px] uppercase tracking-wider text-zinc-500">Other options</div>
          {draft.alternatives.map((alt: string, i: number) => (
            <button
              key={i}
              onClick={() => setValue(alt)}
              className="block w-full text-left p-2 rounded-lg bg-white/[0.02] hover:bg-white/[0.05] border border-white/5 text-[11px] text-zinc-300 whitespace-pre-wrap line-clamp-3"
            >
              {alt}
            </button>
          ))}
        </div>
      )}

      {draft.instructions && (
        <p className="text-[11px] text-zinc-400">
          <span className="text-zinc-500">Where: </span>
          {draft.instructions}
        </p>
      )}
      {draft.last_error && (
        <p className="flex items-start gap-1 text-[11px] text-amber-300">
          <AlertCircle className="w-3 h-3 mt-0.5 shrink-0" /> {draft.last_error}
        </p>
      )}

      <div className="flex flex-wrap items-center gap-2 pt-1">
        {editable && (
          <>
            <button
              disabled={busy || !!over}
              onClick={() => act('APPROVE', true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-xs font-bold text-white disabled:opacity-40"
            >
              {busy ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />} Approve
            </button>
            <button
              disabled={busy}
              onClick={() => act('REJECT')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-200 border border-white/10 text-xs text-zinc-300 hover:text-white"
            >
              <X className="w-3 h-3" /> Reject
            </button>
          </>
        )}
        <button
          onClick={() => {
            navigator.clipboard.writeText(value);
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
          }}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-200 border border-white/10 text-xs text-zinc-300 hover:text-white"
        >
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />} Copy
        </button>
        {draft.status === 'APPROVED' && draft.apply_mode === 'MANUAL' && (
          <button
            disabled={busy}
            onClick={() => act('MARK_APPLIED')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white"
          >
            <CheckCircle2 className="w-3 h-3" /> I've done it
          </button>
        )}
        {['APPROVED', 'REJECTED', 'FAILED'].includes(draft.status) && (
          <button
            disabled={busy}
            onClick={() => act('REOPEN')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-zinc-400 hover:text-white"
          >
            <RotateCcw className="w-3 h-3" /> Reopen
          </button>
        )}
      </div>
    </div>
  );
}

export function LinkedInOptimizerView() {
  const [state, setState] = useState<any>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [exportPath, setExportPath] = useState('');

  const load = async () => {
    try {
      setState(await fetchApi<any>('/api/linkedin/optimizer'));
    } catch (err: any) {
      setNotice(`Could not load optimizer: ${err.message}`);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const run = async (label: string, fn: () => Promise<any>) => {
    setBusy(label);
    setNotice(null);
    try {
      setState(await fn());
    } catch (err: any) {
      setNotice(err.message);
    } finally {
      setBusy(null);
    }
  };

  const importExport = () =>
    run('import', () =>
      fetchApi('/api/linkedin/optimizer/import-export', {
        method: 'POST',
        body: JSON.stringify({ path: exportPath || null }),
      }),
    );
  const analyze = () => run('analyze', () => fetchApi('/api/linkedin/optimizer/analyze', { method: 'POST' }));

  const decide = async (id: string, decision: string, value?: string) => {
    try {
      await fetchApi(`/api/linkedin/optimizer/drafts/${id}`, {
        method: 'POST',
        body: JSON.stringify({ decision, value }),
      });
      await load();
    } catch (err: any) {
      setNotice(err.message);
    }
  };

  if (!state) {
    return (
      <div className="flex items-center gap-2 text-xs text-zinc-400">
        <Loader2 className="w-4 h-4 animate-spin" /> Loading profile optimizer...
      </div>
    );
  }

  const audit = state.audit;
  const drafts: any[] = state.drafts || [];
  const approvedAgent = drafts.filter((d) => d.status === 'APPROVED' && d.apply_mode === 'AGENT').length;

  return (
    <div className="space-y-6">
      {/* Sources */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="p-4 rounded-xl bg-surface-300 border border-white/5 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-white">
            <Terminal className="w-4 h-4 text-brand-400" /> Read your live profile (most complete)
          </div>
          <p className="text-[11px] text-zinc-400">
            Opens your profile in the automation browser, reads it, scores it and drafts fixes.
          </p>
          <code className="block p-2 rounded-lg bg-black/40 text-[11px] text-brand-300">
            python -m apps.worker.cli linkedin-audit
          </code>
        </div>
        <div className="p-4 rounded-xl bg-surface-300 border border-white/5 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-white">
            <FileUp className="w-4 h-4 text-brand-400" /> Or import your LinkedIn data export
          </div>
          <p className="text-[11px] text-zinc-400">
            Settings &gt; Data privacy &gt; Get a copy of your data. Leave blank to use the path from your intake.
          </p>
          <div className="flex gap-2">
            <input
              value={exportPath}
              onChange={(e) => setExportPath(e.target.value)}
              placeholder="/Users/you/Downloads/Basic_LinkedInDataExport.zip"
              className="flex-1 p-2 rounded-lg bg-surface-200 border border-white/10 text-xs text-white focus:outline-none focus:border-brand-500"
            />
            <button
              onClick={importExport}
              disabled={!!busy}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-xs font-bold text-white disabled:opacity-40"
            >
              {busy === 'import' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FileUp className="w-3.5 h-3.5" />}
              Import
            </button>
          </div>
        </div>
      </div>

      {notice && (
        <div className="flex items-center justify-between p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-200">
          <span>{notice}</span>
          <button onClick={() => setNotice(null)}>
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {!state.snapshot && (
        <div className="p-10 text-center text-xs text-zinc-500 border border-dashed border-white/10 rounded-2xl">
          No profile reading yet. Use one of the two options above.
        </div>
      )}

      {state.snapshot && !audit && (
        <button onClick={analyze} className="text-xs text-brand-300 hover:text-brand-200">
          Profile read but not audited yet. Run the audit.
        </button>
      )}

      {audit && (
        <>
          {/* Score header */}
          <div className="p-5 rounded-2xl bg-surface-300 border border-white/5 flex flex-wrap items-center gap-6">
            <div className="flex items-center gap-3">
              <Gauge className="w-8 h-8 text-brand-400" />
              <div>
                <div className="text-3xl font-bold text-white">
                  {audit.overall_score}
                  <span className="text-sm text-zinc-500">/100</span>
                </div>
                <div className="text-[11px] text-zinc-400">
                  From {state.snapshot.source === 'SCREEN' ? 'live profile' : 'data export'},{' '}
                  {new Date(state.snapshot.captured_at).toLocaleString()}
                </div>
              </div>
            </div>
            <div className="flex-1 min-w-[240px] text-[11px] text-zinc-400">
              {state.claude_available ? (
                <span className="flex items-center gap-1 text-purple-300">
                  <Sparkles className="w-3 h-3" /> Drafts polished by Claude, checked against your facts.
                </span>
              ) : (
                <span>Template drafts from your facts. Set ANTHROPIC_API_KEY on the API to have Claude polish them.</span>
              )}
            </div>
            <button
              onClick={analyze}
              disabled={!!busy}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-surface-200 border border-white/10 text-xs text-zinc-200 hover:text-white disabled:opacity-40"
            >
              {busy === 'analyze' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
              Re-run audit & drafts
            </button>
          </div>

          {/* Sections */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {audit.sections.map((s: any) => (
              <div key={s.key} className="p-4 rounded-xl bg-surface-300 border border-white/5 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">{s.label}</span>
                  <span className="text-xs font-mono text-zinc-300">{s.score === null ? '?' : s.score}</span>
                </div>
                <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                  <div className={`h-full ${scoreColor(s.score)}`} style={{ width: `${s.score ?? 100}%`, opacity: s.score === null ? 0.3 : 1 }} />
                </div>
                {s.findings.length > 0 && (
                  <ul className="space-y-1">
                    {s.findings.map((f: string, i: number) => (
                      <li key={i} className="text-[11px] text-zinc-400 leading-snug">
                        {f}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>

          {/* Keywords */}
          <div className="p-4 rounded-xl bg-surface-300 border border-white/5 space-y-2">
            <div className="text-xs font-bold text-white">
              Recruiter keywords <span className="font-normal text-zinc-500">from {audit.keywords_source}</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {audit.keywords.map((k: string) => {
                const missing = audit.missing_keywords.includes(k);
                return (
                  <span
                    key={k}
                    className={`text-[11px] px-2 py-0.5 rounded-full border ${
                      missing
                        ? 'bg-amber-500/10 text-amber-300 border-amber-500/20'
                        : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'
                    }`}
                  >
                    {missing ? '' : '✓ '}
                    {k}
                  </span>
                );
              })}
            </div>
            <p className="text-[10px] text-zinc-500">Amber = not on your profile yet. Add only skills you actually have.</p>
          </div>
        </>
      )}

      {/* Apply hint */}
      {approvedAgent > 0 && (
        <div className="flex items-start gap-2 p-3 rounded-xl bg-brand-500/10 border border-brand-500/20 text-[11px] text-brand-200">
          <Bot className="w-4 h-4 mt-0.5 shrink-0" />
          <span>
            {approvedAgent} approved edit(s) ready for the agent. Preview with{' '}
            <code className="text-white">python -m apps.worker.cli linkedin-apply</code>, then save with{' '}
            <code className="text-white">python -m apps.worker.cli linkedin-apply --save</code>.
          </span>
        </div>
      )}

      {/* Drafts */}
      {STATUS_ORDER.map((status) => {
        const group = drafts.filter((d) => d.status === status);
        if (!group.length) return null;
        return (
          <div key={status} className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400">
              {STATUS_LABEL[status]} ({group.length})
            </h3>
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
              {group.map((d) => (
                <DraftCard key={d.id} draft={d} onDecide={decide} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

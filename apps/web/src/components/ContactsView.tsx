'use client';

import React, { useState } from 'react';
import { Users, Mail, ExternalLink, Calendar, CheckCircle2, Clock, Send, Eye, X, Loader2, Sparkles, Copy, Check } from 'lucide-react';
import { fetchApi } from '@/lib/api';

interface ContactsViewProps {
  contacts: any[];
  outreachSequences: any[];
  onRefresh?: () => void;
}

export function ContactsView({ contacts, outreachSequences, onRefresh }: ContactsViewProps) {
  const [selectedMessage, setSelectedMessage] = useState<any>(null);
  const [sendingId, setSendingId] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleSendMessage = async (msgId: string) => {
    setSendingId(msgId);
    try {
      await fetchApi(`/api/outreach/messages/${msgId}/send`, { method: 'POST' });
      if (selectedMessage && selectedMessage.id === msgId) {
        setSelectedMessage({ ...selectedMessage, status: 'SENT', sent_at: new Date().toISOString() });
      }
      if (onRefresh) onRefresh();
    } catch (err: any) {
      alert(`Failed to send email: ${err.message}`);
    } finally {
      setSendingId(null);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      <div className="pb-3 border-b border-white/5 flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-white tracking-tight flex items-center gap-2">
            <Users className="w-4 h-4 text-brand-400" />
            Hiring Contacts & Relationship CRM
          </h2>
          <p className="text-xs text-zinc-400 mt-0.5">
            Discovered decision makers, recruiter interactions, and staged follow-up drip sequences.
          </p>
        </div>
        <span className="text-xs font-mono text-zinc-400 bg-surface-300 px-3 py-1 rounded-lg border border-white/5">
          {contacts.length} Decision Makers • {outreachSequences.length} Active Sequences
        </span>
      </div>

      {/* Contacts Table / Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {contacts.map((c) => (
          <div
            key={c.id}
            className="p-4 rounded-xl bg-surface-300/40 border border-white/5 hover:border-brand-500/30 transition-all space-y-3"
          >
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-xs font-bold text-white">{c.full_name}</h3>
                <p className="text-[11px] text-brand-300 font-medium">{c.role}</p>
                <p className="text-[11px] text-zinc-400">{c.company_name}</p>
              </div>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                c.relationship_status === 'CONTACTED'
                  ? 'text-emerald-400 bg-emerald-950/40 border-emerald-800/40'
                  : 'text-cyan-300 bg-cyan-950/40 border-cyan-800/40'
              }`}>
                {c.relationship_status}
              </span>
            </div>

            {c.email && (
              <div className="flex items-center gap-2 text-xs text-zinc-300 font-mono bg-white/[0.02] p-2 rounded-lg border border-white/5">
                <Mail className="w-3.5 h-3.5 text-zinc-500 shrink-0" />
                <span className="truncate">{c.email}</span>
              </div>
            )}

            {c.notes && (
              <p className="text-[11px] text-zinc-400 italic font-sans">{c.notes}</p>
            )}

            <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[11px] text-zinc-500">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" /> {c.last_interaction_at ? 'Interacted' : 'Cadence Staged'}
              </span>
              <span className="text-[11px] font-mono text-brand-400">
                3-Step Drip
              </span>
            </div>
          </div>
        ))}

        {contacts.length === 0 && (
          <div className="col-span-full p-12 text-center text-zinc-500 text-xs border border-dashed border-white/5 rounded-xl">
            No contacts identified yet. Discovered hiring contacts appear here automatically.
          </div>
        )}
      </div>

      {/* Active Outreach Sequences */}
      <div className="pt-4 border-t border-white/5">
        <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3 font-mono flex items-center gap-2">
          <Mail className="w-3.5 h-3.5 text-brand-400" /> Staged Outreach Drip Sequences (Day 1 Intro, Day 4 Value-Add, Day 9 Check-In)
        </h3>
        <div className="space-y-4">
          {outreachSequences.map((seq) => (
            <div
              key={seq.id}
              className="p-5 rounded-xl bg-surface-300/40 border border-white/5 space-y-3"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold text-white">
                    Outreach Sequence: {seq.id.slice(0, 8)}
                  </span>
                  <span className="text-[10px] font-mono text-zinc-400 bg-white/5 px-2 py-0.5 rounded">
                    Step {seq.current_step} of 3
                  </span>
                </div>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-2.5 py-0.5 rounded border border-emerald-800/40">
                  {seq.status}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {(seq.messages || []).map((msg: any) => {
                  const isSent = msg.status === 'SENT';
                  const isSending = sendingId === msg.id;

                  return (
                    <div
                      key={msg.id}
                      className={`p-3.5 rounded-xl border text-xs space-y-2 transition-all flex flex-col justify-between ${
                        isSent
                          ? 'bg-emerald-950/10 border-emerald-500/20'
                          : 'bg-surface-200/90 border-white/5 hover:border-brand-500/30'
                      }`}
                    >
                      <div>
                        <div className="flex items-center justify-between text-[10px] text-zinc-400 font-mono mb-1">
                          <span className="font-semibold text-zinc-300">
                            Step {msg.step_number} • {msg.step_number === 1 ? 'Day 1' : msg.step_number === 2 ? 'Day 4' : 'Day 9'}
                          </span>
                          <span className={isSent ? 'text-emerald-400 font-bold' : 'text-amber-400'}>
                            {msg.status}
                          </span>
                        </div>
                        <p className="font-semibold text-white truncate text-xs">{msg.subject}</p>
                        <p className="text-[11px] text-zinc-400 line-clamp-3 mt-1 leading-relaxed">{msg.body}</p>
                      </div>

                      <div className="pt-2 border-t border-white/5 flex items-center justify-between gap-2 mt-2">
                        <button
                          onClick={() => setSelectedMessage(msg)}
                          className="text-[11px] text-zinc-400 hover:text-white flex items-center gap-1"
                        >
                          <Eye className="w-3 h-3" /> Preview
                        </button>

                        {!isSent ? (
                          <button
                            onClick={() => handleSendMessage(msg.id)}
                            disabled={isSending}
                            className="px-2.5 py-1 rounded bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white font-mono text-[10px] font-semibold flex items-center gap-1 shadow-sm transition-all"
                          >
                            {isSending ? <Loader2 className="w-3 h-3 animate-spin" /> : <Send className="w-3 h-3" />}
                            <span>Send Email Now</span>
                          </button>
                        ) : (
                          <span className="text-[10px] font-mono text-emerald-400 flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" /> Sent
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Message Preview & Quick Action Modal */}
      {selectedMessage && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-xl bg-surface-200 border border-white/10 rounded-2xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <div>
                <span className="text-[10px] font-mono text-brand-400 uppercase tracking-wider block">
                  Outreach Email Draft • Step {selectedMessage.step_number}
                </span>
                <h3 className="text-sm font-bold text-white truncate">{selectedMessage.subject}</h3>
              </div>
              <button
                onClick={() => setSelectedMessage(null)}
                className="text-zinc-400 hover:text-white p-1 rounded-lg hover:bg-white/5"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-3 rounded-lg bg-surface-300 text-xs font-mono text-zinc-400 space-y-1">
              <div><strong className="text-zinc-300">Channel:</strong> Direct Email</div>
              <div><strong className="text-zinc-300">Status:</strong> {selectedMessage.status}</div>
              <div><strong className="text-zinc-300">Scheduled:</strong> {new Date(selectedMessage.scheduled_for).toLocaleDateString()}</div>
            </div>

            <div className="bg-surface-400/80 p-4 rounded-xl border border-white/5 max-h-60 overflow-y-auto">
              <pre className="text-xs text-zinc-200 whitespace-pre-wrap font-sans leading-relaxed">
                {selectedMessage.body}
              </pre>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-white/5">
              <button
                onClick={() => copyToClipboard(selectedMessage.body)}
                className="text-xs text-zinc-400 hover:text-white flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied to Clipboard' : 'Copy Text'}</span>
              </button>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setSelectedMessage(null)}
                  className="px-4 py-2 rounded-lg text-xs font-medium text-zinc-400 hover:text-white"
                >
                  Close
                </button>
                {selectedMessage.status !== 'SENT' && (
                  <button
                    onClick={() => handleSendMessage(selectedMessage.id)}
                    disabled={sendingId === selectedMessage.id}
                    className="px-4 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white text-xs font-bold flex items-center gap-1.5 shadow-glow"
                  >
                    {sendingId === selectedMessage.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                    <span>Send Email Now</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

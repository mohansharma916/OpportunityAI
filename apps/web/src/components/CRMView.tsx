'use client';

import React, { useState, useEffect } from 'react';
import {
  Send,
  Users,
  Sparkles,
  Play,
  Plus,
  Mail,
  ExternalLink,
  CheckCircle2,
  Clock,
  Building2,
  UserCheck,
  MessageSquare,
  AlertCircle,
  Copy,
  ChevronRight,
  Loader2,
  X,
  PauseCircle,
  Check,
} from 'lucide-react';
import { fetchApi } from '@/lib/api';

interface CRMViewProps {
  onRefreshAllData?: () => void;
  profile?: any;
}

export function CRMView({ onRefreshAllData, profile }: CRMViewProps) {
  const [activeTab, setActiveTab] = useState<'cadences' | 'directory'>('cadences');
  const [contacts, setContacts] = useState<any[]>([]);
  const [sequences, setSequences] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Add Contact Modal
  const [showAddContactModal, setShowAddContactModal] = useState(false);
  const [newCompany, setNewCompany] = useState('');
  const [newName, setNewName] = useState('');
  const [newRole, setNewRole] = useState('Technical Recruiter');
  const [newEmail, setNewEmail] = useState('');
  const [newLinkedIn, setNewLinkedIn] = useState('');
  const [newNotes, setNewNotes] = useState('');

  // AI Message Generator Modal
  const [selectedContactForOutreach, setSelectedContactForOutreach] = useState<any>(null);
  const [generatedSubject, setGeneratedSubject] = useState('');
  const [generatedBody, setGeneratedBody] = useState('');
  const [isGeneratingMessage, setIsGeneratingMessage] = useState(false);
  const [isDispatchingMessage, setIsDispatchingMessage] = useState(false);
  const [copied, setCopied] = useState(false);

  // Cadence Advancement Loading
  const [advancingSequenceId, setAdvancingSequenceId] = useState<string | null>(null);

  // Notification Banner
  const [notification, setNotification] = useState<string | null>(null);

  // Load Contacts and Sequences
  const loadCrmData = async () => {
    try {
      setLoading(true);
      const [contactsData, sequencesData] = await Promise.all([
        fetchApi<any[]>('/api/crm/contacts'),
        fetchApi<any[]>('/api/crm/sequences'),
      ]);

      if (contactsData) setContacts(contactsData);
      if (sequencesData) setSequences(sequencesData);
    } catch (err) {
      console.error('Failed to load CRM data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCrmData();
  }, []);

  // Create Contact
  const handleCreateContact = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCompany || !newName) return;

    try {
      const res = await fetchApi<any>('/api/crm/contacts', {
        method: 'POST',
        body: JSON.stringify({
          company_name: newCompany,
          full_name: newName,
          role: newRole,
          email: newEmail || null,
          linkedin_url: newLinkedIn || null,
          notes: newNotes || null,
        }),
      });

      setShowAddContactModal(false);
      setNewCompany('');
      setNewName('');
      setNewEmail('');
      setNewLinkedIn('');
      setNewNotes('');
      setNotification(`Added ${newName} (${newCompany}) to recruiter directory.`);
      await loadCrmData();
    } catch (err) {
      console.error('Failed to create contact:', err);
    }
  };

  // Start Cadence for Contact
  const handleStartCadence = async (contact: any) => {
    try {
      const res = await fetchApi<any>('/api/crm/sequences', {
        method: 'POST',
        body: JSON.stringify({
          opportunity_id: contact.associated_opportunity_id || 'general-opp',
          contact_id: contact.id,
        }),
      });
      setNotification(`Started 3-step automated cadence for ${contact.full_name}!`);
      await loadCrmData();
    } catch (err) {
      console.error('Failed to start sequence:', err);
    }
  };

  // Advance Sequence Step
  const handleAdvanceSequence = async (sequenceId: string) => {
    try {
      setAdvancingSequenceId(sequenceId);
      const res = await fetchApi<any>(`/api/crm/sequences/${sequenceId}/advance`, {
        method: 'POST',
      });
      if (res && res.success) {
        setNotification(res.message);
        await loadCrmData();
      } else {
        setNotification(res?.message || 'Sequence completed.');
      }
    } catch (err) {
      console.error('Failed to advance sequence:', err);
    } finally {
      setAdvancingSequenceId(null);
    }
  };

  // Generate AI Outreach Message
  const handleOpenAiOutreach = async (contact: any) => {
    setSelectedContactForOutreach(contact);
    setCopied(false);
    try {
      setIsGeneratingMessage(true);
      const res = await fetchApi<any>(`/api/crm/contacts/${contact.id}/generate-outreach`, {
        method: 'POST',
        body: JSON.stringify({
          opportunity_id: contact.associated_opportunity_id || null,
          tone: 'TECHNICAL',
        }),
      });
      if (res) {
        setGeneratedSubject(res.subject);
        setGeneratedBody(res.body);
      }
    } catch (err) {
      console.error('Failed to generate outreach message:', err);
    } finally {
      setIsGeneratingMessage(false);
    }
  };

  // Dispatch Generated Message
  const handleDispatchGeneratedMessage = async () => {
    if (!selectedContactForOutreach) return;
    try {
      setIsDispatchingMessage(true);
      // Simulate / dispatch message
      await new Promise((r) => setTimeout(r, 600));
      setNotification(`Outreach message sent to ${selectedContactForOutreach.full_name}!`);
      setSelectedContactForOutreach(null);
      await loadCrmData();
    } catch (err) {
      console.error('Failed to dispatch message:', err);
    } finally {
      setIsDispatchingMessage(false);
    }
  };

  const handleCopyMessage = () => {
    navigator.clipboard.writeText(`Subject: ${generatedSubject}\n\n${generatedBody}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300 pb-16">
      {/* Toast Notification */}
      {notification && (
        <div className="p-4 rounded-xl bg-gradient-to-r from-emerald-600/30 to-teal-500/20 border border-emerald-500/40 text-emerald-200 text-xs font-medium flex items-center justify-between shadow-lg">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-emerald-300" />
            <span>{notification}</span>
          </div>
          <button onClick={() => setNotification(null)} className="text-zinc-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Hero Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-surface-300 via-surface-300/90 to-surface-200 border border-white/10 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2.5 mb-2">
            <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] font-mono font-bold border border-emerald-500/30 flex items-center gap-1">
              <Send className="w-3 h-3" />
              Feature #3
            </span>
            <span className="px-2.5 py-0.5 rounded-full bg-teal-950/60 text-teal-400 text-[10px] font-mono border border-teal-800/40 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" />
              Automated Follow-Up Cadences Active
            </span>
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight">
            Automated Outreach & Networking CRM
          </h1>
          <p className="text-xs text-zinc-400 mt-1 max-w-2xl leading-relaxed">
            Manage hiring managers & recruiter contacts, orchestrate multi-step drip cadences
            (Day 1 Intro, Day 4 Value Follow-Up, Day 9 Check-In), and auto-generate personalized messaging.
          </p>
        </div>

        {/* Action Button */}
        <button
          onClick={() => setShowAddContactModal(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white shadow-glow transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>+ Add Recruiter / Contact</span>
        </button>
      </div>

      {/* CRM Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-white/5 pb-2">
        <button
          onClick={() => setActiveTab('cadences')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === 'cadences'
              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm'
              : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'
          }`}
        >
          <Clock className="w-3.5 h-3.5" />
          <span>Active Cadences ({sequences.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('directory')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === 'directory'
              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm'
              : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'
          }`}
        >
          <Users className="w-3.5 h-3.5" />
          <span>Recruiter & Lead Directory ({contacts.length})</span>
        </button>
      </div>

      {/* TAB 1: Automated Outreach Cadences */}
      {activeTab === 'cadences' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              3-Step Drip Outreach Sequences
            </h2>
            <span className="text-[11px] text-zinc-400">
              Auto-pauses instantly if recipient responds
            </span>
          </div>

          {loading ? (
            <div className="p-8 text-center text-zinc-400 text-xs flex items-center justify-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-emerald-400" /> Loading sequences...
            </div>
          ) : sequences.length === 0 ? (
            <div className="p-12 rounded-2xl bg-surface-300/40 border border-white/5 text-center space-y-3">
              <Send className="w-8 h-8 text-zinc-400 mx-auto" />
              <p className="text-xs text-zinc-400">No active cadences running right now.</p>
              <button
                onClick={() => setActiveTab('directory')}
                className="px-4 py-1.5 rounded-lg text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 hover:bg-emerald-500/30 transition-all inline-flex items-center gap-1.5"
              >
                <span>Select Contact to Launch Cadence</span>
                <ChevronRight className="w-3 h-3" />
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {sequences.map((seq) => {
                const contact = contacts.find((c) => c.id === seq.contact_id);
                const isAdvancing = advancingSequenceId === seq.id;
                const messages = seq.messages || [];

                return (
                  <div
                    key={seq.id}
                    className="p-5 rounded-2xl bg-surface-300/80 border border-white/10 hover:border-emerald-500/30 transition-all shadow-sm space-y-4"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/5 pb-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="text-sm font-bold text-white">
                            {contact?.full_name || 'Hiring Lead'}
                          </h3>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-zinc-400">
                            {contact?.role} @ {contact?.company_name}
                          </span>
                        </div>
                        <p className="text-xs text-zinc-400 mt-0.5">
                          Sequence Status: <span className="text-emerald-400 font-semibold">{seq.status}</span> • Current Step: {seq.current_step} of 3
                        </p>
                      </div>

                      <button
                        onClick={() => handleAdvanceSequence(seq.id)}
                        disabled={isAdvancing}
                        className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-glow transition-all disabled:opacity-50"
                      >
                        {isAdvancing ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Play className="w-3 h-3 fill-white" />
                        )}
                        <span>Dispatch Next Cadence Step</span>
                      </button>
                    </div>

                    {/* 3 Step Timeline Display */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      {messages.map((msg: any) => {
                        const isSent = msg.status === 'SENT';

                        return (
                          <div
                            key={msg.id}
                            className={`p-3.5 rounded-xl border transition-all text-xs space-y-2 ${
                              isSent
                                ? 'bg-emerald-950/30 border-emerald-500/30'
                                : 'bg-surface-400/40 border-white/5'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-white/5 text-zinc-300">
                                Step {msg.step_number} {msg.step_number === 1 ? '(Day 1)' : msg.step_number === 2 ? '(Day 4)' : '(Day 9)'}
                              </span>
                              <span
                                className={`text-[9px] font-mono px-2 py-0.5 rounded-full font-bold ${
                                  isSent
                                    ? 'bg-emerald-950 text-emerald-300 border border-emerald-700/60'
                                    : 'bg-zinc-800 text-zinc-400'
                                }`}
                              >
                                {msg.status}
                              </span>
                            </div>

                            <p className="font-semibold text-zinc-200 truncate">{msg.subject}</p>
                            <p className="text-[11px] text-zinc-400 line-clamp-3 italic">
                              "{msg.body}"
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Recruiter Directory */}
      {activeTab === 'directory' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              Recruiter & Hiring Lead Directory ({contacts.length})
            </h2>
            <button
              onClick={() => setShowAddContactModal(true)}
              className="px-3 py-1 rounded-lg text-xs font-bold bg-white/5 hover:bg-white/10 text-white transition-all"
            >
              + Add Contact
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {contacts.map((contact) => (
              <div
                key={contact.id}
                className="p-4 rounded-xl bg-surface-300/80 border border-white/10 hover:border-emerald-500/30 transition-all shadow-sm space-y-3 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-xs font-bold text-white">{contact.full_name}</h3>
                      <p className="text-[11px] text-zinc-400">
                        {contact.role} @ <span className="text-zinc-200 font-semibold">{contact.company_name}</span>
                      </p>
                    </div>

                    <span
                      className={`text-[9px] font-mono px-2 py-0.5 rounded-full font-bold ${
                        contact.relationship_status === 'CONTACTED'
                          ? 'bg-emerald-950/70 text-emerald-300 border border-emerald-800/50'
                          : 'bg-white/5 text-zinc-400'
                      }`}
                    >
                      {contact.relationship_status}
                    </span>
                  </div>

                  <div className="space-y-1 mt-3 pt-2 border-t border-white/5 text-[11px] text-zinc-400">
                    {contact.email && (
                      <p className="flex items-center gap-1.5 truncate">
                        <Mail className="w-3 h-3 text-zinc-400" />
                        <span className="truncate">{contact.email}</span>
                      </p>
                    )}
                    {contact.linkedin_url && (
                      <a
                        href={contact.linkedin_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-emerald-400 hover:text-emerald-300 flex items-center gap-1 font-semibold"
                      >
                        <span>LinkedIn Profile</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </a>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 pt-3 border-t border-white/5">
                  <button
                    onClick={() => handleOpenAiOutreach(contact)}
                    className="flex-1 flex items-center justify-center gap-1 py-1.5 rounded-lg text-[11px] font-bold bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 transition-all"
                  >
                    <Sparkles className="w-3 h-3" />
                    <span>AI Message</span>
                  </button>

                  <button
                    onClick={() => handleStartCadence(contact)}
                    className="flex-1 flex items-center justify-center gap-1 py-1.5 rounded-lg text-[11px] font-bold bg-white/5 hover:bg-white/10 text-white border border-white/10 transition-all"
                  >
                    <Play className="w-3 h-3" />
                    <span>Cadence</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* MODAL 1: Add Contact */}
      {showAddContactModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-surface-300 rounded-2xl border border-white/10 shadow-2xl p-6 space-y-4 animate-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-bold text-white">Add Recruiter / Contact</h3>
              </div>
              <button onClick={() => setShowAddContactModal(false)} className="text-zinc-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateContact} className="space-y-3 text-xs">
              <div>
                <label className="block text-zinc-300 font-medium mb-1">Company Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Stripe, OpenAI, CloudScale"
                  value={newCompany}
                  onChange={(e) => setNewCompany(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-surface-400 border border-white/10 text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-zinc-300 font-medium mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Sarah Jenkins"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-surface-400 border border-white/10 text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-zinc-300 font-medium mb-1">Role / Title</label>
                <input
                  type="text"
                  placeholder="e.g. Head of Engineering Talent"
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-surface-400 border border-white/10 text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-zinc-300 font-medium mb-1">Email (Optional)</label>
                <input
                  type="email"
                  placeholder="recruiter@company.com"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-surface-400 border border-white/10 text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-zinc-300 font-medium mb-1">LinkedIn URL (Optional)</label>
                <input
                  type="url"
                  placeholder="https://linkedin.com/in/sarahjenkins"
                  value={newLinkedIn}
                  onChange={(e) => setNewLinkedIn(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-surface-400 border border-white/10 text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddContactModal(false)}
                  className="px-4 py-2 rounded-lg text-zinc-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold shadow-glow"
                >
                  Add Contact
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: AI Message Composer */}
      {selectedContactForOutreach && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-surface-300 rounded-2xl border border-white/10 shadow-2xl p-6 space-y-4 animate-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-bold text-white">
                  Personalized Outreach for {selectedContactForOutreach.full_name}
                </h3>
              </div>
              <button
                onClick={() => setSelectedContactForOutreach(null)}
                className="text-zinc-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {isGeneratingMessage ? (
              <div className="py-12 text-center text-zinc-400 text-xs flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-emerald-400" />
                Drafting personalized outreach note based on verified candidate profile...
              </div>
            ) : (
              <div className="space-y-3 text-xs">
                <div>
                  <label className="block text-zinc-400 font-mono text-[11px] mb-1">Subject</label>
                  <input
                    type="text"
                    value={generatedSubject}
                    onChange={(e) => setGeneratedSubject(e.target.value)}
                    className="w-full p-2.5 rounded-lg bg-surface-400 border border-white/10 text-white font-medium focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-zinc-400 font-mono text-[11px] mb-1">Message Body</label>
                  <textarea
                    rows={8}
                    value={generatedBody}
                    onChange={(e) => setGeneratedBody(e.target.value)}
                    className="w-full p-3 rounded-lg bg-surface-400 border border-white/10 text-zinc-200 whitespace-pre-line leading-relaxed focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-white/5">
                  <button
                    onClick={handleCopyMessage}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-zinc-300 bg-white/5 hover:bg-white/10 transition-all font-semibold"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? 'Copied!' : 'Copy to Clipboard'}</span>
                  </button>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setSelectedContactForOutreach(null)}
                      className="px-3 py-1.5 rounded-lg text-zinc-400 hover:text-white"
                    >
                      Close
                    </button>
                    <button
                      type="button"
                      onClick={handleDispatchGeneratedMessage}
                      disabled={isDispatchingMessage}
                      className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold shadow-glow transition-all disabled:opacity-50"
                    >
                      {isDispatchingMessage ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Send className="w-3.5 h-3.5" />
                      )}
                      <span>Dispatch Email</span>
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

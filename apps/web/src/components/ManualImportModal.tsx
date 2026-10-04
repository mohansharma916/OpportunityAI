'use client';

import React, { useState } from 'react';
import { X, Sparkles, Link, FileText, Building, Loader2 } from 'lucide-react';
import { fetchApi } from '@/lib/api';

interface ManualImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportSuccess: (opp: any) => void;
}

export function ManualImportModal({
  isOpen,
  onClose,
  onImportSuccess,
}: ManualImportModalProps) {
  const [url, setUrl] = useState('');
  const [title, setTitle] = useState('');
  const [company, setCompany] = useState('');
  const [body, setBody] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!body.trim() && !url.trim()) return;

    setLoading(true);
    try {
      const opp = await fetchApi<any>('/api/opportunities/import', {
        method: 'POST',
        body: JSON.stringify({
          url: url || undefined,
          title: title || undefined,
          company: company || undefined,
          body: body || `Listing from ${url}`,
        }),
      });
      onImportSuccess(opp);
      onClose();
    } catch (err: any) {
      alert(`Import error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-xl bg-surface-200 border border-white/10 rounded-2xl shadow-2xl overflow-hidden glass-panel animate-in fade-in zoom-in-95 duration-150">
        <div className="p-5 border-b border-white/5 flex items-center justify-between bg-surface-300/40">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-brand-500/10 border border-brand-500/20 text-brand-400">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Import Opportunity</h2>
              <p className="text-[11px] text-zinc-400">
                Paste any job URL, recruiter email, or job description
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/5 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="text-[11px] font-medium text-zinc-300 block mb-1">
              Job URL (Optional)
            </label>
            <div className="relative">
              <Link className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://company.com/careers/lead-engineer"
                className="w-full bg-surface-300 border border-white/10 rounded-lg pl-8 pr-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-500/50"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[11px] font-medium text-zinc-300 block mb-1">
                Company Name (Optional)
              </label>
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder="e.g. Stripe, Linear"
                className="w-full bg-surface-300 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-500/50"
              />
            </div>
            <div>
              <label className="text-[11px] font-medium text-zinc-300 block mb-1">
                Role Title (Optional)
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Senior Full Stack Architect"
                className="w-full bg-surface-300 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-500/50"
              />
            </div>
          </div>

          <div>
            <label className="text-[11px] font-medium text-zinc-300 block mb-1">
              Job Description / Recruiter Note <span className="text-brand-400">*</span>
            </label>
            <textarea
              required
              rows={6}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Paste full text here... The parsing engine will automatically extract compensation, remote terms, and requirements."
              className="w-full bg-surface-300 border border-white/10 rounded-lg p-3 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-500/50 leading-relaxed"
            />
          </div>

          <div className="pt-3 border-t border-white/5 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-xs font-medium text-zinc-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-xs font-semibold text-white shadow-glow transition-all flex items-center gap-1.5"
            >
              {loading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Parsing & Scoring...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Ingest & Deep Score</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

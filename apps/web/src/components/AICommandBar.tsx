'use client';

import React, { useState } from 'react';
import { Sparkles, Terminal, ArrowRight, CheckCircle2, Loader2, X } from 'lucide-react';
import { fetchApi } from '@/lib/api';

interface AICommandBarProps {
  isOpen: boolean;
  onClose: () => void;
  onCommandExecuted: () => void;
}

export function AICommandBar({ isOpen, onClose, onCommandExecuted }: AICommandBarProps) {
  const [command, setCommand] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  if (!isOpen) return null;

  const quickPrompts = [
    'Prepare applications for everything above 85% match',
    'Increase minimum contract rate to $95/hour',
    'Discover new global opportunities',
    'Find open source projects and paid bounties',
    'Set automation level to 4',
  ];

  const handleExecute = async (promptToRun: string) => {
    if (!promptToRun.trim() || loading) return;
    setLoading(true);
    setResult(null);
    try {
      const data = await fetchApi<any>('/api/ai/command', {
        method: 'POST',
        body: JSON.stringify({ command: promptToRun }),
      });
      setResult(data);
      onCommandExecuted();
    } catch (err: any) {
      setResult({ action: 'ERROR', message: err.message || 'Execution failed' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-start justify-center pt-24 p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-2xl bg-surface-200 border border-white/10 rounded-xl shadow-2xl overflow-hidden glass-panel">
        {/* Command Input Header */}
        <div className="p-4 border-b border-white/5 flex items-center gap-3">
          <Sparkles className="w-5 h-5 text-brand-400 animate-pulse" />
          <input
            type="text"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleExecute(command);
              if (e.key === 'Escape') onClose();
            }}
            placeholder="Type an AI command (e.g. 'Prepare applications for everything above 85% match')..."
            autoFocus
            className="w-full bg-transparent text-sm text-white placeholder-zinc-500 focus:outline-none"
          />
          <button
            onClick={onClose}
            className="text-zinc-500 hover:text-zinc-300 transition-colors p-1"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Quick Suggestion Pills */}
        <div className="p-3 bg-surface-300/40 border-b border-white/5 flex flex-wrap gap-1.5">
          <span className="text-[11px] text-zinc-500 flex items-center gap-1 mr-1">
            <Terminal className="w-3 h-3" /> Quick commands:
          </span>
          {quickPrompts.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => {
                setCommand(prompt);
                handleExecute(prompt);
              }}
              className="text-[11px] px-2.5 py-1 rounded bg-white/[0.04] text-zinc-300 hover:bg-brand-500/20 hover:text-brand-300 border border-white/5 hover:border-brand-500/30 transition-all text-left"
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Loading / Result Area */}
        {loading && (
          <div className="p-6 flex items-center justify-center gap-3 text-zinc-400 text-xs">
            <Loader2 className="w-4 h-4 animate-spin text-brand-400" />
            Analyzing intent and executing backend orchestration...
          </div>
        )}

        {result && !loading && (
          <div className="p-4 bg-brand-950/20 border-t border-brand-500/20">
            <div className="flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider block font-mono">
                  {result.action}
                </span>
                <p className="text-xs text-zinc-200 mt-0.5">{result.message}</p>
              </div>
            </div>
          </div>
        )}

        {/* Footer info */}
        <div className="px-4 py-2 bg-surface-400/80 border-t border-white/5 flex items-center justify-between text-[11px] text-zinc-500 font-mono">
          <span>Press Enter to execute</span>
          <span>Esc to dismiss</span>
        </div>
      </div>
    </div>
  );
}

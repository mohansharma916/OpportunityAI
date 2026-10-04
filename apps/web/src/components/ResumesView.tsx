'use client';

import React from 'react';
import { FileText, Sparkles, Download, CheckCircle2, Hash } from 'lucide-react';

interface ResumesViewProps {
  resumes: any[];
}

export function ResumesView({ resumes }: ResumesViewProps) {
  return (
    <div className="space-y-6">
      <div className="pb-3 border-b border-white/5">
        <h2 className="text-base font-semibold text-white tracking-tight flex items-center gap-2">
          <FileText className="w-4 h-4 text-cyan-400" />
          Targeted Resume Engine & Generated Variants
        </h2>
        <p className="text-xs text-zinc-400 mt-0.5">
          Grounded variants compiled from Master Knowledge Base. Zero hallucinated employment or dates.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {resumes.map((r) => (
          <div
            key={r.id}
            className="p-5 rounded-xl bg-surface-300/40 border border-white/5 space-y-3 glass-card"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/40">
                  Targeted Variant
                </span>
                <h3 className="text-sm font-bold text-white mt-1.5">{r.variant_name}</h3>
                <p className="text-xs text-brand-300 font-medium mt-0.5">{r.headline}</p>
              </div>
              <span className="text-[10px] font-mono text-zinc-500 bg-white/5 px-2 py-1 rounded">
                #{r.content_hash?.slice(0, 8)}
              </span>
            </div>

            <p className="text-xs text-zinc-300 leading-relaxed font-sans line-clamp-3">
              {r.summary}
            </p>

            <div className="pt-2 border-t border-white/5">
              <span className="text-[10px] text-zinc-500 uppercase font-mono block mb-1">
                Prioritized Skills:
              </span>
              <div className="flex flex-wrap gap-1">
                {(r.selected_skills || []).slice(0, 6).map((sk: string, idx: number) => (
                  <span
                    key={idx}
                    className="text-[9px] font-mono bg-cyan-500/10 text-cyan-300 px-1.5 py-0.5 rounded border border-cyan-500/20"
                  >
                    {sk}
                  </span>
                ))}
              </div>
            </div>

            <div className="pt-3 border-t border-white/5 flex items-center justify-between text-xs text-zinc-400">
              <span className="text-[10px] font-mono text-zinc-500">
                {new Date(r.generated_at).toLocaleDateString()}
              </span>
              <button className="text-brand-400 hover:text-brand-300 font-medium flex items-center gap-1 text-[11px]">
                <Download className="w-3 h-3" /> Export Clean Typography
              </button>
            </div>
          </div>
        ))}

        {resumes.length === 0 && (
          <div className="col-span-full p-12 text-center text-zinc-500 text-xs border border-dashed border-white/5 rounded-xl">
            No targeted variants generated yet. Open any opportunity to prepare a role-specific resume.
          </div>
        )}
      </div>
    </div>
  );
}

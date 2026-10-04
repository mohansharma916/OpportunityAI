'use client';

import React, { useState } from 'react';
import {
  Send,
  CheckCircle2,
  Clock,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Plus,
  Filter,
  Search,
  Sparkles,
  Building,
  FileText,
  AlertCircle,
  Check,
  X,
  Loader2,
  Calendar,
  Layers,
  ArrowRight,
} from 'lucide-react';
import { fetchApi } from '@/lib/api';

interface ApplicationsTrackerViewProps {
  opportunities: any[];
  onSelectApplication: (app: any) => void;
  onRefreshData: () => void;
}

export function ApplicationsTrackerView({
  opportunities,
  onSelectApplication,
  onRefreshData,
}: ApplicationsTrackerViewProps) {
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [expandedAppId, setExpandedAppId] = useState<string | null>(null);

  // New Task input state per application: { [appId]: string }
  const [newTaskInput, setNewTaskInput] = useState<{ [appId: string]: string }>({});
  const [loadingAction, setLoadingAction] = useState<string | null>(null);

  // Extract all opportunities with applications
  const applications = opportunities
    .filter((o: any) => o.application)
    .map((o: any) => ({
      ...o.application,
      opportunity: o,
    }));

  const filteredApps = applications.filter((app) => {
    const opp = app.opportunity || {};
    const matchesSearch =
      (opp.title || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (opp.company_name || '').toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;
    if (statusFilter === 'ALL') return true;
    return app.status === statusFilter;
  });

  const handleStatusChange = async (appId: string, newStatus: string) => {
    setLoadingAction(`status-${appId}`);
    try {
      await fetchApi(`/api/applications/${appId}/status`, {
        method: 'PUT',
        body: JSON.stringify({ status: newStatus }),
      });
      onRefreshData();
    } catch (err: any) {
      alert(`Failed to update status: ${err.message}`);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleToggleTask = async (appId: string, taskId: string) => {
    setLoadingAction(`task-${taskId}`);
    try {
      await fetchApi(`/api/applications/${appId}/tasks/${taskId}`, {
        method: 'PUT',
      });
      onRefreshData();
    } catch (err: any) {
      alert(`Failed to toggle task: ${err.message}`);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleAddTask = async (appId: string) => {
    const title = (newTaskInput[appId] || '').trim();
    if (!title) return;
    setLoadingAction(`add-task-${appId}`);
    try {
      await fetchApi(`/api/applications/${appId}/tasks`, {
        method: 'POST',
        body: JSON.stringify({ title }),
      });
      setNewTaskInput({ ...newTaskInput, [appId]: '' });
      onRefreshData();
    } catch (err: any) {
      alert(`Failed to add task: ${err.message}`);
    } finally {
      setLoadingAction(null);
    }
  };

  // Metrics
  const totalApps = applications.length;
  const needsApproval = applications.filter((a) => a.status === 'NEEDS_APPROVAL').length;
  const autoApplied = applications.filter((a) => a.status === 'AUTO_APPLIED' || a.submission_mode === 'AUTO').length;
  const submitted = applications.filter((a) => a.status === 'SUBMITTED').length;
  const interviewing = applications.filter((a) => a.status === 'INTERVIEWING').length;

  return (
    <div className="space-y-6">
      {/* Header & KPI Summary */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-surface-100 to-surface-200 border border-white/10 glass-panel space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
              <Send className="w-5 h-5 text-emerald-400" />
              Application Tracker & Attached Task Pipeline
            </h2>
            <p className="text-xs text-zinc-400 mt-0.5 font-sans">
              Track submission status, review packages, and manage lifecycle tasks for every opportunity.
            </p>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2 border-t border-white/5">
          <div className="p-3 rounded-xl bg-surface-300/40 border border-white/5">
            <span className="text-[10px] text-zinc-400 font-mono block">Total Tracked</span>
            <span className="text-lg font-bold text-white font-mono">{totalApps}</span>
          </div>
          <div className="p-3 rounded-xl bg-surface-300/40 border border-amber-500/20">
            <span className="text-[10px] text-amber-400 font-mono block">Needs Approval</span>
            <span className="text-lg font-bold text-amber-300 font-mono">{needsApproval}</span>
          </div>
          <div className="p-3 rounded-xl bg-surface-300/40 border border-cyan-500/20">
            <span className="text-[10px] text-cyan-400 font-mono block">Auto-Applied</span>
            <span className="text-lg font-bold text-cyan-300 font-mono">{autoApplied}</span>
          </div>
          <div className="p-3 rounded-xl bg-surface-300/40 border border-emerald-500/20">
            <span className="text-[10px] text-emerald-400 font-mono block">Submitted</span>
            <span className="text-lg font-bold text-emerald-300 font-mono">{submitted}</span>
          </div>
          <div className="p-3 rounded-xl bg-surface-300/40 border border-purple-500/20">
            <span className="text-[10px] text-purple-400 font-mono block">Interviewing</span>
            <span className="text-lg font-bold text-purple-300 font-mono">{interviewing}</span>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Status Pills */}
        <div className="flex flex-wrap gap-1.5 p-1 bg-surface-300/60 rounded-xl border border-white/5">
          {[
            { id: 'ALL', label: 'All' },
            { id: 'NEEDS_APPROVAL', label: 'Needs Approval' },
            { id: 'AUTO_APPLIED', label: 'Auto-Applied' },
            { id: 'SUBMITTED', label: 'Submitted' },
            { id: 'INTERVIEWING', label: 'Interviewing' },
            { id: 'OFFERED', label: 'Offered' },
            { id: 'REJECTED', label: 'Rejected' },
          ].map((pill) => (
            <button
              key={pill.id}
              type="button"
              onClick={() => setStatusFilter(pill.id)}
              className={`px-3 py-1 text-xs font-mono rounded-lg transition-all ${
                statusFilter === pill.id
                  ? 'bg-brand-500 text-white font-medium shadow-sm'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              {pill.label}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by company or role..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-surface-300/80 border border-white/10 rounded-xl pl-9 pr-3 py-1.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-500/50"
          />
        </div>
      </div>

      {/* Applications Cards List */}
      <div className="space-y-4">
        {filteredApps.length === 0 ? (
          <div className="p-12 text-center text-zinc-500 rounded-2xl bg-surface-300/20 border border-white/5 space-y-2">
            <Send className="w-8 h-8 mx-auto opacity-30" />
            <p className="text-sm font-mono">No applications matching current filters.</p>
            <span className="text-xs text-zinc-600 block">
              Discover opportunities and click "Prepare Application" or run the Autonomous Crawler to populate your pipeline.
            </span>
          </div>
        ) : (
          filteredApps.map((app: any) => {
            const opp = app.opportunity || {};
            const isExpanded = expandedAppId === app.id;
            const tasks = app.tasks || [];
            const completedTasks = tasks.filter((t: any) => t.status === 'COMPLETED').length;
            const totalTasks = tasks.length;
            const score = opp.matching_score?.overall_match_score || 0;

            const statusColors: Record<string, string> = {
              NEEDS_APPROVAL: 'bg-amber-950/40 text-amber-300 border-amber-500/30',
              AUTO_APPLIED: 'bg-cyan-950/40 text-cyan-300 border-cyan-500/30',
              SUBMITTED: 'bg-emerald-950/40 text-emerald-300 border-emerald-500/30',
              INTERVIEWING: 'bg-purple-950/40 text-purple-300 border-purple-500/30',
              OFFERED: 'bg-emerald-500/20 text-emerald-300 border-emerald-400',
              REJECTED: 'bg-rose-950/40 text-rose-300 border-rose-500/30',
              PREPARED: 'bg-blue-950/40 text-blue-300 border-blue-500/30',
            };

            return (
              <div
                key={app.id}
                className="rounded-2xl bg-surface-300/40 border border-white/10 hover:border-brand-500/30 transition-all overflow-hidden shadow-sm"
              >
                {/* Main Row */}
                <div className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-1.5 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-bold text-white hover:text-brand-300 transition-colors">
                        {opp.title}
                      </span>
                      <span className="text-xs text-zinc-400 font-medium">
                        at {opp.company_name}
                      </span>
                      {score > 0 && (
                        <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40">
                          {score.toFixed(0)}% Match
                        </span>
                      )}
                      <span className="text-[10px] font-mono text-zinc-400 bg-white/5 px-2 py-0.5 rounded">
                        {opp.source || 'WEB'}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-xs text-zinc-400 font-mono">
                      <span>Created: {new Date(app.created_at).toLocaleDateString()}</span>
                      {app.submitted_at && (
                        <span className="text-emerald-400">
                          Submitted: {new Date(app.submitted_at).toLocaleDateString()}
                        </span>
                      )}
                      <span>Mode: {app.submission_mode}</span>
                      {totalTasks > 0 && (
                        <span className="text-cyan-400">
                          Tasks: {completedTasks}/{totalTasks} Done
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions & Status Selector */}
                  <div className="flex flex-wrap items-center gap-3">
                    {/* Status Dropdown */}
                    <div className="flex items-center gap-1.5">
                      <span className="text-[11px] text-zinc-400 font-mono">Status:</span>
                      <select
                        value={app.status}
                        disabled={loadingAction === `status-${app.id}`}
                        onChange={(e) => handleStatusChange(app.id, e.target.value)}
                        className={`text-xs font-mono font-semibold rounded-lg px-2.5 py-1.5 border focus:outline-none cursor-pointer ${
                          statusColors[app.status] || 'bg-surface-400 text-white border-white/10'
                        }`}
                      >
                        <option value="NEEDS_APPROVAL">Needs Approval</option>
                        <option value="AUTO_APPLIED">Auto-Applied</option>
                        <option value="SUBMITTED">Submitted</option>
                        <option value="INTERVIEWING">Interviewing</option>
                        <option value="OFFERED">Offered</option>
                        <option value="REJECTED">Rejected</option>
                      </select>
                    </div>

                    {/* Review Button */}
                    <button
                      type="button"
                      onClick={() => onSelectApplication(app)}
                      className="px-3 py-1.5 text-xs font-mono bg-brand-500/20 hover:bg-brand-500/30 text-brand-300 border border-brand-500/40 rounded-lg flex items-center gap-1 transition-colors"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      Review
                    </button>

                    {/* External Link */}
                    {opp.url && (
                      <a
                        href={opp.url}
                        target="_blank"
                        rel="noreferrer"
                        className="p-2 text-zinc-400 hover:text-white bg-white/5 hover:bg-white/10 rounded-lg border border-white/5 transition-colors"
                        title="Open posting"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}

                    {/* Expand Tasks Toggle */}
                    <button
                      type="button"
                      onClick={() => setExpandedAppId(isExpanded ? null : app.id)}
                      className="flex items-center gap-1 text-xs font-mono text-zinc-400 hover:text-white px-2 py-1.5 rounded bg-white/5"
                    >
                      <span>Tasks</span>
                      {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>

                {/* Attached Tasks Checklist Panel */}
                {isExpanded && (
                  <div className="px-5 pb-5 pt-3 border-t border-white/5 bg-surface-400/30 space-y-3 animate-in fade-in duration-150">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-zinc-300 font-mono flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-brand-400" />
                        Attached Pipeline Tasks ({completedTasks}/{totalTasks} Completed)
                      </span>
                    </div>

                    {/* Tasks List */}
                    <div className="space-y-1.5">
                      {tasks.map((task: any) => {
                        const isDone = task.status === 'COMPLETED';
                        return (
                          <div
                            key={task.id}
                            onClick={() => handleToggleTask(app.id, task.id)}
                            className={`p-2.5 rounded-xl border text-xs font-mono flex items-center justify-between cursor-pointer transition-all ${
                              isDone
                                ? 'bg-emerald-950/20 border-emerald-500/20 text-zinc-300'
                                : 'bg-surface-300/50 border-white/5 text-zinc-400 hover:border-white/10'
                            }`}
                          >
                            <div className="flex items-center gap-2.5">
                              <div
                                className={`w-4 h-4 rounded flex items-center justify-center border transition-colors ${
                                  isDone
                                    ? 'bg-emerald-500 border-emerald-400 text-white'
                                    : 'border-white/20 bg-surface-400'
                                }`}
                              >
                                {isDone && <Check className="w-3 h-3 stroke-[3]" />}
                              </div>
                              <span className={isDone ? 'line-through text-zinc-400' : 'text-zinc-200'}>
                                {task.title}
                              </span>
                            </div>

                            {task.completed_at && (
                              <span className="text-[10px] text-zinc-500">
                                {task.completed_at}
                              </span>
                            )}
                          </div>
                        );
                      })}
                    </div>

                    {/* Add Custom Task Input */}
                    <div className="flex items-center gap-2 pt-2 border-t border-white/5">
                      <input
                        type="text"
                        placeholder="Add custom task (e.g. Schedule screening call with tech lead)..."
                        value={newTaskInput[app.id] || ''}
                        onChange={(e) =>
                          setNewTaskInput({ ...newTaskInput, [app.id]: e.target.value })
                        }
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            handleAddTask(app.id);
                          }
                        }}
                        className="flex-1 bg-surface-400 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-500/50"
                      />
                      <button
                        type="button"
                        onClick={() => handleAddTask(app.id)}
                        className="text-xs font-mono bg-white/5 hover:bg-white/10 text-zinc-200 border border-white/10 px-3 py-1.5 rounded-lg flex items-center gap-1 transition-colors"
                      >
                        <Plus className="w-3 h-3" /> Add Task
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

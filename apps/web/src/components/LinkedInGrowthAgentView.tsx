'use client';

import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Zap,
  TrendingUp,
  ShieldCheck,
  Send,
  UserCheck,
  MessageSquare,
  FileText,
  Building2,
  Calendar,
  Layers,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ArrowRight,
  RefreshCw,
  Plus,
  Compass,
  Award,
  Search,
  ExternalLink,
  ChevronRight,
  Filter,
  Check,
  X,
  Edit3,
  Flame,
  Brain,
  Sliders,
  Code2,
  Terminal,
} from 'lucide-react';
import { fetchApi } from '@/lib/api';

interface LinkedInGrowthAgentViewProps {
  onRefreshAllData?: () => void;
  profile?: any;
}

export function LinkedInGrowthAgentView({ onRefreshAllData, profile }: LinkedInGrowthAgentViewProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'approvals' | 'optimizer' | 'content' | 'network' | 'comments' | 'companies'>('overview');
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Core Data States
  const [dashboard, setDashboard] = useState<any>(null);
  const [profileOptimizer, setProfileOptimizer] = useState<any>(null);
  const [brandStrategy, setBrandStrategy] = useState<any>(null);
  const [contentPosts, setContentPosts] = useState<any[]>([]);
  const [relationships, setRelationships] = useState<any[]>([]);
  const [commentOpportunities, setCommentOpportunities] = useState<any[]>([]);
  const [companies, setCompanies] = useState<any[]>([]);
  const [pendingActions, setPendingActions] = useState<any[]>([]);

  // Interactive Command Bar State
  const [commandInput, setCommandInput] = useState('');
  const [commandResult, setCommandResult] = useState<any>(null);

  // New Post Generation Modal
  const [showGeneratePostModal, setShowGeneratePostModal] = useState(false);
  const [postTopicInput, setPostTopicInput] = useState('');
  const [postPillarInput, setPostPillarInput] = useState('Technical Deep-Dives');
  const [postTypeInput, setPostTypeInput] = useState('TECHNICAL_BREAKDOWN');

  // Knowledge Post Generation Modal
  const [showKnowledgeModal, setShowKnowledgeModal] = useState(false);
  const [knowledgeInput, setKnowledgeInput] = useState('');

  // Initial Data Fetch
  const loadAllLinkedInData = async () => {
    try {
      setLoading(true);
      const [dash, opt, strat, posts, rels, comms, comps, approvals] = await Promise.all([
        fetchApi<any>('/api/linkedin/dashboard'),
        fetchApi<any>('/api/linkedin/profile-optimizer'),
        fetchApi<any>('/api/linkedin/brand-strategy'),
        fetchApi<any[]>('/api/linkedin/content'),
        fetchApi<any[]>('/api/linkedin/relationships'),
        fetchApi<any[]>('/api/linkedin/comment-opportunities'),
        fetchApi<any[]>('/api/linkedin/companies'),
        fetchApi<any[]>('/api/linkedin/actions/approvals'),
      ]);

      setDashboard(dash);
      setProfileOptimizer(opt);
      setBrandStrategy(strat);
      setContentPosts(posts || []);
      setRelationships(rels || []);
      setCommentOpportunities(comms || []);
      setCompanies(comps || []);
      setPendingActions(approvals || []);
    } catch (err) {
      console.error('Failed to load LinkedIn AI Agent data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllLinkedInData();
  }, []);

  // Run AI Decision Cycle
  const handleRunDecisionCycle = async () => {
    try {
      setActionLoading('cycle');
      const res = await fetchApi<any>('/api/linkedin/agent/run-cycle', { method: 'POST' });
      await loadAllLinkedInData();
      alert(`AI Decision Planner Cycle Complete: ${res.decision} (${res.target || res.reasoning})`);
    } catch (err: any) {
      alert(`Decision cycle failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Execute Natural Language Command
  const handleExecuteCommand = async (promptText?: string) => {
    const textToRun = promptText || commandInput;
    if (!textToRun.trim()) return;

    try {
      setActionLoading('command');
      const res = await fetchApi<any>('/api/linkedin/command', {
        method: 'POST',
        body: JSON.stringify({ prompt: textToRun }),
      });
      setCommandResult(res);
      setCommandInput('');
      await loadAllLinkedInData();
    } catch (err: any) {
      alert(`Command execution failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Handle Approval Inbox Decision
  const handleDecideAction = async (actionId: string, decision: 'APPROVE' | 'REJECT' | 'LATER') => {
    try {
      setActionLoading(actionId);
      await fetchApi<any>(`/api/linkedin/actions/${actionId}/decide`, {
        method: 'POST',
        body: JSON.stringify({ decision }),
      });
      await loadAllLinkedInData();
    } catch (err: any) {
      alert(`Action decision failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Apply Profile Optimization Recommendation
  const handleApplyProfileOpt = async (field: string, value: string) => {
    try {
      setActionLoading(`opt-${field}`);
      await fetchApi<any>('/api/linkedin/profile-optimizer/apply', {
        method: 'POST',
        body: JSON.stringify({ field, value }),
      });
      alert(`Successfully applied recommended ${field} to your candidate profile!`);
      await loadAllLinkedInData();
      onRefreshAllData?.();
    } catch (err: any) {
      alert(`Failed to apply optimization: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Generate New Post
  const handleCreatePost = async () => {
    if (!postTopicInput.trim()) return;
    try {
      setActionLoading('gen_post');
      await fetchApi<any>('/api/linkedin/content/generate', {
        method: 'POST',
        body: JSON.stringify({
          custom_topic: postTopicInput.trim(),
          topic_pillar: postPillarInput,
          post_type: postTypeInput,
        }),
      });
      setShowGeneratePostModal(false);
      setPostTopicInput('');
      await loadAllLinkedInData();
    } catch (err: any) {
      alert(`Failed to generate post: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Generate from Knowledge
  const handleCreateFromKnowledge = async () => {
    if (!knowledgeInput.trim()) return;
    try {
      setActionLoading('gen_knowledge');
      await fetchApi<any>('/api/linkedin/content/from-knowledge', {
        method: 'POST',
        body: JSON.stringify({
          knowledge_input: knowledgeInput.trim(),
          source_type: 'GITHUB_COMMIT',
        }),
      });
      setShowKnowledgeModal(false);
      setKnowledgeInput('');
      await loadAllLinkedInData();
    } catch (err: any) {
      alert(`Failed to generate from knowledge: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Update Relationship CRM Stage
  const handleUpdateStage = async (relId: string, newStage: string) => {
    try {
      await fetchApi<any>(`/api/linkedin/relationships/${relId}/stage`, {
        method: 'PUT',
        body: JSON.stringify({ stage: newStage }),
      });
      await loadAllLinkedInData();
    } catch (err: any) {
      alert(`Failed to update stage: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-20 space-y-4">
        <RefreshCw className="w-8 h-8 text-brand-400 animate-spin" />
        <p className="text-xs font-mono text-zinc-400">Synthesizing Professional Brain & LinkedIn Growth Engine...</p>
      </div>
    );
  }

  const growthScore = dashboard?.professional_growth_score || 78;

  return (
    <div className="space-y-6 animate-in fade-in duration-300 pb-16">
      {/* Top Banner & Control Deck */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-surface-300 via-surface-300/80 to-surface-200 border border-white/10 relative overflow-hidden shadow-2xl">
        <div className="absolute right-0 top-0 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center gap-3">
              <span className="px-2.5 py-1 rounded-full bg-brand-500/20 text-brand-300 text-[11px] font-mono font-bold border border-brand-500/30 flex items-center gap-1.5">
                <Brain className="w-3.5 h-3.5" />
                Intelligent LinkedIn AI Growth Agent
              </span>
              <span className="px-2.5 py-1 rounded-full bg-emerald-950/60 text-emerald-400 text-[10px] font-mono border border-emerald-800/40 flex items-center gap-1">
                <ShieldCheck className="w-3 h-3" />
                Zero-Spam & API Policy Compliant
              </span>
              <span className="px-2.5 py-1 rounded-full bg-indigo-950/60 text-indigo-300 text-[10px] font-mono border border-indigo-800/40">
                Mode: COPILOT (Human-in-the-Loop)
              </span>
            </div>

            <h1 className="text-2xl font-extrabold text-white tracking-tight mt-3">
              Professional Brand & Relationship Command Center
            </h1>
            <p className="text-xs text-zinc-400 mt-1 max-w-2xl leading-relaxed">
              Autonomous strategy engine that analyzes your career depth, crafts high-signal technical content,
              discovers high-value engineering leaders, and prioritizes quality over volume.
            </p>
          </div>

          <div className="flex items-center gap-4">
            <div className="p-4 rounded-xl bg-surface-400/90 border border-white/10 flex items-center gap-4 shadow-inner">
              <div className="text-right">
                <div className="text-[10px] font-mono uppercase tracking-wider text-zinc-400 font-bold">
                  Professional Growth Score
                </div>
                <div className="text-2xl font-black text-white flex items-center justify-end gap-1.5 mt-0.5">
                  <span className="text-brand-400">{growthScore}</span>
                  <span className="text-xs text-zinc-500">/ 100</span>
                </div>
              </div>
              <div className="w-12 h-12 rounded-xl bg-brand-500/20 border border-brand-500/40 flex items-center justify-center text-brand-300 shadow-glow">
                <Award className="w-6 h-6" />
              </div>
            </div>

            <button
              onClick={handleRunDecisionCycle}
              disabled={actionLoading === 'cycle'}
              className="flex items-center gap-2 px-4 py-3 rounded-xl bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white font-bold text-xs tracking-wide shadow-glow transition-all hover:scale-[1.02] active:scale-95 disabled:opacity-50"
            >
              {actionLoading === 'cycle' ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Zap className="w-4 h-4 text-amber-300" />
              )}
              <span>Run AI Decision Cycle</span>
            </button>
          </div>
        </div>

        {/* Daily Strategy Briefing Bar */}
        {dashboard?.daily_briefing && (
          <div className="mt-6 pt-5 border-t border-white/5 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-3.5 rounded-xl bg-surface-400/60 border border-white/5 flex flex-col justify-between">
              <div>
                <span className="text-[10px] font-mono uppercase font-bold text-amber-400 flex items-center gap-1.5 mb-1">
                  <Flame className="w-3.5 h-3.5" />
                  Priority #1: Networking
                </span>
                <p className="text-xs font-semibold text-zinc-200">
                  {dashboard.daily_briefing.priority_1.title}
                </p>
              </div>
              <span className="text-[10px] text-zinc-400 mt-2 font-mono">
                {dashboard.daily_briefing.priority_1.impact}
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-surface-400/60 border border-white/5 flex flex-col justify-between">
              <div>
                <span className="text-[10px] font-mono uppercase font-bold text-emerald-400 flex items-center gap-1.5 mb-1">
                  <FileText className="w-3.5 h-3.5" />
                  Priority #2: Content
                </span>
                <p className="text-xs font-semibold text-zinc-200">
                  {dashboard.daily_briefing.priority_2.title}
                </p>
              </div>
              <span className="text-[10px] text-zinc-400 mt-2 font-mono">
                {dashboard.daily_briefing.priority_2.impact}
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-surface-400/60 border border-white/5 flex flex-col justify-between">
              <div>
                <span className="text-[10px] font-mono uppercase font-bold text-cyan-400 flex items-center gap-1.5 mb-1">
                  <MessageSquare className="w-3.5 h-3.5" />
                  Priority #3: Relationships
                </span>
                <p className="text-xs font-semibold text-zinc-200">
                  {dashboard.daily_briefing.priority_3.title}
                </p>
              </div>
              <span className="text-[10px] text-zinc-400 mt-2 font-mono">
                {dashboard.daily_briefing.priority_3.impact}
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-gradient-to-br from-indigo-950/40 to-surface-400/60 border border-indigo-500/20 flex flex-col justify-between">
              <div>
                <span className="text-[10px] font-mono uppercase font-bold text-indigo-300 flex items-center gap-1.5 mb-1">
                  <Clock className="w-3.5 h-3.5" />
                  Estimated Effort
                </span>
                <p className="text-xs font-semibold text-white">
                  {dashboard.daily_briefing.estimated_effort_minutes} Minutes Total Focus Time
                </p>
              </div>
              <p className="text-[10px] text-zinc-400 mt-2 font-mono">
                Achieve high-trust career outcomes with less LinkedIn screen time.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Natural Language Command Bar */}
      <div className="p-4 rounded-xl bg-surface-300 border border-white/10 shadow-lg space-y-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-brand-500/10 text-brand-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <input
            type="text"
            value={commandInput}
            onChange={(e) => setCommandInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleExecuteCommand()}
            placeholder="Ask agent: 'Write a post about Redis distributed locks', 'Find engineering managers to network with', 'Optimize my headline'..."
            className="flex-1 bg-surface-400/90 border border-white/10 rounded-lg px-4 py-2.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-500 font-mono transition-all"
          />
          <button
            onClick={() => handleExecuteCommand()}
            disabled={actionLoading === 'command' || !commandInput.trim()}
            className="px-4 py-2.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold transition-all disabled:opacity-40 flex items-center gap-1.5"
          >
            {actionLoading === 'command' ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <ArrowRight className="w-3.5 h-3.5" />
            )}
            <span>Execute</span>
          </button>
        </div>

        {/* Quick Suggestion Chips */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-[10px] font-mono text-zinc-500 uppercase font-bold">Quick Prompts:</span>
          {[
            'Write a post about Redis distributed locks',
            'Find engineering managers I should network with',
            'Optimize my headline and about section',
            'Show recruiters I should follow up with',
          ].map((promptText) => (
            <button
              key={promptText}
              onClick={() => handleExecuteCommand(promptText)}
              className="text-[11px] font-mono text-zinc-400 hover:text-white px-2.5 py-1 rounded bg-white/5 hover:bg-white/10 border border-white/5 hover:border-brand-500/30 transition-all"
            >
              {promptText}
            </button>
          ))}
        </div>

        {commandResult && (
          <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 text-xs font-mono flex items-center justify-between">
            <span>{commandResult.message}</span>
            <button
              onClick={() => setCommandResult(null)}
              className="text-[10px] text-zinc-400 hover:text-white px-2 py-0.5 rounded bg-white/5"
            >
              Dismiss
            </button>
          </div>
        )}
      </div>

      {/* Sub-Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-white/5 pb-2 overflow-x-auto">
        {[
          { id: 'overview', label: 'Overview & Strategy', icon: Compass, badge: null },
          { id: 'approvals', label: 'Approval Inbox', icon: ShieldCheck, badge: pendingActions.length },
          { id: 'optimizer', label: 'Profile Optimizer', icon: Award, badge: `${growthScore}%` },
          { id: 'content', label: 'Content Engine & Calendar', icon: FileText, badge: contentPosts.length },
          { id: 'network', label: 'Relationship CRM', icon: UserCheck, badge: relationships.length },
          { id: 'comments', label: 'Comment Opportunities', icon: MessageSquare, badge: commentOpportunities.length },
          { id: 'companies', label: 'Target Companies', icon: Building2, badge: companies.length },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                isActive
                  ? 'bg-brand-500/20 text-brand-300 border border-brand-500/40 shadow-glow'
                  : 'text-zinc-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
              {tab.badge !== null && (
                <span
                  className={`text-[10px] font-mono px-1.5 py-0.2 rounded ${
                    isActive ? 'bg-brand-500/40 text-white' : 'bg-white/10 text-zinc-400'
                  }`}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* TAB 1: OVERVIEW & STRATEGY */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Topic Pillars Grid */}
          <div className="p-6 rounded-2xl bg-surface-300 border border-white/5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
                  <Layers className="w-4 h-4 text-brand-400" />
                  Dynamic Personal Brand Pillars
                </h3>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Content distribution weights automatically adjust based on engagement signals and target opportunities.
                </p>
              </div>
              <span className="text-[10px] font-mono text-zinc-400 bg-white/5 px-2.5 py-1 rounded border border-white/5">
                Voice: {brandStrategy?.tone_preference || 'Technical & Authoritative'}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
              {(brandStrategy?.topic_pillars || []).map((pillar: any) => (
                <div
                  key={pillar.name}
                  className="p-3.5 rounded-xl bg-surface-400/80 border border-white/5 flex flex-col justify-between"
                >
                  <span className="text-[11px] font-medium text-zinc-300 leading-tight">
                    {pillar.name}
                  </span>
                  <div className="mt-3 flex items-baseline justify-between">
                    <span className="text-lg font-black text-white">{pillar.percentage}%</span>
                    <span className="w-2 h-2 rounded-full bg-brand-400" />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 7-Day Action Roadmap */}
          <div className="p-6 rounded-2xl bg-surface-300 border border-white/5 space-y-4">
            <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
              <Calendar className="w-4 h-4 text-indigo-400" />
              7-Day Execution Blueprint
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-7 gap-2.5">
              {(brandStrategy?.seven_day_plan || []).map((item: any) => (
                <div
                  key={item.day}
                  className="p-3 rounded-xl bg-surface-400/60 border border-white/5 hover:border-brand-500/30 transition-all flex flex-col justify-between"
                >
                  <div>
                    <span className="text-[10px] font-mono font-bold text-brand-400 block mb-1">
                      Day {item.day}
                    </span>
                    <p className="text-[11px] text-zinc-200 font-medium leading-snug">
                      {item.action}
                    </p>
                  </div>
                  <span className="text-[9px] font-mono text-zinc-500 uppercase mt-3">
                    {item.pillar}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: APPROVAL INBOX */}
      {activeTab === 'approvals' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-white/5">
            <div>
              <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-brand-400" />
                Human-in-the-Loop Approval Queue ({pendingActions.length})
              </h3>
              <p className="text-xs text-zinc-400 mt-0.5">
                Every external touchpoint (connections, posts, follow-ups) requires your explicit review before dispatch.
              </p>
            </div>
          </div>

          {pendingActions.length === 0 ? (
            <div className="p-12 text-center text-zinc-500 text-xs border border-dashed border-white/10 rounded-2xl">
              No actions currently awaiting approval. The AI agent prioritizes quality over unnecessary volume.
            </div>
          ) : (
            <div className="space-y-3">
              {pendingActions.map((action: any) => (
                <div
                  key={action.id}
                  className="p-5 rounded-xl bg-surface-300 border border-white/10 hover:border-brand-500/30 transition-all space-y-3 shadow-sm"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-bold text-white">{action.target_name}</span>
                        <span className="text-[10px] font-mono text-brand-300 bg-brand-950/60 px-2 py-0.5 rounded border border-brand-800/40">
                          {action.action_type}
                        </span>
                        <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40">
                          Expected Value: {Math.round(action.expected_value * 100)}%
                        </span>
                        <span className="text-[10px] font-mono text-zinc-400 bg-zinc-800/60 px-2 py-0.5 rounded">
                          Risk: {Math.round(action.risk_score * 100)}%
                        </span>
                      </div>
                      <p className="text-xs text-zinc-300">{action.reasoning}</p>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleDecideAction(action.id, 'APPROVE')}
                        disabled={actionLoading === action.id}
                        className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-all flex items-center gap-1 shadow-sm"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>Approve</span>
                      </button>
                      <button
                        onClick={() => handleDecideAction(action.id, 'REJECT')}
                        disabled={actionLoading === action.id}
                        className="px-3.5 py-1.5 rounded-lg bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border border-rose-800/40 text-xs font-semibold transition-all flex items-center gap-1"
                      >
                        <X className="w-3.5 h-3.5" />
                        <span>Reject</span>
                      </button>
                    </div>
                  </div>

                  {action.action_payload?.message && (
                    <div className="p-3 rounded-lg bg-surface-400/90 border border-white/5 text-xs font-mono text-zinc-300 leading-relaxed">
                      "{action.action_payload.message}"
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: PROFILE OPTIMIZER */}
      {activeTab === 'optimizer' && profileOptimizer && (
        <div className="space-y-6">
          {/* Score Matrix */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
            {[
              { label: 'Overall Score', score: profileOptimizer.overall_score, color: 'text-brand-400' },
              { label: 'Headline', score: profileOptimizer.headline_score, color: 'text-blue-400' },
              { label: 'About Section', score: profileOptimizer.about_score, color: 'text-cyan-400' },
              { label: 'Experience Depth', score: profileOptimizer.experience_score, color: 'text-emerald-400' },
              { label: 'Skills & Duration', score: profileOptimizer.skills_score, color: 'text-purple-400' },
              { label: 'Recruiter Search', score: profileOptimizer.recruiter_discoverability_score, color: 'text-amber-400' },
            ].map((metric) => (
              <div key={metric.label} className="p-4 rounded-xl bg-surface-300 border border-white/5 text-center">
                <span className="text-[10px] font-mono text-zinc-400 uppercase font-bold">{metric.label}</span>
                <div className={`text-2xl font-black mt-1 ${metric.color}`}>
                  {metric.score}<span className="text-xs text-zinc-500 font-normal">/100</span>
                </div>
              </div>
            ))}
          </div>

          {/* Specific Before vs. After Recommendations */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
              <Award className="w-4 h-4 text-brand-400" />
              Actionable Profile Optimizations
            </h3>

            {(profileOptimizer.recommendations || []).map((rec: any, idx: number) => (
              <div
                key={idx}
                className="p-5 rounded-2xl bg-surface-300 border border-white/5 space-y-4 hover:border-brand-500/30 transition-all shadow-sm"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-brand-300 bg-brand-950/60 px-2.5 py-0.5 rounded border border-brand-800/40">
                    Category: {rec.category}
                  </span>
                  <span className="text-[11px] font-mono text-emerald-400">
                    Expected Benefit: {rec.expected_benefit}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-3.5 rounded-xl bg-surface-400/80 border border-rose-900/30">
                    <span className="text-[10px] font-mono text-rose-400 uppercase font-bold block mb-1">
                      Current Value
                    </span>
                    <p className="text-xs text-zinc-300 leading-relaxed font-mono">
                      {rec.current}
                    </p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-surface-400/80 border border-emerald-800/40">
                    <span className="text-[10px] font-mono text-emerald-400 uppercase font-bold block mb-1">
                      AI Suggested High-Impact Value
                    </span>
                    <p className="text-xs text-white leading-relaxed font-mono font-medium">
                      {rec.suggested}
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-white/5">
                  <p className="text-xs text-zinc-400 italic">
                    Reason: {rec.reason}
                  </p>
                  {rec.category === 'HEADLINE' && (
                    <button
                      onClick={() => handleApplyProfileOpt('headline', rec.suggested)}
                      disabled={actionLoading === 'opt-headline'}
                      className="px-3.5 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold transition-all flex items-center gap-1.5 shadow-sm"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Apply to Profile</span>
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 4: CONTENT ENGINE & CALENDAR */}
      {activeTab === 'content' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-white/5">
            <div>
              <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
                <FileText className="w-4 h-4 text-brand-400" />
                Grounded Content Calendar & Drafting Studio
              </h3>
              <p className="text-xs text-zinc-400 mt-0.5">
                Authentic, opinionated technical posts drawn strictly from your real engineering experience.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowKnowledgeModal(true)}
                className="px-3.5 py-1.5 rounded-lg bg-surface-400 hover:bg-surface-200 text-zinc-300 hover:text-white text-xs font-semibold border border-white/10 transition-all flex items-center gap-1.5"
              >
                <Code2 className="w-3.5 h-3.5 text-cyan-400" />
                <span>From GitHub / Project</span>
              </button>
              <button
                onClick={() => setShowGeneratePostModal(true)}
                className="px-3.5 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold transition-all flex items-center gap-1.5 shadow-sm"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Draft New Post</span>
              </button>
            </div>
          </div>

          {/* Posts Feed */}
          <div className="space-y-4">
            {contentPosts.map((post) => (
              <div
                key={post.id}
                className="p-5 rounded-2xl bg-surface-300 border border-white/5 hover:border-brand-500/30 transition-all space-y-4 shadow-sm"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold text-white">{post.title}</span>
                      <span className="text-[10px] font-mono text-indigo-300 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-800/40">
                        {post.post_type}
                      </span>
                      <span className="text-[10px] font-mono text-amber-300 bg-amber-950/60 px-2 py-0.5 rounded border border-amber-800/40">
                        {post.status}
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-zinc-400">
                      Pillar: {post.topic_pillar}
                    </span>
                  </div>

                  {post.quality_checks && (
                    <div className="flex items-center gap-2 text-[10px] font-mono text-emerald-400 bg-emerald-950/30 px-2.5 py-1 rounded border border-emerald-800/30">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      <span>Originality: {post.quality_checks.originality_score}%</span>
                    </div>
                  )}
                </div>

                <div className="p-4 rounded-xl bg-surface-400/90 border border-white/5 text-xs text-zinc-200 whitespace-pre-line font-sans leading-relaxed">
                  {post.content_text}
                </div>

                {post.grounded_sources && post.grounded_sources.length > 0 && (
                  <div className="flex items-center gap-2 text-[10px] font-mono text-zinc-400">
                    <span className="font-bold uppercase">Grounded In:</span>
                    {post.grounded_sources.map((src: string, i: number) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-white/5 border border-white/5">
                        {src}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 5: RELATIONSHIP CRM & NETWORK DISCOVERY */}
      {activeTab === 'network' && (
        <div className="space-y-6">
          <div className="pb-2 border-b border-white/5">
            <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
              <UserCheck className="w-4 h-4 text-brand-400" />
              High-Value Relationships & Strategic CRM ({relationships.length})
            </h3>
            <p className="text-xs text-zinc-400 mt-0.5">
              Personalized, context-rich connection proposals and long-term conversation tracking.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {relationships.map((rel) => (
              <div
                key={rel.id}
                className="p-5 rounded-2xl bg-surface-300 border border-white/5 hover:border-brand-500/30 transition-all space-y-4 shadow-sm flex flex-col justify-between"
              >
                <div className="space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-white">{rel.full_name}</h4>
                      <p className="text-xs text-zinc-400">{rel.role} • {rel.company}</p>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] font-mono text-brand-300 bg-brand-950/60 px-2 py-0.5 rounded border border-brand-800/40 block">
                        Fit Score: {rel.relationship_score}%
                      </span>
                      <span className="text-[10px] font-mono text-zinc-400 mt-1 block">
                        Stage: {rel.relationship_stage}
                      </span>
                    </div>
                  </div>

                  {/* Explainable Reasons */}
                  {rel.score_reasons && (
                    <div className="space-y-1">
                      {rel.score_reasons.map((reason: string, rIdx: number) => (
                        <div key={rIdx} className="text-[11px] font-mono text-zinc-300 flex items-center gap-1.5">
                          <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                          <span>{reason}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {rel.suggested_connection_message && (
                    <div className="p-3 rounded-xl bg-surface-400/80 border border-white/5 space-y-1.5">
                      <span className="text-[10px] font-mono text-brand-400 uppercase font-bold block">
                        Personalized Connection Note
                      </span>
                      <p className="text-xs text-zinc-200 font-mono leading-relaxed">
                        "{rel.suggested_connection_message}"
                      </p>
                    </div>
                  )}
                </div>

                <div className="pt-3 border-t border-white/5 flex items-center justify-between">
                  <span className="text-[10px] font-mono text-zinc-500">
                    Next: {rel.next_action || 'Follow conversation'}
                  </span>

                  <select
                    value={rel.relationship_stage}
                    onChange={(e) => handleUpdateStage(rel.id, e.target.value)}
                    className="bg-surface-400 border border-white/10 rounded px-2.5 py-1 text-[11px] font-mono text-zinc-300 focus:outline-none focus:border-brand-500"
                  >
                    <option value="DISCOVERED">Discovered</option>
                    <option value="CONNECTION_PROPOSED">Connection Proposed</option>
                    <option value="CONNECTED">Connected</option>
                    <option value="CONVERSATION_STARTED">Conversation Started</option>
                    <option value="WARM_RELATIONSHIP">Warm Relationship</option>
                    <option value="OPPORTUNITY">Opportunity</option>
                    <option value="INACTIVE">Inactive</option>
                  </select>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 6: COMMENT OPPORTUNITIES */}
      {activeTab === 'comments' && (
        <div className="space-y-4">
          <div className="pb-2 border-b border-white/5">
            <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-brand-400" />
              High-Signal Technical Comment Opportunities ({commentOpportunities.length})
            </h3>
            <p className="text-xs text-zinc-400 mt-0.5">
              Thoughtful, expert contributions on relevant discussions. Zero generic spam.
            </p>
          </div>

          <div className="space-y-4">
            {commentOpportunities.map((comm) => (
              <div
                key={comm.id}
                className="p-5 rounded-2xl bg-surface-300 border border-white/5 hover:border-brand-500/30 transition-all space-y-4 shadow-sm"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="text-xs font-bold text-white">{comm.post_author}</h4>
                    <p className="text-[11px] text-zinc-400">{comm.post_author_role} • {comm.post_author_company}</p>
                    <p className="text-xs font-semibold text-brand-300 mt-1">Topic: {comm.post_topic}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-2.5 py-0.5 rounded border border-emerald-800/40">
                      Expertise Fit: {comm.expertise_fit_score}%
                    </span>
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-surface-400/60 border border-white/5 text-xs text-zinc-300 italic">
                  "{comm.post_snippet}"
                </div>

                <div className="p-4 rounded-xl bg-surface-400/90 border border-brand-500/20 space-y-1.5">
                  <span className="text-[10px] font-mono text-brand-400 uppercase font-bold block">
                    AI Grounded Technical Contribution
                  </span>
                  <p className="text-xs text-white font-mono leading-relaxed">
                    "{comm.suggested_comment}"
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 7: TARGET COMPANIES */}
      {activeTab === 'companies' && (
        <div className="space-y-4">
          <div className="pb-2 border-b border-white/5">
            <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
              <Building2 className="w-4 h-4 text-brand-400" />
              Target Company Intelligence & Networking Plans ({companies.length})
            </h3>
            <p className="text-xs text-zinc-400 mt-0.5">
              Deep telemetry on target companies, verified tech stacks, open roles, and key leaders.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {companies.map((comp) => (
              <div
                key={comp.id}
                className="p-5 rounded-2xl bg-surface-300 border border-white/5 hover:border-brand-500/30 transition-all space-y-4 shadow-sm"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="text-sm font-bold text-white">{comp.company_name}</h4>
                    <p className="text-xs text-zinc-400">{comp.industry} • {comp.domain}</p>
                  </div>
                  <span className="text-[10px] font-mono text-rose-300 bg-rose-950/60 px-2 py-0.5 rounded border border-rose-800/40">
                    Priority: {comp.target_priority}
                  </span>
                </div>

                {comp.tech_stack && (
                  <div className="space-y-1">
                    <span className="text-[10px] font-mono uppercase font-bold text-zinc-400 block">
                      Target Tech Stack Signals:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {comp.tech_stack.map((tech: string, tIdx: number) => (
                        <span key={tIdx} className="text-[10px] font-mono text-brand-300 bg-brand-950/40 px-2 py-0.5 rounded border border-brand-800/30">
                          {tech}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {comp.networking_plan && (
                  <div className="space-y-1.5 pt-2 border-t border-white/5">
                    <span className="text-[10px] font-mono uppercase font-bold text-zinc-400 block">
                      Actionable Networking Plan:
                    </span>
                    {comp.networking_plan.map((step: string, sIdx: number) => (
                      <div key={sIdx} className="text-xs text-zinc-300 flex items-start gap-1.5">
                        <ArrowRight className="w-3.5 h-3.5 text-brand-400 shrink-0 mt-0.5" />
                        <span>{step}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* MODAL: Draft New Post */}
      {showGeneratePostModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface-300 border border-white/10 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <FileText className="w-4 h-4 text-brand-400" />
              Draft Authentic Technical Post
            </h3>
            <p className="text-xs text-zinc-400">
              The AI Content Engine will craft a high-signal post grounded in your real verified skills and engineering depth.
            </p>

            <div className="space-y-3">
              <div>
                <label className="text-[10px] font-mono uppercase text-zinc-400 block mb-1">Post Topic</label>
                <input
                  type="text"
                  value={postTopicInput}
                  onChange={(e) => setPostTopicInput(e.target.value)}
                  placeholder="e.g. Architectural trade-offs of Redis caching vs Database reads"
                  className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] font-mono uppercase text-zinc-400 block mb-1">Topic Pillar</label>
                  <select
                    value={postPillarInput}
                    onChange={(e) => setPostPillarInput(e.target.value)}
                    className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500 font-mono"
                  >
                    <option value="Technical Deep-Dives">Technical Deep-Dives</option>
                    <option value="Real Engineering Experiences">Real Engineering Experiences</option>
                    <option value="System Design & Architecture">System Design</option>
                    <option value="Career & Engineering Lessons">Career Lessons</option>
                    <option value="Open-Source & Projects">Open-Source & Projects</option>
                  </select>
                </div>

                <div>
                  <label className="text-[10px] font-mono uppercase text-zinc-400 block mb-1">Format</label>
                  <select
                    value={postTypeInput}
                    onChange={(e) => setPostTypeInput(e.target.value)}
                    className="w-full bg-surface-400 border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500 font-mono"
                  >
                    <option value="TECHNICAL_BREAKDOWN">Technical Breakdown</option>
                    <option value="CASE_STUDY">Production Case Study</option>
                    <option value="ARCHITECTURE_LESSON">Architecture Lesson</option>
                    <option value="MINI_TUTORIAL">Mini Tutorial</option>
                    <option value="LESSONS_LEARNED">Lessons Learned</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-white/5">
              <button
                onClick={() => setShowGeneratePostModal(false)}
                className="px-4 py-2 rounded-lg text-xs text-zinc-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleCreatePost}
                disabled={actionLoading === 'gen_post' || !postTopicInput.trim()}
                className="px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold transition-all disabled:opacity-40"
              >
                {actionLoading === 'gen_post' ? 'Synthesizing...' : 'Generate & Stage'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Generate from Knowledge / GitHub */}
      {showKnowledgeModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface-300 border border-white/10 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Code2 className="w-4 h-4 text-cyan-400" />
              Generate Post from GitHub Commit / Project Milestone
            </h3>
            <p className="text-xs text-zinc-400">
              Paste a commit message, PR description, or technical note. The agent converts it into an educational post idea without exposing private code.
            </p>

            <div>
              <label className="text-[10px] font-mono uppercase text-zinc-400 block mb-1">Commit / Technical Note</label>
              <textarea
                rows={4}
                value={knowledgeInput}
                onChange={(e) => setKnowledgeInput(e.target.value)}
                placeholder="e.g. Implemented Redis Redlock with jittered backoff to eliminate connection contention spikes under 50M event telemetry load"
                className="w-full bg-surface-400 border border-white/10 rounded-lg p-3 text-xs text-white focus:outline-none focus:border-brand-500 font-mono"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-white/5">
              <button
                onClick={() => setShowKnowledgeModal(false)}
                className="px-4 py-2 rounded-lg text-xs text-zinc-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateFromKnowledge}
                disabled={actionLoading === 'gen_knowledge' || !knowledgeInput.trim()}
                className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold transition-all disabled:opacity-40"
              >
                {actionLoading === 'gen_knowledge' ? 'Analyzing...' : 'Generate Post Idea'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

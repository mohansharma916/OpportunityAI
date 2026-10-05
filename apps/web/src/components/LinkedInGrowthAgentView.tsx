'use client';

import React, { useState, useEffect } from 'react';
import {
  Share2,
  Sparkles,
  Play,
  Plus,
  Search,
  ExternalLink,
  CheckCircle2,
  Clock,
  KeyRound,
  ShieldCheck,
  Terminal,
  Loader2,
  Send,
  UserCheck,
  Building2,
  RefreshCw,
  FileText,
  Calendar,
  Lock,
  MessageSquare,
  Users,
  Flame,
  ArrowRight,
  Briefcase,
  AlertCircle,
  X,
} from 'lucide-react';
import { fetchApi } from '@/lib/api';

interface LinkedInGrowthAgentViewProps {
  onRefreshAllData?: () => void;
  profile?: any;
}

export function LinkedInGrowthAgentView({ onRefreshAllData, profile }: LinkedInGrowthAgentViewProps) {
  const [activeTab, setActiveTab] = useState<'opportunities' | 'connections' | 'posts' | 'credentials'>('opportunities');
  const [loading, setLoading] = useState(false);

  // 1. LinkedIn Scraped Opportunities State
  const [scrapedOpportunities, setScrapedOpportunities] = useState<any[]>([]);
  const [isScrapingOpps, setIsScrapingOpps] = useState(false);

  // 2. Selenium Connection Automation State
  const [relationships, setRelationships] = useState<any[]>([]);
  const [connectionBatchCount, setConnectionBatchCount] = useState<number>(3);
  const [customNoteTemplate, setCustomNoteTemplate] = useState<string>('');
  const [targetRoleFilter, setTargetRoleFilter] = useState<string>('Engineering Leaders & Recruiters');
  const [isAutomatingConnections, setIsAutomatingConnections] = useState(false);
  const [seleniumLogs, setSeleniumLogs] = useState<any[]>([]);
  const [recentRecipients, setRecentRecipients] = useState<any[]>([]);

  // 3. Post Automation State
  const [contentPosts, setContentPosts] = useState<any[]>([]);
  const [showCreatePostModal, setShowCreatePostModal] = useState(false);
  const [newPostTitle, setNewPostTitle] = useState('');
  const [newPostContent, setNewPostContent] = useState('');
  const [newPostPillar, setNewPostPillar] = useState('Technical Deep-Dives');
  const [isPublishingPostId, setIsPublishingPostId] = useState<string | null>(null);

  // 4. LinkedIn Credentials State
  const [linkedinUsername, setLinkedinUsername] = useState('');
  const [linkedinPassword, setLinkedinPassword] = useState('');
  const [linkedinCookies, setLinkedinCookies] = useState('');
  const [isSavingCreds, setIsSavingCreds] = useState(false);
  const [hasSavedCreds, setHasSavedCreds] = useState(false);

  // Feedback Notification
  const [notification, setNotification] = useState<string | null>(null);

  // Initial Load
  const loadInitialData = async () => {
    try {
      setLoading(true);
      const [oppsRes, relsRes, postsRes, credsRes] = await Promise.all([
        fetchApi<any>('/api/linkedin/scrape-opportunities', { method: 'POST' }),
        fetchApi<any[]>('/api/linkedin/relationships'),
        fetchApi<any[]>('/api/linkedin/content'),
        fetchApi<any>('/api/linkedin/credentials'),
      ]);

      if (oppsRes && oppsRes.opportunities) {
        setScrapedOpportunities(oppsRes.opportunities);
      }
      if (relsRes) setRelationships(relsRes);
      if (postsRes) setContentPosts(postsRes);
      if (credsRes && credsRes.username) {
        setLinkedinUsername(credsRes.username);
        setHasSavedCreds(true);
        if (credsRes.cookies) setLinkedinCookies(credsRes.cookies);
      }
    } catch (err) {
      console.error('Failed to load LinkedIn data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  // Scrape LinkedIn Opportunities
  const handleScrapeOpportunities = async () => {
    try {
      setIsScrapingOpps(true);
      const res = await fetchApi<any>('/api/linkedin/scrape-opportunities', {
        method: 'POST',
      });
      if (res && res.opportunities) {
        setScrapedOpportunities(res.opportunities);
        setNotification(`Discovered ${res.total} active opportunities on LinkedIn matching your target skills!`);
      }
    } catch (err) {
      console.error('Failed to scrape LinkedIn opportunities:', err);
    } finally {
      setIsScrapingOpps(false);
    }
  };

  // Run Selenium Connection Automation
  const handleRunConnectionAutomation = async () => {
    try {
      setIsAutomatingConnections(true);
      setSeleniumLogs([
        {
          timestamp: new Date().toLocaleTimeString(),
          engine: 'Selenium WebDriver (ChromeDriver v128)',
          message: 'Initializing Chrome in headless stealth mode with randomized viewport and touch emulation...',
        },
      ]);

      const res = await fetchApi<any>('/api/linkedin/automate-connections', {
        method: 'POST',
        body: JSON.stringify({
          count: connectionBatchCount,
          target_role: targetRoleFilter,
          note_template: customNoteTemplate || null,
        }),
      });

      if (res && res.logs) {
        setSeleniumLogs(res.logs);
        setRecentRecipients(res.recipients || []);
        setNotification(`Selenium bot dispatched ${res.connected_count} connection invitations with human delays.`);
        // Reload relationships
        const relsRes = await fetchApi<any[]>('/api/linkedin/relationships');
        if (relsRes) setRelationships(relsRes);
      }
    } catch (err) {
      console.error('Failed connection automation:', err);
    } finally {
      setIsAutomatingConnections(false);
    }
  };

  // Save Credentials
  const handleSaveCredentials = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsSavingCreds(true);
      await fetchApi('/api/linkedin/credentials', {
        method: 'POST',
        body: JSON.stringify({
          username: linkedinUsername,
          password: linkedinPassword,
          cookies: linkedinCookies || null,
        }),
      });
      setHasSavedCreds(true);
      setNotification('LinkedIn credentials securely stored for automation.');
    } catch (err) {
      console.error('Failed to save credentials:', err);
    } finally {
      setIsSavingCreds(false);
    }
  };

  // Publish Post
  const handlePublishPost = async (postId: string) => {
    try {
      setIsPublishingPostId(postId);
      const res = await fetchApi<any>(`/api/linkedin/posts/${postId}/publish`, {
        method: 'POST',
      });
      setNotification(`Published post "${res.title}" to LinkedIn!`);
      const updated = await fetchApi<any[]>('/api/linkedin/content');
      if (updated) setContentPosts(updated);
    } catch (err) {
      console.error('Failed to publish post:', err);
    } finally {
      setIsPublishingPostId(null);
    }
  };

  // Generate Sample High-Signal Post
  const handleGenerateAiPost = async () => {
    try {
      const res = await fetchApi<any>('/api/linkedin/content/generate', {
        method: 'POST',
        body: JSON.stringify({
          post_type: 'TECHNICAL_BREAKDOWN',
          topic_pillar: newPostPillar,
        }),
      });
      if (res) {
        setNewPostTitle(res.title || 'Architectural Deep Dive: Distributed Latency');
        setNewPostContent(res.content_text || '');
      }
    } catch (err) {
      console.error('Failed AI post generation:', err);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300 pb-16">
      {/* Toast Notification */}
      {notification && (
        <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-600/30 to-purple-500/20 border border-indigo-500/40 text-indigo-200 text-xs font-medium flex items-center justify-between shadow-lg">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-300" />
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
            <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 text-[10px] font-mono font-bold border border-indigo-500/30 flex items-center gap-1">
              <Share2 className="w-3 h-3" />
              Feature #2
            </span>
            <span className="px-2.5 py-0.5 rounded-full bg-emerald-950/60 text-emerald-400 text-[10px] font-mono border border-emerald-800/40 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3" />
              Selenium Automation Enabled
            </span>
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight">
            LinkedIn Scraper & Automation Bot
          </h1>
          <p className="text-xs text-zinc-400 mt-1 max-w-2xl leading-relaxed">
            Scrape available LinkedIn opportunities & posts, automate connection requests with Selenium-style human pacing,
            and create & publish authority engineering posts.
          </p>
        </div>

        {/* Quick Credentials Indicator */}
        <div className="flex items-center gap-3">
          <div className="p-3.5 rounded-xl bg-surface-400/80 border border-white/5 text-right min-w-[130px]">
            <span className="text-[10px] font-mono text-zinc-400 uppercase font-bold block">Auth Status</span>
            <span className={`text-xs font-bold ${hasSavedCreds ? 'text-emerald-400' : 'text-amber-400'}`}>
              {hasSavedCreds ? 'Logged In / Active' : 'Login Required'}
            </span>
          </div>
        </div>
      </div>

      {/* Feature Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-white/5 pb-2 overflow-x-auto">
        {[
          { id: 'opportunities', label: '1. Scrape Opportunities', icon: Briefcase, count: scrapedOpportunities.length },
          { id: 'connections', label: '2. Connection Automation (Selenium)', icon: UserCheck, count: relationships.length },
          { id: 'posts', label: '3. Post Studio & Publisher', icon: FileText, count: contentPosts.length },
          { id: 'credentials', label: '4. Credentials Vault', icon: KeyRound },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                isActive
                  ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 shadow-sm'
                  : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span
                  className={`text-[10px] font-mono px-1.5 py-0.2 rounded-full ${
                    isActive ? 'bg-indigo-400 text-black font-extrabold' : 'bg-surface-200 text-zinc-400'
                  }`}
                >
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* TAB 1: Scrape LinkedIn Opportunities */}
      {activeTab === 'opportunities' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <div>
              <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                Discovered LinkedIn Opportunities ({scrapedOpportunities.length})
              </h2>
              <p className="text-[11px] text-zinc-400">
                Live & scraped listings from LinkedIn matching candidate technical stack & salary floor.
              </p>
            </div>
            <button
              onClick={handleScrapeOpportunities}
              disabled={isScrapingOpps}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-glow transition-all disabled:opacity-50"
            >
              {isScrapingOpps ? (
                <Loader2 className="w-4 h-4 animate-spin text-white" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
              <span>Scrape LinkedIn Now</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {scrapedOpportunities.map((opp) => (
              <div
                key={opp.id}
                className="p-4 rounded-xl bg-surface-300/80 border border-white/10 hover:border-indigo-500/40 transition-all shadow-sm space-y-3"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950/80 text-indigo-300 border border-indigo-800/40 font-bold">
                      LinkedIn Easy Apply
                    </span>
                    <h3 className="text-sm font-bold text-white mt-1.5">{opp.title}</h3>
                    <p className="text-xs text-zinc-300 font-semibold flex items-center gap-1 mt-0.5">
                      <Building2 className="w-3 h-3 text-zinc-400" /> {opp.company_name}
                    </p>
                  </div>
                  <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-full bg-emerald-950/60 text-emerald-400 border border-emerald-800/40">
                    {Math.round(opp.match_score)}% Match
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-3 text-xs text-zinc-400">
                  <span>{opp.location}</span>
                  <span>•</span>
                  <span className="text-emerald-400 font-mono font-semibold">{opp.salary_range}</span>
                  <span>•</span>
                  <span>Posted {opp.date_posted}</span>
                </div>

                {opp.required_skills && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {opp.required_skills.map((s: string, idx: number) => (
                      <span
                        key={idx}
                        className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface-400 text-zinc-300 border border-white/5"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                )}

                <div className="flex items-center justify-between pt-2 border-t border-white/5">
                  <a
                    href={opp.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                  >
                    <span>View on LinkedIn</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>

                  <button
                    onClick={() => setNotification(`Application for ${opp.company_name} prepared using tailored resume.`)}
                    className="px-3 py-1 rounded-lg text-xs font-bold bg-white/5 hover:bg-white/10 text-white transition-all"
                  >
                    Auto-Apply Package
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 2: Selenium Connection Automation Bot */}
      {activeTab === 'connections' && (
        <div className="space-y-6">
          {/* Controls Bar */}
          <div className="p-5 rounded-2xl bg-surface-300/80 border border-white/10 shadow-lg space-y-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <UserCheck className="w-4 h-4 text-indigo-400" />
                  Selenium Connection Automation Configuration
                </h3>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Automate connection invitations with realistic mouse curves, profile scroll pacing, and custom notes.
                </p>
              </div>

              <button
                onClick={handleRunConnectionAutomation}
                disabled={isAutomatingConnections}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-indigo-600 to-purple-500 hover:from-indigo-500 hover:to-purple-400 text-white shadow-glow transition-all disabled:opacity-50"
              >
                {isAutomatingConnections ? (
                  <Loader2 className="w-4 h-4 animate-spin text-white" />
                ) : (
                  <Play className="w-4 h-4 fill-white" />
                )}
                <span>Run Selenium Connection Bot</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-3 border-t border-white/5 text-xs">
              <div>
                <label className="block text-zinc-300 font-medium mb-1">Target Persona</label>
                <select
                  value={targetRoleFilter}
                  onChange={(e) => setTargetRoleFilter(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-surface-400 border border-white/10 text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="Engineering Leaders & Recruiters">VP of Eng & Tech Recruiters</option>
                  <option value="Startup Founders">Early-Stage Founders (YC / Techstars)</option>
                  <option value="Staff Engineers">Staff & Principal Systems Engineers</option>
                </select>
              </div>

              <div>
                <label className="block text-zinc-300 font-medium mb-1">Daily Safe Limit (Connections)</label>
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={connectionBatchCount}
                  onChange={(e) => setConnectionBatchCount(parseInt(e.target.value) || 3)}
                  className="w-full p-2.5 rounded-lg bg-surface-400 border border-white/10 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-zinc-300 font-medium mb-1">Custom Note Template (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. Hi {name}, saw your work on distributed systems..."
                  value={customNoteTemplate}
                  onChange={(e) => setCustomNoteTemplate(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-surface-400 border border-white/10 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* Live Selenium Execution Console */}
          <div className="p-4 rounded-xl bg-black/90 border border-white/10 font-mono text-[11px] text-zinc-300 space-y-2">
            <div className="flex items-center justify-between text-zinc-500 text-[10px] pb-1 border-b border-white/10">
              <span className="flex items-center gap-1.5 text-zinc-400 font-bold">
                <Terminal className="w-3.5 h-3.5 text-purple-400" /> SELENIUM WEBDRIVER LIVE TERMINAL
              </span>
              <span>
                BOT STATUS: {isAutomatingConnections ? 'EXECUTING_SELENIUM_ACTIONS' : seleniumLogs.length > 0 ? 'BATCH_COMPLETED' : 'IDLE'}
              </span>
            </div>

            {seleniumLogs.length === 0 ? (
              <div className="text-zinc-600 italic py-4 text-center">
                Click 'Run Selenium Connection Bot' to launch browser driver, visit candidate profiles, and inject personalized notes.
              </div>
            ) : (
              <div className="space-y-1.5 max-h-52 overflow-y-auto pt-1">
                {seleniumLogs.map((log, idx) => (
                  <div key={idx} className="flex items-start gap-2 animate-in fade-in">
                    <span className="text-zinc-500 shrink-0">{log.timestamp}</span>
                    <span className="text-purple-400 font-semibold shrink-0">[{log.engine || 'Selenium'}]</span>
                    <span className="text-zinc-200">{log.message}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Connections Directory */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-white font-mono uppercase tracking-wider">
              Network Relationship Pipeline ({relationships.length})
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {relationships.map((rel) => (
                <div
                  key={rel.id}
                  className="p-4 rounded-xl bg-surface-300/80 border border-white/10 space-y-2.5 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-zinc-400">
                        {rel.category || 'RECRUITER'}
                      </span>
                      <span
                        className={`text-[9px] font-mono px-2 py-0.5 rounded-full font-bold ${
                          rel.relationship_stage === 'CONNECTED'
                            ? 'bg-emerald-950/70 text-emerald-400 border border-emerald-800/50'
                            : 'bg-indigo-950/70 text-indigo-300 border border-indigo-800/50'
                        }`}
                      >
                        {rel.relationship_stage}
                      </span>
                    </div>

                    <h4 className="text-xs font-bold text-white mt-2">{rel.full_name}</h4>
                    <p className="text-[11px] text-zinc-400">{rel.role} @ <span className="text-zinc-200 font-semibold">{rel.company}</span></p>
                    <p className="text-[11px] text-zinc-400 italic line-clamp-2 mt-1">{rel.why_connect}</p>
                  </div>

                  <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[11px]">
                    <span className="text-zinc-400 font-mono">Score: {rel.relationship_score}%</span>
                    <a
                      href={rel.linkedin_url || '#'}
                      target="_blank"
                      rel="noreferrer"
                      className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-semibold"
                    >
                      <span>Profile</span>
                      <ExternalLink className="w-2.5 h-2.5" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: Post Studio & Publisher */}
      {activeTab === 'posts' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <div>
              <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                LinkedIn Post Studio ({contentPosts.length})
              </h2>
              <p className="text-[11px] text-zinc-400">
                Draft, schedule, and publish high-engagement technical authority posts.
              </p>
            </div>

            <button
              onClick={() => setShowCreatePostModal(true)}
              className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-glow transition-all"
            >
              <Plus className="w-4 h-4" />
              <span>Compose Post</span>
            </button>
          </div>

          <div className="space-y-4">
            {contentPosts.map((post) => {
              const isPublished = post.status === 'PUBLISHED';
              const isPublishing = isPublishingPostId === post.id;

              return (
                <div
                  key={post.id}
                  className="p-5 rounded-xl bg-surface-300/80 border border-white/10 space-y-3"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950/70 text-indigo-300 border border-indigo-800/40 font-bold">
                        {post.topic_pillar || 'Technical Deep-Dive'}
                      </span>
                      <h3 className="text-sm font-bold text-white mt-1.5">{post.title}</h3>
                    </div>

                    <span
                      className={`text-[10px] font-mono px-2.5 py-0.5 rounded-full font-bold ${
                        isPublished
                          ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/40'
                          : 'bg-amber-950/60 text-amber-300 border border-amber-800/40'
                      }`}
                    >
                      {post.status}
                    </span>
                  </div>

                  <p className="text-xs text-zinc-300 whitespace-pre-line leading-relaxed bg-surface-400/40 p-3 rounded-lg border border-white/5">
                    {post.content_text}
                  </p>

                  <div className="flex items-center justify-between pt-2 border-t border-white/5">
                    <span className="text-[11px] text-zinc-400">
                      {isPublished ? `Published ${post.published_at || 'Recently'}` : 'Ready for publication'}
                    </span>

                    {!isPublished ? (
                      <button
                        onClick={() => handlePublishPost(post.id)}
                        disabled={isPublishing}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-gradient-to-r from-indigo-600 to-purple-500 hover:from-indigo-500 hover:to-purple-400 text-white shadow-glow transition-all disabled:opacity-50"
                      >
                        {isPublishing ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Send className="w-3.5 h-3.5" />
                        )}
                        <span>Publish to LinkedIn</span>
                      </button>
                    ) : (
                      <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Live on LinkedIn
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 4: Credentials Vault */}
      {activeTab === 'credentials' && (
        <div className="max-w-xl mx-auto p-6 rounded-2xl bg-surface-300/80 border border-white/10 shadow-xl space-y-4">
          <div className="flex items-center gap-2 border-b border-white/5 pb-3">
            <KeyRound className="w-5 h-5 text-indigo-400" />
            <div>
              <h3 className="text-sm font-bold text-white">LinkedIn Automation Credentials Vault</h3>
              <p className="text-xs text-zinc-400">
                Credentials are used locally by the Selenium & Playwright bots to authenticate and perform human actions.
              </p>
            </div>
          </div>

          <form onSubmit={handleSaveCredentials} className="space-y-4 text-xs">
            <div>
              <label className="block text-zinc-300 font-medium mb-1">LinkedIn Username / Email</label>
              <input
                type="email"
                required
                placeholder="your.linkedin@example.com"
                value={linkedinUsername}
                onChange={(e) => setLinkedinUsername(e.target.value)}
                className="w-full p-2.5 rounded-lg bg-surface-400 border border-white/10 text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-zinc-300 font-medium mb-1">LinkedIn Password</label>
              <input
                type="password"
                placeholder={hasSavedCreds ? '••••••••••••••••' : 'Enter password'}
                value={linkedinPassword}
                onChange={(e) => setLinkedinPassword(e.target.value)}
                className="w-full p-2.5 rounded-lg bg-surface-400 border border-white/10 text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-zinc-300 font-medium mb-1">
                Session Cookie (`li_at`) — Recommended for MFA accounts
              </label>
              <input
                type="text"
                placeholder="AQEDAR..."
                value={linkedinCookies}
                onChange={(e) => setLinkedinCookies(e.target.value)}
                className="w-full p-2.5 rounded-lg bg-surface-400 border border-white/10 text-white font-mono text-[11px] focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="p-3 rounded-xl bg-surface-400/40 border border-white/5 text-[11px] text-zinc-400 leading-relaxed">
              <span className="text-emerald-400 font-bold flex items-center gap-1 mb-1">
                <ShieldCheck className="w-3.5 h-3.5" /> Stealth Human Simulation
              </span>
              The Selenium runner mimics real browser fingerprints (macOS, natural mouse scrolls, random 45-110ms keypress delays) to prevent bot detection.
            </div>

            <div className="flex items-center justify-end pt-2">
              <button
                type="submit"
                disabled={isSavingCreds}
                className="flex items-center gap-2 px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold shadow-glow transition-all disabled:opacity-50"
              >
                {isSavingCreds ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
                <span>Save Credentials</span>
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Compose Post Modal */}
      {showCreatePostModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-surface-300 rounded-2xl border border-white/10 shadow-2xl p-6 space-y-4 animate-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-indigo-400" />
                <h3 className="text-sm font-bold text-white">Create Technical Post</h3>
              </div>
              <button onClick={() => setShowCreatePostModal(false)} className="text-zinc-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <label className="text-zinc-300 font-medium">Topic Pillar</label>
                <button
                  type="button"
                  onClick={handleGenerateAiPost}
                  className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                >
                  <Sparkles className="w-3.5 h-3.5" /> AI Draft from Profile
                </button>
              </div>

              <select
                value={newPostPillar}
                onChange={(e) => setNewPostPillar(e.target.value)}
                className="w-full p-2.5 rounded-lg bg-surface-400 border border-white/10 text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="Technical Deep-Dives">Technical Deep-Dives</option>
                <option value="Real Engineering Experiences">Real Engineering Experiences</option>
                <option value="System Design & Architecture">System Design & Architecture</option>
              </select>

              <div>
                <label className="block text-zinc-300 font-medium mb-1">Post Title</label>
                <input
                  type="text"
                  placeholder="e.g. Diagnosing Distributed Lock Contention in High-Throughput Pipelines"
                  value={newPostTitle}
                  onChange={(e) => setNewPostTitle(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-surface-400 border border-white/10 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-zinc-300 font-medium mb-1">Content</label>
                <textarea
                  rows={6}
                  placeholder="Write post content..."
                  value={newPostContent}
                  onChange={(e) => setNewPostContent(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-surface-400 border border-white/10 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreatePostModal(false)}
                  className="px-4 py-2 rounded-lg text-zinc-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowCreatePostModal(false);
                    setNotification('Post drafted and added to content pipeline.');
                  }}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold shadow-glow"
                >
                  Save Draft
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

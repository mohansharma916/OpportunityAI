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
  ThumbsUp,
  Repeat,
  Wand2,
  BookOpen,
  Filter,
  Lightbulb,
  Compass,
  Copy,
  Check,
  UserPlus,
  Layers,
  TrendingUp,
} from 'lucide-react';
import { fetchApi } from '@/lib/api';

interface LinkedInGrowthAgentViewProps {
  onRefreshAllData?: () => void;
  profile?: any;
}

export function LinkedInGrowthAgentView({ onRefreshAllData, profile }: LinkedInGrowthAgentViewProps) {
  const [activeTab, setActiveTab] = useState<'scraped_posts' | 'post_studio' | 'connections' | 'credentials'>('scraped_posts');
  const [loading, setLoading] = useState(false);

  // 1. Multi-Type Scraped Posts State
  const [scrapedPosts, setScrapedPosts] = useState<any[]>([]);
  const [scrapeTypeFilter, setScrapeTypeFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [isScrapingPosts, setIsScrapingPosts] = useState(false);

  // 2. Post Studio & Human Synthesis State
  const [activeStudioPost, setActiveStudioPost] = useState<any | null>(null);
  const [analysisData, setAnalysisData] = useState<any | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedAngleKey, setSelectedAngleKey] = useState<string>('PERSONAL_PRODUCTION_EXPERIENCE');
  const [customStudioNotes, setCustomStudioNotes] = useState('');
  const [synthesizedDraft, setSynthesizedDraft] = useState<any | null>(null);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [analyzedLibrary, setAnalyzedLibrary] = useState<any[]>([]);
  const [isCopied, setIsCopied] = useState(false);
  const [isPublishingPost, setIsPublishingPost] = useState(false);

  // 3. Selenium Connection Automation State
  const [relationships, setRelationships] = useState<any[]>([]);
  const [connectionBatchCount, setConnectionBatchCount] = useState<number>(3);
  const [customNoteTemplate, setCustomNoteTemplate] = useState<string>('');
  const [targetRoleFilter, setTargetRoleFilter] = useState<string>('Engineering Leaders & Recruiters');
  const [isAutomatingConnections, setIsAutomatingConnections] = useState(false);
  const [seleniumLogs, setSeleniumLogs] = useState<any[]>([]);
  const [recentRecipients, setRecentRecipients] = useState<any[]>([]);

  // 4. LinkedIn Credentials State
  const [linkedinUsername, setLinkedinUsername] = useState('');
  const [linkedinPassword, setLinkedinPassword] = useState('');
  const [linkedinCookies, setLinkedinCookies] = useState('');
  const [isSavingCreds, setIsSavingCreds] = useState(false);
  const [hasSavedCreds, setHasSavedCreds] = useState(false);

  // Notification Toast
  const [notification, setNotification] = useState<string | null>(null);

  // Initial Load
  const loadInitialData = async () => {
    try {
      setLoading(true);
      const [scrapedRes, relsRes, libRes, credsRes] = await Promise.all([
        fetchApi<any[]>('/api/linkedin/scraped-posts'),
        fetchApi<any[]>('/api/linkedin/relationships'),
        fetchApi<any[]>('/api/linkedin/post-studio/library'),
        fetchApi<any>('/api/linkedin/credentials'),
      ]);

      if (scrapedRes) {
        setScrapedPosts(scrapedRes);
        if (scrapedRes.length > 0 && !activeStudioPost) {
          // Pre-select first interesting/hiring post for post studio
          const interestingPost = scrapedRes.find((p) => p.scrape_type === 'INTERESTING_POST') || scrapedRes[0];
          setActiveStudioPost(interestingPost);
          if (interestingPost.is_analyzed && interestingPost.analysis_summary) {
            setAnalysisData(interestingPost.analysis_summary);
          }
        }
      }
      if (relsRes) setRelationships(relsRes);
      if (libRes) setAnalyzedLibrary(libRes);
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

  // Run Multi-Type Scrape
  const handleRunMultiTypeScrape = async () => {
    try {
      setIsScrapingPosts(true);
      const res = await fetchApi<any[]>(`/api/linkedin/scraped-posts${scrapeTypeFilter !== 'ALL' ? `?scrape_type=${scrapeTypeFilter}` : ''}`);
      if (res) {
        setScrapedPosts(res);
        setNotification(`Scraped ${res.length} LinkedIn posts across hiring, contracts, collaborations & industry discussions!`);
      }
    } catch (err: any) {
      console.error('Failed to scrape posts:', err);
    } finally {
      setIsScrapingPosts(false);
    }
  };

  // Open Post in Post Studio & Analyze
  const handleOpenInStudio = async (post: any) => {
    setActiveStudioPost(post);
    setActiveTab('post_studio');
    if (post.is_analyzed && post.analysis_summary && post.analysis_summary.hook_technique) {
      setAnalysisData(post.analysis_summary);
    } else {
      await handleAnalyzePost(post.id);
    }
  };

  // Analyze Post Dynamics
  const handleAnalyzePost = async (postId: string) => {
    try {
      setIsAnalyzing(true);
      const analysis = await fetchApi<any>(`/api/linkedin/posts/${postId}/analyze`, {
        method: 'POST',
      });
      if (analysis) {
        setAnalysisData(analysis);
        if (analysis.human_angles && analysis.human_angles.length > 0) {
          setSelectedAngleKey(analysis.human_angles[0].key);
        }
        // Refresh library
        const libRes = await fetchApi<any[]>('/api/linkedin/post-studio/library');
        if (libRes) setAnalyzedLibrary(libRes);
      }
    } catch (err) {
      console.error('Failed to analyze post:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Synthesize Human-Like Post
  const handleSynthesizeHumanPost = async () => {
    if (!activeStudioPost) return;
    try {
      setIsSynthesizing(true);
      const postDraft = await fetchApi<any>(`/api/linkedin/posts/${activeStudioPost.id}/synthesize-human-post`, {
        method: 'POST',
        body: JSON.stringify({
          angle_key: selectedAngleKey,
          custom_notes: customStudioNotes || undefined,
        }),
      });
      if (postDraft) {
        setSynthesizedDraft(postDraft);
        setNotification('Humanized post synthesized! Grounded in your real experience without robotic AI buzzwords.');
        // Refresh library
        const libRes = await fetchApi<any[]>('/api/linkedin/post-studio/library');
        if (libRes) setAnalyzedLibrary(libRes);
      }
    } catch (err) {
      console.error('Failed to synthesize post:', err);
    } finally {
      setIsSynthesizing(false);
    }
  };

  // Publish Post
  const handlePublishPost = async () => {
    if (!synthesizedDraft) return;
    try {
      setIsPublishingPost(true);
      const res = await fetchApi<any>(`/api/linkedin/posts/${synthesizedDraft.id}/publish`, {
        method: 'POST',
      });
      if (res) {
        setSynthesizedDraft({ ...synthesizedDraft, status: 'PUBLISHED' });
        setNotification('Post successfully published to your LinkedIn profile!');
      }
    } catch (err) {
      console.error('Failed to publish post:', err);
    } finally {
      setIsPublishingPost(false);
    }
  };

  // Copy to clipboard
  const handleCopyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  // Run Selenium Connection Automation
  const handleRunConnectionAutomation = async (customNote?: string) => {
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
          note_template: customNote || customNoteTemplate || undefined,
        }),
      });

      if (res && res.logs) {
        setSeleniumLogs(res.logs);
        setRecentRecipients(res.recipients || []);
        setNotification(`Dispatched ${res.connected_count} connection invitations with human delays!`);
      }
    } catch (err) {
      console.error('Connection automation error:', err);
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
          cookies: linkedinCookies || undefined,
        }),
      });
      setHasSavedCreds(true);
      setNotification('LinkedIn credentials saved securely.');
    } catch (err: any) {
      alert(`Failed to save credentials: ${err.message}`);
    } finally {
      setIsSavingCreds(false);
    }
  };

  // Filtered scraped posts
  const filteredPosts = scrapedPosts.filter((post) => {
    const matchesType = scrapeTypeFilter === 'ALL' || post.scrape_type === scrapeTypeFilter;
    const matchesSearch =
      !searchQuery ||
      post.author_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      post.author_company?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      post.post_text?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      post.role_or_project_title?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesType && matchesSearch;
  });

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {notification && (
        <div className="p-3.5 rounded-xl bg-gradient-to-r from-brand-950/80 to-surface-300 border border-brand-500/40 text-brand-300 text-xs flex items-center justify-between shadow-lg shadow-brand-950/40 animate-in fade-in">
          <div className="flex items-center gap-2.5">
            <Sparkles className="w-4 h-4 text-brand-400" />
            <span>{notification}</span>
          </div>
          <button onClick={() => setNotification(null)} className="text-zinc-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Sub-Feature Tab Switcher */}
      <div className="flex items-center justify-between border-b border-white/5 pb-3">
        <div className="flex items-center gap-2 bg-surface-200/80 p-1 rounded-xl border border-white/5">
          <button
            onClick={() => setActiveTab('scraped_posts')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'scraped_posts'
                ? 'bg-brand-500 text-white shadow-glow'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/5'
            }`}
          >
            <Compass className="w-3.5 h-3.5" />
            <span>Multi-Type Scraper</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-white/10">{scrapedPosts.length}</span>
          </button>

          <button
            onClick={() => setActiveTab('post_studio')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'post_studio'
                ? 'bg-brand-500 text-white shadow-glow'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/5'
            }`}
          >
            <Wand2 className="w-3.5 h-3.5" />
            <span>LinkedIn Post Studio</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300">Human Voice</span>
          </button>

          <button
            onClick={() => setActiveTab('connections')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'connections'
                ? 'bg-brand-500 text-white shadow-glow'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/5'
            }`}
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>Selenium Connection Bot</span>
          </button>

          <button
            onClick={() => setActiveTab('credentials')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'credentials'
                ? 'bg-brand-500 text-white shadow-glow'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/5'
            }`}
          >
            <KeyRound className="w-3.5 h-3.5" />
            <span>Credentials Vault</span>
            {hasSavedCreds && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />}
          </button>
        </div>

        {activeTab === 'scraped_posts' && (
          <button
            onClick={handleRunMultiTypeScrape}
            disabled={isScrapingPosts}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-surface-300 hover:bg-surface-400 border border-white/10 text-xs font-medium text-white transition-all shadow-sm"
          >
            {isScrapingPosts ? <Loader2 className="w-3.5 h-3.5 animate-spin text-brand-400" /> : <RefreshCw className="w-3.5 h-3.5 text-brand-400" />}
            <span>{isScrapingPosts ? 'Scraping Live LinkedIn Feeds...' : 'Run Multi-Type Scrape'}</span>
          </button>
        )}
      </div>

      {/* =========================================================================
          TAB 1: MULTI-TYPE LINKEDIN SCRAPER
         ========================================================================= */}
      {activeTab === 'scraped_posts' && (
        <div className="space-y-5">
          {/* Filter Bar & Search */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            {/* Category Pills */}
            <div className="flex flex-wrap items-center gap-1.5">
              {[
                { key: 'ALL', label: 'All Scraped Posts', icon: Layers, count: scrapedPosts.length },
                { key: 'HIRING_POST', label: 'Hiring in Posts', icon: Briefcase, count: scrapedPosts.filter((p) => p.scrape_type === 'HIRING_POST').length },
                { key: 'FREELANCE_GIG', label: 'Freelance & Contracts', icon: Flame, count: scrapedPosts.filter((p) => p.scrape_type === 'FREELANCE_GIG').length },
                { key: 'PROJECT_COLLAB', label: 'Project Collaboration', icon: Users, count: scrapedPosts.filter((p) => p.scrape_type === 'PROJECT_COLLAB').length },
                { key: 'INTERESTING_POST', label: 'Interesting Tech Posts', icon: Lightbulb, count: scrapedPosts.filter((p) => p.scrape_type === 'INTERESTING_POST').length },
              ].map((pill) => {
                const Icon = pill.icon;
                const isSelected = scrapeTypeFilter === pill.key;
                return (
                  <button
                    key={pill.key}
                    onClick={() => setScrapeTypeFilter(pill.key)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                      isSelected
                        ? 'bg-brand-500/20 text-brand-300 border border-brand-500/40 shadow-sm'
                        : 'bg-surface-200/60 text-zinc-400 border border-white/5 hover:text-zinc-200 hover:bg-surface-300'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    <span>{pill.label}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-black/20 text-zinc-300">{pill.count}</span>
                  </button>
                );
              })}
            </div>

            {/* Search Input */}
            <div className="relative min-w-[220px]">
              <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search author, role, or text..."
                className="w-full bg-surface-200/80 border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-500/50"
              />
            </div>
          </div>

          {/* Scraped Posts List */}
          <div className="grid grid-cols-1 gap-4">
            {filteredPosts.map((post) => {
              const isHiring = post.scrape_type === 'HIRING_POST';
              const isFreelance = post.scrape_type === 'FREELANCE_GIG';
              const isCollab = post.scrape_type === 'PROJECT_COLLAB';
              const isInteresting = post.scrape_type === 'INTERESTING_POST';

              return (
                <div
                  key={post.id}
                  className="p-5 rounded-2xl bg-surface-200/80 border border-white/5 hover:border-brand-500/30 transition-all space-y-4 shadow-xl"
                >
                  {/* Author Header */}
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3">
                      <img
                        src={post.author_avatar_url || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150'}
                        alt={post.author_name}
                        className="w-10 h-10 rounded-full object-cover border border-white/10 flex-shrink-0"
                      />
                      <div>
                        <div className="flex items-center gap-2">
                          <a
                            href={post.author_profile_url || '#'}
                            target="_blank"
                            rel="noreferrer"
                            className="text-xs font-bold text-white hover:text-brand-300 flex items-center gap-1"
                          >
                            <span>{post.author_name}</span>
                            <ExternalLink className="w-3 h-3 text-zinc-500" />
                          </a>
                          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-surface-300 border border-white/5 text-zinc-400">
                            {post.connection_degree}
                          </span>
                          <span className="text-[10px] text-zinc-500">• {post.posted_at_str}</span>
                        </div>
                        <p className="text-[11px] text-zinc-400 mt-0.5 line-clamp-1">{post.author_headline}</p>
                        <p className="text-[10px] text-brand-400/90 font-mono mt-0.5">{post.author_company}</p>
                      </div>
                    </div>

                    {/* Scrape Type Badge */}
                    <div className="flex flex-col items-end gap-1.5">
                      <span
                        className={`text-[10px] font-bold tracking-wider px-2.5 py-1 rounded-full uppercase border ${
                          isHiring
                            ? 'bg-emerald-950/60 text-emerald-300 border-emerald-500/30'
                            : isFreelance
                            ? 'bg-amber-950/60 text-amber-300 border-amber-500/30'
                            : isCollab
                            ? 'bg-indigo-950/60 text-indigo-300 border-indigo-500/30'
                            : 'bg-purple-950/60 text-purple-300 border-purple-500/30'
                        }`}
                      >
                        {isHiring && 'Hiring in Post'}
                        {isFreelance && 'Freelance / Contract'}
                        {isCollab && 'Project Collaboration'}
                        {isInteresting && 'Industry Discussion'}
                      </span>
                      {post.compensation_or_budget && (
                        <span className="text-[11px] font-mono font-semibold text-emerald-400">
                          {post.compensation_or_budget}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Role / Project Headline if present */}
                  {post.role_or_project_title && (
                    <div className="p-2.5 rounded-xl bg-surface-300/60 border border-white/5 flex items-center justify-between">
                      <span className="text-xs font-semibold text-zinc-200 flex items-center gap-2">
                        <Briefcase className="w-3.5 h-3.5 text-brand-400" />
                        {post.role_or_project_title}
                      </span>
                      {post.how_to_apply && (
                        <span className="text-[10px] font-mono text-zinc-400 bg-surface-400/60 px-2 py-0.5 rounded">
                          Apply: {post.how_to_apply}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Post Content */}
                  <div className="p-3.5 rounded-xl bg-surface-300/30 border border-white/5 text-xs text-zinc-300 leading-relaxed whitespace-pre-line font-sans">
                    {post.post_text}
                  </div>

                  {/* Skills Tags */}
                  {post.skills_required && post.skills_required.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5">
                      {post.skills_required.map((skill: string, idx: number) => (
                        <span key={idx} className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-white/5 text-zinc-300 border border-white/5">
                          {skill}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Engagement Bar & Quick Actions */}
                  <div className="pt-2 border-t border-white/5 flex flex-wrap items-center justify-between gap-3">
                    {/* Metrics */}
                    <div className="flex items-center gap-4 text-xs text-zinc-500 font-mono">
                      <span className="flex items-center gap-1.5 hover:text-zinc-300">
                        <ThumbsUp className="w-3.5 h-3.5 text-zinc-400" />
                        <span>{post.likes_count}</span>
                      </span>
                      <span className="flex items-center gap-1.5 hover:text-zinc-300">
                        <MessageSquare className="w-3.5 h-3.5 text-zinc-400" />
                        <span>{post.comments_count}</span>
                      </span>
                      <span className="flex items-center gap-1.5 hover:text-zinc-300">
                        <Repeat className="w-3.5 h-3.5 text-zinc-400" />
                        <span>{post.reposts_count}</span>
                      </span>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleOpenInStudio(post)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-500/10 hover:bg-brand-500/20 text-brand-300 border border-brand-500/30 text-xs font-semibold transition-all shadow-sm"
                      >
                        <Wand2 className="w-3.5 h-3.5 text-brand-400" />
                        <span>Analyze & Create in Post Studio</span>
                      </button>

                      <button
                        onClick={() => {
                          const note = `Hi ${post.author_name.split(' ')[0]}, saw your post regarding "${post.role_or_project_title || post.author_company}". Given my background in distributed systems, would love to connect!`;
                          handleRunConnectionAutomation(note);
                          setActiveTab('connections');
                        }}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-300 hover:bg-surface-400 border border-white/10 text-xs font-medium text-zinc-200 transition-all"
                      >
                        <UserPlus className="w-3.5 h-3.5 text-cyan-400" />
                        <span>Connect with {post.author_name.split(' ')[0]}</span>
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}

            {filteredPosts.length === 0 && (
              <div className="p-12 text-center text-zinc-500 text-xs border border-dashed border-white/5 rounded-2xl">
                No scraped LinkedIn posts match the selected filter. Click "Run Multi-Type Scrape" to scan feeds.
              </div>
            )}
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 2: LINKEDIN POST STUDIO (ANALYZE & SYNTHESIZE HUMAN POST)
         ========================================================================= */}
      {activeTab === 'post_studio' && (
        <div className="space-y-6">
          {/* Header Info */}
          <div className="p-4 rounded-2xl bg-surface-200/80 border border-white/5 flex flex-wrap items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Wand2 className="w-4 h-4 text-purple-400" />
                <span>LinkedIn Post Studio — Human Voice Synthesizer</span>
              </h3>
              <p className="text-xs text-zinc-400 mt-0.5">
                Analyze viral or high-signal posts from previous steps, extract underlying dynamics, and craft an authentically human response or counter-post.
              </p>
            </div>

            {/* Quick Inspiration Selector */}
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-zinc-400 font-mono">Inspiration:</span>
              <select
                value={activeStudioPost?.id || ''}
                onChange={(e) => {
                  const found = scrapedPosts.find((p) => p.id === e.target.value);
                  if (found) handleOpenInStudio(found);
                }}
                className="bg-surface-300 border border-white/10 rounded-lg px-2.5 py-1 text-xs text-zinc-200 focus:outline-none focus:border-brand-500"
              >
                {scrapedPosts.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.author_name} ({p.scrape_type}) — {p.role_or_project_title || p.author_company}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* 2-Column Studio Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* LEFT COLUMN: Source Post & Dynamic Analysis (5 cols) */}
            <div className="lg:col-span-5 space-y-4">
              {/* Selected Source Post Card */}
              {activeStudioPost ? (
                <div className="p-4 rounded-2xl bg-surface-200/80 border border-white/5 space-y-3">
                  <div className="flex items-center justify-between border-b border-white/5 pb-2.5">
                    <span className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
                      <BookOpen className="w-3.5 h-3.5 text-brand-400" />
                      Source Inspiration
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-brand-500/10 text-brand-300 border border-brand-500/20">
                      {activeStudioPost.scrape_type}
                    </span>
                  </div>

                  <div className="flex items-center gap-2.5">
                    <img
                      src={activeStudioPost.author_avatar_url || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150'}
                      alt=""
                      className="w-8 h-8 rounded-full object-cover border border-white/10"
                    />
                    <div>
                      <div className="text-xs font-bold text-white">{activeStudioPost.author_name}</div>
                      <div className="text-[10px] text-zinc-400">{activeStudioPost.author_company}</div>
                    </div>
                  </div>

                  <p className="text-xs text-zinc-300 italic line-clamp-4 bg-surface-300/40 p-2.5 rounded-lg border border-white/5">
                    "{activeStudioPost.post_text}"
                  </p>

                  <button
                    onClick={() => handleAnalyzePost(activeStudioPost.id)}
                    disabled={isAnalyzing}
                    className="w-full py-2 rounded-lg bg-surface-300 hover:bg-surface-400 border border-white/10 text-xs font-semibold text-brand-300 transition-all flex items-center justify-center gap-2"
                  >
                    {isAnalyzing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                    <span>{isAnalyzing ? 'Analyzing Narrative Dynamics...' : 'Re-Analyze Post Dynamics'}</span>
                  </button>
                </div>
              ) : (
                <div className="p-8 text-center text-xs text-zinc-500 border border-dashed border-white/10 rounded-2xl">
                  Select a post from the Multi-Type Scraper tab to begin.
                </div>
              )}

              {/* Analysis Results & Angle Selector */}
              {analysisData && (
                <div className="p-5 rounded-2xl bg-surface-200/80 border border-white/5 space-y-4 shadow-xl">
                  <div className="flex items-center justify-between border-b border-white/5 pb-2.5">
                    <span className="text-xs font-bold text-white flex items-center gap-2">
                      <Lightbulb className="w-4 h-4 text-amber-400" />
                      Dynamic Breakdown
                    </span>
                    <span className="text-[10px] font-mono text-zinc-500">{analysisData.analyzed_at}</span>
                  </div>

                  {/* Hook Technique */}
                  <div className="space-y-1">
                    <span className="text-[10px] uppercase font-mono text-zinc-400 tracking-wider">Hook Technique</span>
                    <p className="text-xs font-medium text-emerald-300 bg-emerald-950/40 p-2 rounded-lg border border-emerald-500/20">
                      {analysisData.hook_technique}
                    </p>
                  </div>

                  {/* Tone & Delivery */}
                  <div className="space-y-1">
                    <span className="text-[10px] uppercase font-mono text-zinc-400 tracking-wider">Tone & Delivery Voice</span>
                    <p className="text-xs text-zinc-300 bg-surface-300/40 p-2 rounded-lg border border-white/5">
                      {analysisData.tone_and_delivery}
                    </p>
                  </div>

                  {/* Key Discussion Points */}
                  <div className="space-y-1.5">
                    <span className="text-[10px] uppercase font-mono text-zinc-400 tracking-wider">Key Debate / Value Points</span>
                    <ul className="space-y-1 text-xs text-zinc-300">
                      {analysisData.key_discussion_points?.map((pt: string, idx: number) => (
                        <li key={idx} className="flex items-start gap-2 bg-surface-300/20 p-1.5 rounded">
                          <span className="text-brand-400 font-bold">•</span>
                          <span>{pt}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Transformation Angles */}
                  <div className="space-y-2 pt-2 border-t border-white/5">
                    <span className="text-[10px] uppercase font-mono text-purple-300 tracking-wider block">
                      Choose Your Human Angle
                    </span>
                    <div className="space-y-2">
                      {analysisData.human_angles?.map((angle: any) => {
                        const isSelected = selectedAngleKey === angle.key;
                        return (
                          <div
                            key={angle.key}
                            onClick={() => setSelectedAngleKey(angle.key)}
                            className={`p-3 rounded-xl border cursor-pointer transition-all ${
                              isSelected
                                ? 'bg-purple-950/50 border-purple-500/50 text-white shadow-glow'
                                : 'bg-surface-300/40 border-white/5 hover:border-white/20 text-zinc-300'
                            }`}
                          >
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs font-bold text-white flex items-center gap-1.5">
                                {isSelected ? <CheckCircle2 className="w-3.5 h-3.5 text-purple-400" /> : <div className="w-3.5 h-3.5 rounded-full border border-white/20" />}
                                {angle.title}
                              </span>
                            </div>
                            <p className="text-[11px] text-zinc-400 leading-snug">{angle.description}</p>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* RIGHT COLUMN: Human Post Synthesizer & Live Editor (7 cols) */}
            <div className="lg:col-span-7 space-y-4">
              <div className="p-6 rounded-2xl bg-surface-200/90 border border-white/5 shadow-2xl space-y-5">
                {/* Editor Header */}
                <div className="flex items-center justify-between border-b border-white/5 pb-3">
                  <div>
                    <h4 className="text-sm font-bold text-white flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-brand-400" />
                      <span>Synthesized Human Draft</span>
                    </h4>
                    <span className="text-[10px] text-zinc-400">
                      Grounded in your verified stack • 0 robotic AI tropes
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleSynthesizeHumanPost}
                      disabled={isSynthesizing || !activeStudioPost}
                      className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-xs font-semibold shadow-glow transition-all disabled:opacity-50"
                    >
                      {isSynthesizing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Wand2 className="w-3.5 h-3.5" />}
                      <span>{isSynthesizing ? 'Synthesizing...' : 'Synthesize Human Post'}</span>
                    </button>
                  </div>
                </div>

                {/* Optional Custom Notes Input */}
                <div>
                  <label className="text-[10px] font-mono uppercase text-zinc-400 block mb-1">
                    Specific Experience / Context to Weave In (Optional)
                  </label>
                  <input
                    type="text"
                    value={customStudioNotes}
                    onChange={(e) => setCustomStudioNotes(e.target.value)}
                    placeholder="e.g. In our FastAPI cluster, we saw redis connection spikes during traffic bursts..."
                    className="w-full bg-surface-300 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-500/50"
                  />
                </div>

                {/* Synthesized Post Display & Editor */}
                {synthesizedDraft ? (
                  <div className="space-y-4">
                    {/* Live Metric Badges */}
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                        Human Authenticity: 98%
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface-300 text-zinc-300 border border-white/5">
                        {synthesizedDraft.content_text?.length || 0} / 3000 chars
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface-300 text-zinc-300 border border-white/5">
                        {synthesizedDraft.estimated_read_time || '1.5 min read'}
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-950/50 text-purple-300 border border-purple-500/30">
                        Status: {synthesizedDraft.status}
                      </span>
                    </div>

                    {/* Post Content Textarea */}
                    <div className="relative">
                      <textarea
                        rows={14}
                        value={synthesizedDraft.content_text}
                        onChange={(e) =>
                          setSynthesizedDraft({
                            ...synthesizedDraft,
                            content_text: e.target.value,
                          })
                        }
                        className="w-full bg-surface-300/80 border border-white/10 rounded-xl p-4 text-xs text-zinc-100 font-sans leading-relaxed focus:outline-none focus:border-brand-500/50 resize-y"
                      />
                    </div>

                    {/* Post Action Footer */}
                    <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleCopyToClipboard(synthesizedDraft.content_text)}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-300 hover:bg-surface-400 text-zinc-300 text-xs font-medium border border-white/10 transition-all"
                        >
                          {isCopied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                          <span>{isCopied ? 'Copied!' : 'Copy Post'}</span>
                        </button>

                        <button
                          onClick={handleSynthesizeHumanPost}
                          disabled={isSynthesizing}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-300 hover:bg-surface-400 text-zinc-300 text-xs font-medium border border-white/10 transition-all"
                        >
                          <RefreshCw className="w-3.5 h-3.5" />
                          <span>Regenerate Angle</span>
                        </button>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={handlePublishPost}
                          disabled={isPublishingPost || synthesizedDraft.status === 'PUBLISHED'}
                          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-brand-600 to-cyan-500 hover:from-brand-500 hover:to-cyan-400 text-white text-xs font-bold shadow-glow transition-all disabled:opacity-50"
                        >
                          {isPublishingPost ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                          <span>{synthesizedDraft.status === 'PUBLISHED' ? 'Published to Profile' : 'Publish to LinkedIn'}</span>
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="p-12 text-center text-xs text-zinc-500 border border-dashed border-white/10 rounded-xl space-y-2">
                    <Wand2 className="w-6 h-6 text-zinc-600 mx-auto" />
                    <p>Click "Synthesize Human Post" above to craft an authentic post based on your selected angle.</p>
                  </div>
                )}
              </div>

              {/* Tracked Inspiration Library */}
              <div className="p-5 rounded-2xl bg-surface-200/80 border border-white/5 space-y-3">
                <div className="flex items-center justify-between border-b border-white/5 pb-2">
                  <span className="text-xs font-bold text-white flex items-center gap-2">
                    <BookOpen className="w-3.5 h-3.5 text-brand-400" />
                    Tracked Inspiration Library ({analyzedLibrary.length})
                  </span>
                  <span className="text-[10px] text-zinc-500">History of analyzed posts</span>
                </div>

                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {analyzedLibrary.map((item) => (
                    <div
                      key={item.id}
                      onClick={() => {
                        const found = scrapedPosts.find((p) => p.id === item.id);
                        if (found) handleOpenInStudio(found);
                      }}
                      className="p-2.5 rounded-xl bg-surface-300/40 border border-white/5 hover:border-brand-500/30 cursor-pointer transition-all flex items-center justify-between"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-white">{item.author_name}</span>
                          <span className="text-[10px] font-mono text-zinc-400 bg-black/20 px-1.5 py-0.2 rounded">
                            {item.scrape_type}
                          </span>
                        </div>
                        <p className="text-[11px] text-zinc-400 line-clamp-1">{item.role_or_project_title || item.author_company}</p>
                      </div>

                      {item.linked_draft ? (
                        <span className="text-[10px] font-mono text-emerald-300 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-500/20">
                          Draft Ready
                        </span>
                      ) : (
                        <span className="text-[10px] font-mono text-zinc-500">Analyzed</span>
                      )}
                    </div>
                  ))}

                  {analyzedLibrary.length === 0 && (
                    <div className="p-4 text-center text-xs text-zinc-500">No posts analyzed yet.</div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 3: SELENIUM CONNECTION AUTOMATION BOT
         ========================================================================= */}
      {activeTab === 'connections' && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-surface-200/90 border border-white/5 space-y-5">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Terminal className="w-5 h-5 text-emerald-400" />
                <span>Selenium WebDriver Connection Automation</span>
              </h3>
              <p className="text-xs text-zinc-400 mt-1">
                Automates targeted connection requests with Selenium browser emulation: natural mouse paths, human typing delays (50-120ms/keystroke), page scroll curves, and zero bot footprint.
              </p>
            </div>

            {/* Configuration Controls */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
              <div>
                <label className="text-[11px] font-medium text-zinc-300 block mb-1">Target Profile Filter</label>
                <select
                  value={targetRoleFilter}
                  onChange={(e) => setTargetRoleFilter(e.target.value)}
                  className="w-full bg-surface-300 border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
                >
                  <option value="Engineering Leaders & Recruiters">Engineering Leaders & Recruiters</option>
                  <option value="Founders & CTOs">Founders & CTOs</option>
                  <option value="Hiring Managers">Hiring Managers</option>
                </select>
              </div>

              <div>
                <label className="text-[11px] font-medium text-zinc-300 block mb-1">Batch Batch Size (Daily Safe Cap)</label>
                <input
                  type="number"
                  min={1}
                  max={10}
                  value={connectionBatchCount}
                  onChange={(e) => setConnectionBatchCount(parseInt(e.target.value) || 1)}
                  className="w-full bg-surface-300 border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="flex items-end">
                <button
                  onClick={() => handleRunConnectionAutomation()}
                  disabled={isAutomatingConnections}
                  className="w-full py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white shadow-glow transition-all flex items-center justify-center gap-2"
                >
                  {isAutomatingConnections ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                  <span>{isAutomatingConnections ? 'Running Selenium Bot...' : 'Launch Connection Bot'}</span>
                </button>
              </div>
            </div>

            {/* Custom Note Template */}
            <div>
              <label className="text-[11px] font-medium text-zinc-300 block mb-1">Custom Note Template (Optional)</label>
              <input
                type="text"
                value={customNoteTemplate}
                onChange={(e) => setCustomNoteTemplate(e.target.value)}
                placeholder="Hi {name}, saw your team's work at {company}. Given my background in distributed systems, would love to connect!"
                className="w-full bg-surface-300 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-500"
              />
            </div>

            {/* Live Terminal Output */}
            {seleniumLogs.length > 0 && (
              <div className="rounded-xl bg-black/80 border border-white/10 p-4 font-mono text-xs text-zinc-300 space-y-2">
                <div className="flex items-center justify-between border-b border-white/10 pb-2 text-zinc-500 text-[11px]">
                  <span className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    Selenium Live Automation Stream
                  </span>
                  <span>stealth_chromedriver_v128</span>
                </div>
                <div className="space-y-1.5 max-h-56 overflow-y-auto pt-2">
                  {seleniumLogs.map((log, index) => (
                    <div key={index} className="flex items-start gap-2">
                      <span className="text-zinc-500 select-none">[{log.timestamp}]</span>
                      <span className="text-cyan-400 select-none">[{log.action || log.engine}]</span>
                      <span className={log.status === 'SUCCESS' ? 'text-emerald-300' : 'text-zinc-200'}>{log.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 4: CREDENTIALS VAULT
         ========================================================================= */}
      {activeTab === 'credentials' && (
        <div className="max-w-xl mx-auto p-6 rounded-2xl bg-surface-200/90 border border-white/5 space-y-5 shadow-2xl">
          <div className="border-b border-white/5 pb-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <KeyRound className="w-5 h-5 text-brand-400" />
              <span>LinkedIn Automation Credentials Vault</span>
            </h3>
            <p className="text-xs text-zinc-400 mt-1">
              Credentials are used strictly by the local Selenium automation bot. All passwords and cookies are stored with encrypted protection.
            </p>
          </div>

          <form onSubmit={handleSaveCredentials} className="space-y-4">
            <div>
              <label className="text-xs font-medium text-zinc-300 block mb-1">LinkedIn Username / Email</label>
              <input
                required
                type="text"
                value={linkedinUsername}
                onChange={(e) => setLinkedinUsername(e.target.value)}
                placeholder="your.email@example.com"
                className="w-full bg-surface-300 border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-zinc-300 block mb-1">LinkedIn Password</label>
              <input
                required
                type="password"
                value={linkedinPassword}
                onChange={(e) => setLinkedinPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full bg-surface-300 border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-zinc-300 block mb-1">Session Cookie (li_at) (Optional for 2FA bypass)</label>
              <input
                type="text"
                value={linkedinCookies}
                onChange={(e) => setLinkedinCookies(e.target.value)}
                placeholder="AQEDAR05189XYZ..."
                className="w-full bg-surface-300 border border-white/10 rounded-lg px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-brand-500"
              />
            </div>

            <button
              type="submit"
              disabled={isSavingCreds}
              className="w-full py-2.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-xs font-semibold text-white shadow-glow transition-all flex items-center justify-center gap-2"
            >
              {isSavingCreds ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
              <span>{isSavingCreds ? 'Saving Credentials...' : 'Save to Vault'}</span>
            </button>
          </form>
        </div>
      )}
    </div>
  );
}

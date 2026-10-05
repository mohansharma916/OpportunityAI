'use client';

import React, { useState, useEffect } from 'react';
import {
  Globe,
  Plus,
  Sparkles,
  RefreshCw,
  Play,
  KeyRound,
  ShieldCheck,
  CheckCircle2,
  Calendar,
  Layers,
  Search,
  Filter,
  ExternalLink,
  ChevronDown,
  Trash2,
  Clock,
  Briefcase,
  Terminal,
  Loader2,
  Lock,
  Building2,
  DollarSign,
  AlertCircle,
  X,
  Sliders,
} from 'lucide-react';
import { fetchApi } from '@/lib/api';

interface JobScraperViewProps {
  onRefreshAllData?: () => void;
  profile?: any;
}

export function JobScraperView({ onRefreshAllData, profile }: JobScraperViewProps) {
  // Platforms State
  const [platforms, setPlatforms] = useState<any[]>([]);
  const [loadingPlatforms, setLoadingPlatforms] = useState(true);
  const [isDiscoveringAi, setIsDiscoveringAi] = useState(false);
  const [isScrapingAll, setIsScrapingAll] = useState(false);
  const [scrapingSingleId, setScrapingSingleId] = useState<string | null>(null);

  // Opportunities Grouped by Date State
  const [dateData, setDateData] = useState<any>({
    total: 0,
    status_counts: {},
    groups: { today: [], yesterday: [], this_week: [], earlier: [] },
  });
  const [activeDateTab, setActiveDateTab] = useState<'today' | 'yesterday' | 'this_week' | 'earlier'>('today');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [loadingOpps, setLoadingOpps] = useState(true);

  // Add Platform Modal
  const [showAddPlatformModal, setShowAddPlatformModal] = useState(false);
  const [newPlatformName, setNewPlatformName] = useState('');
  const [newPlatformUrl, setNewPlatformUrl] = useState('');
  const [newPlatformCategory, setNewPlatformCategory] = useState('JOB_BOARD');
  const [newRequiresAuth, setNewRequiresAuth] = useState(false);
  const [newAuthUsername, setNewAuthUsername] = useState('');
  const [newAuthPassword, setNewAuthPassword] = useState('');
  const [newAuthNotes, setNewAuthNotes] = useState('');

  // Human Apply Modal
  const [selectedOppForApply, setSelectedOppForApply] = useState<any>(null);
  const [applyUserId, setApplyUserId] = useState('');
  const [applyPassword, setApplyPassword] = useState('');
  const [isExecutingApply, setIsExecutingApply] = useState(false);
  const [applyLogs, setApplyLogs] = useState<any[]>([]);
  const [applyConfirmation, setApplyConfirmation] = useState<string | null>(null);

  // Notification Banner
  const [notification, setNotification] = useState<string | null>(null);

  // Initial Load
  const loadPlatforms = async () => {
    try {
      setLoadingPlatforms(true);
      const data = await fetchApi<any[]>('/api/platforms');
      if (data) setPlatforms(data);
    } catch (err) {
      console.error('Failed to load platforms:', err);
    } finally {
      setLoadingPlatforms(false);
    }
  };

  const loadDateGroupedOpportunities = async () => {
    try {
      setLoadingOpps(true);
      const queryParams = new URLSearchParams();
      if (searchQuery) queryParams.set('search', searchQuery);
      if (statusFilter !== 'ALL') queryParams.set('status', statusFilter);

      const url = `/api/opportunities/grouped-by-date?${queryParams.toString()}`;
      const res = await fetchApi<any>(url);
      if (res) {
        setDateData(res);
      }
    } catch (err) {
      console.error('Failed to load date-grouped opportunities:', err);
    } finally {
      setLoadingOpps(false);
    }
  };

  useEffect(() => {
    loadPlatforms();
    loadDateGroupedOpportunities();
  }, []);

  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      loadDateGroupedOpportunities();
    }, 300);
    return () => clearTimeout(delayDebounce);
  }, [searchQuery, statusFilter]);

  // AI Discover Platforms
  const handleAiDiscoverPlatforms = async () => {
    try {
      setIsDiscoveringAi(true);
      const res = await fetchApi<any>('/api/platforms/ai-discover', {
        method: 'POST',
      });
      if (res && res.discovered_platforms) {
        setNotification(`AI Scraper Agent discovered & added ${res.count} new developer platform(s)!`);
        await loadPlatforms();
      }
    } catch (err) {
      console.error('Failed to discover platforms:', err);
    } finally {
      setIsDiscoveringAi(false);
    }
  };

  // Add User Platform
  const handleCreatePlatform = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPlatformName || !newPlatformUrl) return;

    try {
      await fetchApi('/api/platforms', {
        method: 'POST',
        body: JSON.stringify({
          name: newPlatformName,
          url: newPlatformUrl,
          category: newPlatformCategory,
          requires_auth: newRequiresAuth,
          auth_username: newRequiresAuth ? newAuthUsername : null,
          auth_password: newRequiresAuth ? newAuthPassword : null,
          auth_notes: newAuthNotes,
        }),
      });

      setShowAddPlatformModal(false);
      setNewPlatformName('');
      setNewPlatformUrl('');
      setNewAuthUsername('');
      setNewAuthPassword('');
      setNewAuthNotes('');
      setNewRequiresAuth(false);
      setNotification(`Platform '${newPlatformName}' added to active scraping list.`);
      await loadPlatforms();
    } catch (err) {
      console.error('Failed to add platform:', err);
    }
  };

  // Single Platform Scrape
  const handleScrapeSingle = async (platformId: string, name: string) => {
    try {
      setScrapingSingleId(platformId);
      const res = await fetchApi<any>(`/api/platforms/${platformId}/scrape`, {
        method: 'POST',
      });
      setNotification(`Scraped ${name}: Discovered ${res.discovered_count} opportunities!`);
      await Promise.all([loadPlatforms(), loadDateGroupedOpportunities()]);
    } catch (err) {
      console.error('Failed single scrape:', err);
    } finally {
      setScrapingSingleId(null);
    }
  };

  // Scrape All Active Platforms
  const handleScrapeAll = async () => {
    try {
      setIsScrapingAll(true);
      const res = await fetchApi<any>('/api/platforms/scrape-all', {
        method: 'POST',
      });
      setNotification(`Full multi-platform crawl finished! Discovered ${res.total_discovered} total opportunities.`);
      await Promise.all([loadPlatforms(), loadDateGroupedOpportunities()]);
    } catch (err) {
      console.error('Failed scrape all:', err);
    } finally {
      setIsScrapingAll(false);
    }
  };

  // Toggle Platform Active
  const handleTogglePlatform = async (platform: any) => {
    const nextStatus = platform.status === 'ACTIVE' ? 'PAUSED' : 'ACTIVE';
    try {
      await fetchApi(`/api/platforms/${platform.id}`, {
        method: 'PUT',
        body: JSON.stringify({ status: nextStatus }),
      });
      await loadPlatforms();
    } catch (err) {
      console.error('Failed to toggle platform:', err);
    }
  };

  // Delete Platform
  const handleDeletePlatform = async (platformId: string) => {
    try {
      await fetchApi(`/api/platforms/${platformId}`, {
        method: 'DELETE',
      });
      await loadPlatforms();
    } catch (err) {
      console.error('Failed to delete platform:', err);
    }
  };

  // Update Status Maintained by User
  const handleUpdateUserStatus = async (oppId: string, newStatus: string) => {
    try {
      await fetchApi(`/api/opportunities/${oppId}/user-status`, {
        method: 'PUT',
        body: JSON.stringify({ status: newStatus }),
      });
      await loadDateGroupedOpportunities();
      setNotification(`Opportunity status updated to ${newStatus}.`);
    } catch (err) {
      console.error('Failed to update status:', err);
    }
  };

  // Open Human Apply Modal
  const handleOpenHumanApply = (opp: any) => {
    setSelectedOppForApply(opp);
    setApplyLogs([]);
    setApplyConfirmation(null);

    // Check if platform has saved username
    const matchingPlatform = platforms.find((p) => p.name.toLowerCase() === opp.source?.toLowerCase());
    if (matchingPlatform && matchingPlatform.auth_username) {
      setApplyUserId(matchingPlatform.auth_username);
    } else if (profile?.email) {
      setApplyUserId(profile.email);
    } else {
      setApplyUserId('');
    }
    setApplyPassword('');
  };

  // Execute Human Apply
  const handleExecuteHumanApply = async () => {
    if (!selectedOppForApply) return;
    try {
      setIsExecutingApply(true);
      setApplyLogs([
        { step: 'INITIALIZING', message: 'Launching stealth browser with human emulation hooks...', status: 'INFO' },
      ]);

      const res = await fetchApi<any>(`/api/opportunities/${selectedOppForApply.id}/human-apply`, {
        method: 'POST',
        body: JSON.stringify({
          user_id: applyUserId || null,
          password: applyPassword || null,
        }),
      });

      if (res && res.steps) {
        setApplyLogs(res.steps);
        setApplyConfirmation(res.confirmation_reference);
        await loadDateGroupedOpportunities();
      }
    } catch (err) {
      console.error('Failed human apply:', err);
    } finally {
      setIsExecutingApply(false);
    }
  };

  // Get active list for current date tab
  const currentTabOpps = dateData.groups[activeDateTab] || [];

  return (
    <div className="space-y-8 animate-in fade-in duration-300 pb-16">
      {/* Notification Toast */}
      {notification && (
        <div className="p-4 rounded-xl bg-gradient-to-r from-brand-600/30 to-cyan-500/20 border border-brand-500/40 text-brand-200 text-xs font-medium flex items-center justify-between shadow-lg">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-brand-300" />
            <span>{notification}</span>
          </div>
          <button onClick={() => setNotification(null)} className="text-zinc-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Hero Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-surface-300 via-surface-300/90 to-surface-200 border border-white/10 shadow-xl flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2.5 mb-2">
            <span className="px-2.5 py-0.5 rounded-full bg-brand-500/20 text-brand-300 text-[10px] font-mono font-bold border border-brand-500/30 flex items-center gap-1">
              <Globe className="w-3 h-3" />
              Feature #1
            </span>
            <span className="px-2.5 py-0.5 rounded-full bg-emerald-950/60 text-emerald-400 text-[10px] font-mono border border-emerald-800/40 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3" />
              Human-Paced Automation Ready
            </span>
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight">
            Job & Project Web Scraper Tool
          </h1>
          <p className="text-xs text-zinc-400 mt-1 max-w-2xl leading-relaxed">
            Manage platforms (User & AI-added), scrape opportunities across remote boards & GitHub bounties,
            track application status by Date, and submit applications with human-like browser automation.
          </p>
        </div>

        {/* Global Action Buttons */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => setShowAddPlatformModal(true)}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold bg-surface-200 hover:bg-surface-100 text-white border border-white/10 transition-all shadow-sm"
          >
            <Plus className="w-4 h-4 text-brand-400" />
            <span>+ Add Platform</span>
          </button>

          <button
            onClick={handleAiDiscoverPlatforms}
            disabled={isDiscoveringAi}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold bg-indigo-950/60 hover:bg-indigo-900/80 text-indigo-300 border border-indigo-700/50 transition-all shadow-sm disabled:opacity-50"
          >
            {isDiscoveringAi ? (
              <Loader2 className="w-4 h-4 animate-spin text-indigo-300" />
            ) : (
              <Sparkles className="w-4 h-4 text-indigo-400" />
            )}
            <span>AI Discover Platforms</span>
          </button>

          <button
            onClick={handleScrapeAll}
            disabled={isScrapingAll}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-brand-600 to-cyan-500 hover:from-brand-500 hover:to-cyan-400 text-white shadow-glow transition-all disabled:opacity-50"
          >
            {isScrapingAll ? (
              <Loader2 className="w-4 h-4 animate-spin text-white" />
            ) : (
              <Play className="w-4 h-4 text-white fill-white" />
            )}
            <span>Scrape All Platforms</span>
          </button>
        </div>
      </div>

      {/* SECTION 1: Active Scraping Platforms Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-white/5 pb-2">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-brand-400" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              Scraping Platforms ({platforms.length})
            </h2>
          </div>
          <span className="text-[11px] text-zinc-400">
            User-configured & AI-discovered sources with credential support
          </span>
        </div>

        {loadingPlatforms ? (
          <div className="p-8 text-center text-zinc-400 text-xs flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" /> Loading platforms...
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {platforms.map((p) => {
              const isScrapingThis = scrapingSingleId === p.id;
              const isAiAdded = p.added_by === 'AI';

              return (
                <div
                  key={p.id}
                  className={`p-4 rounded-xl border transition-all flex flex-col justify-between ${
                    p.status === 'ACTIVE'
                      ? 'bg-surface-300/80 border-white/10 hover:border-brand-500/40 shadow-sm'
                      : 'bg-surface-400/30 border-white/5 opacity-60'
                  }`}
                >
                  <div>
                    {/* Header */}
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="text-xs font-bold text-white truncate">{p.name}</h3>
                          <span
                            className={`text-[9px] font-mono px-1.5 py-0.5 rounded font-semibold ${
                              isAiAdded
                                ? 'bg-indigo-950/60 text-indigo-300 border border-indigo-800/40'
                                : 'bg-brand-950/60 text-brand-300 border border-brand-800/40'
                            }`}
                          >
                            {isAiAdded ? 'AI Added' : 'User Added'}
                          </span>
                        </div>
                        <a
                          href={p.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[11px] text-zinc-400 hover:text-cyan-400 flex items-center gap-1 mt-0.5 truncate max-w-[220px]"
                        >
                          <span className="truncate">{p.url}</span>
                          <ExternalLink className="w-2.5 h-2.5 shrink-0" />
                        </a>
                      </div>

                      {/* Status Toggle */}
                      <button
                        onClick={() => handleTogglePlatform(p)}
                        className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-bold transition-all ${
                          p.status === 'ACTIVE'
                            ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/50'
                            : 'bg-zinc-800 text-zinc-400 border border-zinc-700'
                        }`}
                      >
                        {p.status}
                      </button>
                    </div>

                    {/* Metadata & Auth details */}
                    <div className="space-y-1.5 mt-3 pt-3 border-t border-white/5 text-[11px]">
                      <div className="flex items-center justify-between text-zinc-400">
                        <span>Category:</span>
                        <span className="text-zinc-300 font-mono text-[10px]">{p.category}</span>
                      </div>
                      <div className="flex items-center justify-between text-zinc-400">
                        <span>Authentication:</span>
                        <span className="flex items-center gap-1 font-mono text-[10px]">
                          {p.requires_auth ? (
                            <span className="text-amber-400 flex items-center gap-1">
                              <Lock className="w-2.5 h-2.5" />
                              {p.auth_username ? 'Credentials Stored' : 'Requires Login'}
                            </span>
                          ) : (
                            <span className="text-zinc-400">Public Access</span>
                          )}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-zinc-400">
                        <span>Opportunities Scraped:</span>
                        <span className="text-brand-300 font-bold font-mono">{p.total_opportunities_found || 0}</span>
                      </div>
                    </div>
                  </div>

                  {/* Platform Card Footer */}
                  <div className="flex items-center justify-between pt-3 mt-3 border-t border-white/5">
                    <button
                      onClick={() => handleScrapeSingle(p.id, p.name)}
                      disabled={isScrapingThis}
                      className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-bold bg-brand-500/10 hover:bg-brand-500/20 text-brand-300 border border-brand-500/30 transition-all disabled:opacity-50"
                    >
                      {isScrapingThis ? (
                        <Loader2 className="w-3 h-3 animate-spin text-brand-300" />
                      ) : (
                        <Play className="w-3 h-3 text-brand-400" />
                      )}
                      <span>Scrape Now</span>
                    </button>

                    <button
                      onClick={() => handleDeletePlatform(p.id)}
                      className="text-zinc-400 hover:text-rose-400 p-1 rounded transition-colors"
                      title="Remove platform"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* SECTION 2: Opportunities Grouped by Date & Track Status Maintained by User */}
      <div className="space-y-4 pt-4 border-t border-white/5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-brand-400" />
              <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                Opportunities Grouped by Date ({dateData.total || 0})
              </h2>
            </div>
            <p className="text-[11px] text-zinc-400 mt-0.5">
              Review scraped postings by date, maintain candidate status, and apply with human automation.
            </p>
          </div>

          {/* Search & Status Filter Controls */}
          <div className="flex flex-wrap items-center gap-2.5">
            <div className="relative min-w-[200px]">
              <Search className="w-3.5 h-3.5 text-zinc-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filter by role, company..."
                className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-surface-400/80 border border-white/10 text-xs text-white placeholder-zinc-400 focus:outline-none focus:border-brand-500"
              />
            </div>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg bg-surface-400/80 border border-white/10 text-xs text-zinc-300 font-medium focus:outline-none focus:border-brand-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="DISCOVERED">Discovered</option>
              <option value="REVIEWING">Reviewing</option>
              <option value="APPLIED">Applied</option>
              <option value="INTERVIEWING">Interviewing</option>
              <option value="OFFER">Offer</option>
              <option value="REJECTED">Rejected</option>
              <option value="ARCHIVED">Archived</option>
            </select>
          </div>
        </div>

        {/* Date Tabs (Today, Yesterday, This Week, Earlier) */}
        <div className="flex items-center gap-2 border-b border-white/5 pb-2 overflow-x-auto">
          {[
            { id: 'today', label: 'Today', count: dateData.groups.today?.length || 0 },
            { id: 'yesterday', label: 'Yesterday', count: dateData.groups.yesterday?.length || 0 },
            { id: 'this_week', label: 'This Week', count: dateData.groups.this_week?.length || 0 },
            { id: 'earlier', label: 'Earlier / Archive', count: dateData.groups.earlier?.length || 0 },
          ].map((tab) => {
            const isActive = activeDateTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveDateTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                  isActive
                    ? 'bg-brand-500/20 text-brand-300 border border-brand-500/40 shadow-sm'
                    : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'
                }`}
              >
                <span>{tab.label}</span>
                <span
                  className={`text-[10px] font-mono px-1.5 py-0.2 rounded-full ${
                    isActive ? 'bg-brand-400 text-black font-extrabold' : 'bg-surface-200 text-zinc-400'
                  }`}
                >
                  {tab.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Opportunities List for Active Tab */}
        {loadingOpps ? (
          <div className="p-12 text-center text-zinc-400 text-xs flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-brand-400" /> Loading date-grouped opportunities...
          </div>
        ) : currentTabOpps.length === 0 ? (
          <div className="p-12 rounded-2xl bg-surface-300/40 border border-white/5 text-center space-y-3">
            <Briefcase className="w-8 h-8 text-zinc-400 mx-auto" />
            <p className="text-xs text-zinc-400">
              No opportunities found in <span className="text-white font-bold">{activeDateTab}</span>.
            </p>
            <button
              onClick={handleScrapeAll}
              className="px-3.5 py-1.5 rounded-lg text-xs font-bold bg-brand-500/10 text-brand-300 border border-brand-500/30 hover:bg-brand-500/20 transition-all inline-flex items-center gap-1.5"
            >
              <Play className="w-3 h-3" />
              <span>Scrape Live Platforms</span>
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {currentTabOpps.map((opp: any) => {
              const matchScore = Math.round(opp.overall_match_score || 80);
              const isApplied = opp.status === 'APPLIED';

              return (
                <div
                  key={opp.id}
                  className="p-4 rounded-xl bg-surface-300/80 border border-white/10 hover:border-white/20 transition-all shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  {/* Left Column: Job & Company Info */}
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-brand-500/15 text-brand-300 border border-brand-500/30">
                        {opp.source || 'Scraped Portal'}
                      </span>
                      <span className="text-[10px] text-zinc-400 flex items-center gap-1 font-mono">
                        <Clock className="w-3 h-3" /> {opp.date_formatted}
                      </span>
                      {matchScore >= 80 && (
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-950/60 text-emerald-400 border border-emerald-800/40 font-bold">
                          {matchScore}% Fit Match
                        </span>
                      )}
                    </div>

                    <h3 className="text-sm font-bold text-white tracking-tight truncate">
                      {opp.title}
                    </h3>

                    <div className="flex flex-wrap items-center gap-3 text-xs text-zinc-400">
                      <span className="text-zinc-200 font-semibold flex items-center gap-1">
                        <Building2 className="w-3.5 h-3.5 text-zinc-400" /> {opp.company_name}
                      </span>
                      <span>•</span>
                      <span>{opp.location || 'Remote'}</span>
                      {opp.salary_min && (
                        <>
                          <span>•</span>
                          <span className="text-emerald-400 font-mono font-medium">
                            ${opp.salary_min.toLocaleString()} - ${opp.salary_max?.toLocaleString()}
                          </span>
                        </>
                      )}
                    </div>

                    {/* Required Skills Chips */}
                    {opp.required_skills && opp.required_skills.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {opp.required_skills.slice(0, 4).map((s: string, idx: number) => (
                          <span
                            key={idx}
                            className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface-400 text-zinc-300 border border-white/5"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Right Column: User Status Selector & Human Apply Button */}
                  <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 shrink-0">
                    {/* User Maintained Status Selector */}
                    <div className="space-y-1">
                      <span className="text-[9px] font-mono uppercase text-zinc-400 font-bold block">
                        My Tracked Status:
                      </span>
                      <select
                        value={opp.status}
                        onChange={(e) => handleUpdateUserStatus(opp.id, e.target.value)}
                        className={`text-xs font-bold px-2.5 py-1.5 rounded-lg border focus:outline-none ${
                          opp.status === 'APPLIED'
                            ? 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60'
                            : opp.status === 'INTERVIEWING'
                            ? 'bg-purple-950/80 text-purple-300 border-purple-700/60'
                            : opp.status === 'OFFER'
                            ? 'bg-amber-950/80 text-amber-300 border-amber-700/60'
                            : opp.status === 'REJECTED'
                            ? 'bg-rose-950/80 text-rose-300 border-rose-700/60'
                            : 'bg-surface-400 text-zinc-300 border-white/10'
                        }`}
                      >
                        <option value="DISCOVERED">Discovered</option>
                        <option value="REVIEWING">Reviewing</option>
                        <option value="APPLIED">Applied</option>
                        <option value="INTERVIEWING">Interviewing</option>
                        <option value="OFFER">Offer Received</option>
                        <option value="REJECTED">Rejected</option>
                        <option value="ARCHIVED">Archived</option>
                      </select>
                    </div>

                    {/* Apply Action Button */}
                    <div className="pt-3 sm:pt-4">
                      {isApplied ? (
                        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 text-xs font-bold border border-emerald-500/30">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Applied</span>
                        </div>
                      ) : (
                        <button
                          onClick={() => handleOpenHumanApply(opp)}
                          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold bg-gradient-to-r from-brand-600 to-cyan-500 hover:from-brand-500 hover:to-cyan-400 text-white shadow-glow transition-all"
                        >
                          <Play className="w-3 h-3 fill-white" />
                          <span>Human Apply</span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* MODAL 1: Add Scraping Target Platform */}
      {showAddPlatformModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-surface-300 rounded-2xl border border-white/10 shadow-2xl p-6 space-y-4 animate-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <div className="flex items-center gap-2">
                <Globe className="w-4 h-4 text-brand-400" />
                <h3 className="text-sm font-bold text-white">Add New Scraping Target Platform</h3>
              </div>
              <button onClick={() => setShowAddPlatformModal(false)} className="text-zinc-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreatePlatform} className="space-y-4 text-xs">
              <div>
                <label className="block text-zinc-300 font-medium mb-1">Platform Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Wellfound Startups, RemoteOK, Indeed Tech"
                  value={newPlatformName}
                  onChange={(e) => setNewPlatformName(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-surface-400 border border-white/10 text-white focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-zinc-300 font-medium mb-1">Target Portal URL / Feed</label>
                <input
                  type="url"
                  required
                  placeholder="https://example.com/jobs"
                  value={newPlatformUrl}
                  onChange={(e) => setNewPlatformUrl(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-surface-400 border border-white/10 text-white focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-zinc-300 font-medium mb-1">Category</label>
                <select
                  value={newPlatformCategory}
                  onChange={(e) => setNewPlatformCategory(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-surface-400 border border-white/10 text-white focus:outline-none focus:border-brand-500"
                >
                  <option value="JOB_BOARD">Job Board / Portal</option>
                  <option value="PROJECT_CONTRIBUTIONS">Project Contribution / Bug Bounty</option>
                  <option value="FREELANCE">Freelance / Contract Hub</option>
                  <option value="STARTUPS">Startup Network</option>
                  <option value="COMMUNITY">Community / Tech Forum</option>
                </select>
              </div>

              {/* Authentication Credentials Section */}
              <div className="p-3.5 rounded-xl bg-surface-400/50 border border-white/5 space-y-3">
                <label className="flex items-center gap-2 text-zinc-200 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={newRequiresAuth}
                    onChange={(e) => setNewRequiresAuth(e.target.checked)}
                    className="rounded bg-surface-300 border-zinc-700 text-brand-500"
                  />
                  <span className="font-bold flex items-center gap-1">
                    <KeyRound className="w-3.5 h-3.5 text-amber-400" />
                    This platform requires login / user credentials to apply
                  </span>
                </label>

                {newRequiresAuth && (
                  <div className="space-y-3 pt-2">
                    <div>
                      <label className="block text-zinc-400 text-[11px] mb-1">User ID / Username / Email</label>
                      <input
                        type="text"
                        placeholder="candidate@email.com or username"
                        value={newAuthUsername}
                        onChange={(e) => setNewAuthUsername(e.target.value)}
                        className="w-full p-2 rounded bg-surface-300 border border-white/10 text-white focus:outline-none focus:border-brand-500"
                      />
                    </div>
                    <div>
                      <label className="block text-zinc-400 text-[11px] mb-1">Password</label>
                      <input
                        type="password"
                        placeholder="••••••••••••"
                        value={newAuthPassword}
                        onChange={(e) => setNewAuthPassword(e.target.value)}
                        className="w-full p-2 rounded bg-surface-300 border border-white/10 text-white focus:outline-none focus:border-brand-500"
                      />
                    </div>
                    <div>
                      <label className="block text-zinc-400 text-[11px] mb-1">Automation Notes (Optional)</label>
                      <input
                        type="text"
                        placeholder="e.g. 2FA via SMS, click Google Auth, etc."
                        value={newAuthNotes}
                        onChange={(e) => setNewAuthNotes(e.target.value)}
                        className="w-full p-2 rounded bg-surface-300 border border-white/10 text-white focus:outline-none focus:border-brand-500"
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddPlatformModal(false)}
                  className="px-4 py-2 rounded-lg text-zinc-400 hover:text-white font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-brand-500 hover:bg-brand-400 text-white font-bold shadow-glow"
                >
                  Register Platform
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Human-Like Automation Runner Console */}
      {selectedOppForApply && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-2xl bg-surface-300 rounded-2xl border border-white/10 shadow-2xl p-6 space-y-4 animate-in zoom-in-95">
            {/* Header */}
            <div className="flex items-start justify-between border-b border-white/5 pb-3">
              <div>
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <h3 className="text-sm font-bold text-white">Human-Like Application Automation</h3>
                </div>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Submitting to <span className="text-brand-300 font-semibold">{selectedOppForApply.company_name}</span> ({selectedOppForApply.title})
                </p>
              </div>
              <button
                onClick={() => setSelectedOppForApply(null)}
                className="text-zinc-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Credentials & Human Simulation Configuration */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-xl bg-surface-400/50 border border-white/5 text-xs">
              <div>
                <label className="block text-zinc-300 font-medium mb-1 flex items-center gap-1">
                  <KeyRound className="w-3.5 h-3.5 text-brand-400" /> Platform User ID / Email
                </label>
                <input
                  type="text"
                  value={applyUserId}
                  onChange={(e) => setApplyUserId(e.target.value)}
                  placeholder="user@example.com"
                  className="w-full p-2 rounded bg-surface-300 border border-white/10 text-white focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-zinc-300 font-medium mb-1 flex items-center gap-1">
                  <Lock className="w-3.5 h-3.5 text-brand-400" /> Platform Password
                </label>
                <input
                  type="password"
                  value={applyPassword}
                  onChange={(e) => setApplyPassword(e.target.value)}
                  placeholder="•••••••••••• (if required)"
                  className="w-full p-2 rounded bg-surface-300 border border-white/10 text-white focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="col-span-1 md:col-span-2 flex flex-wrap items-center gap-4 text-[11px] text-zinc-400 pt-2 border-t border-white/5">
                <span className="flex items-center gap-1 text-emerald-400">
                  <CheckCircle2 className="w-3 h-3" /> Human typing cadence (45-65 WPM)
                </span>
                <span className="flex items-center gap-1 text-emerald-400">
                  <CheckCircle2 className="w-3 h-3" /> Natural micro-pauses (1.2s - 2.5s)
                </span>
                <span className="flex items-center gap-1 text-emerald-400">
                  <CheckCircle2 className="w-3 h-3" /> Auto-attaches Tailored Resume PDF
                </span>
              </div>
            </div>

            {/* Live Human Simulation Execution Terminal */}
            <div className="p-4 rounded-xl bg-black/90 border border-white/10 font-mono text-[11px] text-zinc-300 space-y-2 max-h-64 overflow-y-auto">
              <div className="flex items-center justify-between text-zinc-500 text-[10px] pb-1 border-b border-white/10">
                <span className="flex items-center gap-1.5 text-zinc-400 font-bold">
                  <Terminal className="w-3 h-3" /> BROWSER AUTOMATION CONSOLE
                </span>
                <span>STATUS: {isExecutingApply ? 'SIMULATING_HUMAN_ACTIONS' : applyConfirmation ? 'SUBMITTED' : 'STANDBY'}</span>
              </div>

              {applyLogs.length === 0 ? (
                <div className="text-zinc-600 italic py-4 text-center">
                  Click 'Start Human-Like Automation' to launch browser runner and submit application.
                </div>
              ) : (
                <div className="space-y-1.5 pt-1">
                  {applyLogs.map((log, idx) => (
                    <div key={idx} className="flex items-start gap-2 animate-in fade-in">
                      <span className="text-zinc-500 shrink-0">{log.time || 'NOW'}</span>
                      <span className="text-cyan-400 font-semibold shrink-0">[{log.step}]</span>
                      <span className="text-zinc-200">{log.message}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Confirmation Banner */}
            {applyConfirmation && (
              <div className="p-3 rounded-xl bg-emerald-950/70 border border-emerald-500/40 text-emerald-300 text-xs font-bold flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  Submission Confirmed! Ref: #{applyConfirmation}
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-900/60 text-emerald-200">
                  Status: APPLIED
                </span>
              </div>
            )}

            {/* Modal Actions */}
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setSelectedOppForApply(null)}
                className="px-4 py-2 rounded-lg text-xs font-medium text-zinc-400 hover:text-white"
              >
                Close
              </button>
              <button
                type="button"
                onClick={handleExecuteHumanApply}
                disabled={isExecutingApply}
                className="flex items-center gap-2 px-5 py-2 rounded-lg text-xs font-bold bg-gradient-to-r from-brand-600 to-cyan-500 hover:from-brand-500 hover:to-cyan-400 text-white shadow-glow transition-all disabled:opacity-50"
              >
                {isExecutingApply ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Emulating Human Submission...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-white" />
                    <span>Start Human-Like Automation</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

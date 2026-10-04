'use client';

import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Command,
  Search,
  Bell,
  RefreshCw,
  Plus,
  Terminal,
  Activity,
  CheckCircle2,
  Sliders,
  Send,
  Zap,
  LogOut,
} from 'lucide-react';
import { fetchApi } from '@/lib/api';
import { Navigation } from '@/components/Navigation';
import { DailyBriefingCard } from '@/components/DailyBriefingCard';
import { KanbanBoard } from '@/components/KanbanBoard';
import { OpportunityDetailModal } from '@/components/OpportunityDetailModal';
import { ApplicationReviewModal } from '@/components/ApplicationReviewModal';
import { ManualImportModal } from '@/components/ManualImportModal';
import { AICommandBar } from '@/components/AICommandBar';
import { ActivityFeed } from '@/components/ActivityFeed';
import { AnalyticsView } from '@/components/AnalyticsView';
import { ProfileView } from '@/components/ProfileView';
import { ContactsView } from '@/components/ContactsView';
import { ContributionsView } from '@/components/ContributionsView';
import { ResumesView } from '@/components/ResumesView';
import { AuthScreen } from '@/components/AuthScreen';
import { OnboardingWizard } from '@/components/OnboardingWizard';

export default function OpportunityOSApp() {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [user, setUser] = useState<any>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [onboardingSuccessBanner, setOnboardingSuccessBanner] = useState<any>(null);

  const [profile, setProfile] = useState<any>(null);
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [briefing, setBriefing] = useState<any>(null);
  const [activities, setActivities] = useState<any[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [contacts, setContacts] = useState<any[]>([]);
  const [outreachSequences, setOutreachSequences] = useState<any[]>([]);
  const [resumes, setResumes] = useState<any[]>([]);
  const [verifiedAnswers, setVerifiedAnswers] = useState<any[]>([]);

  // Modals & triggers
  const [selectedOpportunity, setSelectedOpportunity] = useState<any>(null);
  const [selectedApplication, setSelectedApplication] = useState<any>(null);
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [isCommandBarOpen, setIsCommandBarOpen] = useState(false);
  const [loadingDiscovery, setLoadingDiscovery] = useState(false);

  // Global Keyboard shortcut listener: Cmd+K / Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsCommandBarOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Check stored credentials or demo user on mount
  useEffect(() => {
    const initAuth = async () => {
      try {
        const stored = localStorage.getItem('opportunity_user');
        if (stored) {
          const parsed = JSON.parse(stored);
          setUser(parsed);
          try {
            const fresh = await fetchApi<any>(`/api/auth/me?user_id=${parsed.id}`);
            if (fresh && fresh.id) {
              setUser(fresh);
              localStorage.setItem('opportunity_user', JSON.stringify(fresh));
            }
          } catch (_) {}
        }
      } catch (err) {
        console.warn('Auth check error:', err);
      } finally {
        setAuthLoading(false);
      }
    };
    initAuth();
  }, []);

  // Fetch all primary datasets
  const loadData = async () => {
    try {
      const [pData, oData, bData, aData, anData, cData, outData, rData, vAns] = await Promise.all([
        fetchApi<any>('/api/profile'),
        fetchApi<any[]>('/api/opportunities'),
        fetchApi<any>('/api/briefing'),
        fetchApi<any[]>('/api/activity?limit=35'),
        fetchApi<any>('/api/analytics'),
        fetchApi<any[]>('/api/contacts'),
        fetchApi<any[]>('/api/outreach'),
        fetchApi<any[]>('/api/resumes'),
        fetchApi<any[]>('/api/profile/answers'),
      ]);

      setProfile(pData);
      setOpportunities(oData);
      setBriefing(bData);
      setActivities(aData);
      setAnalytics(anData);
      setContacts(cData);
      setOutreachSequences(outData);
      setResumes(rData);
      setVerifiedAnswers(vAns);
    } catch (err: any) {
      console.error('Failed to load application data:', err);
    }
  };

  useEffect(() => {
    if (user && user.onboarding_completed) {
      loadData();
    }
  }, [user]);

  const handleRefreshDiscovery = async () => {
    setLoadingDiscovery(true);
    try {
      await fetchApi('/api/opportunities/discover', { method: 'POST' });
      await loadData();
    } catch (err: any) {
      alert(`Discovery failed: ${err.message}`);
    } finally {
      setLoadingDiscovery(false);
    }
  };

  const handleAutoApply = async () => {
    try {
      const res: any = await fetchApi('/api/applications/auto-run', { method: 'POST' });
      alert(res.message);
      await loadData();
    } catch (err: any) {
      alert(`Auto-Apply failed: ${err.message}`);
    }
  };

  const handleSignOut = async () => {
    try {
      await fetchApi('/api/auth/logout', { method: 'POST' });
    } catch (_) {}
    localStorage.removeItem('opportunity_user');
    setUser(null);
    setShowOnboarding(false);
    setOnboardingSuccessBanner(null);
  };

  // 1. Loading screen
  if (authLoading) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center">
        <div className="w-8 h-8 rounded-full border-2 border-brand-500 border-t-transparent animate-spin mb-3 shadow-glow" />
        <p className="text-xs font-mono text-zinc-400">Initializing OpportunityOS Engine...</p>
      </div>
    );
  }

  // 2. Unauthenticated: Login & Signup Screen
  if (!user) {
    return (
      <AuthScreen
        onAuthenticated={(authenticatedUser) => {
          setUser(authenticatedUser);
          localStorage.setItem('opportunity_user', JSON.stringify(authenticatedUser));
          if (authenticatedUser.onboarding_completed) {
            loadData();
          }
        }}
      />
    );
  }

  // 3. Candidate Onboarding Wizard (Resume Upload, AI Parse, Missing Info, Section Verification, Global Crawl)
  if (!user.onboarding_completed || showOnboarding) {
    return (
      <OnboardingWizard
        user={user}
        onSignOut={handleSignOut}
        onCompleted={(result) => {
          const updatedUser = { ...user, onboarding_completed: true };
          setUser(updatedUser);
          localStorage.setItem('opportunity_user', JSON.stringify(updatedUser));
          setShowOnboarding(false);
          setOnboardingSuccessBanner(result);
          loadData();
        }}
      />
    );
  }

  return (
    <div className="flex min-h-screen bg-background text-zinc-100">
      {/* Sidebar Navigation */}
      <Navigation
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        automationLevel={profile?.automation_level ?? 3}
        user={user}
        onLogout={handleSignOut}
      />

      {/* Main Content Area */}
      <main className="flex-1 ml-64 min-h-screen flex flex-col">
        {/* Top Floating Command Bar & Control Header */}
        <header className="h-16 border-b border-white/5 bg-surface-400/80 backdrop-blur-md sticky top-0 z-20 px-8 flex items-center justify-between">
          {/* Quick AI Command trigger input */}
          <div className="flex items-center gap-3 w-96">
            <button
              onClick={() => setIsCommandBarOpen(true)}
              className="w-full flex items-center justify-between px-3.5 py-1.5 rounded-lg bg-surface-200/90 border border-white/10 hover:border-brand-500/40 text-xs text-zinc-400 transition-all shadow-sm group"
            >
              <span className="flex items-center gap-2">
                <Sparkles className="w-3.5 h-3.5 text-brand-400 group-hover:animate-pulse" />
                <span>Ask AI Agent or execute command...</span>
              </span>
              <kbd className="text-[10px] font-mono bg-white/5 text-zinc-400 px-1.5 py-0.5 rounded border border-white/5">
                ⌘K
              </kbd>
            </button>
          </div>

          {/* Right Action Icons */}
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-950/40 border border-emerald-800/40 text-emerald-400 text-[10px] font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
              <span>Orchestration Worker Active</span>
            </div>

            <button
              onClick={() => setIsImportOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-medium text-white border border-white/10 hover:border-white/20 transition-all"
            >
              <Plus className="w-3.5 h-3.5 text-brand-400" />
              <span>Import URL/Text</span>
            </button>

            <button
              onClick={handleSignOut}
              title="Sign Out of OpportunityOS"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-200/80 hover:bg-rose-950/30 text-xs font-medium text-zinc-300 hover:text-rose-300 border border-white/10 hover:border-rose-500/30 transition-all shadow-sm"
            >
              <LogOut className="w-3.5 h-3.5 text-zinc-400 group-hover:text-rose-300" />
              <span>Sign Out</span>
            </button>
          </div>
        </header>

        {/* Viewport Content */}
        <div className="p-8 flex-1 max-w-7xl w-full mx-auto">
          {onboardingSuccessBanner && (
            <div className="mb-6 p-4 rounded-xl bg-gradient-to-r from-emerald-950/80 to-surface-300 border border-emerald-500/40 flex items-center justify-between shadow-glow-emerald animate-in fade-in">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white flex items-center gap-2">
                    Global Discovery & Autonomous Applications Active!
                    <span className="text-[10px] font-mono text-emerald-300 bg-emerald-900/60 px-2 py-0.5 rounded">
                      Live
                    </span>
                  </h4>
                  <p className="text-[11px] text-zinc-300 mt-0.5">
                    {onboardingSuccessBanner.message ||
                      `Discovered ${onboardingSuccessBanner.opportunities_discovered} live jobs across global boards and processed ${onboardingSuccessBanner.auto_applied_count} automated submissions.`}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setOnboardingSuccessBanner(null)}
                className="text-xs font-mono text-zinc-400 hover:text-white px-3 py-1 rounded bg-white/5 hover:bg-white/10 transition-all"
              >
                Dismiss
              </button>
            </div>
          )}

          {currentTab === 'dashboard' && (
            <div>
              <DailyBriefingCard
                briefing={briefing}
                onRefreshDiscovery={handleRefreshDiscovery}
                onSelectOpportunity={(oppId) => {
                  const found = opportunities.find((o) => o.id === oppId);
                  if (found) setSelectedOpportunity(found);
                }}
                loadingDiscovery={loadingDiscovery}
              />

              <div className="mt-8">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-base font-bold text-white tracking-tight">
                    Active Pipeline Matrix
                  </h2>
                  <span className="text-xs text-zinc-400">
                    {opportunities.length} Total Monitored Opportunities
                  </span>
                </div>
                <KanbanBoard
                  opportunities={opportunities}
                  onSelectOpportunity={setSelectedOpportunity}
                  onOpenImport={() => setIsImportOpen(true)}
                  onAutoApply={handleAutoApply}
                />
              </div>
            </div>
          )}

          {currentTab === 'opportunities' && (
            <div>
              <KanbanBoard
                opportunities={opportunities}
                onSelectOpportunity={setSelectedOpportunity}
                onOpenImport={() => setIsImportOpen(true)}
                onAutoApply={handleAutoApply}
              />
            </div>
          )}

          {currentTab === 'applications' && (
            <div className="space-y-4">
              <div className="pb-3 border-b border-white/5">
                <h2 className="text-base font-semibold text-white tracking-tight flex items-center gap-2">
                  <Send className="w-4 h-4 text-emerald-400" />
                  Prepared & Staged Applications
                </h2>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Tailored application packages ready for 1-click review or automated dispatch.
                </p>
              </div>

              <div className="grid grid-cols-1 gap-3">
                {opportunities
                  .filter((o) => o.application)
                  .map((opp) => (
                    <div
                      key={opp.id}
                      onClick={() => {
                        setSelectedApplication({
                          ...opp.application,
                          opportunity: opp,
                        });
                      }}
                      className="p-4 rounded-xl bg-surface-300/40 border border-white/5 hover:border-brand-500/30 cursor-pointer transition-all flex items-center justify-between"
                    >
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-bold text-white">{opp.company_name}</span>
                          <span className="text-[10px] font-mono text-amber-300 bg-amber-950/40 px-2 py-0.5 rounded border border-amber-800/40">
                            {opp.application.status}
                          </span>
                        </div>
                        <p className="text-xs text-zinc-400">{opp.title}</p>
                      </div>

                      <button className="px-3 py-1.5 rounded-lg bg-brand-500/10 hover:bg-brand-500/20 text-brand-300 text-xs font-semibold border border-brand-500/30 transition-all">
                        Review Package
                      </button>
                    </div>
                  ))}

                {opportunities.filter((o) => o.application).length === 0 && (
                  <div className="p-12 text-center text-zinc-500 text-xs border border-dashed border-white/5 rounded-xl">
                    No applications prepared yet. Click "Prepare Application" on any opportunity card.
                  </div>
                )}
              </div>
            </div>
          )}

          {currentTab === 'contacts' && (
            <ContactsView contacts={contacts} outreachSequences={outreachSequences} onRefresh={loadData} />
          )}

          {currentTab === 'contributions' && (
            <ContributionsView
              opportunities={opportunities}
              onSelectOpportunity={setSelectedOpportunity}
            />
          )}

          {currentTab === 'resumes' && <ResumesView resumes={resumes} />}

          {currentTab === 'activity' && <ActivityFeed activities={activities} />}

          {currentTab === 'analytics' && <AnalyticsView analytics={analytics} />}

          {currentTab === 'profile' && (
            <ProfileView
              profile={profile}
              verifiedAnswers={verifiedAnswers}
              onRestartOnboarding={() => setShowOnboarding(true)}
            />
          )}
        </div>
      </main>

      {/* Detail / Action Modals */}
      {selectedOpportunity && (
        <OpportunityDetailModal
          opportunity={selectedOpportunity}
          onClose={() => setSelectedOpportunity(null)}
          onRefresh={loadData}
          onOpenReview={(app) => {
            setSelectedOpportunity(null);
            setSelectedApplication({
              ...app,
              opportunity: selectedOpportunity,
            });
          }}
        />
      )}

      {selectedApplication && (
        <ApplicationReviewModal
          application={selectedApplication}
          onClose={() => setSelectedApplication(null)}
          onSubmitted={loadData}
        />
      )}

      {isImportOpen && (
        <ManualImportModal
          isOpen={isImportOpen}
          onClose={() => setIsImportOpen(false)}
          onImportSuccess={(newOpp) => {
            loadData();
            setSelectedOpportunity(newOpp);
          }}
        />
      )}

      {isCommandBarOpen && (
        <AICommandBar
          isOpen={isCommandBarOpen}
          onClose={() => setIsCommandBarOpen(false)}
          onCommandExecuted={loadData}
        />
      )}
    </div>
  );
}

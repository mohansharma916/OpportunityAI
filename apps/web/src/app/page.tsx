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
  Globe,
  Share2,
  KeyRound,
  ShieldCheck,
  User,
  X,
} from 'lucide-react';
import { fetchApi } from '@/lib/api';
import { Navigation } from '@/components/Navigation';
import { JobScraperView } from '@/components/JobScraperView';
import { LinkedInGrowthAgentView } from '@/components/LinkedInGrowthAgentView';
import { CRMView } from '@/components/CRMView';
import { ProfileView } from '@/components/ProfileView';
import { AuthScreen } from '@/components/AuthScreen';

export default function OpportunityOSApp() {
  const [currentTab, setCurrentTab] = useState<'scraper' | 'linkedin' | 'crm'>('scraper');
  const [user, setUser] = useState<any>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [profile, setProfile] = useState<any>(null);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [verifiedAnswers, setVerifiedAnswers] = useState<any[]>([]);

  // Tab Header Details
  const tabInfo: Record<string, { title: string; subtitle: string; icon: any }> = {
    scraper: {
      title: 'Job / Project Web Scraper Tool',
      subtitle: 'Multi-platform list management, date-grouped opportunity pipeline & human-like auto-applier',
      icon: Globe,
    },
    linkedin: {
      title: 'LinkedIn Scraper & Automation Bot',
      subtitle: 'LinkedIn opportunity & post scraper, Selenium-style connection bot & content publisher',
      icon: Share2,
    },
    crm: {
      title: 'Automated Outreach & Networking CRM',
      subtitle: 'Multi-step recruiter follow-up cadences, AI personalized messaging & auto-pause tracking',
      icon: Send,
    },
  };

  const currentTabDetails = tabInfo[currentTab] || tabInfo.scraper;
  const CurrentIcon = currentTabDetails.icon;

  // Initialize Auth
  useEffect(() => {
    let mounted = true;
    const initAuth = async () => {
      try {
        const stored = typeof window !== 'undefined' ? localStorage.getItem('opportunity_user') : null;
        if (stored) {
          try {
            const parsed = JSON.parse(stored);
            if (mounted) setUser(parsed);
            const fresh = await fetchApi<any>(`/api/auth/me?user_id=${parsed.id}`);
            if (fresh && fresh.id && mounted) {
              setUser(fresh);
              localStorage.setItem('opportunity_user', JSON.stringify(fresh));
            }
          } catch (_) {}
        } else {
          // Auto-authenticate with demo user for seamless zero-friction access
          try {
            const demo = await fetchApi<any>('/api/auth/demo', { method: 'POST' });
            if (demo && demo.id && mounted) {
              setUser(demo);
              localStorage.setItem('opportunity_user', JSON.stringify(demo));
            }
          } catch (_) {
            if (mounted) {
              setUser({ id: 'demo-user', full_name: 'Lead Engineer', email: 'engineer@opportunityos.internal' });
            }
          }
        }
      } catch (err) {
        console.warn('Auth init warning:', err);
        if (mounted) {
          setUser({ id: 'demo-user', full_name: 'Lead Engineer', email: 'engineer@opportunityos.internal' });
        }
      } finally {
        if (mounted) {
          setAuthLoading(false);
        }
      }
    };

    initAuth();

    // Safety timeout: Guarantee authLoading never stays true for more than 1 second
    const timer = setTimeout(() => {
      if (mounted) {
        setAuthLoading(false);
      }
    }, 1000);

    return () => {
      mounted = false;
      clearTimeout(timer);
    };
  }, []);

  // Load Profile Data
  const loadProfileData = async () => {
    try {
      const [profData, answersData] = await Promise.all([
        fetchApi<any>('/api/profile'),
        fetchApi<any[]>('/api/profile/answers'),
      ]);
      if (profData) setProfile(profData);
      if (answersData) setVerifiedAnswers(answersData);
    } catch (err) {
      console.error('Failed to load profile data:', err);
    }
  };

  useEffect(() => {
    if (user) {
      loadProfileData();
    }
  }, [user]);

  const handleLogout = () => {
    localStorage.removeItem('opportunity_user');
    setUser(null);
  };

  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-surface-100 text-white text-xs font-mono">
        <div className="flex flex-col items-center gap-3 p-6 rounded-xl bg-surface-300 border border-white/5 shadow-2xl">
          <Zap className="w-6 h-6 animate-pulse text-brand-400" />
          <span>Connecting to OpportunityOS...</span>
          <button
            onClick={() => {
              setUser({ id: 'demo-user', full_name: 'Lead Engineer', email: 'engineer@opportunityos.internal' });
              setAuthLoading(false);
            }}
            className="mt-2 text-[10px] text-zinc-400 hover:text-white underline underline-offset-2"
          >
            Click here if loading takes too long
          </button>
        </div>
      </div>
    );
  }

  if (!user) {
    return <AuthScreen onAuthenticated={(loggedInUser) => setUser(loggedInUser)} />;
  }

  return (
    <div className="flex min-h-screen bg-surface-100 text-zinc-100">
      {/* Primary Sidebar Navigation (Only 3 Core Features) */}
      <Navigation
        currentTab={currentTab}
        onSelectTab={(tab: string) => setCurrentTab(tab as any)}
        automationLevel={profile?.automation_level ?? 4}
        user={user}
        onLogout={handleLogout}
        onOpenProfile={() => setShowProfileModal(true)}
      />

      {/* Main Viewport Content Area */}
      <main className="flex-1 ml-72 flex flex-col min-h-screen">
        {/* Top Header Bar */}
        <header className="h-16 border-b border-white/5 px-8 flex items-center justify-between sticky top-0 bg-surface-100/90 backdrop-blur-md z-20">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-surface-300 border border-white/10 flex items-center justify-center text-brand-400">
              <CurrentIcon className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
                {currentTabDetails.title}
              </h2>
              <p className="text-[11px] text-zinc-400 truncate max-w-xl">
                {currentTabDetails.subtitle}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowProfileModal(true)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-300 hover:bg-surface-200 border border-white/10 text-xs font-medium text-zinc-200 transition-all"
            >
              <KeyRound className="w-3.5 h-3.5 text-brand-400" />
              <span>Identity & Vault</span>
            </button>
          </div>
        </header>

        {/* Dynamic Viewport (Only the 3 Main Features) */}
        <div className="p-8 flex-1 max-w-7xl w-full mx-auto">
          {currentTab === 'scraper' && (
            <JobScraperView
              onRefreshAllData={loadProfileData}
              profile={profile}
            />
          )}

          {currentTab === 'linkedin' && (
            <LinkedInGrowthAgentView
              onRefreshAllData={loadProfileData}
              profile={profile}
            />
          )}

          {currentTab === 'crm' && (
            <CRMView
              onRefreshAllData={loadProfileData}
              profile={profile}
            />
          )}
        </div>
      </main>

      {/* Identity, Skills & Credentials Vault Modal */}
      {showProfileModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-4xl max-h-[90vh] bg-surface-300 rounded-2xl border border-white/10 shadow-2xl p-6 overflow-y-auto space-y-4 animate-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <div className="flex items-center gap-2">
                <KeyRound className="w-5 h-5 text-brand-400" />
                <div>
                  <h3 className="text-sm font-bold text-white">Candidate Identity & Knowledge Vault</h3>
                  <p className="text-xs text-zinc-400">
                    The verified skills, work experiences, and screening memory used by the auto-apply bots.
                  </p>
                </div>
              </div>
              <button onClick={() => setShowProfileModal(false)} className="text-zinc-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <ProfileView
              profile={profile}
              verifiedAnswers={verifiedAnswers}
              onRestartOnboarding={() => {}}
              onUpdateAnswers={loadProfileData}
            />
          </div>
        </div>
      )}
    </div>
  );
}

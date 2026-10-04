'use client';

import React, { useState } from 'react';
import { Zap, Sparkles, ArrowRight, Lock, Mail, User, ShieldCheck, Loader2 } from 'lucide-react';
import { fetchApi } from '@/lib/api';

interface AuthScreenProps {
  onAuthenticated: (user: any) => void;
}

export function AuthScreen({ onAuthenticated }: AuthScreenProps) {
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (isSignUp) {
        const user = await fetchApi<any>('/api/auth/register', {
          method: 'POST',
          body: JSON.stringify({ email, password, full_name: fullName }),
        });
        onAuthenticated(user);
      } else {
        const user = await fetchApi<any>('/api/auth/login', {
          method: 'POST',
          body: JSON.stringify({ email, password }),
        });
        onAuthenticated(user);
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      const user = await fetchApi<any>('/api/auth/demo', { method: 'POST' });
      onAuthenticated(user);
    } catch (err: any) {
      setError(err.message || 'Demo login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col justify-center items-center p-6 relative overflow-hidden">
      {/* Background glow accents */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-brand-500/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-10 left-10 w-96 h-96 bg-cyan-500/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-md relative z-10 space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 rounded-2xl bg-gradient-to-tr from-brand-600 to-cyan-400 shadow-glow mb-2">
            <Zap className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">OpportunityOS</h1>
          <p className="text-xs text-zinc-400 max-w-sm mx-auto">
            Autonomous AI Career & Opportunity Acquisition Platform. Discover, evaluate, and apply worldwide.
          </p>
        </div>

        {/* Auth Form Card */}
        <div className="p-8 rounded-2xl bg-surface-200/80 border border-white/10 shadow-2xl glass-panel space-y-5">
          <div className="flex border-b border-white/5 pb-4 mb-2">
            <button
              onClick={() => {
                setIsSignUp(false);
                setError(null);
              }}
              className={`flex-1 py-1.5 text-xs font-semibold text-center border-b-2 transition-all ${
                !isSignUp
                  ? 'border-brand-500 text-white'
                  : 'border-transparent text-zinc-500 hover:text-zinc-300'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => {
                setIsSignUp(true);
                setError(null);
              }}
              className={`flex-1 py-1.5 text-xs font-semibold text-center border-b-2 transition-all ${
                isSignUp
                  ? 'border-brand-500 text-white'
                  : 'border-transparent text-zinc-500 hover:text-zinc-300'
              }`}
            >
              Create Account
            </button>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs font-mono">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {isSignUp && (
              <div>
                <label className="text-[11px] font-medium text-zinc-300 block mb-1">
                  Full Name
                </label>
                <div className="relative">
                  <User className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    required
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Sarah Connor"
                    className="w-full bg-surface-300 border border-white/10 rounded-lg pl-8 pr-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-500/50"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="text-[11px] font-medium text-zinc-300 block mb-1">
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  required
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@domain.com"
                  className="w-full bg-surface-300 border border-white/10 rounded-lg pl-8 pr-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-500/50"
                />
              </div>
            </div>

            <div>
              <label className="text-[11px] font-medium text-zinc-300 block mb-1">
                Password
              </label>
              <div className="relative">
                <Lock className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  required
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full bg-surface-300 border border-white/10 rounded-lg pl-8 pr-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-500/50"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-xs font-semibold text-white shadow-glow transition-all flex items-center justify-center gap-2 mt-2"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <span>{isSignUp ? 'Start Onboarding' : 'Sign In'}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Access Divider */}
          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/5" />
            </div>
            <div className="relative flex justify-center text-[10px] uppercase font-mono">
              <span className="bg-surface-200 px-2 text-zinc-500">Or Instant Demo Access</span>
            </div>
          </div>

          <button
            type="button"
            onClick={handleDemoLogin}
            disabled={loading}
            className="w-full py-2.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 text-xs font-medium text-zinc-200 transition-all flex items-center justify-center gap-2"
          >
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Continue as Alex Morgan (Pre-seeded Profile)</span>
          </button>
        </div>

        <p className="text-center text-[11px] text-zinc-500">
          Zero-hallucination career intelligence • All credentials encrypted
        </p>
      </div>
    </div>
  );
}

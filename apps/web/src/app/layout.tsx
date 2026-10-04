import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'OpportunityOS — Autonomous Career & Opportunity Acquisition Agent',
  description: 'AI-powered Job, Contract, Freelance, Networking, Project Contribution, and Opportunity Automation Platform.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-zinc-100 antialiased selection:bg-brand-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}

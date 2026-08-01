import Link from 'next/link';
import { ArrowRight, Bot, Zap, Shield, Search } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#050505] text-white selection:bg-purple-500/30 font-sans overflow-hidden">
      {/* Dynamic Background Effects */}
      <div className="fixed top-[-20%] left-[-10%] w-[800px] h-[800px] bg-purple-600/20 rounded-full blur-[150px] pointer-events-none" />
      <div className="fixed bottom-[-20%] right-[-10%] w-[600px] h-[600px] bg-blue-600/20 rounded-full blur-[120px] pointer-events-none" />

      {/* Navigation */}
      <nav className="relative z-10 flex items-center justify-between px-8 py-6 max-w-7xl mx-auto">
        <div className="text-2xl font-black bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent tracking-tight">
          Jobistan
        </div>
        <div className="flex items-center gap-6">
          <Link href="/login" className="text-sm font-medium text-zinc-300 hover:text-white transition-colors">
            Sign In
          </Link>
          <Link 
            href="/register" 
            className="text-sm font-semibold bg-white text-black px-5 py-2.5 rounded-full hover:scale-105 hover:bg-zinc-200 transition-all shadow-[0_0_20px_rgba(255,255,255,0.3)]"
          >
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="relative z-10 flex flex-col items-center justify-center text-center px-4 pt-32 pb-20 max-w-5xl mx-auto">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-sm font-medium text-zinc-300 mb-8 backdrop-blur-md">
          <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
          Agentic AI is now live
        </div>

        <h1 className="text-6xl md:text-8xl font-extrabold tracking-tight mb-8 leading-[1.1]">
          Your Personal <br />
          <span className="bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500 bg-clip-text text-transparent">
            AI Job Agent
          </span>
        </h1>

        <p className="text-lg md:text-xl text-zinc-400 mb-12 max-w-2xl leading-relaxed">
          Stop scrolling through job boards. Jobistan's autonomous AI agents continuously search, evaluate, and rank the best opportunities tailored perfectly to your profile, delivering them straight to you.
        </p>

        <div className="flex flex-col sm:flex-row items-center gap-4">
          <Link 
            href="/register" 
            className="group flex items-center justify-center px-8 py-4 bg-white text-black rounded-full font-bold text-lg hover:scale-105 transition-all shadow-[0_0_40px_rgba(255,255,255,0.2)]"
          >
            Start For Free
            <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
          <button className="flex items-center justify-center px-8 py-4 rounded-full font-bold text-lg text-white border border-white/20 hover:bg-white/5 transition-all backdrop-blur-sm">
            View Live Demo
          </button>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-32 text-left w-full">
          <FeatureCard 
            icon={<Bot className="text-purple-400 w-8 h-8" />}
            title="Autonomous Scraping"
            description="Our LangGraph agents crawl hundreds of company career pages daily to find hidden roles before they hit major job boards."
          />
          <FeatureCard 
            icon={<Zap className="text-blue-400 w-8 h-8" />}
            title="Smart Deduplication"
            description="We use pgvector and advanced semantic matching to ensure you never see the same job twice, saving you hours of time."
          />
          <FeatureCard 
            icon={<Search className="text-pink-400 w-8 h-8" />}
            title="Personalized Ranking"
            description="Jobs are evaluated against your specific skills and preferences, delivering a curated feed ranked by perfect match percentage."
          />
        </div>
      </main>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    <div className="p-8 rounded-3xl bg-white/5 border border-white/10 backdrop-blur-md hover:bg-white/10 transition-colors group">
      <div className="w-14 h-14 rounded-2xl bg-white/5 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <h3 className="text-xl font-bold mb-3">{title}</h3>
      <p className="text-zinc-400 leading-relaxed">{description}</p>
    </div>
  );
}

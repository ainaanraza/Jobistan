"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import { api } from '@/lib/api';
import { 
  LogOut, Briefcase, User as UserIcon, Bell, Search, Star, Clock, 
  MapPin, Building2, ChevronRight, Save, Database, AlertCircle, Sparkles
} from 'lucide-react';

export default function DashboardPage() {
  const { user, profile, isAuthenticated, fetchUser, fetchProfile, updateProfile, logout } = useAuthStore();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'jobs' | 'profile'>('jobs');
  const [jobs, setJobs] = useState<any[]>([]);
  const [fetchingJobs, setFetchingJobs] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileSuccess, setProfileSuccess] = useState('');
  
  const [profileForm, setProfileForm] = useState({
    phone: '',
    resume_url: '',
    skills: '',
    experience: '',
    education: '',
    preferred_roles: '',
    preferred_locations: '',
    salary_expectations: '',
    linkedin_url: '',
    github_url: '',
    portfolio_url: ''
  });

  useEffect(() => {
    const init = async () => {
      await fetchUser();
      await fetchProfile();
      setLoading(false);
    };
    init();
  }, [fetchUser, fetchProfile]);

  useEffect(() => {
    if (profile) {
      setProfileForm({
        phone: profile.phone || '',
        resume_url: profile.resume_url || '',
        skills: profile.skills || '',
        experience: profile.experience || '',
        education: profile.education || '',
        preferred_roles: profile.preferred_roles || '',
        preferred_locations: profile.preferred_locations || '',
        salary_expectations: profile.salary_expectations || '',
        linkedin_url: profile.linkedin_url || '',
        github_url: profile.github_url || '',
        portfolio_url: profile.portfolio_url || ''
      });
    }
  }, [profile]);

  const fetchJobs = async () => {
    setFetchingJobs(true);
    try {
      const response = await api.get('/jobs/');
      setJobs(response.data);
    } catch (error) {
      console.error('Failed to fetch jobs', error);
    } finally {
      setFetchingJobs(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchJobs();
    }
  }, [isAuthenticated]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    router.push('/login');
    return null;
  }

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const handleSeedJobs = async () => {
    try {
      await api.post('/jobs/seed');
      await fetchJobs();
    } catch (error) {
      console.error('Failed to seed jobs', error);
    }
  };

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    setProfileSuccess('');
    try {
      await updateProfile(profileForm);
      setProfileSuccess('Profile updated successfully!');
      setTimeout(() => setProfileSuccess(''), 3000);
    } catch (error) {
      console.error('Failed to save profile', error);
    } finally {
      setSavingProfile(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-zinc-100 font-sans selection:bg-purple-500/30">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-screen w-64 border-r border-white/5 bg-black/40 backdrop-blur-xl flex flex-col z-20">
        <div className="p-6 border-b border-white/5">
          <div className="text-2xl font-black bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent tracking-tight">
            Jobistan
          </div>
        </div>
        
        <nav className="flex-1 p-4 space-y-1">
          <button 
            onClick={() => setActiveTab('jobs')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
              activeTab === 'jobs'
                ? 'bg-gradient-to-r from-purple-500/20 to-blue-500/20 text-white border border-purple-500/20' 
                : 'text-zinc-400 hover:text-white hover:bg-white/5 border border-transparent'
            }`}
          >
            <Briefcase size={20} />
            <span className="font-medium">Job Matches</span>
          </button>
          <button 
            onClick={() => setActiveTab('profile')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
              activeTab === 'profile'
                ? 'bg-gradient-to-r from-purple-500/20 to-blue-500/20 text-white border border-purple-500/20' 
                : 'text-zinc-400 hover:text-white hover:bg-white/5 border border-transparent'
            }`}
          >
            <UserIcon size={20} />
            <span className="font-medium">Profile Settings</span>
          </button>
        </nav>

        <div className="p-4 border-t border-white/5">
          <div className="flex items-center gap-3 mb-4 p-2 rounded-xl hover:bg-white/5 transition-colors cursor-pointer">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center font-bold">
              {user.full_name?.charAt(0) || 'U'}
            </div>
            <div className="overflow-hidden">
              <p className="font-medium truncate">{user.full_name}</p>
              <p className="text-xs text-zinc-400 truncate">{user.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-4 py-2 text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
          >
            <LogOut size={18} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="ml-64 p-8 relative min-h-screen">
        {/* Glow Effects */}
        <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-purple-600/10 rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute bottom-1/4 right-0 w-[400px] h-[400px] bg-blue-600/10 rounded-full blur-[100px] pointer-events-none" />

        <div className="max-w-5xl mx-auto relative z-10">
          <header className="flex items-center justify-between mb-12">
            <div>
              <h1 className="text-3xl font-bold mb-2">Welcome back, {user.full_name?.split(' ')[0] || 'User'} 👋</h1>
              <p className="text-zinc-400">
                {activeTab === 'jobs' 
                  ? 'Here are your top AI-curated job matches for today.' 
                  : 'Customize your search profile to improve your matching accuracy.'}
              </p>
            </div>
            
            {activeTab === 'jobs' && (
              <div className="flex gap-4">
                <button 
                  onClick={handleSeedJobs}
                  className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 hover:bg-white/10 rounded-full text-sm font-semibold transition-all"
                  title="Populate mock jobs in database"
                >
                  <Database size={16} />
                  <span>Seed Mock Jobs</span>
                </button>
              </div>
            )}
          </header>

          {activeTab === 'jobs' ? (
            <div>
              <div className="grid grid-cols-3 gap-6 mb-12">
                <StatCard title="Active Applications" value="0" trend="Setup your profile first" />
                <StatCard title="AI Profile Score" value={profileForm.skills ? "94/100" : "30/100"} trend={profileForm.skills ? "Optimized" : "Needs Skills"} glow="purple" />
                <StatCard title="Jobs Scanned Today" value={jobs.length > 0 ? "2,845" : "0"} trend="By active agents" glow="blue" />
              </div>

              <div className="space-y-4">
                <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                  <Star className="text-yellow-500" size={20} /> Matched Jobs ({jobs.length})
                </h2>
                
                {fetchingJobs ? (
                  <div className="p-12 text-center text-zinc-400">Loading jobs...</div>
                ) : jobs.length === 0 ? (
                  <div className="p-12 rounded-3xl bg-white/5 border border-white/5 text-center max-w-xl mx-auto">
                    <AlertCircle className="w-12 h-12 text-purple-400 mx-auto mb-4" />
                    <h3 className="text-lg font-bold mb-2">No matched jobs in database</h3>
                    <p className="text-zinc-400 text-sm mb-6">
                      Click the "Seed Mock Jobs" button in the top right to populate your database with initial data for developer review.
                    </p>
                    <button 
                      onClick={handleSeedJobs}
                      className="px-6 py-2.5 bg-gradient-to-r from-purple-600 to-blue-600 rounded-full font-semibold text-sm hover:opacity-90 active:scale-[0.98] transition-all"
                    >
                      Seed Database
                    </button>
                  </div>
                ) : (
                  jobs.map((job) => (
                    <div key={job.id} className="group p-5 rounded-2xl bg-white/5 border border-white/5 hover:border-purple-500/30 hover:bg-white/10 transition-all cursor-pointer flex items-center justify-between">
                      <div className="flex items-center gap-5">
                        <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-zinc-800 to-zinc-900 border border-white/10 flex items-center justify-center text-xl font-bold shadow-lg">
                          {job.company_name?.charAt(0) || 'J'}
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold group-hover:text-purple-300 transition-colors">{job.title}</h3>
                          <div className="flex items-center gap-4 text-sm text-zinc-400 mt-1.5">
                            <span className="flex items-center gap-1"><Building2 size={14} /> {job.company_name || 'Unknown'}</span>
                            <span className="flex items-center gap-1"><MapPin size={14} /> {job.location || 'Remote'}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-6">
                        <div className="text-right">
                          {job.match_score !== undefined && job.match_score !== null ? (
                            <div className={`text-sm font-bold mb-1 ${job.match_score >= 80 ? 'text-emerald-400' : job.match_score >= 50 ? 'text-yellow-400' : 'text-orange-400'}`}>
                              {job.match_score}% Match
                            </div>
                          ) : (
                            <div className="text-sm font-medium text-zinc-500 mb-1">New Job</div>
                          )}
                          <div className="text-sm text-zinc-300">{job.salary_range || 'Undisclosed'}</div>
                        </div>
                        <a 
                          href={job.job_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="w-10 h-10 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center transition-colors"
                        >
                          <ChevronRight size={20} className="text-zinc-400" />
                        </a>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          ) : (
            <div className="rounded-3xl bg-white/5 border border-white/5 p-8 max-w-3xl">
              <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
                <Sparkles className="text-purple-400" size={24} /> Candidate Search Profile
              </h2>
              
              {profileSuccess && (
                <div className="mb-6 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm text-center">
                  {profileSuccess}
                </div>
              )}

              <form onSubmit={handleProfileSubmit} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-300">Phone Number</label>
                    <input 
                      type="text" 
                      className="w-full bg-black/20 border border-white/10 rounded-xl py-3 px-4 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all text-sm"
                      placeholder="+1 (555) 000-0000"
                      value={profileForm.phone}
                      onChange={(e) => setProfileForm({...profileForm, phone: e.target.value})}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-300">Resume Link</label>
                    <input 
                      type="url" 
                      className="w-full bg-black/20 border border-white/10 rounded-xl py-3 px-4 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all text-sm"
                      placeholder="https://drive.google.com/..."
                      value={profileForm.resume_url}
                      onChange={(e) => setProfileForm({...profileForm, resume_url: e.target.value})}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-zinc-300">Skills (Comma-separated)</label>
                  <textarea 
                    rows={3}
                    className="w-full bg-black/20 border border-white/10 rounded-xl py-3 px-4 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all text-sm"
                    placeholder="React, TypeScript, FastAPI, PostgreSQL, AWS"
                    value={profileForm.skills}
                    onChange={(e) => setProfileForm({...profileForm, skills: e.target.value})}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-300">Preferred Roles</label>
                    <input 
                      type="text" 
                      className="w-full bg-black/20 border border-white/10 rounded-xl py-3 px-4 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all text-sm"
                      placeholder="Full Stack Engineer, Frontend Dev"
                      value={profileForm.preferred_roles}
                      onChange={(e) => setProfileForm({...profileForm, preferred_roles: e.target.value})}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-300">Preferred Locations</label>
                    <input 
                      type="text" 
                      className="w-full bg-black/20 border border-white/10 rounded-xl py-3 px-4 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all text-sm"
                      placeholder="Remote, San Francisco, New York"
                      value={profileForm.preferred_locations}
                      onChange={(e) => setProfileForm({...profileForm, preferred_locations: e.target.value})}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-300">LinkedIn URL</label>
                    <input 
                      type="url" 
                      className="w-full bg-black/20 border border-white/10 rounded-xl py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all text-sm"
                      placeholder="https://linkedin.com/in/..."
                      value={profileForm.linkedin_url}
                      onChange={(e) => setProfileForm({...profileForm, linkedin_url: e.target.value})}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-300">GitHub URL</label>
                    <input 
                      type="url" 
                      className="w-full bg-black/20 border border-white/10 rounded-xl py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all text-sm"
                      placeholder="https://github.com/..."
                      value={profileForm.github_url}
                      onChange={(e) => setProfileForm({...profileForm, github_url: e.target.value})}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-300">Portfolio URL</label>
                    <input 
                      type="url" 
                      className="w-full bg-black/20 border border-white/10 rounded-xl py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all text-sm"
                      placeholder="https://portfolio.me"
                      value={profileForm.portfolio_url}
                      onChange={(e) => setProfileForm({...profileForm, portfolio_url: e.target.value})}
                    />
                  </div>
                </div>

                <div className="flex justify-end pt-4">
                  <button 
                    type="submit" 
                    disabled={savingProfile}
                    className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl font-semibold text-sm hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-50"
                  >
                    <Save size={18} />
                    <span>{savingProfile ? 'Saving...' : 'Save Profile Changes'}</span>
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

function StatCard({ title, value, trend, glow }: { title: string, value: string, trend: string, glow?: 'purple' | 'blue' }) {
  return (
    <div className={`p-6 rounded-2xl bg-white/5 border border-white/5 relative overflow-hidden`}>
      {glow === 'purple' && <div className="absolute -top-10 -right-10 w-32 h-32 bg-purple-500/20 rounded-full blur-[40px]" />}
      {glow === 'blue' && <div className="absolute -top-10 -right-10 w-32 h-32 bg-blue-500/20 rounded-full blur-[40px]" />}
      
      <h4 className="text-zinc-400 text-sm font-medium mb-2 relative z-10">{title}</h4>
      <div className="text-3xl font-bold mb-1 relative z-10">{value}</div>
      <div className="text-xs text-zinc-500 relative z-10">{trend}</div>
    </div>
  );
}

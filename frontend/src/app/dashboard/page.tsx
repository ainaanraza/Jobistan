"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import { api } from '@/lib/api';
import { 
  LogOut, Briefcase, User as UserIcon, Bell, Search, Star, Clock, 
  MapPin, Building2, ChevronRight, Save, Database, AlertCircle, Sparkles,
  Link2, Plus, Trash2, Edit2, LayoutDashboard
} from 'lucide-react';
import KanbanBoard from '@/components/KanbanBoard';

export default function DashboardPage() {
  const { user, profile, isAuthenticated, fetchUser, fetchProfile, updateProfile, logout } = useAuthStore();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'jobs' | 'applications' | 'profile' | 'sources'>('jobs');
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
    portfolio_url: '',
    college: '',
    school: '',
    city: '',
    projects: ''
  });

  const [jobSources, setJobSources] = useState<any[]>([]);
  const [fetchingSources, setFetchingSources] = useState(false);
  const [showAddSource, setShowAddSource] = useState(false);
  const [sourceForm, setSourceForm] = useState({ 
    name: '', 
    url: '', 
    source_type: 'CAREER_PAGE',
    configuration: {
      portal: 'Indeed',
      query: '',
      location: '',
      experience: '',
      remote: false,
      date_posted: '',
      raw_params: {}
    }
  });

  const parseIndeedUrl = (url: string) => {
    try {
      const parsed = new URL(url);
      if (parsed.hostname.includes('indeed.com')) {
        const query = parsed.searchParams.get('q') || '';
        const location = parsed.searchParams.get('l') || '';
        
        const raw_params: Record<string, string> = {};
        parsed.searchParams.forEach((value, key) => {
          if (key !== 'q' && key !== 'l') {
            raw_params[key] = value;
          }
        });
        
        setSourceForm(prev => ({
          ...prev,
          url,
          configuration: {
            ...prev.configuration,
            portal: 'Indeed',
            query,
            location,
            raw_params
          }
        }));
      } else {
        setSourceForm(prev => ({ ...prev, url }));
      }
    } catch {
      setSourceForm(prev => ({ ...prev, url }));
    }
  };

  const handleTestSource = async (url: string) => {
    try {
      setTestResult(null);
      alert(`Testing source: ${url}\nThis may take a moment if it needs to launch a browser...`);
      const response = await api.post('/ingestion/test-source', { url });
      setTestResult(response.data);
    } catch (error) {
      console.error('Failed to test source', error);
      alert('Failed to test source. See console.');
    }
  };

  const [testResult, setTestResult] = useState<any>(null);

  useEffect(() => {
    const init = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        useAuthStore.setState({ token, isAuthenticated: true });
        await fetchUser();
        if (useAuthStore.getState().isAuthenticated) {
          await fetchProfile();
        }
      }
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
        portfolio_url: profile.portfolio_url || '',
        college: profile.college || '',
        school: profile.school || '',
        city: profile.city || '',
        projects: profile.projects || ''
      });
    }
  }, [profile]);

  const fetchJobSources = async () => {
    setFetchingSources(true);
    try {
      const response = await api.get('/sources/');
      setJobSources(response.data);
    } catch (error) {
      console.error('Failed to fetch job sources', error);
    } finally {
      setFetchingSources(false);
    }
  };

  const handleAddSource = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/sources/', sourceForm);
      setSourceForm({ 
        name: '', 
        url: '', 
        source_type: 'CAREER_PAGE',
        configuration: {
          portal: 'Indeed',
          query: '',
          location: '',
          experience: '',
          remote: false,
          date_posted: '',
          raw_params: {}
        }
      });
      setShowAddSource(false);
      fetchJobSources();
    } catch (error) {
      console.error('Failed to add job source', error);
    }
  };

  const handleDeleteSource = async (id: number) => {
    try {
      await api.delete(`/sources/${id}`);
      fetchJobSources();
    } catch (error) {
      console.error('Failed to delete job source', error);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchJobs();
      fetchJobSources();
    }
  }, [isAuthenticated]);

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
      // Jobs fetched above with sources
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (!loading && (!isAuthenticated || !user)) {
      router.push('/login');
    }
  }, [loading, isAuthenticated, user, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated || !user) {
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
            <Search size={20} />
            <span className="font-medium">Find Jobs</span>
          </button>
          <button 
            onClick={() => setActiveTab('applications')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
              activeTab === 'applications'
                ? 'bg-gradient-to-r from-purple-500/20 to-blue-500/20 text-white border border-purple-500/20' 
                : 'text-zinc-400 hover:text-white hover:bg-white/5 border border-transparent'
            }`}
          >
            <LayoutDashboard size={20} />
            <span className="font-medium">Applications</span>
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
          <button 
            onClick={() => setActiveTab('sources')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
              activeTab === 'sources'
                ? 'bg-gradient-to-r from-purple-500/20 to-blue-500/20 text-white border border-purple-500/20' 
                : 'text-zinc-400 hover:text-white hover:bg-white/5 border border-transparent'
            }`}
          >
            <Link2 size={20} />
            <span className="font-medium">Job Sources</span>
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
                  : activeTab === 'profile' 
                    ? 'Customize your search profile to improve your matching accuracy.'
                    : 'Manage custom job sources for your AI agent to scrape.'}
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
                    <div key={job.id} className="relative group p-5 rounded-2xl bg-white/5 border border-white/5 hover:border-purple-500/30 hover:bg-white/10 transition-all cursor-pointer flex items-center justify-between">
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
                      
                      <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button 
                          onClick={(e) => {
                            e.stopPropagation();
                            api.post('/applications/', { job_id: job.id, status: 'Saved' }).then(() => {
                              alert('Job Saved to Applications!');
                            }).catch(err => console.error(err));
                          }}
                          className="w-8 h-8 rounded-full bg-purple-500/20 text-purple-400 hover:bg-purple-500/30 flex items-center justify-center transition-colors"
                          title="Save Job"
                        >
                          <Plus size={16} />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          ) : activeTab === 'applications' ? (
            <div className="h-[calc(100vh-200px)]">
               <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
                 <LayoutDashboard className="text-purple-400" size={24} /> Application Tracker
               </h2>
               <KanbanBoard />
            </div>
          ) : activeTab === 'profile' ? (
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

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-300">College / University</label>
                    <input 
                      type="text" 
                      className="w-full bg-black/20 border border-white/10 rounded-xl py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all text-sm"
                      placeholder="Stanford University"
                      value={profileForm.college}
                      onChange={(e) => setProfileForm({...profileForm, college: e.target.value})}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-300">City</label>
                    <input 
                      type="text" 
                      className="w-full bg-black/20 border border-white/10 rounded-xl py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all text-sm"
                      placeholder="San Francisco, CA"
                      value={profileForm.city}
                      onChange={(e) => setProfileForm({...profileForm, city: e.target.value})}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-300">School / High School</label>
                    <input 
                      type="text" 
                      className="w-full bg-black/20 border border-white/10 rounded-xl py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all text-sm"
                      placeholder="Lincoln High"
                      value={profileForm.school}
                      onChange={(e) => setProfileForm({...profileForm, school: e.target.value})}
                    />
                  </div>
                </div>

                <div className="space-y-2 mt-6">
                  <label className="text-sm font-medium text-zinc-300">Projects & Experience Details</label>
                  <textarea 
                    rows={4}
                    className="w-full bg-black/20 border border-white/10 rounded-xl py-3 px-4 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all text-sm"
                    placeholder="Describe your major projects, architectures you've built, etc."
                    value={profileForm.projects}
                    onChange={(e) => setProfileForm({...profileForm, projects: e.target.value})}
                  />
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
          ) : activeTab === 'sources' ? (
            <div className="rounded-3xl bg-white/5 border border-white/5 p-8 max-w-4xl">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-2xl font-bold flex items-center gap-2">
                  <Link2 className="text-blue-400" size={24} /> Job Sources Management
                </h2>
                <button 
                  onClick={() => setShowAddSource(!showAddSource)}
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full text-sm font-semibold hover:opacity-90 transition-all"
                >
                  <Plus size={16} /> Add Source
                </button>
              </div>

              {testResult && (
                <div className={`mb-8 p-6 rounded-2xl border ${testResult.status === 'SUCCESS' ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-red-500/10 border-red-500/30'}`}>
                  <h3 className="font-bold text-lg mb-2 flex items-center gap-2">
                    {testResult.status === 'SUCCESS' ? '✅ Source Test Successful' : '❌ Source Test Failed'}
                  </h3>
                  <div className="grid grid-cols-2 gap-4 text-sm mt-4">
                    <div><span className="text-zinc-400">URL:</span> {testResult.url}</div>
                    <div><span className="text-zinc-400">Detected Adapter:</span> <span className="text-purple-400 font-mono">{testResult.detected_platform}</span></div>
                    <div><span className="text-zinc-400">Jobs Found:</span> <span className="font-bold">{testResult.jobs_found}</span></div>
                    {testResult.error && <div className="col-span-2 text-red-400 mt-2">{testResult.error}</div>}
                  </div>
                  {testResult.sample_jobs && testResult.sample_jobs.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-white/10">
                      <p className="text-sm font-medium mb-2 text-zinc-400">Sample Extracted Job:</p>
                      <pre className="bg-black/50 p-3 rounded-lg text-xs overflow-x-auto text-blue-300">
                        {JSON.stringify(testResult.sample_jobs[0], null, 2)}
                      </pre>
                    </div>
                  )}
                  <button onClick={() => setTestResult(null)} className="mt-4 px-4 py-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-sm transition-colors">
                    Dismiss
                  </button>
                </div>
              )}

              {showAddSource && (
                <form onSubmit={handleAddSource} className="bg-black/40 p-6 rounded-2xl border border-white/10 mb-8 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm text-zinc-400 block mb-1.5">Source Name</label>
                      <input 
                        required
                        type="text" 
                        placeholder="e.g. OpenAI Careers"
                        className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 px-3 text-white focus:ring-2 focus:ring-blue-500/50"
                        value={sourceForm.name}
                        onChange={e => setSourceForm({...sourceForm, name: e.target.value})}
                      />
                    </div>
                    <div>
                      <label className="text-sm text-zinc-400 block mb-1.5">Source Type</label>
                      <select 
                        className="w-full bg-[#111] border border-white/10 rounded-xl py-2.5 px-3 text-white focus:ring-2 focus:ring-blue-500/50"
                        value={sourceForm.source_type}
                        onChange={e => setSourceForm({...sourceForm, source_type: e.target.value})}
                      >
                        <option value="CAREER_PAGE">Company Career Page</option>
                        <option value="JOB_PORTAL">Job Portal</option>
                        <option value="ATS">ATS</option>
                        <option value="DIRECT_JOB">Direct Job URL</option>
                      </select>
                    </div>
                  </div>
                  
                  {sourceForm.source_type === 'JOB_PORTAL' && (
                    <div className="p-4 bg-black/20 rounded-xl border border-white/5 space-y-4">
                      <h4 className="text-sm font-semibold text-purple-400">Portal Configuration</h4>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="text-xs text-zinc-400 block mb-1">Portal Platform</label>
                          <select 
                            className="w-full bg-[#111] border border-white/10 rounded-lg py-2 px-3 text-white text-sm"
                            value={sourceForm.configuration.portal}
                            onChange={e => setSourceForm({
                              ...sourceForm, 
                              configuration: {...sourceForm.configuration, portal: e.target.value}
                            })}
                          >
                            <option value="Indeed">Indeed</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-xs text-zinc-400 block mb-1">Keywords (Query)</label>
                          <input 
                            type="text" 
                            className="w-full bg-[#111] border border-white/10 rounded-lg py-2 px-3 text-white text-sm"
                            value={sourceForm.configuration.query}
                            onChange={e => setSourceForm({
                              ...sourceForm, 
                              configuration: {...sourceForm.configuration, query: e.target.value}
                            })}
                          />
                        </div>
                        <div>
                          <label className="text-xs text-zinc-400 block mb-1">Location</label>
                          <input 
                            type="text" 
                            className="w-full bg-[#111] border border-white/10 rounded-lg py-2 px-3 text-white text-sm"
                            value={sourceForm.configuration.location}
                            onChange={e => setSourceForm({
                              ...sourceForm, 
                              configuration: {...sourceForm.configuration, location: e.target.value}
                            })}
                          />
                        </div>
                        <div>
                          <label className="text-xs text-zinc-400 block mb-1">Experience Level</label>
                          <input 
                            type="text" 
                            className="w-full bg-[#111] border border-white/10 rounded-lg py-2 px-3 text-white text-sm"
                            value={sourceForm.configuration.experience}
                            onChange={e => setSourceForm({
                              ...sourceForm, 
                              configuration: {...sourceForm.configuration, experience: e.target.value}
                            })}
                          />
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-4">
                        <label className="flex items-center gap-2 text-sm text-zinc-300">
                          <input 
                            type="checkbox" 
                            checked={sourceForm.configuration.remote}
                            onChange={e => setSourceForm({
                              ...sourceForm, 
                              configuration: {...sourceForm.configuration, remote: e.target.checked}
                            })}
                            className="rounded bg-[#111] border-white/10 text-purple-500 focus:ring-purple-500/50"
                          />
                          Remote Only
                        </label>
                        
                        <div className="flex-1">
                          <label className="text-xs text-zinc-400 block mb-1">Date Posted</label>
                          <select 
                            className="w-full bg-[#111] border border-white/10 rounded-lg py-2 px-3 text-white text-sm"
                            value={sourceForm.configuration.date_posted}
                            onChange={e => setSourceForm({
                              ...sourceForm, 
                              configuration: {...sourceForm.configuration, date_posted: e.target.value}
                            })}
                          >
                            <option value="">Any Time</option>
                            <option value="24h">Past 24 Hours</option>
                            <option value="3d">Past 3 Days</option>
                            <option value="7d">Past 7 Days</option>
                            <option value="14d">Past 14 Days</option>
                          </select>
                        </div>
                      </div>
                      <div className="text-xs text-zinc-500">
                        * Note: Raw parameters extracted from pasted URLs are preserved automatically.
                      </div>
                    </div>
                  )}

                  <div>
                    <label className="text-sm text-zinc-400 block mb-1.5">URL</label>
                    <input 
                      required
                      type="url" 
                      placeholder={sourceForm.source_type === 'JOB_PORTAL' ? "Paste Indeed Search URL to auto-fill..." : "https://..."}
                      className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 px-3 text-white focus:ring-2 focus:ring-blue-500/50"
                      value={sourceForm.url}
                      onChange={e => {
                        if (sourceForm.source_type === 'JOB_PORTAL') {
                          parseIndeedUrl(e.target.value);
                        } else {
                          setSourceForm({...sourceForm, url: e.target.value})
                        }
                      }}
                    />
                  </div>
                  <div className="flex justify-end gap-3 pt-2">
                    <button type="button" onClick={() => setShowAddSource(false)} className="px-4 py-2 rounded-xl text-zinc-400 hover:bg-white/5">Cancel</button>
                    <button type="submit" className="px-5 py-2 bg-blue-600 hover:bg-blue-500 rounded-xl font-semibold">Save Source</button>
                  </div>
                </form>
              )}

              <div className="space-y-4">
                {fetchingSources ? (
                  <div className="text-center py-8 text-zinc-400">Loading sources...</div>
                ) : jobSources.length === 0 ? (
                  <div className="text-center py-12 border border-dashed border-white/10 rounded-2xl text-zinc-500">
                    No custom job sources added yet.
                  </div>
                ) : (
                  jobSources.map(source => (
                    <div key={source.id} className="flex flex-col p-5 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-colors">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-semibold text-lg">{source.name}</h4>
                            <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 bg-blue-500/20 text-blue-300 rounded-md">
                              {source.source_type.replace(/_/g, ' ')}
                            </span>
                            {source.last_error && (
                              <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 bg-red-500/20 text-red-300 rounded-md" title={source.last_error}>
                                ERROR
                              </span>
                            )}
                          </div>
                          <a href={source.url} target="_blank" rel="noreferrer" className="text-sm text-zinc-400 hover:text-blue-400 truncate max-w-md inline-block">
                            {source.url}
                          </a>
                        </div>
                        <div className="flex items-center gap-2">
                          <button onClick={() => handleTestSource(source.url)} className="px-3 py-1.5 text-xs font-semibold bg-purple-600 hover:bg-purple-500 rounded-lg transition-colors">
                            Test Source
                          </button>
                          <button onClick={() => handleDeleteSource(source.id)} className="p-2 text-zinc-400 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors" title="Delete">
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-2 pt-3 border-t border-white/5 text-xs">
                        <div>
                          <p className="text-zinc-500 mb-0.5">Last Checked</p>
                          <p className="font-mono text-zinc-300">{source.last_checked_at ? new Date(source.last_checked_at).toLocaleString() : 'Never'}</p>
                        </div>
                        <div>
                          <p className="text-zinc-500 mb-0.5">Last Success</p>
                          <p className="font-mono text-emerald-400/80">{source.last_success_at ? new Date(source.last_success_at).toLocaleString() : 'Never'}</p>
                        </div>
                        <div className="col-span-2">
                          <p className="text-zinc-500 mb-0.5">Source Sync Status</p>
                          <p className="text-zinc-300">
                            {source.content_hash ? 'Synced successfully.' : 'Pending initial sync.'} 
                            {source.last_error && <span className="text-red-400 ml-2">Error during last run.</span>}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          ) : null}
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

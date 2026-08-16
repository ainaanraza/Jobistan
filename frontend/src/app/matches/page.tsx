'use client';

import { useState, useEffect } from 'react';

interface MatchReason {
  reason: string;
}

interface JobMatch {
  id: number;
  job_id: number;
  title: string;
  company: string;
  location: string;
  salary_min: number | null;
  salary_max: number | null;
  currency: string | null;
  match_score: number;
  match_reasons: MatchReason[] | null;
  posted_at: string;
  application_url: string | null;
  is_saved: boolean;
}

export default function RecommendedJobs() {
  const [matches, setMatches] = useState<JobMatch[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMatches();
  }, []);

  const fetchMatches = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/v1/matches/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setMatches(data);
      }
    } catch (error) {
      console.error('Failed to fetch matches:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleSave = async (id: number, currentSavedState: boolean) => {
    try {
      const token = localStorage.getItem('token');
      const method = currentSavedState ? 'DELETE' : 'POST';
      const response = await fetch(`http://localhost:8000/api/v1/matches/${id}/save`, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        setMatches(matches.map(m => m.id === id ? { ...m, is_saved: !currentSavedState } : m));
      }
    } catch (error) {
      console.error('Failed to toggle save state:', error);
    }
  };

  if (loading) {
    return <div className="p-8 text-center">Loading your recommended jobs...</div>;
  }

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <h1 className="text-3xl font-bold mb-6 text-slate-800">Recommended Jobs</h1>
      
      {matches.length === 0 ? (
        <div className="bg-white p-8 rounded-xl shadow border border-slate-100 text-center">
          <p className="text-slate-500 mb-4">We haven't found any matches for you yet.</p>
          <p className="text-sm">Make sure your profile is complete and check back later.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {matches.map((match) => (
            <div key={match.id} className="bg-white rounded-xl shadow border border-slate-200 overflow-hidden transition-all hover:shadow-md">
              <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h2 className="text-xl font-semibold text-slate-900">{match.title}</h2>
                    <p className="text-slate-600 font-medium">{match.company}</p>
                    <div className="flex items-center gap-4 mt-2 text-sm text-slate-500">
                      <span className="flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                        {match.location || 'Location not specified'}
                      </span>
                      {match.salary_min && (
                        <span className="flex items-center gap-1">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                          {match.currency || '$'}{match.salary_min.toLocaleString()}{match.salary_max ? ` - ${match.salary_max.toLocaleString()}` : '+'}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                        {new Date(match.posted_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex flex-col items-end">
                    <div className="bg-emerald-50 text-emerald-700 px-3 py-1 rounded-full text-sm font-bold border border-emerald-200">
                      {Math.round(match.match_score)}% Match
                    </div>
                  </div>
                </div>
                
                {match.match_reasons && match.match_reasons.length > 0 && (
                  <div className="mt-4 bg-slate-50 p-4 rounded-lg">
                    <h3 className="text-sm font-semibold text-slate-700 mb-2 uppercase tracking-wider">Why it's a match</h3>
                    <ul className="space-y-1">
                      {match.match_reasons.map((r, i) => (
                        <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                          <svg className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                          {r.reason}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                <div className="mt-6 flex justify-end gap-3">
                  <button 
                    onClick={() => toggleSave(match.id, match.is_saved)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors border ${match.is_saved ? 'bg-slate-100 text-slate-700 border-slate-200 hover:bg-slate-200' : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'}`}
                  >
                    {match.is_saved ? 'Saved' : 'Save Job'}
                  </button>
                  <a 
                    href={match.application_url || '#'} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
                  >
                    Apply Now
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

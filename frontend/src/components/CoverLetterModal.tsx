"use client";

import React, { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Sparkles, X, Copy, Check } from 'lucide-react';

interface Props {
  jobId: number;
  jobTitle: string;
  onClose: () => void;
}

export default function CoverLetterModal({ jobId, jobTitle, onClose }: Props) {
  const [loading, setLoading] = useState(true);
  const [content, setContent] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const fetchCoverLetter = async () => {
      try {
        const response = await api.post(`/ai/generate-cover-letter/${jobId}`);
        setContent(response.data.cover_letter);
      } catch (error) {
        console.error('Failed to generate cover letter:', error);
        setContent('Failed to generate cover letter. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchCoverLetter();
  }, [jobId]);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div 
        className="w-full max-w-3xl bg-zinc-900 border border-white/10 rounded-3xl overflow-hidden shadow-2xl flex flex-col max-h-[85vh]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-6 border-b border-white/5 bg-white/5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center text-purple-400">
              <Sparkles size={20} />
            </div>
            <div>
              <h2 className="text-xl font-bold">Auto-Apply Prep</h2>
              <p className="text-sm text-zinc-400">Tailored Cover Letter for {jobTitle}</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-full transition-colors text-zinc-400 hover:text-white"
          >
            <X size={24} />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 space-y-4">
              <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-zinc-400 font-medium animate-pulse">Gemini is writing your cover letter...</p>
            </div>
          ) : (
            <div className="prose prose-invert max-w-none">
              <div className="whitespace-pre-wrap text-zinc-300 leading-relaxed text-[15px]">
                {content}
              </div>
            </div>
          )}
        </div>
        
        {!loading && (
          <div className="p-6 border-t border-white/5 bg-black/40 flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-5 py-2.5 rounded-xl font-medium hover:bg-white/5 text-zinc-300 transition-colors"
            >
              Close
            </button>
            <button
              onClick={handleCopy}
              className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 rounded-xl font-semibold transition-all active:scale-95"
            >
              {copied ? <Check size={18} /> : <Copy size={18} />}
              {copied ? 'Copied!' : 'Copy to Clipboard'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

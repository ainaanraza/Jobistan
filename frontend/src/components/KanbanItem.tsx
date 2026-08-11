"use client";

import React, { useState } from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Building2, MapPin, ExternalLink, Calendar, Sparkles } from 'lucide-react';
import CoverLetterModal from './CoverLetterModal';

interface Props {
  application: any;
}

export default function KanbanItem({ application }: Props) {
  const [showModal, setShowModal] = useState(false);
  
  const {
    setNodeRef,
    attributes,
    listeners,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: application.id,
    data: {
      type: 'Task',
      task: application,
    },
  });

  const style = {
    transition,
    transform: CSS.Transform.toString(transform),
  };

  if (isDragging) {
    return (
      <div 
        ref={setNodeRef} 
        style={style} 
        className="opacity-30 p-4 rounded-xl bg-white/5 border border-purple-500/50 min-h-[120px]" 
      />
    );
  }

  const job = application.job;
  const matchScore = job.match_score;

  return (
    <>
      <div
        ref={setNodeRef}
        style={style}
        {...attributes}
        {...listeners}
        className="p-4 rounded-xl bg-black/40 border border-white/10 hover:border-purple-500/30 hover:bg-white/5 transition-all cursor-grab active:cursor-grabbing group"
      >
        <div className="flex justify-between items-start mb-2">
          <h4 className="font-semibold text-sm group-hover:text-purple-300 transition-colors line-clamp-2 pr-6">
            {job.title}
          </h4>
          <button 
            onPointerDown={(e) => e.stopPropagation()}
            onClick={() => setShowModal(true)}
            className="text-purple-400 hover:text-purple-300 hover:bg-purple-500/20 p-1.5 rounded-lg transition-colors flex-shrink-0"
            title="Auto-Apply Prep (AI Cover Letter)"
          >
            <Sparkles size={16} />
          </button>
        </div>
        
        <div className="space-y-1.5 mb-3">
          <div className="flex items-center gap-2 text-xs text-zinc-400">
            <Building2 size={12} />
            <span className="truncate">{job.company_name || 'Unknown'}</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-zinc-400">
            <MapPin size={12} />
            <span className="truncate">{job.location || 'Remote'}</span>
          </div>
        </div>

        <div className="flex items-center justify-between pt-3 border-t border-white/5">
          <div className="flex items-center gap-2">
            {matchScore && (
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                matchScore >= 80 ? 'bg-emerald-500/20 text-emerald-400' :
                matchScore >= 50 ? 'bg-yellow-500/20 text-yellow-400' :
                'bg-orange-500/20 text-orange-400'
              }`}>
                {matchScore}% Match
              </span>
            )}
          </div>
          
          <a 
            href={job.job_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-zinc-500 hover:text-white transition-colors"
            onPointerDown={(e) => e.stopPropagation()} // prevent dragging when clicking link
          >
            <ExternalLink size={14} />
          </a>
        </div>
      </div>
      
      {showModal && (
        <CoverLetterModal 
          jobId={job.id} 
          jobTitle={job.title} 
          onClose={() => setShowModal(false)} 
        />
      )}
    </>
  );
}

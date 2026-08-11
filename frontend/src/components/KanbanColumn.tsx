"use client";

import React from 'react';
import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import KanbanItem from './KanbanItem';

interface Props {
  status: string;
  applications: any[];
}

export default function KanbanColumn({ status, applications }: Props) {
  const { setNodeRef } = useDroppable({
    id: status,
    data: {
      type: 'Column',
    },
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Saved': return 'border-blue-500/30 bg-blue-500/10 text-blue-400';
      case 'Applied': return 'border-purple-500/30 bg-purple-500/10 text-purple-400';
      case 'Interviewing': return 'border-yellow-500/30 bg-yellow-500/10 text-yellow-400';
      case 'Offer': return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400';
      case 'Rejected': return 'border-red-500/30 bg-red-500/10 text-red-400';
      default: return 'border-zinc-500/30 bg-zinc-500/10 text-zinc-400';
    }
  };

  return (
    <div className="flex flex-col flex-1 min-w-[280px] bg-white/5 border border-white/5 rounded-2xl overflow-hidden">
      <div className={`px-4 py-3 border-b flex items-center justify-between ${getStatusColor(status).replace('text-', 'border-b-')}`}>
        <h3 className={`font-semibold ${getStatusColor(status).split(' ')[2]}`}>{status}</h3>
        <span className="text-xs bg-black/40 px-2 py-1 rounded-full text-zinc-400 font-mono">
          {applications.length}
        </span>
      </div>
      
      <div 
        ref={setNodeRef}
        className="flex-1 p-3 space-y-3 overflow-y-auto"
      >
        <SortableContext 
          items={applications.map(a => a.id)} 
          strategy={verticalListSortingStrategy}
        >
          {applications.map((app) => (
            <KanbanItem key={app.id} application={app} />
          ))}
        </SortableContext>
        
        {applications.length === 0 && (
          <div className="h-full flex items-center justify-center text-sm text-zinc-500 border-2 border-dashed border-white/5 rounded-xl min-h-[100px]">
            Drop here
          </div>
        )}
      </div>
    </div>
  );
}

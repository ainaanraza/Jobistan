"use client";

import React, { useState, useEffect } from 'react';
import {
  DndContext,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragOverlay,
} from '@dnd-kit/core';
import { SortableContext, arrayMove, sortableKeyboardCoordinates } from '@dnd-kit/sortable';
import { api } from '@/lib/api';
import KanbanColumn from './KanbanColumn';
import KanbanItem from './KanbanItem';

const STATUSES = ['Saved', 'Applied', 'Interviewing', 'Offer', 'Rejected'];

export default function KanbanBoard() {
  const [applications, setApplications] = useState<any[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);

  useEffect(() => {
    fetchApplications();
  }, []);

  const fetchApplications = async () => {
    try {
      const response = await api.get('/applications/');
      setApplications(response.data);
    } catch (error) {
      console.error('Failed to fetch applications', error);
    }
  };

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const handleDragStart = (event: any) => {
    setActiveId(event.active.id);
  };

  const handleDragOver = (event: any) => {
    const { active, over } = event;
    if (!over) return;

    const activeId = active.id;
    const overId = over.id;

    if (activeId === overId) return;

    const isActiveTask = active.data.current?.type === 'Task';
    const isOverTask = over.data.current?.type === 'Task';
    const isOverColumn = over.data.current?.type === 'Column';

    if (!isActiveTask) return;

    if (isActiveTask && isOverTask) {
      setApplications((tasks) => {
        const activeIndex = tasks.findIndex((t) => t.id === activeId);
        const overIndex = tasks.findIndex((t) => t.id === overId);

        if (tasks[activeIndex].status !== tasks[overIndex].status) {
          tasks[activeIndex].status = tasks[overIndex].status;
          return arrayMove(tasks, activeIndex, overIndex);
        }
        return arrayMove(tasks, activeIndex, overIndex);
      });
    }

    if (isActiveTask && isOverColumn) {
      setApplications((tasks) => {
        const activeIndex = tasks.findIndex((t) => t.id === activeId);
        tasks[activeIndex].status = overId;
        return arrayMove(tasks, activeIndex, activeIndex);
      });
    }
  };

  const handleDragEnd = async (event: any) => {
    setActiveId(null);
    const { active, over } = event;
    if (!over) return;

    const activeApp = applications.find(a => a.id === active.id);
    if (!activeApp) return;

    const newStatus = over.data.current?.type === 'Column' ? over.id : over.data.current?.task?.status;
    
    if (newStatus && activeApp.status !== newStatus) {
       try {
         await api.patch(`/applications/${activeApp.id}`, { status: newStatus });
         fetchApplications();
       } catch (err) {
         console.error(err);
         fetchApplications(); // revert
       }
    }
  };

  const activeApp = activeId ? applications.find(a => a.id === activeId) : null;

  return (
    <div className="flex gap-4 h-full min-h-[600px] overflow-x-auto pb-4">
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
      >
        {STATUSES.map((status) => (
          <KanbanColumn 
            key={status} 
            status={status} 
            applications={applications.filter(a => a.status === status)} 
          />
        ))}
        
        <DragOverlay>
          {activeApp ? <KanbanItem application={activeApp} /> : null}
        </DragOverlay>
      </DndContext>
    </div>
  );
}

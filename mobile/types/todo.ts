export type TaskType = 'foot_care' | 'nutrition' | 'activity' | 'health_tracking' | 'medication' | 'education';
export type TaskUrgency = 'low' | 'medium' | 'high';

export interface TodoTask {
  id: string;
  title: string;
  description: string;
  type: TaskType;
  urgency: TaskUrgency;
  completed: boolean;
  createdAt: number;
  completedAt?: number;
  dueTime?: string;
  generatedBy: 'system' | 'stepmate' | 'user';
  relatedAlert?: string;
}

export interface WeeklyObjective {
  id: string;
  title: string;
  description: string;
  targetDays: number;
  completedDays: number;
  metric: string;
  currentValue: number;
  targetValue: number;
  startDate: string;
  endDate: string;
}

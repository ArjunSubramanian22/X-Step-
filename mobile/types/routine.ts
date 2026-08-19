export interface LifestyleRecommendation {
  id: string;
  category: 'footwear' | 'rest' | 'hydration' | 'nutrition' | 'activity' | 'wound_care';
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high';
  triggerCondition: string;
  canConvertToTodo: boolean;
  timestamp: number;
}

export interface DailyRoutine {
  morning: RoutineStep[];
  midday: RoutineStep[];
  evening: RoutineStep[];
}

export interface RoutineStep {
  id: string;
  time: string;
  title: string;
  description: string;
  completed: boolean;
  icon: string;
}

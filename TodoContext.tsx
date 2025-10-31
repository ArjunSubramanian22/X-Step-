import createContextHook from '@nkzw/create-context-hook';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useCallback, useEffect, useMemo, useState } from 'react';
import type { TodoTask, WeeklyObjective } from '../types/todo';

const STORAGE_KEY = 'xstep_todos';

const INITIAL_TASKS: TodoTask[] = [
  {
    id: '1',
    title: 'Morning Foot Inspection',
    description: 'Check both feet for redness, blisters, cuts, or swelling',
    type: 'foot_care',
    urgency: 'high',
    completed: false,
    createdAt: Date.now(),
    dueTime: '08:00',
    generatedBy: 'system',
  },
  {
    id: '2',
    title: 'Check Blood Glucose',
    description: 'Fasting blood glucose before breakfast',
    type: 'health_tracking',
    urgency: 'high',
    completed: false,
    createdAt: Date.now(),
    dueTime: '07:30',
    generatedBy: 'system',
  },
  {
    id: '3',
    title: 'Balanced Breakfast',
    description: 'Include protein, whole grains, and vegetables. Limit refined carbs.',
    type: 'nutrition',
    urgency: 'medium',
    completed: false,
    createdAt: Date.now(),
    dueTime: '08:00',
    generatedBy: 'stepmate',
  },
  {
    id: '4',
    title: 'Moisturize Feet',
    description: 'Apply diabetic foot cream, avoid between toes',
    type: 'foot_care',
    urgency: 'medium',
    completed: false,
    createdAt: Date.now(),
    dueTime: '09:00',
    generatedBy: 'system',
  },
  {
    id: '5',
    title: 'Gentle Walk',
    description: '15-minute light walk with proper footwear',
    type: 'activity',
    urgency: 'medium',
    completed: false,
    createdAt: Date.now(),
    dueTime: '10:00',
    generatedBy: 'stepmate',
  },
  {
    id: '6',
    title: 'Inspect Footwear',
    description: 'Check shoes for foreign objects, worn insoles, or rough seams',
    type: 'foot_care',
    urgency: 'medium',
    completed: false,
    createdAt: Date.now(),
    dueTime: '12:00',
    generatedBy: 'system',
  },
];

const INITIAL_OBJECTIVES: WeeklyObjective[] = [
  {
    id: 'obj1',
    title: 'Maintain Safe Heel Pressure',
    description: 'Keep heel pressure below 75 kPa for 5 days',
    targetDays: 5,
    completedDays: 2,
    metric: 'Heel Pressure',
    currentValue: 68,
    targetValue: 75,
    startDate: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    endDate: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  },
  {
    id: 'obj2',
    title: 'Daily Foot Inspection Streak',
    description: 'Complete foot inspection 7 days straight',
    targetDays: 7,
    completedDays: 4,
    metric: 'Inspections',
    currentValue: 4,
    targetValue: 7,
    startDate: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    endDate: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  },
  {
    id: 'obj3',
    title: 'Hydration Goal',
    description: 'Drink 8 glasses of water daily for 5 days',
    targetDays: 5,
    completedDays: 1,
    metric: 'Water Intake',
    currentValue: 6,
    targetValue: 8,
    startDate: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    endDate: new Date(Date.now() + 4 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  },
];

export const [TodoProvider, useTodo] = createContextHook(() => {
  const [tasks, setTasks] = useState<TodoTask[]>(INITIAL_TASKS);
  const [objectives, setObjectives] = useState<WeeklyObjective[]>(INITIAL_OBJECTIVES);

  useEffect(() => {
    loadTodoData();
  }, []);

  const loadTodoData = async () => {
    try {
      const stored = await AsyncStorage.getItem(STORAGE_KEY);
      if (stored) {
        const data = JSON.parse(stored);
        if (data.tasks) setTasks(data.tasks);
        if (data.objectives) setObjectives(data.objectives);
      }
    } catch (error) {
      console.error('Failed to load todo data:', error);
    }
  };

  const saveTodoData = async (newTasks: TodoTask[], newObjectives: WeeklyObjective[]) => {
    try {
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify({
        tasks: newTasks,
        objectives: newObjectives,
      }));
    } catch (error) {
      console.error('Failed to save todo data:', error);
    }
  };

  const addTask = useCallback((task: Omit<TodoTask, 'id' | 'createdAt'>) => {
    const newTask: TodoTask = {
      ...task,
      id: `task-${Date.now()}-${Math.random()}`,
      createdAt: Date.now(),
    };
    const updated = [newTask, ...tasks];
    setTasks(updated);
    saveTodoData(updated, objectives);
  }, [tasks, objectives]);

  const toggleTask = useCallback((taskId: string) => {
    const updated = tasks.map(task =>
      task.id === taskId
        ? {
            ...task,
            completed: !task.completed,
            completedAt: !task.completed ? Date.now() : undefined,
          }
        : task
    );
    setTasks(updated);
    saveTodoData(updated, objectives);
  }, [tasks, objectives]);

  const deleteTask = useCallback((taskId: string) => {
    const updated = tasks.filter(task => task.id !== taskId);
    setTasks(updated);
    saveTodoData(updated, objectives);
  }, [tasks, objectives]);

  const updateObjective = useCallback((objectiveId: string, updates: Partial<WeeklyObjective>) => {
    const updated = objectives.map(obj =>
      obj.id === objectiveId ? { ...obj, ...updates } : obj
    );
    setObjectives(updated);
    saveTodoData(tasks, updated);
  }, [objectives, tasks]);

  const completionRate = useMemo(() => {
    if (tasks.length === 0) return 0;
    const completed = tasks.filter(t => t.completed).length;
    return Math.round((completed / tasks.length) * 100);
  }, [tasks]);

  const todayTasks = useMemo(() => {
    const today = new Date().toISOString().split('T')[0];
    return tasks.filter(task => {
      const taskDate = new Date(task.createdAt).toISOString().split('T')[0];
      return taskDate === today;
    });
  }, [tasks]);

  return useMemo(() => ({
    tasks,
    objectives,
    todayTasks,
    completionRate,
    addTask,
    toggleTask,
    deleteTask,
    updateObjective,
  }), [tasks, objectives, todayTasks, completionRate, addTask, toggleTask, deleteTask, updateObjective]);
});

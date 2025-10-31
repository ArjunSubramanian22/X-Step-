import createContextHook from '@nkzw/create-context-hook';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useCallback, useEffect, useMemo, useState } from 'react';
import type { DailyRoutine, LifestyleRecommendation } from '../types/routine';

const STORAGE_KEY = 'xstep_routine';

const INITIAL_ROUTINE: DailyRoutine = {
  morning: [
    {
      id: 'morning1',
      time: '07:00',
      title: 'Wake Up & Blood Glucose',
      description: 'Check fasting blood glucose before any food or drink',
      completed: false,
      icon: 'droplet',
    },
    {
      id: 'morning2',
      time: '07:30',
      title: 'Foot Inspection',
      description: 'Check both feet for any changes, redness, or injuries',
      completed: false,
      icon: 'search',
    },
    {
      id: 'morning3',
      time: '08:00',
      title: 'Healthy Breakfast',
      description: 'Balanced meal with protein, whole grains, and vegetables',
      completed: false,
      icon: 'utensils',
    },
    {
      id: 'morning4',
      time: '08:30',
      title: 'Morning Medication',
      description: 'Take prescribed medications with food',
      completed: false,
      icon: 'pill',
    },
  ],
  midday: [
    {
      id: 'midday1',
      time: '12:00',
      title: 'Check Footwear',
      description: 'Inspect shoes for debris or wear before going out',
      completed: false,
      icon: 'scan',
    },
    {
      id: 'midday2',
      time: '13:00',
      title: 'Light Activity',
      description: '15-minute gentle walk with proper footwear',
      completed: false,
      icon: 'walk',
    },
    {
      id: 'midday3',
      time: '14:00',
      title: 'Hydration Check',
      description: 'Ensure adequate water intake throughout the day',
      completed: false,
      icon: 'glass-water',
    },
  ],
  evening: [
    {
      id: 'evening1',
      time: '18:00',
      title: 'Evening Foot Care',
      description: 'Wash and moisturize feet (avoid between toes)',
      completed: false,
      icon: 'heart-pulse',
    },
    {
      id: 'evening2',
      time: '19:00',
      title: 'Review Pressure Data',
      description: 'Check daily foot pressure trends in the app',
      completed: false,
      icon: 'chart-line',
    },
    {
      id: 'evening3',
      time: '20:00',
      title: 'Reflect & Plan',
      description: 'Review completed tasks and prepare for tomorrow',
      completed: false,
      icon: 'clipboard-check',
    },
  ],
};

const INITIAL_RECOMMENDATIONS: LifestyleRecommendation[] = [
  {
    id: 'rec1',
    category: 'footwear',
    title: 'Rotate Your Shoes',
    description: 'Wearing the same shoes daily increases pressure on specific foot areas. Alternate between 2-3 pairs of well-fitted diabetic shoes.',
    priority: 'medium',
    triggerCondition: 'High pressure detected for 2+ consecutive days',
    canConvertToTodo: true,
    timestamp: Date.now(),
  },
  {
    id: 'rec2',
    category: 'rest',
    title: 'Elevate Your Feet',
    description: 'When sitting, elevate feet to reduce swelling and improve circulation. Do this 2-3 times daily for 15 minutes.',
    priority: 'high',
    triggerCondition: 'Temperature spike detected',
    canConvertToTodo: true,
    timestamp: Date.now(),
  },
  {
    id: 'rec3',
    category: 'hydration',
    title: 'Increase Water Intake',
    description: 'Aim for 8 glasses of water daily to maintain skin elasticity and support circulation.',
    priority: 'medium',
    triggerCondition: 'General wellness',
    canConvertToTodo: true,
    timestamp: Date.now(),
  },
];

export const [RoutineProvider, useRoutine] = createContextHook(() => {
  const [routine, setRoutine] = useState<DailyRoutine>(INITIAL_ROUTINE);
  const [recommendations, setRecommendations] = useState<LifestyleRecommendation[]>(INITIAL_RECOMMENDATIONS);

  useEffect(() => {
    loadRoutineData();
  }, []);

  const loadRoutineData = async () => {
    try {
      const stored = await AsyncStorage.getItem(STORAGE_KEY);
      if (stored) {
        const data = JSON.parse(stored);
        if (data.routine) setRoutine(data.routine);
        if (data.recommendations) setRecommendations(data.recommendations);
      }
    } catch (error) {
      console.error('Failed to load routine data:', error);
    }
  };

  const saveRoutineData = async (newRoutine: DailyRoutine, newRecommendations: LifestyleRecommendation[]) => {
    try {
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify({
        routine: newRoutine,
        recommendations: newRecommendations,
      }));
    } catch (error) {
      console.error('Failed to save routine data:', error);
    }
  };

  const toggleRoutineStep = useCallback((stepId: string) => {
    const updatedRoutine = { ...routine };
    let found = false;

    Object.keys(updatedRoutine).forEach((period) => {
      const periodKey = period as keyof DailyRoutine;
      updatedRoutine[periodKey] = updatedRoutine[periodKey].map((step) => {
        if (step.id === stepId) {
          found = true;
          return { ...step, completed: !step.completed };
        }
        return step;
      });
    });

    if (found) {
      setRoutine(updatedRoutine);
      saveRoutineData(updatedRoutine, recommendations);
    }
  }, [routine, recommendations]);

  const addRecommendation = useCallback((recommendation: Omit<LifestyleRecommendation, 'id' | 'timestamp'>) => {
    const newRec: LifestyleRecommendation = {
      ...recommendation,
      id: `rec-${Date.now()}-${Math.random()}`,
      timestamp: Date.now(),
    };
    const updated = [newRec, ...recommendations];
    setRecommendations(updated);
    saveRoutineData(routine, updated);
  }, [recommendations, routine]);

  const removeRecommendation = useCallback((recId: string) => {
    const updated = recommendations.filter(rec => rec.id !== recId);
    setRecommendations(updated);
    saveRoutineData(routine, updated);
  }, [recommendations, routine]);

  const completionProgress = useMemo(() => {
    const allSteps = [...routine.morning, ...routine.midday, ...routine.evening];
    if (allSteps.length === 0) return 0;
    const completed = allSteps.filter(step => step.completed).length;
    return Math.round((completed / allSteps.length) * 100);
  }, [routine]);

  return useMemo(() => ({
    routine,
    recommendations,
    completionProgress,
    toggleRoutineStep,
    addRecommendation,
    removeRecommendation,
  }), [routine, recommendations, completionProgress, toggleRoutineStep, addRecommendation, removeRecommendation]);
});

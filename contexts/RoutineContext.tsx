import createContextHook from '@nkzw/create-context-hook';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { generateRecommendations } from '@/services/recommendationEngine';
import type { DailyScore } from '@/types/sensor';
import type { DailyRoutine, LifestyleRecommendation } from '@/types/routine';

const STORAGE_KEY = 'xstep_routine';
const ROUTINE_DATE_KEY = 'xstep_routine_date';

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

function resetRoutineIfNewDay(routine: DailyRoutine): DailyRoutine {
  const reset: DailyRoutine = { morning: [], midday: [], evening: [] };
  (['morning', 'midday', 'evening'] as const).forEach((period) => {
    reset[period] = routine[period].map((step) => ({ ...step, completed: false }));
  });
  return reset;
}

export const [RoutineProvider, useRoutine] = createContextHook(() => {
  const [routine, setRoutine] = useState<DailyRoutine>(INITIAL_ROUTINE);
  const [recommendations, setRecommendations] = useState<LifestyleRecommendation[]>([]);

  useEffect(() => {
    loadRoutineData();
  }, []);

  const loadRoutineData = async () => {
    try {
      const [stored, storedDate] = await Promise.all([
        AsyncStorage.getItem(STORAGE_KEY),
        AsyncStorage.getItem(ROUTINE_DATE_KEY),
      ]);

      const today = new Date().toISOString().split('T')[0];
      let loadedRoutine = INITIAL_ROUTINE;
      let loadedRecommendations: LifestyleRecommendation[] = [];

      if (stored) {
        const data = JSON.parse(stored);
        if (data.routine) loadedRoutine = data.routine;
        if (data.recommendations) loadedRecommendations = data.recommendations;
      }

      if (storedDate !== today) {
        loadedRoutine = resetRoutineIfNewDay(loadedRoutine);
        await AsyncStorage.setItem(ROUTINE_DATE_KEY, today);
        await AsyncStorage.setItem(
          STORAGE_KEY,
          JSON.stringify({ routine: loadedRoutine, recommendations: loadedRecommendations })
        );
      }

      setRoutine(loadedRoutine);
      setRecommendations(loadedRecommendations);
    } catch (error) {
      console.error('Failed to load routine data:', error);
    }
  };

  const saveRoutineData = async (
    newRoutine: DailyRoutine,
    newRecommendations: LifestyleRecommendation[]
  ) => {
    try {
      await AsyncStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ routine: newRoutine, recommendations: newRecommendations })
      );
    } catch (error) {
      console.error('Failed to save routine data:', error);
    }
  };

  const toggleRoutineStep = useCallback((stepId: string) => {
    const updatedRoutine = { ...routine };
    let found = false;

    (['morning', 'midday', 'evening'] as const).forEach((period) => {
      updatedRoutine[period] = updatedRoutine[period].map((step) => {
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

  const refreshRecommendations = useCallback((
    history: DailyScore[],
    activeAlertCount: number,
    completionRate: number
  ) => {
    const generated = generateRecommendations(history, activeAlertCount, completionRate);
    setRecommendations(generated);
    saveRoutineData(routine, generated);
  }, [routine]);

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

  const completionProgress = useMemo(() => {
    const allSteps = [...routine.morning, ...routine.midday, ...routine.evening];
    if (allSteps.length === 0) return 0;
    const completed = allSteps.filter((step) => step.completed).length;
    return Math.round((completed / allSteps.length) * 100);
  }, [routine]);

  return useMemo(() => ({
    routine,
    recommendations,
    completionProgress,
    toggleRoutineStep,
    addRecommendation,
    refreshRecommendations,
  }), [routine, recommendations, completionProgress, toggleRoutineStep, addRecommendation, refreshRecommendations]);
});

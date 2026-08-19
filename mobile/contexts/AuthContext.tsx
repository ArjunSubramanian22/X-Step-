import createContextHook from '@nkzw/create-context-hook';
import AsyncStorage from '@react-native-async-storage/async-storage';
import React, { useCallback, useEffect, useState } from 'react';
import type { OnboardingData } from '@/types/onboarding';

const STORAGE_KEY = 'xstep_auth';

export interface User {
  id: string;
  name: string;
  email: string;
  loginMethod: 'email' | 'google' | 'apple' | 'guest';
}

export type { OnboardingData };

export const [AuthProvider, useAuth] = createContextHook(() => {
  const [user, setUser] = useState<User | null>(null);
  const [onboardingData, setOnboardingData] = useState<OnboardingData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState<boolean>(false);

  useEffect(() => {
    loadAuthData();
  }, []);

  const loadAuthData = async () => {
    try {
      const stored = await AsyncStorage.getItem(STORAGE_KEY);
      if (stored) {
        const data = JSON.parse(stored);
        setUser(data.user);
        setOnboardingData(data.onboardingData);
        setHasCompletedOnboarding(data.hasCompletedOnboarding || false);
      }
    } catch (error) {
      console.error('Failed to load auth data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const persistAuth = async (
    nextUser: User | null,
    nextOnboarding: OnboardingData | null,
    completed: boolean
  ) => {
    if (!nextUser) {
      await AsyncStorage.removeItem(STORAGE_KEY);
      return;
    }
    await AsyncStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        user: nextUser,
        onboardingData: nextOnboarding,
        hasCompletedOnboarding: completed,
      })
    );
  };

  const login = useCallback(async (userData: User) => {
    setUser(userData);
    await persistAuth(userData, onboardingData, hasCompletedOnboarding);
  }, [onboardingData, hasCompletedOnboarding]);

  const completeOnboarding = useCallback(async (data: OnboardingData) => {
    setOnboardingData(data);
    setHasCompletedOnboarding(true);
    await persistAuth(user, data, true);
  }, [user]);

  const logout = useCallback(async () => {
    setUser(null);
    setOnboardingData(null);
    setHasCompletedOnboarding(false);
    await AsyncStorage.removeItem(STORAGE_KEY);
  }, []);

  return React.useMemo(() => ({
    user,
    onboardingData,
    isLoading,
    hasCompletedOnboarding,
    login,
    completeOnboarding,
    logout,
  }), [user, onboardingData, isLoading, hasCompletedOnboarding, login, completeOnboarding, logout]);
});

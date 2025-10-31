import createContextHook from '@nkzw/create-context-hook';
import AsyncStorage from '@react-native-async-storage/async-storage';
import React, { useCallback, useEffect, useState } from 'react';

const STORAGE_KEY = 'xstep_auth';

interface User {
  id: string;
  name: string;
  email: string;
  loginMethod: 'email' | 'google' | 'apple' | 'guest';
}

interface OnboardingData {
  measurementUnit: 'kPa' | 'PSI';
  notificationThreshold: number;
  mockDataFrequency: 'slow' | 'normal' | 'fast';
}

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

  const login = useCallback(async (userData: User) => {
    setUser(userData);
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify({
      user: userData,
      onboardingData,
      hasCompletedOnboarding,
    }));
  }, [onboardingData, hasCompletedOnboarding]);

  const completeOnboarding = useCallback(async (data: OnboardingData) => {
    setOnboardingData(data);
    setHasCompletedOnboarding(true);
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify({
      user,
      onboardingData: data,
      hasCompletedOnboarding: true,
    }));
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

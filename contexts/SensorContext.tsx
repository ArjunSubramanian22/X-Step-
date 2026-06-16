import createContextHook from '@nkzw/create-context-hook';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import {
  calculateRiskScore as computeRiskScore,
  checkThresholds,
  generateFootData,
  getDefaultBaseline,
  getMonitoringInterval,
} from '@/services/sensorService';
import { onboardingToUserProfile } from '@/services/onboardingMapper';
import type { Alert, DailyScore, FootData, Thresholds, UserProfile } from '@/types/sensor';

const STORAGE_KEYS = {
  PROFILE: 'xstep_profile',
  THRESHOLDS: 'xstep_thresholds',
  HISTORY: 'xstep_history',
  ALERTS: 'xstep_alerts',
  THEME: 'xstep_theme',
};

export const [SensorProvider, useSensor] = createContextHook(() => {
  const { onboardingData, user } = useAuth();
  const baseline = getDefaultBaseline(onboardingData?.calibrationBaseline);
  const [footData, setFootData] = useState<FootData>(() =>
    generateFootData(baseline.pressure, baseline.temperature)
  );
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [history, setHistory] = useState<DailyScore[]>([]);
  const [thresholds, setThresholds] = useState<Thresholds>({
    pressure: onboardingData?.notificationThreshold ?? 75,
    temperature: 36,
  });
  const [profile, setProfile] = useState<UserProfile>({
    name: user?.name ?? 'User',
    age: 0,
    weight: 0,
    height: 0,
    diabetesDuration: 0,
    hba1c: 7.0,
    riskLevel: 'medium',
  });
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [measurementUnit, setMeasurementUnit] = useState<'kPa' | 'PSI'>('kPa');
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const thresholdsRef = useRef<Thresholds>(thresholds);
  const baselineRef = useRef(baseline);

  useEffect(() => {
    loadStoredData();
  }, []);

  useEffect(() => {
    if (onboardingData) {
      const nextThresholds = {
        pressure: onboardingData.notificationThreshold,
        temperature: 36,
      };
      setThresholds(nextThresholds);
      thresholdsRef.current = nextThresholds;
      setMeasurementUnit(onboardingData.measurementUnit);

      if (user) {
        const mappedProfile = onboardingToUserProfile(onboardingData, user.name);
        setProfile(mappedProfile);
        AsyncStorage.setItem(STORAGE_KEYS.PROFILE, JSON.stringify(mappedProfile));
      }

      if (onboardingData.calibrationBaseline) {
        baselineRef.current = onboardingData.calibrationBaseline;
        setFootData(
          generateFootData(
            onboardingData.calibrationBaseline.pressure,
            onboardingData.calibrationBaseline.temperature
          )
        );
      }
    }
  }, [onboardingData, user]);

  const loadStoredData = async () => {
    try {
      const [storedProfile, storedThresholds, storedHistory, storedAlerts, storedTheme] =
        await Promise.all([
          AsyncStorage.getItem(STORAGE_KEYS.PROFILE),
          AsyncStorage.getItem(STORAGE_KEYS.THRESHOLDS),
          AsyncStorage.getItem(STORAGE_KEYS.HISTORY),
          AsyncStorage.getItem(STORAGE_KEYS.ALERTS),
          AsyncStorage.getItem(STORAGE_KEYS.THEME),
        ]);

      if (storedProfile) setProfile(JSON.parse(storedProfile));
      if (storedThresholds) {
        const parsed = JSON.parse(storedThresholds);
        setThresholds(parsed);
        thresholdsRef.current = parsed;
      }
      if (storedHistory) setHistory(JSON.parse(storedHistory));
      if (storedAlerts) setAlerts(JSON.parse(storedAlerts));
      if (storedTheme) setIsDarkMode(JSON.parse(storedTheme));
    } catch (error) {
      console.error('Failed to load stored data:', error);
    }
  };

  const saveProfile = useCallback(async (newProfile: UserProfile) => {
    setProfile(newProfile);
    await AsyncStorage.setItem(STORAGE_KEYS.PROFILE, JSON.stringify(newProfile));
  }, []);

  const saveThresholds = useCallback(async (newThresholds: Thresholds) => {
    setThresholds(newThresholds);
    thresholdsRef.current = newThresholds;
    await AsyncStorage.setItem(STORAGE_KEYS.THRESHOLDS, JSON.stringify(newThresholds));
  }, []);

  const dismissAlert = useCallback((alertId: string) => {
    setAlerts((prev) => {
      const updated = prev.map((alert) =>
        alert.id === alertId ? { ...alert, dismissed: true } : alert
      );
      AsyncStorage.setItem(STORAGE_KEYS.ALERTS, JSON.stringify(updated));
      return updated;
    });
  }, []);

  const calculateRiskScore = useCallback((): number => {
    return computeRiskScore(footData, thresholdsRef.current);
  }, [footData]);

  const toggleTheme = useCallback(() => {
    setIsDarkMode((prev) => {
      const next = !prev;
      AsyncStorage.setItem(STORAGE_KEYS.THEME, JSON.stringify(next));
      return next;
    });
  }, []);

  const activeAlertCount = useMemo(
    () => alerts.filter((a) => !a.dismissed).length,
    [alerts]
  );

  useEffect(() => {
    thresholdsRef.current = thresholds;
  }, [thresholds]);

  useEffect(() => {
    const frequency = onboardingData?.mockDataFrequency ?? 'normal';
    const intervalTime = getMonitoringInterval(frequency);
    let tick = 0;

    const poll = () => {
      tick += 1;
      const spike =
        tick % 7 === 0
          ? { foot: 'left' as const, zone: 'heel' as const }
          : undefined;

      const data = generateFootData(
        baselineRef.current.pressure,
        baselineRef.current.temperature,
        spike
      );
      setFootData(data);

      const newAlerts = checkThresholds(data, thresholdsRef.current);
      if (newAlerts.length > 0) {
        setAlerts((prev) => {
          const updated = [...newAlerts, ...prev].slice(0, 50);
          AsyncStorage.setItem(STORAGE_KEYS.ALERTS, JSON.stringify(updated));
          return updated;
        });
      }
    };

    poll();
    intervalRef.current = setInterval(poll, intervalTime);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [onboardingData]);

  useEffect(() => {
    const updateDailyScore = () => {
      const today = new Date().toISOString().split('T')[0];
      const score = computeRiskScore(footData, thresholdsRef.current);

      const maxPressure = Math.max(
        ...Object.values(footData.left).map((r) => r.pressure),
        ...Object.values(footData.right).map((r) => r.pressure)
      );

      const maxTemperature = Math.max(
        ...Object.values(footData.left).map((r) => r.temperature),
        ...Object.values(footData.right).map((r) => r.temperature)
      );

      const todayAlerts = alerts.filter(
        (a) => new Date(a.timestamp).toISOString().split('T')[0] === today
      ).length;

      const newScore: DailyScore = {
        date: today,
        score,
        maxPressure,
        maxTemperature,
        alertCount: todayAlerts,
      };

      setHistory((prev) => {
        const updatedHistory = [newScore, ...prev.filter((h) => h.date !== today)].slice(0, 30);
        AsyncStorage.setItem(STORAGE_KEYS.HISTORY, JSON.stringify(updatedHistory));
        return updatedHistory;
      });
    };

    const interval = setInterval(updateDailyScore, 60000);
    updateDailyScore();

    return () => clearInterval(interval);
  }, [footData, alerts]);

  return useMemo(() => ({
    footData,
    alerts,
    history,
    thresholds,
    profile,
    isDarkMode,
    measurementUnit,
    activeAlertCount,
    saveProfile,
    saveThresholds,
    dismissAlert,
    calculateRiskScore,
    toggleTheme,
  }), [
    footData,
    alerts,
    history,
    thresholds,
    profile,
    isDarkMode,
    measurementUnit,
    activeAlertCount,
    saveProfile,
    saveThresholds,
    dismissAlert,
    calculateRiskScore,
    toggleTheme,
  ]);
});

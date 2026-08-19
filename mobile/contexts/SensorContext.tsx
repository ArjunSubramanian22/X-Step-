import createContextHook from '@nkzw/create-context-hook';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import {
  analyzeBuffer,
  checkThresholds,
  calculateRiskScore as computeRiskScore,
  getDefaultBaseline,
  getMonitoringInterval,
} from '@/services/sensorService';
import { simulateWalkFrame, type SimScenario } from '@/services/walkingSimulator';
import { frameToFootData, footDataToFrame } from '@/services/gaitEngine';
import { analyzeRemote, remoteToGaitAnalysis } from '@/services/mlClient';
import { onboardingToUserProfile } from '@/services/onboardingMapper';
import type { Alert, DailyScore, FootData, GaitAnalysis, Thresholds, UserProfile } from '@/types/sensor';

const STORAGE_KEYS = {
  PROFILE: 'xstep_profile',
  THRESHOLDS: 'xstep_thresholds',
  HISTORY: 'xstep_history',
  ALERTS: 'xstep_alerts',
  THEME: 'xstep_theme',
};

const EMPTY_ANALYSIS: GaitAnalysis = {
  healthIndex: 0,
  level: 'green',
  gaitPattern: 'unknown',
  gaitConfidence: 0,
  highRiskZone: 'none',
  iwgdfCategory: 0,
  cadenceSpm: 0,
  peakKpa: 0,
  factors: {},
};

export const [SensorProvider, useSensor] = createContextHook(() => {
  const { onboardingData, user } = useAuth();
  const baseline = getDefaultBaseline(onboardingData?.calibrationBaseline);
  const [footData, setFootData] = useState<FootData>(() =>
    frameToFootData([40, 42, 30, 38, 40, 42, 30, 38], null, 90, { source: 'simulator' })
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
  const [gaitAnalysis, setGaitAnalysis] = useState<GaitAnalysis>(EMPTY_ANALYSIS);
  const [scenario, setScenario] = useState<SimScenario>('normal');
  const [streamSource, setStreamSource] = useState<'simulator' | 'ble'>('simulator');
  const [apiOnline, setApiOnline] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const thresholdsRef = useRef<Thresholds>(thresholds);
  const baselineRef = useRef(baseline);
  const bufferRef = useRef<number[][]>([]);
  const t0Ref = useRef(Date.now());
  const tickRef = useRef(0);
  const scenarioRef = useRef<SimScenario>('normal');

  useEffect(() => {
    loadStoredData();
  }, []);

  useEffect(() => {
    scenarioRef.current = scenario;
  }, [scenario]);

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
    if (gaitAnalysis.healthIndex > 0) return gaitAnalysis.healthIndex;
    return computeRiskScore(footData, thresholdsRef.current);
  }, [footData, gaitAnalysis.healthIndex]);

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

    const poll = () => {
      tickRef.current += 1;
      const t = (Date.now() - t0Ref.current) / 1000;
      const demoScenario: SimScenario =
        tickRef.current % 400 > 300 ? 'left_forefoot_overload' : scenarioRef.current;
      const { frame, temps, battery } = simulateWalkFrame(
        t,
        baselineRef.current.pressure,
        baselineRef.current.temperature,
        demoScenario
      );
      bufferRef.current = [...bufferRef.current, frame].slice(-100);
      const data = frameToFootData(frame, temps, battery, {
        source: 'simulator',
        cadenceSpm: gaitAnalysis.cadenceSpm,
        gaitPattern: gaitAnalysis.gaitPattern,
      });
      setFootData(data);

      const newAlerts = checkThresholds(data, thresholdsRef.current);
      if (newAlerts.length > 0 && tickRef.current % 12 === 0) {
        setAlerts((prev) => {
          const updated = [...newAlerts, ...prev].slice(0, 50);
          AsyncStorage.setItem(STORAGE_KEYS.ALERTS, JSON.stringify(updated));
          return updated;
        });
      }

      if (tickRef.current % 20 === 0 && bufferRef.current.length >= 25) {
        const local = analyzeBuffer(bufferRef.current, {
          hba1c: profile.hba1c,
          neuropathy: 'None',
          priorUlcer: false,
          amputation: false,
          compliance: 80,
        });
        setGaitAnalysis(local);
        analyzeRemote(bufferRef.current, {
          hba1c: profile.hba1c,
          diabetes_duration_years: profile.diabetesDuration,
          neuropathy: 'None',
          age: profile.age,
        }).then((remote) => {
          if (!remote) {
            setApiOnline(false);
            return;
          }
          setApiOnline(true);
          setGaitAnalysis(remoteToGaitAnalysis(remote));
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
  }, [onboardingData, profile.hba1c, profile.diabetesDuration, profile.age]);

  useEffect(() => {
    const updateDailyScore = () => {
      const today = new Date().toISOString().split('T')[0];
      const score = calculateRiskScore();

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
        meanCadence: gaitAnalysis.cadenceSpm,
        gaitPattern: gaitAnalysis.gaitPattern,
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
  }, [footData, alerts, gaitAnalysis, calculateRiskScore]);

  return useMemo(() => ({
    footData,
    alerts,
    history,
    thresholds,
    profile,
    isDarkMode,
    measurementUnit,
    activeAlertCount,
    gaitAnalysis,
    scenario,
    setScenario,
    streamSource,
    setStreamSource,
    apiOnline,
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
    gaitAnalysis,
    scenario,
    streamSource,
    apiOnline,
    saveProfile,
    saveThresholds,
    dismissAlert,
    calculateRiskScore,
    toggleTheme,
  ]);
});

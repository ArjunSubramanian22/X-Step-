import createContextHook from '@nkzw/create-context-hook';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { Alert, DailyScore, FootData, FootZone, Thresholds, UserProfile } from '../types/sensor';
import { useAuth } from './AuthContext';

const STORAGE_KEYS = {
  PROFILE: 'xstep_profile',
  THRESHOLDS: 'xstep_thresholds',
  HISTORY: 'xstep_history',
  ALERTS: 'xstep_alerts',
};

function generateMockReading(baseline: number, variation: number) {
  const noise = (Math.random() - 0.5) * variation;
  return Math.max(0, baseline + noise);
}

function generateFootData(baselinePressure: number, baselineTemp: number): FootData {
  const zones: FootZone[] = ['heel', 'arch', 'ball', 'toes'];
  const timestamp = Date.now();
  
  const left: Record<FootZone, any> = {} as any;
  const right: Record<FootZone, any> = {} as any;
  
  zones.forEach(zone => {
    left[zone] = {
      pressure: generateMockReading(baselinePressure, 15),
      temperature: generateMockReading(baselineTemp, 1.5),
      timestamp,
    };
    right[zone] = {
      pressure: generateMockReading(baselinePressure, 15),
      temperature: generateMockReading(baselineTemp, 1.5),
      timestamp,
    };
  });

  return {
    left,
    right,
    battery: 85 + Math.random() * 10,
    lastUpdate: timestamp,
  };
}

export const [SensorProvider, useSensor] = createContextHook(() => {
  const { onboardingData } = useAuth();
  const [footData, setFootData] = useState<FootData>(() => generateFootData(45, 34));
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [history, setHistory] = useState<DailyScore[]>([]);
  const [thresholds, setThresholds] = useState<Thresholds>(() => ({
    pressure: onboardingData?.notificationThreshold || 75,
    temperature: 36,
  }));
  const [profile, setProfile] = useState<UserProfile>({
    name: 'John Doe',
    age: 58,
    weight: 82,
    height: 175,
    diabetesDuration: 8,
    hba1c: 7.2,
    riskLevel: 'medium',
  });
  const [isDarkMode, setIsDarkMode] = useState(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const thresholdsRef = useRef<Thresholds>(thresholds);

  useEffect(() => {
    loadStoredData();
  }, []);

  useEffect(() => {
    if (onboardingData?.notificationThreshold && thresholds.pressure !== onboardingData.notificationThreshold) {
      setThresholds(prev => ({
        ...prev,
        pressure: onboardingData.notificationThreshold,
      }));
      thresholdsRef.current = {
        ...thresholdsRef.current,
        pressure: onboardingData.notificationThreshold,
      };
    }
  }, [onboardingData, thresholds.pressure]);

  const loadStoredData = async () => {
    try {
      const [storedProfile, storedThresholds, storedHistory, storedAlerts] = await Promise.all([
        AsyncStorage.getItem(STORAGE_KEYS.PROFILE),
        AsyncStorage.getItem(STORAGE_KEYS.THRESHOLDS),
        AsyncStorage.getItem(STORAGE_KEYS.HISTORY),
        AsyncStorage.getItem(STORAGE_KEYS.ALERTS),
      ]);

      if (storedProfile) setProfile(JSON.parse(storedProfile));
      if (storedThresholds) setThresholds(JSON.parse(storedThresholds));
      if (storedHistory) setHistory(JSON.parse(storedHistory));
      if (storedAlerts) setAlerts(JSON.parse(storedAlerts));
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

  const startMonitoring = useCallback(() => {
    if (intervalRef.current) return;
    
    const newData = generateFootData(45, 34);
    setFootData(newData);

    const checkAndGenerateAlerts = () => {
      const data = generateFootData(45, 34);
      setFootData(data);

      const newAlerts: Alert[] = [];
      const checkZone = (foot: 'left' | 'right', zone: FootZone) => {
        const reading = data[foot][zone];
        
        if (reading.pressure > thresholds.pressure) {
          newAlerts.push({
            id: `${Date.now()}-${foot}-${zone}-pressure`,
            type: 'pressure',
            foot,
            zone,
            value: reading.pressure,
            threshold: thresholds.pressure,
            message: `High pressure detected on ${foot} ${zone}: ${reading.pressure.toFixed(1)} kPa`,
            timestamp: Date.now(),
            dismissed: false,
          });
        }
        
        if (reading.temperature > thresholds.temperature) {
          newAlerts.push({
            id: `${Date.now()}-${foot}-${zone}-temp`,
            type: 'temperature',
            foot,
            zone,
            value: reading.temperature,
            threshold: thresholds.temperature,
            message: `High temperature on ${foot} ${zone}: ${reading.temperature.toFixed(1)}°C`,
            timestamp: Date.now(),
            dismissed: false,
          });
        }
      };

      const zones: FootZone[] = ['heel', 'arch', 'ball', 'toes'];
      zones.forEach(zone => {
        checkZone('left', zone);
        checkZone('right', zone);
      });

      if (newAlerts.length > 0) {
        setAlerts(prev => {
          const updated = [...newAlerts, ...prev].slice(0, 50);
          AsyncStorage.setItem(STORAGE_KEYS.ALERTS, JSON.stringify(updated));
          return updated;
        });
      }
    };
    
    intervalRef.current = setInterval(checkAndGenerateAlerts, 3000) as any;
  }, [thresholds]);

  const stopMonitoring = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const dismissAlert = useCallback((alertId: string) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === alertId ? { ...alert, dismissed: true } : alert
    ));
  }, []);

  const calculateRiskScore = useCallback((): number => {
    let score = 0;
    const zones: FootZone[] = ['heel', 'arch', 'ball', 'toes'];
    
    zones.forEach(zone => {
      const leftReading = footData.left[zone];
      const rightReading = footData.right[zone];
      
      const pressureScore = Math.max(
        (leftReading.pressure / thresholds.pressure) * 50,
        (rightReading.pressure / thresholds.pressure) * 50
      );
      
      const tempScore = Math.max(
        (leftReading.temperature / thresholds.temperature) * 50,
        (rightReading.temperature / thresholds.temperature) * 50
      );
      
      score += (pressureScore + tempScore) / 8;
    });

    return Math.min(100, Math.max(0, score));
  }, [footData, thresholds]);



  useEffect(() => {
    thresholdsRef.current = thresholds;
  }, [thresholds]);

  useEffect(() => {
    const frequency = onboardingData?.mockDataFrequency || 'normal';
    const intervalTime = frequency === 'slow' ? 5000 : frequency === 'fast' ? 1000 : 3000;

    const initialData = generateFootData(45, 34);
    setFootData(initialData);

    const checkAndGenerateAlerts = () => {
      const data = generateFootData(45, 34);
      setFootData(data);

      const currentThresholds = thresholdsRef.current;
      const newAlerts: Alert[] = [];
      const checkZone = (foot: 'left' | 'right', zone: FootZone) => {
        const reading = data[foot][zone];
        
        if (reading.pressure > currentThresholds.pressure) {
          newAlerts.push({
            id: `${Date.now()}-${foot}-${zone}-pressure`,
            type: 'pressure',
            foot,
            zone,
            value: reading.pressure,
            threshold: currentThresholds.pressure,
            message: `High pressure detected on ${foot} ${zone}: ${reading.pressure.toFixed(1)} kPa`,
            timestamp: Date.now(),
            dismissed: false,
          });
        }
        
        if (reading.temperature > currentThresholds.temperature) {
          newAlerts.push({
            id: `${Date.now()}-${foot}-${zone}-temp`,
            type: 'temperature',
            foot,
            zone,
            value: reading.temperature,
            threshold: currentThresholds.temperature,
            message: `High temperature on ${foot} ${zone}: ${reading.temperature.toFixed(1)}°C`,
            timestamp: Date.now(),
            dismissed: false,
          });
        }
      };

      const zones: FootZone[] = ['heel', 'arch', 'ball', 'toes'];
      zones.forEach(zone => {
        checkZone('left', zone);
        checkZone('right', zone);
      });

      if (newAlerts.length > 0) {
        setAlerts(prev => {
          const updated = [...newAlerts, ...prev].slice(0, 50);
          AsyncStorage.setItem(STORAGE_KEYS.ALERTS, JSON.stringify(updated));
          return updated;
        });
      }
    };
    
    intervalRef.current = setInterval(checkAndGenerateAlerts, intervalTime) as any;

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
      const score = calculateRiskScore();
      
      const maxPressure = Math.max(
        ...Object.values(footData.left).map(r => r.pressure),
        ...Object.values(footData.right).map(r => r.pressure)
      );
      
      const maxTemperature = Math.max(
        ...Object.values(footData.left).map(r => r.temperature),
        ...Object.values(footData.right).map(r => r.temperature)
      );

      const todayAlerts = alerts.filter(a => 
        new Date(a.timestamp).toISOString().split('T')[0] === today
      ).length;

      const newScore: DailyScore = {
        date: today,
        score,
        maxPressure,
        maxTemperature,
        alertCount: todayAlerts,
      };

      setHistory(prev => {
        const updatedHistory = [newScore, ...prev.filter(h => h.date !== today)].slice(0, 30);
        AsyncStorage.setItem(STORAGE_KEYS.HISTORY, JSON.stringify(updatedHistory));
        return updatedHistory;
      });
    };

    const interval = setInterval(updateDailyScore, 60000);
    updateDailyScore();

    return () => clearInterval(interval);
  }, [footData, alerts, calculateRiskScore]);

  const toggleTheme = useCallback(() => {
    setIsDarkMode(prev => !prev);
  }, []);

  return useMemo(() => ({
    footData,
    alerts,
    history,
    thresholds,
    profile,
    isDarkMode,
    saveProfile,
    saveThresholds,
    dismissAlert,
    calculateRiskScore,
    toggleTheme,
    startMonitoring,
    stopMonitoring,
  }), [footData, alerts, history, thresholds, profile, isDarkMode, saveProfile, saveThresholds, dismissAlert, calculateRiskScore, toggleTheme, startMonitoring, stopMonitoring]);
});

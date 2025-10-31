import createContextHook from '@nkzw/create-context-hook';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useCallback, useEffect, useMemo, useState } from 'react';
import type { HealthIndex, MedicalRecord } from '../types/health';

const STORAGE_KEY = 'xstep_health';

const MOCK_MEDICAL_RECORD: MedicalRecord = {
  diabetesType: 'Type 2',
  diabetesDuration: 8,
  hba1c: 7.2,
  lastHba1cDate: '2025-09-15',
  medications: ['Metformin 1000mg', 'Insulin Glargine 20 units', 'Gabapentin 300mg'],
  neuropathyStatus: 'Moderate',
  hasFootUlcers: false,
  ulcerHistory: ['Right heel ulcer (2023, healed)', 'Left toe blister (2024, healed)'],
  amputationHistory: false,
  vascularComplications: ['Peripheral arterial disease (mild)'],
  cholesterol: 195,
  bloodPressure: '138/85',
  smokingStatus: 'Former',
  alcoholUse: 'Occasional',
  exerciseLevel: 'Light',
  workType: 'Standing',
  footwearHabits: ['Steel-toe work boots 8hrs/day', 'Diabetic insoles'],
};

export const [HealthProvider, useHealth] = createContextHook(() => {
  const [medicalRecord, setMedicalRecord] = useState<MedicalRecord>(MOCK_MEDICAL_RECORD);
  const [healthIndex, setHealthIndex] = useState<HealthIndex>({
    score: 0,
    level: 'green',
    factors: {
      footPressure: 0,
      temperature: 0,
      neuropathy: 0,
      glycemicControl: 0,
      compliance: 0,
    },
  });

  useEffect(() => {
    loadHealthData();
  }, []);

  const loadHealthData = async () => {
    try {
      const stored = await AsyncStorage.getItem(STORAGE_KEY);
      if (stored) {
        const data = JSON.parse(stored);
        if (data.medicalRecord) setMedicalRecord(data.medicalRecord);
        if (data.healthIndex) setHealthIndex(data.healthIndex);
      }
    } catch (error) {
      console.error('Failed to load health data:', error);
    }
  };

  const updateHealthIndex = useCallback((
    footPressureScore: number,
    temperatureScore: number,
    complianceScore: number
  ) => {
    const neuropathyScore = medicalRecord.neuropathyStatus === 'Severe' ? 25 :
      medicalRecord.neuropathyStatus === 'Moderate' ? 15 :
      medicalRecord.neuropathyStatus === 'Mild' ? 8 : 0;

    const glycemicScore = medicalRecord.hba1c > 8 ? 20 :
      medicalRecord.hba1c > 7 ? 12 :
      medicalRecord.hba1c > 6.5 ? 6 : 0;

    const totalScore = footPressureScore + temperatureScore + neuropathyScore + glycemicScore + (100 - complianceScore);

    const level = totalScore < 45 ? 'green' : totalScore < 75 ? 'amber' : 'red';

    const newIndex: HealthIndex = {
      score: Math.min(100, Math.max(0, totalScore)),
      level,
      factors: {
        footPressure: footPressureScore,
        temperature: temperatureScore,
        neuropathy: neuropathyScore,
        glycemicControl: glycemicScore,
        compliance: complianceScore,
      },
    };

    setHealthIndex(newIndex);
    AsyncStorage.setItem(STORAGE_KEY, JSON.stringify({ medicalRecord, healthIndex: newIndex }));
  }, [medicalRecord]);

  const updateMedicalRecord = useCallback(async (record: Partial<MedicalRecord>) => {
    const updated = { ...medicalRecord, ...record };
    setMedicalRecord(updated);
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify({ medicalRecord: updated, healthIndex }));
  }, [medicalRecord, healthIndex]);

  return useMemo(() => ({
    medicalRecord,
    healthIndex,
    updateHealthIndex,
    updateMedicalRecord,
  }), [medicalRecord, healthIndex, updateHealthIndex, updateMedicalRecord]);
});

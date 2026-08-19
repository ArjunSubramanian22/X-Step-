import type { Alert, FootData, FootZone, GaitAnalysis, Thresholds } from '@/types/sensor';
import type { CalibrationBaseline } from '@/types/onboarding';
import { generateFootData as simulateGenerateFootData } from '@/services/walkingSimulator';
import { footDataToFrame, localRiskAnalysis } from '@/services/gaitEngine';

const ZONES: FootZone[] = ['heel', 'arch', 'ball', 'toes'];

export function generateFootData(
  baselinePressure = 45,
  baselineTemp = 34,
  spikeZone?: { foot: 'left' | 'right'; zone: FootZone }
): FootData {
  return simulateGenerateFootData(baselinePressure, baselineTemp, spikeZone);
}

export function checkThresholds(data: FootData, thresholds: Thresholds): Alert[] {
  const alerts: Alert[] = [];

  const checkZone = (foot: 'left' | 'right', zone: FootZone) => {
    const reading = data[foot][zone];

    if (reading.pressure > thresholds.pressure) {
      alerts.push({
        id: `${Date.now()}-${foot}-${zone}-pressure-${Math.random()}`,
        type: 'pressure',
        foot,
        zone,
        value: reading.pressure,
        threshold: thresholds.pressure,
        message: `High pressure on ${foot} ${zone} (${reading.pressure.toFixed(1)} kPa). Offload this area and inspect the skin.`,
        timestamp: Date.now(),
        dismissed: false,
      });
    }

    if (reading.temperature > thresholds.temperature) {
      alerts.push({
        id: `${Date.now()}-${foot}-${zone}-temp-${Math.random()}`,
        type: 'temperature',
        foot,
        zone,
        value: reading.temperature,
        threshold: thresholds.temperature,
        message: `Temperature ${reading.temperature.toFixed(1)}°C on ${foot} ${zone}. Rest and re-check in 15 minutes.`,
        timestamp: Date.now(),
        dismissed: false,
      });
    }
  };

  ZONES.forEach((zone) => {
    checkZone('left', zone);
    checkZone('right', zone);
  });

  return alerts;
}

export function calculateRiskScore(footData: FootData, thresholds: Thresholds): number {
  const analysis = localRiskAnalysis([footDataToFrame(footData)], {
    hba1c: 7,
    neuropathy: 'None',
    priorUlcer: false,
    amputation: false,
    compliance: 80,
  });
  const thresholdRatio = Math.max(
    ...ZONES.flatMap((z) => [footData.left[z].pressure, footData.right[z].pressure])
  ) / Math.max(thresholds.pressure, 1);
  return Math.min(100, Math.max(analysis.healthIndex, thresholdRatio * 55));
}

export function analyzeBuffer(
  frames: number[][],
  clinical: { hba1c: number; neuropathy: string; priorUlcer: boolean; amputation: boolean; compliance: number }
): GaitAnalysis {
  return localRiskAnalysis(frames, clinical);
}

export function getMonitoringInterval(frequency: 'slow' | 'normal' | 'fast'): number {
  if (frequency === 'slow') return 200;
  if (frequency === 'fast') return 40;
  return 80;
}

export function getDefaultBaseline(
  calibration?: CalibrationBaseline
): { pressure: number; temperature: number } {
  return {
    pressure: calibration?.pressure ?? 40,
    temperature: calibration?.temperature ?? 34,
  };
}

export function convertPressure(value: number, unit: 'kPa' | 'PSI'): number {
  if (unit === 'PSI') return value * 0.145038;
  return value;
}

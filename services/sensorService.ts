import type { Alert, FootData, FootZone, Thresholds } from '@/types/sensor';
import type { CalibrationBaseline } from '@/types/onboarding';

const ZONES: FootZone[] = ['heel', 'arch', 'ball', 'toes'];

function generateMockReading(baseline: number, variation: number): number {
  const noise = (Math.random() - 0.5) * variation;
  return Math.max(0, baseline + noise);
}

export function generateFootData(
  baselinePressure = 45,
  baselineTemp = 34,
  spikeZone?: { foot: 'left' | 'right'; zone: FootZone }
): FootData {
  const timestamp = Date.now();
  const left = {} as FootData['left'];
  const right = {} as FootData['right'];

  ZONES.forEach((zone) => {
    const isSpike =
      spikeZone &&
      ((spikeZone.foot === 'left' && spikeZone.zone === zone) ||
        (spikeZone.foot === 'right' && spikeZone.zone === zone));

    left[zone] = {
      pressure: generateMockReading(
        isSpike ? baselinePressure + 35 : baselinePressure,
        isSpike ? 5 : 15
      ),
      temperature: generateMockReading(
        isSpike ? baselineTemp + 2.5 : baselineTemp,
        isSpike ? 0.3 : 1.5
      ),
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

export function checkThresholds(
  data: FootData,
  thresholds: Thresholds
): Alert[] {
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
        message: `High pressure detected on ${foot} ${zone}: ${reading.pressure.toFixed(1)} kPa`,
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
        message: `High temperature on ${foot} ${zone}: ${reading.temperature.toFixed(1)}°C`,
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

export function calculateRiskScore(
  footData: FootData,
  thresholds: Thresholds
): number {
  let score = 0;

  ZONES.forEach((zone) => {
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
}

export function getMonitoringInterval(
  frequency: 'slow' | 'normal' | 'fast'
): number {
  if (frequency === 'slow') return 5000;
  if (frequency === 'fast') return 1000;
  return 3000;
}

export function getDefaultBaseline(
  calibration?: CalibrationBaseline
): { pressure: number; temperature: number } {
  return {
    pressure: calibration?.pressure ?? 45,
    temperature: calibration?.temperature ?? 34,
  };
}

export function convertPressure(value: number, unit: 'kPa' | 'PSI'): number {
  if (unit === 'PSI') return value * 0.145038;
  return value;
}

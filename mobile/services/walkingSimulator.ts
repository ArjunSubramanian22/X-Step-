import type { FootData, FootZone } from '@/types/sensor';
import { frameToFootData, type Frame8 } from '@/services/gaitEngine';

const ZONES: FootZone[] = ['heel', 'arch', 'ball', 'toes'];

function wave(t: number, cadence: number, phase: number): number {
  const s = Math.sin(2 * Math.PI * (cadence / 60) * t + phase);
  return s > 0 ? s ** 1.4 : 0;
}

export type SimScenario =
  | 'normal'
  | 'left_forefoot_overload'
  | 'left_heel_overload'
  | 'right_lateral_overload';

/**
 * Physiologic 4-FSR walking simulator (MET1/MET2/MET5/HEEL × 2 feet).
 * Used when BLE insoles are not connected so the product still demonstrates
 * real-time alerts, gait analysis, and clinician graphs.
 */
export function simulateWalkFrame(
  tSeconds: number,
  baselinePressure = 40,
  baselineTemp = 34,
  scenario: SimScenario = 'normal'
): { frame: Frame8; temps: number[]; battery: number } {
  const cadence = scenario === 'normal' ? 112 : 100;
  const lHeel = baselinePressure * 0.9 * wave(tSeconds, cadence, 0);
  const lFore = baselinePressure * 0.85 * wave(tSeconds, cadence, -0.7);
  const rHeel = baselinePressure * 0.9 * wave(tSeconds, cadence, Math.PI);
  const rFore = baselinePressure * 0.85 * wave(tSeconds, cadence, Math.PI - 0.7);
  const n = () => (Math.random() - 0.5) * 4;

  let l = [lFore * 0.85, lFore, lFore * 0.6, lHeel];
  let r = [rFore * 0.85, rFore, rFore * 0.6, rHeel];

  if (scenario === 'left_forefoot_overload') {
    l[0] += 90 * wave(tSeconds, cadence, -0.7);
    l[1] += 110 * wave(tSeconds, cadence, -0.7);
  } else if (scenario === 'left_heel_overload') {
    l[3] += 95 * wave(tSeconds, cadence, 0);
  } else if (scenario === 'right_lateral_overload') {
    r[2] += 100 * wave(tSeconds, cadence, Math.PI - 0.7);
  }

  const frame: Frame8 = [
    Math.max(0, l[0] + n()),
    Math.max(0, l[1] + n()),
    Math.max(0, l[2] + n()),
    Math.max(0, l[3] + n()),
    Math.max(0, r[0] + n()),
    Math.max(0, r[1] + n()),
    Math.max(0, r[2] + n()),
    Math.max(0, r[3] + n()),
  ];
  const temps = frame.map((p) => baselineTemp + p / 80);
  return { frame, temps, battery: 88 + Math.random() * 6 };
}

export function simulateFootData(
  tSeconds: number,
  baselinePressure = 40,
  baselineTemp = 34,
  scenario: SimScenario = 'normal'
): FootData {
  const { frame, temps, battery } = simulateWalkFrame(tSeconds, baselinePressure, baselineTemp, scenario);
  return frameToFootData(frame, temps, battery, { source: 'simulator' });
}

export function generateFootData(
  baselinePressure = 45,
  baselineTemp = 34,
  spikeZone?: { foot: 'left' | 'right'; zone: FootZone }
): FootData {
  const scenario: SimScenario =
    spikeZone?.zone === 'heel'
      ? 'left_heel_overload'
      : spikeZone?.zone === 'ball' || spikeZone?.zone === 'toes'
        ? 'left_forefoot_overload'
        : 'normal';
  return simulateFootData(Date.now() / 1000, baselinePressure, baselineTemp, scenario);
}

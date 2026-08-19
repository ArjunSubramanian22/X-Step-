import type { FootData, FootZone, GaitAnalysis } from '@/types/sensor';

const ZONES: FootZone[] = ['toes', 'ball', 'arch', 'heel'];

export type Frame8 = [number, number, number, number, number, number, number, number];

export function footDataToFrame(data: FootData): Frame8 {
  return [
    data.left.toes.pressure,
    data.left.ball.pressure,
    data.left.arch.pressure,
    data.left.heel.pressure,
    data.right.toes.pressure,
    data.right.ball.pressure,
    data.right.arch.pressure,
    data.right.heel.pressure,
  ];
}

export function frameToFootData(
  frame: number[],
  temps: number[] | null,
  battery: number,
  extras?: Partial<FootData>
): FootData {
  const ts = Date.now();
  const t = temps ?? [34, 34, 34, 34, 34, 34, 34, 34];
  const side = (offset: number) => ({
    toes: { pressure: frame[offset], temperature: t[offset], timestamp: ts },
    ball: { pressure: frame[offset + 1], temperature: t[offset + 1], timestamp: ts },
    arch: { pressure: frame[offset + 2], temperature: t[offset + 2], timestamp: ts },
    heel: { pressure: frame[offset + 3], temperature: t[offset + 3], timestamp: ts },
  });
  return {
    left: side(0),
    right: side(4),
    battery,
    lastUpdate: ts,
    ...extras,
  };
}

function clip(n: number, lo: number, hi: number) {
  return Math.max(lo, Math.min(hi, n));
}

export function classifyGait(frames: number[][]): { pattern: string; zone: string; cadence: number; peak: number } {
  if (frames.length < 8) {
    return { pattern: 'unknown', zone: 'none', cadence: 0, peak: 0 };
  }
  const cols = 8;
  const peaks = Array.from({ length: cols }, (_, i) => Math.max(...frames.map((f) => f[i] ?? 0)));
  const peak = Math.max(...peaks);
  const lHeel = frames.map((f) => (f[3] + f[7]) / 2);
  let strikes = 0;
  for (let i = 1; i < lHeel.length - 1; i++) {
    if (lHeel[i] > lHeel[i - 1] && lHeel[i] >= lHeel[i + 1] && lHeel[i] > 20) strikes += 1;
  }
  const duration = frames.length / 25;
  const cadence = (strikes / Math.max(duration, 0.2)) * 60;

  const lFore = (peaks[0] + peaks[1]) / 2;
  const rFore = (peaks[4] + peaks[5]) / 2;
  const lHeelP = peaks[3];
  const rHeelP = peaks[7];
  const lLat = peaks[2];
  const rLat = peaks[6];

  let pattern = 'normal';
  let zone = 'none';
  if (cadence < 90 && peak < 70) {
    pattern = 'shuffling_low_cadence';
  } else if (lFore > rFore * 1.35 && lFore > 70) {
    pattern = 'left_forefoot_overload';
    zone = 'met2';
  } else if (rFore > lFore * 1.35 && rFore > 70) {
    pattern = 'right_forefoot_overload';
    zone = 'met2';
  } else if (lHeelP > rHeelP * 1.35 && lHeelP > 70) {
    pattern = 'left_heel_overload';
    zone = 'heel';
  } else if (rHeelP > lHeelP * 1.35 && rHeelP > 70) {
    pattern = 'right_heel_overload';
    zone = 'heel';
  } else if (lLat > lFore * 1.15 && lLat > 65) {
    pattern = 'left_lateral_overload';
    zone = 'met5';
  } else if (rLat > rFore * 1.15 && rLat > 65) {
    pattern = 'right_lateral_overload';
    zone = 'met5';
  } else if (Math.abs(lFore + lHeelP - (rFore + rHeelP)) > 40) {
    pattern = 'asymmetric_antalgic';
    zone = 'met1';
  }
  return { pattern, zone, cadence, peak };
}

export function localRiskAnalysis(
  frames: number[][],
  clinical: { hba1c: number; neuropathy: string; priorUlcer: boolean; amputation: boolean; compliance: number }
): GaitAnalysis {
  const gait = classifyGait(frames);
  const neuro = { None: 0, Mild: 12, Moderate: 22, Severe: 32 }[clinical.neuropathy] ?? 0;
  const glycemic = clinical.hba1c > 8.5 ? 22 : clinical.hba1c > 7.5 ? 14 : clinical.hba1c > 6.5 ? 7 : 0;
  const history = clinical.amputation ? 28 : clinical.priorUlcer ? 18 : 0;
  const clinicalScore = clip(neuro + glycemic + history, 0, 100);
  const pressureScore = clip(((gait.peak - 40) / 160) * 40, 0, 40);
  const gaitScore = gait.pattern === 'normal' ? 0 : 12;
  const healthIndex = clip(0.45 * clinicalScore + pressureScore + gaitScore, 0, 100);
  const iwgdfCategory = clinical.amputation || clinical.priorUlcer ? 3 : clinical.neuropathy !== 'None' ? 1 : 0;
  const level = healthIndex < 35 ? 'green' : healthIndex < 65 ? 'amber' : 'red';
  return {
    healthIndex,
    level,
    gaitPattern: gait.pattern,
    gaitConfidence: gait.pattern === 'unknown' ? 0.3 : 0.78,
    highRiskZone: gait.zone,
    iwgdfCategory,
    cadenceSpm: gait.cadence,
    peakKpa: gait.peak,
    factors: {
      clinical: clinicalScore,
      footPressure: pressureScore,
      gait: gaitScore,
      compliance: clinical.compliance,
    },
  };
}

export function emptyBuffer(): number[][] {
  return [];
}

export { ZONES };

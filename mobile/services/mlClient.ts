import type { GaitAnalysis } from '@/types/sensor';

const DEFAULT_BASE = process.env.EXPO_PUBLIC_XSTEP_API ?? 'http://127.0.0.1:8080';

export interface AnalyzeResponse {
  health_index: number;
  level: 'green' | 'amber' | 'red';
  gait_pattern: string;
  gait_confidence: number;
  high_risk_zone: string;
  iwgdf_category: number;
  factors: Record<string, number>;
  extras: Record<string, number>;
  alerts: Array<{
    foot: string;
    zone: string;
    value_kpa: number;
    threshold_kpa: number;
    message: string;
  }>;
  recommendations: Array<{
    id: string;
    category: string;
    title: string;
    description: string;
    priority: string;
    triggerCondition: string;
    canConvertToTodo: boolean;
  }>;
  foot_pressures: {
    left: Record<string, number>;
    right: Record<string, number>;
  };
  stepmate_prompt: string;
}

export async function analyzeRemote(
  frames: number[][],
  clinical?: Record<string, unknown>,
  compliance = 80
): Promise<AnalyzeResponse | null> {
  try {
    const res = await fetch(`${DEFAULT_BASE}/v1/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        frames,
        sample_hz: 25,
        compliance,
        clinical,
      }),
    });
    if (!res.ok) return null;
    return (await res.json()) as AnalyzeResponse;
  } catch {
    return null;
  }
}

export async function uploadUlcerPhoto(uri: string): Promise<{
  grade: number;
  label: string;
  probs: number[];
  backend: string;
  disclaimer: string;
} | null> {
  try {
    const form = new FormData();
    form.append('file', {
      uri,
      name: 'wound.jpg',
      type: 'image/jpeg',
    } as unknown as Blob);
    const res = await fetch(`${DEFAULT_BASE}/v1/ulcer`, { method: 'POST', body: form });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export function remoteToGaitAnalysis(r: AnalyzeResponse): GaitAnalysis {
  return {
    healthIndex: r.health_index,
    level: r.level,
    gaitPattern: r.gait_pattern,
    gaitConfidence: r.gait_confidence,
    highRiskZone: r.high_risk_zone,
    iwgdfCategory: r.iwgdf_category,
    cadenceSpm: r.extras?.cadence_spm ?? 0,
    peakKpa: r.extras?.peak_any ?? 0,
    factors: r.factors,
  };
}

export { DEFAULT_BASE as API_BASE };

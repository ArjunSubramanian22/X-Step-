export type FootZone = 'heel' | 'arch' | 'ball' | 'toes';
export type SensorSite = 'met1' | 'met2' | 'met5' | 'heel';

export const ZONE_TO_SITE: Record<FootZone, SensorSite> = {
  toes: 'met1',
  ball: 'met2',
  arch: 'met5',
  heel: 'heel',
};

export const SITE_TO_ZONE: Record<SensorSite, FootZone> = {
  met1: 'toes',
  met2: 'ball',
  met5: 'arch',
  heel: 'heel',
};

export const SITE_LABELS: Record<SensorSite, string> = {
  met1: '1st metatarsal',
  met2: '2nd metatarsal',
  met5: '5th metatarsal',
  heel: 'Heel',
};

export interface SensorReading {
  pressure: number;
  temperature: number;
  timestamp: number;
}

export interface FootData {
  left: Record<FootZone, SensorReading>;
  right: Record<FootZone, SensorReading>;
  battery: number;
  lastUpdate: number;
  cadenceSpm?: number;
  gaitPattern?: string;
  source?: 'ble' | 'simulator' | 'api';
}

export interface Alert {
  id: string;
  type: 'pressure' | 'temperature' | 'gait';
  foot: 'left' | 'right';
  zone: FootZone;
  value: number;
  threshold: number;
  message: string;
  timestamp: number;
  dismissed: boolean;
}

export interface DailyScore {
  date: string;
  score: number;
  maxPressure: number;
  maxTemperature: number;
  alertCount: number;
  meanCadence?: number;
  gaitPattern?: string;
}

export interface UserProfile {
  name: string;
  age: number;
  weight: number;
  height: number;
  diabetesDuration: number;
  hba1c: number;
  riskLevel: 'low' | 'medium' | 'high';
}

export interface Thresholds {
  pressure: number;
  temperature: number;
}

export interface GaitAnalysis {
  healthIndex: number;
  level: 'green' | 'amber' | 'red';
  gaitPattern: string;
  gaitConfidence: number;
  highRiskZone: string;
  iwgdfCategory: number;
  cadenceSpm: number;
  peakKpa: number;
  factors: Record<string, number>;
}

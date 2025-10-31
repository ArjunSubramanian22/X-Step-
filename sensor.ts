export type FootZone = 'heel' | 'arch' | 'ball' | 'toes';

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
}

export interface Alert {
  id: string;
  type: 'pressure' | 'temperature';
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

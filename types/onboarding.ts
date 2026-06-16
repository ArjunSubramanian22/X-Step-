export interface OnboardingProfile {
  age?: number;
  gender?: string;
  weight?: number;
  height?: number;
  diabetesType?: string;
  diabetesDuration?: number;
  hasNeuropathy?: boolean | null;
  hasUlcers?: boolean | null;
  hasAmputation?: boolean | null;
  hba1c?: number;
  medications?: string;
  workType?: string;
  footwearType?: string;
}

export interface CalibrationBaseline {
  pressure: number;
  temperature: number;
}

export interface OnboardingData {
  profile: OnboardingProfile;
  measurementUnit: 'kPa' | 'PSI';
  notificationThreshold: number;
  mockDataFrequency: 'slow' | 'normal' | 'fast';
  calibrationBaseline?: CalibrationBaseline;
}

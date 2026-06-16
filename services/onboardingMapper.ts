import type { OnboardingData } from '@/types/onboarding';
import type { MedicalRecord } from '@/types/health';
import type { UserProfile } from '@/types/sensor';

function mapNeuropathyStatus(
  hasNeuropathy: boolean | null | undefined
): MedicalRecord['neuropathyStatus'] {
  if (hasNeuropathy === true) return 'Moderate';
  if (hasNeuropathy === false) return 'None';
  return 'Mild';
}

function mapWorkType(workType?: string): MedicalRecord['workType'] {
  switch (workType) {
    case 'Mostly Sitting':
      return 'Sedentary';
    case 'Mostly Standing':
      return 'Standing';
    case 'Mostly Walking':
      return 'Walking';
    case 'Physical Labor':
      return 'Physical Labor';
    default:
      return 'Standing';
  }
}

function mapDiabetesType(
  type?: string
): MedicalRecord['diabetesType'] {
  if (type === 'Type 1') return 'Type 1';
  if (type === 'Prediabetes') return 'Type 2';
  return 'Type 2';
}

export function onboardingToMedicalRecord(
  data: OnboardingData
): MedicalRecord {
  const { profile } = data;

  return {
    diabetesType: mapDiabetesType(profile.diabetesType),
    diabetesDuration: profile.diabetesDuration ?? 0,
    hba1c: profile.hba1c ?? 7.0,
    lastHba1cDate: new Date().toISOString().split('T')[0],
    medications: profile.medications
      ? profile.medications.split(',').map((m) => m.trim()).filter(Boolean)
      : [],
    neuropathyStatus: mapNeuropathyStatus(profile.hasNeuropathy),
    hasFootUlcers: profile.hasUlcers === true,
    ulcerHistory: profile.hasUlcers ? ['Reported during onboarding'] : [],
    amputationHistory: profile.hasAmputation === true,
    vascularComplications: [],
    cholesterol: 0,
    bloodPressure: '',
    smokingStatus: 'Never',
    alcoholUse: 'None',
    exerciseLevel: 'Light',
    workType: mapWorkType(profile.workType),
    footwearHabits: profile.footwearType ? [profile.footwearType] : [],
  };
}

export function onboardingToUserProfile(
  data: OnboardingData,
  userName: string
): UserProfile {
  const { profile } = data;
  const hba1c = profile.hba1c ?? 7.0;

  let riskLevel: UserProfile['riskLevel'] = 'low';
  if (profile.hasUlcers || profile.hasAmputation) {
    riskLevel = 'high';
  } else if (profile.hasNeuropathy || hba1c > 7.5) {
    riskLevel = 'medium';
  }

  return {
    name: userName,
    age: profile.age ?? 0,
    weight: profile.weight ?? 0,
    height: profile.height ?? 0,
    diabetesDuration: profile.diabetesDuration ?? 0,
    hba1c,
    riskLevel,
  };
}

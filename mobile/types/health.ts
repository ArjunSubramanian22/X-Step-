export interface MedicalRecord {
  diabetesType: 'Type 1' | 'Type 2' | 'Gestational';
  diabetesDuration: number;
  hba1c: number;
  lastHba1cDate: string;
  medications: string[];
  neuropathyStatus: 'None' | 'Mild' | 'Moderate' | 'Severe';
  hasFootUlcers: boolean;
  ulcerHistory: string[];
  amputationHistory: boolean;
  vascularComplications: string[];
  cholesterol: number;
  bloodPressure: string;
  smokingStatus: 'Never' | 'Former' | 'Current';
  alcoholUse: 'None' | 'Occasional' | 'Regular';
  exerciseLevel: 'Sedentary' | 'Light' | 'Moderate' | 'Active';
  workType: 'Sedentary' | 'Standing' | 'Walking' | 'Physical Labor';
  footwearHabits: string[];
}

export interface HealthIndex {
  score: number;
  level: 'green' | 'amber' | 'red';
  factors: {
    footPressure: number;
    temperature: number;
    neuropathy: number;
    glycemicControl: number;
    compliance: number;
  };
}

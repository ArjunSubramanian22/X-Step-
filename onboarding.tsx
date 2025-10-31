import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'expo-router';
import { 
  Activity, 
  CheckCircle, 
  ChevronRight, 
  Heart, 
  Settings as SettingsIcon,
  User,
  Footprints,
  Shield
} from 'lucide-react-native';
import { useEffect, useRef, useState } from 'react';
import { 
  Animated, 
  ScrollView, 
  StyleSheet, 
  Text, 
  TextInput, 
  TouchableOpacity, 
  View 
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const STEPS = [
  { id: 'welcome', title: 'Welcome', icon: Heart },
  { id: 'profile', title: 'Profile', icon: User },
  { id: 'medical', title: 'Medical History', icon: Heart },
  { id: 'lifestyle', title: 'Lifestyle', icon: Activity },
  { id: 'settings', title: 'Preferences', icon: SettingsIcon },
  { id: 'calibration', title: 'Calibration', icon: Footprints },
  { id: 'complete', title: 'Complete', icon: Shield },
];

export default function OnboardingScreen() {
  const { user, completeOnboarding } = useAuth();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const [currentStep, setCurrentStep] = useState<number>(0);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const progressAnim = useRef(new Animated.Value(0)).current;

  const [age, setAge] = useState<string>('');
  const [gender, setGender] = useState<string>('');
  const [weight, setWeight] = useState<string>('');
  const [height, setHeight] = useState<string>('');
  
  const [diabetesType, setDiabetesType] = useState<string>('');
  const [diabetesDuration, setDiabetesDuration] = useState<string>('');
  const [hasNeuropathy, setHasNeuropathy] = useState<boolean | null>(null);
  const [hasUlcers, setHasUlcers] = useState<boolean | null>(null);
  const [hasAmputation, setHasAmputation] = useState<boolean | null>(null);
  const [hba1c, setHba1c] = useState<string>('');
  const [medications, setMedications] = useState<string>('');

  const [workType, setWorkType] = useState<string>('');
  const [footwearType, setFootwearType] = useState<string>('');

  const [measurementUnit, setMeasurementUnit] = useState<'kPa' | 'PSI'>('kPa');
  const [notificationThreshold, setNotificationThreshold] = useState<number>(75);
  const [mockDataFrequency, setMockDataFrequency] = useState<'slow' | 'normal' | 'fast'>('normal');

  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [scanProgress, setScanProgress] = useState<number>(0);

  useEffect(() => {
    fadeAnim.setValue(0);
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 400,
      useNativeDriver: true,
    }).start();
  }, [currentStep, fadeAnim]);

  const nextStep = () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const startCalibration = () => {
    setIsScanning(true);
    setScanProgress(0);

    Animated.timing(progressAnim, {
      toValue: 1,
      duration: 4000,
      useNativeDriver: false,
    }).start(() => {
      setIsScanning(false);
      setScanProgress(100);
      setTimeout(() => nextStep(), 500);
    });
  };

  const handleComplete = async () => {
    await completeOnboarding({
      measurementUnit,
      notificationThreshold,
      mockDataFrequency,
    });
    router.replace('/dashboard');
  };

  useEffect(() => {
    if (isScanning) {
      const interval = setInterval(() => {
        setScanProgress(prev => {
          const newProgress = prev + (100 / 40);
          return newProgress > 100 ? 100 : newProgress;
        });
      }, 100);
      return () => clearInterval(interval);
    }
  }, [isScanning]);

  const renderWelcome = () => (
    <Animated.View style={[styles.stepContainer, { opacity: fadeAnim }]}>
      <View style={styles.centerContent}>
        <View style={styles.iconCircle}>
          <Heart size={48} color="#3B82F6" />
        </View>
        
        <Text style={styles.stepTitle}>Welcome to X-Step</Text>
        <Text style={styles.stepSubtitle}>
          Your journey to better foot health starts here
        </Text>

        <View style={styles.featureList}>
          <View style={styles.featureItem}>
            <Activity size={20} color="#3B82F6" />
            <Text style={styles.featureText}>Real-time pressure monitoring</Text>
          </View>
          <View style={styles.featureItem}>
            <Heart size={20} color="#3B82F6" />
            <Text style={styles.featureText}>Personalized risk assessment</Text>
          </View>
          <View style={styles.featureItem}>
            <Shield size={20} color="#3B82F6" />
            <Text style={styles.featureText}>Proactive alerts & insights</Text>
          </View>
        </View>
      </View>

      <TouchableOpacity style={styles.primaryButton} onPress={nextStep}>
        <Text style={styles.primaryButtonText}>Get Started</Text>
        <ChevronRight size={20} color="#FFFFFF" />
      </TouchableOpacity>
    </Animated.View>
  );

  const renderProfile = () => (
    <Animated.View style={[styles.stepContainer, { opacity: fadeAnim }]}>
      <ScrollView showsVerticalScrollIndicator={false}>
        <Text style={styles.stepTitle}>Basic Information</Text>
        <Text style={styles.stepDescription}>
          Help us personalize your experience
        </Text>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Age</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter your age"
            placeholderTextColor="#475569"
            value={age}
            onChangeText={setAge}
            keyboardType="numeric"
          />
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Gender</Text>
          <View style={styles.optionRow}>
            {['Male', 'Female', 'Other'].map((option) => (
              <TouchableOpacity
                key={option}
                style={[
                  styles.optionButton,
                  gender === option && styles.optionButtonActive,
                ]}
                onPress={() => setGender(option)}
              >
                <Text
                  style={[
                    styles.optionButtonText,
                    gender === option && styles.optionButtonTextActive,
                  ]}
                >
                  {option}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={styles.formRow}>
          <View style={[styles.formGroup, { flex: 1 }]}>
            <Text style={styles.label}>Weight (kg)</Text>
            <TextInput
              style={styles.input}
              placeholder="70"
              placeholderTextColor="#475569"
              value={weight}
              onChangeText={setWeight}
              keyboardType="numeric"
            />
          </View>

          <View style={[styles.formGroup, { flex: 1 }]}>
            <Text style={styles.label}>Height (cm)</Text>
            <TextInput
              style={styles.input}
              placeholder="170"
              placeholderTextColor="#475569"
              value={height}
              onChangeText={setHeight}
              keyboardType="numeric"
            />
          </View>
        </View>
      </ScrollView>

      <View style={styles.buttonRow}>
        <TouchableOpacity style={styles.secondaryButton} onPress={prevStep}>
          <Text style={styles.secondaryButtonText}>Back</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.primaryButton, { flex: 1 }]} onPress={nextStep}>
          <Text style={styles.primaryButtonText}>Continue</Text>
        </TouchableOpacity>
      </View>
    </Animated.View>
  );

  const renderMedical = () => (
    <Animated.View style={[styles.stepContainer, { opacity: fadeAnim }]}>
      <ScrollView showsVerticalScrollIndicator={false}>
        <Text style={styles.stepTitle}>Medical Profile</Text>
        <Text style={styles.stepDescription}>
          This helps us assess your risk level accurately
        </Text>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Diabetes Type</Text>
          <View style={styles.optionRow}>
            {['Type 1', 'Type 2', 'Prediabetes'].map((option) => (
              <TouchableOpacity
                key={option}
                style={[
                  styles.optionButton,
                  diabetesType === option && styles.optionButtonActive,
                ]}
                onPress={() => setDiabetesType(option)}
              >
                <Text
                  style={[
                    styles.optionButtonText,
                    diabetesType === option && styles.optionButtonTextActive,
                  ]}
                >
                  {option}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Duration (years)</Text>
          <TextInput
            style={styles.input}
            placeholder="How long have you had diabetes?"
            placeholderTextColor="#475569"
            value={diabetesDuration}
            onChangeText={setDiabetesDuration}
            keyboardType="numeric"
          />
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>HbA1c Level (optional)</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g., 7.2"
            placeholderTextColor="#475569"
            value={hba1c}
            onChangeText={setHba1c}
            keyboardType="decimal-pad"
          />
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Do you have peripheral neuropathy?</Text>
          <View style={styles.optionRow}>
            {[
              { label: 'Yes', value: true },
              { label: 'No', value: false },
              { label: 'Unknown', value: null },
            ].map((option) => (
              <TouchableOpacity
                key={option.label}
                style={[
                  styles.optionButton,
                  hasNeuropathy === option.value && styles.optionButtonActive,
                ]}
                onPress={() => setHasNeuropathy(option.value)}
              >
                <Text
                  style={[
                    styles.optionButtonText,
                    hasNeuropathy === option.value && styles.optionButtonTextActive,
                  ]}
                >
                  {option.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Current or past foot ulcers?</Text>
          <View style={styles.optionRow}>
            {[
              { label: 'Yes', value: true },
              { label: 'No', value: false },
            ].map((option) => (
              <TouchableOpacity
                key={option.label}
                style={[
                  styles.optionButton,
                  hasUlcers === option.value && styles.optionButtonActive,
                ]}
                onPress={() => setHasUlcers(option.value)}
              >
                <Text
                  style={[
                    styles.optionButtonText,
                    hasUlcers === option.value && styles.optionButtonTextActive,
                  ]}
                >
                  {option.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Previous amputation?</Text>
          <View style={styles.optionRow}>
            {[
              { label: 'Yes', value: true },
              { label: 'No', value: false },
            ].map((option) => (
              <TouchableOpacity
                key={option.label}
                style={[
                  styles.optionButton,
                  hasAmputation === option.value && styles.optionButtonActive,
                ]}
                onPress={() => setHasAmputation(option.value)}
              >
                <Text
                  style={[
                    styles.optionButtonText,
                    hasAmputation === option.value && styles.optionButtonTextActive,
                  ]}
                >
                  {option.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Current Medications (optional)</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            placeholder="e.g., Metformin, Insulin"
            placeholderTextColor="#475569"
            value={medications}
            onChangeText={setMedications}
            multiline
            numberOfLines={3}
          />
        </View>
      </ScrollView>

      <View style={styles.buttonRow}>
        <TouchableOpacity style={styles.secondaryButton} onPress={prevStep}>
          <Text style={styles.secondaryButtonText}>Back</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.primaryButton, { flex: 1 }]} onPress={nextStep}>
          <Text style={styles.primaryButtonText}>Continue</Text>
        </TouchableOpacity>
      </View>
    </Animated.View>
  );

  const renderLifestyle = () => (
    <Animated.View style={[styles.stepContainer, { opacity: fadeAnim }]}>
      <ScrollView showsVerticalScrollIndicator={false}>
        <Text style={styles.stepTitle}>Lifestyle & Activity</Text>
        <Text style={styles.stepDescription}>
          Understanding your daily routine helps us tailor insights
        </Text>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Primary Work Activity</Text>
          <View style={styles.optionGrid}>
            {['Mostly Sitting', 'Mostly Standing', 'Mostly Walking', 'Physical Labor'].map(
              (option) => (
                <TouchableOpacity
                  key={option}
                  style={[
                    styles.gridButton,
                    workType === option && styles.optionButtonActive,
                  ]}
                  onPress={() => setWorkType(option)}
                >
                  <Text
                    style={[
                      styles.optionButtonText,
                      workType === option && styles.optionButtonTextActive,
                    ]}
                  >
                    {option}
                  </Text>
                </TouchableOpacity>
              )
            )}
          </View>
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Typical Footwear</Text>
          <View style={styles.optionGrid}>
            {['Athletic Shoes', 'Dress Shoes', 'Sandals', 'Diabetic Shoes'].map((option) => (
              <TouchableOpacity
                key={option}
                style={[
                  styles.gridButton,
                  footwearType === option && styles.optionButtonActive,
                ]}
                onPress={() => setFootwearType(option)}
              >
                <Text
                  style={[
                    styles.optionButtonText,
                    footwearType === option && styles.optionButtonTextActive,
                  ]}
                >
                  {option}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </ScrollView>

      <View style={styles.buttonRow}>
        <TouchableOpacity style={styles.secondaryButton} onPress={prevStep}>
          <Text style={styles.secondaryButtonText}>Back</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.primaryButton, { flex: 1 }]} onPress={nextStep}>
          <Text style={styles.primaryButtonText}>Continue</Text>
        </TouchableOpacity>
      </View>
    </Animated.View>
  );

  const renderSettings = () => (
    <Animated.View style={[styles.stepContainer, { opacity: fadeAnim }]}>
      <ScrollView showsVerticalScrollIndicator={false}>
        <Text style={styles.stepTitle}>App Preferences</Text>
        <Text style={styles.stepDescription}>Customize your monitoring experience</Text>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Measurement Unit</Text>
          <View style={styles.optionRow}>
            {(['kPa', 'PSI'] as const).map((unit) => (
              <TouchableOpacity
                key={unit}
                style={[
                  styles.optionButton,
                  measurementUnit === unit && styles.optionButtonActive,
                ]}
                onPress={() => setMeasurementUnit(unit)}
              >
                <Text
                  style={[
                    styles.optionButtonText,
                    measurementUnit === unit && styles.optionButtonTextActive,
                  ]}
                >
                  {unit}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Alert Threshold</Text>
          <View style={styles.optionRow}>
            {[65, 75, 85].map((value) => (
              <TouchableOpacity
                key={value}
                style={[
                  styles.optionButton,
                  notificationThreshold === value && styles.optionButtonActive,
                ]}
                onPress={() => setNotificationThreshold(value)}
              >
                <Text
                  style={[
                    styles.optionButtonText,
                    notificationThreshold === value && styles.optionButtonTextActive,
                  ]}
                >
                  {value}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Data Update Speed</Text>
          <View style={styles.optionRow}>
            {(['slow', 'normal', 'fast'] as const).map((freq) => (
              <TouchableOpacity
                key={freq}
                style={[
                  styles.optionButton,
                  mockDataFrequency === freq && styles.optionButtonActive,
                ]}
                onPress={() => setMockDataFrequency(freq)}
              >
                <Text
                  style={[
                    styles.optionButtonText,
                    mockDataFrequency === freq && styles.optionButtonTextActive,
                  ]}
                >
                  {freq.charAt(0).toUpperCase() + freq.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </ScrollView>

      <View style={styles.buttonRow}>
        <TouchableOpacity style={styles.secondaryButton} onPress={prevStep}>
          <Text style={styles.secondaryButtonText}>Back</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.primaryButton, { flex: 1 }]} onPress={nextStep}>
          <Text style={styles.primaryButtonText}>Continue</Text>
        </TouchableOpacity>
      </View>
    </Animated.View>
  );

  const renderCalibration = () => {
    const progress = progressAnim.interpolate({
      inputRange: [0, 1],
      outputRange: ['0%', '100%'],
    });

    return (
      <Animated.View style={[styles.stepContainer, { opacity: fadeAnim }]}>
        <View style={styles.centerContent}>
          <Text style={styles.stepTitle}>Calibration</Text>
          <Text style={styles.stepDescription}>
            {!isScanning && scanProgress === 0
              ? 'Stand comfortably to calibrate your baseline'
              : isScanning
              ? 'Recording baseline... Hold steady'
              : 'Calibration complete!'}
          </Text>

          <View style={styles.scanContainer}>
            <View style={styles.scanCircle}>
              {scanProgress === 100 ? (
                <CheckCircle size={64} color="#10B981" />
              ) : (
                <Footprints size={64} color={isScanning ? '#3B82F6' : '#475569'} />
              )}
              {isScanning && (
                <Animated.View
                  style={[
                    styles.scanPulse,
                    {
                      opacity: progressAnim.interpolate({
                        inputRange: [0, 0.5, 1],
                        outputRange: [0.2, 0.6, 0.2],
                      }),
                    },
                  ]}
                />
              )}
            </View>

            {isScanning && (
              <View style={styles.progressContainer}>
                <View style={styles.progressBar}>
                  <Animated.View style={[styles.progressFill, { width: progress }]} />
                </View>
                <Text style={styles.progressText}>{Math.round(scanProgress)}%</Text>
              </View>
            )}
          </View>
        </View>

        {!isScanning && scanProgress === 0 && (
          <View style={styles.buttonRow}>
            <TouchableOpacity style={styles.secondaryButton} onPress={prevStep}>
              <Text style={styles.secondaryButtonText}>Back</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.primaryButton, { flex: 1 }]} onPress={startCalibration}>
              <Text style={styles.primaryButtonText}>Start Calibration</Text>
            </TouchableOpacity>
          </View>
        )}
      </Animated.View>
    );
  };

  const renderComplete = () => (
    <Animated.View style={[styles.stepContainer, { opacity: fadeAnim }]}>
      <View style={styles.centerContent}>
        <View style={[styles.iconCircle, { backgroundColor: '#10B98120' }]}>
          <CheckCircle size={56} color="#10B981" />
        </View>

        <Text style={styles.stepTitle}>You&apos;re All Set!</Text>
        <Text style={styles.stepDescription}>
          Your profile is complete. X-Step is now personalized to your needs and ready to monitor
          your foot health.
        </Text>

        <View style={styles.completeSummary}>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryLabel}>Profile Created</Text>
            <Text style={styles.summaryValue}>{user?.name}</Text>
          </View>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryLabel}>Risk Assessment</Text>
            <Text style={styles.summaryValue}>Personalized</Text>
          </View>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryLabel}>Alerts Enabled</Text>
            <Text style={styles.summaryValue}>Active</Text>
          </View>
        </View>
      </View>

      <TouchableOpacity style={styles.primaryButton} onPress={handleComplete}>
        <Text style={styles.primaryButtonText}>Start Monitoring</Text>
        <ChevronRight size={20} color="#FFFFFF" />
      </TouchableOpacity>
    </Animated.View>
  );

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return renderWelcome();
      case 1:
        return renderProfile();
      case 2:
        return renderMedical();
      case 3:
        return renderLifestyle();
      case 4:
        return renderSettings();
      case 5:
        return renderCalibration();
      case 6:
        return renderComplete();
      default:
        return renderWelcome();
    }
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top, paddingBottom: insets.bottom }]}>
      <View style={styles.progressHeader}>
        <View style={styles.progressBarContainer}>
          {STEPS.map((_, index) => (
            <View
              key={index}
              style={[
                styles.progressSegment,
                index <= currentStep && styles.progressSegmentActive,
              ]}
            />
          ))}
        </View>
        <Text style={styles.progressText}>
          Step {currentStep + 1} of {STEPS.length}
        </Text>
      </View>

      {renderStep()}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0A0E1A',
  },
  progressHeader: {
    paddingHorizontal: 24,
    paddingVertical: 16,
  },
  progressBarContainer: {
    flexDirection: 'row',
    gap: 4,
    marginBottom: 8,
  },
  progressSegment: {
    flex: 1,
    height: 3,
    backgroundColor: '#1E2530',
    borderRadius: 2,
  },
  progressSegmentActive: {
    backgroundColor: '#3B82F6',
  },
  progressText: {
    fontSize: 12,
    color: '#6E7681',
    textAlign: 'center',
  },
  stepContainer: {
    flex: 1,
    paddingHorizontal: 24,
    paddingVertical: 16,
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconCircle: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: '#3B82F620',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  stepTitle: {
    fontSize: 28,
    fontWeight: '700' as const,
    color: '#FFFFFF',
    marginBottom: 12,
    textAlign: 'center',
  },
  stepSubtitle: {
    fontSize: 16,
    color: '#94A3B8',
    textAlign: 'center',
    marginBottom: 32,
    lineHeight: 24,
  },
  stepDescription: {
    fontSize: 15,
    color: '#6E7681',
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 22,
  },
  featureList: {
    width: '100%',
    gap: 16,
    marginBottom: 32,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#0F1419',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#1E2530',
  },
  featureText: {
    fontSize: 15,
    color: '#C9D1D9',
    flex: 1,
  },
  formGroup: {
    marginBottom: 20,
  },
  formRow: {
    flexDirection: 'row',
    gap: 12,
  },
  label: {
    fontSize: 14,
    fontWeight: '600' as const,
    color: '#C9D1D9',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#0F1419',
    borderWidth: 1,
    borderColor: '#1E2530',
    borderRadius: 12,
    padding: 14,
    fontSize: 15,
    color: '#E8EAED',
  },
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  optionRow: {
    flexDirection: 'row',
    gap: 8,
  },
  optionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  optionButton: {
    flex: 1,
    backgroundColor: '#0F1419',
    borderWidth: 1,
    borderColor: '#1E2530',
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 16,
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 80,
  },
  gridButton: {
    width: '48%',
    backgroundColor: '#0F1419',
    borderWidth: 1,
    borderColor: '#1E2530',
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  optionButtonActive: {
    backgroundColor: '#2563EB',
    borderColor: '#2563EB',
  },
  optionButtonText: {
    fontSize: 14,
    fontWeight: '500' as const,
    color: '#6E7681',
  },
  optionButtonTextActive: {
    color: '#FFFFFF',
  },
  scanContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 32,
  },
  scanCircle: {
    width: 160,
    height: 160,
    borderRadius: 80,
    backgroundColor: '#0F1419',
    borderWidth: 2,
    borderColor: '#1E2530',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  scanPulse: {
    position: 'absolute',
    width: 180,
    height: 180,
    borderRadius: 90,
    borderWidth: 3,
    borderColor: '#3B82F6',
  },
  progressContainer: {
    width: '100%',
    alignItems: 'center',
  },
  progressBar: {
    width: '100%',
    height: 6,
    backgroundColor: '#0F1419',
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: 12,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#3B82F6',
    borderRadius: 3,
  },
  completeSummary: {
    width: '100%',
    gap: 12,
    marginTop: 24,
  },
  summaryItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#0F1419',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#1E2530',
  },
  summaryLabel: {
    fontSize: 14,
    color: '#6E7681',
  },
  summaryValue: {
    fontSize: 15,
    fontWeight: '600' as const,
    color: '#C9D1D9',
  },
  primaryButton: {
    backgroundColor: '#2563EB',
    borderRadius: 12,
    height: 52,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600' as const,
  },
  secondaryButton: {
    backgroundColor: '#0F1419',
    borderWidth: 1,
    borderColor: '#1E2530',
    borderRadius: 12,
    height: 52,
    paddingHorizontal: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  secondaryButtonText: {
    color: '#C9D1D9',
    fontSize: 16,
    fontWeight: '500' as const,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
  },
});

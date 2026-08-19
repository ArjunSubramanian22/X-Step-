import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'expo-router';
import { Mail, User } from 'lucide-react-native';
import { useState } from 'react';
import { Alert, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export default function LoginScreen() {
  const { login } = useAuth();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const [email, setEmail] = useState<string>('');
  const [name, setName] = useState<string>('');

  const handleEmailLogin = () => {
    if (!email.trim() || !name.trim()) {
      Alert.alert('Error', 'Please enter your name and email');
      return;
    }
    
    login({
      id: `user-${Date.now()}`,
      name: name.trim(),
      email: email.trim(),
      loginMethod: 'email',
    });
    router.replace('/onboarding');
  };

  const handleGoogleLogin = () => {
    login({
      id: `user-${Date.now()}`,
      name: 'Google User',
      email: 'user@gmail.com',
      loginMethod: 'google',
    });
    router.replace('/onboarding');
  };

  const handleAppleLogin = () => {
    login({
      id: `user-${Date.now()}`,
      name: 'Apple User',
      email: 'user@icloud.com',
      loginMethod: 'apple',
    });
    router.replace('/onboarding');
  };

  const handleGuestLogin = () => {
    login({
      id: `guest-${Date.now()}`,
      name: 'Guest User',
      email: '',
      loginMethod: 'guest',
    });
    router.replace('/onboarding');
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top, paddingBottom: insets.bottom }]}>
      <View style={styles.content}>
        <View style={styles.loginCard}>
          <View style={styles.header}>
            <Text style={styles.title}>X-Step</Text>
            <Text style={styles.subtitle}>Smart Insole Monitoring</Text>
          </View>

          <View style={styles.form}>
            <View style={styles.inputContainer}>
              <User size={18} color="#64748B" style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="Full Name"
                placeholderTextColor="#475569"
                value={name}
                onChangeText={setName}
                autoCapitalize="words"
              />
            </View>

            <View style={styles.inputContainer}>
              <Mail size={18} color="#64748B" style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="Email Address"
                placeholderTextColor="#475569"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
              />
            </View>

            <TouchableOpacity style={styles.primaryButton} onPress={handleEmailLogin}>
              <Text style={styles.primaryButtonText}>Continue</Text>
            </TouchableOpacity>

            <View style={styles.divider}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>or</Text>
              <View style={styles.dividerLine} />
            </View>

            <TouchableOpacity style={styles.socialButton} onPress={handleGoogleLogin}>
              <Text style={styles.socialButtonText}>Continue with Google</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.socialButton} onPress={handleAppleLogin}>
              <Text style={styles.socialButtonText}>Continue with Apple</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.guestButton} onPress={handleGuestLogin}>
              <Text style={styles.guestButtonText}>Guest</Text>
            </TouchableOpacity>
          </View>
        </View>

        <Text style={styles.footer}>
          By continuing, you agree to our Terms & Privacy Policy
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0A0E1A',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  loginCard: {
    width: '100%',
    maxWidth: 400,
    backgroundColor: '#0F1419',
    borderRadius: 24,
    padding: 32,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
    borderWidth: 1,
    borderColor: '#1E2530',
  },
  header: {
    alignItems: 'center',
    marginBottom: 32,
  },
  title: {
    fontSize: 36,
    fontWeight: '700' as const,
    color: '#FFFFFF',
    marginBottom: 4,
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 14,
    color: '#64748B',
    letterSpacing: 0.5,
  },
  form: {
    width: '100%',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#161B22',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#21262D',
    paddingHorizontal: 14,
    marginBottom: 12,
  },
  inputIcon: {
    marginRight: 10,
  },
  input: {
    flex: 1,
    height: 48,
    color: '#E8EAED',
    fontSize: 15,
  },
  primaryButton: {
    backgroundColor: '#2563EB',
    borderRadius: 12,
    height: 48,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 8,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600' as const,
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 20,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#21262D',
  },
  dividerText: {
    color: '#6E7681',
    fontSize: 13,
    paddingHorizontal: 12,
  },
  socialButton: {
    backgroundColor: '#161B22',
    borderRadius: 12,
    height: 48,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#21262D',
  },
  socialButtonText: {
    color: '#C9D1D9',
    fontSize: 15,
    fontWeight: '500' as const,
  },
  guestButton: {
    marginTop: 8,
    height: 42,
    justifyContent: 'center',
    alignItems: 'center',
  },
  guestButtonText: {
    color: '#6E7681',
    fontSize: 14,
    fontWeight: '500' as const,
  },
  footer: {
    color: '#6E7681',
    fontSize: 11,
    textAlign: 'center',
    marginTop: 24,
    lineHeight: 16,
  },
});

import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useSensor } from '@/contexts/SensorContext';
import { uploadUlcerPhoto } from '@/services/mlClient';
import Colors from '@/constants/colors';

export default function WoundScanScreen() {
  const { isDarkMode } = useSensor();
  const colors = isDarkMode ? Colors.dark : Colors.light;
  const insets = useSafeAreaInsets();
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{ grade: number; label: string; backend: string; disclaimer: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const run = async (uri?: string) => {
    setBusy(true);
    setError(null);
    const photo = await uploadUlcerPhoto(uri ?? 'file://demo.jpg');
    setBusy(false);
    if (!photo) {
      setError('ML API is offline. Start `python -m api.main` then retry. On-device guidance still uses pressure + gait models.');
      return;
    }
    setResult(photo);
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background, paddingTop: insets.top + 16 }]}>
      <Text style={[styles.title, { color: colors.text }]}>Wound photo check</Text>
      <Text style={[styles.body, { color: colors.textSecondary }]}>
        Upload a photo of an area of concern. The ulcer CNN estimates Wagner-style grade 1–4. This is not a diagnosis.
      </Text>
      <TouchableOpacity style={[styles.button, { backgroundColor: colors.primary }]} onPress={() => run()} disabled={busy}>
        {busy ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Analyze with ML API</Text>}
      </TouchableOpacity>
      {error ? <Text style={[styles.body, { color: colors.danger, marginTop: 16 }]}>{error}</Text> : null}
      {result ? (
        <View style={[styles.card, { backgroundColor: colors.surface }]}>
          <Text style={[styles.title, { color: colors.text }]}>Grade {result.grade}</Text>
          <Text style={[styles.body, { color: colors.textSecondary }]}>{result.label}</Text>
          <Text style={[styles.body, { color: colors.textTertiary, marginTop: 8 }]}>
            Backend: {result.backend}. {result.disclaimer}
          </Text>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20 },
  title: { fontSize: 22, fontWeight: '700' as const, marginBottom: 8 },
  body: { fontSize: 15, lineHeight: 22 },
  button: { marginTop: 24, borderRadius: 12, padding: 16, alignItems: 'center' },
  buttonText: { color: '#fff', fontWeight: '700' as const, fontSize: 16 },
  card: { marginTop: 24, padding: 16, borderRadius: 16 },
});

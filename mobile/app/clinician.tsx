import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useSensor } from '@/contexts/SensorContext';
import { useHealth } from '@/contexts/HealthContext';
import Colors from '@/constants/colors';

export default function ClinicianScreen() {
  const { isDarkMode, history, alerts, gaitAnalysis, footData } = useSensor();
  const { medicalRecord } = useHealth();
  const colors = isDarkMode ? Colors.dark : Colors.light;
  const insets = useSafeAreaInsets();
  const openAlerts = alerts.filter((a) => !a.dismissed).slice(0, 8);

  return (
    <ScrollView style={[styles.container, { backgroundColor: colors.background, paddingTop: insets.top + 16 }]}>
      <Text style={[styles.title, { color: colors.text }]}>Clinician snapshot</Text>
      <Text style={[styles.body, { color: colors.textSecondary }]}>
        Share this summary at clinic visits. Pressure, gait pattern, and alert log are generated from the 4-FSR insole (1st, 2nd, 5th metatarsal + heel).
      </Text>

      <View style={[styles.card, { backgroundColor: colors.surface }]}>
        <Text style={[styles.label, { color: colors.textSecondary }]}>Clinical</Text>
        <Text style={[styles.body, { color: colors.text }]}>
          {medicalRecord.diabetesType} · HbA1c {medicalRecord.hba1c}% · neuropathy {medicalRecord.neuropathyStatus}
        </Text>
        <Text style={[styles.body, { color: colors.text }]}>IWGDF-style category {gaitAnalysis.iwgdfCategory}</Text>
      </View>

      <View style={[styles.card, { backgroundColor: colors.surface }]}>
        <Text style={[styles.label, { color: colors.textSecondary }]}>Today's biomechanics</Text>
        <Text style={[styles.body, { color: colors.text }]}>
          Pattern: {gaitAnalysis.gaitPattern.replace(/_/g, ' ')} ({(gaitAnalysis.gaitConfidence * 100).toFixed(0)}%)
        </Text>
        <Text style={[styles.body, { color: colors.text }]}>
          Cadence {gaitAnalysis.cadenceSpm.toFixed(0)} steps/min · peak {gaitAnalysis.peakKpa.toFixed(0)} kPa · zone {gaitAnalysis.highRiskZone}
        </Text>
        <Text style={[styles.body, { color: colors.text }]}>
          L heel {footData.left.heel.pressure.toFixed(0)} · 2nd MT {footData.left.ball.pressure.toFixed(0)} kPa
        </Text>
      </View>

      <View style={[styles.card, { backgroundColor: colors.surface }]}>
        <Text style={[styles.label, { color: colors.textSecondary }]}>14-day pressure peaks</Text>
        {history.slice(0, 14).map((d) => (
          <Text key={d.date} style={[styles.row, { color: colors.text }]}>
            {d.date}  {d.maxPressure.toFixed(0)} kPa  score {d.score.toFixed(0)}  alerts {d.alertCount}
          </Text>
        ))}
      </View>

      <View style={[styles.card, { backgroundColor: colors.surface, marginBottom: 40 }]}>
        <Text style={[styles.label, { color: colors.textSecondary }]}>Open alerts</Text>
        {openAlerts.length === 0 ? (
          <Text style={[styles.body, { color: colors.text }]}>None</Text>
        ) : (
          openAlerts.map((a) => (
            <Text key={a.id} style={[styles.row, { color: colors.text }]}>
              {a.foot} {a.zone}: {a.message}
            </Text>
          ))
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, paddingHorizontal: 20 },
  title: { fontSize: 22, fontWeight: '700' as const, marginBottom: 8 },
  body: { fontSize: 15, lineHeight: 22, marginBottom: 6 },
  label: { fontSize: 12, fontWeight: '700' as const, marginBottom: 8, textTransform: 'uppercase' as const },
  card: { marginTop: 16, padding: 16, borderRadius: 16 },
  row: { fontSize: 13, marginBottom: 4 },
});

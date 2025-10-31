import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { AlertTriangle, X, CheckCircle } from 'lucide-react-native';
import { useSensor } from '../../contexts/SensorContext';
import Colors from '../../constants/colors';

export default function AlertsScreen() {
  const { alerts, isDarkMode, dismissAlert } = useSensor();
  const colors = isDarkMode ? Colors.dark : Colors.light;
  const insets = useSafeAreaInsets();

  const activeAlerts = alerts.filter(a => !a.dismissed);
  const dismissedAlerts = alerts.filter(a => a.dismissed);

  const getAlertIcon = (type: 'pressure' | 'temperature') => {
    return type === 'pressure' ? (
      <AlertTriangle size={20} color={colors.danger} />
    ) : (
      <AlertTriangle size={20} color={colors.warning} />
    );
  };

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  };

  const renderAlert = (alert: any, isDismissed: boolean) => (
    <View
      key={alert.id}
      style={[
        styles.alertCard,
        {
          backgroundColor: colors.surface,
          opacity: isDismissed ? 0.5 : 1,
        },
      ]}
    >
      <View style={styles.alertHeader}>
        {getAlertIcon(alert.type)}
        <View style={styles.alertHeaderText}>
          <Text style={[styles.alertTitle, { color: colors.text }]}>
            {alert.type === 'pressure' ? 'High Pressure' : 'High Temperature'}
          </Text>
          <Text style={[styles.alertTime, { color: colors.textTertiary }]}>
            {formatTime(alert.timestamp)}
          </Text>
        </View>
        
        {!isDismissed && (
          <TouchableOpacity
            style={[styles.dismissButton, { backgroundColor: colors.surfaceElevated }]}
            onPress={() => dismissAlert(alert.id)}
          >
            <X size={16} color={colors.textSecondary} />
          </TouchableOpacity>
        )}
      </View>
      
      <Text style={[styles.alertMessage, { color: colors.textSecondary }]}>
        {alert.message}
      </Text>
      
      <View style={styles.alertDetails}>
        <View style={[styles.alertDetailItem, { backgroundColor: colors.surfaceElevated }]}>
          <Text style={[styles.alertDetailLabel, { color: colors.textTertiary }]}>
            Location
          </Text>
          <Text style={[styles.alertDetailValue, { color: colors.text }]}>
            {alert.foot} {alert.zone}
          </Text>
        </View>
        
        <View style={[styles.alertDetailItem, { backgroundColor: colors.surfaceElevated }]}>
          <Text style={[styles.alertDetailLabel, { color: colors.textTertiary }]}>
            Threshold
          </Text>
          <Text style={[styles.alertDetailValue, { color: colors.text }]}>
            {alert.threshold.toFixed(1)}
          </Text>
        </View>
      </View>
    </View>
  );

  return (
    <View style={[styles.container, { backgroundColor: colors.background, paddingTop: Platform.OS === 'web' ? insets.top : 0 }]}>
      <ScrollView style={styles.scrollView}>
        <View style={styles.header}>
          <AlertTriangle size={24} color={colors.primary} />
          <Text style={[styles.title, { color: colors.text }]}>
            Alerts & Notifications
          </Text>
        </View>

        {activeAlerts.length === 0 && dismissedAlerts.length === 0 && (
          <View style={styles.emptyState}>
            <CheckCircle size={64} color={colors.success} />
            <Text style={[styles.emptyTitle, { color: colors.text }]}>
              All Clear!
            </Text>
            <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
              No alerts detected. Your feet are in good condition.
            </Text>
          </View>
        )}

        {activeAlerts.length > 0 && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>
              Active Alerts ({activeAlerts.length})
            </Text>
            {activeAlerts.map(alert => renderAlert(alert, false))}
          </View>
        )}

        {dismissedAlerts.length > 0 && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>
              Dismissed ({dismissedAlerts.length})
            </Text>
            {dismissedAlerts.slice(0, 5).map(alert => renderAlert(alert, true))}
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: '700' as const,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600' as const,
    paddingHorizontal: 20,
    marginBottom: 12,
  },
  alertCard: {
    marginHorizontal: 20,
    marginBottom: 12,
    padding: 16,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  alertHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  alertHeaderText: {
    flex: 1,
  },
  alertTitle: {
    fontSize: 16,
    fontWeight: '600' as const,
    marginBottom: 2,
  },
  alertTime: {
    fontSize: 12,
  },
  dismissButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  alertMessage: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
  },
  alertDetails: {
    flexDirection: 'row',
    gap: 12,
  },
  alertDetailItem: {
    flex: 1,
    padding: 12,
    borderRadius: 12,
  },
  alertDetailLabel: {
    fontSize: 11,
    marginBottom: 4,
  },
  alertDetailValue: {
    fontSize: 16,
    fontWeight: '600' as const,
    textTransform: 'capitalize' as const,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 80,
    paddingHorizontal: 40,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: '700' as const,
    marginTop: 20,
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },
});

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Switch,
  Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Settings as SettingsIcon, User, Bell, Sliders, Moon, Sun, LogOut } from 'lucide-react-native';
import { useSensor } from '../../contexts/SensorContext';
import { useAuth } from '../../contexts/AuthContext';
import { useHealth } from '../../contexts/HealthContext';
import { useRouter } from 'expo-router';
import Colors from '../../constants/colors';

export default function SettingsScreen() {
  const { thresholds, isDarkMode, saveThresholds, toggleTheme } = useSensor();
  const { logout, user } = useAuth();
  const { medicalRecord } = useHealth();
  const router = useRouter();
  const colors = isDarkMode ? Colors.dark : Colors.light;
  const insets = useSafeAreaInsets();

  const [editingProfile, setEditingProfile] = useState(false);
  const [editingThresholds, setEditingThresholds] = useState(false);
  
  const [tempProfile, setTempProfile] = useState({
    name: user?.name || 'Guest User',
    age: 0,
    weight: 0,
    height: 0,
  });
  const [tempThresholds, setTempThresholds] = useState(thresholds);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);

  const handleSaveProfile = () => {
    setEditingProfile(false);
  };

  const handleSaveThresholds = () => {
    saveThresholds(tempThresholds);
    setEditingThresholds(false);
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background, paddingTop: Platform.OS === 'web' ? insets.top : 0 }]}>
      <ScrollView style={styles.scrollView}>
        <View style={styles.header}>
          <SettingsIcon size={24} color={colors.primary} />
          <Text style={[styles.title, { color: colors.text }]}>
            Settings
          </Text>
        </View>

        <View style={[styles.card, { backgroundColor: colors.surface }]}>
          <View style={styles.cardHeader}>
            <User size={20} color={colors.primary} />
            <Text style={[styles.cardTitle, { color: colors.text }]}>
              Profile Information
            </Text>
            <TouchableOpacity
              onPress={() => editingProfile ? handleSaveProfile() : setEditingProfile(true)}
              style={[styles.editButton, { backgroundColor: colors.surfaceElevated }]}
            >
              <Text style={[styles.editButtonText, { color: colors.primary }]}>
                {editingProfile ? 'Save' : 'Edit'}
              </Text>
            </TouchableOpacity>
          </View>

          <View style={styles.formRow}>
            <Text style={[styles.label, { color: colors.textSecondary }]}>Name</Text>
            <TextInput
              style={[
                styles.input,
                {
                  backgroundColor: colors.surfaceElevated,
                  color: colors.text,
                },
              ]}
              value={tempProfile.name}
              onChangeText={(text) => setTempProfile({ ...tempProfile, name: text })}
              editable={editingProfile}
              placeholderTextColor={colors.textTertiary}
            />
          </View>

          <View style={styles.formRow}>
            <Text style={[styles.label, { color: colors.textSecondary }]}>Age</Text>
            <TextInput
              style={[
                styles.input,
                {
                  backgroundColor: colors.surfaceElevated,
                  color: colors.text,
                },
              ]}
              value={tempProfile.age.toString()}
              onChangeText={(text) => setTempProfile({ ...tempProfile, age: parseInt(text) || 0 })}
              keyboardType="numeric"
              editable={editingProfile}
              placeholderTextColor={colors.textTertiary}
            />
          </View>

          <View style={styles.formRow}>
            <Text style={[styles.label, { color: colors.textSecondary }]}>Weight (kg)</Text>
            <TextInput
              style={[
                styles.input,
                {
                  backgroundColor: colors.surfaceElevated,
                  color: colors.text,
                },
              ]}
              value={tempProfile.weight.toString()}
              onChangeText={(text) => setTempProfile({ ...tempProfile, weight: parseInt(text) || 0 })}
              keyboardType="numeric"
              editable={editingProfile}
              placeholderTextColor={colors.textTertiary}
            />
          </View>

          <View style={styles.formRow}>
            <Text style={[styles.label, { color: colors.textSecondary }]}>Height (cm)</Text>
            <TextInput
              style={[
                styles.input,
                {
                  backgroundColor: colors.surfaceElevated,
                  color: colors.text,
                },
              ]}
              value={tempProfile.height.toString()}
              onChangeText={(text) => setTempProfile({ ...tempProfile, height: parseInt(text) || 0 })}
              keyboardType="numeric"
              editable={editingProfile}
              placeholderTextColor={colors.textTertiary}
            />
          </View>
        </View>

        <View style={[styles.card, { backgroundColor: colors.surface }]}>
          <View style={styles.cardHeader}>
            <Sliders size={20} color={colors.primary} />
            <Text style={[styles.cardTitle, { color: colors.text }]}>
              Alert Thresholds
            </Text>
            <TouchableOpacity
              onPress={() => editingThresholds ? handleSaveThresholds() : setEditingThresholds(true)}
              style={[styles.editButton, { backgroundColor: colors.surfaceElevated }]}
            >
              <Text style={[styles.editButtonText, { color: colors.primary }]}>
                {editingThresholds ? 'Save' : 'Edit'}
              </Text>
            </TouchableOpacity>
          </View>

          <View style={styles.formRow}>
            <Text style={[styles.label, { color: colors.textSecondary }]}>
              Pressure Threshold (kPa)
            </Text>
            <TextInput
              style={[
                styles.input,
                {
                  backgroundColor: colors.surfaceElevated,
                  color: colors.text,
                },
              ]}
              value={tempThresholds.pressure.toString()}
              onChangeText={(text) =>
                setTempThresholds({ ...tempThresholds, pressure: parseFloat(text) || 0 })
              }
              keyboardType="numeric"
              editable={editingThresholds}
              placeholderTextColor={colors.textTertiary}
            />
          </View>

          <View style={styles.formRow}>
            <Text style={[styles.label, { color: colors.textSecondary }]}>
              Temperature Threshold (°C)
            </Text>
            <TextInput
              style={[
                styles.input,
                {
                  backgroundColor: colors.surfaceElevated,
                  color: colors.text,
                },
              ]}
              value={tempThresholds.temperature.toString()}
              onChangeText={(text) =>
                setTempThresholds({ ...tempThresholds, temperature: parseFloat(text) || 0 })
              }
              keyboardType="numeric"
              editable={editingThresholds}
              placeholderTextColor={colors.textTertiary}
            />
          </View>
        </View>

        <View style={[styles.card, { backgroundColor: colors.surface }]}>
          <View style={styles.cardHeader}>
            <Bell size={20} color={colors.primary} />
            <Text style={[styles.cardTitle, { color: colors.text }]}>
              Preferences
            </Text>
          </View>

          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              {isDarkMode ? (
                <Moon size={20} color={colors.primary} />
              ) : (
                <Sun size={20} color={colors.primary} />
              )}
              <View>
                <Text style={[styles.settingTitle, { color: colors.text }]}>
                  Dark Mode
                </Text>
                <Text style={[styles.settingDescription, { color: colors.textSecondary }]}>
                  {isDarkMode ? 'Dark theme enabled' : 'Light theme enabled'}
                </Text>
              </View>
            </View>
            <Switch
              value={isDarkMode}
              onValueChange={toggleTheme}
              trackColor={{ false: colors.border, true: colors.primary }}
              thumbColor="#FFFFFF"
            />
          </View>

          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Bell size={20} color={colors.primary} />
              <View>
                <Text style={[styles.settingTitle, { color: colors.text }]}>
                  Push Notifications
                </Text>
                <Text style={[styles.settingDescription, { color: colors.textSecondary }]}>
                  Receive alerts for high readings
                </Text>
              </View>
            </View>
            <Switch
              value={notificationsEnabled}
              onValueChange={setNotificationsEnabled}
              trackColor={{ false: colors.border, true: colors.primary }}
              thumbColor="#FFFFFF"
            />
          </View>
        </View>

        <View style={[styles.card, { backgroundColor: colors.surface }]}>
          <TouchableOpacity
            style={styles.logoutButton}
            onPress={() => {
              logout();
              router.replace('/login');
            }}
          >
            <LogOut size={20} color={colors.danger} />
            <Text style={[styles.logoutText, { color: colors.danger }]}>Log Out</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.versionInfo}>
          <Text style={[styles.versionText, { color: colors.textTertiary }]}>
            Logged in as {user?.name || 'Guest'}
          </Text>
          <Text style={[styles.versionText, { color: colors.textTertiary }]}>
            X-Step v1.0.0 • Mock Data Edition
          </Text>
        </View>
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
  card: {
    marginHorizontal: 20,
    marginBottom: 16,
    padding: 20,
    borderRadius: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 20,
  },
  cardTitle: {
    flex: 1,
    fontSize: 18,
    fontWeight: '700' as const,
  },
  editButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 16,
  },
  editButtonText: {
    fontSize: 14,
    fontWeight: '600' as const,
  },
  formRow: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '500' as const,
    marginBottom: 8,
  },
  input: {
    padding: 12,
    borderRadius: 12,
    fontSize: 16,
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
  },
  settingInfo: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  settingTitle: {
    fontSize: 16,
    fontWeight: '600' as const,
    marginBottom: 2,
  },
  settingDescription: {
    fontSize: 13,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    paddingVertical: 16,
  },
  logoutText: {
    fontSize: 16,
    fontWeight: '600' as const,
  },
  versionInfo: {
    alignItems: 'center',
    paddingVertical: 32,
    gap: 4,
  },
  versionText: {
    fontSize: 12,
  },
});

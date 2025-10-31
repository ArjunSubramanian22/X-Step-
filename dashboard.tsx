import React, { useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import {
  Activity,
  MessageCircle,
  CheckCircle2,
  Circle,
  ChevronRight,
  Heart,
  TrendingUp,
  Clock,
  Sparkles,
} from 'lucide-react-native';
import { useSensor } from '../../contexts/SensorContext';
import { useHealth } from '../../contexts/HealthContext';
import { useTodo } from '../../contexts/TodoContext';
import { useRoutine } from '../../contexts/RoutineContext';
import { useAuth } from '../../contexts/AuthContext';
import FootMap from '../../components/FootMap';
import Colors from '../../constants/colors';

export default function DashboardScreen() {
  const router = useRouter();
  const { footData, isDarkMode, calculateRiskScore } = useSensor();
  const { healthIndex, updateHealthIndex, medicalRecord } = useHealth();
  const { todayTasks, toggleTask, completionRate } = useTodo();
  const { completionProgress, recommendations } = useRoutine();
  const { user } = useAuth();
  const [refreshing, setRefreshing] = React.useState(false);
  const colors = isDarkMode ? Colors.dark : Colors.light;
  const insets = useSafeAreaInsets();

  const topTasks = todayTasks.slice(0, 3);
  const topRecommendation = recommendations[0];

  useEffect(() => {
    const riskScore = calculateRiskScore();
    const maxPressure = Math.max(
      ...Object.values(footData.left).map(r => r.pressure),
      ...Object.values(footData.right).map(r => r.pressure)
    );
    const maxTemp = Math.max(
      ...Object.values(footData.left).map(r => r.temperature),
      ...Object.values(footData.right).map(r => r.temperature)
    );
    
    const pressureScore = (maxPressure / 100) * 25;
    const tempScore = maxTemp > 36 ? ((maxTemp - 36) / 2) * 25 : 0;
    
    updateHealthIndex(pressureScore, tempScore, completionRate);
  }, [footData, completionRate, calculateRiskScore, updateHealthIndex]);

  const onRefresh = React.useCallback(() => {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 1000);
  }, []);

  const getHealthLevelColor = (level: string) => {
    switch (level) {
      case 'green':
        return colors.success;
      case 'amber':
        return colors.warning;
      case 'red':
        return colors.danger;
      default:
        return colors.textTertiary;
    }
  };

  const getHealthLevelText = (level: string) => {
    switch (level) {
      case 'green':
        return 'Good Health';
      case 'amber':
        return 'Moderate Risk';
      case 'red':
        return 'High Risk';
      default:
        return 'Unknown';
    }
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background, paddingTop: Platform.OS === 'web' ? insets.top : 0 }]}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={colors.primary}
          />
        }
      >
        <View style={styles.header}>
          <View>
            <Text style={[styles.greeting, { color: colors.text }]}>
              Welcome back, {user?.name?.split(' ')[0] || 'there'}
            </Text>
            <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
              {medicalRecord.diabetesType} • {medicalRecord.neuropathyStatus} Neuropathy
            </Text>
          </View>
        </View>

        <View style={[styles.healthIndexCard, { backgroundColor: colors.surface }]}>
          <View style={styles.healthIndexHeader}>
            <Heart size={20} color={getHealthLevelColor(healthIndex.level)} />
            <Text style={[styles.healthIndexTitle, { color: colors.text }]}>
              Personal Health Index
            </Text>
          </View>
          
          <View style={styles.healthIndexBody}>
            <View style={styles.healthIndexScore}>
              <Text style={[styles.healthIndexValue, { color: getHealthLevelColor(healthIndex.level) }]}>
                {healthIndex.score.toFixed(0)}
              </Text>
              <Text style={[styles.healthIndexLevel, { color: getHealthLevelColor(healthIndex.level) }]}>
                {getHealthLevelText(healthIndex.level)}
              </Text>
            </View>
            
            <View style={styles.healthIndexFactors}>
              <View style={styles.factorRow}>
                <Text style={[styles.factorLabel, { color: colors.textSecondary }]}>Foot Pressure</Text>
                <View style={styles.factorBar}>
                  <View
                    style={[
                      styles.factorFill,
                      {
                        backgroundColor: colors.primary,
                        width: `${healthIndex.factors.footPressure}%`,
                      },
                    ]}
                  />
                </View>
              </View>
              <View style={styles.factorRow}>
                <Text style={[styles.factorLabel, { color: colors.textSecondary }]}>Temperature</Text>
                <View style={styles.factorBar}>
                  <View
                    style={[
                      styles.factorFill,
                      {
                        backgroundColor: colors.warning,
                        width: `${healthIndex.factors.temperature}%`,
                      },
                    ]}
                  />
                </View>
              </View>
              <View style={styles.factorRow}>
                <Text style={[styles.factorLabel, { color: colors.textSecondary }]}>Compliance</Text>
                <View style={styles.factorBar}>
                  <View
                    style={[
                      styles.factorFill,
                      {
                        backgroundColor: colors.success,
                        width: `${healthIndex.factors.compliance}%`,
                      },
                    ]}
                  />
                </View>
              </View>
            </View>
          </View>
        </View>

        <View style={[styles.quickActionsCard, { backgroundColor: colors.surface }]}>
          <TouchableOpacity
            style={[styles.quickAction, { borderRightWidth: 1, borderRightColor: colors.border }]}
            onPress={() => router.push('/(tabs)/chatbot')}
          >
            <View style={[styles.quickActionIcon, { backgroundColor: colors.primaryLight + '20' }]}>
              <MessageCircle size={24} color={colors.primary} />
            </View>
            <Text style={[styles.quickActionLabel, { color: colors.text }]}>Ask StepMate</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.quickAction}
            onPress={() => router.push('/(tabs)/routine')}
          >
            <View style={[styles.quickActionIcon, { backgroundColor: colors.success + '20' }]}>
              <Activity size={24} color={colors.success} />
            </View>
            <Text style={[styles.quickActionLabel, { color: colors.text }]}>View Routine</Text>
          </TouchableOpacity>
        </View>

        <View style={[styles.card, { backgroundColor: colors.surface }]}>
          <View style={styles.cardHeader}>
            <View style={styles.cardTitleRow}>
              <CheckCircle2 size={20} color={colors.primary} />
              <Text style={[styles.cardTitle, { color: colors.text }]}>
                Today&apos;s Tasks
              </Text>
            </View>
            <TouchableOpacity onPress={() => router.push('/(tabs)/routine')}>
              <ChevronRight size={20} color={colors.textTertiary} />
            </TouchableOpacity>
          </View>
          
          <View style={styles.progressRow}>
            <View style={[styles.progressBar, { backgroundColor: colors.surfaceElevated }]}>
              <View
                style={[
                  styles.progressFill,
                  {
                    backgroundColor: colors.primary,
                    width: `${completionRate}%`,
                  },
                ]}
              />
            </View>
            <Text style={[styles.progressText, { color: colors.text }]}>
              {completionRate}%
            </Text>
          </View>

          <View style={styles.tasksList}>
            {topTasks.map((task) => (
              <TouchableOpacity
                key={task.id}
                style={styles.taskItem}
                onPress={() => toggleTask(task.id)}
              >
                <View style={styles.taskCheckbox}>
                  {task.completed ? (
                    <CheckCircle2 size={20} color={colors.success} />
                  ) : (
                    <Circle size={20} color={colors.textTertiary} />
                  )}
                </View>
                <View style={styles.taskContent}>
                  <Text
                    style={[
                      styles.taskTitle,
                      { color: task.completed ? colors.textSecondary : colors.text },
                      task.completed && styles.taskCompleted,
                    ]}
                  >
                    {task.title}
                  </Text>
                  {task.dueTime && (
                    <View style={styles.taskTime}>
                      <Clock size={12} color={colors.textTertiary} />
                      <Text style={[styles.taskTimeText, { color: colors.textTertiary }]}>
                        {task.dueTime}
                      </Text>
                    </View>
                  )}
                </View>
              </TouchableOpacity>
            ))}
          </View>

          {todayTasks.length > 3 && (
            <TouchableOpacity
              style={styles.viewAllButton}
              onPress={() => router.push('/(tabs)/routine')}
            >
              <Text style={[styles.viewAllText, { color: colors.primary }]}>
                View all {todayTasks.length} tasks
              </Text>
              <ChevronRight size={16} color={colors.primary} />
            </TouchableOpacity>
          )}
        </View>

        {topRecommendation && (
          <View style={[styles.card, { backgroundColor: colors.surface }]}>
            <View style={styles.cardHeader}>
              <View style={styles.cardTitleRow}>
                <Sparkles size={20} color={colors.warning} />
                <Text style={[styles.cardTitle, { color: colors.text }]}>
                  Featured Recommendation
                </Text>
              </View>
              <View
                style={[
                  styles.priorityBadge,
                  {
                    backgroundColor:
                      topRecommendation.priority === 'high'
                        ? colors.danger
                        : topRecommendation.priority === 'medium'
                        ? colors.warning
                        : colors.success,
                  },
                ]}
              >
                <Text style={styles.priorityText}>
                  {topRecommendation.priority.toUpperCase()}
                </Text>
              </View>
            </View>
            <Text style={[styles.recTitle, { color: colors.text }]}>
              {topRecommendation.title}
            </Text>
            <Text style={[styles.recDescription, { color: colors.textSecondary }]}>
              {topRecommendation.description}
            </Text>
            <TouchableOpacity
              style={[styles.recButton, { backgroundColor: colors.primary }]}
              onPress={() => router.push('/(tabs)/routine')}
            >
              <Text style={styles.recButtonText}>View All Recommendations</Text>
            </TouchableOpacity>
          </View>
        )}

        <View style={[styles.card, { backgroundColor: colors.surface }]}>
          <View style={styles.cardHeader}>
            <View style={styles.cardTitleRow}>
              <TrendingUp size={20} color={colors.primary} />
              <Text style={[styles.cardTitle, { color: colors.text }]}>
                Routine Progress
              </Text>
            </View>
            <Text style={[styles.progressText, { color: colors.primary }]}>
              {completionProgress}%
            </Text>
          </View>
          <View style={[styles.progressBar, { backgroundColor: colors.surfaceElevated }]}>
            <View
              style={[
                styles.progressFill,
                {
                  backgroundColor: colors.primary,
                  width: `${completionProgress}%`,
                },
              ]}
            />
          </View>
          <TouchableOpacity
            style={styles.viewRoutineButton}
            onPress={() => router.push('/(tabs)/routine')}
          >
            <Text style={[styles.viewRoutineText, { color: colors.textSecondary }]}>
              Check your daily routine
            </Text>
            <ChevronRight size={16} color={colors.textTertiary} />
          </TouchableOpacity>
        </View>

        <View style={[styles.card, { backgroundColor: colors.surface }]}>
          <Text style={[styles.cardTitle, { color: colors.text, marginBottom: 20 }]}>
            Live Foot Pressure Map
          </Text>
          
          <View style={styles.footMapsContainer}>
            <FootMap
              footData={footData}
              isDarkMode={isDarkMode}
              foot="left"
            />
            <FootMap
              footData={footData}
              isDarkMode={isDarkMode}
              foot="right"
            />
          </View>

          <TouchableOpacity
            style={styles.viewTrendsButton}
            onPress={() => router.push('/(tabs)/trends')}
          >
            <TrendingUp size={16} color={colors.primary} />
            <Text style={[styles.viewTrendsText, { color: colors.primary }]}>
              View Pressure Trends
            </Text>
          </TouchableOpacity>
        </View>

        <View style={{ height: 32 }} />
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
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'web' ? 20 : 8,
    paddingBottom: 20,
  },
  greeting: {
    fontSize: 28,
    fontWeight: '700' as const,
  },
  subtitle: {
    fontSize: 13,
    marginTop: 4,
  },
  healthIndexCard: {
    marginHorizontal: 20,
    marginBottom: 16,
    padding: 20,
    borderRadius: 20,
  },
  healthIndexHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 16,
  },
  healthIndexTitle: {
    fontSize: 16,
    fontWeight: '600' as const,
  },
  healthIndexBody: {
    flexDirection: 'row',
    gap: 20,
  },
  healthIndexScore: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingRight: 20,
    borderRightWidth: 1,
    borderRightColor: 'rgba(255, 255, 255, 0.1)',
  },
  healthIndexValue: {
    fontSize: 48,
    fontWeight: '700' as const,
  },
  healthIndexLevel: {
    fontSize: 13,
    fontWeight: '600' as const,
    marginTop: 4,
  },
  healthIndexFactors: {
    flex: 1,
    gap: 12,
    justifyContent: 'center',
  },
  factorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  factorLabel: {
    fontSize: 12,
    width: 80,
  },
  factorBar: {
    flex: 1,
    height: 6,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 3,
    overflow: 'hidden',
  },
  factorFill: {
    height: '100%',
    borderRadius: 3,
  },
  quickActionsCard: {
    marginHorizontal: 20,
    marginBottom: 16,
    borderRadius: 20,
    flexDirection: 'row',
    overflow: 'hidden',
  },
  quickAction: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 20,
    gap: 8,
  },
  quickActionIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
  },
  quickActionLabel: {
    fontSize: 13,
    fontWeight: '600' as const,
  },
  card: {
    marginHorizontal: 20,
    marginBottom: 16,
    padding: 20,
    borderRadius: 20,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  cardTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '700' as const,
  },
  progressRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 16,
  },
  progressBar: {
    flex: 1,
    height: 8,
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  progressText: {
    fontSize: 16,
    fontWeight: '700' as const,
    minWidth: 45,
  },
  tasksList: {
    gap: 12,
  },
  taskItem: {
    flexDirection: 'row',
    gap: 12,
    alignItems: 'flex-start',
  },
  taskCheckbox: {
    paddingTop: 2,
  },
  taskContent: {
    flex: 1,
    gap: 4,
  },
  taskTitle: {
    fontSize: 15,
    fontWeight: '500' as const,
  },
  taskCompleted: {
    textDecorationLine: 'line-through',
  },
  taskTime: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  taskTimeText: {
    fontSize: 12,
  },
  viewAllButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 16,
    paddingVertical: 12,
    gap: 4,
  },
  viewAllText: {
    fontSize: 14,
    fontWeight: '600' as const,
  },
  priorityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  priorityText: {
    fontSize: 10,
    fontWeight: '700' as const,
    color: '#FFFFFF',
  },
  recTitle: {
    fontSize: 16,
    fontWeight: '600' as const,
    marginBottom: 8,
  },
  recDescription: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 16,
  },
  recButton: {
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 12,
    alignItems: 'center',
  },
  recButtonText: {
    fontSize: 14,
    fontWeight: '600' as const,
    color: '#FFFFFF',
  },
  viewRoutineButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.05)',
  },
  viewRoutineText: {
    fontSize: 13,
  },
  footMapsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    gap: 20,
    marginBottom: 16,
  },
  viewTrendsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.05)',
  },
  viewTrendsText: {
    fontSize: 14,
    fontWeight: '600' as const,
  },
});

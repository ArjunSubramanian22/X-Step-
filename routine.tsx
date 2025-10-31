import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import {
  CheckCircle2,
  Circle,
  Clock,
  TrendingUp,
  Plus,
  ChevronDown,
  ChevronUp,
  Sparkles,
} from 'lucide-react-native';
import { useRoutine } from '../../contexts/RoutineContext';
import { useTodo } from '../../contexts/TodoContext';
import { useSensor } from '../../contexts/SensorContext';
import Colors from '../../constants/colors';

export default function RoutineScreen() {
  const { routine, completionProgress, toggleRoutineStep, recommendations } = useRoutine();
  const { objectives, addTask } = useTodo();
  const { isDarkMode } = useSensor();
  const [expandedSection, setExpandedSection] = useState<'morning' | 'midday' | 'evening' | null>('morning');
  const colors = isDarkMode ? Colors.dark : Colors.light;
  const insets = useSafeAreaInsets();

  const handleAddToTodo = (rec: any) => {
    addTask({
      title: rec.title,
      description: rec.description,
      completed: false,
      type: rec.category === 'footwear' ? 'foot_care' : rec.category === 'rest' ? 'activity' : 'health_tracking',
      urgency: rec.priority,
      generatedBy: 'stepmate',
    });
  };

  const toggleSection = (section: 'morning' | 'midday' | 'evening') => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  const renderRoutineSection = (
    title: string,
    period: 'morning' | 'midday' | 'evening',
    icon: React.ReactNode
  ) => {
    const steps = routine[period];
    const completed = steps.filter(s => s.completed).length;
    const isExpanded = expandedSection === period;

    return (
      <View style={[styles.section, { backgroundColor: colors.surface }]}>
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => toggleSection(period)}
        >
          <View style={styles.sectionTitleRow}>
            {icon}
            <View style={styles.sectionTitleContent}>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>{title}</Text>
              <Text style={[styles.sectionSubtitle, { color: colors.textSecondary }]}>
                {completed}/{steps.length} completed
              </Text>
            </View>
          </View>
          {isExpanded ? (
            <ChevronUp size={20} color={colors.textSecondary} />
          ) : (
            <ChevronDown size={20} color={colors.textSecondary} />
          )}
        </TouchableOpacity>

        {isExpanded && (
          <View style={styles.sectionContent}>
            {steps.map((step) => (
              <TouchableOpacity
                key={step.id}
                style={styles.stepItem}
                onPress={() => toggleRoutineStep(step.id)}
              >
                <View style={styles.stepCheckbox}>
                  {step.completed ? (
                    <CheckCircle2 size={24} color={colors.success} />
                  ) : (
                    <Circle size={24} color={colors.textTertiary} />
                  )}
                </View>
                <View style={styles.stepContent}>
                  <View style={styles.stepHeader}>
                    <Text
                      style={[
                        styles.stepTitle,
                        { color: step.completed ? colors.textSecondary : colors.text },
                        step.completed && styles.stepCompleted,
                      ]}
                    >
                      {step.title}
                    </Text>
                    <View style={styles.stepTime}>
                      <Clock size={14} color={colors.textTertiary} />
                      <Text style={[styles.stepTimeText, { color: colors.textTertiary }]}>
                        {step.time}
                      </Text>
                    </View>
                  </View>
                  <Text style={[styles.stepDescription, { color: colors.textSecondary }]}>
                    {step.description}
                  </Text>
                </View>
              </TouchableOpacity>
            ))}
          </View>
        )}
      </View>
    );
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background, paddingTop: Platform.OS === 'web' ? insets.top : 0 }]}>
      <ScrollView style={styles.scrollView}>
        <View style={styles.header}>
          <Text style={[styles.title, { color: colors.text }]}>Daily Routine</Text>
          <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
            Stay on track with your foot care schedule
          </Text>
        </View>

        <View style={[styles.progressCard, { backgroundColor: colors.surface }]}>
          <View style={styles.progressHeader}>
            <TrendingUp size={20} color={colors.primary} />
            <Text style={[styles.progressTitle, { color: colors.text }]}>
              Today's Progress
            </Text>
          </View>
          <View style={styles.progressBarContainer}>
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
            <Text style={[styles.progressText, { color: colors.text }]}>
              {completionProgress}%
            </Text>
          </View>
        </View>

        {renderRoutineSection('Morning Routine', 'morning', <Clock size={20} color={colors.warning} />)}
        {renderRoutineSection('Midday Routine', 'midday', <Clock size={20} color={colors.primary} />)}
        {renderRoutineSection('Evening Routine', 'evening', <Clock size={20} color={colors.primaryDark} />)}

        <View style={[styles.section, { backgroundColor: colors.surface }]}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionTitleRow}>
              <TrendingUp size={20} color={colors.primary} />
              <Text style={[styles.sectionTitle, { color: colors.text }]}>
                Weekly Objectives
              </Text>
            </View>
          </View>
          <View style={styles.sectionContent}>
            {objectives.map((objective) => (
              <View key={objective.id} style={styles.objectiveItem}>
                <View style={styles.objectiveHeader}>
                  <Text style={[styles.objectiveTitle, { color: colors.text }]}>
                    {objective.title}
                  </Text>
                  <Text style={[styles.objectiveProgress, { color: colors.primary }]}>
                    {objective.completedDays}/{objective.targetDays} days
                  </Text>
                </View>
                <Text style={[styles.objectiveDescription, { color: colors.textSecondary }]}>
                  {objective.description.replace("'", "&apos;")}
                </Text>
                <View style={styles.objectiveBar}>
                  <View style={[styles.progressBar, { backgroundColor: colors.surfaceElevated }]}>
                    <View
                      style={[
                        styles.progressFill,
                        {
                          backgroundColor: colors.success,
                          width: `${(objective.completedDays / objective.targetDays) * 100}%`,
                        },
                      ]}
                    />
                  </View>
                </View>
                <View style={styles.objectiveMetric}>
                  <Text style={[styles.metricLabel, { color: colors.textTertiary }]}>
                    {objective.metric}:
                  </Text>
                  <Text style={[styles.metricValue, { color: colors.text }]}>
                    {objective.currentValue} / {objective.targetValue}
                  </Text>
                </View>
              </View>
            ))}
          </View>
        </View>

        <View style={[styles.section, { backgroundColor: colors.surface }]}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionTitleRow}>
              <Sparkles size={20} color={colors.warning} />
              <Text style={[styles.sectionTitle, { color: colors.text }]}>
                Lifestyle Recommendations
              </Text>
            </View>
          </View>
          <View style={styles.sectionContent}>
            {recommendations.map((rec) => (
              <View key={rec.id} style={[styles.recommendationCard, { borderLeftColor: rec.priority === 'high' ? colors.danger : rec.priority === 'medium' ? colors.warning : colors.success }]}>
                <View style={styles.recHeader}>
                  <Text style={[styles.recTitle, { color: colors.text }]}>{rec.title}</Text>
                  <View style={[styles.priorityBadge, { backgroundColor: rec.priority === 'high' ? colors.danger : rec.priority === 'medium' ? colors.warning : colors.success }]}>
                    <Text style={styles.priorityText}>
                      {rec.priority.toUpperCase()}
                    </Text>
                  </View>
                </View>
                <Text style={[styles.recDescription, { color: colors.textSecondary }]}>
                  {rec.description}
                </Text>
                <View style={styles.recFooter}>
                  <Text style={[styles.recTrigger, { color: colors.textTertiary }]}>
                    Triggered by: {rec.triggerCondition}
                  </Text>
                  {rec.canConvertToTodo && (
                    <TouchableOpacity 
                      style={[styles.addButton, { backgroundColor: colors.primary }]}
                      onPress={() => handleAddToTodo(rec)}
                    >
                      <Plus size={14} color="#FFFFFF" />
                      <Text style={styles.addButtonText}>Add to To-Do</Text>
                    </TouchableOpacity>
                  )}
                </View>
              </View>
            ))}
          </View>
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
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'web' ? 20 : 8,
    paddingBottom: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: '700' as const,
  },
  subtitle: {
    fontSize: 14,
    marginTop: 4,
  },
  progressCard: {
    marginHorizontal: 20,
    marginBottom: 16,
    padding: 20,
    borderRadius: 16,
  },
  progressHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 16,
  },
  progressTitle: {
    fontSize: 16,
    fontWeight: '600' as const,
  },
  progressBarContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
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
  section: {
    marginHorizontal: 20,
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 20,
  },
  sectionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  sectionTitleContent: {
    flex: 1,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700' as const,
  },
  sectionSubtitle: {
    fontSize: 13,
    marginTop: 2,
  },
  sectionContent: {
    paddingHorizontal: 20,
    paddingBottom: 20,
    gap: 12,
  },
  stepItem: {
    flexDirection: 'row',
    gap: 12,
    paddingVertical: 12,
  },
  stepCheckbox: {
    paddingTop: 2,
  },
  stepContent: {
    flex: 1,
    gap: 6,
  },
  stepHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  stepTitle: {
    fontSize: 15,
    fontWeight: '600' as const,
    flex: 1,
  },
  stepCompleted: {
    textDecorationLine: 'line-through',
  },
  stepTime: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  stepTimeText: {
    fontSize: 13,
  },
  stepDescription: {
    fontSize: 13,
    lineHeight: 18,
  },
  objectiveItem: {
    paddingVertical: 12,
    gap: 8,
  },
  objectiveHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  objectiveTitle: {
    fontSize: 15,
    fontWeight: '600' as const,
    flex: 1,
  },
  objectiveProgress: {
    fontSize: 14,
    fontWeight: '700' as const,
  },
  objectiveDescription: {
    fontSize: 13,
    lineHeight: 18,
  },
  objectiveBar: {
    marginTop: 4,
  },
  objectiveMetric: {
    flexDirection: 'row',
    gap: 6,
    marginTop: 4,
  },
  metricLabel: {
    fontSize: 12,
  },
  metricValue: {
    fontSize: 12,
    fontWeight: '600' as const,
  },
  recommendationCard: {
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderLeftWidth: 4,
    gap: 10,
  },
  recHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  recTitle: {
    fontSize: 15,
    fontWeight: '600' as const,
    flex: 1,
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
  recDescription: {
    fontSize: 13,
    lineHeight: 18,
  },
  recFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 4,
  },
  recTrigger: {
    fontSize: 11,
    flex: 1,
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  addButtonText: {
    fontSize: 12,
    fontWeight: '600' as const,
    color: '#FFFFFF',
  },
});

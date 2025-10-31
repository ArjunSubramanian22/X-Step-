import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { TrendingUp, Calendar } from 'lucide-react-native';
import { useSensor } from '../../contexts/SensorContext';
import Colors from '../../constants/colors';

const { width } = Dimensions.get('window');
const CHART_WIDTH = width - 40;
const CHART_HEIGHT = 200;

export default function TrendsScreen() {
  const { history, isDarkMode } = useSensor();
  const [period, setPeriod] = useState<'7d' | '30d'>('7d');
  const colors = isDarkMode ? Colors.dark : Colors.light;

  const data = history.slice(0, period === '7d' ? 7 : 30).reverse();
  
  const maxScore = Math.max(...data.map(d => d.score), 100);
  const maxPressure = Math.max(...data.map(d => d.maxPressure), 100);

  const renderLineChart = (values: number[], max: number, color: string) => {
    if (values.length === 0) return null;
    
    const pointSpacing = CHART_WIDTH / (values.length - 1);
    const chartPadding = 20;

    return (
      <View style={[styles.chart, { height: CHART_HEIGHT }]}>
        <View style={styles.chartArea}>
          {values.map((value, index) => {
            const x = index * pointSpacing;
            const y = CHART_HEIGHT - chartPadding - ((value / max) * (CHART_HEIGHT - 2 * chartPadding));
            
            return (
              <View key={index}>
                {index < values.length - 1 && (
                  <View
                    style={[
                      styles.lineSegment,
                      {
                        position: 'absolute',
                        left: x,
                        top: y,
                        width: pointSpacing,
                        height: 3,
                        backgroundColor: color,
                        transform: [
                          {
                            rotate: `${Math.atan2(
                              CHART_HEIGHT - chartPadding - ((values[index + 1] / max) * (CHART_HEIGHT - 2 * chartPadding)) - y,
                              pointSpacing
                            )}rad`,
                          },
                        ],
                        transformOrigin: 'left center',
                      },
                    ]}
                  />
                )}
                <View
                  style={[
                    styles.dataPoint,
                    {
                      position: 'absolute',
                      left: x - 4,
                      top: y - 4,
                      backgroundColor: color,
                    },
                  ]}
                />
              </View>
            );
          })}
        </View>
        <View style={styles.xAxisLabels}>
          {values.map((_, index) => {
            if (index === 0 || index === values.length - 1 || index === Math.floor(values.length / 2)) {
              return (
                <Text
                  key={`label-${index}`}
                  style={[
                    styles.axisLabel,
                    { color: colors.textTertiary, left: index * pointSpacing - 20 },
                  ]}
                >
                  {new Date(Date.now() - (values.length - 1 - index) * 86400000)
                    .toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                </Text>
              );
            }
            return null;
          })}
        </View>
      </View>
    );
  };

  const generateMockData = () => {
    const days = period === '7d' ? 7 : 30;
    return Array.from({ length: days }, (_, i) => ({
      date: new Date(Date.now() - (days - 1 - i) * 86400000).toISOString().split('T')[0],
      score: 30 + Math.random() * 40,
      maxPressure: 50 + Math.random() * 30,
      maxTemperature: 33 + Math.random() * 3,
      alertCount: Math.floor(Math.random() * 3),
    }));
  };

  const displayData = data.length > 0 ? data : generateMockData();

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <ScrollView style={styles.scrollView}>
        <View style={styles.header}>
          <View style={styles.headerContent}>
            <TrendingUp size={24} color={colors.primary} />
            <Text style={[styles.title, { color: colors.text }]}>
              Analytics & Trends
            </Text>
          </View>
          
          <View style={styles.periodSelector}>
            <TouchableOpacity
              style={[
                styles.periodButton,
                period === '7d' && { backgroundColor: colors.primary },
                period !== '7d' && { backgroundColor: colors.surfaceElevated },
              ]}
              onPress={() => setPeriod('7d')}
            >
              <Text
                style={[
                  styles.periodText,
                  { color: period === '7d' ? '#FFFFFF' : colors.textSecondary },
                ]}
              >
                7 Days
              </Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[
                styles.periodButton,
                period === '30d' && { backgroundColor: colors.primary },
                period !== '30d' && { backgroundColor: colors.surfaceElevated },
              ]}
              onPress={() => setPeriod('30d')}
            >
              <Text
                style={[
                  styles.periodText,
                  { color: period === '30d' ? '#FFFFFF' : colors.textSecondary },
                ]}
              >
                30 Days
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        <View style={[styles.card, { backgroundColor: colors.surface }]}>
          <Text style={[styles.cardTitle, { color: colors.text }]}>
            Risk Score Trend
          </Text>
          {renderLineChart(
            displayData.map(d => d.score),
            maxScore,
            colors.primary
          )}
        </View>

        <View style={[styles.card, { backgroundColor: colors.surface }]}>
          <Text style={[styles.cardTitle, { color: colors.text }]}>
            Max Pressure Trend (kPa)
          </Text>
          {renderLineChart(
            displayData.map(d => d.maxPressure),
            maxPressure,
            colors.warning
          )}
        </View>

        <View style={[styles.summaryCard, { backgroundColor: colors.surface }]}>
          <View style={styles.summaryHeader}>
            <Calendar size={20} color={colors.primary} />
            <Text style={[styles.cardTitle, { color: colors.text }]}>
              Period Summary
            </Text>
          </View>
          
          <View style={styles.summaryGrid}>
            <View style={styles.summaryItem}>
              <Text style={[styles.summaryValue, { color: colors.text }]}>
                {(displayData.reduce((sum, d) => sum + d.score, 0) / displayData.length).toFixed(0)}
              </Text>
              <Text style={[styles.summaryLabel, { color: colors.textSecondary }]}>
                Avg Risk Score
              </Text>
            </View>
            
            <View style={styles.summaryItem}>
              <Text style={[styles.summaryValue, { color: colors.text }]}>
                {(displayData.reduce((sum, d) => sum + d.maxPressure, 0) / displayData.length).toFixed(0)}
              </Text>
              <Text style={[styles.summaryLabel, { color: colors.textSecondary }]}>
                Avg Max Pressure
              </Text>
            </View>
            
            <View style={styles.summaryItem}>
              <Text style={[styles.summaryValue, { color: colors.text }]}>
                {displayData.reduce((sum, d) => sum + d.alertCount, 0)}
              </Text>
              <Text style={[styles.summaryLabel, { color: colors.textSecondary }]}>
                Total Alerts
              </Text>
            </View>
            
            <View style={styles.summaryItem}>
              <Text style={[styles.summaryValue, { color: colors.text }]}>
                {Math.max(...displayData.map(d => d.score)).toFixed(0)}
              </Text>
              <Text style={[styles.summaryLabel, { color: colors.textSecondary }]}>
                Peak Risk Score
              </Text>
            </View>
          </View>
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
    padding: 20,
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: '700' as const,
  },
  periodSelector: {
    flexDirection: 'row',
    gap: 12,
  },
  periodButton: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
  },
  periodText: {
    fontSize: 14,
    fontWeight: '600' as const,
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
  cardTitle: {
    fontSize: 16,
    fontWeight: '700' as const,
    marginBottom: 16,
  },
  chart: {
    height: CHART_HEIGHT,
    position: 'relative',
  },
  chartArea: {
    flex: 1,
    position: 'relative',
  },
  lineSegment: {
    borderRadius: 2,
  },
  dataPoint: {
    width: 8,
    height: 8,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: '#FFFFFF',
  },
  xAxisLabels: {
    flexDirection: 'row',
    position: 'relative',
    marginTop: 8,
  },
  axisLabel: {
    fontSize: 10,
    position: 'absolute',
    width: 40,
    textAlign: 'center',
  },
  summaryCard: {
    marginHorizontal: 20,
    marginBottom: 32,
    padding: 20,
    borderRadius: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  summaryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 20,
  },
  summaryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 16,
  },
  summaryItem: {
    width: '47%',
    padding: 16,
    alignItems: 'center',
  },
  summaryValue: {
    fontSize: 32,
    fontWeight: '700' as const,
    marginBottom: 4,
  },
  summaryLabel: {
    fontSize: 12,
    textAlign: 'center',
  },
});

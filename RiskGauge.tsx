import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Circle } from 'react-native-svg';
import Colors from '../constants/colors';

interface RiskGaugeProps {
  score: number;
  isDarkMode: boolean;
}

export default function RiskGauge({ score, isDarkMode }: RiskGaugeProps) {
  const colors = isDarkMode ? Colors.dark : Colors.light;
  const size = 160;
  const strokeWidth = 16;
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const progress = (score / 100) * circumference;

  let riskColor = colors.success;
  let riskLabel = 'Low Risk';
  
  if (score >= 70) {
    riskColor = colors.danger;
    riskLabel = 'High Risk';
  } else if (score >= 40) {
    riskColor = colors.warning;
    riskLabel = 'Medium Risk';
  }

  return (
    <View style={styles.container}>
      <View style={styles.gaugeContainer}>
        <Svg width={size} height={size}>
          <Circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={colors.surfaceElevated}
            strokeWidth={strokeWidth}
            fill="none"
          />
          <Circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={riskColor}
            strokeWidth={strokeWidth}
            fill="none"
            strokeDasharray={`${circumference} ${circumference}`}
            strokeDashoffset={circumference - progress}
            strokeLinecap="round"
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
          />
        </Svg>
        
        <View style={styles.centerContent}>
          <Text style={[styles.scoreText, { color: colors.text }]}>
            {Math.round(score)}
          </Text>
          <Text style={[styles.riskLabel, { color: riskColor }]}>
            {riskLabel}
          </Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  gaugeContainer: {
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
  },
  centerContent: {
    position: 'absolute',
    alignItems: 'center',
    justifyContent: 'center',
  },
  scoreText: {
    fontSize: 48,
    fontWeight: '700' as const,
    lineHeight: 52,
  },
  riskLabel: {
    fontSize: 14,
    fontWeight: '600' as const,
    marginTop: 4,
  },
});

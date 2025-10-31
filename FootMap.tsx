import React from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import Svg, { Path, Circle } from 'react-native-svg';
import type { FootData, FootZone } from '../types/sensor';
import Colors from '../constants/colors';

interface FootMapProps {
  footData: FootData;
  isDarkMode: boolean;
  foot: 'left' | 'right';
  showValues?: boolean;
}

const { width } = Dimensions.get('window');
const FOOT_WIDTH = Math.min(width * 0.35, 140);
const FOOT_HEIGHT = FOOT_WIDTH * 2.2;

function getColorForValue(value: number, threshold: number, isDarkMode: boolean): string {
  const ratio = value / threshold;
  const colors = isDarkMode ? Colors.dark : Colors.light;
  
  if (ratio < 0.7) return colors.success;
  if (ratio < 0.9) return colors.warning;
  return colors.danger;
}

export default function FootMap({ footData, isDarkMode, foot, showValues = true }: FootMapProps) {
  const data = footData[foot];
  const colors = isDarkMode ? Colors.dark : Colors.light;
  
  const zones: { zone: FootZone; x: number; y: number; label: string }[] = [
    { zone: 'toes', x: FOOT_WIDTH / 2, y: FOOT_HEIGHT * 0.12, label: 'Toes' },
    { zone: 'ball', x: foot === 'left' ? FOOT_WIDTH * 0.65 : FOOT_WIDTH * 0.35, y: FOOT_HEIGHT * 0.35, label: 'Ball' },
    { zone: 'arch', x: FOOT_WIDTH / 2, y: FOOT_HEIGHT * 0.58, label: 'Arch' },
    { zone: 'heel', x: FOOT_WIDTH / 2, y: FOOT_HEIGHT * 0.85, label: 'Heel' },
  ];

  const pressurePoints = [
    { zone: 'heel', x: FOOT_WIDTH / 2, y: FOOT_HEIGHT * 0.85 },
    { zone: 'arch', x: FOOT_WIDTH / 2, y: FOOT_HEIGHT * 0.58 },
    { zone: 'ball', x: foot === 'left' ? FOOT_WIDTH * 0.65 : FOOT_WIDTH * 0.35, y: FOOT_HEIGHT * 0.35 },
    { zone: 'toes', x: foot === 'left' ? FOOT_WIDTH * 0.35 : FOOT_WIDTH * 0.65, y: FOOT_HEIGHT * 0.35 },
  ];

  const footPath = foot === 'left'
    ? `M ${FOOT_WIDTH * 0.5},${FOOT_HEIGHT * 0.02}
       Q ${FOOT_WIDTH * 0.38},${FOOT_HEIGHT * 0.04} ${FOOT_WIDTH * 0.32},${FOOT_HEIGHT * 0.08}
       Q ${FOOT_WIDTH * 0.28},${FOOT_HEIGHT * 0.12} ${FOOT_WIDTH * 0.28},${FOOT_HEIGHT * 0.18}
       L ${FOOT_WIDTH * 0.32},${FOOT_HEIGHT * 0.28}
       Q ${FOOT_WIDTH * 0.68},${FOOT_HEIGHT * 0.30} ${FOOT_WIDTH * 0.72},${FOOT_HEIGHT * 0.28}
       L ${FOOT_WIDTH * 0.72},${FOOT_HEIGHT * 0.18}
       Q ${FOOT_WIDTH * 0.72},${FOOT_HEIGHT * 0.12} ${FOOT_WIDTH * 0.68},${FOOT_HEIGHT * 0.08}
       Q ${FOOT_WIDTH * 0.62},${FOOT_HEIGHT * 0.04} ${FOOT_WIDTH * 0.5},${FOOT_HEIGHT * 0.02}
       Z
       M ${FOOT_WIDTH * 0.32},${FOOT_HEIGHT * 0.30}
       Q ${FOOT_WIDTH * 0.28},${FOOT_HEIGHT * 0.40} ${FOOT_WIDTH * 0.28},${FOOT_HEIGHT * 0.52}
       Q ${FOOT_WIDTH * 0.30},${FOOT_HEIGHT * 0.68} ${FOOT_WIDTH * 0.38},${FOOT_HEIGHT * 0.76}
       Q ${FOOT_WIDTH * 0.42},${FOOT_HEIGHT * 0.80} ${FOOT_WIDTH * 0.46},${FOOT_HEIGHT * 0.82}
       L ${FOOT_WIDTH * 0.46},${FOOT_HEIGHT * 0.93}
       Q ${FOOT_WIDTH * 0.48},${FOOT_HEIGHT * 0.98} ${FOOT_WIDTH * 0.5},${FOOT_HEIGHT * 0.98}
       Q ${FOOT_WIDTH * 0.52},${FOOT_HEIGHT * 0.98} ${FOOT_WIDTH * 0.54},${FOOT_HEIGHT * 0.93}
       L ${FOOT_WIDTH * 0.54},${FOOT_HEIGHT * 0.82}
       Q ${FOOT_WIDTH * 0.56},${FOOT_HEIGHT * 0.78} ${FOOT_WIDTH * 0.59},${FOOT_HEIGHT * 0.75}
       Q ${FOOT_WIDTH * 0.65},${FOOT_HEIGHT * 0.68} ${FOOT_WIDTH * 0.68},${FOOT_HEIGHT * 0.56}
       Q ${FOOT_WIDTH * 0.70},${FOOT_HEIGHT * 0.44} ${FOOT_WIDTH * 0.70},${FOOT_HEIGHT * 0.34}
       L ${FOOT_WIDTH * 0.72},${FOOT_HEIGHT * 0.28}
       Q ${FOOT_WIDTH * 0.68},${FOOT_HEIGHT * 0.30} ${FOOT_WIDTH * 0.32},${FOOT_HEIGHT * 0.30}
       Z`
    : `M ${FOOT_WIDTH * 0.5},${FOOT_HEIGHT * 0.02}
       Q ${FOOT_WIDTH * 0.62},${FOOT_HEIGHT * 0.04} ${FOOT_WIDTH * 0.68},${FOOT_HEIGHT * 0.08}
       Q ${FOOT_WIDTH * 0.72},${FOOT_HEIGHT * 0.12} ${FOOT_WIDTH * 0.72},${FOOT_HEIGHT * 0.18}
       L ${FOOT_WIDTH * 0.68},${FOOT_HEIGHT * 0.28}
       Q ${FOOT_WIDTH * 0.32},${FOOT_HEIGHT * 0.30} ${FOOT_WIDTH * 0.28},${FOOT_HEIGHT * 0.28}
       L ${FOOT_WIDTH * 0.28},${FOOT_HEIGHT * 0.18}
       Q ${FOOT_WIDTH * 0.28},${FOOT_HEIGHT * 0.12} ${FOOT_WIDTH * 0.32},${FOOT_HEIGHT * 0.08}
       Q ${FOOT_WIDTH * 0.38},${FOOT_HEIGHT * 0.04} ${FOOT_WIDTH * 0.5},${FOOT_HEIGHT * 0.02}
       Z
       M ${FOOT_WIDTH * 0.68},${FOOT_HEIGHT * 0.30}
       Q ${FOOT_WIDTH * 0.72},${FOOT_HEIGHT * 0.40} ${FOOT_WIDTH * 0.72},${FOOT_HEIGHT * 0.52}
       Q ${FOOT_WIDTH * 0.70},${FOOT_HEIGHT * 0.68} ${FOOT_WIDTH * 0.62},${FOOT_HEIGHT * 0.76}
       Q ${FOOT_WIDTH * 0.58},${FOOT_HEIGHT * 0.80} ${FOOT_WIDTH * 0.54},${FOOT_HEIGHT * 0.82}
       L ${FOOT_WIDTH * 0.54},${FOOT_HEIGHT * 0.93}
       Q ${FOOT_WIDTH * 0.52},${FOOT_HEIGHT * 0.98} ${FOOT_WIDTH * 0.5},${FOOT_HEIGHT * 0.98}
       Q ${FOOT_WIDTH * 0.48},${FOOT_HEIGHT * 0.98} ${FOOT_WIDTH * 0.46},${FOOT_HEIGHT * 0.93}
       L ${FOOT_WIDTH * 0.46},${FOOT_HEIGHT * 0.82}
       Q ${FOOT_WIDTH * 0.44},${FOOT_HEIGHT * 0.78} ${FOOT_WIDTH * 0.41},${FOOT_HEIGHT * 0.75}
       Q ${FOOT_WIDTH * 0.35},${FOOT_HEIGHT * 0.68} ${FOOT_WIDTH * 0.32},${FOOT_HEIGHT * 0.56}
       Q ${FOOT_WIDTH * 0.30},${FOOT_HEIGHT * 0.44} ${FOOT_WIDTH * 0.30},${FOOT_HEIGHT * 0.34}
       L ${FOOT_WIDTH * 0.28},${FOOT_HEIGHT * 0.28}
       Q ${FOOT_WIDTH * 0.32},${FOOT_HEIGHT * 0.30} ${FOOT_WIDTH * 0.68},${FOOT_HEIGHT * 0.30}
       Z`;

  return (
    <View style={styles.container}>
      <Text style={[styles.footLabel, { color: colors.text }]}>
        {foot.charAt(0).toUpperCase() + foot.slice(1)} Foot
      </Text>
      
      <View style={styles.footContainer}>
        <Svg width={FOOT_WIDTH} height={FOOT_HEIGHT} viewBox={`0 0 ${FOOT_WIDTH} ${FOOT_HEIGHT}`}>
          <Path
            d={footPath}
            fill={colors.surface}
            stroke={colors.border}
            strokeWidth={2}
          />
          
          {pressurePoints.map(({ zone, x, y }) => {
            const reading = data[zone as FootZone];
            const pressureColor = getColorForValue(reading.pressure, 75, isDarkMode);
            const radius = 14;
            
            return (
              <Circle
                key={`${zone}-${x}-${y}`}
                cx={x}
                cy={y}
                r={radius}
                fill={pressureColor}
                opacity={0.85}
                stroke="#FFFFFF"
                strokeWidth={2}
              />
            );
          })}
        </Svg>
        
        {showValues && zones.map(({ zone, x, y, label }) => {
          const reading = data[zone];
          return (
            <View
              key={`value-${zone}`}
              style={[
                styles.valueContainer,
                {
                  position: 'absolute',
                  left: x - 30,
                  top: y - 30,
                },
              ]}
            >
              <Text style={[styles.zoneLabel, { color: colors.textSecondary }]}>
                {label}
              </Text>
              <Text style={[styles.pressureValue, { color: colors.text }]}>
                {reading.pressure.toFixed(0)}
              </Text>
              <Text style={[styles.unit, { color: colors.textTertiary }]}>kPa</Text>
              <Text style={[styles.tempValue, { color: colors.textSecondary }]}>
                {reading.temperature.toFixed(1)}°C
              </Text>
            </View>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
  },
  footLabel: {
    fontSize: 14,
    fontWeight: '600' as const,
    marginBottom: 12,
    textTransform: 'capitalize' as const,
  },
  footContainer: {
    position: 'relative',
    width: FOOT_WIDTH,
    height: FOOT_HEIGHT,
  },
  valueContainer: {
    width: 60,
    alignItems: 'center',
    justifyContent: 'center',
  },
  zoneLabel: {
    fontSize: 9,
    fontWeight: '500' as const,
    marginBottom: 2,
  },
  pressureValue: {
    fontSize: 14,
    fontWeight: '700' as const,
  },
  unit: {
    fontSize: 8,
    marginTop: -2,
  },
  tempValue: {
    fontSize: 10,
    marginTop: 2,
  },
});

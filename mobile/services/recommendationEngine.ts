import type { DailyScore } from '@/types/sensor';
import type { LifestyleRecommendation } from '@/types/routine';

export function generateRecommendations(
  history: DailyScore[],
  activeAlertCount: number,
  completionRate: number,
  gaitPattern?: string
): LifestyleRecommendation[] {
  const recommendations: LifestyleRecommendation[] = [];
  const now = Date.now();

  if (gaitPattern && gaitPattern.includes('forefoot')) {
    recommendations.push({
      id: 'rec-forefoot',
      category: 'footwear',
      title: 'Offload the forefoot',
      description:
        'Gait analysis shows metatarsal overload. Rotate extra-depth diabetic shoes and inspect the ball of the foot tonight.',
      priority: 'high',
      triggerCondition: gaitPattern,
      canConvertToTodo: true,
      timestamp: now,
    });
  }

  if (gaitPattern && gaitPattern.includes('heel')) {
    recommendations.push({
      id: 'rec-heel',
      category: 'rest',
      title: 'Unload the heel',
      description: 'Heel pressure is elevated. Elevate feet 15 minutes, 2–3 times today, and check for non-blanching redness.',
      priority: 'high',
      triggerCondition: gaitPattern,
      canConvertToTodo: true,
      timestamp: now,
    });
  }

  const recentHighPressureDays = history
    .slice(0, 3)
    .filter((day) => day.maxPressure > 75).length;

  if (recentHighPressureDays >= 2) {
    recommendations.push({
      id: 'rec-pressure',
      category: 'footwear',
      title: 'Rotate Your Shoes',
      description:
        'Wearing the same shoes daily increases pressure on specific foot areas. Alternate between 2-3 pairs of well-fitted diabetic shoes.',
      priority: 'medium',
      triggerCondition: 'High pressure detected for 2+ consecutive days',
      canConvertToTodo: true,
      timestamp: now,
    });
  }

  const recentTempSpike = history
    .slice(0, 2)
    .some((day) => day.maxTemperature > 36.5);

  if (recentTempSpike || activeAlertCount > 0) {
    recommendations.push({
      id: 'rec-temp',
      category: 'rest',
      title: 'Elevate Your Feet',
      description:
        'When sitting, elevate feet to reduce swelling and improve circulation. Do this 2-3 times daily for 15 minutes.',
      priority: 'high',
      triggerCondition: 'Temperature spike or active alert detected',
      canConvertToTodo: true,
      timestamp: now,
    });
  }

  if (completionRate < 50) {
    recommendations.push({
      id: 'rec-compliance',
      category: 'hydration',
      title: 'Increase Water Intake',
      description:
        'Aim for 8 glasses of water daily to maintain skin elasticity and support circulation.',
      priority: 'medium',
      triggerCondition: 'Low daily task compliance',
      canConvertToTodo: true,
      timestamp: now,
    });
  }

  if (recommendations.length === 0) {
    recommendations.push({
      id: 'rec-general',
      category: 'activity',
      title: 'Keep Up Daily Foot Checks',
      description:
        'Your readings look stable. Continue daily foot inspections and monitor pressure trends.',
      priority: 'low',
      triggerCondition: 'Stable readings',
      canConvertToTodo: false,
      timestamp: now,
    });
  }

  return recommendations;
}

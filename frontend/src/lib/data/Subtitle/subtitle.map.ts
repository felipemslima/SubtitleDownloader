import { EpisodeSubtitlePlan } from '@/types/subtitle';

export function normalizePlans(plans: EpisodeSubtitlePlan[]): EpisodeSubtitlePlan[] {
  return plans.map((plan) => ({
    ...plan,
    enabled: Boolean(plan.selectedSubtitle),
  }));
}

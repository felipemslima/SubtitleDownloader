from __future__ import annotations

from subtitle_app.models import EpisodeSubtitlePlan


def shouldDownloadPlan(plan: EpisodeSubtitlePlan) -> bool:
    return bool(plan.enabled and plan.selected_subtitle)

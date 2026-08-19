"""Deterministic, clinically conservative care recommendations.

These are educational prompts, not a diagnosis. The LLM-facing prompt builder
in the API wraps the same facts so StepMate stays grounded in sensor data.
"""

from __future__ import annotations

from xstep_ml.inference.engine import RiskResult


def build_recommendations(result: RiskResult, active_alert_count: int, completion_rate: float) -> list[dict]:
    recs: list[dict] = []

    if result.high_risk_zone in ("met1", "met2") or "forefoot" in result.gait_pattern:
        recs.append(
            {
                "id": "rec-forefoot",
                "category": "footwear",
                "title": "Offload the forefoot",
                "description": (
                    "Your insole is seeing elevated pressure under the metatarsal heads. "
                    "Rotate into a second pair of extra-depth diabetic shoes and avoid walking barefoot. "
                    "Inspect the ball of the foot tonight with a mirror."
                ),
                "priority": "high",
                "triggerCondition": f"gait={result.gait_pattern} zone={result.high_risk_zone}",
                "canConvertToTodo": True,
            }
        )
    if result.high_risk_zone == "heel" or "heel" in result.gait_pattern:
        recs.append(
            {
                "id": "rec-heel",
                "category": "rest",
                "title": "Unload the heel",
                "description": (
                    "Heel pressure is spiking. When sitting, elevate your feet 15 minutes, "
                    "2–3 times today, and check the back of the heel for redness that does not fade."
                ),
                "priority": "high",
                "triggerCondition": "heel overload",
                "canConvertToTodo": True,
            }
        )
    if result.extras.get("temp_asym_max", 0) >= 2.2:
        recs.append(
            {
                "id": "rec-temp",
                "category": "rest",
                "title": "Temperature asymmetry — rest this foot",
                "description": (
                    "A >2.2°C difference between matching sites can precede inflammation. "
                    "Reduce walking volume today and contact your clinic if redness or swelling appears."
                ),
                "priority": "high",
                "triggerCondition": "thermal asymmetry",
                "canConvertToTodo": True,
            }
        )
    if result.iwgdf_category >= 2:
        recs.append(
            {
                "id": "rec-clinic",
                "category": "activity",
                "title": "Schedule a foot-care visit",
                "description": (
                    "Your clinical risk category is elevated (prior ulcer, neuropathy, or both). "
                    "Daily 4-site skin checks plus a clinician review this month are recommended."
                ),
                "priority": "medium",
                "triggerCondition": f"IWGDF {result.iwgdf_category}",
                "canConvertToTodo": True,
            }
        )
    if completion_rate < 50:
        recs.append(
            {
                "id": "rec-compliance",
                "category": "hydration",
                "title": "Rebuild today's routine",
                "description": "Aim for 8 glasses of water and complete your foot-check task before evening.",
                "priority": "medium",
                "triggerCondition": "low task completion",
                "canConvertToTodo": True,
            }
        )
    if active_alert_count >= 3:
        recs.append(
            {
                "id": "rec-posture",
                "category": "activity",
                "title": "Correct posture now",
                "description": (
                    "Repeated high-pressure alerts: stand, redistribute weight, and take a short seated break. "
                    "The app will re-check after you offload."
                ),
                "priority": "high",
                "triggerCondition": "repeated pressure alerts",
                "canConvertToTodo": False,
            }
        )
    if not recs:
        recs.append(
            {
                "id": "rec-stable",
                "category": "activity",
                "title": "Keep up daily foot checks",
                "description": "Pressure and gait look stable. Continue inspections and trend review with your clinician.",
                "priority": "low",
                "triggerCondition": "stable",
                "canConvertToTodo": False,
            }
        )
    return recs


def stepmate_system_prompt(result: RiskResult, medical: dict, tasks: str) -> str:
    return (
        "You are StepMate, X-Step's diabetic foot-care education assistant. "
        "You are not a clinician and you must not diagnose, predict ulcers, or override "
        "the deterministic pressure/gait risk score. Ground every suggestion in the "
        "sensor-derived factors below. If a potentially serious condition is mentioned "
        "(open wound, spreading redness, fever, black tissue), tell the user to seek "
        "professional care. Always include that this is not medical advice.\n\n"
        f"Health index (deterministic engine, not LLM): {result.health_index:.0f}/100 ({result.level})\n"
        f"IWGDF-style category: {result.iwgdf_category}\n"
        f"Gait pattern: {result.gait_pattern} ({result.gait_confidence:.2f})\n"
        f"High-risk zone: {result.high_risk_zone} ({result.zone_confidence:.2f})\n"
        f"Peak pressure: {result.extras.get('peak_any', 0):.1f} kPa\n"
        f"Cadence: {result.extras.get('cadence_spm', 0):.0f} spm\n"
        f"Logged source features: {sorted(result.extras.keys())[:24]}\n"
        f"Medical questionnaire fields: {medical}\n"
        f"Tasks: {tasks}\n"
        "Visible disclaimer to the user: Not a diagnosis. Requires professional care for concerning findings.\n"
    )

# StepMate / LLM safety boundary

StepMate is an **educational** chat layer. It is not the risk engine.

## Separation of roles

| Component | May do | Must not do |
| --- | --- | --- |
| Deterministic engine (`ProductionEngine`) | Compute health index, gait class, zone, threshold alerts, decomposable `contributions` | Claim diagnosis |
| Feature/risk code | Log source features used for the score | Call an LLM |
| LLM | Summarize already-computed factors in plain language | Set or override the score; invent medical tests; diagnose |

API fields: `risk_source = deterministic_engine`, `disclaimer`, `contributions`, `stepmate_prompt`.

## Grounding

Prompts include peak pressure, cadence, gait class, zone, and questionnaire fields. The model is instructed to defer to clinicians and to recommend professional care for potentially serious signs (open wound, spreading redness, fever, necrotic appearance).

## Visible disclaimer

Mobile and API copy must remain: educational / not a diagnosis / not a medical device.

## Logging

Store the feature keys that entered the prompt (`extras` keys), the engine score, and the model name/version if a vendor LLM is used. Do not log raw identifiable chat without a privacy review.

## Ulcer images

Photograph grading, if enabled, is a separate public-dataset CNN. It does not update insole labels and is not fused unless paired IDs exist.

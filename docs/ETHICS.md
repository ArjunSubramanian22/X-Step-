# Ethics, intended use, and clinical claims

X-Step software in this repository is a **research prototype** for e-health and bioengineering methods work (EHB 2026: wearable systems, biosignal processing, AI in medicine). It is **not** an FDA-cleared or CE-marked medical device.

## Allowed claims in papers and talks
- Four FSR sites match high-risk plantar anatomy described in DFU literature.
- Features (PPP, PTI, asymmetry, cadence) are standard biomechanical quantities.
- Subject-grouped in-silico experiments are reproducible from this repo.
- The system can **display** pressure, gait class, and conservative offload prompts.

## Disallowed claims
- “Prevents amputation” or “detects ulcers” as a validated clinical outcome of this software release.
- Equivalence to Moticon/Tekscan spatial resolution.
- Diagnostic replacement for a wound-care visit.

## Human data
Do not commit identifiable telemetry. Wound images, if used, must remain public-dataset licensed. Prospective insole logging needs IRB/ethics approval and informed consent.

## Safety design
Threshold-based alerts still fire if the classifier is wrong. LLM/chat text is constrained to sensor facts and must defer to clinicians.

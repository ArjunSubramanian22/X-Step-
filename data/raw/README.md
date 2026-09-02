# Drop-in raw insole recordings

Put **new** session folders here. Raw files are never overwritten by the importer.

```text
python -m research.import_real_data
```

See `SCHEMA.md` for the CSV / JSON / BLE-bin layout (X-Step 4-FSR sessions).

A separate operator-provided archive, `InsolesOpitrackDataset.zip`, is a **32-cell insole + OptiTrack** walking dataset, not the four-site X-Step prototype. Evaluate it with:

```text
python -m research.experiments.evaluate_insoles_optitrack
```

Provenance: `research/data/insoles_optitrack/PROVENANCE.md`. Do not commit identifiable data. Anonymous codes only.

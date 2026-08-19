# Immutable processed datasets

Created only by `python -m research.import_real_data`.

Each run writes a new directory `data/processed/<run_id>/` and **refuses** to overwrite an existing run. Raw files under `data/raw/` are never modified.

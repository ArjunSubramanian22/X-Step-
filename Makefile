.PHONY: env test experiments api paper
PYTHON ?= python3

env:
	bash scripts/setup_env.sh

test:
	PYTHONPATH=. $(PYTHON) -m pytest tests -q

experiments:
	PYTHONPATH=. $(PYTHON) scripts/run_ehb_experiments.py

train:
	PYTHONPATH=. $(PYTHON) scripts/train_production.py

api:
	PYTHONPATH=. $(PYTHON) -m api.main

paper: experiments
	@echo "Figures in papers/ehb2026/figures (300 dpi)"

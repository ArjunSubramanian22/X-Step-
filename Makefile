.PHONY: setup test lint experiments figures tables paper-assets api ci-local
PYTHON ?= python3
export PYTHONPATH := .

setup:
	bash scripts/setup_env.sh
	chmod +x scripts/lock_requirements.sh
	@echo "Optional: source .venv/bin/activate && bash scripts/lock_requirements.sh"

test:
	$(PYTHON) -m pytest tests -q

lint:
	$(PYTHON) -m ruff check xstep_ml tests research/experiments api scripts --exclude 'ulcer model,heatmap model' || true

experiments:
	$(PYTHON) research/experiments/run_research.py
	$(PYTHON) scripts/run_ehb_experiments.py

figures:
	$(PYTHON) research/experiments/generate_figures.py

tables:
	$(PYTHON) research/experiments/generate_tables.py
	$(PYTHON) research/experiments/inject_results.py

paper-assets: experiments figures tables
	@echo "Paper assets in research/figures, research/tables, research/manuscript/results_fragment.md"

api:
	$(PYTHON) -m api.main

ci-local: test
	RESEARCH_SMOKE=1 $(PYTHON) research/experiments/run_research.py
	$(PYTHON) research/experiments/generate_figures.py
	$(PYTHON) research/experiments/generate_tables.py
	$(PYTHON) research/experiments/inject_results.py

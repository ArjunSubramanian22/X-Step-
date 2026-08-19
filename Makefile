.PHONY: setup test lint experiments final-eval figures tables generated-results paper-assets paper registry api ci-local
PYTHON ?= python3
export PYTHONPATH := .

setup:
	bash scripts/setup_env.sh
	chmod +x scripts/lock_requirements.sh
	@echo "Optional: source .venv/bin/activate && bash scripts/lock_requirements.sh"

test:
	$(PYTHON) -m pytest tests -q

lint:
	$(PYTHON) -m ruff check xstep_ml tests research api scripts --exclude 'ulcer model,heatmap model,research/notebooks' || true

experiments:
	$(PYTHON) research/experiments/run_research.py
	$(PYTHON) scripts/run_ehb_experiments.py

final-eval:
	$(PYTHON) research/experiments/run_final_eval.py

figures:
	$(PYTHON) research/experiments/generate_figures.py

tables:
	$(PYTHON) research/experiments/generate_tables.py
	$(PYTHON) research/experiments/inject_results.py

registry:
	$(PYTHON) research/experiments/build_registry.py

generated-results: registry
	$(PYTHON) research/experiments/generate_results.py
	$(PYTHON) research/experiments/inject_results.py

# Retrains synthetic experiments. Do not use to chase decimals after freeze.
paper-assets: experiments final-eval figures tables generated-results
	@echo "Paper assets in research/figures, research/tables, research/manuscript/"

# Submission package: no training.
paper:
	$(PYTHON) -m research.build_paper

api:
	$(PYTHON) -m api.main

ci-local: test
	RESEARCH_SMOKE=1 $(PYTHON) research/experiments/run_research.py
	RESEARCH_SMOKE=1 $(PYTHON) research/experiments/run_final_eval.py
	$(PYTHON) research/experiments/generate_figures.py
	$(PYTHON) research/experiments/generate_tables.py
	$(PYTHON) research/experiments/build_registry.py
	$(PYTHON) research/experiments/generate_results.py
	$(PYTHON) research/experiments/inject_results.py
	$(PYTHON) research/experiments/verify_references.py
	$(PYTHON) research/experiments/lint_manuscript.py

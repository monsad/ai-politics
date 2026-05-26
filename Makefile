.PHONY: setup smoke validate-skills demo clean

setup:
	uv venv .venv --python 3.11
	. .venv/bin/activate && uv pip install -e ".[dev]"
	npm install
	npx skills add mmtmr/pageindex-rag -g -y
	. .venv/bin/activate && pre-commit install

smoke:
	. .venv/bin/activate && pytest tests/test_gate_01_hermes_import.py
	. .venv/bin/activate && pytest tests/test_gate_02_minimal_agent.py
	. .venv/bin/activate && pytest tests/test_gate_03_delegate_task.py
	. .venv/bin/activate && pytest tests/test_gate_04_pageindex_doc_search.py
	. .venv/bin/activate && pytest tests/test_gate_05_diacritics.py
	. .venv/bin/activate && pytest tests/test_gate_06_skills_ref.py
	. .venv/bin/activate && pytest tests/test_gate_07_concurrent_search.py

validate-skills:
	npx skills-ref@0.1.5 validate skills/

demo:
	@echo "Phase 1: nothing to demo yet — run 'make smoke' to verify gates"

clean:
	rm -rf .venv node_modules .pytest_cache .ruff_cache __pycache__ dist build *.egg-info

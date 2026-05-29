# MarketPulse AI — common dev commands
# Run from the project root (the same directory as this Makefile).
#
# Each target prefers `uv run …` so commands work without manually activating
# the venv. `uv run` syncs dependencies on demand.

.PHONY: help install lint fmt typecheck test ingest producer consumer kafka-up kafka-down ui eval clean

help:  ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "Targets:\n"} /^[a-zA-Z_-]+:.*##/ { printf "  %-12s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install:  ## Install / sync all dependencies (runtime + dev)
	uv sync

lint:  ## Run ruff linter (does not modify files)
	uv run ruff check src tests

fmt:  ## Format src + tests with ruff
	uv run ruff format src tests
	uv run ruff check --fix src tests

typecheck:  ## Run mypy in strict mode on src/ (skipped if src/ has no .py files yet)
	@if find src -name '*.py' -print -quit | grep -q .; then \
		uv run mypy; \
	else \
		echo "[typecheck] No .py files in src/ yet — skipping. Will run once code lands."; \
	fi

test:  ## Run pytest with coverage (skipped if tests/ has no test files yet)
	@if find tests -name 'test_*.py' -print -quit | grep -q .; then \
		uv run pytest --cov=src --cov-report=term-missing; \
	else \
		echo "[test] No test files in tests/ yet — skipping. Will run once tests land."; \
	fi

# --- Placeholders for v0.1 MVP slices (filled in as each slice lands) ---

ingest:  ## Run the RSS ingestion + indexing pipeline once (no Kafka)
	uv run python -m marketpulse.ingestion --mode once

producer:  ## Start the Kafka RSS producer (polls every 5 min); requires make kafka-up first
	uv run python -m marketpulse.ingestion --mode producer

consumer:  ## Start the Kafka consumer (embeds + upserts to ChromaDB); requires make kafka-up first
	uv run python -m marketpulse.ingestion --mode consumer

kafka-up:  ## Start Kafka (Docker) in the background
	docker compose -f docker/docker-compose.yml up -d

kafka-down:  ## Stop and remove Kafka containers
	docker compose -f docker/docker-compose.yml down

query:  ## Ad-hoc retrieval query (usage: make query Q="your question")
	@if [ -z "$(Q)" ]; then echo 'usage: make query Q="your question"'; exit 1; fi
	uv run python -m marketpulse.retrieval "$(Q)"

ask:  ## Ask Gemini a question over the indexed corpus (usage: make ask Q="your question")
	@if [ -z "$(Q)" ]; then echo 'usage: make ask Q="your question"'; exit 1; fi
	uv run python -m marketpulse.synthesis "$(Q)"

ui:  ## Launch the Streamlit demo UI at http://localhost:8501
	uv run streamlit run src/marketpulse/ui/app.py

eval:  ## Run RAGAS evaluation against a small hardcoded question set (requires GEMINI_API_KEY)
	uv run python scripts/evaluate.py

clean:  ## Remove caches and the virtual env
	rm -rf .venv .ruff_cache .mypy_cache .pytest_cache .coverage htmlcov coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +

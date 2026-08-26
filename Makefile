# ==============================================================================
# Python Togo API - Makefile
# Usage : make <cible>   |   make help pour la liste complete
# ==============================================================================

# --- Variables configurables (surchargeables : make dev PORT=9000) -----------
PYTHON      ?= python3
VENV        ?= venv
BIN         := $(VENV)/bin
HOST        ?= 0.0.0.0
PORT        ?= 8000
WORKERS     ?= 4
APP         := app/main.py
ENV_FILE    := app/.env
ENV_EXAMPLE := app/.env.example
API_PORT    ?= 8080
COMPOSE     ?= API_PORT=$(API_PORT) docker compose
SERVICE     ?= api

.DEFAULT_GOAL := help
.PHONY: help venv install env migrate dev run start stop check-env freeze \
	clean clean-pyc reset build up down restart logs ps shell db-shell \
	redis-cli docker-migrate rebuild prune

# ==============================================================================
# Aide
# ==============================================================================
help: ## Affiche cette aide
	@echo "Python Togo API - commandes disponibles :"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Variables : PORT=$(PORT) API_PORT=$(API_PORT) HOST=$(HOST) VENV=$(VENV) SERVICE=$(SERVICE)"

# ==============================================================================
# Developpement local
# ==============================================================================
venv: ## Cree l'environnement virtuel Python
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	@$(BIN)/pip install --upgrade pip

install: venv ## Installe les dependances dans le venv
	@$(BIN)/pip install -r requirements.txt

env: ## Cree app/.env a partir de app/.env.example (si absent)
	@if [ -f $(ENV_FILE) ]; then \
		echo "$(ENV_FILE) existe deja, aucune action."; \
	else \
		cp $(ENV_EXAMPLE) $(ENV_FILE); \
		echo "$(ENV_FILE) cree. Pensez a remplir les variables."; \
	fi

check-env: ## Verifie que app/.env est present
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "Erreur : $(ENV_FILE) manquant. Lancez 'make env'."; \
		exit 1; \
	fi

migrate: check-env ## Execute les migrations de la base de donnees
	@$(BIN)/python -m app.database.migrations

dev: check-env ## Demarre l'API en mode developpement (rechargement auto)
	@$(BIN)/fastapi dev $(APP) --host $(HOST) --port $(PORT)

run: check-env ## Demarre l'API en mode production (multi-workers)
	@$(BIN)/fastapi run $(APP) --host $(HOST) --port $(PORT) --workers $(WORKERS)

start: install env migrate dev ## Installation complete puis demarrage en dev

freeze: ## Fige les dependances installees dans requirements.lock.txt
	@$(BIN)/pip freeze > requirements.lock.txt
	@echo "requirements.lock.txt genere."

# ==============================================================================
# Docker
# ==============================================================================
build: ## Construit les images Docker
	@$(COMPOSE) build

up: ## Demarre la stack Docker (api + postgres + redis) en arriere-plan
	@$(COMPOSE) up -d
	@echo "API disponible sur http://localhost:$(API_PORT)"

down: ## Arrete la stack Docker
	@$(COMPOSE) down

stop: down ## Alias de 'down'

restart: ## Redemarre la stack Docker
	@$(COMPOSE) restart

rebuild: ## Reconstruit sans cache puis redemarre la stack
	@$(COMPOSE) build --no-cache
	@$(COMPOSE) up -d --force-recreate

logs: ## Suit les logs du service api (SERVICE=db pour un autre)
	@$(COMPOSE) logs -f $(SERVICE)

ps: ## Liste l'etat des conteneurs
	@$(COMPOSE) ps

shell: ## Ouvre un shell dans le conteneur api
	@$(COMPOSE) exec $(SERVICE) bash

db-shell: ## Ouvre psql dans le conteneur postgres
	@$(COMPOSE) exec db psql -U $${DB_USER:-postgres} -d $${DB_NAME:-pythontogo_db}

redis-cli: ## Ouvre redis-cli dans le conteneur redis
	@$(COMPOSE) exec redis redis-cli

docker-migrate: ## Execute les migrations dans le conteneur api
	@$(COMPOSE) exec $(SERVICE) python -m app.database.migrations

prune: ## Arrete la stack et supprime les volumes (DONNEES PERDUES)
	@$(COMPOSE) down -v

# ==============================================================================
# Nettoyage
# ==============================================================================
clean-pyc: ## Supprime les fichiers Python compiles
	@find . -type d -name '__pycache__' -not -path './$(VENV)/*' -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name '*.py[co]' -not -path './$(VENV)/*' -delete

clean: clean-pyc ## Nettoie les caches (pycache, pytest, mypy)
	@rm -rf .pytest_cache .mypy_cache .coverage htmlcov

reset: clean ## Supprime aussi l'environnement virtuel
	@rm -rf $(VENV)

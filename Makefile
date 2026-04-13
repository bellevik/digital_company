COMPOSE := docker compose

.PHONY: dev down logs backend-shell db-shell

dev:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down --remove-orphans

logs:
	$(COMPOSE) logs -f

backend-shell:
	$(COMPOSE) exec backend /bin/bash

db-shell:
	$(COMPOSE) exec db psql -U $$POSTGRES_USER -d $$POSTGRES_DB


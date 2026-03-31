include .env
export

up:
	docker compose up -d

down:
	docker compose down

down-v:
	docker compose down -v

logs:
	docker compose logs -f postgres

status:
	docker compose ps

psql:
	docker compose exec postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

generate-source:
	python src/generators/generate_source_data.py

validate-source:
	python src/validation/validate_source_data.py
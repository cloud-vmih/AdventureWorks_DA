# Makefile for orchestrating the AdventureWorks Data Analytics pipeline

.PHONY: up down build logs shell ingest-macro etl build-marts quality-check train-all run-all

# Start all Docker containers
up:
	docker compose up -d

# Stop and clean Docker containers and volumes
down:
	docker compose down -v

# Force build all Docker images
build:
	docker compose build --no-cache

# Stream logs of all containers
logs:
	docker compose logs -f

# Open shell inside python analytics container
shell:
	docker compose exec analytics_runner bash

# Fetch macroeconomic data from World Bank + FRED APIs to staging
ingest-macro:
	docker compose exec analytics_runner python src/etl/run_prj2_macro.py

# Extract OLTP database to Staging and load DWH core dimension/fact tables
etl:
	docker compose exec analytics_runner python src/etl/run_etl.py

# Rebuild monthly sales and other analytical data marts
build-marts:
	docker compose exec analytics_runner python src/marts/build_marts.py

# Execute data quality queries and print violations
quality-check:
	docker compose exec analytics_runner python src/data_quality.py

# Re-generate features and run train/evaluation/predictions for ML models
train-all:
	docker compose exec analytics_runner python src/ml/run_ml.py

# Run the complete end-to-end analytics pipeline
run-all:
	@make ingest-macro
	@make etl
	@make build-marts
	@make quality-check
	@make train-all
	@echo "--- COMPLETE PIPELINE EXECUTED SUCCESSFULLY ---"

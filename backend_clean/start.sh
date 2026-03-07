#!/bin/bash
# Script de démarrage pour Railway
# Installe les browsers Playwright puis démarre l'application

echo "[START] Installation des browsers Playwright..."
playwright install chromium

echo "[START] Démarrage de l'application FastAPI..."
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

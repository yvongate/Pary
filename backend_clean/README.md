# ⚽ Backend Clean - Système de Prédictions Football

Backend propre et optimisé pour les prédictions de matchs de football.

## 🎯 Fonctionnalités

### ✅ Prédictions
- **Double vérification** : Calcul mathématique + IA deep reasoning
- **Régression dynamique** : Basée sur historique + classements temps réel
- **8 championnats** : Premier League, Liga, Serie A, Ligue 1, Bundesliga, Championship, Ligue 2, Primeira Liga

### ✅ Données
- **12 classements** temps réel (soccerstats.com)
- **Historique complet** saison 2025-2026
- **Contexte match** (Rue des Joueurs)
- **Météo** en temps réel

### ✅ Coûts
- **SerpAPI** : 0€ (scraping direct gratuit)
- **DeepInfra** : ~0.001$ par prédiction
- **Total** : < 1$/jour pour 100 prédictions

---

## 📁 Structure

```
backend_clean/
├── main.py                          # FastAPI app
├── complete_analysis_service.py     # Service analyse complète
│
├── services/                        # Services métier
│   ├── prediction_service.py        # Orchestration
│   ├── data_service.py              # Gestion CSV
│   ├── ai_service.py                # DeepInfra
│   ├── database_service.py          # Interface DB
│   └── sqlite_database_service.py   # SQLite
│
├── core/                            # Logique métier
│   ├── dynamic_prediction.py        # Moteur prédiction
│   ├── data_collector.py            # Collecteur données
│   ├── ai_reasoning_generator.py    # Textes IA
│   └── ai_deep_reasoning.py         # Vérification IA
│
├── scrapers/                        # Scrapers externes
│   ├── soccerstats_overview.py      # Classements (12 tables)
│   ├── ruedesjoueurs_direct.py      # RDJ gratuit
│   ├── ruedesjoueurs_finder.py      # Interface RDJ
│   └── ruedesjoueurs_scraper.py     # Parser RDJ
│
├── utils/                           # Utilitaires
│   └── download_data.py             # Téléchargement CSV
│
├── config/                          # Configuration
│   └── settings.py                  # Settings
│
└── data/                            # Données locales
    ├── E0_2526.csv                  # Premier League
    ├── SP1_2526.csv, I1_2526.csv...
    └── fixtures.csv
```

---

## 🚀 Installation

### 1. Prérequis
```bash
Python 3.9+
pip
```

### 2. Installer dépendances
```bash
cd backend_clean
pip install -r requirements.txt
```

### 3. Configuration
Créer `.env` avec :
```env
DEEPINFRA_API_KEY=your_key_here
SERP API_KEY=optional_not_used
```

### 4. Télécharger données
```bash
python -c "from utils.download_data import download_all; download_all()"
```

### 5. Démarrer
```bash
python main.py
```

API disponible sur : `http://localhost:8000`

---

## 📡 API Endpoints

### Génére une prédiction
```http
POST /predictions/generate
Content-Type: application/json

{
  "home_team": "Everton",
  "away_team": "Man United",
  "league_code": "E0",
  "match_date": "2026-02-23T15:00:00Z"
}
```

**Réponse:**
```json
{
  "match_id": "E0_20260223_EvertonManUnited",
  "predictions": {
    "shots": {"min": 20, "max": 35},
    "corners": {"min": 7, "max": 12}
  },
  "ai_verification": {
    "shots_min": 22,
    "shots_max": 32,
    "reasoning": "...",
    "agreement_shots": 85.2
  },
  "metadata": {
    "execution_time": 58.3,
    "ruedesjoueurs_used": true,
    "ai_verification_used": true
  }
}
```

### Récupérer prédictions
```http
GET /predictions/upcoming?league_code=E0&limit=10
```

---

## 🧪 Tests

### Test rapide
```bash
python -c "from services.prediction_service import get_prediction_service; ps = get_prediction_service(); ps.generate_prediction_for_match({'match_id': 'test', 'home_team': 'Everton', 'away_team': 'Man United', 'league_code': 'E0', 'match_date': '2026-02-23'})"
```

### Test scraping RDJ
```bash
python -c "from scrapers.ruedesjoueurs_direct import get_match_analysis_auto; print(get_match_analysis_auto('Strasbourg', 'Lens', 'F1'))"
```

### Test classements
```bash
python -c "from scrapers.soccerstats_overview import get_tables_overview; print(get_tables_overview('england'))"
```

---

## 🔧 Configuration Service (Production)

### Systemd (Linux)
```ini
[Unit]
Description=Football Predictions Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/backend_clean
Environment="PATH=/var/www/backend_clean/venv/bin"
ExecStart=/var/www/backend_clean/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### PM2 (Node.js process manager)
```bash
pm2 start main.py --name football-backend --interpreter python3
pm2 save
pm2 startup
```

---

## 📊 Performance

- **Génération prédiction** : ~60 secondes
  - Scraping classements : 5s
  - Analyse historique : 10s
  - Contexte RDJ : 10s
  - Génération IA : 30s
  - Vérification IA : 15s

- **Base de données** : SQLite (local, rapide)
- **Concurrence** : FastAPI async

---

## 🐛 Troubleshooting

### Erreur "No module named 'services'"
```bash
# Ajouter backend_clean au PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/backend_clean"
```

### Erreur DB
```bash
# Supprimer et recréer
rm predictions.db
python -c "from services.sqlite_database_service import SQLiteDatabaseService; SQLiteDatabaseService()"
```

### Scraping ne fonctionne pas
```bash
# Vérifier connexion
python -c "import requests; print(requests.get('https://www.soccerstats.com').status_code)"
```

---

## 📝 Changelog

### v2.0 (24/02/2026)
- ✅ Backend restructuré et nettoyé
- ✅ Scraping RDJ gratuit (sans SerpAPI)
- ✅ Double vérification IA
- ✅ Économie 180$/an sur SerpAPI

### v1.0 (23/02/2026)
- ✅ Système de base
- ✅ 87.5% précision sur tests

---

## 📜 License

Propriétaire - Tous droits réservés

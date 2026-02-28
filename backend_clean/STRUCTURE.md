# Structure Backend Clean

```
backend_clean/
│
├── main.py                          # FastAPI app principale
│
├── services/                        # Services métier
│   ├── __init__.py
│   ├── prediction_service.py        # Orchestration prédictions
│   ├── complete_analysis_service.py # Analyse complète match
│   ├── data_service.py              # Gestion données CSV
│   ├── ai_service.py                # Service IA (DeepInfra)
│   ├── database_service.py          # Interface DB
│   └── sqlite_database_service.py   # Implémentation SQLite
│
├── core/                            # Logique métier core
│   ├── __init__.py
│   ├── dynamic_prediction.py        # Moteur prédiction dynamique
│   ├── data_collector.py            # Collecteur données (météo, ville)
│   └── ai_reasoning_generator.py    # Génération textes IA
│
├── scrapers/                        # Scrapers externes
│   ├── __init__.py
│   ├── soccerstats_overview.py      # Classements soccerstats (12 tables)
│   ├── ruedesjoueurs_direct.py      # RDJ scraping direct GRATUIT
│   ├── ruedesjoueurs_finder.py      # Interface RDJ
│   └── ruedesjoueurs_scraper.py     # Scraper pages RDJ
│
├── utils/                           # Utilitaires
│   ├── __init__.py
│   └── download_data.py             # Téléchargement données historiques
│
├── config/                          # Configuration
│   ├── __init__.py
│   └── settings.py                  # Settings centralisés
│
├── data/                            # Données locales
│   ├── E0_2526.csv                  # Premier League
│   ├── SP1_2526.csv                 # La Liga
│   ├── I1_2526.csv                  # Serie A
│   ├── F1_2526.csv                  # Ligue 1
│   ├── D1_2526.csv                  # Bundesliga
│   └── fixtures.csv                 # Matchs à venir
│
├── .env                             # Variables environnement
├── requirements.txt                 # Dépendances Python
├── predictions.db                   # Base SQLite
│
└── README.md                        # Documentation

## Fonctionnalités

✅ Prédictions dynamiques (calcul + IA)
✅ Double vérification (calcul mathématique + IA deep reasoning)
✅ Scraping gratuit (soccerstats + RDJ sans SerpAPI)
✅ Base SQLite locale
✅ API REST (FastAPI)
✅ Support 8 championnats

## Coût

- SerpAPI : 0€ (scraping direct)
- DeepInfra : ~0.001$/prédiction
- Hébergement : Variable

## Performance

- Génération prédiction : ~60 secondes
- Double vérification IA : incluse
- Base de données : SQLite (local, rapide)
```

# ParY - Système de Prédictions Football

**Version**: 2.0 (Clean)
**Date**: 25/02/2026
**Status**: ✅ Production Ready

---

## 📁 Structure du Projet

```
parY/
├── backend_clean/          # Backend API (production-ready)
│   ├── services/          # Services métier
│   ├── core/              # Logique de prédiction
│   ├── scrapers/          # Scrapers (gratuit - 0€)
│   ├── data/              # Données CSV (17 fichiers)
│   └── README.md          # Documentation complète
│
├── front/                 # Frontend (interface web)
│
├── docs_archive/          # Anciennes documentations de développement
│
└── README.md             # Ce fichier
```

---

## 🚀 Démarrage Rapide

### Backend

```bash
cd backend_clean

# Windows
start_service.bat

# Linux/Mac
python main.py
```

**API disponible**: http://localhost:8000
**Documentation**: http://localhost:8000/docs

### Frontend

```bash
cd front
# Suivre les instructions dans front/README.md
```

---

## 📊 Système de Prédiction

### Architecture

- **Calcul Mathématique**: Régression dynamique basée sur historique
- **IA Deep Reasoning**: Vérification indépendante par IA
- **Scraping Gratuit**: 0€ (soccerstats + RDJ direct)
- **Base de données**: SQLite local + Supabase cloud (PostgreSQL)

### Championnats Supportés (8)

1. Premier League (E0)
2. Championship (E1)
3. La Liga (SP1)
4. Serie A (I1)
5. Ligue 1 (F1)
6. Ligue 2 (F2)
7. Bundesliga (D1)
8. Primeira Liga (P1)

### Données Utilisées

**12 Tables Soccerstats** (temps réel):
- Classement général
- Forme récente (8 matchs)
- Domicile / Extérieur
- Attaque / Défense
- Statistiques combinées

**Historique**: 26+ matchs par équipe (CSV football-data.co.uk)

**Contexte**:
- Météo (wttr.in)
- Formations (4-3-3, 5-4-1, etc.)
- Classements actuels
- Contexte RDJ (Rue des Joueurs)

---

## 💰 Coûts

| Service | Ancien | Nouveau | Économie |
|---------|--------|---------|----------|
| SerpAPI | 180€/an | 0€ | 180€/an |
| DeepInfra IA | - | ~36€/an | - |
| **TOTAL** | **180€/an** | **~36€/an** | **144€/an (80%)** |

---

## 📚 Documentation

### Backend
- `backend_clean/README.md` - Documentation complète
- `backend_clean/DEPLOYMENT.md` - Guide déploiement
- `backend_clean/STRUCTURE.md` - Architecture
- `backend_clean/SCHEMA_SUPABASE.md` - Base de données
- `backend_clean/SUPABASE_STATUS.md` - État Supabase

### Anciennes Docs (Archivées)
- `docs_archive/` - Guides de développement historiques

---

## ✅ Tests de Validation

### Backend Tests (100% passés)
- ✅ API REST opérationnelle
- ✅ Prédictions générées (11.5s)
- ✅ Scrapers gratuits fonctionnels
- ✅ Base de données (SQLite + Supabase)
- ✅ Documentation Swagger
- ✅ Supabase 100% opérationnel (29 prédictions)

**Exemple de prédiction**:
- Match: Everton vs Man United
- Temps: 11.5 secondes
- Résultat: 28.2 tirs, 9.3 corners
- Confiance: 8.3% (R²)

---

## 🔧 Configuration

### Variables d'environnement (.env)

```env
# DeepInfra (IA)
DEEPINFRA_API_KEY=your_key_here

# Supabase (optionnel - si vous utilisez cloud)
SUPABASE_URL=postgresql://...
```

---

## 📈 Performance

### Génération de Prédiction

**Temps moyen**: 15-20 secondes
- Scraping classements: 5s
- Analyse historique: 5s
- Calcul corrélation: 2s
- Météo et contexte: 3s

**Avec IA Deep Reasoning**: 60-90 secondes
- Génération IA: +30s
- Vérification IA: +15s
- Comparaison: +2s

---

## 🛠️ Technologies

### Backend
- **Python 3.9+**
- FastAPI (API REST)
- Pandas, NumPy (analyse)
- BeautifulSoup (scraping)
- scikit-learn (régression)
- psycopg2 (PostgreSQL)

### Base de Données
- **SQLite** (local - développement)
- **Supabase** (PostgreSQL cloud - production)

### IA
- **DeepInfra** (Llama 3 70B)

---

## 📞 Support

Pour toute question, consulter:
1. `backend_clean/README.md` - Documentation complète
2. `backend_clean/DEPLOYMENT.md` - Déploiement
3. http://localhost:8000/docs - API Swagger

---

## 🔄 Historique

**v2.0 (25/02/2026)** - Backend Clean
- ✅ Restructuration complète
- ✅ Suppression ancien backend (3.9M → 2.7M)
- ✅ Scraping gratuit (0€ - économie 180€/an)
- ✅ Supabase configuré et opérationnel
- ✅ Tests 100% passés
- ✅ Documentation complète

**v1.0** - Version initiale
- Backend monolithique
- SerpAPI payant (180€/an)
- SQLite uniquement

---

## 📝 License

Projet privé - Tous droits réservés

---

**✅ Prêt pour la production**

Backend propre, optimisé, et 100% fonctionnel!

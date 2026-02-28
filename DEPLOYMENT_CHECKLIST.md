# Checklist de Déploiement - ParY Football Predictions

## ✅ Étapes Complétées

### 1. Structure du Projet
- [x] Backend FastAPI nettoyé et opérationnel
- [x] Frontend Next.js avec 2 pages (calendrier + prédictions)
- [x] Connexion front-back vérifiée
- [x] Système d'automatisation créé
- [x] Documentation complète

### 2. GitHub
- [x] Repository initialisé
- [x] Premier commit effectué (94 fichiers, 21097 lignes)
- [x] Push vers https://github.com/yvongate/Pary.git ✅
- [x] .gitignore configurés (backend + frontend + root)

### 3. Configuration de Déploiement
- [x] `backend_clean/railway.json` + `Procfile` - Configuration Railway ⭐
- [x] `backend_clean/RAILWAY_DEPLOY.md` - Guide déploiement Railway (recommandé)
- [x] `backend_clean/render.yaml` - Configuration Render (alternative)
- [x] `backend_clean/RENDER_DEPLOY.md` - Guide déploiement Render (alternative)
- [x] `front/my-app/VERCEL_DEPLOY.md` - Guide déploiement frontend

---

## 📋 Prochaines Étapes

### Étape 1: Déployer le Backend sur Railway ⭐ (Recommandé)

**Guide complet:** `backend_clean/RAILWAY_DEPLOY.md`

**Pourquoi Railway?**
- ✅ Pas de cold start (service toujours actif)
- ✅ Plus rapide à déployer (2-3 minutes)
- ✅ $5 de crédit gratuit/mois (~500h)
- ✅ Interface plus simple

**Résumé rapide:**
1. Créer compte sur https://railway.app
2. "New Project" → "Deploy from GitHub repo"
3. Sélectionner `yvongate/Pary`
4. Railway détecte automatiquement Python et configure tout
5. Ajouter les variables d'environnement:
   ```
   SUPABASE_URL = https://votre-projet.supabase.co
   SUPABASE_KEY = votre-clé-service-role
   DEEPINFRA_API_KEY = votre-clé-deepinfra
   AUTOMATION_API_KEY = (générer avec: openssl rand -hex 32)
   ```
6. Settings → Networking → "Generate Domain"
7. Noter l'URL (ex: https://pary-backend-production.up.railway.app)

**Alternative: Render** - Voir `backend_clean/RENDER_DEPLOY.md`

---

### Étape 2: Déployer le Frontend sur Vercel

**Guide complet:** `front/my-app/VERCEL_DEPLOY.md`

**Résumé rapide:**
1. Créer compte sur https://vercel.com
2. Importer le repository `yvongate/Pary`
3. Configurer:
   ```
   Project Name: pary-frontend
   Framework: Next.js
   Root Directory: front/my-app
   ```
4. Ajouter variable d'environnement:
   ```
   NEXT_PUBLIC_API_URL = https://pary-backend.onrender.com
   ```
   (Utiliser l'URL obtenue à l'étape 1)
5. Déployer et noter l'URL (ex: https://pary-frontend.vercel.app)

---

### Étape 3: Configurer l'Automatisation (Cron-job.org)

**Guide complet:** `backend_clean/CRONJOB_SETUP.md`

**Résumé rapide:**
1. Créer compte sur https://cron-job.org
2. Configurer 3 cron jobs:

**Job 1: Mise à jour des données (08:00 quotidien)**
```
URL: https://pary-backend.onrender.com/automation/update-data
Method: POST
Schedule: 0 8 * * *
Header: X-API-Key: votre-clé
```

**Job 2: Génération prédictions (10:00 quotidien)**
```
URL: https://pary-backend.onrender.com/automation/generate-predictions?hours_ahead=48
Method: POST
Schedule: 0 10 * * *
Header: X-API-Key: votre-clé
```

**Job 3: Health Check (toutes les 6h)**
```
URL: https://pary-backend.onrender.com/automation/status
Method: GET
Schedule: 0 0,6,12,18 * * *
```

---

## 📊 Structure du Repository GitHub

```
Pary/
├── backend_clean/              # Backend FastAPI
│   ├── automation/            # Scripts automatisation
│   ├── core/                  # Logique métier
│   ├── scrapers/              # Web scrapers
│   ├── services/              # Services (DB, AI, etc.)
│   ├── data/                  # CSV historiques
│   ├── main.py                # API FastAPI
│   ├── requirements.txt       # Dépendances Python
│   ├── render.yaml            # Config Render
│   └── *.md                   # Documentation
│
├── front/my-app/              # Frontend Next.js
│   ├── app/                   # Pages Next.js
│   │   ├── page.tsx          # Accueil (calendrier)
│   │   └── predictions/      # Page prédictions
│   ├── components/            # Composants React
│   ├── lib/                   # API client
│   ├── package.json           # Dépendances Node
│   └── VERCEL_DEPLOY.md      # Guide déploiement
│
├── .gitignore                 # Ignorer fichiers sensibles
└── README.md                  # Documentation projet
```

---

## 🔑 Variables d'Environnement Nécessaires

### Backend (Render)
```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx
DEEPINFRA_API_KEY=xxx
AUTOMATION_API_KEY=xxx (générer aléatoirement)
```

### Frontend (Vercel)
```env
NEXT_PUBLIC_API_URL=https://pary-backend.onrender.com
```

### Cron-job.org
```
Header: X-API-Key: [même que AUTOMATION_API_KEY]
```

---

## 🎯 Résumé des URLs

Une fois déployé, tu auras:

| Service | URL | Utilisation |
|---------|-----|-------------|
| **Backend API** | https://pary-backend-production.up.railway.app | API FastAPI + Automatisation |
| **Frontend Web** | https://pary-frontend.vercel.app | Interface utilisateur |
| **GitHub Repo** | https://github.com/yvongate/Pary | Code source |
| **Cron-job.org** | https://console.cron-job.org | Automatisation |

---

## ⚙️ Fonctionnalités du Système

### Backend
- ✅ Prédictions dynamiques (tirs + corners)
- ✅ IA deep reasoning (DeepInfra)
- ✅ Scraping gratuit (Soccerstats + RDJ)
- ✅ CSV historiques (football-data.co.uk)
- ✅ Automatisation complète
- ✅ Base de données SQLite + Supabase

### Frontend
- ✅ Calendrier de matchs (8 championnats)
- ✅ Page de prédictions avec filtres
- ✅ Design responsive

### Automatisation
- ✅ Mise à jour CSV quotidienne (08:00)
- ✅ Génération prédictions (10:00)
- ✅ Health checks (6h)
- ✅ 100% gratuit

---

## 📚 Documentation Disponible

| Fichier | Description |
|---------|-------------|
| `backend_clean/README.md` | Vue d'ensemble backend |
| `backend_clean/RENDER_DEPLOY.md` | Guide déploiement Render |
| `backend_clean/AUTOMATION.md` | Documentation automatisation |
| `backend_clean/CRONJOB_SETUP.md` | Configuration cron jobs |
| `backend_clean/EXPLICATION_SYSTEMES.md` | Explication erreurs API |
| `front/my-app/VERCEL_DEPLOY.md` | Guide déploiement Vercel |
| `CLEANUP_SUMMARY.md` | Résumé nettoyage projet |

---

## 💰 Coût Total

| Service | Plan | Coût |
|---------|------|------|
| **Railway** | Starter | 0€ ($5 crédit/mois ~500h) |
| **Vercel** | Hobby | 0€ (100GB/mois) |
| **Cron-job.org** | Free | 0€ (illimité) |
| **football-data.co.uk** | Free | 0€ |
| **Soccerstats** | Free | 0€ (scraping) |
| **RDJ** | Free | 0€ (scraping) |
| **Supabase** | Free | 0€ (500MB) |
| **DeepInfra** | Free tier | ~0€ (avec limites) |
| **TOTAL** | | **0€/mois** ✅ |

---

## ⚠️ Notes Importantes

### Plan Gratuit Render
- Le service s'arrête après 15min d'inactivité
- Premier démarrage: 30-60s (cold start)
- Solution: Health check toutes les 6h garde le service actif

### Variables d'Environnement
- Ne jamais commiter .env dans Git
- Toujours configurer dans les dashboards (Render/Vercel)

### CORS
Si problème de CORS, vérifier `backend_clean/main.py`:
```python
allow_origins=[
    "https://pary-frontend.vercel.app",
    "http://localhost:3000",
    "https://*.vercel.app"  # Pour les previews Vercel
]
```

### Railway vs Render
**Railway (recommandé):**
- ✅ Pas de cold start
- ✅ Déploiement plus rapide
- ✅ Interface plus simple

**Render (alternative):**
- ⚠️ Cold start après 15min inactivité
- ✅ 750h gratuites vs 500h Railway

---

## ✅ Checklist de Déploiement Final

### Pre-déploiement
- [x] Code committé sur GitHub
- [x] .gitignore configurés
- [x] Documentation complète

### Backend (Railway)
- [ ] Compte Railway créé
- [ ] Projet créé depuis GitHub
- [ ] Service Python détecté automatiquement
- [ ] Variables d'environnement configurées
- [ ] Build et déploiement réussis
- [ ] Domaine généré (Settings → Networking)
- [ ] URL notée: _______________

### Frontend
- [ ] Compte Vercel créé
- [ ] Projet importé
- [ ] NEXT_PUBLIC_API_URL configurée
- [ ] Build réussi
- [ ] URL notée: _______________

### Automatisation
- [ ] Compte Cron-job.org créé
- [ ] API Key générée
- [ ] Job 1: Update Data (08:00) configuré
- [ ] Job 2: Generate Predictions (10:00) configuré
- [ ] Job 3: Health Check (6h) configuré
- [ ] Test manuel réussi
- [ ] Email notifications configurées

### Vérification Finale
- [ ] Backend accessible (curl https://backend/docs)
- [ ] Frontend accessible et fonctionnel
- [ ] Connexion front-back fonctionne
- [ ] Cron jobs exécutent avec succès
- [ ] Données se mettent à jour automatiquement

---

## 🎉 Félicitations!

Une fois ces étapes complétées, ton système sera **100% automatique**:
- Données mises à jour quotidiennement
- Prédictions générées automatiquement
- Aucune intervention manuelle nécessaire
- 0€ de coût mensuel

**Bon déploiement! 🚀**

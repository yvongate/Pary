# Guide de Déploiement sur Railway

## 🚀 Backend FastAPI sur Railway

Railway est **plus simple et rapide** que Render, avec moins de limitations sur le plan gratuit.

---

## ✅ Avantages de Railway

- ✅ **Pas de cold start** (service toujours actif)
- ✅ **Déploiement en 2 minutes**
- ✅ **$5 de crédit gratuit/mois** (~500h d'utilisation)
- ✅ **Build automatique** depuis GitHub
- ✅ **Dashboard simple et clair**
- ✅ **Logs en temps réel**
- ✅ **Variables d'environnement faciles**

---

## 📋 Étape 1: Créer un Compte Railway

1. Aller sur **https://railway.app**
2. Cliquer sur **"Login"** ou **"Start a New Project"**
3. Se connecter avec **GitHub** (recommandé)
   - Railway aura accès à tes repositories
4. Confirmer l'autorisation GitHub

---

## 🚂 Étape 2: Déployer le Backend

### 2.1 Créer un Nouveau Projet

1. Dans le dashboard Railway, cliquer sur **"New Project"**
2. Sélectionner **"Deploy from GitHub repo"**
3. Choisir le repository **"yvongate/Pary"**
   - Si tu ne le vois pas, cliquer sur "Configure GitHub App" pour donner accès

### 2.2 Configuration Automatique

Railway va **automatiquement détecter**:
- ✅ Langage: Python
- ✅ Fichier: `requirements.txt`
- ✅ Type: Web Service

**Important:** Railway détecte automatiquement le `backend_clean` comme root directory si tu as bien le `railway.json` dedans!

### 2.3 Configuration du Service

Si Railway demande des détails:

```
Service Name: pary-backend
Root Directory: backend_clean (détecté automatiquement)
Build Command: (automatique - pip install)
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Note:** Le `Procfile` et `railway.json` que j'ai créés gèrent déjà tout ça!

---

## 🔐 Étape 3: Configurer les Variables d'Environnement

### 3.1 Accéder aux Variables

1. Dans ton projet Railway, cliquer sur le service **"pary-backend"**
2. Aller dans l'onglet **"Variables"**

### 3.2 Ajouter les Variables

Cliquer sur **"+ New Variable"** et ajouter:

```env
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_KEY=votre-clé-service-role
DEEPINFRA_API_KEY=votre-clé-deepinfra
AUTOMATION_API_KEY=générer-une-clé-aléatoire
```

**Pour générer AUTOMATION_API_KEY:**
```bash
# Option 1: OpenSSL
openssl rand -hex 32

# Option 2: Python
python -c "import secrets; print(secrets.token_hex(32))"

# Option 3: Générateur en ligne
# https://www.uuidgenerator.net/
```

### 3.3 Sauvegarder

Railway **redéploie automatiquement** après chaque changement de variable!

---

## 🎯 Étape 4: Déploiement

### 4.1 Attendre le Build

Railway va:
1. ✅ Cloner ton repository
2. ✅ Installer les dépendances (`pip install -r requirements.txt`)
3. ✅ Démarrer le service (`uvicorn main:app...`)

**Durée:** ~2-4 minutes

### 4.2 Suivre les Logs

Dans l'onglet **"Deployments"**, cliquer sur le dernier déploiement pour voir:
- Logs de build
- Logs de démarrage
- Logs runtime

**Rechercher dans les logs:**
```
✅ Application startup complete
✅ Uvicorn running on http://0.0.0.0:XXXX
```

### 4.3 Obtenir l'URL

1. Dans ton service, aller dans l'onglet **"Settings"**
2. Section **"Networking"** → **"Public Networking"**
3. Cliquer sur **"Generate Domain"**

Railway génère une URL automatique:
```
https://pary-backend-production-XXXX.up.railway.app
```

**Noter cette URL!** Tu en auras besoin pour le frontend et Cron-job.org.

---

## ✅ Étape 5: Vérifier le Déploiement

### 5.1 Tester l'API

```bash
# Health check
curl https://pary-backend-production-XXXX.up.railway.app/

# Documentation interactive
# Ouvrir dans un navigateur:
https://pary-backend-production-XXXX.up.railway.app/docs

# Tester l'automatisation
curl https://pary-backend-production-XXXX.up.railway.app/automation/status
```

### 5.2 Vérifier les Endpoints

Dans `/docs`, tester:
- ✅ `GET /` - Root endpoint
- ✅ `GET /leagues` - Liste des championnats
- ✅ `GET /fixtures` - Fixtures
- ✅ `GET /automation/status` - Statut automatisation

---

## 🔄 Étape 6: Redéploiement Automatique

Railway redéploie **automatiquement** à chaque:
- Push sur GitHub (branche `main` ou `master`)
- Changement de variable d'environnement

**Pour désactiver (optionnel):**
1. Settings → "Service"
2. Désactiver "Auto Deploy"

---

## 📊 Étape 7: Monitoring

### 7.1 Dashboard Railway

Le dashboard montre en temps réel:
- 🟢 CPU Usage
- 🟢 Memory Usage
- 🟢 Network I/O
- 🟢 Deployment Status

### 7.2 Logs

Onglet **"Deployments"** → Cliquer sur un déploiement → **"View Logs"**

**Filtres disponibles:**
- Build logs
- Deploy logs
- Application logs

### 7.3 Métriques

Onglet **"Metrics"** pour voir:
- Utilisation CPU/RAM sur 24h
- Requêtes réseau
- Temps de réponse

---

## 💰 Plan Gratuit Railway

### Crédits Gratuits

**$5 de crédit gratuit/mois**, ce qui donne environ:
- ~500 heures d'utilisation (si ton service utilise peu de RAM)
- Largement suffisant pour un projet comme le tien!

### Calcul de la Consommation

Railway charge basé sur:
- **RAM utilisée** (par GB par heure)
- **CPU** (par vCPU par heure)

**Exemple pour ton backend:**
- RAM: ~200-300MB
- CPU: Faible (sauf pendant génération prédictions)
- **Coût estimé:** ~$2-3/mois (bien en dessous du crédit gratuit!)

### Upgrade si Nécessaire

Si tu dépasses $5/mois:
- **Hobby Plan:** $5/mois minimum
- Pas de limite de crédit
- Facturation à l'utilisation

---

## 🔐 Sécurité

### HTTPS Automatique

Railway fournit **automatiquement HTTPS** pour tous les domaines.

### Variables d'Environnement

Les variables sont **chiffrées** et sécurisées.
- Jamais exposées dans les logs
- Jamais dans le code source

### API Key pour Automatisation

Protège tes endpoints d'automatisation avec la clé API.

**Dans le code (déjà dans `main.py`):**
```python
# L'API key est vérifiée automatiquement si AUTOMATION_API_KEY est configuré
```

**Dans Cron-job.org:**
```
Header: X-API-Key: ta-clé-AUTOMATION_API_KEY
```

---

## 🐛 Dépannage

### Problème: Build échoue

**Erreur: "No module named 'xyz'"**

**Solution:**
```bash
# Localement, regénérer requirements.txt
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements"
git push
```

### Problème: Service ne démarre pas

**Vérifier les logs:**
1. Deployments → Latest → View Logs
2. Chercher les erreurs Python

**Erreurs communes:**
- Port incorrect (doit utiliser `$PORT`)
- Variable d'environnement manquante
- Import manquant

### Problème: 502 Bad Gateway

**Causes:**
- Service n'a pas démarré
- Port incorrect
- Crash au démarrage

**Solution:**
1. Vérifier les logs de démarrage
2. Vérifier que `uvicorn` utilise `--port $PORT`
3. Tester localement: `uvicorn main:app --port 8000`

### Problème: Variables d'environnement ne fonctionnent pas

**Solution:**
1. Vérifier l'orthographe des noms de variables
2. Redéployer après avoir ajouté les variables
3. Vérifier dans les logs que les variables sont chargées

---

## 🔧 Configuration Avancée

### Custom Domain (Optionnel)

Si tu as un domaine personnalisé:

1. Settings → Networking → Custom Domain
2. Ajouter ton domaine (ex: `api.pary.com`)
3. Configurer le DNS:
   ```
   Type: CNAME
   Name: api
   Value: pary-backend-production-XXXX.up.railway.app
   ```

### Base de Données PostgreSQL (Optionnel)

Si tu veux remplacer SQLite par PostgreSQL:

1. Dans ton projet, cliquer sur **"+ New"**
2. Sélectionner **"Database" → "PostgreSQL"**
3. Railway crée automatiquement la variable `DATABASE_URL`
4. Utiliser cette URL dans ton code

---

## 📝 Checklist de Déploiement Railway

### Compte et Projet
- [ ] Compte Railway créé
- [ ] GitHub connecté
- [ ] Repository `yvongate/Pary` accessible

### Configuration Service
- [ ] Nouveau projet créé
- [ ] Repository déployé
- [ ] Service détecté comme Python ✓
- [ ] `railway.json` et `Procfile` présents ✓

### Variables d'Environnement
- [ ] SUPABASE_URL configurée
- [ ] SUPABASE_KEY configurée
- [ ] DEEPINFRA_API_KEY configurée
- [ ] AUTOMATION_API_KEY générée et configurée

### Déploiement
- [ ] Build réussi (Deployments → Latest → Success)
- [ ] Service démarré (logs montrent "Application startup complete")
- [ ] Domaine généré (Settings → Networking)
- [ ] URL notée: ___________________________________

### Tests
- [ ] `curl https://ton-url/` fonctionne
- [ ] `/docs` accessible dans le navigateur
- [ ] `/automation/status` retourne un JSON
- [ ] `/leagues` retourne la liste des championnats

---

## 🎯 Prochaine Étape

Une fois le backend déployé sur Railway:

1. **Noter l'URL Railway:**
   ```
   https://pary-backend-production-XXXX.up.railway.app
   ```

2. **Configurer le Frontend Vercel:**
   - Variable: `NEXT_PUBLIC_API_URL`
   - Valeur: L'URL Railway notée ci-dessus

3. **Configurer Cron-job.org:**
   - Utiliser l'URL Railway pour tous les jobs
   - Ajouter le header `X-API-Key`

**Voir:** `front/my-app/VERCEL_DEPLOY.md` pour déployer le frontend

---

## 🎉 Avantages de Railway vs Render

| Fonctionnalité | Railway | Render Free |
|----------------|---------|-------------|
| **Cold Start** | ❌ Non | ✅ Oui (15min) |
| **Crédits/mois** | $5 (~500h) | 750h |
| **Build Speed** | ⚡ Rapide | 🐢 Lent |
| **Dashboard** | 🎨 Simple | 😕 Complexe |
| **Logs** | ✅ Temps réel | ⚠️ Limités |
| **Auto-redéploiement** | ✅ Instant | ⚠️ Lent |

**Railway est généralement meilleur pour un projet comme le tien!**

---

## 🚀 C'est Parti!

1. Va sur https://railway.app
2. Login avec GitHub
3. "New Project" → "Deploy from GitHub"
4. Sélectionner `yvongate/Pary`
5. Ajouter les variables d'environnement
6. Attendre 2-3 minutes
7. C'est déployé! 🎉

**Besoin d'aide?** Railway a une excellente documentation: https://docs.railway.app

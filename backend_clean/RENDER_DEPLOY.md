# Guide de Déploiement sur Render

## 🚀 Backend FastAPI sur Render

### Étape 1: Créer un Compte Render

1. Aller sur https://render.com
2. Cliquer sur **"Get Started"**
3. Se connecter avec GitHub (recommandé) ou email

### Étape 2: Déployer le Backend

1. Dans le dashboard Render, cliquer sur **"New +"** → **"Web Service"**

2. **Connecter le Repository GitHub:**
   - Sélectionner le repository `yvongate/Pary`
   - Ou coller l'URL: https://github.com/yvongate/Pary

3. **Configuration du Service:**
   ```
   Name: pary-backend
   Region: Frankfurt (EU Central) - le plus proche
   Branch: main
   Root Directory: backend_clean
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

4. **Instance Type:**
   - Sélectionner: **Free** (pour commencer)
   - RAM: 512MB
   - Note: Le service gratuit s'arrête après 15min d'inactivité

5. **Variables d'Environnement:**

   Cliquer sur **"Advanced"** → **"Add Environment Variable"**

   Ajouter:
   ```
   SUPABASE_URL = https://votre-projet.supabase.co
   SUPABASE_KEY = votre-clé-service-role
   DEEPINFRA_API_KEY = votre-clé-deepinfra
   AUTOMATION_API_KEY = générer avec: openssl rand -hex 32
   ```

6. **Cliquer sur "Create Web Service"**

### Étape 3: Vérifier le Déploiement

Une fois déployé, Render fournira une URL:
```
https://pary-backend.onrender.com
```

Tester:
```bash
# Health check
curl https://pary-backend.onrender.com/

# Vérifier les endpoints
curl https://pary-backend.onrender.com/docs
curl https://pary-backend.onrender.com/automation/status
```

### Étape 4: Configuration Automatique des Redéploiements

Render redéploie automatiquement quand tu push sur GitHub!

**Désactiver le redéploiement auto (optionnel):**
- Settings → "Auto-Deploy" → Désactiver

### Étape 5: Configurer le Frontend

Une fois le backend déployé, noter l'URL et configurer le frontend:

Dans `front/my-app/.env.local`:
```env
NEXT_PUBLIC_API_URL=https://pary-backend.onrender.com
```

---

## ⚠️ Important - Plan Gratuit Render

**Limites:**
- ✅ 750 heures/mois gratuites
- ⚠️ Le service s'arrête après 15min d'inactivité
- ⚠️ Premier démarrage après inactivité: ~30-60 secondes (cold start)
- ✅ Redémarrage automatique quand requis

**Solutions pour éviter le cold start:**

### Option 1: Cron-job.org Health Check
Dans ton cron job de health check (toutes les 6h):
```
URL: https://pary-backend.onrender.com/automation/status
Fréquence: 0,6,12,18 * * *
```
Cela garde le service actif pendant la journée.

### Option 2: Upgrade vers Paid Plan
- Starter Plan: $7/mois
- Pas de cold start
- Service toujours actif
- Plus de RAM

---

## 🔧 Dépannage

### Problème: Build échoue

**Solution 1: Vérifier requirements.txt**
```bash
# Localement, générer un requirements.txt propre
pip freeze > requirements.txt
```

**Solution 2: Spécifier Python 3.11**
Dans les variables d'environnement:
```
PYTHON_VERSION = 3.11
```

### Problème: Service ne démarre pas

**Vérifier les logs:**
- Dashboard Render → Ton service → Onglet "Logs"

**Erreurs communes:**
- Port incorrect (doit utiliser `$PORT`)
- Variables d'environnement manquantes
- Dépendances Python manquantes

### Problème: Cold Start trop long

**Solution: Optimiser le démarrage**
1. Réduire les imports lourds
2. Lazy load des models ML
3. Utiliser health check réguliers (toutes les 10-15min)

---

## 📊 Monitoring

### Logs en Temps Réel
```bash
# Voir les logs live depuis le dashboard Render
Dashboard → pary-backend → Logs
```

### Métriques
Render fournit automatiquement:
- CPU usage
- Memory usage
- Request count
- Response times

---

## 🔐 Sécurité

### Variables d'Environnement

**IMPORTANT:** Ne jamais commiter les clés dans Git!

Les variables sont stockées de manière sécurisée dans Render.

### HTTPS

Render fournit automatiquement HTTPS avec certificat SSL gratuit.

### API Key pour Automation

Générer une clé sécurisée:
```bash
openssl rand -hex 32
```

Ajouter dans les variables d'environnement Render:
```
AUTOMATION_API_KEY = a3f5b8c9d2e4f1a6b7c8d9e0f1a2b3c4...
```

---

## 📝 Checklist de Déploiement

- [ ] Compte Render créé
- [ ] Repository GitHub connecté
- [ ] Service créé avec les bonnes configurations
- [ ] Variables d'environnement configurées
- [ ] Build réussi
- [ ] Service démarré avec succès
- [ ] URL backend notée
- [ ] Health check fonctionne
- [ ] Endpoints testés (/docs, /automation/status)
- [ ] Frontend configuré avec la nouvelle URL

---

## 🎯 Prochaine Étape

Une fois le backend déployé sur Render:
1. Noter l'URL: `https://pary-backend.onrender.com`
2. Configurer Vercel pour le frontend
3. Configurer Cron-job.org avec la nouvelle URL

**Voir:** `VERCEL_DEPLOY.md` pour déployer le frontend

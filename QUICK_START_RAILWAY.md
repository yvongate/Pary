# 🚀 Démarrage Rapide - Railway

Guide ultra-rapide pour déployer sur Railway en 5 minutes.

---

## ⚡ Étapes Rapides

### 1️⃣ Railway - Backend (2 minutes)

1. Va sur **https://railway.app**
2. "Login" avec GitHub
3. "New Project" → "Deploy from GitHub repo"
4. Sélectionne **"yvongate/Pary"**
5. Railway détecte automatiquement Python ✅
6. Ajoute ces variables (clic sur le service → Variables):
   ```
   SUPABASE_URL = https://xxx.supabase.co
   SUPABASE_KEY = xxx
   DEEPINFRA_API_KEY = xxx
   AUTOMATION_API_KEY = (générer: openssl rand -hex 32)
   ```
7. Settings → Networking → "Generate Domain"
8. **COPIE L'URL!** (ex: https://pary-backend-production-xxx.up.railway.app)

---

### 2️⃣ Vercel - Frontend (2 minutes)

1. Va sur **https://vercel.com**
2. "Sign Up" avec GitHub
3. "Add New..." → "Project"
4. Import **"yvongate/Pary"**
5. Configure:
   - Root Directory: `front/my-app`
   - Framework: Next.js (auto)
6. Ajoute la variable:
   ```
   NEXT_PUBLIC_API_URL = [URL Railway de l'étape 1]
   ```
7. "Deploy"
8. **COPIE L'URL!** (ex: https://pary-frontend.vercel.app)

---

### 3️⃣ Cron-job.org - Automatisation (1 minute)

1. Va sur **https://cron-job.org**
2. "Sign up" (email ou GitHub)
3. "Create cronjob"

**Job 1 - Update Data:**
```
Title: Update Data
URL: [URL Railway]/automation/update-data
Method: POST
Schedule: 0 8 * * * (08:00 quotidien)
Header: X-API-Key: [ta AUTOMATION_API_KEY]
```

**Job 2 - Generate Predictions:**
```
Title: Generate Predictions
URL: [URL Railway]/automation/generate-predictions?hours_ahead=48
Method: POST
Schedule: 0 10 * * * (10:00 quotidien)
Header: X-API-Key: [ta AUTOMATION_API_KEY]
```

**Job 3 - Health Check:**
```
Title: Health Check
URL: [URL Railway]/automation/status
Method: GET
Schedule: 0 */6 * * * (toutes les 6h)
```

---

## ✅ C'est Fini!

Ton système est maintenant **100% automatique**:
- 📥 Données mises à jour tous les jours à 08:00
- 🔮 Prédictions générées tous les jours à 10:00
- 💚 Health check toutes les 6h
- 💰 **Coût: 0€/mois**

---

## 🧪 Tester

### Backend
```bash
curl https://ton-url.up.railway.app/
curl https://ton-url.up.railway.app/docs
curl https://ton-url.up.railway.app/automation/status
```

### Frontend
Ouvre dans un navigateur: `https://ton-url.vercel.app`

### Cron Jobs
Dans Cron-job.org, clique sur "Run now" pour chaque job.

---

## 📚 Documentation Complète

- **Railway:** `backend_clean/RAILWAY_DEPLOY.md`
- **Vercel:** `front/my-app/VERCEL_DEPLOY.md`
- **Cron Jobs:** `backend_clean/CRONJOB_SETUP.md`
- **Checklist:** `DEPLOYMENT_CHECKLIST.md`

---

## 🆘 Problème?

### Backend ne démarre pas
→ Vérifie les logs dans Railway (Deployments → Latest → View Logs)

### Frontend ne charge pas
→ Vérifie que `NEXT_PUBLIC_API_URL` est bien configurée dans Vercel

### Cron job échoue
→ Vérifie que l'URL Railway est correcte et que l'API key est configurée

---

**Bon déploiement! 🎉**

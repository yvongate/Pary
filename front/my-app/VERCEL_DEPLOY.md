# Guide de Déploiement sur Vercel

## 🚀 Frontend Next.js sur Vercel

### Prérequis

Avoir déployé le backend sur Render et noté l'URL:
```
https://pary-backend.onrender.com
```

### Étape 1: Créer un Compte Vercel

1. Aller sur https://vercel.com
2. Cliquer sur **"Sign Up"**
3. Se connecter avec GitHub (recommandé)

### Étape 2: Importer le Projet

1. Dans le dashboard Vercel, cliquer sur **"Add New..." → "Project"**

2. **Importer depuis GitHub:**
   - Sélectionner le repository `yvongate/Pary`
   - Ou coller l'URL: https://github.com/yvongate/Pary

3. **Configuration du Projet:**
   ```
   Project Name: pary-frontend
   Framework Preset: Next.js (détecté automatiquement)
   Root Directory: front/my-app
   Build Command: npm run build (ou yarn build)
   Output Directory: .next
   Install Command: npm install (ou yarn install)
   ```

4. **Variables d'Environnement:**

   Dans la section **"Environment Variables"**, ajouter:

   ```
   Name: NEXT_PUBLIC_API_URL
   Value: https://pary-backend.onrender.com
   ```

   **IMPORTANT:** Remplacer par ta vraie URL backend depuis Render!

5. **Cliquer sur "Deploy"**

### Étape 3: Attendre le Déploiement

Vercel va:
1. Installer les dépendances (`npm install`)
2. Builder l'application (`npm run build`)
3. Déployer automatiquement

Durée: ~2-5 minutes

### Étape 4: Vérifier le Déploiement

Une fois déployé, Vercel fournira une URL:
```
https://pary-frontend.vercel.app
```

**Tester:**
1. Ouvrir l'URL dans le navigateur
2. Vérifier que la page d'accueil se charge
3. Vérifier que le calendrier de matchs fonctionne
4. Aller sur `/predictions` pour voir les prédictions

### Étape 5: Configuration du Domaine (Optionnel)

Si tu as un domaine personnalisé:

1. Dashboard Vercel → Ton projet → **"Settings"** → **"Domains"**
2. Ajouter ton domaine (ex: `pary.com`)
3. Suivre les instructions pour configurer les DNS

---

## ⚙️ Configuration Avancée

### Variables d'Environnement par Environment

Vercel permet de configurer différentes URLs pour:
- **Production:** `https://pary-backend.onrender.com`
- **Preview:** `https://pary-backend-dev.onrender.com` (si tu as un backend de dev)
- **Development:** `http://localhost:8000`

**Pour configurer:**
1. Settings → Environment Variables
2. Ajouter `NEXT_PUBLIC_API_URL`
3. Cocher les environnements appropriés (Production / Preview / Development)

### Redéploiement Automatique

Vercel redéploie automatiquement à chaque push sur GitHub!

**Pour désactiver (optionnel):**
1. Settings → Git
2. Désactiver "Automatic Deployments from Git"

### Preview Deployments

Vercel crée automatiquement des previews pour chaque Pull Request:
- URL unique pour chaque PR
- Parfait pour tester avant merge

---

## 🐛 Dépannage

### Problème: Build échoue

**Erreur commune: "Module not found"**

**Solution:**
Vérifier `package.json` et installer les dépendances manquantes:
```bash
cd front/my-app
npm install
npm run build  # Tester localement
```

### Problème: Page blanche après déploiement

**Causes possibles:**
1. Variable d'environnement `NEXT_PUBLIC_API_URL` manquante
2. Erreur dans le code (voir les logs Vercel)

**Solution:**
1. Vercel Dashboard → Ton projet → Settings → Environment Variables
2. Vérifier que `NEXT_PUBLIC_API_URL` est bien configurée
3. Redéployer: Deployments → Latest → ... → Redeploy

### Problème: Backend inaccessible (CORS)

**Symptômes:**
- Console browser: "CORS policy blocked"
- Requêtes API échouent

**Solution:**
Vérifier que le backend autorise le domaine Vercel dans les CORS.

Dans `backend_clean/main.py`, ajouter:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://pary-frontend.vercel.app",  # Ton domaine Vercel
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Problème: Variables d'environnement ne fonctionnent pas

**Important:** Les variables `NEXT_PUBLIC_*` doivent être définies au moment du build!

**Solution:**
1. Ajouter/modifier la variable dans Vercel Settings
2. Redéployer le projet (Deployments → Redeploy)

---

## 📊 Monitoring

### Analytics

Vercel fournit des analytics gratuits:
- Dashboard → Ton projet → Analytics
- Voir: Pageviews, Visitors, Top pages

### Logs

Voir les logs runtime:
- Dashboard → Ton projet → Deployments → [Latest] → Function Logs
- Utile pour débugger les erreurs

---

## 💰 Coût

### Plan Gratuit (Hobby)

**Limites:**
- ✅ Déploiements illimités
- ✅ 100GB bande passante/mois
- ✅ HTTPS automatique
- ✅ Preview deployments
- ⚠️ Limité à usage personnel (non commercial)

**Largement suffisant pour ton projet!**

### Plan Pro (si besoin)

- $20/mois par utilisateur
- Usage commercial autorisé
- 1TB bande passante
- Support prioritaire

---

## 🔐 Sécurité

### HTTPS

Vercel fournit automatiquement HTTPS avec certificat SSL gratuit.

### Variables d'Environnement

Les variables sont sécurisées et ne sont jamais exposées dans le code client (sauf `NEXT_PUBLIC_*`).

**IMPORTANT:** Les variables `NEXT_PUBLIC_*` sont exposées côté client!
- Ne jamais y mettre de clés secrètes
- Uniquement l'URL du backend (qui est publique de toute façon)

---

## 📝 Checklist de Déploiement

- [ ] Backend déployé sur Render et URL notée
- [ ] Compte Vercel créé
- [ ] Repository GitHub connecté
- [ ] Projet importé avec Root Directory = `front/my-app`
- [ ] Variable `NEXT_PUBLIC_API_URL` configurée
- [ ] Build réussi
- [ ] Application déployée
- [ ] URL Vercel notée
- [ ] Test de la page d'accueil ✓
- [ ] Test de la page `/predictions` ✓
- [ ] Calendrier de matchs fonctionne ✓
- [ ] Appels API au backend fonctionnent ✓

---

## 🎉 Prochaine Étape

Une fois le frontend déployé:
1. Noter l'URL: `https://pary-frontend.vercel.app`
2. Configurer Cron-job.org avec l'URL backend Render
3. Tester l'application complète en production!

**Voir:** `CRONJOB_SETUP.md` pour configurer l'automatisation

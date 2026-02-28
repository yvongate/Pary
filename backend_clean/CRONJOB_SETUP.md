# Guide de Configuration Cron-job.org

Guide pas-à-pas pour configurer l'automatisation complète avec Cron-job.org (gratuit)

---

## 🌐 Étape 1: Créer un Compte

### 1.1 Inscription

1. Aller sur **https://cron-job.org/en/**
2. Cliquer sur **"Sign up"**
3. Remplir le formulaire:
   - Email
   - Mot de passe
   - Nom (optionnel)
4. Cliquer sur **"Create account"**
5. Vérifier votre email et activer le compte

### 1.2 Connexion

- URL: https://console.cron-job.org/
- Email + mot de passe

---

## ⚙️ Étape 2: Configurer les Cron Jobs

### Job 1: Mise à Jour des Données (CSV + Fixtures)

**Objectif**: Télécharger les CSV historiques et fixtures chaque jour

#### Configuration

1. Dans le dashboard, cliquer sur **"Create cronjob"**

2. **Onglet "General"**:
   ```
   Title: ParY - Update Data
   Address: http://YOUR-DOMAIN.com/automation/update-data

   ⚠️ Remplacer YOUR-DOMAIN.com par votre vrai domaine
   Exemple: https://parY-backend.com/automation/update-data
   ```

3. **Onglet "Schedule"**:
   ```
   Schedule type: Advanced

   Minutes: 0
   Hours: 8
   Days: *
   Months: *
   Weekdays: *

   = Tous les jours à 08:00
   ```

4. **Onglet "Request"**:
   ```
   Request method: POST
   Request timeout: 60 seconds

   Headers (optionnel si sécurité activée):
   X-API-Key: votre-clé-secrète
   ```

5. **Onglet "Notifications"**:
   ```
   ✅ Email on failure
   Email: votre@email.com

   Failure triggers:
   ✅ HTTP status code != 200
   ✅ Execution timeout
   ```

6. Cliquer sur **"Create cronjob"**

---

### Job 2: Génération des Prédictions

**Objectif**: Générer les prédictions pour les matchs des prochaines 48h

#### Configuration

1. Cliquer sur **"Create cronjob"**

2. **Onglet "General"**:
   ```
   Title: ParY - Generate Predictions
   Address: http://YOUR-DOMAIN.com/automation/generate-predictions?hours_ahead=48
   ```

3. **Onglet "Schedule"**:
   ```
   Schedule type: Advanced

   Minutes: 0
   Hours: 10
   Days: *
   Months: *
   Weekdays: *

   = Tous les jours à 10:00
   ```

4. **Onglet "Request"**:
   ```
   Request method: POST
   Request timeout: 180 seconds  (3 minutes - génération peut être longue)

   Headers (optionnel):
   X-API-Key: votre-clé-secrète
   ```

5. **Onglet "Notifications"**:
   ```
   ✅ Email on failure
   Email: votre@email.com
   ```

6. Cliquer sur **"Create cronjob"**

---

### Job 3: Health Check (Optionnel)

**Objectif**: Vérifier que l'API fonctionne correctement

#### Configuration

1. Cliquer sur **"Create cronjob"**

2. **Onglet "General"**:
   ```
   Title: ParY - Health Check
   Address: http://YOUR-DOMAIN.com/automation/status
   ```

3. **Onglet "Schedule"**:
   ```
   Schedule type: Advanced

   Minutes: 0
   Hours: 0,6,12,18
   Days: *
   Months: *
   Weekdays: *

   = Toutes les 6 heures (00:00, 06:00, 12:00, 18:00)
   ```

4. **Onglet "Request"**:
   ```
   Request method: GET
   Request timeout: 30 seconds
   ```

5. **Onglet "Notifications"**:
   ```
   ✅ Email on failure
   ✅ Email on success (première fois seulement pour tester)
   Email: votre@email.com
   ```

6. Cliquer sur **"Create cronjob"**

---

## 🔐 Étape 3: Sécuriser (Recommandé)

### Option A: API Key (Simple et Efficace)

#### 3.1 Générer une clé

```bash
# Générer une clé aléatoire
openssl rand -hex 32
# Exemple: a3f5b8c9d2e4f1a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0
```

#### 3.2 Ajouter au backend

Dans `backend_clean/.env`:
```env
AUTOMATION_API_KEY=a3f5b8c9d2e4f1a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0
```

Dans `backend_clean/main.py`, ajouter au début:
```python
import os
from fastapi import Header, HTTPException

AUTOMATION_API_KEY = os.getenv('AUTOMATION_API_KEY')

def verify_automation_key(x_api_key: str = Header(None)):
    if not AUTOMATION_API_KEY:
        return  # Pas de vérification si pas de clé configurée

    if x_api_key != AUTOMATION_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

# Ajouter dependencies aux endpoints
@app.post("/automation/update-data", dependencies=[Depends(verify_automation_key)])
def automation_update_data():
    # ...
```

#### 3.3 Configurer dans Cron-job.org

Pour chaque job, dans **"Request" > "Headers"**:
```
X-API-Key: a3f5b8c9d2e4f1a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0
```

---

### Option B: IP Whitelist

Restreindre aux IPs de Cron-job.org (vérifier les IPs actuelles sur leur site).

---

## 📊 Étape 4: Vérifier le Fonctionnement

### 4.1 Test Manuel

Avant de lancer automatiquement, tester manuellement:

```bash
# Depuis un terminal ou Postman
curl -X POST http://YOUR-DOMAIN.com/automation/update-data

# Avec API key
curl -X POST http://YOUR-DOMAIN.com/automation/update-data \
  -H "X-API-Key: votre-clé"
```

### 4.2 Exécution Manuelle dans Cron-job.org

1. Aller dans **"Cronjobs"**
2. Cliquer sur le job
3. Cliquer sur **"Run now"** (bouton Play ▶️)
4. Attendre l'exécution
5. Vérifier le résultat dans **"Execution log"**

### 4.3 Vérifier les Logs

Dans chaque job:
- Onglet **"Execution log"**
- Voir:
  - Timestamp
  - Duration
  - Status code (doit être 200)
  - Response body

### 4.4 Vérifier les Données

Après exécution:

```bash
# Vérifier que les CSV sont à jour
ls -lh backend_clean/data/*.csv

# Vérifier la date de modification
stat backend_clean/data/E0_2526.csv

# Vérifier le statut API
curl http://YOUR-DOMAIN.com/automation/status
```

---

## 📅 Planning Final

Une fois configuré, voici ce qui se passera automatiquement:

```
00:00 - Health Check ✓
06:00 - Health Check ✓
08:00 - 📥 Mise à jour CSV + Fixtures (15-30s)
10:00 - 🔮 Génération prédictions (60-180s selon nb matchs)
12:00 - Health Check ✓
18:00 - Health Check ✓
```

---

## 🐛 Dépannage

### Problème: Job échoue (Status != 200)

**Solutions**:
1. Vérifier que le backend est en ligne
2. Tester l'endpoint manuellement
3. Vérifier les logs du backend
4. Vérifier l'API key si configurée

### Problème: Timeout

**Solutions**:
1. Augmenter le timeout dans Cron-job.org
2. Optimiser le code backend
3. Vérifier que le serveur répond rapidement

### Problème: Pas de notification email

**Solutions**:
1. Vérifier l'adresse email dans le profil
2. Vérifier les spams
3. Activer les notifications dans les paramètres du job

### Problème: Données pas mises à jour

**Solutions**:
1. Vérifier les logs d'exécution
2. Vérifier que football-data.co.uk est accessible
3. Vérifier les permissions d'écriture dans `data/`
4. Tester le script manuellement: `python automation/update_csv.py`

---

## 🎯 Checklist Complète

### Pré-requis
- [ ] Backend déployé en production
- [ ] URL publique accessible (http://votre-domaine.com)
- [ ] Tests manuels des endpoints réussis

### Configuration Cron-job.org
- [ ] Compte créé et vérifié
- [ ] Job 1: Update Data configuré (08:00)
- [ ] Job 2: Generate Predictions configuré (10:00)
- [ ] Job 3: Health Check configuré (toutes les 6h)
- [ ] API Key configurée (si sécurité activée)
- [ ] Email notifications activées

### Tests
- [ ] Exécution manuelle de chaque job réussie
- [ ] Logs montrent status 200
- [ ] CSV mis à jour dans `data/`
- [ ] Prédictions générées dans la base
- [ ] Email de notification reçu (test)

### Monitoring
- [ ] Dashboard Cron-job.org vérifié quotidiennement
- [ ] Alertes email configurées
- [ ] Backup des données configuré (optionnel)

---

## 📞 Support

### Cron-job.org
- Documentation: https://cron-job.org/en/documentation/
- Support: https://cron-job.org/en/support/

### Limites du Plan Gratuit
- ✅ Cron jobs illimités
- ✅ Exécutions illimitées
- ✅ Historique 25 dernières exécutions
- ✅ Email notifications
- ⚠️ Timeout max: 30 secondes (HTTP) ou 120 secondes (HTTPS)

### Upgrade Pro (Optionnel)
Si besoin de:
- Timeout plus long
- Plus d'historique
- Monitoring avancé
- Support prioritaire

Prix: ~3-5€/mois

---

**Votre système est maintenant entièrement automatisé! 🎉**

Toutes les données se mettront à jour automatiquement chaque jour sans aucune intervention manuelle.

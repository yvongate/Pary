# Système d'Automatisation - ParY Backend

**Automatisation complète des mises à jour de données**

---

## 📋 Vue d'Ensemble

Le système automatise 3 tâches principales:

| Tâche | Fréquence | Heure | Endpoint |
|-------|-----------|-------|----------|
| 1️⃣ Mise à jour CSV | 1x/jour | 08:00 | `/automation/update-data` |
| 2️⃣ Génération prédictions | 1x/jour | 10:00 | `/automation/generate-predictions` |
| 3️⃣ Vérification statut | 4x/jour | 00:00, 06:00, 12:00, 18:00 | `/automation/status` |

---

## 🔧 Composants du Système

### 1. Scripts Python

**`automation/update_csv.py`**
- Télécharge les CSV historiques (football-data.co.uk)
- Met à jour fixtures.csv
- Sauvegarde dans `data/`

**`automation/generate_predictions.py`**
- Récupère les matchs des prochaines 48h
- Génère les prédictions automatiquement
- Sauvegarde dans SQLite + Supabase

### 2. Endpoints API

**POST `/automation/update-data`**
```bash
curl -X POST http://your-domain.com/automation/update-data
```

Réponse:
```json
{
  "success": true,
  "timestamp": "2026-02-26T08:00:00",
  "duration_seconds": 15.3,
  "historical": {
    "total": 16,
    "success": 16,
    "failed": 0
  },
  "fixtures": {
    "success": true
  }
}
```

---

**POST `/automation/generate-predictions`**
```bash
curl -X POST "http://your-domain.com/automation/generate-predictions?hours_ahead=48"
```

Réponse:
```json
{
  "success": true,
  "timestamp": "2026-02-26T10:00:00",
  "duration_seconds": 120.5,
  "total_matches": 15,
  "predictions_generated": 14,
  "predictions_failed": 1
}
```

---

**GET `/automation/status`**
```bash
curl http://your-domain.com/automation/status
```

Réponse:
```json
{
  "timestamp": "2026-02-26T12:00:00",
  "api": "OK",
  "data_files": {
    "E0_2526.csv": {
      "exists": true,
      "size": 125000,
      "last_modified": "2026-02-26T08:00:15"
    },
    "fixtures.csv": {
      "exists": true,
      "size": 45000,
      "last_modified": "2026-02-26T08:00:20"
    }
  },
  "database": {
    "sqlite": {
      "connected": true,
      "total_predictions": 142
    }
  }
}
```

---

## 🌐 Configuration Cron-job.org

### Étape 1: Créer un Compte

1. Aller sur https://cron-job.org
2. S'inscrire (gratuit)
3. Vérifier l'email

### Étape 2: Ajouter les Cron Jobs

#### Job 1: Mise à jour des données (CSV + Fixtures)

```
Titre: ParY - Update Data
URL: http://YOUR-DOMAIN.com/automation/update-data
Méthode: POST
Planification: Tous les jours à 08:00 (Europe/Paris)
Timeout: 60 secondes
```

Configuration détaillée:
```
Minutes: 0
Heures: 8
Jours: *
Mois: *
Jours de la semaine: *
```

---

#### Job 2: Génération des prédictions

```
Titre: ParY - Generate Predictions
URL: http://YOUR-DOMAIN.com/automation/generate-predictions?hours_ahead=48
Méthode: POST
Planification: Tous les jours à 10:00 (Europe/Paris)
Timeout: 180 secondes
```

Configuration détaillée:
```
Minutes: 0
Heures: 10
Jours: *
Mois: *
Jours de la semaine: *
```

---

#### Job 3: Vérification statut (Optionnel)

```
Titre: ParY - Health Check
URL: http://YOUR-DOMAIN.com/automation/status
Méthode: GET
Planification: Toutes les 6 heures
Timeout: 30 secondes
Notifications: Activer (email si échec)
```

Configuration détaillée:
```
Minutes: 0
Heures: 0,6,12,18
Jours: *
Mois: *
Jours de la semaine: *
```

---

## 🔐 Sécurité (Optionnel mais Recommandé)

### Option 1: IP Whitelist

Restreindre l'accès aux endpoints d'automatisation aux IPs de Cron-job.org.

Ajouter dans `main.py`:
```python
from fastapi import Request, HTTPException

ALLOWED_IPS = [
    "88.99.180.160",  # IP exemple de Cron-job.org
    # Ajouter les IPs de Cron-job.org
]

def check_ip(request: Request):
    client_ip = request.client.host
    if client_ip not in ALLOWED_IPS:
        raise HTTPException(status_code=403, detail="Forbidden")

@app.post("/automation/update-data", dependencies=[Depends(check_ip)])
def automation_update_data():
    # ...
```

### Option 2: API Key

Ajouter une clé API dans les headers:

```python
from fastapi import Header, HTTPException

API_KEY = "your-secret-key-here"

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

@app.post("/automation/update-data", dependencies=[Depends(verify_api_key)])
def automation_update_data():
    # ...
```

Configuration Cron-job.org:
```
Headers:
X-API-Key: your-secret-key-here
```

---

## 📊 Monitoring

### Logs d'Exécution

Cron-job.org garde l'historique de chaque exécution:
- Timestamp
- Durée
- Status code
- Réponse

### Email Notifications

Configurer des alertes email en cas de:
- Échec (status code != 200)
- Timeout
- Erreur réseau

### Dashboard Cron-job.org

Interface web pour:
- Voir l'historique complet
- Activer/désactiver les jobs
- Modifier la planification
- Voir les statistiques

---

## 🧪 Tests Manuels

### Test 1: Mise à jour des données

```bash
curl -X POST http://localhost:8000/automation/update-data
```

Vérifier:
- Les CSV dans `data/` sont mis à jour
- La réponse indique `success: true`

### Test 2: Génération prédictions

```bash
curl -X POST "http://localhost:8000/automation/generate-predictions?hours_ahead=48"
```

Vérifier:
- Des prédictions sont créées dans la DB
- La réponse indique le nombre généré

### Test 3: Statut

```bash
curl http://localhost:8000/automation/status
```

Vérifier:
- Tous les fichiers CSV existent
- La base de données est connectée

---

## 🚀 Déploiement

### Avant de Configurer Cron-job.org

1. ✅ Déployer le backend en production
2. ✅ Vérifier que l'API est accessible publiquement
3. ✅ Tester les endpoints manuellement
4. ✅ (Optionnel) Configurer la sécurité (API key ou IP whitelist)

### Après Configuration

1. ⏰ Attendre la première exécution automatique
2. 📊 Vérifier les logs dans Cron-job.org
3. ✅ Confirmer que les données sont mises à jour
4. 📧 Configurer les alertes email

---

## 📅 Planning Quotidien

```
00:00 - Health Check
06:00 - Health Check
08:00 - Mise à jour CSV + Fixtures ⭐
10:00 - Génération prédictions ⭐
12:00 - Health Check
18:00 - Health Check
```

---

## ❓ FAQ

### Les CSV ne se mettent pas à jour?

Vérifier:
1. football-data.co.uk est accessible
2. Les permissions d'écriture dans `data/`
3. Les logs dans Cron-job.org

### Les prédictions ne sont pas générées?

Vérifier:
1. Il y a des matchs dans fixtures.csv
2. Les matchs sont dans les prochaines 48h
3. Les classements soccerstats sont accessibles

### Comment voir les logs?

Dans Cron-job.org:
1. Aller dans "Cronjobs"
2. Cliquer sur le job
3. Voir "Execution log"

---

## 🔄 Maintenance

### Mise à Jour de Saison

Quand la nouvelle saison commence (août):

1. Mettre à jour les URLs dans `automation/update_csv.py`:
```python
CSV_URLS = {
    'E0': 'https://www.football-data.co.uk/mmz4281/2627/E0.csv',  # 2026-2027
    # ...
}
```

2. Redéployer le backend
3. Les cron jobs continueront automatiquement

### Nettoyage

Mensuel:
- Supprimer les vieilles prédictions (matchs joués > 30 jours)
- Vérifier l'espace disque

---

## ✅ Checklist de Configuration

- [ ] Backend déployé en production
- [ ] Compte Cron-job.org créé
- [ ] Job 1 configuré (Update Data - 08:00)
- [ ] Job 2 configuré (Generate Predictions - 10:00)
- [ ] Job 3 configuré (Health Check - toutes les 6h)
- [ ] Première exécution testée
- [ ] Alertes email configurées
- [ ] Sécurité activée (API key ou IP whitelist)

---

**Système d'automatisation prêt! 🤖**

Le backend se mettra à jour automatiquement chaque jour sans intervention manuelle.

# Supabase - État de la Connexion

## ✅ Connexion Opérationnelle

**Testé le**: 25/02/2026
**Status**: ACTIF - 100% FONCTIONNEL

---

## Configuration

### Base de données
- **Type**: PostgreSQL
- **Hébergeur**: Supabase
- **Host**: db.qibilvupnrqyxsoxpbze.supabase.co
- **Port**: 5432
- **Database**: postgres

### Fichier de configuration
`backend_clean/services/supabase_client.py`

---

## ✅ Correction Effectuée (25/02/2026)

La table `analysis_logs` a été corrigée avec succès:
- ✅ Colonnes `step_name` et `execution_time_ms` ajoutées
- ✅ Anciennes colonnes rendues optionnelles
- ✅ Tests d'insertion réussis (4 logs créés)
- ✅ Temps total de logging: 60.7s pour 4 étapes

## Tables Disponibles (4)

### 1. `match_predictions`
Stocke toutes les prédictions de matchs.

**Colonnes principales**:
- `id` - ID auto-incrémenté
- `match_id` - ID unique du match (clé)
- `home_team`, `away_team` - Équipes
- `league_code` - Championnat (E0, SP1, I1, F1, D1)
- `match_date` - Date du match
- `shots_min`, `shots_max`, `shots_confidence` - Prédiction tirs
- `corners_min`, `corners_max`, `corners_confidence` - Prédiction corners
- `analysis_shots`, `analysis_corners` - Détails analyse (JSON)
- `ai_reasoning_shots`, `ai_reasoning_corners` - Raisonnement IA
- `home_formation`, `away_formation` - Formations
- `weather` - Météo (JSON)
- `rankings_used` - Classements utilisés (JSON)
- `is_valid` - Validité de la prédiction
- `created_at`, `updated_at` - Timestamps

**Contrainte**: UNIQUE sur `match_id` (mise à jour automatique si existe)

### 2. `upcoming_predictions`
Vue des prédictions à venir (matchs futurs uniquement).

### 3. `prediction_stats`
Statistiques sur les prédictions.

### 4. `analysis_logs`
Logs des étapes d'analyse pour chaque match.

---

## Tests Réussis

### Test 1: Connexion
- [x] Connexion établie
- [x] Authentication réussie

### Test 2: Tables
- [x] 4 tables trouvées
- [x] Schéma accessible

### Test 3: Insertion
- [x] Prédiction insérée (ID: 88)
- [x] Données JSON correctement stockées
- [x] UPSERT fonctionne (ON CONFLICT)

### Test 4: Récupération
- [x] Prédiction récupérée par match_id
- [x] Données intactes (tirs: 20-35, corners: 7-12)

### Test 5: Comptage
- [x] 27 prédictions en base
- [x] Requêtes COUNT fonctionnelles

### Test 6: Prédictions à venir
- [x] Vue `upcoming_predictions` accessible
- [x] 1 prédiction à venir trouvée

---

## Opérations Disponibles

### Insertion/Mise à jour
```python
from services.supabase_client import SupabaseClient

client = SupabaseClient()
client.connect()

prediction_data = {
    'match_id': 'E0_2026_02_27_Everton_ManUnited',
    'home_team': 'Everton',
    'away_team': 'Man United',
    'league_code': 'E0',
    'match_date': datetime(2026, 2, 27, 15, 0),
    'shots_min': 20,
    'shots_max': 35,
    'shots_confidence': 0.83,
    # ... autres champs
}

pred_id = client.insert_prediction(prediction_data)
client.disconnect()
```

### Récupération
```python
# Par match_id
pred = client.get_prediction_by_match_id('E0_2026_02_27_Everton_ManUnited')

# Prédictions à venir
upcoming = client.get_upcoming_predictions(league_code='E0', limit=10)
```

### Invalidation
```python
# Invalider une prédiction (compositions changées)
client.invalidate_prediction('E0_2026_02_27_Everton_ManUnited')
```

### Logs d'analyse
```python
# Logger une étape
client.log_analysis_step(
    match_id='E0_2026_02_27_Everton_ManUnited',
    step_number=1,
    step_name='Scraping classements',
    step_result='12 tables récupérées',
    execution_time_ms=5230
)
```

---

## Utilisation dans l'API

### Endpoint actuel: SQLite (local)
L'API utilise actuellement SQLite pour le stockage local des prédictions.

**Fichier**: `services/sqlite_database_service.py`

### Migration vers Supabase (optionnel)

Pour utiliser Supabase au lieu de SQLite:

1. Modifier `main.py`:
```python
# Remplacer
from services.sqlite_database_service import SQLiteDatabaseService
db = SQLiteDatabaseService()

# Par
from services.supabase_client import SupabaseClient
db = SupabaseClient()
db.connect()
```

2. Avantages:
   - Base centralisée (accessible depuis plusieurs serveurs)
   - Sauvegarde automatique
   - Scalabilité PostgreSQL
   - Vues SQL complexes

3. Inconvénients:
   - Dépendance à la connexion Internet
   - Latence réseau (~100-200ms)
   - Coût hébergement (gratuit jusqu'à 500MB)

---

## Sécurité

### ⚠️ Amélioration recommandée

Actuellement, le mot de passe est en dur dans le code:
```python
# À ÉVITER (ligne 18 de supabase_client.py)
self.connection_string = "postgresql://postgres:voicilemotdepassedepary@..."
```

**Recommandation**: Utiliser les variables d'environnement:

```python
# .env
SUPABASE_URL=postgresql://postgres:PASSWORD@db.qibilvupnrqyxsoxpbze.supabase.co:5432/postgres

# supabase_client.py
import os
from dotenv import load_dotenv

load_dotenv()

self.connection_string = os.getenv('SUPABASE_URL')
```

---

## Performance

- **Connexion**: ~200-300ms
- **Insertion**: ~150-250ms
- **Requête simple**: ~100-200ms
- **Requête complexe**: ~300-500ms

**Total overhead vs SQLite**: +200-400ms par opération

---

## Conclusion

✅ **Supabase est opérationnel et prêt pour production**

- Connexion stable
- Toutes les opérations fonctionnent
- 27 prédictions déjà en base
- Tables bien structurées
- Possibilité de migrer depuis SQLite si besoin

**Recommandation**: Continuer avec SQLite pour développement local, utiliser Supabase pour production distribuée.

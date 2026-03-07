# Déploiement Railway - Instructions

## Variables d'environnement à configurer

Aller dans **Settings > Variables** sur Railway et ajouter:

### Bright Data Browser API
```
BRIGHTDATA_CUSTOMER_ID=your_customer_id_here
BRIGHTDATA_BROWSER_API_ZONE=your_zone_name
BRIGHTDATA_BROWSER_API_PASSWORD=your_password_here
```

### Anthropic Claude API
```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### OpenWeather API
```
OPENWEATHER_API_KEY=your_openweather_api_key_here
```

### Optionnel (à retirer si présent)
```
# Ces variables ne sont plus utilisées:
SERPAPI_KEY (remplacé par Bright Data)
DEEPINFRA_API_KEY (remplacé par Anthropic)
```

---

## Installation de Playwright sur Railway

Railway installera automatiquement `playwright` via `requirements.txt`, mais il faut aussi installer les browsers.

### Option 1: Ajouter un build script (RECOMMANDÉ)

Créer un fichier `railway.json` à la racine:
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "playwright install chromium && uvicorn main:app --host 0.0.0.0 --port $PORT"
  }
}
```

### Option 2: Modifier le Procfile

Si vous utilisez un `Procfile`, modifier:
```
web: playwright install chromium && uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Option 3: Script de démarrage

Créer `start.sh`:
```bash
#!/bin/bash
playwright install chromium
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Puis dans Railway Settings > Deploy:
```
Start Command: bash start.sh
```

---

## Vérification du déploiement

1. **Vérifier les logs** après le déploiement:
   - Chercher "Playwright Chromium installed" ou similaire
   - Pas d'erreurs sur `google_formation_scraper`

2. **Tester l'endpoint** `/predict`:
   ```bash
   curl https://votre-app.railway.app/predict
   ```

3. **Vérifier les formations**:
   - Les logs doivent afficher `[Formation Scraper] OK`
   - Pas de message "ERREUR - Formations non trouvées"

---

## Dépendances système (Playwright uniquement)

✅ **Configuration automatique via `nixpacks.toml`**

Le fichier `nixpacks.toml` à la racine installe automatiquement:
- **Playwright browsers** (pour Bright Data/Google formations)
- **Dépendances système** (fonts, libs, etc.)

⚠️ **FlashScore/Selenium DÉSACTIVÉ** pour économiser ressources Railway.
- L'app utilise uniquement `football-data.co.uk` CSV pour les fixtures
- Bright Data scrape toujours les formations Google

**Pas d'action nécessaire** - Railway utilise automatiquement ce fichier.

### Vérification après déploiement

Dans les logs Railway, vérifier:
```
✓ Playwright Chromium installé
✓ Application démarrée
✓ [WARNING] FlashScore scraping échoué (NORMAL - désactivé)
```

---

## Troubleshooting

### Erreur: "Executable doesn't exist at ..." (Playwright)
**Solution**: Playwright n'a pas installé les browsers. Vérifier le start command.

### Erreur: "Browser closed unexpectedly"
**Solution**: Manque de mémoire. Augmenter le plan Railway ou optimiser le code.

### Erreur: "Connection timeout to Bright Data"
**Solution**: Vérifier les credentials Bright Data dans les variables d'environnement.

### Matchs sans formations (normal)
**Solution normale**: Google n'affiche pas toujours les compositions (matchs trop tôt, équipes non reconnues).

### FlashScore scraping échoue (NORMAL)
**Comportement attendu**: FlashScore/Selenium est désactivé pour économiser ressources.
- L'app utilise uniquement `fixtures.csv` depuis football-data.co.uk
- Message dans les logs: `[WARNING] FlashScore scraping échoué: No module named 'selenium'`
- **Aucune action nécessaire** - c'est le comportement normal

---

## Migration SerpAPI → Bright Data

✅ **Avantages**:
- Pas de limite API SerpAPI
- Données en temps réel depuis Google
- Plus fiable pour les formations

⚠️ **Coûts Bright Data**:
- Environ $100-300/mois selon utilisation
- Vérifier le dashboard Bright Data régulièrement

📊 **Monitoring**:
- Bright Data: https://brightdata.com/cp/zones
- Logs Railway: observer les `[Formation Scraper]`

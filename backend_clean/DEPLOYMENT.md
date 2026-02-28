# Guide de Deploiement - Backend Clean

## Windows (Developpement)

### Demarrage manuel
```bash
cd backend_clean
python main.py
```

### Demarrage via script
Double-cliquer sur `start_service.bat` ou:
```bash
cd backend_clean
start_service.bat
```

### Demarrage en arriere-plan (Windows)
```bash
cd backend_clean
start /B python main.py
```

---

## Linux (Production)

### Option 1: Systemd Service (Recommande)

#### 1. Installer le service
```bash
# Copier le fichier de service
sudo cp football-backend.service /etc/systemd/system/

# Creer les dossiers de logs
sudo mkdir -p /var/log/football-backend
sudo chown www-data:www-data /var/log/football-backend

# Recharger systemd
sudo systemctl daemon-reload
```

#### 2. Demarrer le service
```bash
sudo systemctl start football-backend
```

#### 3. Activer au demarrage
```bash
sudo systemctl enable football-backend
```

#### 4. Verifier le statut
```bash
sudo systemctl status football-backend
```

#### 5. Voir les logs
```bash
# Logs en temps reel
sudo journalctl -u football-backend -f

# Derniers logs
sudo journalctl -u football-backend -n 100

# Fichiers de logs
tail -f /var/log/football-backend/output.log
tail -f /var/log/football-backend/error.log
```

#### 6. Commandes utiles
```bash
# Redemarrer
sudo systemctl restart football-backend

# Arreter
sudo systemctl stop football-backend

# Recharger la configuration
sudo systemctl reload football-backend

# Desactiver
sudo systemctl disable football-backend
```

---

### Option 2: PM2 (Alternative)

#### 1. Installer PM2
```bash
npm install -g pm2
```

#### 2. Configurer PM2
Editer `ecosystem.config.js` et mettre a jour le chemin:
```javascript
cwd: '/path/to/backend_clean'
```

#### 3. Demarrer avec PM2
```bash
cd backend_clean
pm2 start ecosystem.config.js
```

#### 4. Sauvegarder la configuration
```bash
pm2 save
```

#### 5. Activer au demarrage
```bash
pm2 startup
# Suivre les instructions affichees
```

#### 6. Commandes PM2
```bash
# Voir les process
pm2 list

# Voir les logs
pm2 logs football-backend

# Redemarrer
pm2 restart football-backend

# Arreter
pm2 stop football-backend

# Supprimer
pm2 delete football-backend
```

---

## Docker (Optionnel)

### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEEPINFRA_API_KEY=${DEEPINFRA_API_KEY}
    volumes:
      - ./data:/app/data
      - ./predictions.db:/app/predictions.db
    restart: always
```

### Demarrer avec Docker
```bash
docker-compose up -d
```

---

## Nginx (Reverse Proxy)

### Configuration
```nginx
server {
    listen 80;
    server_name api.votre-domaine.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Activer la configuration
```bash
sudo ln -s /etc/nginx/sites-available/football-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Verification

Apres le deploiement, verifier que l'API est accessible:

```bash
# Test local
curl http://localhost:8000/docs

# Test distant
curl http://votre-serveur:8000/docs
```

---

## Troubleshooting

### Erreur "Port 8000 deja utilise"
```bash
# Trouver le processus
lsof -i :8000  # Linux
netstat -ano | findstr :8000  # Windows

# Tuer le processus
kill -9 <PID>  # Linux
taskkill /PID <PID> /F  # Windows
```

### Erreur "Module not found"
```bash
# Reinstaller les dependances
pip install -r requirements.txt

# Verifier PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/backend_clean"
```

### Base de donnees corrompue
```bash
# Supprimer et recreer
rm predictions.db
python -c "from services.sqlite_database_service import SQLiteDatabaseService; SQLiteDatabaseService()"
```

---

## Securite

### Variables d'environnement
Ne jamais commiter le fichier `.env`. Utiliser:
```bash
# Linux
export DEEPINFRA_API_KEY=your_key_here

# Windows
set DEEPINFRA_API_KEY=your_key_here
```

### Firewall
```bash
# Autoriser le port 8000
sudo ufw allow 8000/tcp
```

### HTTPS (Production)
Utiliser Certbot pour SSL:
```bash
sudo certbot --nginx -d api.votre-domaine.com
```

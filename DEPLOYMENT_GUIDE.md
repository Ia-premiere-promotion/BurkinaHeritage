# 🚀 Guide de Déploiement Complet - BurkinaHeritage

Ce guide vous accompagne dans le déploiement de l'application BurkinaHeritage (frontend + backend) en production.

## 📋 Table des Matières

1. [Prérequis](#prérequis)
2. [Configuration des Variables d'Environnement](#configuration-des-variables-denvironnement)
3. [Déploiement du Backend](#déploiement-du-backend)
4. [Déploiement du Frontend](#déploiement-du-frontend)
5. [Options de Déploiement](#options-de-déploiement)
6. [Vérification Post-Déploiement](#vérification-post-déploiement)
7. [Dépannage](#dépannage)

---

## 🎯 Prérequis

### Backend
- Python 3.9+
- pip
- Serveur avec au moins 2GB RAM
- Accès SSH (pour serveurs)

### Frontend
- Node.js 18+
- npm ou yarn
- Compte sur une plateforme de déploiement (Vercel, Netlify, etc.)

---

## ⚙️ Configuration des Variables d'Environnement

### Frontend

1. **Créez le fichier `.env.production`** dans le dossier `frontend/` :
   ```env
   VITE_API_BASE_URL=https://votre-api-backend.com
   VITE_API_TIMEOUT=30000
   ```

2. **Ou configurez les variables sur votre plateforme** :
   - Vercel : Settings > Environment Variables
   - Netlify : Site settings > Build & deploy > Environment
   - Render : Environment > Environment Variables

### Backend

1. **Créez le fichier `.env`** dans le dossier `backend/` :
   ```env
   ALLOWED_ORIGINS=https://votre-frontend.com
   PORT=8000
   HOST=0.0.0.0
   DEBUG=False
   CORPUS_PATH=./data/corpus.json
   ```

---

## 🔧 Déploiement du Backend

### Option 1 : Serveur VPS (Ubuntu/Debian)

#### 1. Préparation du serveur

```bash
# Se connecter au serveur
ssh user@votre-serveur.com

# Mettre à jour le système
sudo apt update && sudo apt upgrade -y

# Installer Python et pip
sudo apt install python3 python3-pip python3-venv -y
```

#### 2. Cloner et configurer le projet

```bash
# Cloner le projet
git clone https://github.com/votre-repo/BurkinaHeritage.git
cd BurkinaHeritage/backend

# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

#### 3. Configuration

```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer avec vos valeurs
nano .env
```

Ajustez les valeurs :
```env
ALLOWED_ORIGINS=https://votre-frontend.com
PORT=8000
HOST=0.0.0.0
DEBUG=False
```

#### 4. Lancer avec systemd (recommandé)

Créez le fichier service :

```bash
sudo nano /etc/systemd/system/burkinaheritage.service
```

Contenu :
```ini
[Unit]
Description=BurkinaHeritage API
After=network.target

[Service]
Type=simple
User=votre-user
WorkingDirectory=/home/votre-user/BurkinaHeritage/backend
Environment="PATH=/home/votre-user/BurkinaHeritage/backend/venv/bin"
ExecStart=/home/votre-user/BurkinaHeritage/backend/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Activer et démarrer :
```bash
sudo systemctl enable burkinaheritage
sudo systemctl start burkinaheritage
sudo systemctl status burkinaheritage
```

#### 5. Configuration Nginx (reverse proxy)

```bash
sudo apt install nginx -y
sudo nano /etc/nginx/sites-available/burkinaheritage
```

Contenu :
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

Activer :
```bash
sudo ln -s /etc/nginx/sites-available/burkinaheritage /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. SSL avec Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d api.votre-domaine.com
```

### Option 2 : Render.com

1. Connectez votre repo GitHub
2. Créez un nouveau Web Service
3. Configurez :
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `python main.py`
   - **Environment Variables** :
     ```
     ALLOWED_ORIGINS=https://votre-frontend.com
     PORT=8000
     DEBUG=False
     ```

### Option 3 : Railway.app

1. Connectez votre repo GitHub
2. Sélectionnez le dossier `backend`
3. Railway détectera automatiquement Python
4. Ajoutez les variables d'environnement dans l'interface

---

## 🎨 Déploiement du Frontend

### Option 1 : Vercel (Recommandé)

#### Via l'interface web

1. Connectez-vous sur [vercel.com](https://vercel.com)
2. Cliquez sur "New Project"
3. Importez votre repo GitHub
4. Configuration :
   - **Framework Preset** : Vite
   - **Root Directory** : `frontend`
   - **Build Command** : `npm run build`
   - **Output Directory** : `dist`
5. Ajoutez les variables d'environnement :
   ```
   VITE_API_BASE_URL=https://api.votre-domaine.com
   VITE_API_TIMEOUT=30000
   ```
6. Déployez !

#### Via CLI

```bash
# Installer Vercel CLI
npm install -g vercel

# Se connecter
vercel login

# Déployer
cd frontend
vercel --prod
```

### Option 2 : Netlify

1. Connectez-vous sur [netlify.com](https://netlify.com)
2. "Add new site" > "Import an existing project"
3. Configuration :
   - **Base directory** : `frontend`
   - **Build command** : `npm run build`
   - **Publish directory** : `frontend/dist`
4. Variables d'environnement :
   ```
   VITE_API_BASE_URL=https://api.votre-domaine.com
   VITE_API_TIMEOUT=30000
   ```

### Option 3 : Build Manuel + Serveur Statique

```bash
cd frontend

# Build de production
VITE_API_BASE_URL=https://api.votre-domaine.com npm run build

# Le dossier dist/ contient les fichiers statiques
# Uploadez-les sur n'importe quel hébergeur statique :
# - AWS S3 + CloudFront
# - GitHub Pages
# - Cloudflare Pages
# - Azure Static Web Apps
```

---

## 🔍 Vérification Post-Déploiement

### Backend

```bash
# Test de santé
curl https://api.votre-domaine.com/api/health

# Test de requête
curl -X POST https://api.votre-domaine.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Qui est Thomas Sankara?", "use_llm": false}'
```

### Frontend

1. Ouvrez votre site : `https://votre-frontend.com`
2. Ouvrez la console du navigateur (F12)
3. Posez une question dans le chat
4. Vérifiez qu'il n'y a pas d'erreur CORS
5. Vérifiez que les réponses arrivent correctement

---

## 🌐 Options de Déploiement Complètes

### Configuration Recommandée

| Composant | Service | Prix | Avantages |
|-----------|---------|------|-----------|
| **Frontend** | Vercel | Gratuit | CDN mondial, SSL auto, déploiement auto |
| **Backend** | Render.com | Gratuit (avec limitations) | Simple, SSL auto, logs inclus |
| **Alternative Backend** | VPS (DigitalOcean) | ~$5/mois | Contrôle total, performance stable |

### Architecture Production

```
Frontend (Vercel)
    ↓ HTTPS
Backend API (Render/VPS)
    ↓
Base de données ChromaDB
    ↓
Corpus JSON local
```

---

## 🐛 Dépannage

### Erreur CORS

**Symptôme** : Console frontend affiche "CORS policy blocked"

**Solution** :
1. Vérifiez la variable `ALLOWED_ORIGINS` dans le backend `.env`
2. Ajoutez l'URL exacte de votre frontend :
   ```env
   ALLOWED_ORIGINS=https://votre-frontend.vercel.app
   ```

### Frontend ne trouve pas l'API

**Symptôme** : "Failed to fetch" ou "Network error"

**Solution** :
1. Vérifiez `VITE_API_BASE_URL` dans les variables d'environnement de la plateforme
2. Testez l'URL de l'API directement dans le navigateur : `https://api.votre-domaine.com/api/health`
3. Vérifiez les logs de la plateforme de déploiement

### Backend crashe au démarrage

**Symptôme** : Service ne démarre pas, erreur 502

**Solution** :
1. Vérifiez les logs : `sudo journalctl -u burkinaheritage -f` (VPS) ou logs de la plateforme
2. Vérifiez que tous les fichiers nécessaires sont présents (`data/corpus.json`)
3. Vérifiez les dépendances : `pip list`

### Build frontend échoue

**Symptôme** : Erreur lors du build

**Solution** :
1. Vérifiez la version de Node.js : `node --version` (doit être 18+)
2. Supprimez `node_modules` et réinstallez :
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

---

## 📊 Monitoring

### Backend

```bash
# Logs en temps réel (systemd)
sudo journalctl -u burkinaheritage -f

# Utilisation CPU/RAM
htop
```

### Frontend

- **Vercel** : Analytics intégré dans le dashboard
- **Netlify** : Analytics dans l'interface
- **Google Analytics** : Ajoutez le script dans `index.html`

---

## 🔐 Sécurité

### Checklist Production

- [ ] Variables sensibles dans `.env` (pas dans le code)
- [ ] `.env` dans `.gitignore`
- [ ] CORS configuré strictement (pas `allow_origins=["*"]`)
- [ ] HTTPS activé (SSL)
- [ ] DEBUG=False en production
- [ ] Rate limiting sur l'API (optionnel)
- [ ] Logs d'erreur configurés
- [ ] Backups réguliers des données

---

## 📞 Support

En cas de problème :
1. Consultez les logs de votre plateforme
2. Vérifiez la [documentation Vercel](https://vercel.com/docs)
3. Vérifiez la [documentation Render](https://render.com/docs)
4. Ouvrez une issue sur GitHub

---

## 📚 Ressources Utiles

- [Documentation FastAPI](https://fastapi.tiangolo.com/)
- [Documentation Vite](https://vitejs.dev/)
- [Documentation Vercel](https://vercel.com/docs)
- [Documentation Render](https://render.com/docs)
- [Let's Encrypt](https://letsencrypt.org/)

---

**Bonne chance avec votre déploiement ! 🚀**

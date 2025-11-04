# 🎨 BurkinaHeritage - Frontend

> Interface utilisateur React pour l'assistant culturel IA

[![React](https://img.shields.io/badge/React-18.2-blue.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.0-purple.svg)](https://vitejs.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)

---

## 📋 Description

Interface conversationnelle moderne et responsive pour interagir avec le système RAG BurkinaHeritage. Développée avec React et Vite pour une expérience utilisateur fluide et performante.

## ✨ Fonctionnalités

- 💬 **Chat conversationnel** - Interface de messagerie intuitive
- 📱 **Mobile-first** - Design responsive optimisé pour tous les écrans
- 🎭 **Animation typing** - Effet d'écriture progressive pour les réponses IA
- 📚 **Multi-conversations** - Gestion de plusieurs sessions simultanées
- 🔖 **Citations sources** - Affichage des sources documentaires avec liens
- 💾 **Persistance locale** - Historique sauvegardé dans localStorage
- 🎨 **Interface élégante** - Design inspiré de la culture burkinabè (vert, or, beige)
- ⚡ **Performance optimale** - Build optimisé avec Vite

## 🛠️ Technologies Utilisées

| Technologie | Version | Licence | Usage |
|------------|---------|---------|-------|
| [React](https://react.dev/) | 18.2.0 | MIT | Framework UI |
| [Vite](https://vitejs.dev/) | 5.0.8 | MIT | Build tool & dev server |
| HTML5 | - | - | Structure |
| CSS3 | - | - | Styles (responsive) |
| JavaScript ES6+ | - | - | Logique applicative |

## 📦 Installation

### Prérequis
- Node.js 18+ ([Télécharger](https://nodejs.org/))
- npm ou yarn

### Étapes

```bash
# Naviguer dans le dossier frontend
cd frontend

# Installer les dépendances
npm install

# Lancer le serveur de développement
npm run dev

# L'application sera accessible sur http://localhost:5173
```

## 🚀 Scripts Disponibles

```bash
# Serveur de développement avec hot-reload
npm run dev

# Build de production
npm run build

# Prévisualiser le build de production
npm run preview

# Linter (si configuré)
npm run lint
```

## 📂 Structure du Code

```
frontend/
├── index.html              # Point d'entrée HTML
├── package.json            # Dépendances npm
├── vite.config.js          # Configuration Vite
│
├── public/                 # Assets statiques
│   ├── about.html          # Page à propos
│   └── demo-standalone.html
│
└── src/                    # Code source React
    ├── main.jsx            # Point d'entrée React
    ├── App.jsx             # Composant principal
    ├── App.css             # Styles globaux + responsive
    ├── index.css           # Styles de base
    │
    ├── components/         # Composants réutilisables
    │   ├── ChatMessage.jsx # Bulle de message (user/AI)
    │   ├── ChatMessage.css
    │   ├── Sidebar.jsx     # Menu latéral conversations
    │   └── Sidebar.css
    │
    └── services/           # Services API
        └── api.js          # Client HTTP pour le backend
```

## 🔌 Configuration API

L'application utilise des **variables d'environnement** pour se connecter au backend FastAPI.

### Configuration automatique

1. **Développement local** : Copiez `.env.example` en `.env`
   ```bash
   cp .env.example .env
   ```

2. **Modifiez l'URL** dans `.env` :
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   VITE_API_TIMEOUT=30000
   ```

3. **Production** : Modifiez `.env.production` avec votre URL de production :
   ```env
   VITE_API_BASE_URL=https://api.votre-domaine.com
   ```

### Variables d'environnement disponibles

| Variable | Description | Défaut |
|----------|-------------|--------|
| `VITE_API_BASE_URL` | URL du backend API | `http://localhost:8000` |
| `VITE_API_TIMEOUT` | Timeout des requêtes (ms) | `30000` |

> 📖 **Guide complet** : Consultez [DEPLOYMENT.md](./DEPLOYMENT.md) pour plus de détails sur le déploiement.

### Configuration avancée

Le fichier `src/services/api.js` utilise automatiquement ces variables :

```javascript
const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: parseInt(import.meta.env.VITE_API_TIMEOUT) || 30000
};
```

## 🎨 Personnalisation des Styles

### Couleurs principales
Définies dans `App.css` :

```css
:root {
  --color-green-dark: #006400;    /* Vert Burkina */
  --color-gold: #E1AD01;          /* Or du drapeau */
  --color-beige-light: #F5F1E8;   /* Fond clair */
  --color-white: #FFFFFF;
  --color-text-dark: #2C3E50;
}
```

### Breakpoints responsive

```css
/* Tablette */
@media (max-width: 768px) { ... }

/* Mobile */
@media (max-width: 480px) { ... }

/* Très petits écrans */
@media (max-width: 360px) { ... }
```

## 📱 Interface Responsive

L'interface s'adapte automatiquement :

- **Desktop (> 1024px)** : Sidebar ouverte + chat large
- **Tablette (768-1024px)** : Sidebar rétractable + texte lisible
- **Mobile (< 768px)** : 
  - Sidebar en overlay
  - Polices réduites (14px → 13px)
  - Bouton d'envoi avec icône uniquement
  - Champ de saisie optimisé (max-width calculé)

## 🔄 Gestion d'État

### localStorage
Les conversations sont persistées automatiquement :

```javascript
// Clé de stockage
'burkina_conversations'

// Structure
{
  id: timestamp,
  title: "Première question...",
  date: "04/11/2025",
  messages: [
    { id, text, sender: 'user'|'ai', timestamp, sources }
  ]
}
```

### React State
- `conversations` : Liste de toutes les conversations
- `currentConversationId` : ID de la conversation active
- `inputValue` : Texte de l'input utilisateur
- `isLoading` : État de chargement (requête en cours)
- `isSidebarOpen` : État de la sidebar (ouvert/fermé)

## 🌐 API Client

Le fichier `services/api.js` expose :

```javascript
// Envoyer un message
sendMessage(question, use_llm, conversation_history)

// Vérifier l'état du backend
checkHealth()

// Obtenir les statistiques
getStats()
```

## 🎯 Composants Principaux

### App.jsx
- Gestion de l'état global
- Orchestration des composants
- Logique de conversation
- Communication avec l'API

### ChatMessage.jsx
- Affichage d'un message (user ou AI)
- Animation typing pour l'IA
- Affichage des sources citées
- Style différencié selon l'émetteur

### Sidebar.jsx
- Liste des conversations
- Création de nouvelle conversation
- Sélection/suppression de conversation
- Menu responsive (overlay mobile)

## 🔧 Build de Production

```bash
# Créer le build optimisé
npm run build

# Les fichiers seront dans dist/
# Prêts à être déployés sur n'importe quel serveur web statique
```

### Déploiement

Le build peut être déployé sur :
- **Vercel** : `npm install -g vercel && vercel`
- **Netlify** : Drag & drop du dossier `dist/`
- **GitHub Pages** : Push du dossier `dist/` sur branche `gh-pages`
- **Railway** : Connecter le repo et configurer le build

## 🐛 Débogage

### Problèmes courants

**1. L'API ne répond pas**
```javascript
// Vérifier que le backend est lancé sur http://localhost:8000
// Tester : http://localhost:8000/api/health
```

**2. CORS errors**
```
Le backend doit autoriser l'origine du frontend
Voir backend/main.py : allow_origins=["*"]
```

**3. Messages ne s'affichent pas**
```javascript
// Vérifier la console : F12 > Console
// Vérifier localStorage : F12 > Application > Local Storage
```

## 📝 Licence

Ce frontend est sous licence **MIT** - voir le fichier [LICENSE](../LICENSE) à la racine du projet.

## 🤝 Contribution

Ce projet fait partie du système BurkinaHeritage développé pour le **Hackathon RAG Open Source 2025**.

---

**Développé avec ❤️ pour préserver et promouvoir la culture burkinabè**

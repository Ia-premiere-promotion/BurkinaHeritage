# 🇧🇫 BurkinaHeritage - Assistant IA Culturel

> Système RAG (Retrieval-Augmented Generation) 100% Open Source sur la culture et le patrimoine du Burkina Faso

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Open Source](https://img.shields.io/badge/Open%20Source-100%25-green.svg)](https://opensource.org/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

---

## 📋 Sujet et Justification

**Thème choisi :** Patrimoine culturel et historique du Burkina Faso

**Justification :** 
Le Burkina Faso possède une richesse culturelle exceptionnelle (sites UNESCO, artisanat, traditions, histoire) mais ces connaissances sont dispersées et peu accessibles. Notre système RAG centralise et rend accessible ce patrimoine via une interface conversationnelle intelligente, permettant :
- 🎓 **Éducation** : Apprentissage de l'histoire et de la culture burkinabè
- 🌍 **Tourisme** : Information sur les sites et traditions
- 🔬 **Recherche** : Accès rapide à des sources documentées
- 🇧🇫 **Préservation** : Sauvegarde numérique du patrimoine

---

## 🏗️ Architecture Technique

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite)                   │
│  Interface conversationnelle responsive (mobile-first)       │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP REST API
┌────────────────────▼────────────────────────────────────────┐
│                   BACKEND (FastAPI)                          │
│  • Endpoints: /api/chat, /api/health, /api/stats            │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              SYSTÈME RAG (rag_simple.py)                     │
│  1. Retrieval: Recherche documents pertinents (ChromaDB)    │
│  2. Augmentation: Enrichissement du contexte                │
│  3. Generation: Réponse avec LLM (Gemini/HuggingFace)       │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│            BASE DE DONNÉES VECTORIELLE                       │
│  • ChromaDB (open source)                                    │
│  • 582 documents indexés                                     │
│  • Embeddings: Sentence-Transformers                         │
│  • Collections: burkina_heritage_simple                      │
└──────────────────────────────────────────────────────────────┘
```

### Pipeline RAG détaillé

1. **Question utilisateur** → Frontend React
2. **Requête HTTP** → Backend FastAPI (`POST /api/chat`)
3. **Embedding** → Conversion question en vecteur (Sentence-Transformers)
4. **Recherche sémantique** → ChromaDB trouve top-5 documents pertinents
5. **Construction prompt** → Contexte + Question + Historique conversation
6. **Génération LLM** → Gemini API ou Hugging Face (fallback)
7. **Formatage réponse** → Texte + Sources citées
8. **Affichage** → Interface avec animation typing + liens sources

---

## 🛠️ Technologies Open Source Utilisées

### Backend
| Technologie | Version | Licence | Usage |
|------------|---------|---------|-------|
| [Python](https://www.python.org/) | 3.11+ | PSF License | Langage principal |
| [FastAPI](https://fastapi.tiangolo.com/) | 0.104.1 | MIT | Framework API REST |
| [Uvicorn](https://www.uvicorn.org/) | 0.24.0 | BSD | Serveur ASGI |
| [ChromaDB](https://www.trychroma.com/) | 0.4.18 | Apache 2.0 | Base vectorielle |
| [Sentence-Transformers](https://www.sbert.net/) | 2.2.2 | Apache 2.0 | Embeddings sémantiques |
| [PyTorch](https://pytorch.org/) | 2.1.0 | BSD | Framework ML |
| [Transformers](https://huggingface.co/transformers/) | 4.35.0 | Apache 2.0 | Modèles NLP |
| [Pydantic](https://docs.pydantic.dev/) | 2.5.0 | MIT | Validation données |

### Frontend
| Technologie | Licence | Usage |
|------------|---------|-------|
| [React](https://react.dev/) | MIT | UI Framework |
| [Vite](https://vitejs.dev/) | MIT | Build tool |
| HTML/CSS/JS | - | Interface utilisateur |

### LLM (Génération)
| Solution | Type | Licence | Status |
|----------|------|---------|--------|
| **Gemini API** | Cloud | Propriétaire Google | ⚠️ Optionnel (clé requise) |
| **Hugging Face Inference** | Cloud | Apache 2.0 | ✅ Fallback gratuit |
| Modèle: Mistral-7B | Open Source | Apache 2.0 | Via HuggingFace |

**Note importante** : Le système fonctionne avec 3 niveaux de fallback :
1. Si `GEMINI_API_KEY` disponible → Utilise Gemini (meilleure qualité)
2. Sinon si `HUGGINGFACE_TOKEN` → Utilise Mistral-7B (gratuit, open source)
3. Sinon → Mode template basique (100% local, pas de dépendance externe)

---

## 🚀 Installation

### Prérequis
- Python 3.11+ ([Télécharger](https://www.python.org/downloads/))
- Node.js 18+ ([Télécharger](https://nodejs.org/))
- Git ([Télécharger](https://git-scm.com/))

### 1️⃣ Cloner le projet
```bash
git clone https://github.com/votre-username/BurkinaHeritage.git
cd BurkinaHeritage
```

### 2️⃣ Configuration Backend
```bash
cd backend

# Créer environnement virtuel Python
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer dépendances
pip install -r requirements.txt

# Configurer variables d'environnement (optionnel)
cp .env.example .env
# Éditer .env et ajouter vos clés API si disponibles
```

### 3️⃣ Configuration Frontend
```bash
cd ../frontend
npm install
```

### 4️⃣ Lancer l'application

**Terminal 1 - Backend :**
```bash
cd backend
python main.py
# → API disponible sur http://localhost:8000
# → Documentation Swagger: http://localhost:8000/docs
```

**Terminal 2 - Frontend :**
```bash
cd frontend
npm run dev
# → Interface disponible sur http://localhost:5173
```

**Accéder à l'application :** Ouvrez votre navigateur sur `http://localhost:5173`

---

##  Structure du Projet

```
BurkinaHeritage/
├── LICENSE                    # Licence MIT
├── README.md                  # Ce fichier
├── .env.example              # Template configuration
│
├── backend/                   # API + Système RAG
│   ├── main.py               # Serveur FastAPI
│   ├── rag_simple.py         # Logique RAG complète
│   ├── prepare_data.py       # Préparation corpus
│   ├── requirements.txt      # Dépendances Python
│   ├── data/
│   │   ├── corpus.json       # 582 documents indexés
│   │   ├── sources.txt       # URLs sources
│   │   └── chroma_db/        # Base vectorielle ChromaDB
│   └── Documents/
│       └── burkinaheritage_corpus_clean.csv  # Données brutes
│
├── frontend/                  # Interface React
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx           # Composant principal
│       ├── App.css           # Styles (responsive)
│       ├── components/       # ChatMessage, Sidebar
│       └── services/
│           └── api.js        # Client API
```

---

## 🎯 Fonctionnalités Clés

✅ **Interface conversationnelle** - Chat fluide avec historique  
✅ **Recherche sémantique** - Trouve documents pertinents par similarité vectorielle  
✅ **Citations sources** - Chaque réponse cite ses sources documentaires  
✅ **Mode responsive** - Interface mobile-first optimisée  
✅ **Animation typing** - Effet d'écriture progressive réaliste  
✅ **Multi-conversations** - Gestion de plusieurs sessions  
✅ **Fallback intelligent** - 3 niveaux (Gemini → HuggingFace → Template)  
✅ **API REST documentée** - Swagger UI intégrée  

---

## 🤝 Contribution

Ce projet est développé dans le cadre du **Hackathon RAG Open Source 2025**.

**Technologies 100% Open Source** - Aucune dépendance propriétaire obligatoire.

---

## 📜 Licence

Ce projet est sous licence **MIT** - voir le fichier [LICENSE](LICENSE) pour plus de détails.

Toutes les technologies utilisées sont sous licences open source compatibles (MIT, Apache 2.0, BSD).

---

## 👥 Auteurs

**BurkinaHeritage Team** - Hackathon 2025

---

## 🙏 Remerciements

- Données culturelles : UNESCO, Wikipedia, sources gouvernementales burkinabè
- Communauté open source : ChromaDB, Hugging Face, FastAPI, React
- Inspiration : Préservation du patrimoine culturel africain

---

**⭐ Si ce projet vous intéresse, n'hésitez pas à le star sur GitHub !**

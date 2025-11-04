# 🇧🇫 BurkinaHeritage - Guide de Mise à Jour des Données

Ce guide explique comment mettre à jour le système avec de nouvelles données et faire du web scraping.

## 📋 Table des Matières

1. [Scripts Disponibles](#scripts-disponibles)
2. [Mise à Jour Complète (Recommandé)](#mise-à-jour-complète)
3. [Mise à Jour Étape par Étape](#mise-à-jour-étape-par-étape)
4. [Web Scraping](#web-scraping)
5. [Dépannage](#dépannage)

---

## 🛠️ Scripts Disponibles

### 1. `update_system.py` - Script Principal ⭐
Orchestre toute la mise à jour automatiquement.

### 2. `prepare_data_csv.py` - Traitement CSV
Traite le fichier `burkinaheritage_corpus_clean.csv` et crée le corpus.

### 3. `web_scraper.py` - Web Scraping
Récupère du contenu en ligne sur le Burkina Faso (UNESCO, Wikipedia, etc.).

### 4. `rebuild_database.py` - Reconstruction BD
Reconstruit la base de données vectorielle ChromaDB.

---

## 🚀 Mise à Jour Complète (Recommandé)

### Option 1: Avec Web Scraping

```bash
cd backend
python update_system.py
```

Le script va :
1. ✅ Traiter les données CSV
2. ✅ Faire du web scraping (avec votre confirmation)
3. ✅ Reconstruire la base de données
4. ✅ Vérifier que tout fonctionne

### Option 2: Sans Web Scraping

```bash
cd backend
python update_system.py --no-scraping
```

Plus rapide, mais sans enrichissement web.

---

## 📝 Mise à Jour Étape par Étape

Si vous voulez contrôler chaque étape :

### Étape 1 : Traiter les Données CSV

```bash
cd backend
python prepare_data_csv.py
```

**Ce que ça fait :**
- Lit `Documents/burkinaheritage_corpus_clean.csv`
- Nettoie et filtre les textes
- Crée `data/corpus.json`
- Génère `data/sources.txt`

**Résultat attendu :**
```
✅ XXX documents créés
💾 Fichiers sauvegardés
```

### Étape 2 : Web Scraping (Optionnel)

```bash
cd backend
python web_scraper.py
```

**Ce que ça fait :**
- Scrape les sites UNESCO sur le Burkina Faso
- Scrape Wikipedia (Culture, Histoire)
- Fusionne avec le corpus existant
- Respecte les délais entre requêtes

**⚠️ Prérequis :**
- Connexion internet active
- Pas de pare-feu bloquant

**Résultat attendu :**
```
✅ XX pages scrapées
💾 Corpus fusionné
```

### Étape 3 : Reconstruire la Base de Données

```bash
cd backend
python rebuild_database.py
```

**Ce que ça fait :**
- Sauvegarde l'ancienne BD (backup)
- Supprime l'ancienne BD
- Crée une nouvelle BD ChromaDB
- Indexe tous les documents du corpus

**⚠️ ATTENTION :** Cette opération supprime l'ancienne base !

**Résultat attendu :**
```
✅ XXX documents ajoutés à ChromaDB
🔍 Vérification: XXX documents dans la collection
```

---

## 🌐 Web Scraping - Détails

### Sites Scrapés

Le script `web_scraper.py` collecte des données depuis :

1. **UNESCO Burkina Faso**
   - Patrimoine mondial
   - Patrimoine culturel immatériel

2. **Wikipedia**
   - Culture du Burkina Faso
   - Histoire du Burkina Faso
   - Article général sur le Burkina Faso

### Configuration Personnalisée

Pour ajouter d'autres sites, modifiez `web_scraper.py` :

```python
self.target_sites = [
    {
        "name": "Votre Site",
        "urls": [
            "https://example.com/page1",
            "https://example.com/page2"
        ],
        "category": "votre-catégorie"
    }
]
```

### Bonnes Pratiques

✅ **À FAIRE :**
- Vérifier le fichier `robots.txt` des sites
- Respecter les délais entre requêtes (2 secondes minimum)
- Utiliser des User-Agents valides
- Scraper en dehors des heures de pointe

❌ **À ÉVITER :**
- Scraper trop rapidement (risque de ban IP)
- Ignorer les conditions d'utilisation
- Surcharger les serveurs

---

## 🔍 Vérification Après Mise à Jour

### Vérifier les Fichiers Créés

```bash
ls -lh data/
```

Vous devriez voir :
```
corpus.json           # Le corpus complet
sources.txt           # Liste des sources
scraped_data.json     # Données scrapées (si scraping)
chroma_db/            # Base de données vectorielle
```

### Tester le Corpus

```bash
python -c "import json; data=json.load(open('data/corpus.json')); print(f'{len(data)} documents')"
```

### Tester ChromaDB

```python
import chromadb
client = chromadb.PersistentClient(path="data/chroma_db")
collection = client.get_collection("burkinaheritage")
print(f"Documents dans ChromaDB: {collection.count()}")
```

### Tester l'API

```bash
# Lancer l'API
python main.py

# Dans un autre terminal, tester
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"question":"Parle-moi du Burkina Faso","use_llm":false}'
```

---

## 🐛 Dépannage

### Problème : "Fichier CSV introuvable"

**Solution :**
```bash
# Vérifier que le CSV existe
ls -l Documents/burkinaheritage_corpus_clean.csv

# Si manquant, vérifiez le chemin
```

### Problème : "Erreur lors du scraping"

**Solutions possibles :**
1. Vérifier la connexion internet
2. Vérifier que les sites sont accessibles
3. Augmenter le timeout dans `web_scraper.py`
4. Désactiver le scraping : `--no-scraping`

### Problème : "ChromaDB erreur"

**Solutions :**
```bash
# Réinstaller ChromaDB
pip install --force-reinstall chromadb

# Supprimer et recréer la BD
rm -rf data/chroma_db
python rebuild_database.py
```

### Problème : "Pas assez de documents"

**Solutions :**
1. Activer le web scraping
2. Ajouter plus de PDFs dans `Documents/`
3. Ajouter plus d'URLs dans `web_scraper.py`
4. Réduire le filtrage dans `prepare_data_csv.py`

### Problème : "Mémoire insuffisante"

**Solutions :**
```bash
# Traiter par lots plus petits
# Dans prepare_data_csv.py, réduire batch_size

# Ou augmenter la mémoire Python
export PYTHONHASHSEED=0
```

---

## 📊 Statistiques Attendues

Après une mise à jour complète, vous devriez avoir :

- **Documents CSV** : ~300-400 documents (selon le CSV)
- **Documents Scrapés** : ~20-50 documents
- **Total** : ~350-450 documents
- **Taille corpus.json** : ~1-3 MB
- **Taille ChromaDB** : ~5-15 MB

---

## 🔄 Automatisation (Optionnel)

Pour mettre à jour automatiquement chaque semaine :

```bash
# Créer un cron job
crontab -e

# Ajouter cette ligne (tous les dimanches à 2h du matin)
0 2 * * 0 cd /chemin/vers/backend && python update_system.py --no-scraping
```

---

## 📞 Support

En cas de problème :

1. Vérifier les logs dans le terminal
2. Consulter `data/sources.txt` pour voir ce qui a été traité
3. Tester étape par étape au lieu du script global
4. Vérifier les permissions des fichiers/dossiers

---

## ✅ Checklist de Mise à Jour

Avant de mettre en production :

- [ ] Données CSV présentes dans `Documents/`
- [ ] Environnement Python activé
- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] Scripts exécutés avec succès
- [ ] Base de données reconstruite
- [ ] API testée et fonctionnelle
- [ ] Frontend connecté à l'API

---

**Dernière mise à jour :** Novembre 2024
**Version :** 1.0

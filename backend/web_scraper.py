#!/usr/bin/env python3
"""
Script de web scraping pour BurkinaHeritage RAG
Récupère du contenu sur la culture et le patrimoine du Burkina Faso

Usage: python web_scraper.py
Output: data/scraped_data.json
"""

import os
import json
import time
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("⚠️  Installation des dépendances...")
    os.system("pip install requests beautifulsoup4")
    import requests
    from bs4 import BeautifulSoup


class WebScraper:
    """Scraper pour récupérer du contenu web sur le Burkina Faso"""
    
    def __init__(self, output_dir: str = "data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.scraped_data = []
        self.visited_urls = set()
        
        # Headers pour éviter les blocages
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Sites à scraper
        self.target_sites = [
            {
                "name": "UNESCO Burkina Faso",
                "urls": [
                    "https://whc.unesco.org/en/statesparties/bf",
                    "https://ich.unesco.org/en/state/burkina-faso-BF"
                ],
                "category": "patrimoine-unesco"
            },
            {
                "name": "Wikipedia Burkina Faso",
                "urls": [
                    "https://fr.wikipedia.org/wiki/Culture_du_Burkina_Faso",
                    "https://fr.wikipedia.org/wiki/Histoire_du_Burkina_Faso",
                    "https://fr.wikipedia.org/wiki/Burkina_Faso"
                ],
                "category": "encyclopédie"
            }
        ]
        
        self.stats = {
            "total_pages": 0,
            "total_paragraphs": 0,
            "total_words": 0,
            "errors": 0
        }
    
    def clean_text(self, text: str) -> str:
        """Nettoie le texte extrait"""
        if not text:
            return ""
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        # Supprimer les sauts de ligne multiples
        text = re.sub(r'\n+', '\n', text)
        # Supprimer les caractères spéciaux inutiles
        text = re.sub(r'[\[\]\{\}]', '', text)
        # Trim
        text = text.strip()
        return text
    
    def is_valid_text(self, text: str) -> bool:
        """Vérifie si le texte est valide"""
        if not text or len(text.strip()) < 100:
            return False
        # Vérifier qu'il y a des mots
        words = text.split()
        return len(words) >= 20
    
    def extract_text_from_url(self, url: str, category: str) -> List[Dict]:
        """Extrait le texte d'une URL"""
        documents = []
        
        if url in self.visited_urls:
            print(f"  ⏭️  Déjà visité: {url}")
            return documents
        
        try:
            print(f"  🌐 Scraping: {url}")
            
            # Requête HTTP
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Parser le HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraire le titre
            title = soup.find('title')
            page_title = title.get_text().strip() if title else urlparse(url).path
            
            # Supprimer les scripts, styles, etc.
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extraire les paragraphes
            paragraphs = soup.find_all(['p', 'article', 'section'])
            
            for i, para in enumerate(paragraphs):
                text = self.clean_text(para.get_text())
                
                if self.is_valid_text(text):
                    # Limiter la longueur à 500 mots
                    words = text.split()
                    if len(words) > 500:
                        # Découper en chunks
                        chunks = [' '.join(words[i:i+500]) for i in range(0, len(words), 450)]
                    else:
                        chunks = [text]
                    
                    for chunk_idx, chunk in enumerate(chunks):
                        documents.append({
                            "title": f"{page_title} - Partie {i+1}",
                            "content": chunk,
                            "source": url,
                            "category": category,
                            "scraped_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "word_count": len(chunk.split()),
                            "metadata": {
                                "paragraph_index": i,
                                "chunk_index": chunk_idx
                            }
                        })
                        
                        self.stats["total_paragraphs"] += 1
                        self.stats["total_words"] += len(chunk.split())
            
            self.visited_urls.add(url)
            self.stats["total_pages"] += 1
            
            print(f"    ✅ {len(documents)} documents extraits")
            
        except requests.RequestException as e:
            print(f"    ❌ Erreur réseau: {e}")
            self.stats["errors"] += 1
        except Exception as e:
            print(f"    ❌ Erreur: {e}")
            self.stats["errors"] += 1
        
        return documents
    
    def scrape_all_sites(self):
        """Scrape tous les sites configurés"""
        print("🚀 Démarrage du web scraping...\n")
        
        doc_id = 1
        
        for site in self.target_sites:
            print(f"📚 Scraping: {site['name']}")
            print(f"   Catégorie: {site['category']}")
            
            for url in site['urls']:
                docs = self.extract_text_from_url(url, site['category'])
                
                # Ajouter les IDs
                for doc in docs:
                    doc['id'] = doc_id
                    doc_id += 1
                
                self.scraped_data.extend(docs)
                
                # Respecter les délais entre requêtes
                time.sleep(2)
            
            print()
        
        print("✅ Scraping terminé!\n")
    
    def save_scraped_data(self):
        """Sauvegarde les données scrapées"""
        output_path = self.output_dir / "scraped_data.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Données sauvegardées: {output_path}")
        print(f"   📊 {len(self.scraped_data)} documents créés")
    
    def merge_with_corpus(self):
        """Fusionne les données scrapées avec le corpus existant"""
        corpus_path = self.output_dir / "corpus.json"
        
        if not corpus_path.exists():
            print("⚠️  Aucun corpus existant trouvé. Les données scrapées seront le nouveau corpus.")
            existing_corpus = []
        else:
            with open(corpus_path, 'r', encoding='utf-8') as f:
                existing_corpus = json.load(f)
            print(f"📖 Corpus existant: {len(existing_corpus)} documents")
        
        # Trouver le dernier ID
        max_id = max([doc.get('id', 0) for doc in existing_corpus], default=0)
        
        # Réassigner les IDs aux nouvelles données
        for i, doc in enumerate(self.scraped_data, start=1):
            doc['id'] = max_id + i
        
        # Fusionner
        merged_corpus = existing_corpus + self.scraped_data
        
        # Sauvegarder le corpus fusionné
        with open(corpus_path, 'w', encoding='utf-8') as f:
            json.dump(merged_corpus, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Corpus fusionné sauvegardé: {corpus_path}")
        print(f"   📊 Total: {len(merged_corpus)} documents")
        print(f"   ➕ Ajoutés: {len(self.scraped_data)} nouveaux documents")
    
    def print_statistics(self):
        """Affiche les statistiques"""
        print("\n" + "=" * 60)
        print("📊 STATISTIQUES DE SCRAPING")
        print("=" * 60)
        print(f"Pages visitées:      {self.stats['total_pages']}")
        print(f"Paragraphes extraits: {self.stats['total_paragraphs']}")
        print(f"Documents créés:     {len(self.scraped_data)}")
        print(f"Mots totaux:         {self.stats['total_words']:,}")
        print(f"Erreurs:             {self.stats['errors']}")
        
        if len(self.scraped_data) > 0:
            print(f"Moyenne mots/doc:    {self.stats['total_words'] // len(self.scraped_data)}")
        
        print("=" * 60 + "\n")


def main():
    """Point d'entrée principal"""
    print("\n" + "=" * 60)
    print("🇧🇫 BurkinaHeritage - Web Scraping")
    print("=" * 60 + "\n")
    
    # Créer le scraper
    scraper = WebScraper(output_dir="data")
    
    # Scraper les sites
    scraper.scrape_all_sites()
    
    # Sauvegarder les données
    scraper.save_scraped_data()
    
    # Fusionner avec le corpus existant
    scraper.merge_with_corpus()
    
    # Afficher les statistiques
    scraper.print_statistics()
    
    print("🎉 Scraping terminé!")
    print("📁 Fichiers générés/mis à jour:")
    print("   - data/scraped_data.json")
    print("   - data/corpus.json (fusionné)\n")
    
    print("⚠️  Note: Respectez toujours les conditions d'utilisation")
    print("   des sites web et le fichier robots.txt!\n")


if __name__ == "__main__":
    main()

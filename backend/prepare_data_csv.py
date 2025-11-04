#!/usr/bin/env python3
"""
Script de préparation des données CSV pour BurkinaHeritage RAG
Traite le fichier burkinaheritage_corpus_clean.csv

Usage: python prepare_data_csv.py
Output: data/corpus.json (écrase l'ancien), data/sources.txt
"""

import os
import json
import csv
import re
from pathlib import Path
from typing import List, Dict
from datetime import datetime


class CSVProcessor:
    """Traite le CSV et met à jour le corpus de données"""
    
    def __init__(self, csv_file: str = "Documents/burkinaheritage_corpus_clean.csv", output_dir: str = "data"):
        self.csv_file = Path(csv_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.corpus = []
        self.sources = []
        self.stats = {
            "total_rows": 0,
            "total_documents": 0,
            "total_words": 0,
            "urls_unique": set()
        }
    
    def clean_text(self, text: str) -> str:
        """Nettoie le texte extrait"""
        if not text:
            return ""
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        # Supprimer les sauts de ligne multiples
        text = re.sub(r'\n+', '\n', text)
        # Trim
        text = text.strip()
        return text
    
    def categorize_document(self, title: str, text: str, url: str) -> str:
        """Détermine la catégorie du document"""
        title_lower = title.lower() if title else ""
        text_lower = text.lower() if text else ""
        url_lower = url.lower() if url else ""
        
        # Catégorisation par mots-clés
        if any(word in text_lower or word in title_lower for word in ["unesco", "patrimoine", "heritage", "monument"]):
            return "patrimoine-culturel"
        elif any(word in text_lower for word in ["burkina", "faso", "ouagadougou", "bobo"]):
            return "burkina-faso"
        elif "education" in text_lower or "école" in text_lower or "éducation" in text_lower:
            return "éducation"
        elif "culture" in text_lower or "tradition" in text_lower or "art" in text_lower:
            return "culture"
        elif "museum" in text_lower or "musée" in text_lower:
            return "musées"
        elif "法" in text_lower or "中文" in text_lower or "chinese" in url_lower:
            return "autres-langues"
        else:
            return "général"
    
    def is_valid_text(self, text: str) -> bool:
        """Vérifie si le texte est valide et exploitable"""
        if not text or len(text.strip()) < 50:
            return False
        
        # Vérifier si c'est majoritairement du charabia
        # Compter les caractères non-standard
        non_standard = sum(1 for c in text if ord(c) > 1000 and c not in "àâäéèêëïîôùûüÿçÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ")
        ratio = non_standard / len(text) if len(text) > 0 else 0
        
        # Si plus de 30% de caractères non-standard, probablement du charabia
        if ratio > 0.3:
            return False
        
        return True
    
    def chunk_text(self, text: str, max_words: int = 500) -> List[str]:
        """Découpe le texte en chunks si trop long"""
        words = text.split()
        
        if len(words) <= max_words:
            return [text]
        
        chunks = []
        # Découpage avec overlap de 50 mots pour maintenir le contexte
        overlap = 50
        for i in range(0, len(words), max_words - overlap):
            chunk = ' '.join(words[i:i + max_words])
            if len(chunk.split()) > 50:  # Ignorer les chunks trop courts
                chunks.append(chunk)
        
        return chunks
    
    def process_csv(self):
        """Traite le fichier CSV"""
        print("🚀 Démarrage du traitement du CSV...\n")
        
        if not self.csv_file.exists():
            print(f"❌ Fichier CSV introuvable: {self.csv_file}")
            return
        
        print(f"📚 Lecture de: {self.csv_file.name}\n")
        
        chunk_id = 1
        skipped = 0
        
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                for row_num, row in enumerate(csv_reader, 1):
                    self.stats["total_rows"] += 1
                    
                    # Extraire les colonnes
                    id_doc = row.get('id_doc', '')
                    url = row.get('url', '')
                    titre = row.get('titre', '')
                    segment_id = row.get('segment_id', '')
                    texte = row.get('texte', '')
                    
                    # Nettoyer le texte
                    cleaned_text = self.clean_text(texte)
                    
                    # Vérifier si le texte est valide
                    if not self.is_valid_text(cleaned_text):
                        skipped += 1
                        continue
                    
                    # Ajouter l'URL aux sources uniques
                    if url:
                        self.stats["urls_unique"].add(url)
                    
                    # Découper en chunks si nécessaire
                    chunks = self.chunk_text(cleaned_text, max_words=500)
                    
                    for chunk_index, chunk_text in enumerate(chunks):
                        category = self.categorize_document(titre, chunk_text, url)
                        
                        # Titre du document
                        if titre:
                            doc_title = titre
                        else:
                            # Utiliser les premiers mots du texte
                            words = chunk_text.split()[:10]
                            doc_title = ' '.join(words)
                        
                        # Limiter la longueur du titre
                        if len(doc_title) > 100:
                            doc_title = doc_title[:97] + "..."
                        
                        chunk_suffix = f" (partie {chunk_index + 1})" if len(chunks) > 1 else ""
                        
                        self.corpus.append({
                            "id": chunk_id,
                            "title": doc_title + chunk_suffix,
                            "content": chunk_text,
                            "source": url if url else f"Document {id_doc}",
                            "category": category,
                            "word_count": len(chunk_text.split()),
                            "metadata": {
                                "id_doc": id_doc,
                                "url": url,
                                "segment_id": segment_id,
                                "chunk_index": chunk_index if len(chunks) > 1 else 0
                            }
                        })
                        
                        chunk_id += 1
                        self.stats["total_documents"] += 1
                        self.stats["total_words"] += len(chunk_text.split())
                    
                    # Afficher la progression
                    if row_num % 100 == 0:
                        print(f"  Traité: {row_num} lignes, {self.stats['total_documents']} documents créés...")
            
            print(f"\n✅ Traitement terminé!")
            print(f"   Lignes CSV traitées: {self.stats['total_rows']}")
            print(f"   Documents créés: {self.stats['total_documents']}")
            print(f"   Lignes ignorées (texte invalide): {skipped}\n")
            
        except Exception as e:
            print(f"❌ Erreur lors du traitement: {e}")
    
    def save_corpus(self):
        """Sauvegarde le corpus en JSON"""
        corpus_path = self.output_dir / "corpus.json"
        
        with open(corpus_path, 'w', encoding='utf-8') as f:
            json.dump(self.corpus, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Corpus sauvegardé: {corpus_path}")
        print(f"   📊 {len(self.corpus)} documents créés")
    
    def save_sources(self):
        """Sauvegarde la liste des sources"""
        sources_path = self.output_dir / "sources.txt"
        
        with open(sources_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("SOURCES - BurkinaHeritage RAG System\n")
            f.write("Culture et Patrimoine du Burkina Faso\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Date de génération: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
            f.write(f"Nombre total de documents: {len(self.corpus)}\n")
            f.write(f"Sources web uniques: {len(self.stats['urls_unique'])}\n\n")
            
            f.write("-" * 60 + "\n")
            f.write("CATÉGORIES:\n")
            f.write("-" * 60 + "\n\n")
            
            # Compter par catégorie
            categories = {}
            for doc in self.corpus:
                cat = doc['category']
                categories[cat] = categories.get(cat, 0) + 1
            
            for cat, count in sorted(categories.items()):
                f.write(f"  • {cat}: {count} documents\n")
            
            f.write("\n" + "-" * 60 + "\n")
            f.write("SOURCES WEB (échantillon):\n")
            f.write("-" * 60 + "\n\n")
            
            # Afficher un échantillon d'URLs
            for i, url in enumerate(sorted(list(self.stats['urls_unique']))[:20], 1):
                f.write(f"{i}. {url}\n")
            
            if len(self.stats['urls_unique']) > 20:
                f.write(f"\n... et {len(self.stats['urls_unique']) - 20} autres sources\n")
            
            f.write("\n" + "=" * 60 + "\n")
            f.write("Tous les documents sont issus de sources\n")
            f.write("sur la culture, l'histoire et le patrimoine\n")
            f.write("du Burkina Faso.\n")
            f.write("=" * 60 + "\n")
        
        print(f"📝 Sources sauvegardées: {sources_path}")
    
    def print_statistics(self):
        """Affiche les statistiques finales"""
        print("\n" + "=" * 60)
        print("📊 STATISTIQUES FINALES")
        print("=" * 60)
        print(f"Lignes CSV:          {self.stats['total_rows']}")
        print(f"Documents créés:     {self.stats['total_documents']}")
        print(f"Sources web uniques: {len(self.stats['urls_unique'])}")
        print(f"Mots totaux:         {self.stats['total_words']:,}")
        print(f"Moyenne mots/doc:    {self.stats['total_words'] // self.stats['total_documents'] if self.stats['total_documents'] > 0 else 0}")
        print("=" * 60)
        
        # Vérifier le critère des 500 documents
        if self.stats['total_documents'] >= 500:
            print("✅ OBJECTIF ATTEINT: 500+ documents!")
        else:
            print(f"⚠️  Objectif partiel: {self.stats['total_documents']}/500 documents")
        
        print("=" * 60 + "\n")


def main():
    """Point d'entrée principal"""
    import sys
    
    print("\n" + "=" * 60)
    print("🇧🇫 BurkinaHeritage - Préparation des Données CSV")
    print("=" * 60 + "\n")
    
    # Déterminer le fichier CSV à utiliser
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        print(f"📂 Fichier CSV spécifié: {csv_file}")
    else:
        csv_file = "Documents/burkinaheritage_corpus_clean.csv"
        print(f"📂 Fichier CSV par défaut: {csv_file}")
    
    # Créer le processeur
    processor = CSVProcessor(
        csv_file=csv_file,
        output_dir="data"
    )
    
    # Traiter le CSV
    processor.process_csv()
    
    # Sauvegarder les résultats
    processor.save_corpus()
    processor.save_sources()
    
    # Afficher les statistiques
    processor.print_statistics()
    
    print("🎉 Préparation terminée!")
    print("📁 Fichiers générés:")
    print("   - data/corpus.json")
    print("   - data/sources.txt\n")


if __name__ == "__main__":
    main()

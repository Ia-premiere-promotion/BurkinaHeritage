#!/usr/bin/env python3
"""
Script de préparation des données pour BurkinaHeritage RAG
Extrait le texte des PDFs et crée un corpus structuré

Usage: python prepare_data.py
Output: data/corpus.json, data/sources.txt
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict
from datetime import datetime

try:
    import pypdf
except ImportError:
    print("⚠️  pypdf non installé. Installation en cours...")
    os.system("pip install pypdf")
    import pypdf


class DocumentProcessor:
    """Traite les PDFs et crée le corpus de données"""
    
    def __init__(self, pdf_dir: str = "Documents", output_dir: str = "data"):
        self.pdf_dir = Path(pdf_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.corpus = []
        self.sources = []
        self.stats = {
            "total_pdfs": 0,
            "total_pages": 0,
            "total_chunks": 0,
            "total_words": 0
        }
    
    def clean_text(self, text: str) -> str:
        """Nettoie le texte extrait"""
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        # Supprimer les sauts de ligne multiples
        text = re.sub(r'\n+', '\n', text)
        # Trim
        text = text.strip()
        return text
    
    def extract_pdf_text(self, pdf_path: Path) -> List[Dict]:
        """Extrait le texte de chaque page d'un PDF"""
        documents = []
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                print(f"  📄 {pdf_path.name} - {num_pages} pages")
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text()
                    
                    if text and len(text.strip()) > 50:  # Au moins 50 caractères
                        cleaned_text = self.clean_text(text)
                        
                        documents.append({
                            "pdf": pdf_path.name,
                            "page": page_num,
                            "text": cleaned_text,
                            "word_count": len(cleaned_text.split())
                        })
                        
                        self.stats["total_pages"] += 1
                        self.stats["total_words"] += len(cleaned_text.split())
                
                self.stats["total_pdfs"] += 1
                
        except Exception as e:
            print(f"  ❌ Erreur avec {pdf_path.name}: {e}")
        
        return documents
    
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
    
    def categorize_document(self, filename: str, text: str) -> str:
        """Détermine la catégorie du document"""
        filename_lower = filename.lower()
        text_lower = text.lower()
        
        # Catégorisation par mots-clés
        if "architecture" in filename_lower or "construction" in text_lower:
            return "architecture"
        elif "pédagogique" in filename_lower or "éducation" in text_lower:
            return "éducation"
        elif "culture" in text_lower or "tradition" in text_lower:
            return "culture"
        elif "santé" in text_lower or "médical" in text_lower:
            return "santé"
        elif "technique" in filename_lower or "scientifique" in text_lower:
            return "science-tech"
        else:
            return "culture-générale"
    
    def create_title(self, pdf_name: str, page_num: int, text: str) -> str:
        """Génère un titre pour le document"""
        # Nettoyer le nom du fichier
        base_name = pdf_name.replace('.pdf', '').replace('_', ' ')
        
        # Essayer d'extraire la première phrase significative
        sentences = text.split('.')
        if sentences and len(sentences[0]) > 10 and len(sentences[0]) < 100:
            title = sentences[0].strip()
        else:
            # Sinon, utiliser les premiers mots
            words = text.split()[:10]
            title = ' '.join(words)
        
        # Limiter la longueur
        if len(title) > 80:
            title = title[:77] + "..."
        
        return title
    
    def process_all_pdfs(self):
        """Traite tous les PDFs du dossier"""
        print("🚀 Démarrage du traitement des PDFs...\n")
        
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            print(f"❌ Aucun PDF trouvé dans {self.pdf_dir}")
            return
        
        print(f"📚 {len(pdf_files)} PDFs trouvés\n")
        
        chunk_id = 1
        
        for pdf_path in pdf_files:
            print(f"Traitement: {pdf_path.name}")
            
            # Ajouter à la liste des sources
            self.sources.append({
                "filename": pdf_path.name,
                "size_mb": pdf_path.stat().st_size / (1024 * 1024),
                "date": datetime.now().strftime("%Y-%m-%d")
            })
            
            # Extraire le texte
            pages = self.extract_pdf_text(pdf_path)
            
            # Créer les entrées du corpus
            for page_data in pages:
                # Découper en chunks si nécessaire (500 mots max)
                chunks = self.chunk_text(page_data["text"], max_words=500)
                
                for chunk_index, chunk_text in enumerate(chunks):
                    category = self.categorize_document(pdf_path.name, chunk_text)
                    title = self.create_title(pdf_path.name, page_data["page"], chunk_text)
                    
                    chunk_suffix = f" (partie {chunk_index + 1})" if len(chunks) > 1 else ""
                    
                    self.corpus.append({
                        "id": chunk_id,
                        "title": title + chunk_suffix,
                        "content": chunk_text,
                        "source": f"{pdf_path.name} - page {page_data['page']}",
                        "category": category,
                        "word_count": len(chunk_text.split()),
                        "metadata": {
                            "pdf": pdf_path.name,
                            "page": page_data["page"],
                            "chunk_index": chunk_index if len(chunks) > 1 else 0
                        }
                    })
                    
                    chunk_id += 1
                    self.stats["total_chunks"] += 1
            
            print()
        
        print("✅ Extraction terminée!\n")
    
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
            f.write("Culture du Burkina Faso\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Date de génération: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
            f.write(f"Nombre total de documents: {len(self.corpus)}\n\n")
            
            f.write("-" * 60 + "\n")
            f.write("DOCUMENTS PDF SOURCES:\n")
            f.write("-" * 60 + "\n\n")
            
            for i, source in enumerate(self.sources, 1):
                f.write(f"{i}. {source['filename']}\n")
                f.write(f"   Taille: {source['size_mb']:.2f} MB\n")
                f.write(f"   Traité le: {source['date']}\n\n")
            
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
        print(f"PDFs traités:        {self.stats['total_pdfs']}")
        print(f"Pages extraites:     {self.stats['total_pages']}")
        print(f"Documents créés:     {self.stats['total_chunks']}")
        print(f"Mots totaux:         {self.stats['total_words']:,}")
        print(f"Moyenne mots/doc:    {self.stats['total_words'] // self.stats['total_chunks'] if self.stats['total_chunks'] > 0 else 0}")
        print("=" * 60)
        
        # Vérifier le critère des 500 documents
        if self.stats['total_chunks'] >= 500:
            print("✅ OBJECTIF ATTEINT: 500+ documents!")
        else:
            print(f"⚠️  Objectif partiel: {self.stats['total_chunks']}/500 documents")
            print(f"   Manquant: {500 - self.stats['total_chunks']} documents")
        
        print("=" * 60 + "\n")


def main():
    """Point d'entrée principal"""
    print("\n" + "=" * 60)
    print("🇧🇫 BurkinaHeritage - Préparation des Données")
    print("=" * 60 + "\n")
    
    # Créer le processeur
    processor = DocumentProcessor(
        pdf_dir="Documents",
        output_dir="data"
    )
    
    # Traiter tous les PDFs
    processor.process_all_pdfs()
    
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

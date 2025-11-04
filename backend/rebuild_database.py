#!/usr/bin/env python3
"""
Script de reconstruction de la base de données ChromaDB
Recrée la base de données vectorielle à partir du corpus

Usage: python rebuild_database.py
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("⚠️  ChromaDB non installé. Installation...")
    os.system("pip install chromadb")
    import chromadb
    from chromadb.config import Settings


class DatabaseRebuilder:
    """Reconstruit la base de données ChromaDB"""
    
    def __init__(self, corpus_file: str = "data/corpus.json", db_path: str = "data/chroma_db"):
        self.corpus_file = Path(corpus_file)
        self.db_path = Path(db_path)
        
        self.corpus = []
        self.stats = {
            "total_documents": 0,
            "successfully_added": 0,
            "errors": 0
        }
    
    def load_corpus(self) -> bool:
        """Charge le corpus depuis le fichier JSON"""
        print("📖 Chargement du corpus...")
        
        if not self.corpus_file.exists():
            print(f"❌ Fichier corpus introuvable: {self.corpus_file}")
            return False
        
        try:
            with open(self.corpus_file, 'r', encoding='utf-8') as f:
                self.corpus = json.load(f)
            
            print(f"✅ Corpus chargé: {len(self.corpus)} documents")
            self.stats["total_documents"] = len(self.corpus)
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement: {e}")
            return False
    
    def backup_existing_db(self):
        """Sauvegarde l'ancienne base de données"""
        if self.db_path.exists():
            backup_path = Path(str(self.db_path) + f"_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            print(f"💾 Sauvegarde de l'ancienne BD: {backup_path.name}")
            
            try:
                shutil.copytree(self.db_path, backup_path)
                print("✅ Sauvegarde créée")
            except Exception as e:
                print(f"⚠️  Erreur lors de la sauvegarde: {e}")
    
    def delete_existing_db(self):
        """Supprime l'ancienne base de données"""
        if self.db_path.exists():
            print(f"🗑️  Suppression de l'ancienne BD...")
            try:
                shutil.rmtree(self.db_path)
                print("✅ Ancienne BD supprimée")
            except Exception as e:
                print(f"❌ Erreur lors de la suppression: {e}")
    
    def create_database(self):
        """Crée et remplit la nouvelle base de données"""
        print("\n🔨 Création de la nouvelle base de données...")
        
        try:
            # Créer le client ChromaDB
            client = chromadb.PersistentClient(
                path=str(self.db_path),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Créer la collection
            collection_name = "burkinaheritage"
            
            # Supprimer la collection si elle existe
            try:
                client.delete_collection(name=collection_name)
            except:
                pass
            
            # Créer la nouvelle collection
            collection = client.create_collection(
                name=collection_name,
                metadata={"description": "Corpus sur la culture et le patrimoine du Burkina Faso"}
            )
            
            print(f"✅ Collection '{collection_name}' créée")
            
            # Ajouter les documents par lots
            batch_size = 100
            total_batches = (len(self.corpus) + batch_size - 1) // batch_size
            
            print(f"\n📝 Ajout des documents ({total_batches} lots de {batch_size})...")
            
            for i in range(0, len(self.corpus), batch_size):
                batch = self.corpus[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                
                # Préparer les données pour ChromaDB
                ids = [str(doc['id']) for doc in batch]
                documents = [doc['content'] for doc in batch]
                metadatas = [
                    {
                        "title": doc.get('title', ''),
                        "source": doc.get('source', ''),
                        "category": doc.get('category', ''),
                        "word_count": str(doc.get('word_count', 0))
                    }
                    for doc in batch
                ]
                
                try:
                    # Ajouter le lot à la collection
                    collection.add(
                        ids=ids,
                        documents=documents,
                        metadatas=metadatas
                    )
                    
                    self.stats["successfully_added"] += len(batch)
                    print(f"  ✅ Lot {batch_num}/{total_batches} ajouté ({len(batch)} documents)")
                    
                except Exception as e:
                    print(f"  ❌ Erreur lot {batch_num}: {e}")
                    self.stats["errors"] += 1
            
            print(f"\n✅ Base de données créée avec succès!")
            print(f"   📊 {self.stats['successfully_added']} documents ajoutés")
            
            # Vérifier la collection
            count = collection.count()
            print(f"   🔍 Vérification: {count} documents dans la collection")
            
        except Exception as e:
            print(f"❌ Erreur lors de la création de la BD: {e}")
            self.stats["errors"] += 1
    
    def print_statistics(self):
        """Affiche les statistiques finales"""
        print("\n" + "=" * 60)
        print("📊 STATISTIQUES DE RECONSTRUCTION")
        print("=" * 60)
        print(f"Documents dans le corpus: {self.stats['total_documents']}")
        print(f"Documents ajoutés:        {self.stats['successfully_added']}")
        print(f"Erreurs:                  {self.stats['errors']}")
        
        if self.stats['successfully_added'] > 0:
            success_rate = (self.stats['successfully_added'] / self.stats['total_documents']) * 100
            print(f"Taux de réussite:         {success_rate:.1f}%")
        
        print("=" * 60 + "\n")


def main():
    """Point d'entrée principal"""
    print("\n" + "=" * 60)
    print("🇧🇫 BurkinaHeritage - Reconstruction de la Base de Données")
    print("=" * 60 + "\n")
    
    # Créer le reconstructeur
    rebuilder = DatabaseRebuilder(
        corpus_file="data/corpus.json",
        db_path="data/chroma_db"
    )
    
    # Charger le corpus
    if not rebuilder.load_corpus():
        print("\n❌ Impossible de continuer sans corpus!")
        return
    
    # Demander confirmation
    print("\n⚠️  ATTENTION:")
    print("   Cette opération va RECRÉER complètement la base de données.")
    print("   L'ancienne BD sera sauvegardée puis supprimée.")
    
    response = input("\n   Continuer ? (oui/non): ").strip().lower()
    
    if response not in ['oui', 'yes', 'o', 'y']:
        print("\n❌ Opération annulée.")
        return
    
    print()
    
    # Sauvegarder l'ancienne BD
    rebuilder.backup_existing_db()
    
    # Supprimer l'ancienne BD
    rebuilder.delete_existing_db()
    
    # Créer la nouvelle BD
    rebuilder.create_database()
    
    # Afficher les statistiques
    rebuilder.print_statistics()
    
    print("🎉 Reconstruction terminée!")
    print("📁 Base de données:")
    print(f"   - {rebuilder.db_path}\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script principal pour mettre à jour complètement le système BurkinaHeritage
- Traite les nouvelles données CSV
- Fait du web scraping (optionnel)
- Reconstruit la base de données

Usage: python update_system.py [--no-scraping]
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime


class SystemUpdater:
    """Orchestre la mise à jour complète du système"""
    
    def __init__(self, enable_scraping: bool = True):
        self.enable_scraping = enable_scraping
        self.backend_dir = Path(__file__).parent
        
        self.steps = []
        self.completed_steps = []
        self.failed_steps = []
    
    def print_header(self, text: str):
        """Affiche un en-tête formaté"""
        print("\n" + "=" * 70)
        print(f"  {text}")
        print("=" * 70 + "\n")
    
    def run_script(self, script_name: str, description: str) -> bool:
        """Exécute un script Python"""
        print(f"▶️  {description}...")
        print(f"   Script: {script_name}\n")
        
        script_path = self.backend_dir / script_name
        
        if not script_path.exists():
            print(f"❌ Script introuvable: {script_path}")
            return False
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(self.backend_dir),
                capture_output=False,
                text=True
            )
            
            if result.returncode == 0:
                print(f"\n✅ {description} - TERMINÉ\n")
                return True
            else:
                print(f"\n❌ {description} - ÉCHEC\n")
                return False
                
        except Exception as e:
            print(f"\n❌ Erreur lors de l'exécution: {e}\n")
            return False
    
    def step_1_prepare_csv(self) -> bool:
        """Étape 1: Préparer les données CSV"""
        return self.run_script(
            "prepare_data_csv.py",
            "Étape 1/4: Traitement des données CSV"
        )
    
    def step_2_web_scraping(self) -> bool:
        """Étape 2: Web scraping (optionnel)"""
        if not self.enable_scraping:
            print("⏭️  Étape 2/4: Web scraping - IGNORÉ (désactivé)\n")
            return True
        
        print("⚠️  Le web scraping peut prendre du temps et nécessite une connexion internet.")
        response = input("   Continuer avec le scraping ? (oui/non): ").strip().lower()
        
        if response not in ['oui', 'yes', 'o', 'y']:
            print("⏭️  Web scraping ignoré.\n")
            return True
        
        return self.run_script(
            "web_scraper.py",
            "Étape 2/4: Web scraping des sources en ligne"
        )
    
    def step_3_rebuild_database(self) -> bool:
        """Étape 3: Reconstruire la base de données"""
        print("▶️  Étape 3/4: Reconstruction de la base de données...")
        print("   Script: rebuild_database.py\n")
        
        # Le script rebuild_database.py demande une confirmation
        # On utilise subprocess.Popen pour pouvoir interagir
        script_path = self.backend_dir / "rebuild_database.py"
        
        if not script_path.exists():
            print(f"❌ Script introuvable: {script_path}")
            return False
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(self.backend_dir)
            )
            
            if result.returncode == 0:
                print(f"\n✅ Reconstruction de la BD - TERMINÉ\n")
                return True
            else:
                print(f"\n❌ Reconstruction de la BD - ÉCHEC\n")
                return False
                
        except Exception as e:
            print(f"\n❌ Erreur: {e}\n")
            return False
    
    def step_4_verify_system(self) -> bool:
        """Étape 4: Vérifier le système"""
        print("▶️  Étape 4/4: Vérification du système...\n")
        
        # Vérifier les fichiers créés
        checks = [
            ("data/corpus.json", "Corpus JSON"),
            ("data/sources.txt", "Liste des sources"),
            ("data/chroma_db", "Base de données ChromaDB")
        ]
        
        all_ok = True
        
        for file_path, description in checks:
            full_path = self.backend_dir / file_path
            if full_path.exists():
                if full_path.is_file():
                    size = full_path.stat().st_size / 1024  # KB
                    print(f"   ✅ {description}: {size:.1f} KB")
                else:
                    print(f"   ✅ {description}: (dossier)")
            else:
                print(f"   ❌ {description}: MANQUANT")
                all_ok = False
        
        print()
        
        if all_ok:
            print("✅ Vérification - SUCCÈS\n")
            return True
        else:
            print("⚠️  Vérification - AVERTISSEMENTS\n")
            return False
    
    def run(self):
        """Lance la mise à jour complète"""
        self.print_header("🇧🇫 BurkinaHeritage - Mise à Jour Complète du Système")
        
        print(f"📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"📂 Répertoire: {self.backend_dir}")
        print(f"🌐 Web scraping: {'Activé' if self.enable_scraping else 'Désactivé'}")
        
        steps = [
            ("Traitement CSV", self.step_1_prepare_csv),
            ("Web Scraping", self.step_2_web_scraping),
            ("Reconstruction BD", self.step_3_rebuild_database),
            ("Vérification", self.step_4_verify_system)
        ]
        
        print(f"\n📋 Étapes prévues: {len(steps)}")
        for i, (name, _) in enumerate(steps, 1):
            print(f"   {i}. {name}")
        
        input("\n▶️  Appuyez sur Entrée pour commencer...")
        
        # Exécuter les étapes
        for i, (name, step_func) in enumerate(steps, 1):
            self.print_header(f"Étape {i}/{len(steps)}: {name}")
            
            success = step_func()
            
            if success:
                self.completed_steps.append(name)
            else:
                self.failed_steps.append(name)
                
                # Demander si on continue
                if i < len(steps):
                    response = input(f"\n⚠️  Continuer malgré l'échec ? (oui/non): ").strip().lower()
                    if response not in ['oui', 'yes', 'o', 'y']:
                        print("\n❌ Mise à jour interrompue.\n")
                        break
        
        # Résumé final
        self.print_summary()
    
    def print_summary(self):
        """Affiche le résumé de la mise à jour"""
        self.print_header("📊 RÉSUMÉ DE LA MISE À JOUR")
        
        print(f"✅ Étapes réussies: {len(self.completed_steps)}")
        for step in self.completed_steps:
            print(f"   • {step}")
        
        if self.failed_steps:
            print(f"\n❌ Étapes échouées: {len(self.failed_steps)}")
            for step in self.failed_steps:
                print(f"   • {step}")
        
        print("\n" + "=" * 70)
        
        if not self.failed_steps:
            print("🎉 MISE À JOUR COMPLÈTE RÉUSSIE !")
        elif len(self.completed_steps) > len(self.failed_steps):
            print("⚠️  MISE À JOUR PARTIELLE")
        else:
            print("❌ MISE À JOUR ÉCHOUÉE")
        
        print("=" * 70 + "\n")
        
        print("📁 Prochaines étapes:")
        print("   1. Vérifiez les fichiers dans data/")
        print("   2. Testez l'API: python main.py")
        print("   3. Lancez le frontend pour tester l'interface\n")


def main():
    """Point d'entrée principal"""
    # Vérifier les arguments
    enable_scraping = "--no-scraping" not in sys.argv
    
    # Créer et lancer l'updater
    updater = SystemUpdater(enable_scraping=enable_scraping)
    updater.run()


if __name__ == "__main__":
    main()

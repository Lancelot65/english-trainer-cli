#!/usr/bin/env python3
"""
English Trainer v7.0 - Launcher Script
Simple launcher with dependency checking and setup.
"""

import sys
import subprocess


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ requis. Version actuelle:", sys.version)
        return False
    return True


def check_dependencies():
    """Check if required dependencies are installed."""
    required = ["openai", "rich", "prompt_toolkit"]
    missing = []

    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"❌ Dépendances manquantes: {', '.join(missing)}")
        print("📦 Installation automatique...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
            )
            print("✅ Dépendances installées avec succès!")
            return True
        except subprocess.CalledProcessError:
            print("❌ Échec de l'installation automatique.")
            print("🔧 Installez manuellement: pip install -r requirements.txt")
            return False

    return True


def check_configuration():
    """Check basic configuration."""
    import os

    base_url = os.getenv("ENGLISH_RPG_BASE_URL")
    api_key = os.getenv("ENGLISH_RPG_API_KEY")

    # Set defaults if not configured
    if not base_url:
        os.environ["ENGLISH_RPG_BASE_URL"] = "http://localhost:3000/v1"
        base_url = os.environ["ENGLISH_RPG_BASE_URL"]

    if not api_key:
        os.environ["ENGLISH_RPG_API_KEY"] = "dummy-key"
        api_key = os.environ["ENGLISH_RPG_API_KEY"]

    return True


def main():
    """Main launcher function."""
    print("🚀 English Trainer v7.0 - Démarrage...")

    # Check Python version
    if not check_python_version():
        return 1

    # Check dependencies
    if not check_dependencies():
        return 1

    # Check configuration
    if not check_configuration():
        print("❌ Configuration incomplète. Arrêt.")
        return 1

    # Launch application
    try:
        print("✅ Lancement de l'application...\n")
        from english_trainer.core.app import main as app_main

        return app_main()

    except KeyboardInterrupt:
        print("\n👋 Au revoir!")
        return 0

    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("🔧 Vérifiez l'installation des dépendances")
        return 1

    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        print("🐛 Veuillez signaler ce bug sur GitHub")
        return 1


if __name__ == "__main__":
    sys.exit(main())

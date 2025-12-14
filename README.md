# English Trainer CLI

Application interactive d'apprentissage de l'anglais en ligne de commande, propulsée par l'IA.

## 🚀 Démarrage rapide

1. **Prérequis** : Python 3.10+ et Docker

2. **Lancer le serveur IA local** :
   ```bash
   docker run -d -p 3000:3000 amirkabiri/duckai
   ```

3. **Configurer les variables d'environnement** :
   ```bash
   export ENGLISH_RPG_BASE_URL="http://localhost:3000/v1"
   export ENGLISH_RPG_API_KEY="dummy-key"
   ```

4. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

5. **Lancer l'application** :
   ```bash
   python run.py
   ```

## 🎯 Fonctionnalités

- Exercices de traduction avec correction IA
- Cahier de cours interactif
- Révision espacée intelligente
- Défis quotidiens
- Suivi de progression

## 📖 Utilisation

Une fois l'application lancée, suivez les instructions à l'écran. 
Les commandes principales sont affichées dans le menu principal.

## ⚙️ Configuration

Les variables d'environnement peuvent être définies dans un fichier `.env` :
- `ENGLISH_RPG_BASE_URL` : URL du serveur LLM (défaut: http://localhost:3000/v1)
- `ENGLISH_RPG_API_KEY` : Clé API (défaut: dummy-key)
# English Trainer v7.0

Une application moderne d'apprentissage de l'anglais pour les francophones, alimentée par l'intelligence artificielle.


### 🎯 Défis quotidiens
- Un nouveau défi chaque jour
- Variété de types d'activités (traduction, vocabulaire, grammaire)

## 🚀 Fonctionnalités principales

### 📝 Exercices de traduction
- Génération dynamique d'exercices adaptés à votre niveau
- Évaluation instantanée avec feedback détaillé
- Suivi des performances

### 📚 Cahier de cours interactif
- Sauvegarde des leçons générées
- Organisation par sujets et tags
- Marquage des favoris

### 🔁 Révision espacée
- Système intelligent de révision
- Algorithmes adaptatifs basés sur votre performance
- Prioritisation des contenus difficiles

### 💬 Pratique conversationnelle
- Simulations de conversations réalistes
- Corrections intégrées et naturelles
- Adaptation au niveau de l'utilisateur

### 📖 Entraînement au vocabulaire
- Listes de mots thématiques
- Exemples contextualisés
- Progression adaptative

# English Trainer

Petit outil CLI pour s'entraîner à l'anglais (pensé pour les francophones).

But
- Générer et évaluer des exercices de traduction et de conversation avec un backend LLM compatible OpenAI.

Quick start
1. Pré-requis : Python 3.10+, Docker (optionnel)
2. (Optionnel) Lancer un serveur LLM local compatible :

```bash
docker run -p 3000:3000 amirkabiri/duckai
```

3. Exporter les variables d'environnement si besoin (valeurs par défaut utilisées sinon) :

```bash
export ENGLISH_RPG_BASE_URL="http://localhost:3000/v1"
export ENGLISH_RPG_API_KEY="dummy-key"
```

4. Lancer l'application :

```bash
python run.py
```

Fonctionnalités principales
- Génération d'exercices de traduction
- Évaluation instantanée avec feedback
- Pratique conversationnelle simulée
- Sauvegarde simple des leçons

Configuration minimale
- `ENGLISH_RPG_BASE_URL` : URL du serveur LLM (défaut `http://localhost:3000/v1`)
- `ENGLISH_RPG_API_KEY` : clé API (défaut `dummy-key`)

Démarrage rapide du serveur LLM
- Image recommandée : `amirkabiri/duckai`
- Repo : https://github.com/amirkabiri/duckai

Contribuer
- Ouvrez une issue ou une PR pour proposer des améliorations.

Licence
- Projet personnel — voir les fichiers du dépôt pour plus d'informations.
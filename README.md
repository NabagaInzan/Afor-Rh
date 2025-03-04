# GeoGestion AFOR

Application web de gestion des employés pour AFOR.

## Fonctionnalités

- Authentification des opérateurs
- Gestion des employés (CRUD)
- Tableau de bord avec statistiques
- Interface responsive
- Mode sombre/clair

## Technologies

- Backend : Flask (Python)
- Frontend : HTML, CSS, JavaScript
- Base de données : SQLite
- UI : Bootstrap 5
- Composants : DataTables, FontAwesome

## Installation

1. Cloner le repository
```bash
git clone <votre-repo>
cd Operateur
```

2. Installer les dépendances
```bash
pip install -r requirements.txt
```

3. Configurer les variables d'environnement
Créer un fichier `.env` à la racine du projet avec :
```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=votre_clé_secrète
```

4. Lancer l'application
```bash
flask run
```

## Déploiement

L'application est configurée pour être déployée sur Render.com.

## Structure du projet

```
Operateur/
├── app.py              # Point d'entrée de l'application
├── auth/              # Authentification
├── services/         # Services métier
├── static/           # Fichiers statiques (CSS, JS, images)
├── templates/        # Templates HTML
├── data/            # Base de données
└── requirements.txt  # Dépendances Python
```

## Auteur

[Votre nom]

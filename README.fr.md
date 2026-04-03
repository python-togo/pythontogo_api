# Python Togo API Version 2.1.0

API officielle de Python Togo.
Ce projet centralise les fonctionnalites backend et sert de base commune pour les evolutions de la plateforme.

## Objectif

- Fournir une API stable et structuree avec FastAPI
- Centraliser les endpoints du projet
- Faciliter les contributions de la communaute

## Contribution

### 1) Forker le projet

Forker ce depot, puis cloner votre fork en local :

```bash
git clone https://github.com/<votre-utilisateur>/pythontogo_api.git
cd pythontogo_api
```

### 2) Installer les dependances

```bash
pip install -r requirements.txt
```

### 3) Configurer l'environnement

Copier le fichier d'exemple puis adapter les variables :

```bash
cp .env.example .env
```

Ensuite, modifier .env avec vos valeurs locales (DB, cles, etc.).

### 4) Lancer les migrations

```bash
python -m app.database.migrations

ou

python3 -m app.database.migrations
```

Verifier au besoin la configuration de migration dans le dossier/fichier Alembic du projet.

### 5) Demarrer l'API en developpement

```bash
fastapi dev app/main.py --port 8000
```

Vous pouvez remplacer 8000 par n'importe quel port disponible.

## Version

Cette branche contient la nouvelle version du projet.

## Bonnes pratiques de contribution

- Creer une branche par fonctionnalite/correctif
- Faire des commits clairs
- Ouvrir une Pull Request avec une description precise
- Ajouter/mettre a jour les tests si necessaire

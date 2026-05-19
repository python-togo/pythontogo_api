#!/bin/bash

# 1. Gestion automatique du fichier .env
# On vérifie si .env existe, sinon on le crée à partir de l'exemple
if [ ! -f app/.env ]; then
    if [ -f app/.env-example ]; then
        echo "Fichier app/.env manquant. Création à partir de app/.env-example..."
    else
        echo "Attention : Aucun fichier d'exemple .env trouvé."
        echo "Veuillez créer un fichier app/.env avec les variables d'environnement nécessaires."
        exit 1
    fi
fi

# 2. Attente de la base de données
# Il est crucial d'attendre que le port 5432 soit ouvert avant de migrer
echo "Attente de la base de données..."
# Si tu n'as pas 'nc' (netcat) installé, tu peux utiliser un simple sleep
# ou installer 'netcat-openbsd' dans ton Dockerfile
sleep 5 

# 3. Exécution des migrations
echo "Exécution des migrations..."
python -m app.database.migrations

# 4. Démarrage de l'API
echo "Démarrage de l'API..."
if [ "$ENV" = "production" ]; then
    echo "Environnement de production détecté. Démarrage en mode production..."
    exec fastapi run app/main.py --port 8000 --host 0.0.0.0 --workers 4
else
    echo "Environnement de développement détecté. Démarrage en mode développement..."
    # Correction : --host 0.0.0.0 (4 octets requis)
    exec fastapi dev app/main.py --port 8080 --host 0.0.0.0
fi
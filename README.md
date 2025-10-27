# TP1 – Exercice 4 : Stack complète avec Docker Compose

> **Objectif** : Orchestrer une application fullstack composée de Flask (API), PostgreSQL (base de données), Redis (cache) et Adminer (interface d’admin).

---

## TP1 – Exercice 4 : Stack complète avec Docker Compose

> Objectif : Orchestrer une application fullstack composée d'une API Flask, PostgreSQL (DB), Redis (cache) et Adminer (interface d'administration).

---

## Aperçu des services

La stack définie dans `fullstack-app/docker-compose.yml` lance les services suivants :

- web (API Flask) — exposée sur le port 5000 de la machine hôte (5000:5000).
- db (PostgreSQL) — base de données `usersdb`, credentials définis dans la compose.
- cache (Redis) — cache pour les listes d'utilisateurs.
- adminer — interface web Adminer pour explorer la base (http://localhost:8080).

## Explication du `docker-compose.yml`

Fichier : `fullstack-app/docker-compose.yml` (version: '3.8') — points importants :

- version: '3.8'
	- Spécifie la version de schema Compose utilisée.

- services.web
	- build: ./app
		- Indique que l'image pour `web` est construite à partir du dossier `fullstack-app/app` (utilise le `Dockerfile` présent).
	- ports: "5000:5000"
		- Mappe le port 5000 du conteneur vers le port 5000 de l'hôte.
	- depends_on
		- db: condition: service_healthy
		- cache: condition: service_started
		- Ces conditions demandent à Docker Compose d'attendre la santé/démarrage des dépendances avant de démarrer (note: `condition` est disponible pour la compatibilité Compose V2; comportement exact dépend de la version de docker-compose utilisée).
	- environment
		- FLASK_ENV=production
		- Variables d'environnement passées au conteneur web.
	- healthcheck
		- test: ["CMD", "curl", "-f", "http://localhost:5000/users"]
		- interval/timeout/retries/start_period : paramètrent la fréquence et tolérance du check.
		- Le service `web` est considéré healthy si la requête HTTP vers `/users` réussit.

- services.db
	- image: postgres:15
	- environment
		- POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD : créent la base et l'utilisateur.
	- volumes
		- postgres_data:/var/lib/postgresql/data
		- Persistance des données PostgreSQL via un volume nommé (`postgres_data`).
	- healthcheck
		- test: ["CMD-SHELL", "pg_isready -U user -d usersdb"]
		- Vérifie que PostgreSQL est prêt à accepter des connexions.

- services.cache
	- image: redis:7-alpine
	- ports: "6379:6379" (optionnel si vous souhaitez accéder à Redis depuis l'hôte)
	- healthcheck
		- test: ["CMD", "redis-cli", "ping"]
		- Vérifie que Redis répond.

- services.adminer
	- image: adminer
	- ports: "8080:8080"
	- Fournit une interface web pour gérer la base PostgreSQL.

- volumes
	- postgres_data
		- Déclaré en bas du fichier ; stocke les données PostgreSQL en-dehors du cycle de vie des conteneurs.

Remarque sur `depends_on` et healthchecks : dans Compose v3+ la clé `condition` peut ne pas être supportée par toutes les versions de docker-compose; ici elle est utilisée pour décrire l'intention (attendre la readiness/health). Les healthchecks eux-mêmes sont effectifs et Composer utilisera l'état `healthy` quand disponible.

## Explication du `Dockerfile` de l'app

Fichier : `fullstack-app/app/Dockerfile`

Contenu principal et rôle de chaque étape :

1) FROM python:3.11-slim
	 - Image officielle Python (slim) : petite, adaptée pour les apps Python en production.
2) WORKDIR /app
	 - Définit le répertoire de travail dans le conteneur.
3) COPY requirements.txt .
	 - Copie uniquement les dépendances d'abord pour profiter du cache de build Docker lorsque requirements.txt n'a pas changé.
4) RUN pip install --no-cache-dir -r requirements.txt
	 - Installe les dépendances : Flask, psycopg2-binary, redis (versions verrouillées dans `requirements.txt`).
5) COPY . .
	 - Copie le code de l'application (app.py, etc.) dans le conteneur.
6) CMD ["python", "app.py"]
	 - Commande par défaut pour lancer l'application (Flask écoute sur 0.0.0.0:5000 dans `app.py`).

Cette construction optimise les rebuilds : tant que `requirements.txt` ne change pas, Docker réutilise la couche d'installation des paquets.

## Points d'intégration entre les fichiers

- Le code `fullstack-app/app/app.py` se connecte aux services en utilisant les noms des services Docker Compose comme hôtes :
	- PostgreSQL : host=`db`, database=`usersdb`, user=`user`, password=`password`
	- Redis : host=`cache`, port=6379

- Le service `web` invalide la clé `users_list` dans Redis quand l'API modifie la table `users`.

## Comment lancer la stack (exemples)

Depuis le dossier `fullstack-app` :

```powershell
# Démarrer en arrière-plan
docker-compose up -d --build

# Voir les logs (tous les services)
docker-compose logs -f

# Vérifier l'état
docker-compose ps

# Arrêter et supprimer les conteneurs (les volumes persistants restent)
docker-compose down

# Supprimer aussi les volumes (attention : supprime les données)
docker-compose down -v
```

## Tester l'API

Après `docker-compose up` :

```powershell
# Créer un utilisateur
curl -X POST http://localhost:5000/users -H "Content-Type: application/json" -d '{"name":"Yassine","email":"yassine@example.com"}'

# Lister les utilisateurs
curl http://localhost:5000/users

# Récupérer un utilisateur
curl http://localhost:5000/users/1
```

## Fichiers clés

- `fullstack-app/docker-compose.yml` : orchestre les services, ports, volumes et healthchecks.
- `fullstack-app/app/Dockerfile` : construction de l'image Python de l'API.
- `fullstack-app/app/app.py` : code Flask exposant les endpoints CRUD et initialisant la table `users`.
- `fullstack-app/app/requirements.txt` : dépendances Python (Flask, psycopg2-binary, redis).


---

Résumé : le dépôt fournit une stack complète et prête à l'emploi pour développer et tester une API Flask reliée à PostgreSQL et Redis. Le README ci-dessus documente le rôle des fichiers `docker-compose.yml` et `Dockerfile`, comment lancer la stack, et les points à améliorer pour une mise en production.


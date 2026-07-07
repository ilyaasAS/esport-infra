# Esport Hub - L'écosystème de gestion de ligue piloté par l'IA

Ce monorepo est le pilier d'orchestration de la plateforme Esport Hub.  
Sa mission est de livrer un environnement **de type production**, reproductible et sécurisé en une seule commande.

## Vision globale

La solution repose sur trois piliers indépendants et complémentaires au sein d'un dépôt unique:

- **`socle d'exploitation de la plateforme`**: pilotage du démarrage, des échanges entre composants, de la configuration et du cycle de vie des environnements.
- **`moteur de gestion de ligue`**: applique les règles métier, sécurise les accès et coordonne l'assistant Oracle.
- **`interface utilisateur de la ligue`**: espace de pilotage en temps réel pour consulter, créer et suivre les actions de la ligue.

Cette séparation de responsabilités garantit:

- isolation des responsabilités,
- évolutivité indépendante des composants,
- déploiement fiable via un socle d'infrastructure unifié.

## Socle technique (infrastructure)

| Domaine | Technologie | Rôle |
|---|---|---|
| Orchestration | Docker Compose | Démarrage et câblage des services |
| Base de données | MySQL 8 | Persistance transactionnelle |
| Moteur IA local | Ollama | Exécution du modèle LLM |
| API métier | Spring Boot (conteneur backend) | Exposition REST/SSE et logique métier |
| Interface web | Nginx + bundle Vite (conteneur frontend) | Distribution frontend optimisée |
| Construction | Constructions Docker multi-étapes | Compilation isolée, artefacts minimaux |

## Architecture d'orchestration Docker

Le `docker-compose.yml` relie les services suivants:

- **`db`**: MySQL 8 avec volume persistant `db_data` et vérification d'état.
- **`ollama`**: moteur IA local exposé sur `11434` avec volume `ollama_data`.
- **`ollama-pull-model`**: job d'initialisation pour précharger le modèle (`mistral`).
- **`backend`**: construction Java 21 multi-étapes, exposé sur `8080`, dépendant de `db`.
- **`frontend`**: construction Node/Nginx multi-étapes, exposé sur `80`, dépendant du `backend`.

Le chaînage `depends_on` + `vérification d'état` impose un démarrage ordonné et réduit les états instables au démarrage.

## Sécurité dès la conception

La posture de sécurité est native dans l'architecture:

- isolation réseau entre services Docker,
- secrets applicatifs externalisés via variables d'environnement,
- contrôle d'accès applicatif JWT côté backend,
- moteur IA local (pas d'exposition obligatoire à un service LLM public),
- conteneurs runtime allégés (artefacts de compilation uniquement).

## Variables d'environnement

| Fichier | Portée | Usage |
|---|---|---|
| `.env` (racine) | Infrastructure Compose | Variables d'orchestration (ex. `DB_ROOT_PASSWORD`) |
| `backend/.env` | Application backend | Secrets applicatifs (`JWT_SECRET`, `ADMIN_PASSWORD`, etc.) |
| `frontend/.env` | Construction/développement frontend | Configuration Vite (`VITE_API_BASE_URL`) |

## Procédure de démarrage local (monorepo)

### 1) Ouvrir le dépôt

```bash
cd esport
```

### 2) Préparer la configuration

```bash
cp .env.example .env
```

Renseigner les secrets requis (`DB_ROOT_PASSWORD`, etc.).  
Configurer également `backend/.env` et `frontend/.env` selon les modèles fournis.

### 3) Lancer l'Empire avec une seule commande

```bash
docker compose up -d --build
```

### 4) Vérifier l'état des services

```bash
docker compose ps
docker compose logs -f backend
```

## Points d'accès et adresses

- Frontend: [http://localhost](http://localhost)
- Service métier (accès applicatif): [http://localhost:8080/api](http://localhost:8080/api)
- Actuator santé: [http://localhost:8080/actuator/health](http://localhost:8080/actuator/health)
- Ollama: [http://localhost:11434](http://localhost:11434)

## Philosophie de livraison

Esport Hub est conçu pour être **Prêt pour la production**:

- compilation à l'intérieur des conteneurs,
- cohérence d'environnement entre développeurs, CI et déploiement,
- architecture modulaire, observable et sécurisée dès la conception.

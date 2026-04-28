# Esport Hub - L'écosystème de gestion de ligue piloté par l'IA

`esport-infra` est le pilier d'orchestration de la plateforme Esport Hub.  
Sa mission est de livrer un environnement **production-like**, reproductible et sécurisé en une seule commande.

## Vision globale

La solution repose sur trois piliers indépendants et complémentaires:

- **`esport-infra`**: orchestration Docker, réseau inter-services, variables d'environnement et cycle de vie runtime.
- **`esport-backend`**: cerveau métier Spring Boot + Oracle IA + sécurité applicative.
- **`esport-frontend`**: interface React orientée performance, expérience utilisateur temps réel, consommation API/SSE.

Cette séparation multi-dépôts garantit:

- isolation des responsabilités,
- évolutivité indépendante des composants,
- déploiement fiable via un socle d'infrastructure unifié.

## Stack technique (infra)

| Domaine | Technologie | Rôle |
|---|---|---|
| Orchestration | Docker Compose | Démarrage et câblage des services |
| Base de données | MySQL 8 | Persistence transactionnelle |
| Moteur IA local | Ollama | Exécution du modèle LLM |
| API métier | Spring Boot (conteneur backend) | Exposition REST/SSE et logique métier |
| Interface web | Nginx + bundle Vite (conteneur frontend) | Distribution frontend optimisée |
| Build | Multi-stage Docker builds | Compilation isolée, artefacts minimaux |

## Architecture d'orchestration Docker

Le `docker-compose.yml` relie les services suivants:

- **`db`**: MySQL 8 avec volume persistant `db_data` et healthcheck.
- **`ollama`**: moteur IA local exposé sur `11434` avec volume `ollama_data`.
- **`ollama-pull-model`**: job d'initialisation pour précharger le modèle (`mistral`).
- **`backend`**: build Java 21 multi-stage, exposé sur `8080`, dépendant de `db`.
- **`frontend`**: build Node/Nginx multi-stage, exposé sur `80`, dépendant du `backend`.

Le chaînage `depends_on` + `healthcheck` impose un démarrage ordonné et réduit les états instables au bootstrap.

## Secure by Design

La posture de sécurité est native dans l'architecture:

- isolation réseau entre services Docker,
- secrets applicatifs externalisés via variables d'environnement,
- contrôle d'accès applicatif JWT côté backend,
- moteur IA local (pas d'exposition obligatoire à un service LLM public),
- conteneurs runtime allégés (artefacts de build uniquement).

## Variables d'environnement

| Fichier | Portée | Usage |
|---|---|---|
| `.env` (racine) | Infrastructure Compose | Variables d'orchestration (ex. `DB_ROOT_PASSWORD`) |
| `backend/.env` | Application backend | Secrets applicatifs (`JWT_SECRET`, `ADMIN_PASSWORD`, etc.) |
| `frontend/.env` | Build/dev frontend | Configuration Vite (`VITE_API_BASE_URL`) |

## Procédure de déploiement (3 dépôts)

### 1) Cloner les trois dépôts

```bash
mkdir esport-hub && cd esport-hub
git clone <URL_GIT_ESPORT_INFRA> esport-infra
git clone <URL_GIT_ESPORT_BACKEND> esport-backend
git clone <URL_GIT_ESPORT_FRONTEND> esport-frontend
```

### 2) Préparer la configuration

```bash
cd esport-infra
cp .env.example .env
```

Renseigner les secrets requis (`DB_ROOT_PASSWORD`, etc.).  
Configurer également `esport-backend/.env` et `esport-frontend/.env` selon les modèles fournis.

### 3) Lancer l'Empire avec une seule commande

```bash
docker compose up -d --build
```

### 4) Vérifier l'état des services

```bash
docker compose ps
docker compose logs -f backend
```

## Endpoints et accès

- Frontend: [http://localhost](http://localhost)
- Backend API: [http://localhost:8080/api](http://localhost:8080/api)
- Actuator santé: [http://localhost:8080/actuator/health](http://localhost:8080/actuator/health)
- Ollama: [http://localhost:11434](http://localhost:11434)

## Philosophie de livraison

Esport Hub est conçu pour être **Production-Ready**:

- compilation à l'intérieur des conteneurs,
- cohérence d'environnement entre développeurs, CI et déploiement,
- architecture modulaire, observable et sécurisée dès la conception.

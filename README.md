# Esport — monorepo (frontend, backend, Docker)

## Fichiers d’environnement (une seule source de vérité par usage)

| Fichier | Rôle | Quand l’utiliser |
|--------|------|-------------------|
| **`.env` à la racine** (`/esport/.env`) | **Docker Compose uniquement** | Copie de `.env.example` racine. Contient **`DB_ROOT_PASSWORD`** : mot de passe root MySQL injecté dans le service `db` et, pour le conteneur backend, **`DB_PASSWORD`** (via interpolation `${DB_ROOT_PASSWORD}` dans `docker-compose.yml`). **Ne pas y mettre `JWT_SECRET`** : ce n’est pas lu par Spring. |
| **`.env.example` à la racine** | Modèle pour la racine | Documente `DB_ROOT_PASSWORD` avec un exemple ; à copier vers `.env`. |
| **`backend/.env`** | **Application Spring Boot** (local ou conteneur) | **`JWT_SECRET`**, **`DB_PASSWORD`** (hors Docker Compose tu le renseignes à la main ; avec Compose il est surchargé par la variable d’environnement du service), **`ADMIN_PASSWORD`**, **`OLLAMA_BASE_URL`**, etc. **C’est la source des secrets applicatifs.** |
| **`backend/.env.example`** | Modèle pour le backend | Liste les clés attendues sans valeurs secrètes. |
| **`frontend/.env`** | **Build / dev Vite** | Copie de `frontend/.env.example`. Définit notamment **`VITE_API_BASE_URL`** (URL de l’API, ex. `http://localhost:8080/api`) — utilisée par `httpClient` et `getApiRootUrl()`. |

### Cohérence des variables critiques

- **`DB_PASSWORD` (Spring)** doit être le **même** que le mot de passe MySQL root utilisé par le conteneur `db`. Avec Docker Compose, définis **`DB_ROOT_PASSWORD`** dans **`.env` racine** : Compose applique la même valeur au backend comme `DB_PASSWORD`.
- **`JWT_SECRET`** : défini **uniquement** dans `backend/.env`. Si tu le changes, les anciens JWT deviennent invalides — déconnexion puis nouvelle connexion.

### Commandes utiles

```bash
# Depuis la racine du dépôt
docker compose up -d --build
```

---

## Sécurité des rôles (rappel)

- **`USER`** et **`ADMIN`** : règles dans `backend/.../SecurityConfig.java` — `POST /api/players` réservé aux utilisateurs authentifiés (USER ou ADMIN), `POST /api/matches` réservé aux **ADMIN** ; le reste de `/api/**` exige une session JWT valide.

---

## Frontend

- **`VITE_API_BASE_URL`** : voir `frontend/.env.example` ; sans cette variable, le client HTTP utilise `http://localhost:8080/api` par défaut.
- Voir aussi `frontend/README.md` pour le template Vite.

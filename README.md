# Flux Meta Marketplace — Hyundai St-Raymond

Serveur Flask qui scrape l'inventaire d'occasion de hyundaistraymond.com
et génère un flux CSV compatible Meta Commerce Manager, mis à jour toutes les 6h.

## Routes disponibles

| URL | Description |
|-----|-------------|
| `/feed.csv` | ✅ Flux CSV à fournir à Meta |
| `/health` | Statut du serveur et du cache |
| `/refresh?token=TOKEN` | Force un rechargement immédiat |

## Déploiement sur Railway

### 1. Créer un compte Railway
Aller sur [railway.app](https://railway.app) et se connecter avec GitHub.

### 2. Déployer le projet
```bash
# Option A : via GitHub (recommandé)
# 1. Créer un repo GitHub avec ces fichiers
# 2. Dans Railway : New Project → Deploy from GitHub repo

# Option B : via CLI
npm install -g @railway/cli
railway login
railway init
railway up
```

### 3. Configurer la variable d'environnement
Dans Railway → Variables :
```
REFRESH_TOKEN=votre-token-secret-ici
```

### 4. Obtenir votre URL
Railway génère automatiquement une URL publique, ex :
`https://hyundai-feed-production.up.railway.app`

### 5. Fournir l'URL à Meta
Dans Meta Commerce Manager → Sources de données → URL du flux :
```
https://hyundai-feed-production.up.railway.app/feed.csv
```

Meta viendra chercher ce fichier automatiquement toutes les 24h.

## Structure du projet

```
hyundai-feed/
├── app/
│   ├── __init__.py
│   ├── scraper.py    # Scrape hyundaistraymond.com
│   ├── cache.py      # Cache 6h pour éviter trop de requêtes
│   └── main.py       # Serveur Flask + routes
├── wsgi.py           # Point d'entrée Gunicorn
├── requirements.txt  # Flask + Gunicorn
├── Procfile          # Commande de démarrage Railway
└── railway.toml      # Config Railway
```

## Forcer un rechargement manuel

```
https://votre-url.railway.app/refresh?token=votre-token-secret-ici
```

## Vérifier le statut

```
https://votre-url.railway.app/health
```
Retourne : `{"status": "ok", "vehicles_in_cache": 74, "cache_age_minutes": 12.3}`

# YouTube-Search-ML-App

A smart YouTube search application powered by Machine Learning. It allows users to search for YouTube videos using natural language queries, leveraging ML models to understand user intent and surface the most relevant video content.

## Features

- Natural language YouTube video search
- ML-powered semantic understanding of search queries
- Context-aware and intent-driven search results
- Multiple ML approaches: Classical ML, PyTorch, TensorFlow, AWS SageMaker, LLMs
- RESTful FastAPI backend
- Two Angular portals: end-user search & admin model builder

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** & **npm**
- **Angular CLI** (`npm install -g @angular/cli`)

---

## Getting Started

### 1. Install Python Dependencies

```bash
npm run env-setup:init:install
```

Installs all Python packages from `requirements.txt`.

### 2. Install Portal Dependencies

```bash
npm run env-setup:portals:install
```

Installs npm dependencies for both Angular portals (`youtube-search` and `youtube-search-admin`).

---

## NPM Commands

| Command | Description |
|---|---|
| `npm run env-setup:init:install` | Install Python dependencies from `requirements.txt` |
| `npm run env-setup:portals:install` | Install npm dependencies for both Angular portals |
| `npm run app-api-web:start` | Start all services (FastAPI backend + both Angular portals) |
| `npm run app-api-web:status` | Check running status of all services |
| `npm run app-api-web:stop` | Stop all running services |
| `npm run portal:search:start` | Start the end-user search portal only (port 4200) |
| `npm run portal:admin:start` | Start the admin portal only (port 4201) |

---

## Services & Ports

| Service | Port | URL |
|---|---|---|
| FastAPI Backend | 8000 | http://localhost:8000 |
| API Docs (Swagger) | 8000 | http://localhost:8000/docs |
| YouTube Search Portal | 4200 | http://localhost:4200 |
| YouTube Search Admin Portal | 4201 | http://localhost:4201 |

All ports are overridable via environment variables: `API_PORT`, `PORTAL_PORT`, `ADMIN_PORT`.

---

## Project Structure

```
YouTube-Search-ML-App/
├── package.json                    # Deployment task runner (not a JS project)
├── requirements.txt                # Python dependencies
├── apis.json → app/apis.json       # API module registry
├── Scripts/
│   ├── api-web-start.sh            # Start all services
│   ├── api-web-status.sh           # Check service status
│   └── api-web-stop.sh             # Stop all services
├── app/
│   ├── main.py                     # FastAPI entry point
│   ├── apis.json                   # Registered API modules
│   ├── app_common/
│   │   ├── api_initializer.py      # Class-based API initializer
│   │   ├── app_info.py             # /info endpoint
│   │   └── dtos/
│   │       ├── init_dtos.py        # InitDTO (FastAPI + context)
│   │       └── model_location_dto.py
│   ├── app_model_builder/
│   │   ├── api/
│   │   │   └── builder_health.py   # /builder/health endpoint
│   │   ├── handlers/
│   │   │   └── model_location_resolver.py
│   │   └── pipeline/
│   └── app_model_serving/
│       └── api/
│           ├── api_manager.py      # FastAPI app factory
│           └── health_check.py     # /health_check endpoint
├── Portals/
│   ├── youtube-search/             # End-user Angular portal (port 4200)
│   └── youtube-search-admin/       # Admin Angular portal (port 4201)
```

---

## Portals

### YouTube Search (End-User)

- **Port:** 4200
- **Theme:** Warm sunset gradient (coral, amber, teal)
- Select a pre-published ML model and search for YouTube videos
- Results displayed in a card grid with thumbnails

### YouTube Search Admin

- **Port:** 4201
- **Theme:** Cool ocean palette (deep blue, sky blue, mint)
- Select ML approach (Classical ML, PyTorch, TensorFlow, SageMaker, LLM)
- Enter YouTube API key — stored in browser `localStorage` only, **never sent to backend**
- Trigger model builds and optionally publish as latest

---

## License

See [LICENSE](LICENSE) for details.

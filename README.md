# travel-agent-service

A production-ready FastAPI backend for an AI Travel Agent application with a modular architecture designed for RAG (Retrieval-Augmented Generation) and LLM agent integration.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Agent Architecture](#agent-architecture)
- [API Endpoints](#api-endpoints)
- [Run Locally](#run-locally)
- [Run with Docker](#run-with-docker)
- [Debug with Docker](#debug-with-docker)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)

---

## Architecture Overview

```
travel-agent-service/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py              # POST /chat
│   │   │   ├── recommendations.py   # POST /recommend-trip
│   │   │   └── user.py              # GET/POST /user-profile
│   │   └── router.py               # Aggregates all route routers
│   ├── core/
│   │   ├── config.py               # Pydantic settings (reads from .env)
│   │   └── dependencies.py         # FastAPI dependency injection helpers
│   ├── agents/
│   │   ├── agent.py                # TravelAgent — main conversational LLM agent with tool use
│   │   ├── preference_extractor.py # PreferenceExtractorAgent — structured preference extraction
│   │   ├── recommendations_agent.py # RecommendationsAgent — portfolio-aware destination recommender
│   │   └── providers.py            # LLMProvider abstraction + create_provider() factory
│   ├── rag/
│   │   ├── embeddings.py           # Placeholder embedding service
│   │   └── retriever.py            # Placeholder document retriever
│   ├── services/
│   │   ├── chat_service.py         # Orchestrates agent calls and profile updates
│   │   ├── recommendation_service.py # Returns travel recommendations (mocked)
│   │   └── user_service.py         # In-memory user profile store
│   ├── models/
│   │   ├── schemas.py              # Pydantic request/response models
│   │   └── domain.py               # Internal domain dataclasses
│   └── main.py                     # FastAPI application entry point
├── infra/
│   ├── docker/
│   │   └── docker-compose.yml
│   └── terraform/                  # Placeholder for AWS IaC
├── data/                           # Local documents for RAG (future use)
├── tests/
│   └── test_api.py
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

**Key design decisions:**
- **Routes** are thin — they delegate all logic to **services**.
- **Services** orchestrate business logic and call the **agent**.
- **TravelAgent** uses the Strands Agents SDK. It exposes `RecommendationsAgent` as a callable tool so the LLM decides autonomously when to fetch destination suggestions.
- **RAG modules** (`embeddings.py`, `retriever.py`) are structured stubs ready for integration.
- **DynamoDB** is used as the persistent user profile store (local DynamoDB for development).

---

## Agent Architecture

The service uses three specialised LLM agents, each independently configurable via environment variables (see [Environment Variables](#environment-variables)).

```
User message
     │
     ▼
┌─────────────────────────────────────────────┐
│              TravelAgent                    │
│  (app/agents/agent.py)                      │
│                                             │
│  1. PreferenceExtractorAgent                │
│     └─ Extracts structured preferences      │
│        from the raw user message            │
│                                             │
│  2. Main Strands agent (conversational)     │
│     └─ Receives enriched message with       │
│        known preferences prepended          │
│     └─ Has access to tool:                  │
│        get_travel_recommendations           │
│           │                                 │
│           ▼  (called only when the LLM      │
│              decides to propose trips)      │
│        RecommendationsAgent                 │
│        └─ Queries agency portfolio with     │
│           user preferences as context       │
│           and returns 2-3 destinations      │
└─────────────────────────────────────────────┘
     │
     ▼
  AgentResult
  ├── reply                  (conversational response)
  ├── extracted_preferences  (merged UserPreferences)
  └── recommendations_preview (destinations if tool was called, else [])
```

### Agents

| Agent | File | Role |
|-------|------|------|
| `TravelAgent` | `app/agents/agent.py` | Main conversational agent. Merges preferences, enriches the prompt, and invokes the Strands LLM with the recommendations tool available. |
| `PreferenceExtractorAgent` | `app/agents/preference_extractor.py` | Uses structured output to pull `travel_style`, `budget`, `destinations`, `interests`, and `dietary_restrictions` from a free-text message. |
| `RecommendationsAgent` | `app/agents/recommendations_agent.py` | Portfolio-aware recommender. Contains the agency's full catalogue of destinations and packages. Called as a Strands tool (`get_travel_recommendations`) only when the main agent decides to propose trips. Returns 2-3 tailored destinations. |

### `get_travel_recommendations` tool

Registered on `TravelAgent`'s Strands agent. The LLM calls it autonomously when it is ready to propose specific destinations. Parameters (all optional strings the model fills from conversation context):

| Parameter | Description |
|-----------|-------------|
| `travel_style` | e.g. `beach`, `adventure`, `cultural`, `city break`, `ski`, `luxury` |
| `budget` | e.g. `luxury`, `mid-range`, `2000` |
| `preferred_destinations` | Comma-separated regions/countries |
| `interests` | Comma-separated interests, e.g. `hiking, diving` |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/health` | Health check |
| `POST` | `/chat` | Send a message, get a reply + extracted preferences + recommendations preview |
| `POST` | `/recommend-trip` | Get a list of travel recommendations (filterable) |
| `GET`  | `/user-profile` | Retrieve the current user profile |
| `POST` | `/user-profile` | Update user preferences |

Interactive docs are available at [http://localhost:8000/docs](http://localhost:8000/docs) when running.

---

## Run Locally

### Prerequisites

- [pyenv](https://github.com/pyenv/pyenv) with Python 3.12.13

```bash
pyenv install 3.12.13
```

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/szymek25/travel-agent-service.git
cd travel-agent-service

# 2. Pin the Python version for this project
pyenv local 3.12.13

# 3. Create a virtual environment using the pinned Python
python -m venv .venv
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Copy and edit the environment file
cp .env.example .env

# 6. Start the server
uvicorn app.main:app --reload

# The API is now available at http://localhost:8000
```

### Run Tests

```bash
.venv/bin/pytest tests/ -v
```

---

## Run with Docker

```bash
# From the repo root
docker compose -f infra/docker/docker-compose.yml up --build
```

The API will be available at [http://localhost:8000](http://localhost:8000).

---

## Debug with Docker

A self-contained `docker-compose.debug.yml` is provided that starts both the API (with `debugpy`) and a local DynamoDB instance.

### Prerequisites

- [VS Code](https://code.visualstudio.com/) with the [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)

### Steps

```bash
# 1. Start the debug stack (from infra/docker/)
podman-compose -f docker-compose.debug.yml up --build
```

The container will pause and wait for a debugger to attach before starting the server.

```bash
# 2. In VS Code, open the Run & Debug panel (Ctrl+Shift+D / Cmd+Shift+D)
#    Select "Docker: Attach debugpy" and press F5
```

The API will be available at [http://localhost:8000](http://localhost:8000) once the debugger attaches. Set breakpoints anywhere in the source — they will be hit on the next matching request.

> **Note:** Hot-reload is disabled in debug mode because uvicorn's file watcher spawns child processes that break debugpy attachment. Rebuild the container (`--build`) to pick up code changes.

---

## Environment Variables

Copy `.env.example` to `.env` and adjust values as needed.

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV` | `development` | Runtime environment (`development`, `staging`, `production`) |
| `LLM_PROVIDER` | `ollama` | LLM backend to use (`ollama` or `bedrock`) |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server address (used when `LLM_PROVIDER=ollama`) |
| `OLLAMA_MODEL_ID` | `llama3.1` | Global default Ollama model (used when `LLM_PROVIDER=ollama`) |
| `OLLAMA_MODEL_ID_TRAVEL_AGENT` | _(empty)_ | Ollama model override for the main travel agent; falls back to `OLLAMA_MODEL_ID` |
| `OLLAMA_MODEL_ID_EXTRACTOR_AGENT` | _(empty)_ | Ollama model override for the preference extractor; falls back to `OLLAMA_MODEL_ID` |
| `OLLAMA_MODEL_ID_RECOMMENDATIONS_AGENT` | _(empty)_ | Ollama model override for the recommendations agent; falls back to `OLLAMA_MODEL_ID` |
| `BEDROCK_MODEL_ID` | `us.anthropic.claude-sonnet-4-20250514-v1:0` | Global default Bedrock model (used when `LLM_PROVIDER=bedrock`) |
| `BEDROCK_MODEL_ID_TRAVEL_AGENT` | _(empty)_ | Bedrock model override for the main travel agent; falls back to `BEDROCK_MODEL_ID` |
| `BEDROCK_MODEL_ID_EXTRACTOR_AGENT` | _(empty)_ | Bedrock model override for the preference extractor; falls back to `BEDROCK_MODEL_ID` |
| `BEDROCK_MODEL_ID_RECOMMENDATIONS_AGENT` | _(empty)_ | Bedrock model override for the recommendations agent; falls back to `BEDROCK_MODEL_ID` |
| `SESSION_STORAGE_DIR` | `/tmp/travel-agent-sessions` | Local path for `FileSessionManager` storage; swap for `S3SessionManager` on AWS |
| `DYNAMODB_ENDPOINT_URL` | `http://localhost:8001` | DynamoDB endpoint (use local URL for dev, omit for AWS) |
| `DYNAMODB_TABLE_USER_PROFILES` | `UserProfiles` | DynamoDB table name for user profiles |
| `AWS_REGION` | `us-east-1` | AWS region |
| `AWS_ACCESS_KEY_ID` | `dummy` | AWS access key (`dummy` is fine for local DynamoDB) |
| `AWS_SECRET_ACCESS_KEY` | `dummy` | AWS secret key (`dummy` is fine for local DynamoDB) |

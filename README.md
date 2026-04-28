# travel-agent-service

A production-ready FastAPI backend for an AI Travel Agent application with a modular architecture designed for RAG (Retrieval-Augmented Generation) and LLM agent integration.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [API Endpoints](#api-endpoints)
- [Run Locally](#run-locally)
- [Run with Docker](#run-with-docker)
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
│   │   └── agent.py                # TravelAgent — placeholder for LLM integration
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
- The **TravelAgent** is a placeholder that will be replaced by an LLM-backed agent.
- **RAG modules** (`embeddings.py`, `retriever.py`) are structured stubs ready for integration.
- **In-memory user profile** — will be replaced by a persistent store (e.g. DynamoDB) on AWS.

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

- Python 3.12+

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/szymek25/travel-agent-service.git
cd travel-agent-service

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate      # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and edit the environment file
cp .env.example .env

# 5. Start the server
uvicorn app.main:app --reload

# The API is now available at http://localhost:8000
```

### Run Tests

```bash
pytest tests/ -v
```

---

## Run with Docker

```bash
# From the repo root
docker compose -f infra/docker/docker-compose.yml up --build
```

The API will be available at [http://localhost:8000](http://localhost:8000).

---

## Environment Variables

Copy `.env.example` to `.env` and adjust values as needed.

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV` | `development` | Runtime environment (`development`, `staging`, `production`) |
| `LLM_PROVIDER` | `openai` | LLM backend to use (future integration) |
| `VECTOR_STORE` | `chroma` | Vector store for RAG (future integration) |

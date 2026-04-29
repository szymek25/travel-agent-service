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
│   │   ├── agent.py                # TravelAgent — Strands-backed LLM agent
│   │   └── providers.py            # LLMProvider abstraction (OllamaProvider, BedrockProvider)
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

## Environment Variables

Copy `.env.example` to `.env` and adjust values as needed.

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV` | `development` | Runtime environment (`development`, `staging`, `production`) |
| `LLM_PROVIDER` | `ollama` | LLM backend to use (`ollama` or `bedrock`) |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server address (used when `LLM_PROVIDER=ollama`) |
| `OLLAMA_MODEL_ID` | `llama3.1` | Ollama model name (used when `LLM_PROVIDER=ollama`) |
| `BEDROCK_MODEL_ID` | `us.anthropic.claude-sonnet-4-20250514-v1:0` | Bedrock model ID (used when `LLM_PROVIDER=bedrock`) |
| `VECTOR_STORE` | `chroma` | Vector store for RAG (future integration) |
| `DYNAMODB_ENDPOINT_URL` | `http://localhost:8001` | DynamoDB endpoint (use local URL for dev, omit for AWS) |
| `DYNAMODB_TABLE_USER_PROFILES` | `UserProfiles` | DynamoDB table name for user profiles |
| `AWS_REGION` | `us-east-1` | AWS region |
| `AWS_ACCESS_KEY_ID` | `dummy` | AWS access key (`dummy` is fine for local DynamoDB) |
| `AWS_SECRET_ACCESS_KEY` | `dummy` | AWS secret key (`dummy` is fine for local DynamoDB) |

# GenIA Agents Demo

A streamlined demo that combines a FastAPI backend, a Starlite UI, and PostgreSQL with the pgvector extension. Use it to upload documents, store embeddings, query the vector store, and interact with the NL2SQL workflow running directly in the backend.

## Stack

- **FastAPI** – Exposes HTTP endpoints for embeddings, pgvector access, and agent chat.
- **Starlite** – Provides a lightweight web app for document ingestion, SQL exploration, and natural-language queries.
- **PostgreSQL + pgvector** – Persists embeddings in chunk-sized tables (`vector_embeddings_*`).
- **LangChain + OpenAI** – Powers the NL2SQL orchestration behind the conversational endpoints.

## Prerequisites

- Docker & Docker Compose
- Python 3.10+ (for local development outside containers)
- An OpenAI API key

Create a `.env` file in `src/` (see `src/.env` for the template) with database credentials and model settings if you plan to run the apps outside Docker.

## Quickstart (Docker)

1. **Start the stack**
   ```bash
   ./architecture/start_all.sh up
   ```
   This builds the Docker images (backend, frontend, pgvector) and starts them in detached mode.

2. **Access the services**
   - Backend API: [http://localhost:8001](http://localhost:8001)
   - Frontend UI: [http://localhost:3000](http://localhost:3000)
   - PostgreSQL (pgvector): exposed on `localhost:5432`

3. **Stop or inspect**
   ```bash
   ./architecture/start_all.sh logs   # Tail container logs
   ./architecture/start_all.sh down   # Tear everything down
   ```

## Running Locally Without Docker

1. **Install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Provision PostgreSQL with pgvector**
   Start a PostgreSQL instance that has the `pgvector` extension enabled, then run `databases/vector_db/creation_script/vector_db.sql` to create the expected tables.

3. **Launch the apps**
   ```bash
   ./architecture/start_backend.sh   # FastAPI on http://localhost:8001
   ./architecture/start_frontend.sh  # Starlite UI on http://localhost:3000
   ```

## FastAPI Endpoints

| Method | Path                | Description |
|--------|--------------------|-------------|
| GET    | `/healthz`          | Health probe with database status.
| GET    | `/vector_databases` | List dataset labels stored in the vector tables.
| POST   | `/compute_vectors`  | Chunk text and compute embeddings.
| POST   | `/text_to_vectordb` | Compute embeddings and persist them in pgvector.
| POST   | `/upload_pdf`       | Extract text from a PDF and store the embeddings.
| POST   | `/agents_chat`      | Trigger the NL2SQL agent workflow.
| POST   | `/execute_query`    | Run ad-hoc SQL against PostgreSQL.

## Starlite Frontend

The single-page app renders three workflows:

1. **Upload Knowledge Source** – send PDFs to `upload_pdf`, optionally tagging them with a dataset label.
2. **Run SQL** – execute queries against the configured PostgreSQL database.
3. **Talk with the Agents** – ask natural-language questions that the NL2SQL workflow solves.

Dataset dropdowns are populated from the FastAPI `/vector_databases` endpoint. The UI communicates directly with the backend using `fetch` and handles both success and error states inline.

## Configuration

Environment variables (see `src/.env` for defaults):

- `OPENAI_API_KEY`, `GPT_MODEL`, `GPT_EMBEDDING_ENGINE`
- `POSTGRESQL_HOST`, `POSTGRESQL_PORT`, `POSTGRESQL_DATABASE`, `POSTGRESQL_USER`, `POSTGRESQL_PASSWORD`
- Optional: `BACKEND_URL`, `DEFAULT_CHUNK_SIZE`, `PGVECTOR_TABLE`, `PGVECTOR_DIMENSIONS`, `PGVECTOR_TOP_K`

## Repository Layout

```
architecture/
├── backend/              # Backend Dockerfile
├── frontend/             # Frontend Dockerfile
├── docker-compose.yml    # Three-service stack (backend, frontend, pgvector)
├── start_all.sh          # Helper to manage the compose stack
├── start_backend.sh      # Local dev launcher for FastAPI
└── start_frontend.sh     # Local dev launcher for Starlite
src/
├── api/                  # FastAPI app, schemas, and service layer
├── agents/               # Agent definitions
├── langchain_app/        # NL2SQL workflow and settings
├── starlite_app/         # Frontend factory, routes, and template
└── ...                   # Supporting utilities and assets
```

## Development Tips

- Run the backend with `uvicorn api:app --reload --port 8001` for hot reloading.
- Start the Starlite UI with `uvicorn starlite_app:create_app --factory --reload --port 3000` during development.
- Keep `DEFAULT_CHUNK_SIZE` in sync between the backend and frontend so vector tables match the expected dimensions.

## License

MIT

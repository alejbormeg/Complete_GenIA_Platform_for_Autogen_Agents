# GenIA Agents Demo

A streamlined demo that combines Ray Serve deployments, a FastAPI backend, a Starlite UI, and PostgreSQL with the pgvector extension. Use it to upload documents, store embeddings, query the vector store, and interact with the NL2SQL agent workflow running on Ray.

## Stack

- **Ray Serve** – Hosts the agent workflow (`RAGChatEndpoint`), embedding pipeline, and pgvector connector.
- **FastAPI** – Exposes HTTP endpoints that proxy the Ray deployments.
- **Starlite** – Provides a small web app for document ingestion, SQL exploration, and agent chat.
- **PostgreSQL + pgvector** – Persists embeddings in chunk-sized tables (`vector_embeddings_*`).

## Prerequisites

- Docker & Docker Compose (for the Ray cluster)
- Python 3.10+
- PostgreSQL instance with the `pgvector` extension enabled
- An OpenAI API key

Create a `.env` file in `src/` (see `src/.env` for the template) with database credentials and model settings.

## Quickstart

1. **Install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Start PostgreSQL** (local instance or container) and run `databases/vector_db/creation_script/vector_db.sql`.

3. **Launch the Ray cluster**
   ```bash
   ./architecture/start_all.sh
   ```
   The script creates the shared Docker network (if needed) and starts the Ray head node.

4. **In separate terminals, start the applications**
   ```bash
   ./architecture/start_backend.sh   # FastAPI on http://localhost:8001
   ./architecture/start_frontend.sh  # Starlite UI on http://localhost:3000
   ```

5. **Deploy the Ray Serve graph**
   ```bash
   PYTHONPATH=src python src/ray_endpoints.py
   ```
   This wires up the embedding pipeline, pgvector connector, and NL2SQL agent inside the running Ray cluster.

6. **Open the UI**
   Visit [http://localhost:3000](http://localhost:3000) to upload PDFs, inspect vectors, and chat with the agents.

## FastAPI Endpoints

| Method | Path                | Description |
|--------|--------------------|-------------|
| GET    | `/healthz`          | Health probe with the Ray address.
| GET    | `/vector_databases` | List dataset labels stored in the vector tables.
| POST   | `/compute_vectors`  | Chunk text and compute embeddings.
| POST   | `/text_to_vectordb` | Compute embeddings and persist them in pgvector.
| POST   | `/upload_pdf`       | Extract text from a PDF and store the embeddings.
| POST   | `/agents_chat`      | Trigger the NL2SQL agent workflow.
| POST   | `/execute_query`    | Run ad-hoc SQL against PostgreSQL.

All endpoints proxy the Ray Serve deployments; responses contain JSON-serialised results.

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
- `RAY_ADDRESS` (defaults to `ray://localhost:10001`)
- Optional: `BACKEND_URL`, `DEFAULT_CHUNK_SIZE`

## Repository Layout

```
architecture/            # Scripts for Ray cluster, backend, and UI launchers
└── ray_cluster/         # Ray head Dockerfile and compose setup
src/
├── api/                 # FastAPI app and schemas
├── ray_endpoints/       # Ray Serve deployments (agents, embeddings, pgvector)
├── starlite_app/        # Frontend factory, routes, and template
└── ...                  # Agents, embeddings, and utilities supporting the workflow
```

## Development Tips

- Run the backend with `uvicorn api:app --reload --port 8001` for hot reloading.
- Start the Starlite UI with `uvicorn starlite_app:create_app --factory --reload --port 3000` during development.
- Redeploy Ray Serve after code changes that affect deployments: `PYTHONPATH=src python src/ray_endpoints.py`.

## License

MIT

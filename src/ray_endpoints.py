import os
import logging

import ray
from dotenv import load_dotenv

import agents
import utils
from ray import serve

from ray_endpoints.set_up_agents_chat import RAGChatEndpoint
from ray_endpoints.set_up_embeddings import ChunkStrategy, EmbeddingEndpoints, Text2Vectors
from ray_endpoints.set_up_pgvector import PGVectorConnection


@serve.deployment(route_prefix=None, ray_actor_options={"num_cpus": 0})
class BootstrapApp:
    """Keeps dependent deployments alive without exposing an HTTP endpoint."""

    def __init__(self, text_to_vectors, pgvector, agents_chat):
        self.text_to_vectors = text_to_vectors
        self.pgvector = pgvector
        self.agents_chat = agents_chat

    async def __call__(self):  # pragma: no cover - defensive noop
        return {"status": "ready"}

load_dotenv()

logger = logging.getLogger()

# Initialize Ray and Serve
ray_address = os.getenv("RAY_ADDRESS", "ray://localhost:10001")
ray.init(address=ray_address, runtime_env={"py_modules": [utils, agents]})
serve.start(detached=True, http_options={"host": "0.0.0.0"})

test2vectors_app = Text2Vectors.bind(ChunkStrategy.bind(), EmbeddingEndpoints.bind())
pgvector_app = PGVectorConnection.bind()
agents_chat = RAGChatEndpoint.bind()
bootstrap_app = BootstrapApp.bind(test2vectors_app, pgvector_app, agents_chat)

serve.run(bootstrap_app)

print("Ray Serve deployments are ready: Text2Vectors, PGVectorConnection, RAGChatEndpoint.")

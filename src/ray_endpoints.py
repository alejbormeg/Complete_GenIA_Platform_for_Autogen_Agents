import ray
import os
import logging
import utils
import agents
from ray_endpoints.set_up_agents_chat import RAGChatEndpoint
from ray_endpoints.set_up_embeddings import Text2Vectors, ChunkStrategy, EmbeddingEndpoints
from ray_endpoints.setup_api_gateway import APIGateway
from ray_endpoints.set_up_pgvector import PGVectorConnection
from dotenv import load_dotenv
from ray import serve

load_dotenv()

logger = logging.getLogger()

# Initialize Ray and Serve
os.environ['RAY_ADDRESS'] = "ray://localhost:10001"
ray.init(runtime_env={"py_modules": [utils, agents]})
serve.start(detached=True, http_options={"host": "0.0.0.0"})

runtime_env = {
    "conda": "src/utils/conda_environments/conda.yaml"
}

test2vectors_app = Text2Vectors.bind(ChunkStrategy.bind(), EmbeddingEndpoints.bind())
pgvector_app = PGVectorConnection.bind()
agents_chat = RAGChatEndpoint.bind()
api_gateway_app = APIGateway.bind(test2vectors_app, pgvector_app, agents_chat)

# Use serve.run to deploy with the runtime environment
serve.run(api_gateway_app, route_prefix="/api")

print("Deployed Text2Vectors, ChunkStrategy, and EmbeddingEndpoints on the Ray cluster.")

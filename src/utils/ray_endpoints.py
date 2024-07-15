import ray
import os
from ray import serve
from ray.serve.handle import DeploymentHandle
from typing import List

@serve.deployment
class Text2Vectors:
    def __init__(
        self, chunk_method: DeploymentHandle, embedding_endpoint: DeploymentHandle
    ):
        self.chunk_method = chunk_method
        self.embedding_endpoint = embedding_endpoint

    async def __call__(self, http_request):
        request = await http_request.json()
        text, chunk_size, embedding_model = request["text"], request["chunk_size"], request["embedding_model"]

        chunks = await self.chunk_method.chunk_fixed.remote(text, chunk_size)

        embeddings = [await self.embedding_endpoint.create_embedding.remote(chunk, embedding_model, chunk_size) for chunk in chunks]

        return embeddings

@serve.deployment
class ChunkStrategy:
    def chunk_fixed(self, sentences: List[str], chunk_size: int) -> List[List[str]]:
        return [sentences[i:i + chunk_size] for i in range(0, len(sentences), chunk_size)]

@serve.deployment
class EmbeddingEndpoints:
    # Function to create embeddings
    def create_embedding(self, text: str, model: str, dimensions: int = None) -> List[float]:
        import openai
        if model == "text-embedding-3-large":
            response = openai.embeddings.create(model=model, input=text, dimensions=dimensions).data[0].embedding
        else:
            response = openai.embeddings.create(model=model, input=text).data[0].embedding[:dimensions]

        return response

# Initialize Ray and Serve
os.environ['RAY_ADDRESS'] = "ray://localhost:10001"
ray.init()
serve.start()

runtime_env = {
    "conda": "src/utils/conda_environments/conda.yaml"
}

# Use serve.run to deploy with the runtime environment
serve.run(Text2Vectors.bind(ChunkStrategy.bind(), EmbeddingEndpoints.bind()), route_prefix="/text2vectors")

print("Deployed Text2Vectors, ChunkStrategy, and EmbeddingEndpoints on the Ray cluster.")

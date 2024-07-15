import ray
import os
import psycopg2
from ray import serve
from ray.serve.handle import DeploymentHandle
from typing import List
from psycopg2.extras import execute_values

@serve.deployment
class PGVectorConnection:
    def __init__(self, text_to_vectors: DeploymentHandle) -> None:
        self.text2vectors = text_to_vectors
        
    async def __call__(self, http_request):
        request = await http_request.json()
        vectors = await self.text2vectors.chunk_fixed.compute_vectors.remote(request=request)
        print(f"Embeddings: {vectors}")
        chunk_size = request["chunk_size"]
        table = f"vector_embeddings_{chunk_size}"
        print(f"Inserting into table {table}")
        self.store_vectors(vectors=vectors, table=table)

        # self.delete_all_vectors(table=table)

        return vectors

    def store_vectors(self, vectors, table):
        conn = psycopg2.connect(
        host=os.getenv("POSTGRESQL_HOST"),
        port=os.getenv("POSTGRESQL_PORT"),
        database=os.getenv("POSTGRESQL_DATABASE"),
        user=os.getenv("POSTGRESQL_USER"),
        password=os.getenv("POSTGRESQL_PASSWORD")
        )
        try:
            with conn.cursor() as cur:
                execute_values(cur, f"INSERT INTO {table} (entity_id, embedding, text) VALUES %s", vectors)
            conn.commit()
        finally:
            conn.close()
    
    def delete_all_vectors(self, table: str):
        conn = psycopg2.connect(
            host=os.getenv("POSTGRESQL_HOST"),
            port=os.getenv("POSTGRESQL_PORT"),
            database=os.getenv("POSTGRESQL_DATABASE"),
            user=os.getenv("POSTGRESQL_USER"),
            password=os.getenv("POSTGRESQL_PASSWORD")
        )

        try:
            with conn.cursor() as cur:
                cur.execute(f"DELETE FROM {table}")
            conn.commit()
        finally:
            conn.close()

@serve.deployment
class Text2Vectors:
    def __init__(
        self, chunk_method: DeploymentHandle, embedding_endpoint: DeploymentHandle
    ):
        self.chunk_method = chunk_method
        self.embedding_endpoint = embedding_endpoint

    async def __call__(self, http_request):
        request = await http_request.json()
        vectors = await self.compute_vectors(request=request)

        return vectors

    async def compute_vectors(self, request):
        text, chunk_size, embedding_model = request["text"], request["chunk_size"], request["embedding_model"]

        chunks = await self.chunk_method.chunk_fixed.remote(text, chunk_size)

        embeddings = [await self.embedding_endpoint.create_embedding.remote(chunk, embedding_model, chunk_size) for chunk in chunks]
        vectors = [(i, embedding, chunk) for i, (embedding, chunk) in enumerate(zip(embeddings, chunks))]

        return vectors

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

test2vectors_app = Text2Vectors.bind(ChunkStrategy.bind(), EmbeddingEndpoints.bind())
app = PGVectorConnection.bind(test2vectors_app)
# Use serve.run to deploy with the runtime environment
serve.run(app, route_prefix="/text2vectors")

print("Deployed Text2Vectors, ChunkStrategy, and EmbeddingEndpoints on the Ray cluster.")

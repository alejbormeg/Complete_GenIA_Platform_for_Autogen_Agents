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

    async def compute_vectors(self, request):
        text, chunk_size, embedding_model = request["text"], request["chunk_size"], request["embedding_model"]
        chunks = await self.chunk_method.chunk_fixed.remote(text, chunk_size)
        embeddings = [await self.embedding_endpoint.create_embedding.remote(chunk, embedding_model, chunk_size) for chunk in chunks]
        vectors = [(i, embedding, chunk) for i, (embedding, chunk) in enumerate(zip(embeddings, chunks))]

        return vectors
    
    async def extract_text_from_pdf(self, file_bytes: bytes):
        import fitz
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
        return text

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

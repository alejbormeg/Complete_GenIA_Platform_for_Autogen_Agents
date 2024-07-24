import logging
from ray import serve
from ray.serve.handle import DeploymentHandle

logger = logging.getLogger()

@serve.deployment()
class APIGateway:
    def __init__(self, text_to_vectors_handle: DeploymentHandle, pgvector_handle: DeploymentHandle, agents_chat: DeploymentHandle):
        self.text_to_vectors_handle = text_to_vectors_handle
        self.pgvector_handle = pgvector_handle
        self.agents_chat = agents_chat

    async def __call__(self, http_request):
        try:
            if http_request.method == "POST":
                action = http_request.url.path.split("/")[-1]
                logger.info(f"Received action: {action} with data: {http_request}")

                if action == "compute_vectors":
                    request = await http_request.json()
                    return await self.text_to_vectors_handle.compute_vectors.remote(request)
                if action == "text_to_vectordb":
                    request = await http_request.json()
                    vectors = await self.text_to_vectors_handle.compute_vectors.remote(request)
                    logger.info(f"Embeddings: {vectors}")
                    chunk_size = request["chunk_size"]
                    table = f"vector_embeddings_{chunk_size}"
                    database = request["database"]
                    logger.info(f"Inserting into table {table}")
                    return await self.pgvector_handle.insert_into_db.remote(chunk_size, vectors, database)
                if action == "agents_chat":
                    request = await http_request.json()
                    return await self.agents_chat.call_rag_chat.remote(request["task"], request["database"])
                if action == "execute_query":
                    request = await http_request.json()
                    return await self.pgvector_handle.execute_query.remote(request["database"], request["query"])
                if action == "upload_pdf":
                    form = await http_request.form()
                    file = form["file"].file.read()
                    chunk_size = form["chunk_size"]
                    database = form["database"]
                    embedding_model = form["embedding_model"]
                    text = await self.text_to_vectors_handle.extract_text_from_pdf.remote(file)
                    vectors = await self.text_to_vectors_handle.compute_vectors.remote({"text": text, "chunk_size": int(chunk_size), "embedding_model": embedding_model})
                    await self.pgvector_handle.insert_into_db.remote(chunk_size, vectors, database)
                    return {"result": "document uploaded successfully"}
                else:
                    logger.error(f"Unknown or missing action: {action}")
                    return {"error": "Unknown or missing action"}
            else:
                return {"error": "Invalid request method"}
        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            return {"error": "Failed to process request", "details": str(e)}

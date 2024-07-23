import ray
import os
import psycopg2
import logging
import utils
import agents
from dotenv import load_dotenv
from ray import serve
from ray.serve.handle import DeploymentHandle
from typing import List
from psycopg2.extras import execute_values
from fastapi import UploadFile
# Import necessary modules and configurations


load_dotenv()


logger = logging.getLogger()

@serve.deployment()
class RAGChatEndpoint:
    def __init__(self) -> None:
        from utils.utils import send_messages_to_front
        from utils.config import create_openai_client, retrieve_config, config
        from agents.feedback_loop_agent import setup_feedback_loop_agent
        from agents.nl_to_sql_agent import setup_nl_to_sql_agent
        from agents.planner_agent import setup_planner_agent
        from agents.rag_pgvector_agent import setup_rag_pgvector_agent
        from agents.user_proxy_agent import setup_user_proxy_agent

        # These are now initialized within the instance to avoid serialization issues.
        openai_client = create_openai_client()
        self.retrieve_config_ = retrieve_config(openai_client)
        self.llm_config = config()
        
        self.document_retrieval_agent = setup_rag_pgvector_agent(name="DRA", retrieve_config=self.retrieve_config_, client=openai_client)
        self.user_proxy = setup_user_proxy_agent()
        self.planner = setup_planner_agent(self.llm_config)
        self.nl_to_sql = setup_nl_to_sql_agent(self.llm_config)
        self.feedback_loop_agent = setup_feedback_loop_agent(self.llm_config)

    async def call_rag_chat(self, task):
        from autogen import GroupChat, GroupChatManager
        from typing_extensions import Annotated

        # Reset and setup agents - ideally this should be encapsulated in methods or managed statefully
        self.user_proxy.reset()
        self.planner.reset()
        self.document_retrieval_agent.reset()
        self.nl_to_sql.reset()
        self.feedback_loop_agent.reset()

        def retrieve_content(
            message: Annotated[
                str,
                "Refined message which keeps the original meaning and can be used to retrieve content for question answering.",
            ],
            n_results: Annotated[int, "number of results"] = 3,
        ) -> str:
            self.document_retrieval_agent.n_results = n_results
            # Check if we need to update the context.
            update_context_case1, update_context_case2 = self.document_retrieval_agent._check_update_context(message)
            print(f"Update_context_1: ")
            if (update_context_case1 or update_context_case2) and self.document_retrieval_agent.update_context:
                self.document_retrieval_agent.problem = message if not hasattr(self.document_retrieval_agent, "problem") else self.document_retrieval_agent.problem
                _, ret_msg = self.document_retrieval_agent._generate_retrieve_user_reply(message)
            else:
                _context = {"problem": message, "n_results": n_results}
                ret_msg = self.document_retrieval_agent.message_generator(self.document_retrieval_agent, None, _context)
            return ret_msg if ret_msg else message
    
        agents = [self.user_proxy, self.planner, self.nl_to_sql, self.feedback_loop_agent]

        self.document_retrieval_agent.human_input_mode = "NEVER"

        for caller in [self.planner]:
            d_retrieve_content = caller.register_for_llm(
                description= " Retrieve content for question answering", api_style="function"
            )(retrieve_content)

        for executor in agents:
            executor.register_for_execution()(d_retrieve_content)

        # Initialize chat components and start chatting process
        groupchat = GroupChat(
            agents=[self.user_proxy, self.planner, self.nl_to_sql, self.feedback_loop_agent],
            messages=[],
            max_round=12,
            speaker_selection_method=self.state_transition_manager,
            allow_repeat_speaker=False,
        )
        manager = GroupChatManager(groupchat=groupchat, llm_config=self.llm_config)
        await self.user_proxy.a_initiate_chat(manager, message=task)
        return groupchat.messages

    # Define tranitions
    def state_transition_manager(self, last_speaker, groupchat):

        if last_speaker is self.user_proxy:
            print("-------------> time for PLANNER")
            return self.planner
        
        elif last_speaker is self.planner:
            print("-------------> time for Content analysis")
            return self.nl_to_sql
        
        elif last_speaker is self.nl_to_sql and "terminate" in groupchat.messages[-1]["content"].lower():
            print("-------------> time for User Proxy")
            return self.user_proxy

        elif last_speaker is self.nl_to_sql:
            print("-------------> time for Feedback")
            return self.feedback_loop_agent
        
        elif last_speaker is self.feedback_loop_agent:
            print("-------------> time for Content analysis")
            return self.nl_to_sql
        
        else:
            return "auto"

@serve.deployment()
class PGVectorConnection:
    async def insert_into_db(self, chunk_size, vectors):
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
    
    def execute_query(self, database: str, query: str):
        conn = psycopg2.connect(
            host=os.getenv("POSTGRESQL_HOST"),
            port=os.getenv("POSTGRESQL_PORT"),
            database=database,
            user=os.getenv("POSTGRESQL_USER"),
            password=os.getenv("POSTGRESQL_PASSWORD")
        )

        try:
            with conn.cursor() as cur:
                cur.execute(query)
                result = cur.fetchall()
            conn.commit()
            return result
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
                    logger.info(f"Inserting into table {table}")
                    return await self.pgvector_handle.insert_into_db.remote(chunk_size, vectors)
                if action == "agents_chat":
                    request = await http_request.json()
                    return await self.agents_chat.call_rag_chat.remote(request["task"])
                if action == "execute_query":
                    request = await http_request.json()
                    return await self.pgvector_handle.execute_query.remote(request["database"], request["query"])
                if action == "upload_pdf":
                    form = await http_request.form()
                    file = form["file"].file.read()
                    chunk_size = form["chunk_size"]
                    embedding_model = form["embedding_model"]
                    text = await self.text_to_vectors_handle.extract_text_from_pdf.remote(file)
                    vectors = await self.text_to_vectors_handle.compute_vectors.remote({"text": text, "chunk_size": int(chunk_size), "embedding_model": embedding_model})
                    await self.pgvector_handle.insert_into_db.remote(chunk_size, vectors)
                    return {"result": "document uploaded successfully"}
                else:
                    logger.error(f"Unknown or missing action: {action}")
                    return {"error": "Unknown or missing action"}
            else:
                return {"error": "Invalid request method"}
        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            return {"error": "Failed to process request", "details": str(e)}

    

# Initialize Ray and Serve
os.environ['RAY_ADDRESS'] = "ray://localhost:10001"
ray.init(runtime_env={"py_modules": [utils, agents]})
serve.start()

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

import os
import psycopg2
from psycopg2.extras import execute_values
from typing import List, Tuple
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent

class PgVectorRetrieveUserProxyAgent(RetrieveUserProxyAgent):
    def __init__(self, name, retrieve_config, client, database=None, **kwargs):
        super().__init__(name=name, retrieve_config=retrieve_config, code_execution_config=False)
        self.openai = client
        self.retrieve_config = retrieve_config
        self.database = database

    def retrieve_docs(self, problem: str, n_results: int = 3, search_string: str = "", database: str = None, **kwargs):
        query_embedding = self.openai.embeddings.create(model=os.getenv("GPT_EMBEDDING_ENGINE"), input=problem, dimensions=1536).data[0].embedding
        results = self.retrieve_related_vectors(query_embedding, self.retrieve_config["table_name"], top_k=n_results, database=self.database)
        self._results = [[({'id': match[0], 'content': match[2]}, match[3])] for match in results]
        return self._results

    def retrieve_related_vectors(self, query_embedding, table, top_k=3, database=None):
        conn = psycopg2.connect(
            host=os.getenv("POSTGRESQL_HOST"),
            port=os.getenv("POSTGRESQL_PORT"),
            database=os.getenv("POSTGRESQL_DATABASE"),
            user=os.getenv("POSTGRESQL_USER"),
            password=os.getenv("POSTGRESQL_PASSWORD")
        )
        cursor = conn.cursor()
        
        if database:
            cursor.execute(f"""
                SELECT id, embedding, text, embedding <-> %s::vector AS score, database
                FROM {table}
                WHERE database = %s
                ORDER BY score
                LIMIT {top_k};
            """, (query_embedding, database))
        else:
            cursor.execute(f"""
                SELECT id, embedding, text, embedding <-> %s::vector AS score
                FROM {table}
                ORDER BY score
                LIMIT {top_k};
            """, (query_embedding,))
        
        related_vectors = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return [(id, embedding, text, score, database) if database else (id, embedding, text, score) for (id, embedding, text, score, *db) in related_vectors]



def termination_msg(x):
    return isinstance(x, dict) and "TERMINATE" == str(x.get("content", ""))[-9:].upper()

def setup_rag_pgvector_agent(name, retrieve_config, client, database=None):

    return PgVectorRetrieveUserProxyAgent(
        name="PgVector Agent",
        retrieve_config=retrieve_config,
        client=client,
        database=database,
        is_termination_msg=termination_msg,
        human_input_mode="NEVER",
        max_consecutive_auto_reply=3,
        code_execution_config=False,  # we don't want to execute code in this case.
        system_message="Your responsibility is to search the user's query answer in the vector store for information that could be relevant for the user intent and query. You receive as input the user query. As output, you will retrieve the relevant documents",
    )
import os
from openai import OpenAI


def create_openai_client():
    return OpenAI(
        api_key=os.getenv('OPENAI_API_KEY')
    )

def retrieve_config(client):
    return {
        "task": "qa",
        "table_name": "vector_embeddings_1536",
        "chunk_token_size": 500,
        "model": os.getenv('GPT_MODEL'),
        "get_or_create": True,
        "embedding_function": lambda x: client.embeddings.create(input=x, model="text-embedding-3-large", dimensions=1536).data[0].embedding,
        "vector_db": None,
    }

def config():
    return {
            "model": os.getenv('GPT_MODEL'), 
            "api_key":  os.getenv('OPENAI_API_KEY'),
            }
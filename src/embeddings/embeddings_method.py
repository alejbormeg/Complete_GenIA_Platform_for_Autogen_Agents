import os
import json
import psycopg2
import openai
import nltk
import spacy
import mlflow
import pandas as pd
from dotenv import load_dotenv
from fuzzywuzzy import fuzz
from psycopg2.extras import execute_values
from typing import List, Tuple

#Load env variables
load_dotenv()

# Load spacy model
# Make sure you do: python -m spacy download en_core_web_sm
nlp = spacy.load('en_core_web_sm')

# Database connection parameters
host = "localhost"
port = 5432
database = "vector_db"
user = "alex"
password = "alexPostgresPassword"

# OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Load queries from the external JSON file
with open('src/embeddings/queries.json', 'r') as file:
    queries_json = json.load(file)

# Chunk strategies
def chunk_fixed(sentences: List[str], chunk_size: int) -> List[List[str]]:
    return [sentences[i:i + chunk_size] for i in range(0, len(sentences), chunk_size)]

def chunk_nltk(text: str) -> List[str]:
    nltk.download('punkt')
    return nltk.tokenize.sent_tokenize(text)

def chunk_spacy(text: str) -> List[str]:
    doc = nlp(text)
    return [sent.text for sent in doc.sents]

chunk_strategies = {
    "fixed": chunk_fixed,
    "nltk": chunk_nltk,
    "spacy": chunk_spacy
}

# Embedding models
embedding_models = {
    "text-embedding-3-small": "text-embedding-3-small",
    "text-embedding-3-large": "text-embedding-3-large",
    "text-embedding-ada-002": "text-embedding-ada-002"
}

# Function to create embeddings
def create_embedding(text: str, model: str) -> List[float]:
    response = openai.Embedding.create(model=model, input=text)
    return response['data'][0]['embedding']

# Function to store vectors in PostgreSQL
def store_vectors(vectors: List[Tuple[int, List[float]]], table: str):
    conn = psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )
    try:
        with conn.cursor() as cur:
            execute_values(cur, f"INSERT INTO {table} (entity_id, embedding) VALUES %s", vectors)
        conn.commit()
    finally:
        conn.close()


# Main experiment function
def run_experiment(query_descriptions: List[str], queries: List[str], expected_sqls: List[str], chunk_size: int, chunk_strategy: str, embedding_model: str):
    mlflow.set_experiment(experiment_id="0")
    
    system_prompt = (
        "You are an AI assistant specialized in translating natural language questions into SQL queries."
        " Given a description of the data and a natural language question, generate the corresponding SQL query."
    )
    
    mlflow.start_run()
    mlflow.log_param("system_prompt", system_prompt)
    mlflow.log_param("chunk_size", chunk_size)
    mlflow.log_param("chunk_strategy", chunk_strategy)
    mlflow.log_param("embedding_model", embedding_model)

    total_similarity = 0
    num_queries = len(queries)
    
    # Log the model with OpenAI
    logged_model = mlflow.openai.log_model(
        model="gpt-3.5-turbo",
        task=openai.chat.completions,
        artifact_path="model",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "{question}"},
        ],
    )

    for i, (query_description, query, expected_sql) in enumerate(zip(query_descriptions, queries, expected_sqls)):
        mlflow.log_param(f"query_{i+1}_description", query_description)

        chunk_func = chunk_strategies[chunk_strategy]
        text = query
        chunks = chunk_func(text, chunk_size) if chunk_strategy == "fixed" else chunk_func(text)

        embeddings = [create_embedding(chunk, embedding_model) for chunk in chunks]

        table = "vector_embeddings_256" if chunk_size == 256 else "vector_embeddings_512"
        vectors = [(i, embedding) for i, embedding in enumerate(embeddings)]
        store_vectors(vectors, table)

        # Evaluate the model on some example questions
        query_description = pd.DataFrame(
            {
                "query_description": [
                    f"Based on the embeddings in {table}, generate SQL to answer: {query_description}"
                ]
            }
        )
        response = mlflow.evaluate(
            model=logged_model.model_uri,
            model_type="question-answering",
            data=query_description,
        )

        generated_sql = response.choices[0].message['content'].strip()

        similarity = fuzz.ratio(generated_sql, expected_sql)
        total_similarity += similarity

        mlflow.log_metric(f"query_{i+1}_similarity", similarity)
        mlflow.log_text(prompt, f"query_{i+1}_prompt.txt")
        mlflow.log_text(generated_sql, f"query_{i+1}_generated_sql.txt")
        mlflow.log_text(expected_sql, f"query_{i+1}_expected_sql.txt")

    average_similarity = total_similarity / num_queries
    mlflow.log_metric("average_similarity", average_similarity)
    mlflow.end_run()



# Running experiments
query_descriptions = list(queries_json.keys())
queries_list = list(queries_json.values())
expected_sqls = queries_list.copy()

for chunk_size in [256, 512]:
    for strategy in ["fixed", "nltk", "spacy"]:
        for model in embedding_models.values():
            run_experiment(query_descriptions, queries_list, expected_sqls, chunk_size, strategy, model)

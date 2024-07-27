import os
import json
import openai
import mlflow
import pandas as pd
import re
import requests
from dotenv import load_dotenv
from fuzzywuzzy import fuzz
from utils.database_utils import execute_query
from typing import List

# Load environment variables
load_dotenv()

# OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Backend URL for API endpoints
backend_url = "http://localhost:8000/api"

# Function to process a query task
def process_query(task, database):
    response = requests.post(
        f"{backend_url}/agents_chat",
        json={"task": task, "database": database},
    )
    messages = response.json()
    return messages[-1]

# Load queries from the external JSON file
with open('src/embeddings/queries.json', 'r') as file:
    queries_json = json.load(file)

# Main experiment function
def run_experiment(query_descriptions: List[str], queries: List[str], expected_sqls: List[str]):
    remote_server_uri = "http://localhost"
    mlflow.set_tracking_uri(remote_server_uri)
    mlflow.set_experiment("Chunk-strategy")

    with mlflow.start_run():
        mlflow.log_param("framework", "Autogen")
        mlflow.log_param("open_ai_model", "gpt-4o")
        mlflow.log_param("chunk_size", 1536)
        mlflow.log_param("chunk_strategy", "fixed")
        mlflow.log_param("embedding_model", "text-embedding-3-large")

        total_similarity = 0
        queries_df = pd.DataFrame({"query_description": [], "generated_sql": []})

        for query_description, query, expected_sql in zip(query_descriptions, queries, expected_sqls):

            # Process the query using the API
            message = process_query(query_description, "social_network_poc")

            # Extract the generated SQL from the messages
            generated_sql = ""
            match = re.search(r'```sql(.*?)```', message["content"], re.DOTALL)
            if match:
                generated_sql = match.group(1).strip()

            # Create a DataFrame for the new row
            new_row = pd.DataFrame({"query_description": [query_description], "generated_sql": [generated_sql]})

            # Concatenate the new row to the DataFrame
            queries_df = pd.concat([queries_df, new_row], ignore_index=True)

        # Access the evaluation metrics and results
        eval_table = pd.DataFrame({
            "query_description": queries_df["query_description"],
            "expected_sql": expected_sqls,
            "generated_sql": queries_df["generated_sql"],
            "similarity": 0,
            "result_coincidence": 0
        })

        # Initialize total similarity
        total_similarity = 0

        # Extracting generated SQL from the evaluation results
        for index, row in eval_table.iterrows():
            generated_sql = row["generated_sql"]

            # Calculate similarity
            expected_sql = row["expected_sql"]
            similarity = fuzz.ratio(generated_sql, expected_sql)
            total_similarity += similarity

            # Execute expected and generated SQL queries
            expected_result = execute_query(query=expected_sql, database="social_network_poc")
            generated_result = execute_query(query=generated_sql, database="social_network_poc")

            # Compare results
            result_coincidence = 1 if expected_result == generated_result else 0

            # Store the similarity and result coincidence in the DataFrame
            eval_table.at[index, "similarity"] = similarity
            eval_table.at[index, "result_coincidence"] = result_coincidence

        # Calculate average similarity if needed
        average_similarity = total_similarity / len(eval_table) if len(eval_table) > 0 else 0

        # Log the average similarity metric
        mlflow.log_metric("average_similarity", average_similarity)

        # Log the DataFrame as an artifact
        eval_table.to_csv("evaluation_results.csv", index=False)
        mlflow.log_artifact("evaluation_results.csv")

# Running experiments
query_descriptions = list(queries_json.keys())
queries_list = list(queries_json.values())
expected_sqls = queries_list.copy()

run_experiment(query_descriptions, queries_list, expected_sqls)

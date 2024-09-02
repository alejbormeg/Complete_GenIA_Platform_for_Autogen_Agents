import os
import json
import openai
import mlflow
import pandas as pd
import re
from dotenv import load_dotenv
from fuzzywuzzy import fuzz
from utils.files_utils import read_text_from_pdf
from utils.embedding_utils import chunk_spacy, chunk_nltk, chunk_fixed, create_embedding
from utils.database_utils import execute_query, retrieve_related_vectors, store_vectors, delete_all_vectors
from typing import List

# Load env variables
load_dotenv()

# OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Load queries from the external JSON file
with open('src/embeddings/queries.json', 'r') as file:
    queries_json = json.load(file)

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

def run_experiment(query_descriptions: List[str], queries: List[str], expected_sqls: List[str], chunk_size: int, chunk_strategy: str, embedding_model: str):
    remote_server_uri = "http://localhost"
    mlflow.set_tracking_uri(remote_server_uri)
    mlflow.set_experiment("NaturalLanguage2SQL")
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
    # gpt_model = "gpt-3.5-turbo"
    gpt_model = "gpt-4o"

    top_k = 3

    # Log the model with OpenAI
    logged_model = mlflow.openai.log_model(
        model=gpt_model,
        task=openai.chat.completions,
        artifact_path="model",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "{question}"},
        ],
    )

    mlflow.log_param("open_ai_model", gpt_model)
    mlflow.log_param("top_k", top_k)
    chunk_func = chunk_strategies[chunk_strategy]
    text = read_text_from_pdf('src/embeddings/SocialNetworkDescription.pdf')
    chunks = chunk_func(text, chunk_size) if chunk_strategy == "fixed" else chunk_func(text)

    embeddings = [create_embedding(chunk, embedding_model, chunk_size) for chunk in chunks]

    table = f"vector_embeddings_{chunk_size}"
    vectors = [(i, embedding, chunk) for i, (embedding, chunk) in enumerate(zip(embeddings, chunks))]
    store_vectors(vectors, table)

    queries_df = pd.DataFrame({ "query_description": []})

    for i, (query_description, query, expected_sql) in enumerate(zip(query_descriptions, queries, expected_sqls)):
        query_embedding = create_embedding(query_description, embedding_model, chunk_size)
        related_vectors = retrieve_related_vectors(query_embedding, table, top_k=top_k)

        related_texts = [text for _, _, text in related_vectors]

        description = f"""
            Based on the embeddings in {table}, generate the SQL query to answer: {query_description}.
            Please provide only the SQL code enclosed within ```sql...``` characters.
            Context: {' '.join(related_texts)}
            """

        new_row = pd.DataFrame({"query_description": [description]})

        queries_df = pd.concat([queries_df, new_row], ignore_index=True)

    response = mlflow.evaluate(
        model=logged_model.model_uri,
        model_type="question-answering",
        data=queries_df
    )

    # Access the evaluation metrics and results
    print(f"Evaluation Metrics: {response.metrics}")
    eval_table = response.tables["eval_results_table"]

    # Initialize total similarity
    total_similarity = 0
    total_accuracy = 0

    # Add a new column to the DataFrame for similarity
    eval_table["query_description"] = ""
    eval_table["expected_sql"] = ""
    eval_table["generated_sql"] = ""
    eval_table["expected_result"] = ""
    eval_table["generated_result"] = ""
    eval_table["similarity"] = 0
    eval_table["result_coincidence"] = 0

    # Extracting generated SQL from the evaluation results
    for index, row in eval_table.iterrows():
        generated_output = row["outputs"]
        description = query_descriptions[index]

        # Extract SQL part using regex
        match = re.search(r'`sql(.*?)`', generated_output, re.DOTALL)
        if match:
            generated_sql = match.group(1)
        else:
            generated_sql = ""

        # Calculate similarity
        expected_sql = expected_sqls[index]
        similarity = fuzz.ratio(generated_sql, expected_sql)
        total_similarity += similarity
        
        # Execute expected and generated SQL queries
        expected_result = execute_query(query=expected_sql, database="social_network_poc")
        generated_result = execute_query(query=generated_sql, database="social_network_poc")
        
        # Compare results
        result_coincidence = 1 if expected_result == generated_result else 0
        
        if not result_coincidence:
            prompt = f"""
                Given the following query description: {description}.
                Two SQL queries were provided:
                - Expected SQL: {expected_sql}
                - Generated SQL: {generated_sql}

                Can we find the information of expected result in generated result ? No matters if we find extra info in generated_result
                - Expected Result:\n{str(expected_result)}
                - Generated Result:\n{str(generated_result)}
                """

            gpt_response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert SQL analyst. Just respond 'yes' or 'no'"},
                    {"role": "user", "content": prompt}
                ]
            )

            # Check if GPT-4 considers them similar in meaning
            gpt_result = gpt_response.choices[0].message.content
            result_coincidence = 1 if "yes" in gpt_result.lower() else 0

        # Store the similarity and result coincidence in the DataFrame
        eval_table.at[index, "query_description"] = description
        eval_table.at[index, "expected_sql"] = expected_sql
        eval_table.at[index, "generated_sql"] = generated_sql
        eval_table.at[index, "expected_result"] = expected_result
        eval_table.at[index, "generated_result"] = generated_result
        eval_table.at[index, "similarity"] = similarity
        eval_table.at[index, "result_coincidence"] = result_coincidence

        total_accuracy += result_coincidence

    # Calculate average similarity if needed
    average_similarity = total_similarity / len(eval_table) if len(eval_table) > 0 else 0
    average_accuracy = total_accuracy /  len(eval_table) if len(eval_table) > 0 else 0

    mlflow.log_metric("average_similarity", average_similarity)
    mlflow.log_metric("average_accuracy", average_accuracy)

    # Log the DataFrame as an artifact
    eval_table.to_csv("evaluation_results.csv", index=False)
    mlflow.log_artifact("evaluation_results.csv")
    mlflow.end_run()
    
    # Delete all vectors from the table
    delete_all_vectors(table)


# Running experiments
query_descriptions = list(queries_json.keys())
queries_list = list(queries_json.values())
expected_sqls = queries_list.copy()

for chunk_size in [256, 512, 1536]:
    for strategy in ["fixed", "nltk", "spacy"]:
        for model in embedding_models.values():
            run_experiment(query_descriptions, queries_list, expected_sqls, chunk_size, strategy, model)

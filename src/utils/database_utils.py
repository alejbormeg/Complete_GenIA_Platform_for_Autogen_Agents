import os
import psycopg2
from psycopg2.extras import execute_values
from typing import List, Tuple


def execute_query(query: str, database: str):
    """
    Executes the given query on the specified database and returns the result.

    Parameters:
    - query: str: The SQL query to execute.
    - database: str: database
    Returns:
    - result: List[Tuple]: The result of the query execution.
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRESQL_HOST"),
            port=os.getenv("POSTGRESQL_PORT"),
            database=database,
            user=os.getenv("POSTGRESQL_USER"),
            password=os.getenv("POSTGRESQL_PASSWORD")
        )
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return result
    except Exception as e:
        print(f"Error executing query: {e}")
        return "Error"
    finally:
        if conn:
            conn.close()

def retrieve_related_vectors(query_embedding, table, top_k=3):
    conn = psycopg2.connect(
        host=os.getenv("POSTGRESQL_HOST"),
        port=os.getenv("POSTGRESQL_PORT"),
        database=os.getenv("POSTGRESQL_DATABASE"),
        user=os.getenv("POSTGRESQL_USER"),
        password=os.getenv("POSTGRESQL_PASSWORD")
    )
    cursor = conn.cursor()
    
    cursor.execute(f"""
        SELECT id, embedding, text
        FROM {table}
        ORDER BY embedding <-> %s::vector
        LIMIT {top_k};
    """, (query_embedding,))
    
    related_vectors = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return related_vectors

def store_vectors(vectors: List[Tuple[int, List[float], str]], table: str):
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

def delete_all_vectors(table: str):
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
import os
from typing import List, Optional

import psycopg2
from psycopg2.extras import execute_values
from ray import serve


def _connect(database: Optional[str] = None):
    return psycopg2.connect(
        host=os.getenv("POSTGRESQL_HOST"),
        port=os.getenv("POSTGRESQL_PORT"),
        database=database or os.getenv("POSTGRESQL_DATABASE"),
        user=os.getenv("POSTGRESQL_USER"),
        password=os.getenv("POSTGRESQL_PASSWORD"),
    )

@serve.deployment()
class PGVectorConnection:
    async def insert_into_db(self, chunk_size, vectors, database=None):
        table = f"vector_embeddings_{chunk_size}"
        print(f"Inserting into table {table}")
        self.store_vectors(vectors=vectors, table=table, database=database)
        # self.delete_all_vectors(table=table)
        return vectors

    def store_vectors(self, vectors, table, database=None):
        conn = _connect()
        try:
            with conn.cursor() as cur:
                if database:
                    # Modify vectors to include the database at the end
                    modified_vectors = [vector + (database,) for vector in vectors]
                    execute_values(cur, f"INSERT INTO {table} (entity_id, embedding, text, database) VALUES %s", modified_vectors)
                else:
                    execute_values(cur, f"INSERT INTO {table} (entity_id, embedding, text) VALUES %s", vectors)
            conn.commit()
        finally:
            conn.close()
    
    def execute_query(self, database: str, query: str):
        conn = _connect(database)

        try:
            with conn.cursor() as cur:
                cur.execute(query)
                result = cur.fetchall()
            conn.commit()
            return result
        finally:
            conn.close()

    def delete_all_vectors(self, table: str):
        conn = _connect()

        try:
            with conn.cursor() as cur:
                cur.execute(f"DELETE FROM {table}")
            conn.commit()
        finally:
            conn.close()

    def list_vector_databases(self, chunk_size: int) -> List[str]:
        table = f"vector_embeddings_{chunk_size}"
        conn = _connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT DISTINCT database FROM {table} WHERE database IS NOT NULL ORDER BY database"
                )
                rows = cur.fetchall()
        finally:
            conn.close()

        return [row[0] for row in rows if row[0]]

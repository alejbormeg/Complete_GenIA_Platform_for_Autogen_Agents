import psycopg2
from pgvector.psycopg2 import register_vector

# Database connection parameters
host = "localhost"
port = 5432
database = "vector_db"
user = "alex"
password = "alexPostgresPassword"

try:
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )

    # Create a cursor object
    cur = conn.cursor()

    # Create a testing table with a vector column
    create_table_query = """
    CREATE TABLE IF NOT EXISTS test_vectors (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        embedding vector(3)
    );
    """
    cur.execute(create_table_query)
    conn.commit()

    # Close the cursor and connection
    cur.close()
    conn.close()

    print("Test table created successfully.")

except psycopg2.Error as e:
    print(f"An error occurred: {e}")

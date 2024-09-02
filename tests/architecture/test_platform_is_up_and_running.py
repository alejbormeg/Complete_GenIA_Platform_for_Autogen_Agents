import pytest
import subprocess
import ray
import os
import mlflow
from mlflow.tracking import MlflowClient
import psycopg2
from psycopg2 import sql
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv

load_dotenv()

RAY_ADDRESS = os.getenv("RAY_ADDRESS")
MLFLOW_ADDRESS = os.getenv("MLFLOW_ADDRESS")
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
MINIO_ADDRESS = os.getenv("MINIO_ADDRESS")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")

missing_env_vars = []
if not RAY_ADDRESS:
    missing_env_vars.append("RAY_ADDRESS")
if not MLFLOW_ADDRESS:
    missing_env_vars.append("MLFLOW_ADDRESS")
if not MLFLOW_TRACKING_URI:
    missing_env_vars.append("MLFLOW_TRACKING_URI")
if not POSTGRES_HOST:
    missing_env_vars.append("POSTGRES_HOST")
if not POSTGRES_PORT:
    missing_env_vars.append("POSTGRES_PORT")
if not POSTGRES_DB:
    missing_env_vars.append("POSTGRES_DB")
if not POSTGRES_USER:
    missing_env_vars.append("POSTGRES_USER")
if not POSTGRES_PASSWORD:
    missing_env_vars.append("POSTGRES_PASSWORD")

if missing_env_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_env_vars)}")

POSTGRES_PORT = int(POSTGRES_PORT)

# Test if Ray cluster is up and running
def test_ray_cluster():
    load_dotenv()
    try:
        ray.init(address=RAY_ADDRESS)
        ray.shutdown()
    except Exception as e:
        pytest.fail(f"Ray cluster is not up and running. "
                    f"Error: {e}")

# Test if PostgreSQL is up and running
def test_postgresql_connection():
    load_dotenv()
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        conn.close()
    except psycopg2.Error as e:
        pytest.fail(f"Connection to PostgreSQL database failed. "
                    f"Error: {e}")

# Test if pgvector extension is properly set up in the PostgreSQL database
def test_pgvector_extension():
    load_dotenv()
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )

        cur = conn.cursor()

        create_table_query = """
        CREATE TABLE IF NOT EXISTS test_vectors (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            embedding vector(3)
        );
        """
        cur.execute(create_table_query)
        conn.commit()

        cur.execute("SELECT * FROM test_vectors;")
        cur.fetchall()

        cur.execute("DROP TABLE IF EXISTS test_vectors;")
        conn.commit()

        cur.close()
        conn.close()

    except psycopg2.Error as e:
        pytest.fail(f"An error occurred while testing pgvector extension: {e}")

def test_postgresql_databases():
    POSTGRES_DATABASES = ["mlflowdb", "vector_db"]
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database='postgres' # Change this database
        )

        cur = conn.cursor()

        cur.execute("SELECT datname FROM pg_database;")
        databases = cur.fetchall()
        database_names = [db[0] for db in databases]

        for db in POSTGRES_DATABASES:
            assert db in database_names, f"Database {db} not found in PostgreSQL."

        cur.close()
        conn.close()

    except psycopg2.Error as e:
        pytest.fail(f"An error occurred while checking PostgreSQL databases: {e}")

def test_mlflow_tracking_server():
    load_dotenv()
    try:
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        client = MlflowClient()
        client.search_experiments()
    except Exception as e:
        pytest.fail(f"MLflow tracking server is not accessible. "
                    f"Error: {e}")

@pytest.mark.parametrize("ip_address", ["localhost"])
def test_minio_connection(ip_address):
    load_dotenv()
    try:
        response = subprocess.run(["curl", f"http://{ip_address}:9000/minio/health/live"],
                                  check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if response.returncode != 0:
            pytest.fail("Minio server is not running.")
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Minio server health check failed. "
                    f"Error: {e.stderr.decode('utf-8')}")

def test_minio_buckets():
    try:
        import boto3
        from botocore.client import Config
        MINIO_BUCKETS = ["data", "mlflow"]
        s3 = boto3.resource(
            's3',
            endpoint_url=f'http://{MINIO_ADDRESS}:9000',
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY,
            config=Config(signature_version='s3v4')
        )

        bucket_names = [bucket.name for bucket in s3.buckets.all()]
        for bucket in MINIO_BUCKETS:
            assert bucket in bucket_names, f"Bucket {bucket} not found in Minio."

    except Exception as e:
        pytest.fail(f"An error occurred while checking Minio buckets: {e}")

if __name__ == "__main__":
    pytest.main()

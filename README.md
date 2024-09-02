# 🤖 Complete GenIA Platform for Autogen Agents 🤖

Sure! Here’s the updated version with the correct commands included to execute the script:

## Requirements

## Architecture

This architecture is based on the Stage 0 framework outlined in [MLOps: Continuous Delivery and Automation Pipelines in Machine Learning](https://cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning?hl=es-419). It utilizes **MLflow** as the Model Registry and **Ray** for Model Serving.

To set up the entire platform, navigate to the `architecture` directory and run the script `start_all.sh` using the following commands:

```bash
cd architecture
chmod +x start_all.sh
./start_all.sh
```

This script creates an internal Docker network that seamlessly connects the containers for PostgreSQL, Ray, and the Gradio UI. This setup enables the complete platform to function cohesively, allowing you to deploy models with Ray, execute queries on PostgreSQL, and interact with the platform through the Gradio UI.


### Mlflow: Model Registry 📊

In the `architecture/mlflow` directory, you will find a `docker-compose.yml` file that sets up a multi-container architecture for an MLflow deployment, including storage, database, and web server components. Here's an explanation of each component and their roles:

#### Services

* **Minio**:
    - **Image**: `minio/minio:RELEASE.2023-11-20T22-40-07Z`
    - **Role**: Provides S3-compatible object storage for MLflow artifacts.
    - **Ports Exposed**: 9000 (API), 9001 (Console)
    - **Command**: Runs the Minio server with a console interface.
    - **Networks**: Connects to the storage network.
    - **Environment Variables**: Uses `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` for root user credentials.
    - **Volumes**: Binds host directory `/mnt/md0/minio` to container’s `/data` directory for persistent storage.

* **Create MLflow Bucket**:
    - **Image**: `minio/mc:RELEASE.2023-11-20T16-30-59Z.fips`
    - **Role**: Initializes Minio buckets and sets policies.
    - **Dependencies**: Waits for Minio to be ready.
    - **Networks**: Connects to the storage network.
    - **Environment Variables**: Loads from `.env` file.
    - **Entrypoint Script**: Configures Minio client (`mc`), creates buckets, and sets policies.

* **Postgres**:
    - **Build Context**: `./pgvector` with `Dockerfile.pgvector`
    - **Role**: Provides a PostgreSQL database for MLflow’s backend store.
    - **Ports Exposed**: Configurable via `POSTGRES_PORT`, defaults to 5432.
    - **Networks**: Connects to the backend network.
    - **Environment Variables**: Sets user, password, and database details.
    - **Volumes**: Persists data in `db_datapg` volume.

* **PGAdmin**:
    - **Image**: `dpage/pgadmin4`
    - **Role**: Provides a web interface for managing the PostgreSQL database.
    - **Networks**: Connects to the backend network.
    - **Environment Variables**: Configures default email, password, and server mode.
    - **Volumes**: Persists data in `pgadmin` volume.

* **Web (MLflow Server)**:
    - **Build Context**: `./mlflow`
    - **Image**: `mlflow_server`
    - **Role**: Runs the MLflow server.
    - **Ports Exposed**: 5000 (MLflow server port)
    - **Networks**: Connects to frontend, backend, and storage networks.
    - **Environment Variables**: Configures S3 endpoint and AWS credentials.
    - **Command**: Starts MLflow server with PostgreSQL backend and S3 artifact store.

* **Nginx**:
    - **Build Context**: `./nginx`
    - **Image**: `mlflow_nginx`
    - **Role**: Acts as a reverse proxy for the MLflow server.
    - **Ports Exposed**: 80 (HTTP), 9000, 9001, 90
    - **Networks**: Connects to frontend, storage, and backend networks.
    - **Dependencies**: Waits for web and minio services to be ready.

#### Networks

* **frontend**: Bridge network for frontend services.
* **backend**: Bridge network for backend services.
* **storage**: Bridge network for storage services.

#### Volumes

* **db_datapg**: Volume for PostgreSQL data.
* **minio**: Volume for Minio data (although not explicitly used in the Minio service).
* **pgadmin**: Volume for PGAdmin data.

#### Summary

This architecture sets up a robust environment for MLflow, including:

* **Minio** for S3-compatible storage.
* **Postgres** for the backend database.
* **PGAdmin** for database management.
* **MLflow Server** for managing machine learning experiments and models.
* **Nginx** for reverse proxying the MLflow server.

Each service is isolated in its own container and connected via Docker networks, ensuring modularity and ease of management.

#### Steps to Connect PGAdmin to PostgreSQL 🛠️

1. Open PGAdmin and register a new server.
2. **Connection Tab**:
   - **Host name/address**: `postgres_container`
   - **Port**: `5432`
   - **Maintenance database**: `mlflowdb`
   - **Username**: `username`
   - **Password**: `password`

#### Steps to Add PGVector Extension to a PostgreSQL Container Database 🗃️

1. **Create a Database**:
    ![Create Database](./imgs/create_database_pgadmin.png)

2. **Execute**:
    ![Execute PGVector](./imgs/pgvector_create_command.png)

3. **Test the Created Database**: Use the `testing_pgvector.py` script to connect to a PostgreSQL database using the psycopg2 library and register a vector type from the pgvector extension. The script establishes a connection, creates a table with an id, name, and embedding column, and prints a success message if no errors occur.

#### .env template for Mlflow

Here’s the `.env` file with updated values and an explanation in markdown format, to set up the platform place it on the `architecture/mlflow`:

```plaintext
# MinIO configuration
AWS_ACCESS_KEY_ID=new_access_key
AWS_SECRET_ACCESS_KEY=new_secret_key
MLFLOW_BUCKET_NAME=mlflow_bucket
DATA_REPO_BUCKET_NAME=data_repository
AWS_S3_BUCKET_NAME=mlflow_bucket

# PostgreSQL configuration
POSTGRES_USER=new_user
POSTGRES_PASSWORD=new_password
POSTGRES_DB=new_mlflowdb
POSTGRES_PORT=5433

# PgAdmin configuration
PGADMIN_DEFAULT_EMAIL=admin@example.com
PGADMIN_DEFAULT_PASSWORD=new_pgadmin_password
PGADMIN_LISTEN_PORT=8080
```

##### MinIO Configuration

- **`AWS_ACCESS_KEY_ID`**: This is the access key ID for MinIO, an object storage service. The value has been updated to `new_access_key` to reflect a new user’s credentials.
- **`AWS_SECRET_ACCESS_KEY`**: The secret access key for MinIO, updated to `new_secret_key`. This should be kept secure as it provides access to the MinIO service.
- **`MLFLOW_BUCKET_NAME`**: The bucket name used by MLflow to store artifacts, updated to `mlflow_bucket`.
- **`DATA_REPO_BUCKET_NAME`**: The bucket name used to store data repositories, updated to `data_repository`.
- **`AWS_S3_BUCKET_NAME`**: The default S3 bucket name for MinIO, also updated to `mlflow_bucket` to match the new MLflow bucket.

##### PostgreSQL Configuration

- **`POSTGRES_USER`**: The username for accessing the PostgreSQL database, updated to `new_user`.
- **`POSTGRES_PASSWORD`**: The password associated with the PostgreSQL user, changed to `new_password`. This password should be kept secure.
- **`POSTGRES_DB`**: The name of the PostgreSQL database, updated to `new_mlflowdb`.
- **`POSTGRES_PORT`**: The port on which PostgreSQL listens, changed to `5433` to avoid potential conflicts with default PostgreSQL installations.

##### PgAdmin Configuration

- **`PGADMIN_DEFAULT_EMAIL`**: The default email address for logging into PgAdmin, updated to `admin@example.com`.
- **`PGADMIN_DEFAULT_PASSWORD`**: The default password for PgAdmin, changed to `new_pgadmin_password`. This password should be secure.
- **`PGADMIN_LISTEN_PORT`**: The port PgAdmin will listen on, updated to `8080` to avoid conflicts with other services that might be using port 90.

### Ray Cluster: Model Serving 🚀

This setup defines a Docker Compose configuration for running a Ray cluster with a head node, integrated with Prometheus and Grafana for monitoring. The architecture includes a Dockerfile and an entrypoint script to facilitate the installation and configuration of necessary components.

#### Docker Compose Configuration (`docker-compose.yml`)

##### Version
Specifies Docker Compose file format version `3.7`.

##### Services

###### ray-head
- **Build**: Specifies the build context as `./ray`.
- **Container Name**: Named `ray-head`.
- **Ports**: Maps ports 8265 (Ray dashboard) and 3000 (Grafana) to the host.
- **Command**: Specifies the command to start the container in "head" mode.
- **Shared Memory Size**: Allocates 8GB of shared memory to the container.
- **Environment Variables**:
  - `RAY_HEAD_IP`: Sets the IP address of the Ray head node.
  - `RAY_DISABLE_DOCKER_CPU_WARNING`: Disables Docker CPU warning.
  - `RAY_HEAD_SERVICE_HOST=0.0.0.0`: Makes the cluster endpoints accessible from outside the docker container.

- **Volumes**: Mounts a volume `ray_data` for persistent storage at `/root/ray`.
- **Logging**: Configures logging with a maximum size of 10MB per file and a maximum of 3 files.
- **Restart Policy**: Restarts the container on failure.
- **Deploy Resources**:
  - **Limits**: Limits the container to 2 CPUs and 8GB memory.
  - **Reservations**: Reserves 1 CPU and 4GB memory for the container.

###### Volumes
- **ray_data**: Defines a local driver volume for persisting Ray data.

#### Entrypoint Script (`entrypoint.sh`)

##### Install Prometheus and Grafana
Installs Prometheus and Grafana if they are not already installed.
- Downloads and extracts Prometheus and Grafana binaries.
- Moves the extracted directories to appropriate locations (`/etc/prometheus` and `/usr/share/grafana`).

##### Environment Variable
Sets the following variables:

```py
# Set the Grafana host for Ray monitoring
export RAY_GRAFANA_HOST="http://127.0.0.1:3000"

# Set locale for the system
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

# OpenAI API Key and GPT Model configuration
export OPENAI_API_KEY="your_openai_api_key"
export GPT_MODEL="gpt-4o"
export GPT_EMBEDDING_ENGINE="text-embedding-3-large"

# PostgreSQL Database connection parameters
export POSTGRESQL_HOST="postgres_container"
export POSTGRESQL_PORT=5432
export POSTGRESQL_DATABASE="vector_db"  # Replace with the actual name of your vector database in PostgreSQL
export POSTGRESQL_USER="new_user"
export POSTGRESQL_PASSWORD="new_password"
```

##### Ray Start Commands
- If the script is run with the argument `head`, it starts the Ray head node with the dashboard accessible on all interfaces and metrics exported on port 8080, using 12 CPUs.
- If the script is run with the argument `worker`, it starts a Ray worker node connecting to the head node, with metrics exported on port 8080, using 12 CPUs.
- For other arguments, it executes the provided command.

##### Wait for Ray to Start
Sleeps for 20 seconds to allow Ray to initialize and generate necessary configuration files.

##### Start Prometheus and Grafana
- Starts Prometheus with the configuration file generated by Ray.
- Starts Grafana with the configuration file and provisioning directory generated by Ray.

##### Keep the Container Running
Uses `tail -f /dev/null` to keep the container running indefinitely.

#### Dockerfile

##### Base Image
Uses `python:3.10` as the base image.

##### Install Packages
- Updates package lists and installs build-essential and curl.
- Installs Ray version 2.31.0 using pip.
- Cleans up unnecessary files to reduce image size.

##### Working Directory
Sets the working directory to `/root`.

##### Copy Entrypoint Script
Copies the `entrypoint.sh` script to `/usr/local/bin/`.

##### Make Entrypoint Script Executable
Changes the script permissions to make it executable.

##### Entrypoint
Specifies `entrypoint.sh` as the entrypoint script to run when the container starts.

#### Summary

This setup creates a Ray cluster head node within a Docker container, integrated with Prometheus and Grafana for monitoring. The `entrypoint.sh` script ensures that Prometheus and Grafana are installed, and starts them along with the Ray head or worker nodes, depending on the command-line arguments. The Dockerfile prepares the environment by installing necessary packages and setting up the entrypoint script. This architecture provides a scalable and monitored environment for running distributed computing tasks with Ray.


Here is the ordered and completed bibliography with relevant links:

### Gradio: User Interface 🎨

The Gradio-based User Interface in this project is located in the `frontend` directory. This UI allows users to interact with the machine learning models and the underlying database through a web-based interface.

#### Directory Structure

- **`.env`**: This file stores environment variables, such as database credentials, which are loaded by the application to configure the connection to PostgreSQL.
- **`docker-compose.yml`**: Defines the Docker services required to run the Gradio interface. It specifies the `frontend` service, which builds the Gradio app using the provided `Dockerfile`.
- **`Dockerfile`**: This file creates a Docker image for the Gradio UI, using a Python 3.11-slim base image. It installs necessary dependencies, including PostgreSQL libraries, and sets up the Gradio application to run on port 7860.
- **`main.py`**: The main script for the Gradio UI. It defines the interface's functionalities, such as uploading documents, executing SQL queries, and processing tasks. The script interacts with a backend service (hosted on Ray) and the PostgreSQL database.
- **`requirements.txt`**: Contains the Python dependencies required to run the Gradio UI, including `gradio`, `psycopg2`, and `requests`.
- **`start_front_app.sh`**: A shell script to start the Gradio UI using Docker.
- **`stop_front_app.sh`**: A shell script to stop the Gradio UI Docker container.

#### .env File Template

The `.env` file is used to store environment variables that configure the connection to the PostgreSQL database and set up the GPT model and embedding engine. Below is a template of the `.env` file with example values:

```plaintext
# OpenAI API Key and Model Configuration
OPENAI_API_KEY='your_openai_api_key'
GPT_MODEL='gpt-4o'
GPT_EMBEDDING_ENGINE='text-embedding-3-large'

# Database connection parameters
POSTGRESQL_HOST="localhost"
POSTGRESQL_PORT=5432
POSTGRESQL_DATABASE="vector_db"
POSTGRESQL_USER="new_user"
POSTGRESQL_PASSWORD="new_password"
```

##### Explanation of Variables:

- **`OPENAI_API_KEY`**: Your API key for accessing OpenAI's GPT models. Replace `'your_openai_api_key'` with your actual API key.
- **`GPT_MODEL`**: Specifies the GPT model to be used, such as `'gpt-4o'`.
- **`GPT_EMBEDDING_ENGINE`**: Defines the embedding engine, such as `'text-embedding-3-large'`, for generating embeddings from text.
  
- **`POSTGRESQL_HOST`**: The hostname or IP address of the PostgreSQL server. Typically, this would be `'localhost'` when running the database locally.
- **`POSTGRESQL_PORT`**: The port number on which PostgreSQL is listening. The default PostgreSQL port is `5432`.
- **`POSTGRESQL_DATABASE`**: The name of the database to connect to. In this example, it’s set to `"vector_db"`.
- **`POSTGRESQL_USER`**: The username for connecting to the PostgreSQL database. Replace `"new_user"` with your actual database username.
- **`POSTGRESQL_PASSWORD`**: The password associated with the PostgreSQL user. Replace `"new_password"` with your actual database password.

#### Docker Setup

To run the Gradio UI, navigate to the `frontend` directory and use the following commands:

```bash
# Navigate to the frontend directory
cd architecture/frontend

# Make the start script executable (if necessary)
chmod +x start_front_app.sh

# Start the Gradio UI using Docker
./start_front_app.sh
```

The Docker setup defines a `front` service that:

- Builds the Docker image from the `Dockerfile`.
- Exposes the Gradio interface on port `7860`.
- Connects to the PostgreSQL database via a common Docker network.
- Uses environment variables defined in `.env` to configure the connection to the PostgreSQL database.

#### Gradio Interface Functionality

The Gradio interface provides the following features:

- **Upload Document**: Allows users to upload a PDF or DOC file to a specified database.
- **Execute SQL Query**: Enables users to run SQL queries against the database and view the results.
- **Process Task**: Users can describe a task for the conversational agent to process, with the results displayed directly in the interface.

To stop the Gradio UI, you can run:

```bash
./stop_front_app.sh
```

This setup provides a complete and interactive web interface for users to manage and interact with their data and machine learning models seamlessly.

### Testing the Platform 🧪

To ensure that the platform is up and running, we have implemented a series of tests using pytest. These tests verify the connectivity and functionality of various components, including Ray, PostgreSQL, MLflow, and Minio. Here is an overview of the tests:

#### Pre-requisites

1. **Environment Variables**: Ensure the following environment variables are set in a `.env` file in the `tests/architecture` directory:
    ```env
    RAY_ADDRESS=ray://localhost:10001
    MLFLOW_ADDRESS=localhost
    MLFLOW_TRACKING_URI=http://localhost
    POSTGRES_HOST=localhost
    POSTGRES_PORT=5432
    POSTGRES_DB=your_db
    POSTGRES_USER=your_user
    POSTGRES_PASSWORD=your_password
    MINIO_ADDRESS=localhost
    MINIO_ACCESS_KEY=your_access_key
    MINIO_SECRET_KEY=your_secret_key
    ```
#### Tests Overview

1. **Ray Cluster**: Checks if the Ray cluster is up and running.
2. **PostgreSQL Connection**: Verifies the connection to the PostgreSQL database.
3. **pgvector Extension**: Ensures that the pgvector extension is properly set up in the PostgreSQL database.
4. **PostgreSQL Databases**: Confirms that the required databases (`mlflowdb` and `vector_db`) are created in PostgreSQL.
5. **MLflow Tracking Server**: Tests the connection to the MLflow tracking server.
6. **Minio Connection**: Checks if the Minio server is up and running.
7. **Minio Buckets**: Verifies that the required buckets (`data` and `mlflow`) are created in Minio.

### Running the Tests

To run the tests, go to `tests/architecture`, and execute the following command in your terminal:

```sh
pytest
```

## NL2SQL
## Bibliography

1. **Attention Is All You Need**
   - [Attention Is All You Need](https://arxiv.org/pdf/1706.03762)

2. **Ray Serve**
   - [Ray Serve: Scalable and Programmable Serving for Machine Learning Models](https://docs.ray.io/en/latest/serve/index.html)

3. **MLflow**
   - [MLflow: An Open-Source Platform for the Machine Learning Lifecycle](https://mlflow.org/)

4. **Autogen**
   - [An Open-Source Programming Framework for Agentic AI](https://microsoft.github.io/autogen/)
   - [Autogen paper](https://arxiv.org/pdf/2308.08155)

6. **Transformers**
   - [Transformers: State-of-the-Art Natural Language Processing](https://huggingface.co/transformers/)

7. **MLOps**
   - [MLOps: Continuous Delivery and Automation Pipelines in Machine Learning](https://cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning?hl=es-419)

8. **Embedding Strategies for documents**
    - [Document Chunking for AI RAG Applications](https://medium.com/@david.richards.tech/document-chunking-for-rag-ai-applications-04363d48fbf7)
    - [Chunking Strategies for LLM Applications](https://www.pinecone.io/learn/chunking-strategies/)
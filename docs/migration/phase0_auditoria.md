# Fase 0 – Auditoría y alineación

## 0.1 Inventario de servicios Ray Serve y contratos actuales

### Despliegues activos
- **`APIGateway`** expone un único endpoint HTTP y enruta acciones REST hacia los manejadores Ray Serve de embeddings, pgvector y orquestación conversacional.【F:src/ray_endpoints/setup_api_gateway.py†L7-L52】
- **`Text2Vectors`** coordina la estrategia de chunking y la generación de embeddings para devolver una lista indexada de vectores listos para persistir.【F:src/ray_endpoints/set_up_embeddings.py†L6-L31】
- **`ChunkStrategy`** aplica un particionado fijo por tamaño de lista, reutilizado por `Text2Vectors`.【F:src/ray_endpoints/set_up_embeddings.py†L33-L36】
- **`EmbeddingEndpoints`** encapsula las llamadas al API de OpenAI y corta manualmente las dimensiones cuando el modelo no acepta el parámetro `dimensions`.【F:src/ray_endpoints/set_up_embeddings.py†L38-L47】
- **`PGVectorConnection`** gestiona inserciones batch, ejecuciones SQL arbitrarias y utilidades de limpieza sobre PostgreSQL/pgvector.【F:src/ray_endpoints/set_up_pgvector.py†L1-L55】
- **`RAGChatEndpoint`** reconstruye agentes Autogen bajo demanda y ejecuta la conversación multiagente con transición explícita entre User Proxy → Planner → NL2SQL ↔ Feedback.【F:src/ray_endpoints/set_up_agents_chat.py†L1-L93】

### Contratos HTTP expuestos por `APIGateway`
| Acción (`/api/<action>`) | Payload esperado | Flujo backend | Respuesta | Observaciones |
| --- | --- | --- | --- | --- |
| `compute_vectors` | JSON con `text`, `chunk_size`, `embedding_model` | `Text2Vectors.compute_vectors` genera chunks y embeddings secuenciales. | Lista de tuplas `(entity_id, embedding, chunk)` | No persiste datos; usado por pipelines manuales.【F:src/ray_endpoints/setup_api_gateway.py†L19-L23】【F:src/ray_endpoints/set_up_embeddings.py†L12-L31】 |
| `text_to_vectordb` | JSON como `compute_vectors` + opcional `database` | Embeddings + inserción en tabla `vector_embeddings_<chunk_size>` mediante `PGVectorConnection`. | Lista de vectores insertados | Inserta `database` cuando está presente.【F:src/ray_endpoints/setup_api_gateway.py†L24-L30】【F:src/ray_endpoints/set_up_pgvector.py†L8-L34】 |
| `agents_chat` | `{ "task": str, "database": str? }` | `RAGChatEndpoint.call_rag_chat` ejecuta conversación Autogen; concatena base si se pasa. | Historial completo de mensajes | Devuelve lista de diccionarios (role, name, content).【F:src/ray_endpoints/setup_api_gateway.py†L31-L33】【F:src/ray_endpoints/set_up_agents_chat.py†L47-L86】 |
| `execute_query` | `{ "database": str?, "query": str }` | Llamada directa a `PGVectorConnection.execute_query`. | Resultado crudo de `cursor.fetchall()` | Sin normalización de tipos ni paginación.【F:src/ray_endpoints/setup_api_gateway.py†L34-L35】【F:src/ray_endpoints/set_up_pgvector.py†L36-L53】 |
| `upload_pdf` | Form multipart con `file`, `chunk_size`, `embedding_model`, opcional `database` | Extrae texto con PyMuPDF, calcula embeddings y almacena. | `{ "result": "document uploaded successfully" }` | Carga síncrona; bloquea hasta finalizar inserción.【F:src/ray_endpoints/setup_api_gateway.py†L36-L45】【F:src/ray_endpoints/set_up_embeddings.py†L20-L28】 |

### Dependencias y configuración
- El contenedor Ray inicializa variables de entorno críticas (`OPENAI_API_KEY`, credenciales PostgreSQL, modelo GPT y embedding) en su script de entrada y prepara entornos Conda con dependencias de Autogen, MLflow y Prometheus/Grafana.【F:architecture/ray_cluster/ray/entrypoint.sh†L3-L84】
- El `docker-compose` actual solo levanta el nodo cabeza de Ray y expone puertos 8000-8999 para los deployments Serve, además del dashboard y métricas.【F:architecture/ray_cluster/docker-compose.yml†L1-L36】

## 0.2 Requisitos funcionales de la UI Gradio y flujo de comunicación
- La interfaz `architecture/frontend/main.py` define tres pestañas: **Upload Document**, **Execute SQL Query** y **Process Task**, todas contra el API Ray Serve alojado en `http://ray-head:8000/api` usando peticiones HTTP síncronas.【F:architecture/frontend/main.py†L1-L103】
- `Upload Document` envía formularios multipart a `/upload_pdf` con parámetros fijos (`chunk_size=1536`, `embedding_model=text-embedding-3-large`) y permite seleccionar o crear base de datos destino.【F:architecture/frontend/main.py†L30-L41】【F:architecture/frontend/main.py†L77-L90】
- `Execute SQL Query` construye un DataFrame localmente para visualizar resultados, generando nombres de columnas cuando el SELECT usa `*` o la API devuelve listas sin cabecera.【F:architecture/frontend/main.py†L43-L74】
- `Process Task` realiza una llamada POST a `/agents_chat` y muestra el historial completo formateado; actualmente no consume streaming ni WebSocket, y se limita a Markdown enriquecido.【F:architecture/frontend/main.py†L79-L101】
- Todas las pestañas dependen de `fetch_databases()`, que consulta directamente PostgreSQL (`vector_embeddings_1536`) para poblar los dropdowns, con botones de refresco por pestaña.【F:architecture/frontend/main.py†L55-L74】【F:architecture/frontend/main.py†L90-L101】

## 0.3 Integración con MLflow y pipeline de evaluación
- El script `src/agents_mlflow.py` carga queries desde `src/embeddings/queries.json` y usa el endpoint local `/agents_chat` para obtener la última respuesta de los agentes, replicando el contrato de producción.【F:src/agents_mlflow.py†L1-L45】
- Durante la evaluación, registra parámetros del experimento (`framework=Autogen`, modelo GPT-4o, chunk_size, estrategia de chunking, embedding model) y calcula similaridad mediante `fuzzywuzzy` junto con coincidencia de resultados ejecutando SQL real contra PostgreSQL.【F:src/agents_mlflow.py†L46-L124】
- Cuando los resultados SQL difieren, invoca `openai.chat.completions` para verificar equivalencia semántica y loguea métricas agregadas (`average_similarity`, `average_accuracy`) en MLflow, además de guardar artefactos CSV.【F:src/agents_mlflow.py†L109-L151】

## 0.4 Observaciones y brecha para la migración
- El flujo actual depende fuertemente de contratos REST síncronos; la migración a Starlite deberá mantener los mismos payloads para no romper la UI/MLflow mientras se introduce WebSocket o streaming opcional.
- `send_messages_to_front` está preparado para WebSocket, pero ninguno de los entrypoints Ray Serve o la UI Gradio lo utiliza hoy; su reemplazo puede centralizarse en la nueva capa Starlite para habilitar comunicación bidireccional.【F:src/utils/utils.py†L6-L76】
- Las credenciales de PostgreSQL se leen en múltiples lugares (Ray Serve, UI Gradio, utilidades de base de datos), por lo que conviene consolidarlas en la nueva configuración Starlite/LangChain para reducir duplicidad.【F:architecture/frontend/main.py†L55-L64】【F:src/ray_endpoints/set_up_pgvector.py†L14-L55】
- Ray se mantiene como orquestador de despliegue y observabilidad (Prometheus/Grafana) aun cuando los agentes se ejecutan dentro de un único deployment; definir si el cluster seguirá siendo necesario tras migrar a Starlite es un punto de decisión clave.【F:architecture/ray_cluster/ray/entrypoint.sh†L56-L108】

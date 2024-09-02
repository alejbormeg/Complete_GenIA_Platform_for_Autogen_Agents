---
title: "Desarrollo y Evaluación de una Plataforma Completa de IA (On Premise) con Agentes Expertos para la Traducción Automática de Lenguaje Natural a SQL (NL2SQL)"
subtitle: "Trabajo fin de Máster"
author: "Alejandro Borrego Megías"
date: "28/08/2024"
documentclass: report
header-includes:
  - \usepackage{longtable}
  - \usepackage{listings}
---

\newpage
\tableofcontents
\newpage

## Abstract
En este trabajo de fin de máster, se ha diseñado y evaluado una plataforma de inteligencia artificial (IA) para la traducción automática de lenguaje natural a SQL (NL2SQL) basada en un enfoque on-premise. Se centra en el uso de técnicas avanzadas como la generación aumentada por recuperación (RAG) y la implementación de agentes expertos autónomos. Este sistema permite la interacción eficaz en lenguaje natural para generar consultas SQL precisas, aplicando modelos avanzados de lenguaje sin reentrenamiento explícito. La arquitectura robusta y modular facilita el despliegue de soluciones de IA independientes de proveedores de servicios en la nube, optimizando tanto la gestión de bases de datos como el procesamiento de lenguaje natural en entornos empresariales y de datos. Este estudio demuestra cómo una infraestructura de IA bien integrada puede mejorar significativamente la accesibilidad y la eficiencia de las tecnologías de bases de datos en diversos escenarios de aplicación.

\newpage

## 1. Introducción

### 1.1. Contexto y Motivación

La rápida evolución de la inteligencia artificial (IA) y el surgimiento de la generación de IA han revolucionado numerosos sectores, facilitando el desarrollo de soluciones innovadoras y cada vez más sofisticadas. A lo largo del Máster en Big Data, Data Science & Inteligencia Artificial en la Universidad Complutense de Madrid, se adquirieron conocimientos avanzados en inteligencia artificial, manejo de grandes volúmenes de datos, y programación en Python. Uno de los campos más prometedores es el desarrollo de agentes autónomos que realizan tareas complejas de manera independiente. 

El progreso en modelos de lenguaje avanzados, especialmente los desarrollados por OpenAI, ha abierto nuevas vías para sistemas interactivos en lenguaje natural. A pesar de sus ventajas, un reto persistente es la integración eficaz de estos modelos sin necesidad de reentrenamiento constante, utilizando enfoques como "Retrieval Augmented Generation" (RAG). Este trabajo de fin de máster responde a la necesidad de aplicar estos conocimientos prácticamente, mediante la creación de una plataforma de IA operativa y aplicable en un contexto productivo.

El objetivo es diseñar y desarrollar una plataforma de IA independiente de servicios en la nube, basada en contenedores y máquinas virtuales para un entorno local. Esta infraestructura facilitará el despliegue eficiente de soluciones de IA y se aplicará específicamente a la traducción de lenguaje natural a SQL (NL2SQL) mediante agentes expertos, optimizando así la precisión y eficiencia del sistema mediante la tecnología RAG.

### 1.2. Objetivos del TFM

Este trabajo de fin de máster tiene como metas:

- **Desarrollar una plataforma de IA funcional y completa:** Construir una arquitectura modular y escalable que permita el despliegue de soluciones de IA en un entorno local, independiente de proveedores de nube.
- **Implementar técnicas de Generación Aumentada por Recuperación (RAG):** Utilizar modelos avanzados de OpenAI para mejorar la gestión del conocimiento y la eficacia en la generación de respuestas sin necesidad de reentrenamiento constante.
- **Desarrollar un sistema de agentes expertos en NL2SQL:** Crear un sistema interactivo que permita a los usuarios formular consultas SQL a través de instrucciones en lenguaje natural, usando agentes autónomos que mejoren la precisión y relevancia de las respuestas.
- **Diseñar una aplicación para usar el sistema implementado:** Finalmente, se pretende desarrollar una interfaz gráfica para poder interacturar con los agentes así como incorporar nuevos datos a la base de datos vectorial usada para el RAG.

## 2. Revisión del Estado del Arte

En esta sección se realiza una revisión exhaustiva del estado del arte en tres áreas clave: las plataformas de Machine Learning (ML) con MLOps, el desarrollo de agentes de inteligencia artificial (IA), y las soluciones para la tarea de NL2SQL.

### 2.1 Estado del Arte en la Construcción de Plataformas de ML con MLOps, el Diseño de Agentes de IA y la Resolución de la Tarea de NL2SQL

#### MLOps y Plataformas de Machine Learning

El campo de MLOps (Machine Learning Operations) continúa evolucionando rápidamente, consolidándose como una práctica esencial para gestionar de manera eficiente todo el ciclo de vida de los modelos de Machine Learning (ML). MLOps se refiere a la combinación de prácticas de DevOps con el desarrollo de modelos de ML, con el objetivo de automatizar y optimizar cada etapa del ciclo de vida de los modelos. Esto incluye desde la preparación y gestión de datos, hasta el entrenamiento, despliegue, monitoreo y mantenimiento continuo de los modelos en producción.

Un ejemplo representativo de este avance es el trabajo sobre las distintas etapas de MLOps presentado en [MLOps stages](https://mlops-for-all.github.io/en/docs/introduction/levels/), que detalla las fases que un proyecto de ML debe atravesar para integrar MLOps de manera efectiva. Este enfoque permite desarrollar plataformas integrales que no solo facilitan la creación de modelos de ML, sino que también aseguran su correcto funcionamiento en entornos productivos, garantizando así su sostenibilidad y escalabilidad a lo largo del tiempo.

Entre las plataformas más destacadas que implementan estas prácticas se encuentran Databricks, Hugging Face, y Weights & Biases, las cuales ofrecen soluciones robustas para gestionar cada aspecto del ciclo de vida de los modelos de ML, desde la ingestión de datos hasta su monitoreo en producción.

1. **Databricks**: Esta plataforma destaca por su integración unificada de la gestión de datos y activos de IA, lo que mejora significativamente la gobernanza y el monitoreo de modelos de ML. Su catálogo Unity Catalog, junto con las mejoras en Model Serving, facilitan la implementación de modelos en tiempo real y garantizan un monitoreo eficiente y continuo ([Databricks, 2024](https://www.databricks.com/blog/big-book-mlops-updated-generative-ai)).

2. **Hugging Face**: Se ha posicionado como una plataforma esencial en el ámbito del procesamiento del lenguaje natural (NLP), ofreciendo herramientas avanzadas para el entrenamiento, ajuste fino y evaluación de modelos. Además, permite compartir modelos y conjuntos de datos con la comunidad, promoviendo la colaboración en proyectos de ML ([Hugging Face, 2024](https://www.kdnuggets.com/7-end-to-end-mlops-platforms-you-must-try-in-2024)).

3. **Weights & Biases**: Evolucionó de ser una plataforma para el seguimiento de experimentos a una solución completa de MLOps, con funcionalidades para la automatización de flujos de trabajo, optimización de hiperparámetros y despliegue de aplicaciones de IA ([Weights & Biases, 2024](https://www.kdnuggets.com/7-end-to-end-mlops-platforms-you-must-try-in-2024), [Saturn Cloud, 2024](https://saturncloud.io/blog/2024-guide-to-mlops-platforms-tools/)).

4. **MLflow**: MLflow es una plataforma de código abierto diseñada para gestionar el ciclo de vida de los modelos de Machine Learning. Ofrece herramientas para el seguimiento de experimentos, la gestión de modelos, el empaquetado de código y la implementación de modelos. Es ampliamente utilizado en la comunidad de ML por su versatilidad y su capacidad para integrarse con diferentes herramientas y plataformas, lo que permite un manejo más eficiente de los experimentos y modelos a lo largo de su ciclo de vida ([MLflow, 2024](https://mlflow.org/)).

5. **Ray**: Ray es un marco de trabajo flexible y de alto rendimiento para la computación distribuida, diseñado para acelerar la ejecución de aplicaciones de IA y ML a gran escala. Ray permite ejecutar tareas paralelas y distribuidas de manera eficiente, lo que lo convierte en una opción ideal para entrenar modelos de ML que requieren grandes volúmenes de datos y recursos computacionales. Además, Ray se integra bien con otras plataformas de MLOps, lo que facilita la escalabilidad y el monitoreo en entornos de producción ([Ray, 2024](https://www.ray.io/)).

El desarrollo de MLOps ha dado lugar a la adopción de LLMOps, una extensión de MLOps centrada en modelos de lenguaje a gran escala (LLMs), especialmente relevante dada la creciente popularidad de los modelos generativos. La integración de estos modelos en plataformas como Databricks facilita su gestión y escalabilidad en entornos empresariales complejos.

En este trabajo se intentará construir una plataforma que cumpla con el *Stage 0* del artículo [MLOps stages](https://mlops-for-all.github.io/en/docs/introduction/levels/) sin usar ningún proveedor cloud, que pueda ser desplegada en un entorno *on-premise* en la que usaremos **Ray cluster** y **Mlflow**.

#### Diseño de Agentes de IA

El diseño de agentes de inteligencia artificial en 2024 está altamente influenciado por los avances en modelos generativos y de lenguaje, particularmente los grandes modelos de lenguaje (LLMs) ([Wu et al., 2024](#wu2024)). Estos agentes ahora pueden interactuar de manera más natural y contextual con los usuarios. Empresas como **OpenAI** y **Google** han incorporado estas capacidades en sus plataformas, permitiendo la creación de agentes que no solo responden a consultas, sino que también pueden ejecutar tareas complejas basadas en texto, como programación o análisis de datos ([Wang et al., 2024](#wang2024)). Soluciones como **AutoGen** ([Wu et al., 2024](#wu2024)), **OpenDevin** ([Wang et al., 2024](#wang2024)), **LlamaIndex** ([Liu, 2022](#liu2022)), y **LangChain** ([Chase, 2022](#chase2022)) son representativas de esta tendencia.

Los agentes de IA modernos también mejoran en su integración con herramientas de desarrollo de software, permitiendo su participación en flujos de trabajo de DevOps, CI/CD y MLOps, lo que asegura una implementación y mantenimiento más efectivos de soluciones de IA.

Para este trabajo emplearemos el framework **Autogen**.

#### Resolución de la Tarea NL2SQL

La tarea de NL2SQL, que convierte consultas en lenguaje natural a SQL, ha avanzado significativamente gracias a la mejora en los modelos de lenguaje y las técnicas de transferencia de aprendizaje. Los modelos como **Transformers** se han mostrado extremadamente efectivos para comprender y mapear el lenguaje natural a SQL. Plataformas como **Hugging Face** ofrecen modelos preentrenados que pueden ser adaptados para tareas específicas de NL2SQL, facilitando su implementación en aplicaciones empresariales.

Además, la integración de técnicas de MLOps ha permitido que estos modelos sean entrenados, desplegados y monitoreados de manera continua, optimizando su rendimiento en entornos de producción ([neptune.ai, 2024](https://neptune.ai/blog/mlops-tools-platforms-landscape)). En nuestro caso intentaremos adaptar *Mlflow* y *Ray Cluster* para este propósito pese a no tener explícitamente implementadas herramientas para agentes en sus respectivas versiones más recientes, tratando de simular una compañia que trabaja con estas herramientas y pretende incorporar agentes.

## 3. Arquitectura de la Plataforma
### 3.1. Visión General de la Plataforma

La plataforma desarrollada en este proyecto está diseñada para ser una solución integral y modular, capaz de gestionar y desplegar modelos de inteligencia artificial en un entorno de producción on-premise. Se trata de una arquitectura compuesta por múltiples componentes interconectados, cada uno de los cuales cumple una función específica en el ciclo de vida de los modelos de IA, desde su almacenamiento hasta su despliegue y gestión continua.

La plataforma está construida sobre tecnologías de contenedorización y virtualización, utilizando Docker y Docker Compose para orquestar los servicios de manera eficiente. La elección de un entorno on-premise permite una mayor flexibilidad e independencia respecto a proveedores de la nube, lo que facilita su adaptación a diferentes infraestructuras y requisitos de seguridad. 

Los componentes principales incluyen **Minio** para el almacenamiento de artefactos, **PostgreSQL** y **PGAdmin** para la gestión de bases de datos, **MLflow** para el registro y seguimiento de modelos, y **Ray Cluster** para la distribución y despliegue de tareas. Estos elementos están integrados en una red de Docker, que asegura el aislamiento y persistencia de datos, mientras que **Nginx** actúa como un proxy inverso para gestionar las solicitudes de manera segura y eficiente. Cada uno de estos componentes corre en un contenedor propio y para levantar la plataforma completa usamos *Docker Compose*.

El diseño de esta plataforma se ha realizado siguiendo el arículo de Google [MLOps: Continuous Delivery and Automation Pipelines in Machine Learning](https://cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning?hl=es-419). En el cual se presenta la siguiente arquitectura para el Stage 0 de un sistema de Machine Learning adaptado a nuestro problema concreto:

![MLOPS](./imgs/stage_0.png)

Este primer stage se caracteriza por la presencia aún de fases manuales para el tratamiento de datos, experimentación y selección de modelo ganador, pero incluye la presencia de un *Model Registry* para registrar los modelos usados, los datasets empleados y los resultados obtenidos con dichos modelos de forma que mantenemos una traza reproducible que nos permite replicar los procesos de entrenamiento y experimentación así como compartir de forma sencilla los modelos ganadores, algo que hoy en día sigue siendo tedioso para los Científicos de datos que continúan en muchas ocasiones compartiendo las carpetas comprimidas con los pesos de los modelos y se corre el riesgo de no conocer exactamente qué versión del modelo se está desplegando. En nuestra Arquitectura, el papel de *Model Registry* lo realizará **Mlflow**, que nos permite registrar entrenamientos y resultados de validación de los modelos que probemos y almacenar todos estos resultados como artefactos en la base de datos **Minio**, también emplea **PostgreSQL** como backend store. 

Por otro lado, en el contexto del Stage 0 de ML, utilizaremos Ray Cluster como la solución de Model Serving. Ray es un framework de código abierto que permite ejecutar y escalar modelos de Machine Learning de manera distribuida y eficiente. Internamente, Ray utiliza FastAPI para exponer los servicios y gestiona las unidades de trabajo denominadas "actores" que explicaremos a continuación.

### 3.2. Descripción de Componentes Clave

A continuación se procede a describir los componentes clave de esta arquitectura, aunque los detalles de cómo se ha construido la plataforma cómo se levanta se pueden encontrar en el repositorio que contiene todo el código del proyecto en[Github](https://github.com/alejbormeg/Complete_GenIA_Platform_for_Autogen_Agents).

#### 3.2.1. Minio para Almacenamiento de Artefactos

Minio es una solución de almacenamiento de objetos compatible con S3 que se utiliza en esta plataforma para gestionar los artefactos generados durante el ciclo de vida de los modelos de IA. Este componente es crucial para almacenar de manera segura y escalable los modelos entrenados, los datos de entrenamiento, y otros artefactos relevantes.

Minio se despliega en un contenedor Docker y se configura para permitir acceso tanto a través de API como de una consola web. Se ha integrado con MLflow para que este último pueda utilizarlo como backend de almacenamiento para los artefactos de los experimentos. La persistencia de los datos se asegura mediante la vinculación de volúmenes locales en el host, lo que permite que los artefactos se mantengan incluso en caso de que el contenedor se detenga o reinicie.

#### 3.2.2. PostgreSQL y PGAdmin para Gestión de Bases de Datos

PostgreSQL es la base de datos relacional utilizada para almacenar la información de backend de la plataforma, incluyendo los metadatos de los experimentos gestionados por MLflow. PostgreSQL es elegido por su robustez, escalabilidad y la capacidad de soportar extensiones como PGVector, que facilita la gestión de datos vectoriales, cruciales en aplicaciones de inteligencia artificial.

PGAdmin es una herramienta esencial para administrar bases de datos PostgreSQL a través de una interfaz gráfica intuitiva. Permite a los desarrolladores y administradores gestionar tablas, ejecutar consultas SQL, y monitorear la actividad de la base de datos de manera eficiente. Al estar contenedorizados, tanto PostgreSQL como PGAdmin son fáciles de desplegar y gestionar en un entorno on-premise, garantizando una configuración consistente y mantenible.

Además, PostgreSQL se potencia con la extensión **PgVector**, que permite almacenar y buscar eficientemente vectores, convirtiéndolo en una base de datos vectorial ideal para aplicaciones de machine learning e inteligencia artificial. Esto facilita la integración de datos estructurados y no estructurados, optimizando las búsquedas y la recuperación de información basada en similitudes.

#### 3.2.3. MLflow para el Registro y Seguimiento de Modelos

MLflow es un componente central de la plataforma que permite el seguimiento, registro y gestión de los modelos de IA. Este componente facilita el ciclo de vida completo del modelo, desde el entrenamiento hasta el despliegue, permitiendo un control exhaustivo sobre las versiones de los modelos y los experimentos realizados.

Dentro de la plataforma, MLflow se configura como un **Tracking Server** para utilizar **Minio** como su backend de almacenamiento de artefactos y **PostgreSQL** como su backend de metadatos. Esto asegura que todos los datos relacionados con los experimentos y los modelos estén centralizados y accesibles para su análisis y despliegue. MLflow también proporciona una interfaz web para la visualización de los experimentos y el estado de los modelos, lo que facilita la colaboración y la toma de decisiones. Más detalles sobre esto en el anexo sobre [Mlflow](#mlflow).

#### 3.2.4. Ray Cluster para Despliegue de Modelos y Distribución de Tareas

Ray es un marco de trabajo distribuido diseñado para la ejecución de aplicaciones de inteligencia artificial a gran escala. En esta plataforma, **Ray Cluster** se utiliza para coordinar y distribuir tareas entre los diferentes agentes del sistema NL2SQL, abarcando tanto el despliegue de modelos como la ejecución de tareas de procesamiento en paralelo, lo que optimiza el uso de los recursos disponibles.

La integración de Ray con la plataforma se realiza mediante contenedores Docker, lo que facilita su escalabilidad y permite agregar nodos al clúster a medida que aumenta la demanda. Además, Ray se conecta con herramientas como Prometheus y Grafana para el monitoreo en tiempo real de su rendimiento, lo que ayuda a detectar cuellos de botella y ajustar la configuración según las necesidades del sistema. véase más en detalle en el anexo sobre [Ray](#ray-cluster)


### 3.3. Redes y Volúmenes en Docker: Aislamiento y Persistencia

Uno de los aspectos fundamentales de la arquitectura es el uso de redes y volúmenes en Docker para asegurar el aislamiento de los componentes y la persistencia de los datos. La plataforma utiliza varias redes de Docker, cada una dedicada a un conjunto de servicios que necesitan comunicarse entre sí. Por ejemplo, se utiliza una red frontend para los servicios accesibles por el usuario final y una red backend para los servicios internos, como las bases de datos.

Los volúmenes de Docker se emplean para garantizar que los datos críticos, como los almacenados en PostgreSQL o Minio, se mantengan persistentes incluso si los contenedores se reinician. Esto no solo asegura la integridad de los datos, sino que también facilita las operaciones de backup y recuperación.

### 3.4. Gestión de Versiones de Modelos

La gestión de versiones de modelos es manejada principalmente por MLflow, que permite rastrear cada versión de un modelo junto con sus metadatos, artefactos y resultados de pruebas. Esto asegura que cualquier versión de un modelo pueda ser restaurada y desplegada nuevamente si fuera necesario, facilitando el mantenimiento y la mejora continua de la plataforma.

Este enfoque modular y escalable asegura que la plataforma no solo sea robusta y eficiente, sino también adaptable a nuevas tecnologías y casos de uso futuros, manteniendo un alto nivel de seguridad y control en un entorno on-premise.

### 3.5 Testeo de la plataforma

Además se ha includio un conjunto de test que comprueban una vez la arquitectura está funcionando que está correctamente levantada. Para más detalles sobre esto consultar el repositorio del proyecto en [GitHub](https://github.com/alejbormeg/Complete_GenIA_Platform_for_Autogen_Agents).

## 4. Desarrollo del Sistema de Agentes NL2SQL

Una vez construida la arquitectura, para aplicarla en un caso de uso real, se ha pensado crear un sistema de Agentes capaz de resolver la tarea de traducir el lenguaje natural a SQL empleando la técnica de RAG detallada en el artículo de Autogen [Retrieval-Augmented Generation (RAG) Applications with AutoGen](https://microsoft.github.io/autogen/blog/2023/10/18/RetrieveChat). A continuación explicamos todos estos componentes en detalle.

### 4.0 Conceptos teóricos

#### Técnica de RAG (Retrieval-Augmented Generation)

La Técnica de RAG, o Retrieval-Augmented Generation, es un enfoque de generación de texto que combina la recuperación de información con la generación automática de contenido. En esencia, RAG integra un sistema de recuperación de documentos (retriever) con un modelo generador de lenguaje natural. El proceso funciona de la siguiente manera:

**Recuperación de Información**: Se utiliza un modelo de recuperación para buscar documentos relevantes en una base de datos o corpus grande en función de una consulta específica. Estos documentos pueden contener información que es crucial para responder o generar un texto preciso y relevante.

**Generación de Contenido**: Luego, un modelo de generación (como un modelo de lenguaje entrenado, en nuestro caso, GPT) toma como entrada tanto la consulta original como los documentos recuperados. Utilizando esta información, el modelo genera una respuesta o texto que está enriquecido con los datos extraídos de los documentos.

La clave de RAG es que permite que el modelo generador produzca respuestas que están informadas por datos específicos y contextualmente relevantes, lo que mejora la precisión y utilidad del contenido generado, especialmente en tareas complejas donde el conocimiento actualizado y específico es crucial.

#### Uso de la Técnica de RAG en un Sistema de Agentes con Autogen para la Tarea de NL2SQL

En el contexto de un sistema de agentes con Autogen para resolver la tarea de NL2SQL, vamos a emplear la Técnica de RAG para mejorar la precisión y eficacia en la generación de consultas SQL. La tarea de NL2SQL implica traducir lenguaje natural a consultas SQL, y en este caso, se trata de un entorno donde las bases de datos están descritas en documentos PDF que incluyen la estructura y detalles de las bases de datos en PostgreSQL con la extensión PGVector.

* **Recuperación de Documentos**: Dado que las bases de datos son complejas y están descritas en documentos PDF, utilizaremos un componente de recuperación para extraer la información relevante de estos documentos. Los agentes en nuestro sistema, apoyados por Autogen, se encargarán de escanear los PDFs para identificar secciones y detalles específicos sobre las bases de datos que son necesarios para construir consultas SQL precisas.

* **Generación de Consultas SQL**: Una vez que los documentos relevantes han sido recuperados, los agentes utilizarán esa información para generar consultas SQL. Por ejemplo, si un usuario pide información que requiere acceder a tablas o columnas específicas, el sistema recuperará los detalles correspondientes desde los PDFs y generará la consulta SQL adecuada utilizando la información obtenida.

* **Contextualización y Adaptación**: Al usar la técnica de RAG, el sistema no solo generará consultas SQL basadas en el lenguaje natural del usuario, sino que también adaptará estas consultas al contexto específico de las bases de datos descritas en los documentos PDF. Esto es especialmente útil cuando se trabaja con bases de datos que han sido extendidas o personalizadas, como es el caso con PGVector en PostgreSQL, donde se pueden requerir consultas especializadas para manejar datos vectoriales.

Al aplicar la Técnica de RAG en este sistema de agentes, logramos que las consultas SQL generadas no solo sean correctas desde el punto de vista sintáctico, sino también precisas y alineadas con la estructura y contenido específico de las bases de datos descritas en los documentos. Esto optimiza el proceso de traducción de lenguaje natural a SQL, garantizando que las respuestas sean adecuadas y útiles para las consultas de los usuarios.

### 4.1. Diseño del Sistema de Agentes

El sistema de agentes NL2SQL desarrollado para esta plataforma se basa en la implementación de múltiples agentes colaborativos, cada uno con roles y responsabilidades específicos, que trabajan en conjunto para traducir consultas en lenguaje natural a SQL. Estos agentes utilizan el modelo GPT-4o para aprovechar sus avanzadas capacidades de procesamiento de lenguaje natural, lo que les permite realizar tareas complejas de manera eficiente y con un alto grado de precisión. El diseño se ha realizado con el framework [Autogen].

### 4.2. Descripción de los Agentes

Cada agente en el sistema tiene un rol especializado, diseñado para contribuir a la resolución eficiente de las consultas del usuario. El esquema que describe el flujo seguido por los agentes para resolver las peticiones del usuario es el siguiente:

![Agents Flow](./imgs/NL2SQL_agents.png)

A continuación, se detallan las funciones y responsabilidades de cada agente.

#### Resumen de los Agentes del Sistema

1. **User Proxy Agent:** Actúa como intermediario entre el usuario y el sistema, gestionando las interacciones y dirigiendo las solicitudes al agente adecuado. Inicia y finaliza las conversaciones basándose en señales específicas, sin requerir intervención humana.

2. **Document Retrieval Agent:** Busca y recupera información relevante de una base de datos vectorizada utilizando embeddings para asegurar que las respuestas sean contextualmente precisas. Funciona de manera autónoma y apoya al Planner Agent con la información recuperada.

3. **Planner Agent:** Comprende la intención del usuario mediante técnicas de comprensión del lenguaje natural (NLU) y planifica el flujo de tareas, decidiendo qué agentes deben activarse para cumplir con la solicitud del usuario. Opera de manera autónoma y coordina el proceso.

4. **NL to SQL Agent:** Transforma la consulta en lenguaje natural del usuario en una consulta SQL optimizada, asegurando precisión y eficiencia. Finaliza su tarea indicando la terminación del proceso.

5. **Feedback Loop Agent:** Evalúa la calidad de la consulta SQL generada y proporciona retroalimentación para mejorar futuras interacciones, cerrando el ciclo de interacción de manera autónoma o reiniciándolo si es necesario.

Para más detalles de la implementación de los [agentes](#agentes-implementados) consultar los anexos.

### 4.3. Implementación de la Infraestructura de Ray para la Coordinación de Agentes

La coordinación entre estos agentes se gestiona a través de un **Ray Cluster**. Ray es una plataforma distribuida que permite ejecutar aplicaciones de inteligencia artificial de manera escalable y eficiente.

### 4.4. Orquestación de Tareas y Escalabilidad

La orquestación de tareas en este sistema de agentes NL2SQL es gestionada mediante **Ray Serve**, un marco de trabajo que permite el despliegue de aplicaciones distribuidas de manera escalable y eficiente.

#### 4.4.1. Arquitectura del Despliegue
El sistema se compone de varios servicios desplegados como "deployments" en Ray Serve. Cada uno de estos servicios se encarga de una parte específica del flujo de trabajo en el proceso de conversión de lenguaje natural a SQL. La arquitectura de despliegue incluye:

**RAGChatEndpoint**: Este servicio gestiona la interacción principal con los agentes que convierten las consultas de lenguaje natural a SQL. Se encarga de orquestar el flujo de trabajo entre los distintos agentes y gestionar la conversación con el usuario.

**PGVectorConnection**: Este servicio maneja las operaciones de base de datos relacionadas con los vectores de embeddings. Puede insertar, eliminar o consultar vectores almacenados en una base de datos PostgreSQL, lo que es esencial para el funcionamiento del Document Retrieval Agent.

**Text2Vectors**: Este servicio transforma el texto en vectores de embeddings, un paso crucial en la indexación y recuperación de documentos relevantes para las consultas del usuario. Utiliza estrategias de fragmentación de texto y genera embeddings utilizando modelos de OpenAI.

**ChunkStrategy** y **EmbeddingEndpoints**: Estos servicios soportan el procesamiento de texto y la generación de embeddings. El primero se encarga de dividir el texto en fragmentos manejables, mientras que el segundo genera los embeddings basados en los fragmentos proporcionados.

**APIGateway**: Este servicio actúa como un punto de entrada centralizado para todas las solicitudes HTTP que interactúan con los diferentes servicios. Dependiendo del tipo de solicitud, dirige la petición al servicio correspondiente, asegurando que cada tarea sea manejada por el agente o proceso adecuado.

En la siguiente imagen podemos ver todos los componentes desplegados en el entorno de **Ray**:

![Endpoints desplegados con Ray Serve](./imgs/ray_deployments.png)

De esta forma, todas las peticiones se envían al **APIGateway**, que en función del contenido de la petición la redirecciona utilizando las *compositions* de Ray al *deployment* que se encarga de procesarla.

#### 4.4.2. Escalabilidad y Gestión de Carga

La escalabilidad vertical está garantizada por el framework **Ray Cluster** como hemos visto en puntos anteriores, y la escalabilidad horizontal por el uso de **Docker**. Que permite levantar todos los Nodos **Workers** de Ray dentro del cluster que se necesiten.

### 4.5. Evaluación de Desempeño y Ajuste de Parámetros

Para asegurar el óptimo desempeño del sistema, se llevan a cabo pruebas de rendimiento y ajustes de parámetros de manera continua. Estas pruebas permiten identificar posibles cuellos de botella y optimizar la interacción entre los agentes. Se utilizan herramientas de monitoreo como **Prometheus** y **Grafana**, integradas con Ray Cluster, para obtener información en tiempo real sobre el comportamiento del sistema y realizar ajustes dinámicos cuando sea necesario.

En resumen, este sistema de agentes NL2SQL es un ejemplo robusto y escalable de cómo las tecnologías de inteligencia artificial, como GPT-4o y Ray, pueden ser utilizadas para crear soluciones prácticas y eficientes para la traducción de lenguaje natural a SQL. Cada agente desempeña un rol crucial en este ecosistema, asegurando que el usuario reciba respuestas precisas y oportunas a sus consultas.

En la siguiente imagen vemos algunas gráficas sobre el uso de CPU y memoria de los componentes desplegados gracias a **Prometheus** y **Grafana**:

![Gráficas de uso de memoria y CPU en Ray por los distintos componentes desplegados](./imgs/graficas_ray.png)

## 5. Pruebas y Validación

En esta sección se describe el proceso de experimentación realizado para seleccionar el mejor modelo de *embeddings* de OpenAI para nuestro problema de NL2SQL así como el mejor modelo de *OpenAI* para la tarea de traducción de *NL2SQL*. Utilizando **MLflow**, hemos registrado, evaluado y validado los resultados de los experimentos, asegurando que la plataforma sea capaz de generar consultas SQL precisas a partir de descripciones en lenguaje natural.


El enfoque de experimentación se basa en un script que ejecuta múltiples pruebas utilizando diferentes estrategias de segmentación de texto y modelos de *embeddings* así como la posterior tarea de *NL2SQL*. Para la elección del modelo se ha utilizado una base de datos ficticia llamada *Social Network* de diseño propio para la prueba y datos irreales, que simula una base de datos de una red social en la que tenemos *Usuarios*, *Comentarios*, *Tweets* y relaciones entre los elementos como usuarios que siguen a otros usuarios, likes en comentarios, etc. Los detalles de la base de datos y su creación pueden encontrarse en los anexos, junto con las preguntas usadas en validación y sus respectivas sentencias SQL. Todos los detalles sobre la creación de la base de datos y su estructura pueden consultarse en el repositorio de [GitHub](https://github.com/alejbormeg/Complete_GenIA_Platform_for_Autogen_Agents).

A continuación, se resume el flujo de trabajo:

1. **Cargar y Preparar el Entorno**: Se inicializa el entorno cargando las variables necesarias para la conexión con Mlflow y configurando la API de OpenAI. Además, se cargan las 10 consultas de evaluación de un archivo JSON externo.

2. **Definir Estrategias y Modelos**: Se configuran varias estrategias de segmentación (fixed, nltk, spacy) y se seleccionan tres candidatos a modelos de *embeddings* de OpenAI: `text-embedding-3-small`, `text-embedding-3-large` y `text-embedding-ada-002`. Los modelos a evaluar como encargados de la tarea de *NL2SQL* fueron *GPT-3.5-Turbo* y *GPT-4o*. 

3. **Ejecución de Experimentos**: Para cada combinación de estrategia de segmentación, tamaño de fragmento, modelo de *embeddings* y modelo para *NL2SQL*, se ejecuta un experimento que incluye:
   - **Segmentación del Texto**: El texto del documento PDF se segmenta utilizando la estrategia seleccionada.
   - **Creación de Embeddings**: Se generan *embeddings* para cada fragmento de texto segmentado con el modelo de embeddings seleccionado.
   - **Almacenamiento y Recuperación de Vectores**: Los *embeddings* generados se almacenan en una base de datos PostgreSQL con la extensión PGVector, y posteriormente se recuperan vectores relacionados para cada consulta.
   - **Generación de Consultas SQL**: Utilizando el modelo de *NL2SQL*, se generan consultas SQL basadas en la descripción de la consulta y los textos relacionados recuperados.
   - **Evaluación de Resultados**: Se compara la consulta SQL generada con la esperada, calculando la similitud utilizando la métrica FuzzyWuzzy con un rango de 0-100 y verificando la coincidencia de resultados al ejecutar ambas consultas en la base de datos. Para verificar la coincidencia se realiza una consulta a GPT-4o dándole el role de experto en SQL y el contexto necesario para que decida si el resultado obtenido por ambas consultas (la generada y la esperada) en esencia son la misma y la única diferencia es que hay información adicional poco relevante en alguna de ellas.

4. **Registro y Validación con MLflow**: 
   - **Parámetros y Resultados**: Se registran todos los parámetros utilizados en cada experimento, así como los resultados obtenidos, como la similitud promedio y el *accuracy* promedio entre las consultas generadas y las esperadas.
   - **Evaluación Continua**: Los resultados se almacenan en un archivo CSV que es registrado como un artefacto en MLflow, permitiendo un análisis detallado de cada experimento y facilitando la toma de decisiones sobre el modelo de *embeddings* más adecuado.
   - **Gestión de Vectores**: Al finalizar cada experimento, se limpian los vectores almacenados para asegurar un entorno limpio para la siguiente prueba.

El objetivo con este experimento es identificar la mejor técnica para realizar la partición en *Chunks* de los documentos que describen las bases de datos que se usen, el mejor modelo para hacer los embeddings y el mejor modelo de openAI para hacer la tarea de *NL2SQL*. Posteriormente, el modelo ganador será empleado para crear un chat de Agentes que mejore los resultados del experimento y añadan robustez a la solución obtenida en este experimento.

### 5.1 Resultados y Conclusiones de la fase de experimentación con Mlflow

En las siguientes gráficas podemos ver el *accuracy* promedio y la similitud promedio entre las queries generadas y las esperadas:

![Resultados obtenidos](./imgs/resultados_graficas.png)

El modelo ganador fue el *Run* de *Mlflow* denominado *polite-fox-990*, que empleó **GPT-4o** utilizando un chunksize de **1536** y la estrategia de segmentación **fixed**. Este modelo logró un excelente desempeño, con una similitud promedio de 84.6 y un 80% de *accuracy* en las consultas SQL generadas. Además se determina que la mejor estrategia de partición en chunks es la *Fixed* y el mejor modelo para embeddings el *text-embedding-3-large* con un chunksize de 1536. Lo podemos ver en la siguiente imagen:

![Modelo Ganador del experimento](./imgs/modelo_ganador_mlflow.png)

Los artifacts almacenados para este experimento en *Minio* son los siguientes:

![Artifacts del modelo ganador](./imgs/mlflow_artifacts.png)

Como vemos, los artifacts almacenados resumen los resultados del experimento y el framework Mlflow proporciona una forma de emplear el modelo garantizando que se usará exactamente el mismo modelo probado con todos sus parámetros.

Estos resultados demuestran que el modelo GPT-4o con la configuración descrita es capaz de generar consultas SQL con alta precisión, lo que lo convierte en la opción más adecuada para integrarse en la plataforma de NL2SQL basada en agentes con Autogen. Este enfoque garantiza la precisión y eficiencia necesarias para la traducción de descripciones en lenguaje natural a consultas SQL en entornos complejos como bases de datos PostgreSQL con la extensión PGVector.

### 5.2 Resultados con el sistema de agentes

Una vez tomado el modelo ganador del experimento anterior se procede a:

1. Crear los embeddings del documento que describe la base de datos *Social Network* empleando una estrategia *Fixed* de partición del documento y el modelo *text-embedding-3-large* con un chunksize de 1536, almacenando los resultados en PostgreSQL.

2. Crear el chat de agentes descrito en el punto 4 de este trabajo.

3. Evaluar su rendimiento en mlflow usando las mismas métricas que empleamos en el experimento anterior.

Los resultados obtenidos son los siguientes:

![Resultados con chat de agentes](./imgs/tablas_agentes_mlflow.png)

Como vemos hay un nuevo *Run* que supera en Accuracy (llegando a un 0.9) y mantiene la similaridad a los que se habían probado hasta ahora, que es el del framework de agentes. No obstante las verdaderas mejoras, además del rendimiento vienen en la robustez y capacidad de adaptarse a preguntas poco precisas del ususario (gracias al planner) así como corregir posibles errores de sintaxis de antemano (gracias al feedback_loop), así como poder seguir la traza de cómo se resuelve el problema por parte de la IA en caso de no entender bien el resultado proporcionado.

## 6. Interfaz de Usuario

Se ha desarrollado una interfaz de usuario con **Gradio** para facilitar la interacción con el sistema NL2SQL basado en agentes. Esta interfaz permite a los usuarios cargar documentos que describan bases de datos presentes previamente en PostgreSQL, escribir consultas en lenguaje natural y visualizar las respuestas generadas por los agentes en tiempo real. A continuación, se detalla cada componente de la interfaz:

### 6.1 Descripción de la Interfaz

#### Título y Descripción:

La interfaz se presenta con un título prominente, "NL2SQL Conversation Agent", que destaca la funcionalidad principal de la aplicación.

#### Carga de Documentos:

**File Input**: Los usuarios pueden cargar documentos en formatos PDF o DOC mediante un componente de subida de archivos. Estos archivos se envían al backend para su procesamiento, creación de embeddings y almacenamiento en PostgreSQL.

**File Output**: Después de la carga del documento, la respuesta del backend, que puede incluir detalles sobre el procesamiento del documento o confirmaciones, se muestra en un campo JSON visible para el usuario.

También pueden indicar el nombre de la base de datos para incluirla como *metadato* en los vectores y ayudar al proceso de RAG.

#### Entrada de Consultas y Sentencias SQL:

**Select Database**: Un cuadro de texto permite elegir la base de datos sobre la que ejecutar la consulta

**SQL Input**: Este cuadro de texto permite introducir una sentencia SQL que ejecutar en la base de datos.

#### Process Task:

**Select Database**: Elegimos la base de datos sobre la que queremos preguntar (hace de filtro para los vectores obtenidos en el retrieval).

**Task description**: Cuadro de texto para escribir la consulta deseada en lenguaje natural.

**Process Button**: Al presionar este botón, la consulta y, opcionalmente, la sentencia SQL ingresada se envían al backend. El sistema procesa la información utilizando los agentes NL2SQL y devuelve las respuestas generadas.

#### Salida de Respuestas del Agente:

**Response Output**: Una vez procesada la consulta, las respuestas del agente se presentan en un cuadro de texto de múltiples líneas, que es interactivo solo para visualización y muestra las respuestas generadas en función de la consulta ingresada.

#### Historial de Conversación:

**Conversation History**: Esta sección muestra el historial completo de la conversación entre los agentes, incluyendo todos los mensajes que cada agente ha enviado para la petición del ususario. El cuadro de texto es amplio y tiene la capacidad de desplazarse, lo que permite a los usuarios revisar toda la conversación de manera continua.

Pueden consultarse más detalles técnicos de la implementación consultar el repositorio de [GitHub](https://github.com/alejbormeg/Complete_GenIA_Platform_for_Autogen_Agents). En el anexo [Detalles de la interfaz de usuario](#detalles-de-la-interfaz-de-usuario) se puede ver un ejemplo de chat de agentes en la interfaz así como el resto de funcionalidades.


## 7. Conclusiones

Este Trabajo de Fin de Máster (TFM) ha permitido desarrollar y evaluar una plataforma avanzada para la gestión de agentes inteligentes especializados en la traducción de lenguaje natural a SQL (NL2SQL). A continuación, se resumen los principales hallazgos y contribuciones del trabajo, además de discutir las limitaciones y sugerir líneas de investigación futuras.

### Principales Hallazgos y Contribuciones

- **Desarrollo de una plataforma robusta y escalable**: El TFM ha demostrado la viabilidad de construir una infraestructura basada en contenedores y máquinas virtuales que es independiente de proveedores de servicios en la nube, asegurando la flexibilidad y adaptabilidad necesarias para implementaciones on-premise.

- **Integración de tecnologías avanzadas**: Se han integrado diversas tecnologías, como Minio, PostgreSQL, MLflow, y Ray Cluster, para manejar eficazmente el ciclo de vida de los modelos de IA, desde su desarrollo hasta su despliegue.

- **Implementación efectiva del sistema de agentes NL2SQL**: Utilizando modelos avanzados de lenguaje natural, el sistema de agentes ha sido capaz de interpretar consultas en lenguaje natural y convertirlas en comandos SQL precisos, mostrando una mejora significativa en eficiencia y precisión gracias a la técnica de Retrieval-Augmented Generation (RAG).

### Limitaciones

A pesar de los avances logrados, existen varias limitaciones que deben abordarse:

- **Dependencia de la calidad de los datos**: La efectividad del sistema de agentes depende en gran medida de la calidad y estructura de los datos en los documentos que describen las bases de datos, lo que puede limitar su aplicabilidad en escenarios donde estos datos no están bien organizados o son incompletos.

- **Complejidad en la gestión de componentes**: Aunque la arquitectura modular facilita la escalabilidad, también introduce complejidad en la gestión de múltiples componentes y sus interdependencias, lo que podría complicar el mantenimiento y la actualización de la plataforma.

### Futuras Líneas de Investigación

Para superar las limitaciones mencionadas y expandir las capacidades de la plataforma, se sugieren las siguientes líneas de investigación futura:

- **Mejora en la gestión de datos heterogéneos**: Investigar métodos avanzados para el procesamiento y normalización de datos provenientes de diversas fuentes y formatos, lo que podría mejorar la adaptabilidad del sistema a diferentes bases de datos. Actualmente solo se soportan descripciones de bases de datos en formato PDF.

- **Automatización en la actualización y mantenimiento de componentes**: Desarrollar técnicas de automatización que faciliten la gestión de actualizaciones y dependencias entre los diferentes componentes software, mejorando así la sostenibilidad de la plataforma a largo plazo.

- **Extensión a otros dominios de aplicación**: Explorar la aplicación de la arquitectura y los agentes desarrollados en otros dominios que requieran la conversión de lenguaje natural a otros tipos de lenguajes de programación o comandos, ampliando el alcance y la utilidad de la plataforma.

En conclusión, este TFM ha establecido un sólido punto de partida para la creación de plataformas independientes de IA que no solo mejoran la precisión y eficiencia en tareas específicas como NL2SQL, sino que también ofrecen un marco escalable y adaptable para futuras innovaciones en el campo de la inteligencia artificial.


\newpage

## Bibliography

- <a name="wu2024"></a>Wu, Q., Bansal, G., Zhang, J., Wu, Y., Li, B., Zhu, E., et al. (2024). *AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation Framework*. COLM.
- <a name="wang2024"></a>Wang, X., Li, B., Song, Y., Xu, F. F., Tang, X., Zhuge, M., et al. (2024). *OpenDevin: An Open Platform for AI Software Developers as Generalist Agents*. arXiv. Available at: [https://arxiv.org/abs/2407.16741](https://arxiv.org/abs/2407.16741)
- <a name="liu2022"></a>Liu, J. (2022). *LlamaIndex*. GitHub. Available at: [https://github.com/jerryjliu/llama_index](https://github.com/jerryjliu/llama_index)
- <a name="chase2022"></a>Chase, H. (2022). *LangChain*. GitHub. Available at: [https://github.com/langchain-ai/langchain](https://github.com/langchain-ai/langchain)
- MLOps stages. (n.d.). *MLOps for All*. Available at: [https://mlops-for-all.github.io/en/docs/introduction/levels/](https://mlops-for-all.github.io/en/docs/introduction/levels/)
- Databricks. (2024). *Big Book of MLOps: Updated with Generative AI*. Available at: [https://www.databricks.com/blog/big-book-mlops-updated-generative-ai](https://www.databricks.com/blog/big-book-mlops-updated-generative-ai)
- *7 End-to-End MLOps Platforms You Must Try in 2024*. KDnuggets. Available at: [https://www.kdnuggets.com/7-end-to-end-mlops-platforms-you-must-try-in-2024](https://www.kdnuggets.com/7-end-to-end-mlops-platforms-you-must-try-in-2024)
- *2024 Guide to MLOps Platforms & Tools*. Saturn Cloud. Available at: [https://saturncloud.io/blog/2024-guide-to-mlops-platforms-tools/](https://saturncloud.io/blog/2024-guide-to-mlops-platforms-tools/)
- *MLOps Tools & Platforms Landscape*. neptune.ai. Available at: [https://neptune.ai/blog/mlops-tools-platforms-landscape](https://neptune.ai/blog/mlops-tools-platforms-landscape)
- MLflow. (2024). MLflow: An Open-Source Platform for the Machine Learning Lifecycle. Available at: [https://mlflow.org/](https://mlflow.org/)
- Ray. (2024). Ray: A High-Performance Distributed Execution Framework. Available at: [https://www.ray.io/](https://www.ray.io/)
- Retrieval-Augmented Generation (RAG) Applications with AutoGen. Available at: [https://microsoft.github.io/autogen/blog/2023/10/18/RetrieveChat](https://microsoft.github.io/autogen/blog/2023/10/18/RetrieveChat)

\newpage

## Anexos

### Código del proyecto

Todo el código del proyecto se encuentra en el siguiente repositorio de GitHub: [https://github.com/alejbormeg/Complete_GenIA_Platform_for_Autogen_Agents](https://github.com/alejbormeg/Complete_GenIA_Platform_for_Autogen_Agents).

En él se encuentra también un README.md que contiene información relevante sobre cómo levantar todo el proyecto para que pueda ser reproducible.

### Mlflow

#### Introducción a MLflow

MLflow es una plataforma de código abierto diseñada para gestionar todo el ciclo de vida del aprendizaje automático (ML). Proporciona un conjunto de herramientas que abordan los desafíos comunes que enfrentan los equipos de data science y desarrollo cuando trabajan con proyectos de ML, como el seguimiento de experimentos, la administración de modelos y el despliegue en producción.

MLflow se compone de cuatro componentes principales:

1. **MLflow Tracking**: Permite a los usuarios registrar y rastrear parámetros, métricas y artefactos asociados con experimentos de ML. Los datos se almacenan en un servidor centralizado que puede consultarse para comparar diferentes ejecuciones de modelos.

2. **MLflow Projects**: Estandariza el formato de los proyectos de ML, permitiendo que los experimentos sean replicables y fáciles de ejecutar en diferentes entornos. Los proyectos pueden ser empaquetados con dependencias específicas y ejecutados en cualquier entorno compatible.

3. **MLflow Models**: Proporciona un formato estandarizado para empaquetar modelos que puede ser entendido por varias herramientas y frameworks, facilitando la transición de los modelos desde la experimentación hasta la producción.

4. **MLflow Registry**: Ofrece un sistema centralizado para gestionar la evolución de los modelos, incluyendo la versionado, la etapa de desarrollo (staging/production) y anotaciones, lo que facilita la colaboración entre equipos.

#### Conceptos Básicos de MLflow

- **Experimentos y Ejecuciones**: Un experimento en MLflow agrupa un conjunto de ejecuciones de modelos que están relacionados entre sí. Cada ejecución guarda información sobre los parámetros utilizados, las métricas obtenidas y los artefactos generados, como modelos o archivos de salida.

- **Artefactos**: Son los archivos generados durante una ejecución, que pueden incluir modelos entrenados, gráficos de resultados, archivos de datos, entre otros. Estos artefactos pueden almacenarse localmente o en un servicio de almacenamiento en la nube.

- **Parámetros y Métricas**: Los parámetros son los valores utilizados para configurar una ejecución de un modelo, como la tasa de aprendizaje o el número de árboles en un modelo de bosque aleatorio. Las métricas son los resultados obtenidos de la ejecución, como la precisión del modelo o el error cuadrático medio.

#### Principal Potencial de MLflow

El principal potencial de MLflow radica en su capacidad para simplificar y estandarizar el proceso de desarrollo de modelos de ML, lo que permite a los equipos trabajar de manera más eficiente y colaborativa. Al centralizar el seguimiento de experimentos, la gestión de modelos y el despliegue, MLflow facilita la reproducción de resultados, el mantenimiento de registros precisos y la integración continua en el ciclo de vida del aprendizaje automático. Además, su capacidad para integrarse con múltiples frameworks y plataformas hace que sea una herramienta versátil, adecuada para una amplia variedad de aplicaciones en el campo del ML.

#### Mlflow en nuestro proyecto

En el presente trabajo Mlflow se ha configurado como lo denominado *Tracking Server*, con un proxy HTTP para los artefactos, lo que permite pasar las solicitudes de artefactos a través del servidor de seguimiento para almacenar y recuperar artefactos sin necesidad de interactuar directamente con los servicios de almacenamiento de objetos subyacentes:

![Mlflow tracking server](./imgs/mlflow_tracking_server.png)

Los beneficios de utilizar MLflow Tracking Server para el seguimiento remoto de experimentos incluyen:

- **Colaboración**: Varios usuarios pueden registrar ejecuciones en el mismo endpoint y consultar ejecuciones y modelos registrados por otros usuarios.
  
- **Compartición de Resultados**: El servidor de seguimiento también sirve como un punto de acceso a la UI de Tracking, donde los miembros del equipo pueden explorar fácilmente los resultados de otros.
  
- **Acceso Centralizado**: El servidor de seguimiento puede funcionar como un proxy para el acceso remoto a metadatos y artefactos, lo que facilita la seguridad y la auditoría del acceso a los datos.

Todos los contenedores que componen el *Model Registry* de Mlflow se levantan con *docker-compose*, como puede verse en la imagen:

![Contenedores que componen Mlflow, con Minio, PostgreSQL, PgAdmin y Nginx como proxy inverso](./imgs/mlflow_dockers.png)

La interfaz de Mlflow se expone en el puerto *80*, accesible desde localhost como puede verse en la imagen:

![Mlflow página principal](./imgs/mlflow_main_page.png)

En ella podemos ver los diferentes experimentos realizados y dentro de cada uno de ellos, las ejecuciones con los diferentes parámetros, modelos y técnicas de validación empleados durante el proceso de experimentación de este trabajo (descrito en el apartado 5), registrando también las métricas obtenidas en validación y el dataset empleado en validación.

También dispone de un apartado *Modelos* en el cual, aquellas ejecuciones que cumplen con las métricas esperadas pueden registrarse como modelos y cargarse de forma sencilla en el servicio en que se vayan a desplegar asegurando así un correcto versionado de los modelos como puede ocurrir en ingeniería del software con el versionado de código.

Para comparar los resultados de las distintas ejecuciones, en el apartado de *chart* y *evaluation* de los distintos experimentos configurados, se pueden realizar gráficos para comparar las distintas métricas obtenidas en evaluación para las distintas ejecuciones, además, la propia herramienta de Mlflow filtra los elementos mostrados en los gráficos seleccionando solo aquellos con mayor valor para dichas métricas, facilitando la tarea de selección de modelo:

![Mlflow chart para métrica de similitud y correción en la tarea de NL2SQL](./imgs/mlflow_chart.png)

![Mlflow evaluation nos permite ver las respuestas de los modelos ante las diferentes preguntas realizadas](./imgs/mlflow_evaluation.png)


Finalmente, en el apartado de modelos, podemos registrar aquellas ejecuciones con mejores resultados y etiquetarlas con los *aliases* para saber qué versión de cada modelo está lista para el entorno de *producción* o está en el entorno de *testing* actualmente (suponiendo un marco empresarial en el cual se dan estas dos fases antes de desplegar un modelo).

![Versionado de modelos y etiquetado en Mlflow](./imgs/mlflow_models_version.png)

![Carga de modelos desde Mlflow](./imgs/mlflow_model_load.png)


### Ray Cluster

A continuación presentamos los principales conceptos sobre Ray y su uso en el presente trabajo.

#### Conceptos Clave de Ray

- **Actores**: Son trabajadores con estado que operan de manera aislada dentro del clúster. Cada actor puede ejecutar métodos específicos y mantener un estado interno que persiste entre llamadas, lo que es ideal para servir modelos de Machine Learning. Los actores pueden gestionar modelos de forma independiente, ejecutar inferencias y mantener la carga de trabajo aislada. Además, pueden especificar sus necesidades de recursos, como CPU, GPU, u otros recursos personalizados, permitiendo a Ray distribuir eficientemente las tareas en función de la disponibilidad de recursos en el clúster.

- **Tareas**: Ray soporta la ejecución asíncrona de funciones, denominadas "tareas", que pueden distribuirse y ejecutarse en paralelo en distintos nodos del clúster. Esto es esencial para manejar cargas de trabajo intensivas en datos o procesamiento. Al igual que los actores, las tareas pueden especificar los recursos que necesitan, optimizando su distribución y ejecución en un entorno distribuido.

- **Objetos Remotos**: Las tareas y actores en Ray generan y manipulan objetos remotos, almacenados en una memoria compartida distribuida a lo largo del clúster. Esta memoria compartida facilita que los datos se mantengan accesibles y distribuidos eficientemente entre los nodos, lo que es crucial para el procesamiento paralelo y la escalabilidad del sistema.

- **Gestión de Entornos**: Ray facilita la gestión de dependencias de entorno en los nodos remotos, ya sea preparándolos previamente en el clúster o instalándolos dinámicamente a través de entornos de tiempo de ejecución. Esto permite que diferentes modelos con requerimientos distintos convivan en el mismo clúster sin conflictos.

#### Escalabilidad y Observabilidad

Ray Cluster gestiona automáticamente la escalabilidad vertical de los nodos actores, creando nuevas réplicas cuando aumenta la carga de solicitudes. El balanceo de carga entre estos nodos es manejado internamente por Ray, asegurando un escalado eficiente sin intervención manual. Además, Ray permite monitorear el uso de CPU y GPU en tiempo real, lo que es crucial para identificar posibles cuellos de botella, memory leaks, y para ajustar el uso de recursos en función de las necesidades del sistema.

Este enfoque modular y escalable, junto con la capacidad de gestionar entornos de conda de manera independiente en cada actor, convierte a Ray en una herramienta poderosa para desplegar y gestionar modelos de Machine Learning en producción, manteniendo un rendimiento óptimo y una gran flexibilidad.

Para la observabilidad, Ray Cluster permite emplear *Prometheus* y *Grafana* para monitorear la plataforma y los recursos disponibles así como permite añadir gráficas personalizadas para detectar bajadas de rendimiento por parte de los modelos y servicios desplegados.

#### Ray Cluster en nuestro proyecto

En este proyecto hemos creado una imagen de *docker* que hemos desplegado con *docker-compose* en la cual hay un nodo *Head* (nodo principal orquestador) de un cluster de Ray y en el que hemos instalado también *prometheus* y *Grafana* para monitorización.

El contenedor corriendo puede verse en la siguiente imagen:

![Contenedor de Ray](./imgs/ray_docker.png)

Si abrimos en nuestro navegador la ruta [localhost:8265/#/overview](http://localhost:8265/#/overview), podemos ver un estado general del cluster, con el uso de CPU, Disco y RAM en una gráfica generada por *grafana*, así como los *jobs* ejecutados recientemente (por ejemplo, para desplegar modelos) y en la parte de *Serve* los endpoints desplegados:

![Ray Cluster Overview](./imgs/Ray_cluster.png)


De todas las demás secciones destacan la sección de *Serve*, dónde podemos ver más detalles sobre los modelos y endpoints deplegados actualmente, en la ventana de *Cluster* podemos ver las hebras disponibles y la memoria RAM que usan (se procura que cada endpoint corra en una hebra distinta). Los actores disponibles y las métricas y ficheros de Logs tando de la plataforma en general como de cada servicio desplegado.

![Ray Serve endpoints desplegados](./imgs/ray_serve.png)

![Estado de los diferentes procesos corriendo en el cluster de Ray](./imgs/ray_cluster_status.png)

### Agentes implementados

A continuación se detallan los agentes implementados para esta solución.

#### **User Proxy Agent**

**Rol:** Este agente actúa como el intermediario principal entre el usuario y el sistema. Es responsable de gestionar la interacción con el usuario, asegurando una comunicación fluida y eficiente.

**Funcionalidad:**

- **Gestión de Interacciones:** Este agente recibe las solicitudes del usuario y las redirige al agente o proceso adecuado dentro del sistema.

- **Iniciación de Conversación:** Es el primer agente en activarse cuando se recibe una nueva tarea. Su objetivo es interpretar la solicitud inicial del usuario y dirigirla hacia el siguiente agente en la cadena de procesamiento.

- **Finalización de Conversaciones:** Monitorea las respuestas para identificar cuándo la conversación debe concluir, basándose en señales específicas como la palabra "terminate".

**Configuración:** Este agente está configurado para no requerir input humano adicional una vez que se inicia la interacción y no ejecuta código directamente. Su enfoque está en la gestión de las comunicaciones.

#### **Document Retrieval Agent (PgVectorRetrieveUserProxyAgent)**

**Rol:** Este agente es responsable de buscar y recuperar información relevante de una base de datos vectorizada que puede ser útil para responder a las consultas del usuario.

**Funcionalidad:**

- **Recuperación Basada en Embeddings:** Utiliza un modelo de embeddings para convertir las consultas del usuario en representaciones vectoriales, que luego se comparan con los vectores almacenados en la base de datos PostgreSQL.

- **Selección de Documentos:** Recupera los documentos más relevantes basándose en la similitud de vectores, lo que permite que las respuestas sean contextualmente precisas.

- **Soporte a Otros Agentes:** Proporciona la información recuperada al Planner Agent, que luego la utiliza para refinar la interpretación de la consulta del usuario.

**Configuración:** Este agente también está configurado para operar de manera autónoma, sin intervención humana, y no ejecuta código, centrando su operación en la búsqueda y recuperación de información.

#### **Planner Agent**

**Rol:** Este agente es el encargado de analizar la consulta del usuario para comprender su intención y extraer la información clave que guiará los siguientes pasos en el proceso de conversión de NL a SQL.

**Funcionalidad:**

- **Comprensión del Lenguaje Natural:** Utiliza técnicas avanzadas de comprensión del lenguaje natural (NLU) para identificar la intención del usuario y desglosar la consulta en elementos esenciales.

- **Planificación del Flujo:** Basado en la interpretación de la consulta, decide qué agentes deben activarse a continuación para completar la tarea.

- **Clarificación de Consultas:** Si es necesario, puede desambiguar o solicitar más información para asegurar que la consulta SQL generada sea precisa y relevante.

**Configuración:** Al igual que los otros agentes, opera de manera autónoma y sin necesidad de ejecutar código externo. Su principal función es la planificación y coordinación dentro del sistema.

#### **NL to SQL Agent**

**Rol:** Este agente tiene la función central en el sistema: transformar la consulta en lenguaje natural del usuario en una consulta SQL válida y optimizada.

**Funcionalidad:**

- **Conversión de Lenguaje Natural a SQL:** Analiza la intención del usuario y la estructura del esquema de la base de datos proporcionado para generar una consulta SQL que sea precisa y eficiente.

- **Optimización:** Asegura que la consulta SQL no solo sea correcta, sino también optimizada para la estructura y los índices de la base de datos, lo que es crucial para el rendimiento en entornos de producción.

- **Terminación de Tareas:** Una vez que genera la consulta SQL, el agente finaliza su tarea indicando la finalización con un mensaje de "Terminate", lo que permite al sistema cerrar el ciclo de interacción.

**Configuración:** Este agente está diseñado para funcionar completamente de manera autónoma, sin requerir entrada humana o ejecución de código externo. Su enfoque es puramente en la traducción y optimización SQL.

#### **Feedback Loop Agent**

**Rol:** El Feedback Loop Agent se encarga de evaluar la calidad de la consulta SQL generada y proporcionar retroalimentación para mejorar futuras interacciones.

**Funcionalidad:**

- **Evaluación de Consultas:** Revisa la consulta SQL generada para identificar posibles errores o áreas de mejora.

- **Retroalimentación Activa:** Ofrece sugerencias o correcciones, que pueden ser utilizadas en futuras interacciones para mejorar la precisión y eficiencia de las traducciones.

- **Cierre del Ciclo:** Si se detecta que la consulta generada es correcta, confirma el cierre de la conversación. De lo contrario, puede reiniciar el proceso para refinar la consulta.

**Configuración:** Este agente también opera de manera autónoma, ayudando a cerrar el ciclo de interacción con el usuario con una evaluación final de la consulta generada.


### Base de datos empleada en la fase de experimentación

#### Descripción de la Base de datos

La base de datos descrita es un esquema relacional que modela una red social similar a Twitter, donde los usuarios pueden crear cuentas, publicar tweets, seguir a otros usuarios, dar "me gusta" a tweets y comentar en ellos. A continuación, se describe detalladamente cada tabla y su función:

##### Tablas Principales

1. **Users**:
   - **Propósito**: Esta tabla almacena la información de los usuarios de la red social.
   - **Columnas**:
     - `user_id`: Es la clave primaria de la tabla, de tipo `SERIAL`, lo que significa que es un valor autoincremental único para cada usuario.
     - `username`: Un nombre de usuario de hasta 50 caracteres, que debe ser único y no nulo.
     - `email`: Dirección de correo electrónico de hasta 100 caracteres, que también debe ser única y no nula.
     - `password_hash`: Almacena un hash de la contraseña del usuario, de hasta 100 caracteres. No es nulo.
     - `bio`: Un campo de texto opcional que permite al usuario proporcionar una breve biografía.
     - `created_at`: Un campo `TIMESTAMP` que almacena la fecha y hora de creación del usuario, con un valor predeterminado de la hora actual (`CURRENT_TIMESTAMP`).

2. **Tweets**:
   - **Propósito**: Esta tabla almacena los tweets publicados por los usuarios.
   - **Columnas**:
     - `tweet_id`: Clave primaria, de tipo `SERIAL`.
     - `user_id`: Un campo `INTEGER` que referencia al `user_id` de la tabla `Users`, indicando quién publicó el tweet. Es una clave externa con la restricción `ON DELETE CASCADE`, lo que significa que si el usuario se elimina, también se eliminarán sus tweets.
     - `content`: Un campo de texto que almacena el contenido del tweet. Es obligatorio.
     - `created_at`: Un campo `TIMESTAMP` que almacena la fecha y hora de publicación del tweet, con un valor predeterminado de `CURRENT_TIMESTAMP`.

3. **Follows**:
   - **Propósito**: Modela las relaciones de "seguir" entre usuarios, indicando quién sigue a quién.
   - **Columnas**:
     - `follower_id`: Un `INTEGER` que referencia al `user_id` de la tabla `Users`, representando al usuario que sigue a otro. Es una clave externa con la restricción `ON DELETE CASCADE`.
     - `followee_id`: Un `INTEGER` que también referencia al `user_id` de la tabla `Users`, representando al usuario que es seguido. Es una clave externa con la misma restricción `ON DELETE CASCADE`.
     - `followed_at`: Un campo `TIMESTAMP` que almacena la fecha y hora en que se inició el seguimiento, con un valor predeterminado de `CURRENT_TIMESTAMP`.
   - **Clave primaria**: La clave primaria es compuesta por los campos `follower_id` y `followee_id`, lo que impide que un usuario siga al mismo usuario más de una vez.

4. **Likes**:
   - **Propósito**: Esta tabla registra los "me gusta" que los usuarios dan a los tweets.
   - **Columnas**:
     - `like_id`: Clave primaria, de tipo `SERIAL`.
     - `user_id`: Un `INTEGER` que referencia al `user_id` de la tabla `Users`, indicando quién dio el "me gusta". Es una clave externa con la restricción `ON DELETE CASCADE`.
     - `tweet_id`: Un `INTEGER` que referencia al `tweet_id` de la tabla `Tweets`, indicando a qué tweet se le dio "me gusta". Es una clave externa con la restricción `ON DELETE CASCADE`.
     - `liked_at`: Un campo `TIMESTAMP` que almacena la fecha y hora en que se dio "me gusta", con un valor predeterminado de `CURRENT_TIMESTAMP`.

5. **Comments**:
   - **Propósito**: Almacena los comentarios que los usuarios hacen en los tweets.
   - **Columnas**:
     - `comment_id`: Clave primaria, de tipo `SERIAL`.
     - `tweet_id`: Un `INTEGER` que referencia al `tweet_id` de la tabla `Tweets`, indicando a qué tweet pertenece el comentario. Es una clave externa con la restricción `ON DELETE CASCADE`.
     - `user_id`: Un `INTEGER` que referencia al `user_id` de la tabla `Users`, indicando quién hizo el comentario. Es una clave externa con la restricción `ON DELETE CASCADE`.
     - `content`: Un campo de texto que almacena el contenido del comentario. Es obligatorio.
     - `created_at`: Un campo `TIMESTAMP` que almacena la fecha y hora de creación del comentario, con un valor predeterminado de `CURRENT_TIMESTAMP`.

##### Datos

También se han insertado algunos datos de ejemplo para poder conocer si las consultas se han realizado con éxito. Estos datos no son reales de usuarios y se han creado exclusivamente para este trabajo.

#### Datos de evaluación

Para esta base de datos se han generado las siguientes 10 preguntas en lenguaje natural con su respectiva solución en lenguaje SQL para evaluar los modelos que empleamos en la tarea de *NL2SQL*:


\begin{longtable}{|p{6cm}|p{6cm}|}
\hline
\textbf{Descripción en lenguaje Natural} & \textbf{SQL} \\
\hline
Retrieve all users with their email addresses &
\sloppy \texttt{SELECT username,} \\
& \sloppy \texttt{email} \\
& \sloppy \texttt{FROM Users;} \\
\hline
List all tweets with their authors &
\sloppy \texttt{SELECT t.content,} \\
& \sloppy \texttt{u.username} \\
& \sloppy \texttt{FROM Tweets t} \\
& \sloppy \texttt{JOIN Users u} \\
& \sloppy \texttt{ON t.user\_id = u.user\_id;} \\
\hline
Find who user 'alice' is following &
\sloppy \texttt{SELECT u2.username} \\
& \sloppy \texttt{FROM Users u1} \\
& \sloppy \texttt{JOIN Follows f} \\
& \sloppy \texttt{ON u1.user\_id = f.follower\_id} \\
& \sloppy \texttt{JOIN Users u2} \\
& \sloppy \texttt{ON f.followee\_id = u2.user\_id} \\
& \sloppy \texttt{WHERE u1.username =} \\
& \sloppy \texttt{'alice';} \\
\hline
Count the number of followers for each user &
\sloppy \texttt{SELECT u.username,} \\
& \sloppy \texttt{COUNT(f.follower\_id)} \\
& \sloppy \texttt{AS followers\_count} \\
& \sloppy \texttt{FROM Users u} \\
& \sloppy \texttt{LEFT JOIN Follows f} \\
& \sloppy \texttt{ON u.user\_id = f.followee\_id} \\
& \sloppy \texttt{GROUP BY u.user\_id;} \\
\hline
Retrieve all tweets and their respective like counts &
\sloppy \texttt{SELECT t.content,} \\
& \sloppy \texttt{COUNT(l.like\_id)} \\
& \sloppy \texttt{AS like\_count} \\
& \sloppy \texttt{FROM Tweets t} \\
& \sloppy \texttt{LEFT JOIN Likes l} \\
& \sloppy \texttt{ON t.tweet\_id = l.tweet\_id} \\
& \sloppy \texttt{GROUP BY t.tweet\_id;} \\
\hline
Find all comments for the tweet 1 &
\sloppy \texttt{SELECT c.content,} \\
& \sloppy \texttt{u.username} \\
& \sloppy \texttt{FROM Comments c} \\
& \sloppy \texttt{JOIN Users u} \\
& \sloppy \texttt{ON c.user\_id = u.user\_id} \\
& \sloppy \texttt{WHERE c.tweet\_id = 1;} \\
\hline
List users who liked tweets posted by 'alice' &
\sloppy \texttt{SELECT DISTINCT} \\
& \sloppy \texttt{u.username} \\
& \sloppy \texttt{FROM Likes l} \\
& \sloppy \texttt{JOIN Tweets t} \\
& \sloppy \texttt{ON l.tweet\_id = t.tweet\_id} \\
& \sloppy \texttt{JOIN Users u} \\
& \sloppy \texttt{ON l.user\_id = u.user\_id} \\
& \sloppy \texttt{WHERE t.user\_id =} \\
& \sloppy \texttt{(SELECT user\_id FROM} \\
& \sloppy \texttt{Users WHERE} \\
& \sloppy \texttt{username = 'alice');} \\
\hline
Find the tweet with the most comments &
\sloppy \texttt{SELECT t.content,} \\
& \sloppy \texttt{COUNT(c.comment\_id)} \\
& \sloppy \texttt{AS comments\_count} \\
& \sloppy \texttt{FROM Tweets t} \\
& \sloppy \texttt{LEFT JOIN Comments c} \\
& \sloppy \texttt{ON t.tweet\_id = c.tweet\_id} \\
& \sloppy \texttt{GROUP BY t.tweet\_id} \\
& \sloppy \texttt{ORDER BY comments\_count} \\
& \sloppy \texttt{DESC LIMIT 1;} \\
\hline
Retrieve users who have never posted a tweet &
\sloppy \texttt{SELECT u.username} \\
& \sloppy \texttt{FROM Users u} \\
& \sloppy \texttt{LEFT JOIN Tweets t} \\
& \sloppy \texttt{ON u.user\_id = t.user\_id} \\
& \sloppy \texttt{WHERE t.tweet\_id IS} \\
& \sloppy \texttt{NULL;} \\
\hline
List tweets liked by users who follow 'alice' &
\sloppy \texttt{SELECT DISTINCT} \\
& \sloppy \texttt{t.content} \\
& \sloppy \texttt{FROM Tweets t} \\
& \sloppy \texttt{JOIN Likes l} \\
& \sloppy \texttt{ON t.tweet\_id = l.tweet\_id} \\
& \sloppy \texttt{JOIN Follows f} \\
& \sloppy \texttt{ON l.user\_id = f.follower\_id} \\
& \sloppy \texttt{WHERE f.followee\_id =} \\
& \sloppy \texttt{(SELECT user\_id FROM} \\
& \sloppy \texttt{Users WHERE} \\
& \sloppy \texttt{username = 'alice');} \\
\hline
\end{longtable}

Estas sentencias han sido especialmente pensadas y diseñadas empezando por una consulta sencilla y gradualmente añadir complejidad a las *queries* incluyendo *Joins*, filtros complejos y relaciones entre varias tablas de la base de datos. Esto proporciona un conjunto adecuado para validar los modelos durante la fase de experimentación.

### Fase de experimentación detallada

#### Experimentación para elección de modelos y técnicas de embeddings

Como se explica en el apartado de [Pruebas y Validación](#5-pruebas-y-validación), se realiza un experimento en el cual se prueban distintos modelos de embeddings ofrecidos por OpenAI así como los modelos GPT-4o y GPT-3.5-Turbo para la tarea de NL2SQL.

Para los GPT encargados de NL2SQl usamos el siguiente system message:

```
You are an AI assistant specialized in translating 
natural language questions into SQL queries. 
Given a description of the data and a natural language question, 
generate the corresponding SQL query.
```

Asignándoles así el role de expertos en SQl que tienen que transformar preguntas del usuario en sentencias SQL.

Posteriormente, mediante un *RAG* se obtienen los vectores del documento *PDF* que describe la base de datos que usamos (en nuestro caso la de [Social Network](#base-de-datos-empleada-en-la-fase-de-experimentación)) con el modelo de embedding elegido y la estrategia de partición en *chunks* elegida, y se le pide que genere la sentencia SQL pertinente usando el siguiente prompt:

```
    Based on the embeddings in {table},
    generate the SQL query to answer: {query_description}.
    Please provide only the SQL code enclosed within 
    ```sql...``` characters.
    Context: {' '.join(related_texts)}
```
En el cual le aportamos la descripción de la sentencia en `query_description` y todos los vectores relacionados en `related_texts`.

Para determinar el éxito en la consulta generada, comparamos el resultado obtenido con el de la tabla que aparece en el apartado  de [Datos de evaluación](#datos-de-evaluación) usamos dos métricas. Primero usamos la medida proporcionada por la librería *FuzzyWuzzy* para medir la similitud entre ambas sentencias y además comprobamos el resultado obtenido por ambas queries. Si el resultado es idéntico contamos como éxito (1) si el resultado no coincide, pedimos al modelo *GPT-4o* que analice las respuestas ante ambas sentencias (la generada y la correcta) y nos diga si son iguales, para contar como éxitos esos casos en los que realmente se responde a la pregunta pero el modelo añade información *extra* a la esperada, porque esto no es un error.

El fragmento de código para esto es el siguiente:

   ```py
    # Compare results
        result_coincidence = 1 if expected_result == generated_result else 0

        if not result_coincidence:
            prompt = f"""
            Given the following query description: {description}.
            Two SQL queries were provided:
            - Expected SQL: {expected_sql}
            - Generated SQL: {generated_sql}

            Can we find the information of expected result in generated result ? 
            No matters if we find extra info in generated_result
            - Expected Result:\n{str(expected_result)}
            - Generated Result:\n{str(generated_result)}
            """

            gpt_response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert SQL analyst. \
                        Just respond 'yes' or 'no'"},
                    {"role": "user", "content": prompt}
                ]
            )

            # Check if GPT-4 considers them similar in meaning
            gpt_result = gpt_response.choices[0].message.content
            result_coincidence = 1 if "yes" in gpt_result.lower() else 0
   ```


Con todos estos parámetros en cuenta, la configuración ganadora fue el *Run* de *Mlflow* denominado *polite-fox-990*, que empleó **GPT-4o** utilizando un chunksize de **1536** y la estrategia de segmentación **fixed**. Este modelo logró un excelente desempeño, con una similitud promedio de 84.6 y un 80% de *accuracy* en las consultas SQL generadas. Además se determina que la mejor estrategia de partición en chunks es la *Fixed* y el mejor modelo para embeddings el *text-embedding-3-large* con un chunksize de 1536. A continuación podemos ver los resultados obtenidos con detalle:

![Resultados del mejor modelo de la fase de evaluación](./imgs/evaluation_result_exp.png)

Como podemos ver, hay una gran similitud en general entre la sentencia SQL generada y la esperada, pero hay algunas diferencias en las respuestas que generan, que gracias a la forma en la que evaluamos su precisión podemos determinar si realmente coinciden en intención.

#### Modelo final con el flujo de agentes implementado

Una vez se desarrolla el flujo de agentes como se describe en el punto [Desarrollo del sistema de agentes NL2NSQL](#4-desarrollo-del-sistema-de-agentes-nl2sql) se registra un *Run* en Mlflow para comparar el rendimiento con los resultados obtenidos en la fase anterior, obteniendo una mejoría en el *Accuracy* de las sentencias, como puede verse en los siguientes resultados:

![Resultado del chat de agentes en evaluación](./imgs/evaluation_result_agentes.png)

Como vemos, solo falla en un caso, frente a los 3 errores del mejor modelo en la fase previa. Además la similitud se mantiene elevada para cada consulta. Vemos como el flujo de agentes hace que la calidad de los resultados mejore y se obtengan consultas de mayor calidad comprendiendo la intención del ususario.


### Detalles de la interfaz de ususario

La interfaz fue desarrollada utilizando el framework Gradio, lo que facilita la creación de interfaces web interactivas para aplicaciones de machine learning. La comunicación con el backend se realiza mediante solicitudes HTTP, enviando los documentos cargados y las consultas ingresadas a un servidor que ejecuta el procesamiento a través de agentes NL2SQL. La respuesta del backend se muestra en tiempo real, proporcionando una experiencia de usuario fluida e intuitiva para la generación y validación de consultas SQL a partir de lenguaje natural.

Este diseño permite a los usuarios interactuar con el sistema de manera sencilla, ofreciendo una experiencia rica y efectiva para la generación y validación de consultas SQL a partir de lenguaje natural.

![Ejemplo de chat de agentes](./imgs/UI_test.png)

Se puede ver cómo el agente planner recupera el contexto con RAG y cómo el agente de Feedback proporciona mejoras a la consulta que se ha propuesto como primera opción, refinándola hasta devolver la correcta.

También dispone la interfaz gráfica de una sección para ejecutar sentencias SQL contra la base de datos que estamos analizando, para poder probar las respuestas devueltas por los agentes, para ello podemos seleccionar de entre las bases de datos disponibles con el menú desplegable cuál será el objetivo de la query, finalmente ejecutamos con el botón *Execute Query*:

![Interfaz para ejecutar sentencias SQl](./imgs/frontend_2.png)

Finalmente tenemos la interfaz para subir documentos a nuestra base de datos vectorial en PostgreSQL, en ella por un lado elegimos el documento PDF a procesar y por otro lado seleccionamos el valor para el parámetro *database* de la tabla con vectores, este parámetro nos permite mejorar el RAG filtrando vectores por dicho parámetro:

![Interfaz para subir documentos PDF](./imgs/frontend_1.png)


Este servicio también se encuentra en un contenedor de *docker* en la misma red interna junto con los contenedores de Ray y PostgreSQL para la correcta comunicación entre ellos.
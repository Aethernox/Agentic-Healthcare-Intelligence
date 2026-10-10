# Databricks notebook source
# MAGIC %md
# MAGIC # MedMap — Step 3: Embedding & Mosaic AI Vector Search Indexing
# MAGIC Generate embeddings and index into Databricks Vector Search

# COMMAND ----------

import mlflow
import json
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, udf
from pyspark.sql.types import StringType, StructType, StructField, FloatType, ArrayType

spark = SparkSession.builder.getOrCreate()

# COMMAND ----------

OPENAI_API_KEY = dbutils.secrets.get(scope="medmap", key="openai_api_key")
DATABRICKS_HOST = spark.conf.get("spark.databricks.workspaceUrl")
DATABRICKS_TOKEN = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

VECTOR_SEARCH_ENDPOINT = "medmap-endpoint"
INDEX_NAME = "medmap.hospitals.embeddings"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Parse Extracted JSON

# COMMAND ----------

raw_extracted = spark.table("medmap.extracted.hospitals_json")

def parse_extracted(json_str: str) -> dict:
    try:
        return json.loads(json_str)
    except Exception:
        return {}

def build_embedding_text(row: dict) -> str:
    """Build rich text representation for embedding."""
    parts = []
    if row.get("name"): parts.append(f"Hospital: {row['name']}")
    if row.get("city"): parts.append(f"City: {row['city']}")
    if row.get("district"): parts.append(f"District: {row['district']}")
    if row.get("state"): parts.append(f"State: {row['state']}")

    caps = row.get("capabilities", {}) or {}
    active = [k.replace("_", " ").title() for k, v in caps.items() if v is True]
    if active: parts.append(f"Capabilities: {', '.join(active)}")

    if row.get("staff_specialties"): parts.append(f"Staff: {', '.join(row['staff_specialties'])}")
    if row.get("bed_count"): parts.append(f"Beds: {row['bed_count']}")
    if row.get("accreditation"): parts.append(f"Accreditation: {row['accreditation']}")

    return " | ".join(parts)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Generate Embeddings (OpenAI text-embedding-3-small)

# COMMAND ----------

from openai import OpenAI
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def embed_batch(texts: list[str], batch_size: int = 100) -> list[list[float]]:
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        response = openai_client.embeddings.create(model="text-embedding-3-small", input=batch)
        all_embeddings.extend([item.embedding for item in response.data])
        print(f"Embedded {min(i+batch_size, len(texts))}/{len(texts)}")
    return all_embeddings

with mlflow.start_run(run_name="embedding-generation"):
    mlflow.log_param("embedding_model", "text-embedding-3-small")

    extracted_pdf = raw_extracted.toPandas()
    records = [json.loads(r) for r in extracted_pdf["extracted_json"]]
    texts = [build_embedding_text(r) for r in records]

    embeddings = embed_batch(texts)
    mlflow.log_metric("records_embedded", len(embeddings))
    print(f"✅ Generated {len(embeddings)} embeddings (dim={len(embeddings[0])})")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Index into Mosaic AI Vector Search

# COMMAND ----------

from databricks.vector_search.client import VectorSearchClient

vs_client = VectorSearchClient(
    workspace_url=f"https://{DATABRICKS_HOST}",
    personal_access_token=DATABRICKS_TOKEN,
)

# Create endpoint if not exists
try:
    vs_client.create_endpoint(name=VECTOR_SEARCH_ENDPOINT, endpoint_type="STANDARD")
    print(f"Created endpoint: {VECTOR_SEARCH_ENDPOINT}")
except Exception:
    print(f"Endpoint {VECTOR_SEARCH_ENDPOINT} already exists")

# Create index
try:
    vs_client.create_direct_access_index(
        endpoint_name=VECTOR_SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        primary_key="id",
        embedding_dimension=1536,
        embedding_vector_column="embedding",
        schema={
            "id": "int",
            "name": "string",
            "city": "string",
            "state": "string",
            "pin_code": "string",
            "trust_score": "int",
            "raw_text": "string",
            "embedding": "array<float>",
        },
    )
    print(f"Created index: {INDEX_NAME}")
except Exception:
    print(f"Index {INDEX_NAME} already exists")

# COMMAND ----------

# Upsert data
index = vs_client.get_index(VECTOR_SEARCH_ENDPOINT, INDEX_NAME)

upsert_data = []
for i, (record, embedding) in enumerate(zip(records, embeddings)):
    upsert_data.append({
        "id": extracted_pdf.iloc[i]["record_id"],
        "name": record.get("name", ""),
        "city": record.get("city", ""),
        "state": record.get("state", ""),
        "pin_code": record.get("pin_code", ""),
        "trust_score": 0,  # Will be updated after trust scoring
        "raw_text": texts[i][:1000],
        "embedding": embedding,
    })

CHUNK_SIZE = 1000
for i in range(0, len(upsert_data), CHUNK_SIZE):
    chunk = upsert_data[i:i+CHUNK_SIZE]
    index.upsert(chunk)
    print(f"Indexed {min(i+CHUNK_SIZE, len(upsert_data))}/{len(upsert_data)}")

print(f"✅ Indexed {len(upsert_data):,} records into Mosaic AI Vector Search")

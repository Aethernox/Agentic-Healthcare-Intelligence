"""
Step 3 — Embedding Pipeline
Generates text embeddings for all hospital records using OpenAI or Databricks.
"""
import logging
from typing import List, Optional
import numpy as np

from config import settings

logger = logging.getLogger(__name__)


def build_embedding_text(hospital: dict) -> str:
    """
    Construct a rich text representation of a hospital for embedding.
    Combines structured fields with raw text for semantic richness.
    """
    parts = []

    if hospital.get("name"):
        parts.append(f"Hospital: {hospital['name']}")
    if hospital.get("city"):
        parts.append(f"Location: {hospital['city']}, {hospital.get('state', '')}")
    if hospital.get("district"):
        parts.append(f"District: {hospital['district']}")

    caps = hospital.get("capabilities", {})
    active_caps = [k.replace("_", " ").title() for k, v in caps.items() if v is True]
    if active_caps:
        parts.append(f"Capabilities: {', '.join(active_caps)}")

    if hospital.get("staff_specialties"):
        parts.append(f"Staff: {', '.join(hospital['staff_specialties'])}")

    if hospital.get("bed_count"):
        parts.append(f"Beds: {hospital['bed_count']}")

    if hospital.get("accreditation"):
        parts.append(f"Accreditation: {hospital['accreditation']}")

    if hospital.get("raw_text"):
        parts.append(hospital["raw_text"][:500])

    return " | ".join(parts)


async def generate_embeddings(
    texts: List[str],
    model: str = "text-embedding-3-small",
    batch_size: int = 100,
) -> List[List[float]]:
    """
    Generate embeddings using OpenAI's embedding API.
    Returns list of embedding vectors.
    """
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.anthropic_api_key)  # Use openai key

        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i: i + batch_size]
            response = await client.embeddings.create(model=model, input=batch)
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            logger.info(f"Embedded {min(i + batch_size, len(texts))}/{len(texts)} records")

        return all_embeddings

    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        # Return zero vectors as fallback
        return [[0.0] * 1536 for _ in texts]


async def index_to_vector_search(
    hospitals: List[dict],
    embeddings: List[List[float]],
) -> bool:
    """
    Index hospital records + embeddings into Databricks Mosaic AI Vector Search.
    """
    try:
        from databricks.vector_search.client import VectorSearchClient

        client = VectorSearchClient(
            workspace_url=settings.databricks_host,
            personal_access_token=settings.databricks_token,
        )

        index = client.get_index(
            endpoint_name=settings.vector_search_endpoint,
            index_name=settings.vector_search_index,
        )

        data = []
        for hospital, embedding in zip(hospitals, embeddings):
            data.append({
                "id": hospital["id"],
                "name": hospital.get("name", ""),
                "city": hospital.get("city", ""),
                "state": hospital.get("state", ""),
                "pin_code": hospital.get("pin_code", ""),
                "trust_score": hospital.get("trust_score", 0),
                "embedding": embedding,
                "raw_text": hospital.get("raw_text", "")[:1000],
            })

        index.upsert(data)
        logger.info(f"Indexed {len(data)} records into Mosaic AI Vector Search")
        return True

    except ImportError:
        logger.warning("Databricks SDK not available — skipping vector index")
        return False
    except Exception as e:
        logger.error(f"Vector index failed: {e}")
        return False

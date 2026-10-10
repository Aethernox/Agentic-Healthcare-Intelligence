"""
Mosaic AI Vector Search tool for semantic retrieval over hospital records.
"""
import logging
from typing import List, Optional

from config import settings

logger = logging.getLogger(__name__)


async def semantic_search(
    query: str,
    top_k: int = 20,
    filters: Optional[dict] = None,
) -> List[dict]:
    """
    Perform semantic search over the Mosaic AI Vector Index.
    Returns list of matching hospital records with scores.
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

        results = index.similarity_search(
            query_text=query,
            columns=["id", "name", "city", "state", "pin_code", "raw_text", "trust_score"],
            num_results=top_k,
            filters=filters,
        )

        return results.get("result", {}).get("data_array", [])

    except ImportError:
        logger.warning("Databricks SDK not available — using mock results")
        return _mock_search_results(query, top_k)
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        return []


def _mock_search_results(query: str, top_k: int) -> List[dict]:
    """Mock results for local development without Databricks."""
    return [
        {
            "id": i + 1,
            "name": f"Mock Hospital {i + 1}",
            "city": "Patna",
            "state": "Bihar",
            "pin_code": "800001",
            "score": 0.95 - (i * 0.05),
        }
        for i in range(min(top_k, 5))
    ]

"""
Tavily web verification tool — triggered for low-trust hospital records.
"""
import logging
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)


async def verify_hospital_with_tavily(
    hospital_name: str,
    city: str,
    claimed_specialty: str,
    tavily_client=None,
) -> tuple[Optional[str], int]:
    """
    Search the web to verify hospital claims.
    Returns (summary, score_adjustment).
    """
    try:
        from tavily import AsyncTavilyClient

        if tavily_client is None:
            if not settings.tavily_api_key:
                logger.warning("No Tavily API key configured")
                return None, 0
            tavily_client = AsyncTavilyClient(api_key=settings.tavily_api_key)

        queries = [
            f"{hospital_name} {city} {claimed_specialty}",
            f"{hospital_name} {city} hospital review",
            f"{hospital_name} accreditation NABH",
        ]

        all_results = []
        for query in queries[:2]:  # Limit to 2 queries per hospital
            result = await tavily_client.search(
                query=query,
                search_depth="basic",
                max_results=3,
            )
            if result.get("results"):
                all_results.extend(result["results"])

        if not all_results:
            return "No web evidence found — claims unverifiable", -5

        # Analyze results
        positive_signals = ["hospital", "medical", "clinic", "care", "health", claimed_specialty.lower()]
        negative_signals = ["closed", "shut", "defunct", "fraud", "fake"]

        content_text = " ".join(r.get("content", "") for r in all_results).lower()

        positive_hits = sum(1 for s in positive_signals if s in content_text)
        negative_hits = sum(1 for s in negative_signals if s in content_text)

        if negative_hits > 0:
            adjustment = -15
            summary = f"Web search found concerning signals for {hospital_name}. Recommend caution."
        elif positive_hits >= 3:
            adjustment = +15
            summary = f"Web search confirms {hospital_name} is an active medical facility with {claimed_specialty} services. Evidence found across {len(all_results)} sources."
        else:
            adjustment = 0
            summary = f"Limited web evidence for {hospital_name}. Some operational signals found but specialty claims not fully confirmed."

        logger.info(f"Tavily verification for '{hospital_name}': adjustment={adjustment:+d}")
        return summary, adjustment

    except ImportError:
        logger.error("tavily-python not installed. Run: pip install tavily-python")
        return None, 0
    except Exception as e:
        logger.error(f"Tavily search failed for '{hospital_name}': {e}")
        return None, 0

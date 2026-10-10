"""
Tavily web verification tool.
Called for hospitals with trust_score < threshold to fetch current web evidence.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def verify_hospital(
    name: str,
    city: str,
    state: str,
    tavily_api_key: str,
    claims: Optional[list[str]] = None,
) -> dict:
    """
    Search the web for evidence about a hospital. Returns a summary and confidence signal.
    """
    if not tavily_api_key:
        logger.warning("Tavily API key not set — skipping web verification")
        return {"verified": False, "summary": None, "score_adjustment": 0}

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=tavily_api_key)

        claim_text = ""
        if claims:
            claim_text = f" Verify claims: {', '.join(claims[:3])}"

        query = f"{name} hospital {city} {state} India accreditation facilities{claim_text}"

        response = client.search(
            query=query,
            search_depth="basic",
            max_results=5,
            include_answer=True,
        )

        answer = response.get("answer", "")
        results = response.get("results", [])

        snippets = []
        for r in results[:3]:
            if r.get("content"):
                snippets.append(r["content"][:300])

        combined = answer or " ".join(snippets)
        if not combined:
            return {"verified": False, "summary": None, "score_adjustment": 0}

        summary = combined[:500]

        # Heuristic: if web results mention the hospital positively, add points
        positive_terms = ["accredited", "nabh", "operational", "government", "verified", "confirmed"]
        negative_terms = ["closed", "defunct", "fake", "unverified", "shutdown"]
        score_adj = 0
        lower = summary.lower()
        if any(t in lower for t in positive_terms):
            score_adj = 10
        if any(t in lower for t in negative_terms):
            score_adj = -15

        logger.info(f"Tavily verified '{name}': adjustment={score_adj:+d}")
        return {
            "verified": True,
            "summary": summary,
            "score_adjustment": score_adj,
        }

    except Exception as e:
        logger.error(f"Tavily verification failed for '{name}': {e}")
        return {"verified": False, "summary": None, "score_adjustment": 0}

"""
Agents package — lazy imports to avoid hard-crashing when optional
dependencies (anthropic, langchain) are not installed.
"""

from .trust_scorer import compute_trust_score, get_trust_tier, should_trigger_tavily

__all__ = [
    "compute_trust_score",
    "get_trust_tier",
    "should_trigger_tavily",
]


def _lazy_import():
    from .extractor import extract_hospital_record, batch_extract
    from .reasoner import run_search_agent, build_agent
    try:
        from .validator import validate_recommendations
    except ImportError:
        pass
    return locals()

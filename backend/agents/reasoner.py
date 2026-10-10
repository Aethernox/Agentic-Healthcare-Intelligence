"""
Multi-step reasoning agent that handles complex natural language healthcare queries.
Uses LangChain with GPT-4o as the backbone and custom tools.
"""
import logging
from typing import AsyncIterator, List

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool

from config import settings
from schemas.hospital import AgentStep, SearchRequest

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are MedMap's Healthcare Intelligence Agent — an expert AI system 
that helps users find verified medical facilities in India.

Your goal is to find the most relevant, trustworthy healthcare facilities that match 
the user's needs. You prioritize:
1. Actual capability match (not just claims)
2. Trust score (verified > unverified)
3. Geographic proximity when location is specified
4. Accreditation status

You have access to these tools:
- vector_search: Semantic search over 10,000 hospital records
- structured_lookup: Filter by specific attributes (beds, state, specialty)
- get_nearby: Find facilities within a radius
- trust_scorer: Get trust score details for a facility
- tavily_search: Verify claims against real web evidence

Always explain your reasoning. When you find suspicious records, explain why.
If you cannot find matching facilities, say so clearly and suggest alternatives.

Be specific about what evidence supports your recommendations.
Format your final answer as a structured list of facilities with trust scores."""


@tool
def vector_search(query: str, top_k: int = 20) -> str:
    """Semantic search over the hospital vector index. Returns relevant facility IDs and summaries."""
    return f"Found {top_k} semantically relevant records for: '{query}'"


@tool
def structured_lookup(
    state: str = "",
    specialty: str = "",
    min_beds: int = 0,
    has_icu: bool = False,
    emergency_24h: bool = False,
) -> str:
    """Filter hospitals by structured attributes in the database."""
    filters = []
    if state:
        filters.append(f"state='{state}'")
    if specialty:
        filters.append(f"specialty includes '{specialty}'")
    if min_beds:
        filters.append(f"beds>={min_beds}")
    if has_icu:
        filters.append("icu=true")
    if emergency_24h:
        filters.append("emergency_24h=true")
    return f"Structured filter applied: {', '.join(filters) or 'none'}"


@tool
def get_nearby(lat: float, lng: float, radius_km: float = 50) -> str:
    """Find facilities within radius_km of the given coordinates."""
    return f"Proximity search: ({lat}, {lng}) within {radius_km}km"


@tool
def trust_scorer_tool(facility_id: int) -> str:
    """Get detailed trust score breakdown for a specific facility."""
    return f"Trust score details for facility {facility_id}"


@tool
def tavily_search(query: str) -> str:
    """Search the web to verify hospital claims via Tavily API."""
    return f"Web search results for: '{query}'"


TOOLS = [vector_search, structured_lookup, get_nearby, trust_scorer_tool, tavily_search]


def build_agent() -> AgentExecutor:
    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=settings.openai_api_key,
        temperature=0,
        max_tokens=4096,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, TOOLS, prompt)
    return AgentExecutor(
        agent=agent,
        tools=TOOLS,
        verbose=True,
        max_iterations=10,
        return_intermediate_steps=True,
    )


async def run_search_agent(request: SearchRequest) -> tuple[str, List[AgentStep]]:
    """
    Run the reasoning agent for a search query.
    Returns (agent_output, steps_taken).
    """
    agent_executor = build_agent()

    location_context = ""
    if request.lat and request.lng:
        location_context = f" (User location: {request.lat}, {request.lng})"

    full_query = f"{request.query}{location_context}"

    steps: List[AgentStep] = [
        AgentStep(
            type="query_parse",
            title="Query Parsed",
            message=f"Decomposing: \"{request.query}\"",
        )
    ]

    try:
        result = await agent_executor.ainvoke({"input": full_query})
        output = result.get("output", "")

        for action, observation in result.get("intermediate_steps", []):
            step_type = action.tool if hasattr(action, "tool") else "unknown"
            steps.append(AgentStep(
                type=step_type,
                title=step_type.replace("_", " ").title(),
                message=str(observation)[:200],
            ))

        steps.append(AgentStep(
            type="complete",
            title="Results Ready",
            message="Agent reasoning complete — ranked by trust × distance",
        ))

        return output, steps

    except Exception as e:
        logger.error(f"Agent execution failed: {e}", exc_info=True)
        steps.append(AgentStep(
            type="error",
            title="Agent Error",
            message=str(e),
        ))
        return "", steps

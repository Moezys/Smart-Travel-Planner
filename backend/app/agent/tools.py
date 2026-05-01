"""LangGraph tool definitions for the travel-planning agent.

Three tools, each with a Pydantic input schema validated before the
function body runs.  If the LLM passes garbage the schema raises a
ValidationError which LangGraph surfaces as a ToolMessage error — the
model then retries with corrected arguments rather than crashing.

Tool allowlist is enforced in graph.py: only these three names may be
invoked.  Any other name the model invents is blocked there.
"""

from __future__ import annotations

from typing import Literal, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.db import session_scope
from app.services.classifier import classify_destination
from app.services.rag import retrieve
from app.services.weather import get_weather as _get_weather

# --------------------------------------------------------------------------- #
# Schemas                                                                      #
# --------------------------------------------------------------------------- #

_ARCHETYPES = Literal[
    "Adventure", "Budget", "Culture", "Family", "Luxury", "Relaxation"
]


class RagSearchInput(BaseModel):
    query: str = Field(
        description=(
            "Natural-language travel query. Be descriptive about the "
            "travel style, activities, and atmosphere the user wants."
        )
    )
    archetype_filter: Optional[_ARCHETYPES] = Field(
        default=None,
        description=(
            "Optional travel-style filter. When you already know the "
            "user's style, set this to narrow results to matching "
            "destinations. Leave null to search the full corpus."
        ),
    )


class ClassifyDestinationInput(BaseModel):
    destination_name: str = Field(
        description=(
            "Name of the destination to classify, e.g. 'Kyoto', 'Rome', "
            "'Banff'. Use a well-known city or park name."
        )
    )


class GetWeatherInput(BaseModel):
    city: str = Field(description="City name, e.g. 'Reykjavik', 'Dubai'.")
    country_code: str = Field(
        description=(
            "ISO 3166-1 alpha-2 country code, e.g. 'IS' for Iceland, "
            "'AE' for UAE, 'JP' for Japan."
        )
    )


# --------------------------------------------------------------------------- #
# Tool implementations                                                         #
# --------------------------------------------------------------------------- #

@tool("rag_search", args_schema=RagSearchInput)
async def rag_search(query: str, archetype_filter: Optional[str] = None) -> str:
    """Search the destination knowledge base for travel-style information.

    Returns the top-5 most relevant chunks from Wikivoyage content about
    destinations that match the query.  Use this to learn what each
    destination is actually like before recommending it.
    """
    async with session_scope() as session:
        hits = await retrieve(session, query, k=5, archetype_filter=archetype_filter)

    if not hits:
        return "No relevant destination information found for that query."

    parts: list[str] = []
    for h in hits:
        snippet = h.text[:300].replace("\n", " ")
        parts.append(
            f"[{h.destination}, {h.country} | {h.archetype} | "
            f"sim={h.similarity:.2f}]\n{snippet}"
        )
    return "\n\n---\n\n".join(parts)


@tool("classify_destination", args_schema=ClassifyDestinationInput)
def classify_destination_tool(destination_name: str) -> str:
    """Classify a destination's travel style using the trained ML model.

    Returns the predicted travel style (Adventure / Budget / Culture /
    Family / Luxury / Relaxation) and per-class probabilities.  Use this
    to validate or cross-check what style a destination primarily serves.
    """
    try:
        result = classify_destination(destination_name)
    except ValueError as exc:
        return f"Classification failed: {exc}"

    prob_str = ", ".join(
        f"{k}: {v:.0%}" for k, v in sorted(
            result.probabilities.items(), key=lambda x: x[1], reverse=True
        )
    )
    return (
        f"Destination: {result.destination} "
        f"(matched dataset row: {result.matched_row})\n"
        f"Predicted travel style: {result.predicted_style}\n"
        f"Probabilities: {prob_str}"
    )


@tool("get_weather", args_schema=GetWeatherInput)
async def get_weather(city: str, country_code: str) -> str:
    """Get current weather conditions and 7-day forecast for a destination.

    Returns temperature, weather condition, wind speed, and a daily
    forecast.  Use this to advise on the best time to visit or warn about
    current conditions.
    """
    try:
        result = await _get_weather(city, country_code)
    except ValueError as exc:
        return f"Weather lookup failed: {exc}"
    except Exception as exc:  # noqa: BLE001
        return f"Weather service error: {exc}"
    return result.summary()


# --------------------------------------------------------------------------- #
# Exported list (used by graph.py)                                             #
# --------------------------------------------------------------------------- #

AGENT_TOOLS = [rag_search, classify_destination_tool, get_weather]
TOOL_ALLOWLIST: frozenset[str] = frozenset(t.name for t in AGENT_TOOLS)

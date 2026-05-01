"""LangGraph two-model ReAct agent for travel planning.

Model routing
-------------
Cheap model  (agent_cheap_model, e.g. gemma-3-4b-it)
    All tool-selection rounds: decides which tools to call, extracts
    arguments, rewrites RAG queries.  This is mechanical, structured work
    that a small model handles well and cheaply.

Strong model  (agent_model, e.g. gemma-4-31b-it)
    Final synthesis only: called exactly once, after all tool results are
    in, to write the actual travel recommendation.  Given the full
    conversation context it can genuinely synthesise across tools.

Graph structure
---------------
    ┌───────────────────┐ tool calls  ┌────────────┐
    │  tool_selection   │────────────►│ allowlist  │
    │  (cheap model)    │◄────────────│  + tools   │
    └────────┬──────────┘ tool results└────────────┘
             │ no tool calls
             ▼
    ┌───────────────────┐
    │    synthesis      │
    │  (strong model)   │──► END
    └───────────────────┘

Token usage
-----------
Every node accumulates token counts in ``state["token_usage"]``.
``run_agent`` returns the final answer and the usage dict so callers can
log cost.  Typical Google AI pricing for Gemma:
    gemma-3-4b-it  : ~$0.03 / 1M input tokens, ~$0.06 / 1M output tokens
    gemma-4-31b-it : ~$0.14 / 1M input tokens, ~$0.28 / 1M output tokens
(Verify current rates at https://ai.google.dev/pricing)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import Annotated, TypedDict

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools import AGENT_TOOLS, TOOL_ALLOWLIST
from app.config import get_settings

# --------------------------------------------------------------------------- #
# LangSmith — inject env vars from Settings so the SDK auto-enables tracing   #
# --------------------------------------------------------------------------- #

def _configure_tracing() -> None:
    s = get_settings()
    key = s.langsmith_api_key.get_secret_value()
    if key:
        os.environ.setdefault("LANGSMITH_API_KEY", key)
    if s.langchain_tracing_v2:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ.setdefault("LANGCHAIN_PROJECT", s.langchain_project)


_configure_tracing()

# --------------------------------------------------------------------------- #
# System prompts                                                               #
# --------------------------------------------------------------------------- #

# Cheap model: focus on mechanical tool orchestration only.
_TOOL_SELECTION_PROMPT = """\
You are a travel research orchestrator. Your ONLY job is to call the right \
tools to collect information about destinations.

Available tools:
- rag_search       : search destination knowledge base (Wikivoyage content).
- classify_destination : predict a destination's travel style with the ML model.
- get_weather      : fetch current conditions and 7-day forecast.

Rules:
1. Call tools to gather information — do NOT write the final recommendation.
2. Write precise, descriptive tool arguments. For rag_search, make the query \
specific about activities, vibe, and travel style.
3. When you have enough data from all relevant tools, stop calling tools and \
output a brief note like "Research complete." — the synthesis step will do \
the rest.
4. Maximum 8 tool calls total. Do not repeat the same query twice.
"""

# Strong model: synthesis only, no tools.
_SYNTHESIS_PROMPT = """\
You are an expert travel advisor. A research phase has gathered data from \
three sources:
  • rag_search       — Wikivoyage destination knowledge
  • classify_destination — ML travel-style prediction
  • get_weather      — current conditions and 7-day forecast

Your job is to synthesise all of that data into a specific, honest, \
actionable travel recommendation.

Guidelines:
- Quote concrete details from the tool results (temperatures, place names, \
activities). Do not give generic advice.
- If the weather or ML classification contradicts the vibe described in RAG \
results, address the tension explicitly.
- Be direct about budget fit, timing risks, and what "not too touristy" \
actually means for each destination.
- Structure: short recommendation, then destination-specific sections, then \
practical note.
"""

# --------------------------------------------------------------------------- #
# State                                                                        #
# --------------------------------------------------------------------------- #

MAX_TOOL_ROUNDS = 6


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    # Cumulative token counts — each node reads + overwrites this field.
    token_usage: dict  # keys: cheap_in, cheap_out, strong_in, strong_out
    # How many tool-selection rounds have completed.
    tool_rounds: int


@dataclass
class TokenUsage:
    cheap_in: int = 0
    cheap_out: int = 0
    strong_in: int = 0
    strong_out: int = 0

    def total_in(self) -> int:
        return self.cheap_in + self.strong_in

    def total_out(self) -> int:
        return self.cheap_out + self.strong_out

    def as_dict(self) -> dict:
        return {
            "cheap_in": self.cheap_in,
            "cheap_out": self.cheap_out,
            "strong_in": self.strong_in,
            "strong_out": self.strong_out,
            "total_in": self.total_in(),
            "total_out": self.total_out(),
        }


def _extract_usage(msg) -> tuple[int, int]:
    """Return (input_tokens, output_tokens) from an AIMessage, or (0, 0)."""
    meta = getattr(msg, "usage_metadata", None)
    if not meta:
        return 0, 0
    return meta.get("input_tokens", 0), meta.get("output_tokens", 0)


# --------------------------------------------------------------------------- #
# Models                                                                       #
# --------------------------------------------------------------------------- #

@lru_cache(maxsize=1)
def _get_cheap_model() -> ChatGoogleGenerativeAI:
    s = get_settings()
    return ChatGoogleGenerativeAI(
        model=s.agent_cheap_model,
        google_api_key=s.google_api_key.get_secret_value(),
        temperature=0.1,
    ).bind_tools(AGENT_TOOLS)


@lru_cache(maxsize=1)
def _get_strong_model() -> ChatGoogleGenerativeAI:
    s = get_settings()
    # No tools bound — synthesis only.
    return ChatGoogleGenerativeAI(
        model=s.agent_model,
        google_api_key=s.google_api_key.get_secret_value(),
        temperature=0.2,
    )


# --------------------------------------------------------------------------- #
# Nodes                                                                        #
# --------------------------------------------------------------------------- #

async def tool_selection_node(state: AgentState) -> dict:
    """Cheap model: decide which tools to call and extract their arguments."""
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=_TOOL_SELECTION_PROMPT)] + messages

    response = await _get_cheap_model().ainvoke(messages)

    usage = state.get("token_usage") or TokenUsage().as_dict()
    inp, out = _extract_usage(response)
    updated = {**usage, "cheap_in": usage["cheap_in"] + inp,
               "cheap_out": usage["cheap_out"] + out}

    tool_rounds = state.get("tool_rounds", 0) + 1
    return {"messages": [response], "token_usage": updated, "tool_rounds": tool_rounds}


async def synthesis_node(state: AgentState) -> dict:
    """Strong model: synthesise all tool results into a final recommendation."""
    # Strip the tool-selection system prompt; inject the synthesis one.
    history = [m for m in state["messages"] if not isinstance(m, SystemMessage)]
    messages = [SystemMessage(content=_SYNTHESIS_PROMPT)] + history

    response = await _get_strong_model().ainvoke(messages)

    usage = state.get("token_usage") or TokenUsage().as_dict()
    inp, out = _extract_usage(response)
    updated = {**usage, "strong_in": usage["strong_in"] + inp,
               "strong_out": usage["strong_out"] + out,
               "total_in": usage.get("total_in", 0) + inp,
               "total_out": usage.get("total_out", 0) + out}

    return {"messages": [response], "token_usage": updated}


def _enforce_allowlist(state: AgentState) -> dict:
    """Block tool calls not in TOOL_ALLOWLIST; return error ToolMessages."""
    last = state["messages"][-1]
    if not hasattr(last, "tool_calls"):
        return {}

    blocked: list[ToolMessage] = []
    allowed = []
    for tc in last.tool_calls:
        if tc["name"] not in TOOL_ALLOWLIST:
            blocked.append(ToolMessage(
                content=(
                    f"Tool '{tc['name']}' is not in the allowlist. "
                    f"Allowed: {sorted(TOOL_ALLOWLIST)}."
                ),
                tool_call_id=tc["id"],
            ))
        else:
            allowed.append(tc)

    if not blocked:
        return {}

    last.tool_calls = allowed  # type: ignore[attr-defined]
    return {"messages": blocked}


# --------------------------------------------------------------------------- #
# Routing                                                                      #
# --------------------------------------------------------------------------- #

def _should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if (
        hasattr(last, "tool_calls")
        and last.tool_calls
        and state.get("tool_rounds", 0) < MAX_TOOL_ROUNDS
    ):
        return "tools"
    return "synthesize"


# --------------------------------------------------------------------------- #
# Graph assembly                                                               #
# --------------------------------------------------------------------------- #

@lru_cache(maxsize=1)
def build_graph():
    """Build and compile the two-model ReAct graph.  Cached — call freely."""
    tool_node = ToolNode(AGENT_TOOLS)

    g = StateGraph(AgentState)
    g.add_node("tool_selection", tool_selection_node)
    g.add_node("allowlist_check", _enforce_allowlist)
    g.add_node("tools", tool_node)
    g.add_node("synthesis", synthesis_node)

    g.add_edge(START, "tool_selection")
    g.add_conditional_edges(
        "tool_selection",
        _should_continue,
        {"tools": "allowlist_check", "synthesize": "synthesis"},
    )
    g.add_edge("allowlist_check", "tools")
    g.add_edge("tools", "tool_selection")
    g.add_edge("synthesis", END)

    return g.compile()


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #

def extract_text(content: str | list) -> str:
    """Normalise Gemma-style typed content blocks to plain text."""
    if isinstance(content, str):
        return content
    parts = [
        block.get("text", "")
        for block in content
        if isinstance(block, dict) and block.get("type") == "text"
    ]
    return "\n".join(parts) if parts else str(content)


async def run_agent(
    user_message: str,
    *,
    session: AsyncSession | None = None,
    user_id: int | None = None,
) -> tuple[str, dict]:
    """Run the agent for a single user turn.

    Returns ``(answer_text, token_usage_dict)``.  The usage dict has keys:
    ``cheap_in``, ``cheap_out``, ``strong_in``, ``strong_out``,
    ``total_in``, ``total_out``.

    When *session* is provided the run and all tool calls are persisted to
    the database via ``run_logger.log_run``.
    """
    graph = build_graph()
    initial: AgentState = {
        "messages": [HumanMessage(content=user_message)],
        "token_usage": TokenUsage().as_dict(),
        "tool_rounds": 0,
    }
    result = await graph.ainvoke(initial, config={"recursion_limit": 20})
    text = extract_text(result["messages"][-1].content)
    usage = result.get("token_usage", TokenUsage().as_dict())
    # Recompute totals in case synthesis_node didn't update them.
    usage["total_in"] = usage.get("cheap_in", 0) + usage.get("strong_in", 0)
    usage["total_out"] = usage.get("cheap_out", 0) + usage.get("strong_out", 0)

    if session is not None:
        from app.services.run_logger import log_run
        await log_run(
            session,
            question=user_message,
            answer=text,
            token_usage=usage,
            messages=result["messages"],
            user_id=user_id,
        )

    return text, usage

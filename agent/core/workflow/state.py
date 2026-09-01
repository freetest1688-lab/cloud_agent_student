import operator
from typing import Annotated, TypedDict, Any, Sequence
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    Global LangGraph state.
    Carries information between the Router, individual sub-agents, and Memory.
    """
    # Message history; operator.add appends new messages to the list
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # ================== TODO 01 - AgentState fields ==================
    # GOAL : Declare the 5 remaining keys carried between graph nodes.
    # WHY  : Every LangGraph node reads and writes this dict. Wrong keys = silent routing bugs.
    # STEPS:
    #   1. next_agent (str): which node the orchestrator picked.
    #   2. user_id / session_id (str): identity + memory isolation.
    #   3. memory_context (str): text injected into each agent's system prompt.
    #   4. metadata (dict[str, Any]): scratch space, e.g. the FinOps handoff flag.
    # HINT : `messages` above is the worked example. These 5 need NO Annotated wrapper - only `messages` accumulates; the rest are overwritten each step.
    # CHECK: python -c "from core.workflow.state import AgentState; print(AgentState.__annotations__)"
    # SIZE : ~6 lines
    # ======================================================

class AgentOutput(TypedDict):
    """Standard output format for agent execution."""
    response: str
    tool_calls: list[dict[str, Any]]
    metadata: dict[str, Any]

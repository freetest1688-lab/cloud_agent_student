import os
import sys
from pathlib import Path
# No sys.path.insert here — the caller (main.py) is expected to set sys.path correctly.

import asyncio
from typing import Literal

from langgraph.graph import StateGraph, START, END
from core.workflow.state import AgentState
from agents.orchestrator import OrchestratorAgent
from agents.product_agent import ProductAgentNode
from agents.billing_agent import BillingAgentNode
from agents.promotion_agent import PromotionAgentNode
from agents.recommendation_agent import RecommendationAgent
from agents.finops_agent import FinOpsAgentNode

class AgentGraphManager:
    """
    Assembles the LangGraph multi-agent orchestration.
    Supports cross-agent state handoff for FinOps workflows.
    """
    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.product_node = ProductAgentNode()
        self.billing_node = BillingAgentNode()
        self.promotion_node = PromotionAgentNode()
        self.recommendation_node = RecommendationAgent()
        self.finops_node = FinOpsAgentNode()

    def _route_condition(self, state: AgentState) -> str:
        """Determine which agent node to route to based on the orchestrator's decision."""
        return state.get("next_agent", "product_agent")

    def _billing_post_condition(self, state: AgentState) -> str:
        """
        Conditional check after the BillingAgent node finishes:
        hands off to the FinOps agent when inside a FinOps workflow,
        otherwise ends directly for a regular billing query.
        """
        # ================== TODO 02 - FinOps handoff condition ==================
        # GOAL : Return the next node after billing_agent finishes.
        # WHY  : This is a conditional edge: one node, two possible successors, chosen at runtime.
        # STEPS:
        #   1. Read metadata['is_finops_workflow'] from state (default False).
        #   2. If truthy return the string 'finops_agent'.
        #   3. Otherwise return END (already imported from langgraph.graph).
        # HINT : Use state.get('metadata', {}).get(...) - metadata may be missing entirely.
        # CHECK: Ask 'my bill is too expensive' -> should hit BOTH billing and finops nodes.
        # SIZE : ~3 lines
        raise NotImplementedError("TODO 02: return 'finops_agent' or END")
        # ======================================================

    def build_graph(self) -> StateGraph:
        """Build the state graph."""
        builder = StateGraph(AgentState)

        # 1. Add nodes
        builder.add_node("orchestrator", self.orchestrator.route)
        builder.add_node("product_agent", self.product_node)
        builder.add_node("billing_agent", self.billing_node)
        builder.add_node("promotion_agent", self.promotion_node)
        builder.add_node("recommendation_agent", self.recommendation_node)
        builder.add_node("finops_agent", self.finops_node)

        # 2. Define edges
        builder.add_edge(START, "orchestrator")

        # After the orchestrator, route to the appropriate sub-agent via condition
        # ================== TODO 03 - Orchestrator routing edges ==================
        # GOAL : Wire the orchestrator to the 4 sub-agents.
        # WHY  : Conditional edges turn the router's string decision into an actual graph transition.
        # STEPS:
        #   1. Call builder.add_conditional_edges('orchestrator', self._route_condition, {...}).
        #   2. The dict maps the RETURN VALUE of _route_condition -> node name.
        #   3. Include product_agent, billing_agent, promotion_agent, recommendation_agent.
        # HINT : Keys and values are identical strings here; the mapping still must be explicit.
        # CHECK: python core/workflow/graph_manager.py  (runs the built-in 2-turn smoke test)
        # SIZE : ~8 lines
        # ======================================================

        # 3. Cross-agent state handoff edges
        # After BillingAgent, dynamically decide whether to pass control to FinOpsAgent
        # ================== TODO 04 - Billing -> FinOps edge ==================
        # GOAL : Register the conditional edge that enables the FinOps handoff.
        # WHY  : This is what makes billing_agent able to END *or* continue - a 2-step workflow.
        # STEPS:
        #   1. Call builder.add_conditional_edges('billing_agent', self._billing_post_condition, {...}).
        #   2. Map 'finops_agent' -> 'finops_agent' and END -> END.
        #   3. END is a sentinel object, not a string - use it directly as a dict key.
        # HINT : Depends on TODO 02 returning those exact values.
        # CHECK: Ask a plain billing question -> must END, not fall into finops.
        # SIZE : ~7 lines
        # ======================================================

        # After each sub-agent finishes, end the flow
        builder.add_edge("product_agent", END)
        builder.add_edge("promotion_agent", END)
        builder.add_edge("recommendation_agent", END)
        builder.add_edge("finops_agent", END)

        return builder.compile()

async def test_graph():
    manager = AgentGraphManager()
    graph = manager.build_graph()

    print("🚀 Starting cloud platform intelligent customer service system (Multi-Agent orchestration mode)...")
    print("="*60)
    
    # Simulate the first conversation turn
    state: AgentState = {
        "messages": [("user", "What is VPC?")],
        "user_id": "user_1001",
        "session_id": "test_session_1",
        "memory_context": "",
        "next_agent": "",
        "metadata": {}
    }
    print(f"👤 User: {state['messages'][0][1]}")
    
    result = await graph.ainvoke(state)
    print(f"🤖 AI: {result['messages'][-1].content}\n")

    # Simulate the second turn to test routing
    state["messages"] = result["messages"]
    state["messages"].append(("user", "Can you check which machines I purchased recently?"))
    
    print(f"👤 User: {state['messages'][-1][1]}")
    result = await graph.ainvoke(state)
    print(f"🤖 AI: {result['messages'][-1].content}\n")

if __name__ == "__main__":
    asyncio.run(test_graph())
"""Central routing node (Orchestrator) for the multi-agent cloud customer-service system."""
import os
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from core.workflow.state import AgentState

class OrchestratorAgent:
    """
    Central routing node (Orchestrator/Router).
    Analyzes user intent and dispatches requests to the appropriate specialized agent.
    """
    def __init__(self):
        dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        load_dotenv(dotenv_path)

        # The router only needs a base LLM for classification decisions — no complex tools required
        self.llm = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("MODEL", "gpt-4o"),
            base_url=os.getenv("BASE_URL") or None,
            temperature=0.1,
        )

    async def route(self, state: AgentState) -> Dict[str, Any]:
        """
        Determines the routing destination based on the user's latest input.
        """
        # Retrieve the most recent user message
        messages = state.get("messages", [])
        if not messages:
            last_message = ""
        else:
            # LangGraph internally sometimes converts tuples into actual BaseMessage subclasses
            last_msg_obj = messages[-1]
            if isinstance(last_msg_obj, tuple):
                last_message = last_msg_obj[1]
            elif hasattr(last_msg_obj, "content"):
                last_message = last_msg_obj.content
            else:
                last_message = str(last_msg_obj)
        memory_context = state.get("memory_context", "")

        system_prompt = f"""You are the central router (Orchestrator) of an intelligent customer-service system.
Your task is to analyze the user's question and decide which specialized agent should handle it.

Available sub-agents:
1. "product_agent"         : Handles cloud product introductions, resource specification descriptions, concept explanations, operation guides, etc. (NOT personal asset queries).
2. "billing_agent"         : Handles queries about a user's personal cloud resource instances, purchased machines, order records, billing details, etc.
3. "promotion_agent"       : Handles requests related to sharing products, referral commissions, obtaining campaign links, generating posters, and other marketing needs.
4. "recommendation_agent"  : Provides professional cloud product selection and recommendations based on the user's business requirements (e.g., Java+MySQL, high concurrency, specific budget), including specific instance types and configuration suggestions.
5. "finops_agent_trigger"  : Select this when the user expresses intent such as "my bill is too expensive", "I need to reduce costs", "idle resources", or "help me optimize costs/servers".

Routing rules (high priority):
- When the user asks "which instance should I pick for a given scenario / is this spec sufficient / recommend a specific model" (e.g., Java + MySQL, is 8-core 16 GB enough), route to product_agent.
- Route to deep_research_agent ONLY when the user explicitly requests a "deep research report / lengthy architecture comparison / competitive analysis document / detailed evaluation report".
- "Recommend a product / recommend a model / product selection advice / which one should I buy" defaults to recommendation_agent, not product_agent.

[Background memory context]:
{memory_context}

Output only the name you want to route to (must be one of: product_agent, billing_agent, promotion_agent, recommendation_agent, finops_agent_trigger). Do not output any explanatory text.
If you cannot determine the intent, default to product_agent.
"""

        # ================== TODO 05 - Router LLM call ==================
        # GOAL : Ask the LLM to classify the user's intent.
        # WHY  : The router is just an LLM with a constrained output space - no tools needed.
        # STEPS:
        #   1. await self.llm.ainvoke([...]) with a 2-message list.
        #   2. SystemMessage(content=system_prompt) then HumanMessage(content=last_message).
        #   3. Store the result in `response`.
        # HINT : Both message classes are already imported at the top of this file.
        # CHECK: Add `print(response.content)` temporarily to see the raw label.
        # SIZE : ~4 lines
        # ======================================================
        
        # ================== TODO 06 - Intent -> node mapping ==================
        # GOAL : Turn the LLM's text label into a node name.
        # WHY  : LLMs return prose, not enums. Substring matching is the cheap robust guard.
        # STEPS:
        #   1. decision = response.content.strip().lower()
        #   2. If 'finops' in decision -> next_node='billing_agent' AND set state['metadata']['is_finops_workflow']=True (FinOps starts by fetching instances).
        #   3. elif 'billing' -> 'billing_agent' and set the flag False.
        #   4. elif 'promotion' -> 'promotion_agent'; elif 'recommendation' -> 'recommendation_agent'.
        #   5. else -> 'product_agent' (safe default when the LLM is unclear).
        # HINT : Note the trap: 'finops' ALSO routes to billing_agent first - the flag is what differs.
        # CHECK: Try 'what is a VPC' (product), 'my orders' (billing), 'cut my costs' (finops).
        # SIZE : ~10 lines
        raise NotImplementedError("TODO 06: set next_node from `decision`")
        # ======================================================
            
        # Return the updated state
        return {"next_agent": next_node, "metadata": state.get("metadata", {})}

"""FinOps cost-optimization agent node for analyzing cloud resource usage and recommending savings."""
import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from typing import Dict, Any

from core.workflow.state import AgentState
from agents.billing_agent import UserIdInjector

class FinOpsAgentNode:
    """
    FinOps Agent: cost-optimization and architecture-diagnosis expert.
    Analyzes resource monitoring data for the user's instances, identifies idle/wasted
    resources, and provides actionable cost-reduction recommendations.
    """
    def __init__(self):
        dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
        load_dotenv(dotenv_path)

        self.llm = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("MODEL", "gpt-4o"),
            base_url=os.getenv("BASE_URL") or None,
            temperature=0.1,
        )
        
        from config.mcp_loader import load_mcp_servers_config
        self.servers_config = load_mcp_servers_config()

    async def _ensure_tools(self):
        pass

    async def __call__(self, state: AgentState) -> Dict[str, Any]:
        config = {"configurable": {"user_id": state.get("user_id", "unknown")}}

        # ================== TODO 09 - FinOps tool set ==================
        # GOAL : Give the FinOps agent its 2 analysis tools.
        # WHY  : Same allowlist pattern as TODO 08 - practice it, then note what differs.
        # STEPS:
        #   1. Build the client with the SAME UserIdInjector (imported from billing_agent).
        #   2. await client.get_tools().
        #   3. Filter to query_user_instances and analyze_instance_usage.
        # HINT : It reuses billing's interceptor - identity rules are global, not per-agent.
        # CHECK: Ask 'my server is too expensive' and watch for analyze_instance_usage.
        # SIZE : ~6 lines
        # ======================================================
        
        system_prompt = f"""You are a professional cloud [FinOps Cost-Optimization Expert].
You have just taken over the context passed from the previous agent (BillingAgent).

Your tasks:
1. Carefully read the conversation history in the context and extract the **instance ID (instance_id)** the user wants to optimize.
2. If no instance_id is present in the context, call `query_user_instances` to retrieve the user's instance list, and prioritize Running ECS instances for analysis. If there are multiple instances, present the list and ask the user to specify a target.
3. Call `analyze_instance_usage` to obtain recent CPU, memory, and other monitoring data for the target instance.
4. Based on the monitoring data, determine whether the instance exhibits "resource idling (RESOURCES_IDLE)".
5. Deliver **cost-reduction recommendations** in the tone of a cloud architect:
   - If CPU utilization has been consistently very low, recommend downsizing the instance (e.g., from 8xlarge to 2xlarge, or switching from compute-optimized to general-purpose).
   - Estimate the benefit of the downsize (e.g., potential monthly savings).
   - Keep the tone professional and sincere — always advocate for the user's financial interests.

Note: The system automatically injects user_id; pass the placeholder "auto" when calling tools.
- Never fabricate instance IDs, monitoring metrics, or cost-saving figures; all responses must be based on actual tool results.
- Never use internal expressions such as "tool unavailable / API broken / system error" when communicating with users; always use business-friendly language.
"""
        inner_agent = create_react_agent(
            model=self.llm,
            tools=tools,
            prompt=system_prompt
        )
        
        print("💡 [FinOpsAgent] Analyzing instance monitoring metrics and generating cost-optimization report...")
        
        result = await inner_agent.ainvoke(
            {"messages": state["messages"]}, 
            config=config
        )
        
        final_message = result["messages"][-1]
        
        # Clear next_agent after execution to signal the end of the workflow
        return {"messages": [final_message], "next_agent": ""}

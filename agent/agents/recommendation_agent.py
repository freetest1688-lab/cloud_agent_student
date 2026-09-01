"""Intelligent product recommendation agent that combines vector search with the MCP product catalog."""
import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from core.workflow.state import AgentState
from typing import Dict, Any
from langchain_mcp_adapters.client import MultiServerMCPClient
from agents.billing_agent import UserIdInjector
from tools.vector_tool import query_vector_db

class RecommendationAgent:
    """
    Intelligent Recommendation Agent: recommends the most suitable cloud product models
    based on the user's business requirements (type, budget, concurrency, etc.).
    It queries the vector database for product specifications and uses MCP to
    retrieve the live product catalog.
    """
    def __init__(self):
        dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
        load_dotenv(dotenv_path)

        self.llm = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("MODEL", "gpt-4o"),
            base_url=os.getenv("BASE_URL") or None,
            temperature=0.3, # Recommendation scenarios benefit from a degree of flexibility, but not too high
        )
        
        from config.mcp_loader import load_mcp_servers_config
        self.servers_config = load_mcp_servers_config()

    async def __call__(self, state: AgentState) -> Dict[str, Any]:
        memory_context = state.get("memory_context", "")
        config = {"configurable": {"user_id": state.get("user_id", "unknown")}}
        
        # Fetch MCP tools (used to pull the product catalog)
        client = MultiServerMCPClient(
            connections=self.servers_config.get("mcpServers", {}),
            tool_interceptors=[UserIdInjector()]
        )
        all_tools = await client.get_tools()
        # We need search_product_catalog and get_promotable_products to pull products,
        # plus get_promotion_materials to retrieve purchase/campaign links
        target_tools = ["get_promotable_products", "search_product_catalog", "get_promotion_materials"]
        mcp_tools = [t for t in all_tools if t.name in target_tools]
        
        # Combine vector tool with MCP tools
        tools = [query_vector_db] + mcp_tools

        system_prompt = f"""You are a senior cloud architect and [Intelligent Recommendation Agent].
Your task is to recommend the most suitable cloud product models based on the user's business scenario (e.g., Java+MySQL, high concurrency, specific budget).

[Workflow]
1. Analyze the user's business requirements (workload type, DAU/concurrency, budget, region, etc.). If the user is simply asking "what products are available", skip the analysis and directly display the current platform's product catalog.
2. (Required) Call `get_promotable_products` or `search_product_catalog` to fetch the real, purchasable product list currently available on the platform.
3. For product-selection recommendations, call `query_vector_db` to retrieve technical characteristics and applicable scenarios for the relevant specifications (e.g., c7, g8a).
4. Select 1–3 of the most suitable products for the user and provide professional justification (why this product, what user pain point it addresses). For catalog inquiries, present the list in a structured format.
5. (Very important) For each recommended product, call `get_promotion_materials` to obtain the purchase/campaign link, and include those direct purchase links in the final response.

[Response requirements]
- Adopt the tone of a professional and enthusiastic cloud architect consultant.
- Always include specific instance types or product names.
- Keep the response well-structured (use lists and bold text).
- Never recommend fictitious products that do not appear in the `get_promotable_products` list.
- At the end of every response, list only the sources from which data was actually retrieved, using the following format:
  Sources:
  - Vector search: xxx.md
  (Do not output tools that were not used or include a "confidence" field.)

[System-provided user memory / background context]:
{memory_context if memory_context else "No background context available."}
"""
        # ================== TODO 11 - Recommendation executor ==================
        # GOAL : Run the recommender over vector + MCP tools.
        # WHY  : Shows a hybrid toolset: local @tool functions and remote MCP tools side by side.
        # STEPS:
        #   1. create_react_agent(model=self.llm, tools=tools, prompt=system_prompt) - `tools` already combines query_vector_db with the MCP tools.
        #   2. await inner_agent.ainvoke({'messages': state['messages']}, config=config).
        #   3. Return the last message wrapped in a list.
        # HINT : config carries user_id so the interceptor still applies to the MCP half.
        # CHECK: Ask 'recommend a server for Java + MySQL' - expect specs AND a purchase link.
        # SIZE : ~6 lines
        raise NotImplementedError("TODO 11: run the recommendation ReAct agent")
        # ======================================================

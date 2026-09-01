"""Product consultation agent node using vector DB and knowledge-graph retrieval tools."""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.prebuilt import create_react_agent

# Import the pre-wrapped tools
from tools.vector_tool import query_vector_db
from tools.graph_tool import query_knowledge_graph
from core.workflow.state import AgentState
from typing import Dict, Any

class ProductAgentNode:
    """
    Node class wrapping LangGraph's create_react_agent.
    Called directly by the main graph orchestrator.
    """
    def __init__(self):
        dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        load_dotenv(dotenv_path)

        self.llm = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("MODEL", "gpt-4o"),
            base_url=os.getenv("BASE_URL") or None,
            temperature=0.1,
        )
        self.tools = [query_vector_db, query_knowledge_graph]

    async def __call__(self, state: AgentState) -> Dict[str, Any]:
        """
        Entry point called by the main LangGraph.
        """
        memory_context = state.get("memory_context", "")
        system_prompt = f"""You are a professional cloud-platform [Product Consultation Agent].
Your task is to answer users' questions about cloud products (e.g., ECS cloud servers, VPC virtual private networks, etc.).
You have two powerful retrieval tools at your disposal:

1. `query_vector_db` (vector database retrieval):
   - Best for: retrieving lengthy concept explanations, step-by-step operation guides, and detailed policy documents.
   - Strength: handles fuzzy semantic matching and long-text comprehension.

2. `query_knowledge_graph` (knowledge graph retrieval):
   - Best for: querying cloud-product architecture, entity containment relationships, specific configuration values and limits, and composite structured-data queries.
   - Strength: handles precise attribute lookups, relationship traversal, and multi-hop topology queries.

Work guidelines:
- Carefully analyze the user's question and independently decide which tool(s) to use, or combine both if the question is complex.
- For questions about structured parameters (e.g., NIC count, bandwidth, instance relationships), prefer `query_knowledge_graph` first; if the graph query times out or fails, automatically fall back to `query_vector_db` and continue answering.
- If the question involves both structured parameters and policy explanations, combining both tools is recommended; however, availability takes priority — using the graph tool is not mandatory.
- Always use tools to gather factual evidence; do not fabricate answers (hallucinate).
- After obtaining information, present the answer in a professional, clear, and friendly customer-service tone.
- If a tool returns no relevant results, honestly tell the user that no related records were found in the knowledge base.
- Only cite sources that explicitly appear in a tool's raw return value; never fabricate document names, version numbers, or whitepaper titles.
- If a tool was not called or its call failed, do not mention it in the "Sources" section, and do not explain why it was not used.
- At the end of every final response, list only the sources from which data was actually retrieved. Do not include a "confidence" field or list unused tools.
  Format example:
  Sources:
  - Vector search: xxx.md
  (If only vector search was used, output only that line; if only the knowledge graph was used, output only that line; if both were used, output both lines.)

[System-provided user memory / background context]:
{memory_context if memory_context else "No background context available."}
"""
        # ================== TODO 10 - ReAct sub-agent ==================
        # GOAL : Build the inner ReAct agent and return its last message.
        # WHY  : Each node is itself a full agent. The outer graph only sees the final message.
        # STEPS:
        #   1. create_react_agent(model=self.llm, tools=self.tools, prompt=system_prompt).
        #   2. result = await inner_agent.ainvoke({'messages': state['messages']}) - pass the FULL history.
        #   3. Take result['messages'][-1] and return {'messages': [<it>]}.
        # HINT : Return a LIST of one message: state.messages uses operator.add, so it appends.
        # CHECK: Ask 'What is a VPC?' - should cite a vector-search source.
        # SIZE : ~8 lines
        raise NotImplementedError("TODO 10: build the ReAct agent and return its final message")
        # ======================================================

def get_product_agent():
    """Retained as an entry point for standalone testing."""
    pass

if __name__ == "__main__":
    # Simple interactive test entry point
    agent = get_product_agent()
    
    print("🤖 ProductAgent started! (type 'quit' or 'exit' to stop)")
    print("=" * 50)
    print("You can try asking:")
    print("1. [Graph test]  How many elastic NICs can an ecs.g8a.4xlarge instance attach?")
    print("2. [Vector test] What are the conditions that restrict the 5-day no-questions-asked refund policy?")
    print("3. [Hybrid test] What is a VPC? And which instance families are available in the China North 2 (Beijing) region?")
    print("=" * 50)

    # A thread ID is needed to maintain context across turns; a simple fixed value is fine for testing
    config = {"configurable": {"thread_id": "test_thread_1"}}

    while True:
        user_input = input("\n👤 User: ")
        if user_input.lower() in ['quit', 'exit']:
            break
            
        if not user_input.strip():
            continue

        print("\n🤖 Thinking and retrieving...")
        
        # Invoke the agent
        try:
            # stream_mode="values" lets us access the final state snapshot
            for event in agent.stream({"messages": [("user", user_input)]}, config=config, stream_mode="values"):
                # Get the last message
                last_message = event["messages"][-1]
                # Print tool-call progress (optional, for clarity during demos)
                if getattr(last_message, "tool_calls", None):
                    for tc in last_message.tool_calls:
                        print(f"   [Tool Call] Calling tool: {tc['name']} (args: {tc['args']})")
            
            # Final answer
            final_message = event["messages"][-1].content
            print(f"\n💡 ProductAgent: {final_message}")
        except Exception as e:
            print(f"\n❌ An error occurred: {str(e)}")

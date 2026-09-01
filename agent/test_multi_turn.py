import asyncio
from core.workflow.graph_manager import AgentGraphManager

async def test_multi_turn():
    manager = AgentGraphManager()
    graph = manager.build_graph()
    
    state = {
        "messages": [],
        "user_id": "user_999",
        "session_id": "test_session_multi",
        "memory_context": "",
        "next_agent": "",
        "metadata": {}
    }
    
    # Turn 1: vague promotion intent
    user_msg_1 = "I want to promote products and earn money — what can I promote?"
    print(f"\n👤 User: {user_msg_1}")
    state["messages"].append(("user", user_msg_1))
    result = await graph.ainvoke(state)
    state["messages"] = result["messages"]
    print(f"\n🤖 AI: {result['messages'][-1].content}\n")
    
    # Turn 2: make a selection from the list
    user_msg_2 = "I'll promote the 2nd one — the compute-optimized ECS"
    print(f"\n👤 User: {user_msg_2}")
    state["messages"].append(("user", user_msg_2))
    
    # Pass user_id via config so the underlying interceptor can read it
    config = {"configurable": {"user_id": "user_999"}}
    result = await graph.ainvoke(state, config=config)
    print(f"\n🤖 AI: {result['messages'][-1].content}\n")

if __name__ == "__main__":
    asyncio.run(test_multi_turn())
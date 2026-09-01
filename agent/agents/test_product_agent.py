import sys
from product_agent import get_product_agent

agent = get_product_agent()
config = {"configurable": {"thread_id": "auto_test"}}

questions = [
    "How many elastic NICs can an ecs.g8a.4xlarge instance attach?",
    "What are the conditions that restrict the 5-day no-questions-asked refund policy?",
    "What is a VPC? And which instance families are available in the China North 2 (Beijing) region?"
]

for q in questions:
    print(f"\n[{'-'*40}]\n👤 Q: {q}")
    for event in agent.stream({"messages": [("user", q)]}, config=config, stream_mode="values"):
        last_message = event["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            for tc in last_message.tool_calls:
                print(f"🔧 Calling tool: {tc['name']}")
    final_message = event["messages"][-1].content
    print(f"🤖 A: {final_message}")

"""Main entry point for the multi-agent cloud customer-service system.

Provides a CLI interface for interacting with the LangGraph-based multi-agent
system, integrating FastMCP tools and short/long-term memory.

Usage:
    python main.py                    # interactive mode
    python main.py --query "What is VPC"  # single-query mode
"""
import argparse
import asyncio
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Any

# Suppress harmless gRPC fork-related warnings on macOS (from pymilvus/grpcio)
os.environ.setdefault("GRPC_VERBOSITY", "ERROR")
os.environ.setdefault("GRPC_TRACE", "")

# Add parent directory to the import path
sys.path.insert(0, str(Path(__file__).parent))

# Ensure stdin/stdout use UTF-8 on all platforms (fixes non-ASCII input on macOS terminals)
if hasattr(sys.stdin, 'reconfigure'):
    sys.stdin.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from config import get_settings
from core.memory import MemoryManager
from core.workflow.graph_manager import AgentGraphManager
from core.workflow.state import AgentState


def setup_logging(log_level: str = "INFO") -> None:
    """Configure application-level logging."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )

async def _extract_memory_context(memory: MemoryManager, user_id: str, session_id: str, query: str) -> str:
    """Helper that fetches memory context from Redis (short-term) and Milvus (long-term)."""
    context_parts = []
    
    # 1. Fetch short-term history
    if memory.short_term.available:
        history = await memory.short_term.get_messages(user_id, session_id)
        if history:
            # Keep only the most recent turns
            recent_history = history[-10:] if len(history) > 10 else history
            context_parts.append("[Recent Conversation History]:")
            for msg in recent_history:
                role = "User" if msg["role"] == "user" else "Assistant"
                context_parts.append(f"{role}: {msg['content']}")
    
    # 2. Fetch long-term preferences
    if memory.long_term.available:
        prefs = await memory.long_term.retrieve_relevant(user_id, query)
        if prefs:
            context_parts.append("\n[User Long-term Preferences / Background]:")
            for p in prefs:
                context_parts.append(f"- {p}")
                
    return "\n".join(context_parts)

async def run_interactive_mode(
    graph_manager: AgentGraphManager,
    user_id: str,
    session_id: str,
    memory: MemoryManager,
) -> None:
    """Run an interactive chat loop with the multi-agent graph."""
    print("\n" + "=" * 60)
    print("🤖 Cloud Platform Multi-Agent System Ready!")
    print(f"  User:    {user_id}")
    print(f"  Session: {session_id}")
    print("  Type 'quit' / 'exit' / 'q' to stop")
    print("=" * 60)

    st_ok = memory.short_term.available
    lt_ok = memory.long_term.available
    print(f"\n  [MEM] Short-term (Redis) : {'✅ connected' if st_ok else '❌ not available'}")
    print(f"  [MEM] Long-term  (Milvus): {'✅ connected' if lt_ok else '❌ not available'}")
    print()

    graph = graph_manager.build_graph()
    
    # Initialize state
    state: AgentState = {
        "messages": [],
        "user_id": user_id,
        "session_id": session_id,
        "memory_context": "",
        "next_agent": "",
        "metadata": {}
    }
    
    turn_count = 0

    try:
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
            except UnicodeDecodeError:
                raw = sys.stdin.buffer.readline()
                user_input = raw.decode('utf-8', errors='replace').strip()
            except EOFError:
                break

            if user_input.lower() in ("quit", "exit", "q"):
                break
            if not user_input:
                continue

            # 1. Fetch memory context before executing
            print("🧠 Retrieving memory context...")
            mem_context = await _extract_memory_context(memory, user_id, session_id, user_input)
            
            # Update state with new input and memory
            state["messages"].append(("user", user_input))
            state["memory_context"] = mem_context

            # 2. Execute the graph
            print("🤖 Processing...")
            result = await graph.ainvoke(state)
            
            # Update state with result messages
            state["messages"] = result["messages"]
            response_text = result["messages"][-1].content
            
            print(f"\n🤖 AI: {response_text}\n")
            
            # 3. Save to short-term memory
            if memory.short_term.available:
                turn = [
                    {"role": "user", "content": user_input},
                    {"role": "assistant", "content": response_text},
                ]
                await memory.save_conversation(user_id, session_id, turn)
            
            # 4. Periodically trigger long-term memory extraction
            turn_count += 1
            if turn_count % 5 == 0:
                print("🔄 [Background] Triggering long-term memory extraction...")
                asyncio.create_task(memory.extract_and_save_preferences(user_id, session_id))

    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        logging.exception("Agent execution failed")
    finally:
        print("\n" + "-" * 60)
        print("💾 Saving session preferences to long-term memory...")
        await memory.extract_and_save_preferences(user_id, session_id)
        print("✅ Session finalized.")
        print("-" * 60 + "\n")


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Multi-Agent Cloud Service System")
    parser.add_argument("--query", "-q", type=str, help="Single query mode")
    parser.add_argument("--user", "-u", type=str, default="user_1001", help="User ID")
    parser.add_argument("--session", "-s", type=str, default=None, help="Session ID")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    log_level = "DEBUG" if args.debug else get_settings().log_level
    setup_logging(log_level)
    
    user_id = args.user
    session_id = args.session or f"session_{uuid.uuid4().hex[:8]}"
    
    settings = get_settings()
    
    # Initialize memory manager
    memory = MemoryManager(
        redis_url=settings.redis_url,
        redis_ttl=settings.redis_ttl,
        milvus_host=settings.milvus_host,
        milvus_port=settings.milvus_port,
        milvus_api_key=settings.milvus_api_key,
        embedding_api_key=settings.openai_api_key,
    )
    await memory.initialize()
    
    # Initialize graph manager
    graph_manager = AgentGraphManager()
    
    try:
        if args.query:
            # Single-query mode: same flow as interactive, but no loop
            graph = graph_manager.build_graph()
            mem_context = await _extract_memory_context(memory, user_id, session_id, args.query)
            state: AgentState = {
                "messages": [("user", args.query)],
                "user_id": user_id,
                "session_id": session_id,
                "memory_context": mem_context,
                "next_agent": "",
                "metadata": {}
            }
            print(f"\n👤 User: {args.query}")
            result = await graph.ainvoke(state)
            print(f"\n🤖 AI: {result['messages'][-1].content}\n")
        else:
            await run_interactive_mode(graph_manager, user_id, session_id, memory)
    finally:
        await memory.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.exception("Application failed")
        sys.exit(1)

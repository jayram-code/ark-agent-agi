import asyncio
import os
import sys
import traceback

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def verify_system():
    print("🔍 Starting System Verification...")
    errors = []

    # 1. Verify Imports
    print("\n1. Verifying Imports...")
    modules_to_check = [
        "orchestrator",
        "a2a_router",
        "models.messages",
        "agents.base_agent",
        "agents.sentiment_agent",
        "agents.priority_agent",
        "agents.ticket_agent",
        "agents.action_executor_agent",
        "agents.refund_agent",
        "agents.shipping_agent",
        "agents.email_sender_agent",
        "agents.supervisor_agent",
        "agents.planner_agent",
        "agents.retryable_agent",
        "agents.knowledge_agent",
        "agents.meeting_agent",
        "agents.memory_agent",
        "agents.emotion_agent",
        "utils.gemini_utils",
        "utils.logging_utils"
    ]

    for module in modules_to_check:
        try:
            __import__(f"src.{module}")
            print(f"  ✅ Imported src.{module}")
        except Exception as e:
            print(f"  ❌ Failed to import src.{module}: {e}")
            errors.append(f"Import Error: {module} - {e}")

    if errors:
        print("\n❌ Import verification failed!")
        return

    # 2. Verify Agent Instantiation
    print("\n2. Verifying Agent Instantiation...")
    from src.orchestrator import Orchestrator
    try:
        orc = Orchestrator()
        print("  ✅ Orchestrator initialized")
    except Exception as e:
        print(f"  ❌ Orchestrator initialization failed: {e}")
        errors.append(f"Orchestrator Init Error: {e}")
        return

    agents = [
        ("src.agents.sentiment_agent", "SentimentAgent"),
        ("src.agents.priority_agent", "PriorityAgent"),
        ("src.agents.ticket_agent", "TicketAgent"),
        ("src.agents.action_executor_agent", "ActionExecutorAgent"),
        ("src.agents.refund_agent", "RefundAgent"),
        ("src.agents.shipping_agent", "ShippingAgent"),
        ("src.agents.email_sender_agent", "EmailSenderAgent"),
        ("src.agents.supervisor_agent", "SupervisorAgent"),
        ("src.agents.planner_agent", "PlannerAgent"),
        ("src.agents.knowledge_agent", "KnowledgeAgent"),
        ("src.agents.meeting_agent", "MeetingAgent"),
        ("src.agents.memory_agent", "MemoryAgent"),
        ("src.agents.emotion_agent", "EmotionAgent"),
    ]

    for module_path, class_name in agents:
        try:
            module = sys.modules[module_path]
            agent_class = getattr(module, class_name)
            agent = agent_class(class_name.lower(), orc)
            print(f"  ✅ Instantiated {class_name}")
        except Exception as e:
            print(f"  ❌ Failed to instantiate {class_name}: {e}")
            errors.append(f"Instantiation Error: {class_name} - {e}")

    # RetryableAgent needs extra args
    try:
        from src.agents.retryable_agent import RetryableAgent
        agent = RetryableAgent("retryable_agent", orc, "target_agent")
        print(f"  ✅ Instantiated RetryableAgent")
    except Exception as e:
        print(f"  ❌ Failed to instantiate RetryableAgent: {e}")
        errors.append(f"Instantiation Error: RetryableAgent - {e}")

    if not errors:
        print("\n✅ System Verification Passed! All agents import and instantiate correctly.")
    else:
        print(f"\n❌ System Verification Failed with {len(errors)} errors.")

if __name__ == "__main__":
    asyncio.run(verify_system())

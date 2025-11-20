# Ark Agent AGI

**Multi-agent enterprise customer-care automation system powered by the A2A (Agent-to-Agent) protocol.**

This system leverages a network of specialized AI agents to automate complex customer service workflows, including refund processing, technical support, shipping inquiries, and intelligent email categorization.

## 🚀 Key Features

*   **Multi-Agent Architecture**: specialized agents (Sentiment, Priority, Planner, Action, etc.) collaborate to solve complex tasks.
*   **Async/Await Core**: Fully asynchronous event-driven architecture for high performance and non-blocking I/O.
*   **Type-Safe Communication**: Uses **Pydantic** models (`AgentMessage`) for robust and validated inter-agent messaging.
*   **Intelligent Routing**: Dynamic message routing based on intent, sentiment, and priority scores.
*   **Hybrid Memory Bank**: Persistent customer context using SQLite (structured) and FAISS (semantic vector search).
*   **Gemini AI Integration**: Powered by Google's Gemini 1.5 Flash for advanced natural language understanding and planning.
*   **Resilient Operations**: Built-in retry mechanisms with exponential backoff and validation frameworks.

## 🛠️ System Architecture

The system is built on the **A2A Protocol**, where agents communicate via structured messages managed by a central **Orchestrator**.

### Core Components

*   **Orchestrator**: The central hub that registers agents and routes messages.
*   **A2A Router**: Handles message validation, trace ID injection, and logging.
*   **BaseAgent**: Abstract base class defining the async `receive` interface.

### Specialized Agents

1.  **SentimentAgent**: Analyzes customer sentiment and emotion.
2.  **PriorityAgent**: Calculates urgency and escalation priority.
3.  **TicketAgent**: Manages support tickets (creation, tagging, updates).
4.  **RefundAgent**: Handles refund logic with risk assessment and payment provider integration.
5.  **ShippingAgent**: Tracks orders and provides shipping status.
6.  **PlannerAgent**: Generates step-by-step resolution plans using AI.
7.  **ActionExecutorAgent**: Executes planned actions (simulated).
8.  **SupervisorAgent**: Validates plans and oversees complex workflows.
9.  **EmailAgent**: Ingests and categorizes incoming emails.
10. **MemoryAgent**: Manages customer history and context retrieval.

## 📦 Data Models

Communication relies on strict Pydantic models defined in `src/models/messages.py`:

```python
class AgentMessage(BaseModel):
    id: str
    session_id: str
    sender: str
    receiver: str
    type: MessageType  # TASK_REQUEST, TASK_RESPONSE, INFO, ERROR, etc.
    timestamp: str
    payload: Union[Dict[str, Any], BaseModel]
    trace_id: Optional[str] = None
```

## 🏃‍♂️ Usage

### Prerequisites

*   Python 3.8+
*   Google Cloud API Key (for Gemini)

### Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Set your API key:
    ```bash
    export GOOGLE_API_KEY="your_api_key_here"
    ```

### Running the Showcase

To see the system in action, run the workflow showcase script:

```bash
python workflow_showcase.py
```

This script demonstrates:
1.  **Refund Automation**: Processing a refund request with risk checks.
2.  **Shipping Inquiry**: Tracking a package status.
3.  **Technical Support**: Escalating a login issue to a supervisor.
4.  **Auto-Categorization**: Tagging incoming emails based on intent.

## 🧪 Verification

Run the verification script to check system integrity:

```bash
python verify_refactor.py
```

## 📁 Project Structure

```
ark-agent-agi/
├── src/
│   ├── agents/           # Agent implementations
│   ├── models/           # Pydantic data models
│   ├── storage/          # Memory bank and DB logic
│   ├── utils/            # Helper utilities (Gemini, logging, validation)
│   ├── orchestrator.py   # Central message router
│   └── a2a_router.py     # Protocol implementation
├── workflow_showcase.py  # Demo script
├── verify_refactor.py    # System verification script
└── README.md             # This file
```

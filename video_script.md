# ARK Agent AGI - 3 Minute Demo Script

## 0:00 - 0:30: The Problem & Solution
**Visual**: Slide showing "Customer Support Overload" (Chaos) -> "ARK Agent AGI" (Order).
**Voiceover**: 
"Customer support is broken. Agents are drowning in repetitive tickets, and customers are tired of waiting. 
Introducing ARK Agent AGI—an autonomous multi-agent system that doesn't just chat, it *acts*. 
Unlike standard chatbots, ARK uses a team of specialized agents to plan, reason, and execute complex workflows like refunds and technical debugging, entirely on its own."

## 0:30 - 1:00: Architecture & Agents
**Visual**: Architecture Diagram (Hub-and-Spoke) zooming into 'Orchestrator' and 'Specialized Agents'.
**Voiceover**: 
"At the core is our intelligent Orchestrator, which routes tasks using the Agent-to-Agent protocol. 
We have over 15 specialized agents. 
The `SentimentAgent` analyzes emotion. 
The `RefundAgent` checks policies and processes payments. 
And the `SupervisorAgent` ensures quality control before replying.
They all share a persistent Memory Bank using SQLite and FAISS to remember every customer detail."

## 1:00 - 2:00: Live Demo (The "Wow" Factor)
**Visual**: Split screen: Chrome Extension (User) and Terminal/Logs (System).
**Action**: User types: "My order #12345 never arrived and I'm frustrated!"
**Voiceover**: 
"Let's see it in action. A customer reports a missing order via our Chrome Extension.
Watch the logs. 
First, the `SentimentAgent` detects 'Frustration' and flags it as High Priority.
The `Orchestrator` routes it to the `ShippingAgent`.
The agent uses the `ShippingAPI` tool to check the status... sees it's lost... and automatically triggers the `RefundAgent`.
The `RefundAgent` validates the amount against the policy in the database... and processes the refund.
Finally, the `EmailAgent` drafts a personalized apology."

## 2:00 - 2:30: Evaluation & Resilience
**Visual**: Evaluation Summary Table (Metrics) & Cloud Run Dashboard.
**Voiceover**: 
"We didn't just build it; we tested it. Our evaluation harness ran 52 failure scenarios, achieving a 48% baseline intent accuracy with zero-shot learning.
The system is built for resilience, featuring circuit breakers for API failures and a pause/resume mechanism for long-running operations.
It's fully deployed on Google Cloud Run with persistent storage on GCS."

## 2:30 - 3:00: Conclusion
**Visual**: "ARK Agent AGI" Logo + GitHub Link.
**Voiceover**: 
"ARK Agent AGI represents the future of autonomous enterprise support—scalable, intelligent, and empathetic.
Check out the code on GitHub. Thank you."

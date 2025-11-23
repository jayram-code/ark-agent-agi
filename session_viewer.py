"""
Session Viewer CLI for ARK Agent AGI
View session logs and system metrics
"""

import argparse
import json
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from utils.observability.session_logger import session_logger
from utils.observability.metrics import metrics_collector


def list_sessions(args):
    """List all available sessions"""
    sessions = session_logger.list_sessions()
    
    if not sessions:
        print("No sessions found.")
        return
    
    print(f"\nFound {len(sessions)} sessions:\n")
    for session_id in sessions:
        messages = session_logger.get_session(session_id)
        print(f"  {session_id} ({len(messages)} messages)")


def view_session(args):
    """View a specific session"""
    session_id = args.session_id
    messages = session_logger.get_session(session_id)
    
    if not messages:
        print(f"Session {session_id} not found.")
        return
    
    print(f"\n=== Session: {session_id} ({len(messages)} messages) ===\n")
    
    for i, msg in enumerate(messages):
        print(f"[{i+1}] {msg.get('sender', '?')} → {msg.get('receiver', '?')}")
        print(f"    Type: {msg.get('type', '?')}")
        print(f"    Time: {msg.get('timestamp', '?')}")
        
        # Show payload
        payload = msg.get('payload', {})
        if isinstance(payload, dict):
            # Show key fields
            if 'text' in payload:
                print(f"    Text: {payload['text'][:100]}...")
            if 'status' in payload:
                print(f"    Status: {payload['status']}")
            if 'action' in payload:
                print(f"    Action: {payload['action']}")
        
        print()


def show_stats(args):
    """Show system metrics"""
    stats = metrics_collector.get_stats()
    
    if not stats:
        print("No metrics available.")
        return
    
    print("\n=== System Metrics ===\n")
    
    # Show global stats first
    if "_global" in stats:
        global_stats = stats.pop("_global")
        print(f"Global Stats:")
        print(f"  Total Messages: {global_stats['count']}")
        print(f"  Success Rate: {global_stats['success_rate']:.1f}%")
        print(f"  Avg Latency: {global_stats['avg_latency_ms']:.2f}ms")
        print(f"  Total Tokens: {global_stats['total_tokens']}")
        print()
    
    # Show per-agent stats
    print("Per-Agent Stats:")
    for agent_name, agent_stats in sorted(stats.items()):
        print(f"\n  {agent_name}:")
        print(f"    Messages: {agent_stats['count']}")
        print(f"    Success Rate: {agent_stats['success_rate']:.1f}%")
        print(f"    Avg Latency: {agent_stats['avg_latency_ms']:.2f}ms")
        print(f"    Tokens Used: {agent_stats['total_tokens']}")


def main():
    parser = argparse.ArgumentParser(description="ARK Agent Session Viewer")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List sessions
    subparsers.add_parser("list", help="List all sessions")
    
    # View session
    view_parser = subparsers.add_parser("view", help="View a specific session")
    view_parser.add_argument("session_id", help="Session ID to view")
    
    # Show stats
    subparsers.add_parser("stats", help="Show system metrics")
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_sessions(args)
    elif args.command == "view":
        view_session(args)
    elif args.command == "stats":
        show_stats(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

import argparse
import json
import os
import sys
import datetime

QUEUE_PATH = "data/human_queue.json"

def load_queue():
    if not os.path.exists(QUEUE_PATH):
        return []
    try:
        with open(QUEUE_PATH, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_queue(queue):
    with open(QUEUE_PATH, "w") as f:
        json.dump(queue, f, indent=2)

def list_tasks(args):
    queue = load_queue()
    pending = [t for t in queue if t["status"] == "pending"]
    
    if not pending:
        print("No pending tasks.")
        return

    print(f"\nFound {len(pending)} pending tasks:\n")
    for t in pending:
        print(f"ID: {t['id']}")
        print(f"From: {t['original_sender']}")
        print(f"Description: {t['description']}")
        print(f"Context: {json.dumps(t['context'], indent=2)}")
        print(f"Created: {t['created_at']}")
        print("-" * 40)

def approve_task(args):
    _process_task(args.id, "approved", args.feedback)

def reject_task(args):
    _process_task(args.id, "rejected", args.reason)

def _process_task(task_id, decision, feedback):
    queue = load_queue()
    task_found = False
    
    for t in queue:
        if t["id"] == task_id:
            if t["status"] != "pending":
                print(f"Task {task_id} is already {t['status']}.")
                return
            
            t["status"] = decision
            t["feedback"] = feedback
            t["reviewed_at"] = str(datetime.datetime.utcnow())
            task_found = True
            break
    
    if not task_found:
        print(f"Task {task_id} not found.")
        return

    save_queue(queue)
    print(f"Task {task_id} marked as {decision}.")
    print("NOTE: In a real deployment, this CLI would also notify the running Orchestrator/Agent to resume.")
    print("For this implementation, the HumanEscalationAgent will check the queue or receive a signal.")

def main():
    parser = argparse.ArgumentParser(description="Human in the Loop CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List command
    subparsers.add_parser("list", help="List pending tasks")

    # Approve command
    approve_parser = subparsers.add_parser("approve", help="Approve a task")
    approve_parser.add_argument("id", help="Task ID")
    approve_parser.add_argument("--feedback", "-f", default="Approved", help="Optional feedback")

    # Reject command
    reject_parser = subparsers.add_parser("reject", help="Reject a task")
    reject_parser.add_argument("id", help="Task ID")
    reject_parser.add_argument("--reason", "-r", default="Rejected", help="Reason for rejection")

    args = parser.parse_args()

    if args.command == "list":
        list_tasks(args)
    elif args.command == "approve":
        approve_task(args)
    elif args.command == "reject":
        reject_task(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

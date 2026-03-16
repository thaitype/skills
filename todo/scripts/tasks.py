#!/usr/bin/env python3
"""
tasks.py — JSONL-based task manager for Agent Claw todo skill

Usage:
  tasks.py list [--domain DOMAIN] [--priority PRIORITY] [--checked]
  tasks.py add --title TITLE [--due DATE] [--priority P0|P1|P2|P3] [--domain DOMAIN]
  tasks.py update ID [--title TITLE] [--checked BOOL] [--due DATE] [--priority PRIORITY] [--domain DOMAIN]
  tasks.py delete ID
  tasks.py get ID
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_WORKSPACE_ROOT = _SCRIPT_DIR.parents[3]  # scripts → todo → skills → .claude → workspace
TASKS_FILE = Path(os.environ.get("AGENT_TASKS_FILE", str(_WORKSPACE_ROOT / "my-data" / "tasks.jsonl")))

VALID_PRIORITIES = ["P0", "P1", "P2", "P3"]
VALID_DOMAINS = ["Personal", "Work"]


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat()


def load_tasks():
    """Reconstruct current task state from JSONL event log."""
    if not os.path.exists(TASKS_FILE):
        return {}
    tasks = {}
    with open(TASKS_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            tid = obj.get("id")
            if not tid:
                continue
            if obj.get("deleted"):
                tasks.pop(tid, None)
            else:
                tasks[tid] = {**tasks.get(tid, {}), **obj}
    return tasks


def append_event(event: dict):
    os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
    with open(TASKS_FILE, "a") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def resolve_id(tasks, tid_prefix):
    match = [k for k in tasks if k == tid_prefix or k.startswith(tid_prefix)]
    if not match:
        print(f"Task not found: {tid_prefix}", file=sys.stderr)
        sys.exit(1)
    if len(match) > 1:
        print(f"Ambiguous ID prefix: {tid_prefix}", file=sys.stderr)
        sys.exit(1)
    return match[0]


def cmd_list(args):
    tasks = load_tasks()
    items = list(tasks.values())

    if args.domain:
        items = [t for t in items if t.get("domain") == args.domain]
    if args.priority:
        items = [t for t in items if t.get("priority") == args.priority]
    if args.checked:
        items = [t for t in items if t.get("checked") is True]
    elif not args.all:
        # default: hide checked tasks
        items = [t for t in items if not t.get("checked")]

    if not items:
        print("No tasks found.")
        return

    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    items.sort(key=lambda t: (priority_order.get(t.get("priority"), 9), t.get("due_date") or "9999"))

    for t in items:
        check = "x" if t.get("checked") else " "
        due = f"  due:{t['due_date']}" if t.get("due_date") else ""
        print(f"[{check}] [{t.get('priority','--')}] {t['id'][:8]}  {t['title']}"
              f"  [{t.get('domain','?')}]{due}")


def cmd_add(args):
    tid = str(uuid.uuid4())
    ts = now_iso()
    event = {
        "id": tid,
        "title": args.title,
        "checked": False,
        "priority": args.priority or "P3",
        "domain": args.domain or "Personal",
        "due_date": args.due or None,
        "created_at": ts,
        "updated_at": ts,
    }
    append_event(event)
    print(f"Added task {tid[:8]}: {args.title}")


def cmd_update(args):
    tasks = load_tasks()
    tid = resolve_id(tasks, args.id)
    event = {"id": tid, "updated_at": now_iso()}

    if args.title:
        event["title"] = args.title
    if args.checked is not None:
        event["checked"] = args.checked.lower() in ("true", "1", "yes")
    if args.priority:
        if args.priority not in VALID_PRIORITIES:
            print(f"Invalid priority. Choose from: {VALID_PRIORITIES}", file=sys.stderr)
            sys.exit(1)
        event["priority"] = args.priority
    if args.domain:
        if args.domain not in VALID_DOMAINS:
            print(f"Invalid domain. Choose from: {VALID_DOMAINS}", file=sys.stderr)
            sys.exit(1)
        event["domain"] = args.domain
    if args.due is not None:
        event["due_date"] = args.due or None

    append_event(event)
    print(f"Updated task {tid[:8]}")


def cmd_delete(args):
    tasks = load_tasks()
    tid = resolve_id(tasks, args.id)
    append_event({"id": tid, "deleted": True, "updated_at": now_iso()})
    print(f"Deleted task {tid[:8]}: {tasks[tid]['title']}")


def cmd_get(args):
    tasks = load_tasks()
    tid = resolve_id(tasks, args.id)
    print(json.dumps(tasks[tid], ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Todo task manager (JSONL)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # list
    p_list = sub.add_parser("list")
    p_list.add_argument("--domain", choices=VALID_DOMAINS)
    p_list.add_argument("--priority", choices=VALID_PRIORITIES)
    p_list.add_argument("--checked", action="store_true", help="Show only checked tasks")
    p_list.add_argument("--all", action="store_true", help="Show all tasks including checked")

    # add
    p_add = sub.add_parser("add")
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--due", default=None)
    p_add.add_argument("--priority", choices=VALID_PRIORITIES, default="P3")
    p_add.add_argument("--domain", choices=VALID_DOMAINS, default="Personal")

    # update
    p_upd = sub.add_parser("update")
    p_upd.add_argument("id")
    p_upd.add_argument("--title")
    p_upd.add_argument("--checked", help="true/false")
    p_upd.add_argument("--due", default=None)
    p_upd.add_argument("--priority", choices=VALID_PRIORITIES)
    p_upd.add_argument("--domain", choices=VALID_DOMAINS)

    # delete
    p_del = sub.add_parser("delete")
    p_del.add_argument("id")

    # get
    p_get = sub.add_parser("get")
    p_get.add_argument("id")

    args = parser.parse_args()
    {"list": cmd_list, "add": cmd_add, "update": cmd_update,
     "delete": cmd_delete, "get": cmd_get}[args.cmd](args)


if __name__ == "__main__":
    main()

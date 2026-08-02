#!/usr/bin/env python3
"""Personal finance tracker — income, expenses, transfers, and account balances."""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", "..", "..", ".."))
_DEFAULT_DATA_DIR = os.path.join(_WORKSPACE_ROOT, "data", "skills_data", "money")
STATE_DIR = os.environ.get("MONEY_STATE_DIR", _DEFAULT_DATA_DIR)
TRANSACTIONS_FILE = os.path.join(STATE_DIR, "transactions.jsonl")
CATEGORIES_FILE = os.path.join(STATE_DIR, "categories.jsonl")
ACCOUNTS_FILE = os.path.join(STATE_DIR, "accounts.jsonl")
CONFIG_FILE = os.path.join(STATE_DIR, "config.json")

VALID_TX_TYPES = ("income", "expense", "transfer")
VALID_CAT_TYPES = ("income", "expense")
VALID_ACCT_TYPES = ("cash", "bank", "credit")


# ── helpers ──────────────────────────────────────────────────────────────

def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_jsonl(path):
    """Load JSONL event log and replay into a dict keyed by id."""
    items = {}
    if not os.path.exists(path):
        return items
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            event = json.loads(line)
            eid = event.get("id")
            if not eid:
                continue
            if event.get("deleted"):
                items.pop(eid, None)
            elif eid in items:
                items[eid].update(event)
            else:
                items[eid] = event
    return items


def append_event(path, event):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def resolve_id(items, prefix):
    """Resolve a short ID prefix to a full UUID."""
    matches = [k for k in items if k.startswith(prefix)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) == 0:
        print(f"Error: no item found with prefix '{prefix}'", file=sys.stderr)
        sys.exit(1)
    print(f"Error: ambiguous prefix '{prefix}' matches {len(matches)} items", file=sys.stderr)
    sys.exit(1)


def resolve_by_slug(items, slug):
    """Resolve a slug to a full UUID. Falls back to ID prefix match."""
    # exact slug match
    for uid, item in items.items():
        if item.get("slug") == slug:
            return uid
    # fallback: ID prefix match
    matches = [k for k in items if k.startswith(slug)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) == 0:
        return None
    print(f"Error: ambiguous prefix '{slug}' matches {len(matches)} items", file=sys.stderr)
    sys.exit(1)


def slug_exists(items, slug, exclude_id=None):
    """Check if a slug is already taken."""
    for uid, item in items.items():
        if item.get("slug") == slug and uid != exclude_id:
            return True
    return False


def get_slug(items, uid):
    """Get slug for a UUID."""
    item = items.get(uid)
    return item.get("slug", uid[:8]) if item else uid[:8]


def fmt_amount(amount):
    """Format amount with comma separators."""
    if amount == int(amount):
        return f"{int(amount):,}"
    return f"{amount:,.2f}"


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


def load_config():
    """Load config.json, return empty dict if missing."""
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg):
    """Save config.json."""
    os.makedirs(os.path.dirname(CONFIG_FILE) or ".", exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        f.write("\n")


def count_references(uid):
    """Count how many transactions reference this UUID (as category, account, or to_account)."""
    txs = load_jsonl(TRANSACTIONS_FILE)
    return sum(1 for tx in txs.values()
               if tx.get("category") == uid
               or tx.get("account") == uid
               or tx.get("to_account") == uid)


def resolve_category(slug, expected_type=None):
    """Resolve category slug to UUID and validate."""
    cats = load_jsonl(CATEGORIES_FILE)
    uid = resolve_by_slug(cats, slug)
    if not uid:
        print(f"Error: category '{slug}' not found. Use 'category list' to see available categories.", file=sys.stderr)
        sys.exit(1)
    if expected_type and cats[uid].get("type") != expected_type:
        cat_slug = cats[uid].get("slug", slug)
        print(f"Warning: category '{cat_slug}' is type '{cats[uid].get('type')}' but transaction is '{expected_type}'", file=sys.stderr)
    return uid


def resolve_account(slug):
    """Resolve account slug to UUID and validate."""
    accts = load_jsonl(ACCOUNTS_FILE)
    uid = resolve_by_slug(accts, slug)
    if not uid:
        print(f"Error: account '{slug}' not found. Use 'account list' to see available accounts.", file=sys.stderr)
        sys.exit(1)
    return uid


# ── transaction commands ─────────────────────────────────────────────────

def cmd_add(args):
    cat_uid = resolve_category(args.category, args.type)
    acct_uid = resolve_account(args.account)

    cats = load_jsonl(CATEGORIES_FILE)
    accts = load_jsonl(ACCOUNTS_FILE)
    cat_slug = get_slug(cats, cat_uid)
    acct_slug = get_slug(accts, acct_uid)

    tx = {
        "id": str(uuid.uuid4()),
        "date": args.date or today_str(),
        "type": args.type,
        "amount": args.amount,
        "category": cat_uid,
        "account": acct_uid,
        "note": args.note or "",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    append_event(TRANSACTIONS_FILE, tx)
    print(f"Added {args.type}: {fmt_amount(args.amount)} ({cat_slug}) → {acct_slug} [{tx['id'][:8]}]")


def cmd_transfer(args):
    from_uid = resolve_account(args.from_account)
    to_uid = resolve_account(args.to_account)

    accts = load_jsonl(ACCOUNTS_FILE)
    from_slug = get_slug(accts, from_uid)
    to_slug = get_slug(accts, to_uid)

    tx = {
        "id": str(uuid.uuid4()),
        "date": args.date or today_str(),
        "type": "transfer",
        "amount": args.amount,
        "account": from_uid,
        "to_account": to_uid,
        "category": "",
        "note": args.note or "",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    append_event(TRANSACTIONS_FILE, tx)
    print(f"Transfer: {fmt_amount(args.amount)} {from_slug} → {to_slug} [{tx['id'][:8]}]")


def cmd_list(args):
    txs = load_jsonl(TRANSACTIONS_FILE)
    cats = load_jsonl(CATEGORIES_FILE)
    accts = load_jsonl(ACCOUNTS_FILE)

    items = sorted(txs.values(), key=lambda x: (x.get("date", ""), x.get("created_at", "")), reverse=True)

    # resolve filter slugs to UUIDs
    filter_cat_uid = None
    if args.category:
        filter_cat_uid = resolve_by_slug(cats, args.category)
    filter_acct_uid = None
    if args.account:
        filter_acct_uid = resolve_by_slug(accts, args.account)

    # filters
    if args.type:
        items = [t for t in items if t.get("type") == args.type]
    if filter_cat_uid:
        items = [t for t in items if t.get("category") == filter_cat_uid]
    if filter_acct_uid:
        items = [t for t in items if t.get("account") == filter_acct_uid or t.get("to_account") == filter_acct_uid]
    if args.from_date:
        items = [t for t in items if t.get("date", "") >= args.from_date]
    if args.to_date:
        items = [t for t in items if t.get("date", "") <= args.to_date]

    items = items[: args.limit]

    if not items:
        print("No transactions found.")
        return

    for t in items:
        tid = t["id"][:8]
        date = t.get("date", "")
        ttype = t.get("type", "")
        amount = fmt_amount(t.get("amount", 0))
        cat = get_slug(cats, t.get("category", "")) if t.get("category") else ""
        acct = get_slug(accts, t.get("account", ""))
        note = t.get("note", "")

        if ttype == "transfer":
            to_acct = get_slug(accts, t.get("to_account", ""))
            line = f"[{tid}] {date}  transfer  {amount}  {acct} → {to_acct}"
        elif ttype == "income":
            line = f"[{tid}] {date}  +{amount}  {cat}  {acct}"
        else:
            line = f"[{tid}] {date}  -{amount}  {cat}  {acct}"

        if note:
            line += f"  ({note})"
        print(line)


def cmd_delete(args):
    txs = load_jsonl(TRANSACTIONS_FILE)
    full_id = resolve_id(txs, args.id)
    tx = txs[full_id]

    event = {"id": full_id, "deleted": True, "updated_at": now_iso()}
    append_event(TRANSACTIONS_FILE, event)
    print(f"Deleted: [{full_id[:8]}] {tx.get('type')} {fmt_amount(tx.get('amount', 0))}")


def cmd_summary(args):
    txs = load_jsonl(TRANSACTIONS_FILE)
    cats = load_jsonl(CATEGORIES_FILE)
    items = list(txs.values())

    # filter by month
    if args.month:
        items = [t for t in items if t.get("date", "").startswith(args.month)]

    # filter by category slug
    if args.category:
        cat_uid = resolve_by_slug(cats, args.category)
        if cat_uid:
            items = [t for t in items if t.get("category") == cat_uid]

    total_income = sum(t.get("amount", 0) for t in items if t.get("type") == "income")
    total_expense = sum(t.get("amount", 0) for t in items if t.get("type") == "expense")
    net = total_income - total_expense

    print(f"Income:   {fmt_amount(total_income)}")
    print(f"Expense:  {fmt_amount(total_expense)}")
    print(f"Net:      {fmt_amount(net)}")

    # breakdown by category, grouped by category_group
    by_group = {}
    for t in items:
        if t.get("type") in ("income", "expense"):
            cat_uid = t.get("category", "")
            cat_slug = get_slug(cats, cat_uid) if cat_uid else "uncategorized"
            cat_data = cats.get(cat_uid, {})
            group = cat_data.get("category_group", "") or "Ungrouped"
            icon = cat_data.get("icon", "")
            display_cat = f"{icon} {cat_slug}" if icon else cat_slug
            by_group.setdefault(group, {})
            key = (t["type"], display_cat)
            by_group[group][key] = by_group[group].get(key, 0) + t.get("amount", 0)

    if by_group:
        print("\nBreakdown:")
        for group_name in sorted(by_group.keys(), key=lambda g: (g == "Ungrouped", g)):
            print(f"  {group_name}:")
            for (ttype, cat), amount in sorted(by_group[group_name].items()):
                sign = "+" if ttype == "income" else "-"
                print(f"    {sign}{fmt_amount(amount)}  {cat}")


def cmd_balance(args):
    accts = load_jsonl(ACCOUNTS_FILE)
    txs = load_jsonl(TRANSACTIONS_FILE)

    if not accts:
        print("No accounts found. Use 'account add' to create one.")
        return

    balances = {}
    for aid, acct in accts.items():
        balances[aid] = acct.get("initial_balance", 0)

    for tx in txs.values():
        ttype = tx.get("type")
        amount = tx.get("amount", 0)
        acct = tx.get("account", "")

        if ttype == "income" and acct in balances:
            if accts[acct].get("type") == "credit":
                balances[acct] -= amount
            else:
                balances[acct] += amount
        elif ttype == "expense" and acct in balances:
            if accts[acct].get("type") == "credit":
                balances[acct] += amount
            else:
                balances[acct] -= amount
        elif ttype == "transfer":
            if acct in balances:
                if accts[acct].get("type") == "credit":
                    balances[acct] += amount
                else:
                    balances[acct] -= amount
            to_acct = tx.get("to_account", "")
            if to_acct in balances:
                if accts[to_acct].get("type") == "credit":
                    balances[to_acct] -= amount
                else:
                    balances[to_acct] += amount

    assets = []
    liabilities = []
    for aid, bal in balances.items():
        name = accts[aid].get("name", aid)
        slug = accts[aid].get("slug", aid[:8])
        atype = accts[aid].get("type", "")
        icon = accts[aid].get("icon", "")
        entry = (slug, name, atype, bal, icon)
        if atype == "credit":
            liabilities.append(entry)
        else:
            assets.append(entry)

    total_assets = 0
    if assets:
        print("Assets:")
        for slug, name, atype, bal, icon in assets:
            display_name = f"{icon} {name}" if icon else name
            print(f"  {display_name} [{slug}] ({atype}): {fmt_amount(bal)}")
            total_assets += bal

    total_liabilities = 0
    if liabilities:
        print("Liabilities:")
        for slug, name, atype, bal, icon in liabilities:
            display_name = f"{icon} {name}" if icon else name
            print(f"  {display_name} [{slug}] ({atype}): {fmt_amount(bal)}")
            total_liabilities += bal

    net_worth = total_assets - total_liabilities
    print(f"\nNet worth: {fmt_amount(net_worth)}")


# ── category commands ────────────────────────────────────────────────────

def cmd_category(args):
    if args.subcmd == "add":
        cmd_category_add(args)
    elif args.subcmd == "list":
        cmd_category_list(args)
    elif args.subcmd == "update":
        cmd_category_update(args)
    elif args.subcmd == "remove":
        cmd_category_remove(args)
    else:
        print("Usage: money.py category {add,list,update,remove}")
        sys.exit(1)


def cmd_category_add(args):
    cats = load_jsonl(CATEGORIES_FILE)
    if slug_exists(cats, args.slug):
        print(f"Error: category slug '{args.slug}' already exists.", file=sys.stderr)
        sys.exit(1)
    if args.type not in VALID_CAT_TYPES:
        print(f"Error: type must be one of {VALID_CAT_TYPES}", file=sys.stderr)
        sys.exit(1)

    cat = {
        "id": str(uuid.uuid4()),
        "slug": args.slug,
        "name": args.name,
        "type": args.type,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    for field in ("icon", "category_group"):
        val = getattr(args, field, None)
        if val:
            cat[field] = val
    append_event(CATEGORIES_FILE, cat)
    print(f"Added category: {args.slug} ({args.name}) [{args.type}] [{cat['id'][:8]}]")


def cmd_category_list(args):
    cats = load_jsonl(CATEGORIES_FILE)
    if not cats:
        print("No categories found.")
        return
    groups = {}
    for cid, cat in sorted(cats.items(), key=lambda x: x[1].get("slug", "")):
        group = cat.get("category_group", "") or "Ungrouped"
        groups.setdefault(group, []).append(cat)
    for group_name in sorted(groups.keys(), key=lambda g: (g == "Ungrouped", g)):
        print(f"{group_name}:")
        for cat in groups[group_name]:
            slug = cat.get("slug", cat["id"][:8])
            name = cat.get("name", "")
            ctype = cat.get("type", "")
            icon = cat.get("icon", "")
            display_name = f"{icon} {name}" if icon else name
            print(f"  {slug}: {display_name} [{ctype}]")


def cmd_category_update(args):
    cats = load_jsonl(CATEGORIES_FILE)
    uid = resolve_by_slug(cats, args.slug)
    if not uid:
        print(f"Error: category '{args.slug}' not found.", file=sys.stderr)
        sys.exit(1)

    event = {"id": uid, "updated_at": now_iso()}
    if args.name:
        event["name"] = args.name
    if args.new_slug:
        if slug_exists(cats, args.new_slug, exclude_id=uid):
            print(f"Error: slug '{args.new_slug}' already taken.", file=sys.stderr)
            sys.exit(1)
        event["slug"] = args.new_slug
    for field in ("icon", "category_group"):
        val = getattr(args, field, None)
        if val is not None:
            event[field] = val

    if len(event) <= 2:
        print("Nothing to update. Use --name, --new-slug, --icon, or --group.", file=sys.stderr)
        sys.exit(1)

    append_event(CATEGORIES_FILE, event)
    slug = args.new_slug or args.slug
    print(f"Updated category: {slug}")


def cmd_category_remove(args):
    cats = load_jsonl(CATEGORIES_FILE)
    uid = resolve_by_slug(cats, args.slug)
    if not uid:
        print(f"Error: category '{args.slug}' not found.", file=sys.stderr)
        sys.exit(1)
    ref_count = count_references(uid)
    if ref_count > 0 and not args.force:
        print(f"Warning: category '{args.slug}' is referenced by {ref_count} transaction(s). Use --force to remove anyway.", file=sys.stderr)
        sys.exit(1)
    event = {"id": uid, "deleted": True, "updated_at": now_iso()}
    append_event(CATEGORIES_FILE, event)
    print(f"Removed category: {args.slug}")


# ── account commands ─────────────────────────────────────────────────────

def cmd_account(args):
    if args.subcmd == "add":
        cmd_account_add(args)
    elif args.subcmd == "list":
        cmd_account_list(args)
    elif args.subcmd == "update":
        cmd_account_update(args)
    elif args.subcmd == "remove":
        cmd_account_remove(args)
    else:
        print("Usage: money.py account {add,list,update,remove}")
        sys.exit(1)


def cmd_account_add(args):
    accts = load_jsonl(ACCOUNTS_FILE)
    if slug_exists(accts, args.slug):
        print(f"Error: account slug '{args.slug}' already exists.", file=sys.stderr)
        sys.exit(1)
    if args.type not in VALID_ACCT_TYPES:
        print(f"Error: type must be one of {VALID_ACCT_TYPES}", file=sys.stderr)
        sys.exit(1)

    acct = {
        "id": str(uuid.uuid4()),
        "slug": args.slug,
        "name": args.name,
        "type": args.type,
        "initial_balance": args.balance,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    for field in ("icon", "provider", "alias", "last_4_digit", "note"):
        val = getattr(args, field, None)
        if val:
            acct[field] = val
    append_event(ACCOUNTS_FILE, acct)
    print(f"Added account: {args.slug} ({args.name}) [{args.type}] balance={fmt_amount(args.balance)} [{acct['id'][:8]}]")


def cmd_account_list(args):
    accts = load_jsonl(ACCOUNTS_FILE)
    if not accts:
        print("No accounts found.")
        return
    for aid, acct in sorted(accts.items(), key=lambda x: x[1].get("slug", "")):
        slug = acct.get("slug", aid[:8])
        name = acct.get("name", "")
        atype = acct.get("type", "")
        bal = fmt_amount(acct.get("initial_balance", 0))
        icon = acct.get("icon", "")
        display_name = f"{icon} {name}" if icon else name
        print(f"  {slug}: {display_name} [{atype}] initial={bal}")
        details = []
        provider = acct.get("provider", "")
        alias = acct.get("alias", "")
        if provider and alias:
            details.append(f"{provider} ({alias})")
        elif provider:
            details.append(provider)
        elif alias:
            details.append(alias)
        last4 = acct.get("last_4_digit", "")
        if last4:
            details.append(f"****{last4}")
        note = acct.get("note", "")
        if note:
            details.append(f"note: {note}")
        if details:
            print(f"       {' | '.join(details)}")


def cmd_account_update(args):
    accts = load_jsonl(ACCOUNTS_FILE)
    uid = resolve_by_slug(accts, args.slug)
    if not uid:
        print(f"Error: account '{args.slug}' not found.", file=sys.stderr)
        sys.exit(1)

    event = {"id": uid, "updated_at": now_iso()}
    if args.name:
        event["name"] = args.name
    if args.new_slug:
        if slug_exists(accts, args.new_slug, exclude_id=uid):
            print(f"Error: slug '{args.new_slug}' already taken.", file=sys.stderr)
            sys.exit(1)
        event["slug"] = args.new_slug
    for field in ("icon", "provider", "alias", "last_4_digit", "note"):
        val = getattr(args, field, None)
        if val is not None:
            event[field] = val

    if len(event) <= 2:
        print("Nothing to update. Use --name, --new-slug, --icon, --provider, --alias, --last-4-digit, or --note.", file=sys.stderr)
        sys.exit(1)

    append_event(ACCOUNTS_FILE, event)
    slug = args.new_slug or args.slug
    print(f"Updated account: {slug}")


def cmd_account_remove(args):
    accts = load_jsonl(ACCOUNTS_FILE)
    uid = resolve_by_slug(accts, args.slug)
    if not uid:
        print(f"Error: account '{args.slug}' not found.", file=sys.stderr)
        sys.exit(1)
    ref_count = count_references(uid)
    if ref_count > 0 and not args.force:
        print(f"Warning: account '{args.slug}' is referenced by {ref_count} transaction(s). Use --force to remove anyway.", file=sys.stderr)
        sys.exit(1)
    event = {"id": uid, "deleted": True, "updated_at": now_iso()}
    append_event(ACCOUNTS_FILE, event)
    print(f"Removed account: {args.slug}")


# ── adjust commands ──────────────────────────────────────────────────────

def cmd_adjust(args):
    if args.subcmd == "setup":
        cmd_adjust_setup(args)
    elif args.subcmd == "set":
        cmd_adjust_set(args)
    elif args.subcmd == "stale":
        cmd_adjust_stale(args)
    else:
        print("Usage: money.py adjust {setup,set,stale}")
        sys.exit(1)


def cmd_adjust_setup(args):
    cats = load_jsonl(CATEGORIES_FILE)
    cfg = load_config()

    # Check if manual-adjustment category exists
    adj_uid = resolve_by_slug(cats, "manual-adjustment")
    if not adj_uid:
        # Create it
        adj_uid = str(uuid.uuid4())
        cat = {
            "id": adj_uid,
            "slug": "manual-adjustment",
            "name": "Manual Balance Adjustment",
            "type": "expense",
            "icon": "⚖️",
            "category_group": "Adjustment",
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
        append_event(CATEGORIES_FILE, cat)
        print(f"Created category: manual-adjustment [{adj_uid[:8]}]")
    else:
        print(f"Category manual-adjustment already exists [{adj_uid[:8]}]")

    cfg["adjust_category_id"] = adj_uid
    save_config(cfg)
    print(f"Config saved: adjust_category_id = {adj_uid[:8]}")


def cmd_adjust_set(args):
    cfg = load_config()
    adj_cat_id = cfg.get("adjust_category_id")
    if not adj_cat_id:
        print("Error: run 'adjust setup' first to configure adjustment category.", file=sys.stderr)
        sys.exit(1)

    accts = load_jsonl(ACCOUNTS_FILE)
    uid = resolve_by_slug(accts, args.account)
    if not uid:
        print(f"Error: account '{args.account}' not found.", file=sys.stderr)
        sys.exit(1)

    acct = accts[uid]
    slug = acct.get("slug", uid[:8])
    acct_type = acct.get("type", "")

    # Calculate current balance
    txs = load_jsonl(TRANSACTIONS_FILE)
    current = acct.get("initial_balance", 0)
    is_credit = acct_type == "credit"
    for tx in txs.values():
        ttype = tx.get("type")
        amount = tx.get("amount", 0)
        tx_acct = tx.get("account", "")
        if ttype == "income" and tx_acct == uid:
            current += -amount if is_credit else amount
        elif ttype == "expense" and tx_acct == uid:
            current += amount if is_credit else -amount
        elif ttype == "transfer":
            if tx_acct == uid:
                current += amount if is_credit else -amount
            if tx.get("to_account") == uid:
                current += -amount if is_credit else amount

    actual = args.actual_balance
    diff = actual - current

    if abs(diff) < 0.01:
        print(f"{slug}: balance is already correct ({fmt_amount(current)})")
    else:
        # Create adjustment transaction
        if acct_type == "credit":
            # For credit: actual > current means more debt (expense), actual < current means less debt (income)
            if diff > 0:
                tx_type = "expense"
                tx_amount = diff
            else:
                tx_type = "income"
                tx_amount = abs(diff)
        else:
            # For non-credit: actual > current means gained money (income), actual < current means lost money (expense)
            if diff > 0:
                tx_type = "income"
                tx_amount = diff
            else:
                tx_type = "expense"
                tx_amount = abs(diff)

        tx = {
            "id": str(uuid.uuid4()),
            "date": args.date or today_str(),
            "type": tx_type,
            "amount": tx_amount,
            "category": adj_cat_id,
            "account": uid,
            "note": f"adjust: {fmt_amount(current)} → {fmt_amount(actual)}",
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
        append_event(TRANSACTIONS_FILE, tx)
        sign = "+" if diff > 0 else ""
        print(f"{slug}: {fmt_amount(current)} → {fmt_amount(actual)} ({sign}{fmt_amount(diff)}) [{tx['id'][:8]}]")

    # Update last_adjusted_at on account
    event = {"id": uid, "last_adjusted_at": now_iso(), "updated_at": now_iso()}
    append_event(ACCOUNTS_FILE, event)


def cmd_adjust_stale(args):
    accts = load_jsonl(ACCOUNTS_FILE)
    if not accts:
        print("No accounts found.")
        return

    threshold_days = args.days
    now = datetime.now(timezone.utc)
    stale = []

    for aid, acct in accts.items():
        last = acct.get("last_adjusted_at")
        slug = acct.get("slug", aid[:8])
        name = acct.get("name", "")
        icon = acct.get("icon", "")
        if last:
            last_dt = datetime.fromisoformat(last)
            days_ago = (now - last_dt).days
            if days_ago >= threshold_days:
                stale.append((slug, name, icon, f"{days_ago} days ago"))
        else:
            stale.append((slug, name, icon, "never"))

    if not stale:
        print(f"All accounts adjusted within {threshold_days} days.")
        return

    print(f"Accounts not adjusted in {threshold_days}+ days:")
    for slug, name, icon, age in sorted(stale, key=lambda x: x[0]):
        display_name = f"{icon} {name}" if icon else name
        print(f"  {slug}: {display_name} — last adjusted: {age}")


# ── CLI ──────────────────────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(description="Personal finance tracker")
    sub = parser.add_subparsers(dest="command")

    # add
    p_add = sub.add_parser("add", help="Add income or expense")
    p_add.add_argument("--type", required=True, choices=["income", "expense"])
    p_add.add_argument("--amount", required=True, type=float)
    p_add.add_argument("--category", required=True, help="Category slug")
    p_add.add_argument("--account", required=True, help="Account slug")
    p_add.add_argument("--date")
    p_add.add_argument("--note", default="")

    # transfer
    p_tr = sub.add_parser("transfer", help="Transfer between accounts")
    p_tr.add_argument("--amount", required=True, type=float)
    p_tr.add_argument("--from", dest="from_account", required=True, help="Source account slug")
    p_tr.add_argument("--to", dest="to_account", required=True, help="Destination account slug")
    p_tr.add_argument("--date")
    p_tr.add_argument("--note", default="")

    # list
    p_ls = sub.add_parser("list", help="List transactions")
    p_ls.add_argument("--type", choices=["income", "expense", "transfer"])
    p_ls.add_argument("--category", help="Filter by category slug")
    p_ls.add_argument("--account", help="Filter by account slug")
    p_ls.add_argument("--from-date")
    p_ls.add_argument("--to-date")
    p_ls.add_argument("--limit", type=int, default=20)

    # delete
    p_del = sub.add_parser("delete", help="Delete a transaction")
    p_del.add_argument("id", help="Transaction ID prefix (8 chars)")

    # summary
    p_sum = sub.add_parser("summary", help="Income vs expense summary")
    p_sum.add_argument("--month", help="YYYY-MM")
    p_sum.add_argument("--category", help="Filter by category slug")

    # balance
    sub.add_parser("balance", help="Account balances")

    # category
    p_cat = sub.add_parser("category", help="Manage categories")
    cat_sub = p_cat.add_subparsers(dest="subcmd")

    p_cat_add = cat_sub.add_parser("add")
    p_cat_add.add_argument("--slug", required=True, help="Short identifier (e.g. food)")
    p_cat_add.add_argument("--name", required=True, help="Display name (e.g. อาหาร)")
    p_cat_add.add_argument("--type", required=True, choices=["income", "expense"])
    p_cat_add.add_argument("--icon", default="", help="Emoji icon for display (e.g. 🍕)")
    p_cat_add.add_argument("--group", dest="category_group", default="", help="Category group (e.g. Fixed Expenses)")

    cat_sub.add_parser("list")

    p_cat_upd = cat_sub.add_parser("update")
    p_cat_upd.add_argument("slug", help="Current slug")
    p_cat_upd.add_argument("--name", help="New display name")
    p_cat_upd.add_argument("--new-slug", help="New slug")
    p_cat_upd.add_argument("--icon", default=None, help="Emoji icon for display")
    p_cat_upd.add_argument("--group", dest="category_group", default=None, help="Category group")

    p_cat_rm = cat_sub.add_parser("remove")
    p_cat_rm.add_argument("slug", help="Category slug")
    p_cat_rm.add_argument("--force", action="store_true", help="Remove even if referenced by transactions")

    # account
    p_acct = sub.add_parser("account", help="Manage accounts")
    acct_sub = p_acct.add_subparsers(dest="subcmd")

    p_acct_add = acct_sub.add_parser("add")
    p_acct_add.add_argument("--slug", required=True, help="Short identifier (e.g. main-bank)")
    p_acct_add.add_argument("--name", required=True, help="Display name (e.g. Main Bank)")
    p_acct_add.add_argument("--type", required=True, choices=["cash", "bank", "credit"])
    p_acct_add.add_argument("--balance", type=float, default=0)
    p_acct_add.add_argument("--icon", default="", help="Emoji icon for display (e.g. 🏦)")
    p_acct_add.add_argument("--provider", default="", help="English institution name (e.g. Example Bank)")
    p_acct_add.add_argument("--alias", default="", help="Local name of provider, if different")
    p_acct_add.add_argument("--last-4-digit", dest="last_4_digit", default="", help="Last 4 digits of account/card number")
    p_acct_add.add_argument("--note", default="", help="Remarks about this account")

    acct_sub.add_parser("list")

    p_acct_upd = acct_sub.add_parser("update")
    p_acct_upd.add_argument("slug", help="Current slug")
    p_acct_upd.add_argument("--name", help="New display name")
    p_acct_upd.add_argument("--new-slug", help="New slug")
    p_acct_upd.add_argument("--icon", default=None, help="Emoji icon for display")
    p_acct_upd.add_argument("--provider", default=None, help="English institution name")
    p_acct_upd.add_argument("--alias", default=None, help="Local name of provider")
    p_acct_upd.add_argument("--last-4-digit", dest="last_4_digit", default=None, help="Last 4 digits of account/card number")
    p_acct_upd.add_argument("--note", default=None, help="Remarks about this account")

    p_acct_rm = acct_sub.add_parser("remove")
    p_acct_rm.add_argument("slug", help="Account slug")
    p_acct_rm.add_argument("--force", action="store_true", help="Remove even if referenced by transactions")

    # adjust
    p_adj = sub.add_parser("adjust", help="Adjust account balance to match reality")
    adj_sub = p_adj.add_subparsers(dest="subcmd")

    adj_sub.add_parser("setup", help="Configure adjustment category")

    p_adj_set = adj_sub.add_parser("set", help="Set actual balance for an account")
    p_adj_set.add_argument("account", help="Account slug")
    p_adj_set.add_argument("actual_balance", type=float, help="Actual balance in the real account")
    p_adj_set.add_argument("--date", help="Date of adjustment (YYYY-MM-DD, defaults to today)")

    p_adj_stale = adj_sub.add_parser("stale", help="Show accounts not adjusted recently")
    p_adj_stale.add_argument("--days", type=int, default=7, help="Threshold in days (default: 7)")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "add": cmd_add,
        "transfer": cmd_transfer,
        "list": cmd_list,
        "delete": cmd_delete,
        "summary": cmd_summary,
        "balance": cmd_balance,
        "category": cmd_category,
        "account": cmd_account,
        "adjust": cmd_adjust,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()

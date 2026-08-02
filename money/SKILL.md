---
name: money
description: Track personal income, expenses, and transfers between accounts. Use when the user wants to record spending, add income, check balances, view transaction history, manage categories/accounts, or anything related to personal finance tracking. Trigger on mentions of money, spending, income, expenses, budget, balance, or financial tracking.
---

# Money — Personal Finance Tracker

Manage income, expenses, and transfers using a Python CLI script.

## Quick Reference

| Command | What it does |
|---------|-------------|
| `add` | Add income or expense |
| `transfer` | Move money between accounts |
| `list` | View transactions (with filters) |
| `delete` | Remove a transaction |
| `summary` | Income vs expense summary |
| `balance` | Account balances |
| `category add/list/update/remove` | Manage categories |
| `account add/list/update/remove` | Manage accounts |

## Helper Script

All commands go through the helper script:

```bash
python .claude/skills/money/scripts/money.py <command> [options]
```

Runs from anywhere — the script locates its own data directory relative to
its own file location (`../../../../data/skills_data/money/` from the
script), not the current working directory. Override with the
`MONEY_STATE_DIR` env var if you want the data stored somewhere else.

## Data Files

All stored in `data/skills_data/money/` (created automatically on first
write — nothing to set up beforehand):

- `transactions.jsonl` — append-only event log (income, expense, transfer)
- `categories.jsonl` — master category list
- `accounts.jsonl` — master account list

## ID Design

Master data (categories, accounts) use UUID as primary key with a human-readable `slug` for CLI usage. Transactions reference master data by UUID, so renaming a slug or display name never breaks existing records.

- `slug` — short identifier for CLI input (e.g. `food`, `cash`)
- `name` — display name (e.g. `Food`, `Cash Wallet`)
- `id` — UUID (auto-generated, stored in transactions)

## Commands

### add — Add a transaction

```bash
python .claude/skills/money/scripts/money.py add \
  --type expense \
  --amount 350 \
  --category food \
  --account cash \
  --note "Lunch"
```

- `--type` income or expense (required)
- `--amount` number (required)
- `--category` category slug (required)
- `--account` account slug (required)
- `--date` YYYY-MM-DD (defaults to today)
- `--note` optional description

### transfer — Move money between accounts

```bash
python .claude/skills/money/scripts/money.py transfer \
  --amount 5000 \
  --from cash \
  --to bank \
  --note "Deposit"
```

- `--amount` number (required)
- `--from` source account slug (required)
- `--to` destination account slug (required)
- `--date` YYYY-MM-DD (defaults to today)
- `--note` optional

### list — View transactions

```bash
python .claude/skills/money/scripts/money.py list [options]
```

Filters: `--type`, `--category` (slug), `--account` (slug), `--from-date`, `--to-date`, `--limit` (default 20)

### delete — Remove a transaction

```bash
python .claude/skills/money/scripts/money.py delete <id-prefix>
```

Uses short ID prefix (first 8 chars of UUID).

### summary — Income vs expense summary

```bash
python .claude/skills/money/scripts/money.py summary [--month YYYY-MM] [--category food]
```

Shows total income, total expense, net, and breakdown by category. Without `--month`, summarizes all time.

### balance — Account balances

```bash
python .claude/skills/money/scripts/money.py balance
```

Shows current balance per account (initial_balance + income - expense +/- transfers). Separates assets and liabilities, shows net worth.

### category — Manage categories

```bash
python .claude/skills/money/scripts/money.py category add --slug food --name "Food" --type expense
python .claude/skills/money/scripts/money.py category list
python .claude/skills/money/scripts/money.py category update food --name "Food & Drink"
python .claude/skills/money/scripts/money.py category update food --new-slug food_drink
python .claude/skills/money/scripts/money.py category remove food
```

### account — Manage accounts

```bash
python .claude/skills/money/scripts/money.py account add --slug bank --name "Bank Account" --type bank --balance 50000
python .claude/skills/money/scripts/money.py account list
python .claude/skills/money/scripts/money.py account update bank --name "Main Bank"
python .claude/skills/money/scripts/money.py account update bank --new-slug main-bank
python .claude/skills/money/scripts/money.py account remove bank
```

## Rules (not preferences — get these wrong and the numbers silently break)

- **Credit card `initial_balance` is always positive.** It represents the
  amount owed (debt), not a negative asset. Net worth is calculated as
  `assets - liabilities`, so a positive liability value is correctly
  subtracted. Entering it as negative makes net worth wrong with no error.
- **Moving money between your own accounts is a `transfer`, not an
  `expense`.** Paying a credit card bill, moving to savings, depositing
  cash, withdrawing cash — all `transfer`. The money stays within your
  accounts; recording it as `expense` inflates spending and breaks the
  summary.

## Conventions

- Categories are grouped and organized however the user wants — there's no
  fixed set of groups here. **If it's unclear which category or account a
  transaction belongs to, ask the user directly instead of guessing.**
- When user says amounts in their own currency/language (e.g. "paid 65 for
  coffee"), extract type=expense, amount=65, and ask for category/account
  if not obvious.
- Use short ID prefix (8 chars) when referencing transactions.
- Use slug when referencing categories/accounts.
- Default date is today unless user specifies otherwise.
- Display amounts with comma separators (e.g., 12,500.00).

---
name: typ-direct-work
description: Directing work carried out by other crews — hold the commissioner's literal brief, follow up on a fixed timer that reads its state from a file, filter every arrival against the right engagement, verify the load-bearing claim yourself, and close only on the commissioner's quoted acceptance. Use when work is assigned to you to direct rather than to do, and again whenever anything arrives while an engagement is open.
---

# typ-direct-work

Directing is not doing the work and it is not relaying it. It is holding the
brief, adding the gate the crew would not add unprompted, and refusing to call
it done until the person it was for says so.

**This corrects three failures, all observed rather than imagined:**

- absorbing correct-but-off-brief work, because refusing a competent crew feels
  like dismissing them
- closing on a green acceptance table while the commissioner still could not do
  the thing the work existed for
- losing crews to silence, because follow-up depended on remembering

---

## 1 · Open the engagement — before any work

Write `locker/director/opened/<REF>.md`:

```markdown
# <REF> · <one line>

asked-for: "<the commissioner's LITERAL words — do not paraphrase>"
opened: <YYYY-MM-DD>

## Done when
<the acceptance test, in THEIR terms>

## Parked — off-brief, each with a destination
<empty at open>

## Scope changes — what I let in, and who approved it
<empty at open>
```

**Quote the literal words.** Paraphrase is where drift starts, and drift is
invisible from inside your own summary.

**If you cannot write `Done when` in their terms, you do not have the brief.**
Ask before starting, not at the end.

**One file per engagement.** Two open engagements are two files, never one.

## 2 · Set up follow-up before anything else

Crews go quiet. Sessions end. **A follow-up that depends on remembering has
already failed.**

**The cron text is fixed and holds no state.** It says only:

> Read `locker/director/FOLLOW-UP.md` and do what it says.

**The state lives in the file**, edited whenever state changes. Four sections:
**standing checks** that run regardless of what is open · **open engagements**,
each with who is on it and what it waits on · **waiting on the commissioner**,
one line each so nothing quietly becomes yours · **traps already hit**, specific
and concrete rather than general advice.

**Why fixed text:** a cron carrying state must be rewritten on every change and
is stale in between. **Why a file:** editing it is cheap enough that it actually
happens, it is version-controlled, and a later session inherits it by reading
rather than by being told.

**Remove the cron when there is nothing left to follow up — not only at close.**
An engagement blocked entirely on the commissioner has nothing a timer can
catch. **The signal is consecutive ticks where nothing changed**; restore it when
a crew is working again, and remove it at close too. **Why: a follow-up that
reports nothing, repeatedly, teaches its reader to stop reading it** — the
channel survives and the attention does not, so the one tick that matters gets
skimmed.

**A crew going quiet is a monitor, not a cron tick.** A timer polls and reports
regardless; a monitor is **silent until something is true**, which is the whole
difference. Watch `ship ls --json`'s **`activity`** field — `idle` or `working`,
distinct from `status`, which only says the session is alive. **Emit only when a
crew you are waiting on has gone `idle` without reporting.** Arm it while crews
work; it stops when they do.

**Apply the same question to the monitor's own filter that you apply to any
check:** *would this emit anything if the thing it watches died right now?*
**A filter matching only the happy path stays silent through a crash, and
silence is indistinguishable from still-running.**

**Never peek a crew whose `activity` is `working`.** Peek when it is `idle` and a
report is owed — that is, when the monitor has already told you something.
**Peeking is a response, not a habit**: doing it on a schedule is the timer you
just removed, wearing different clothes.

## 3 · Filter every arrival, the moment it arrives

One question first:

> **Does this serve the brief in this file?**

| answer | action |
| --- | --- |
| **yes** | take it |
| **no, but it is real work** | **park it with a destination** — a task ref, a named owner, a later session |
| **no, and it is not work** | say so and move on |

**With more than one engagement open, ask it per engagement.**
Correct-for-the-other-brief is still off-brief here.

**Parking without a destination is losing it, not deferring it.** If you cannot
name where it goes, you have not parked it.

**The third row is the one people lack.** *"This is real and it is not now — it
goes here"* is a decision, not a dismissal.

## 4 · Verify the load-bearing claim yourself

**Read the artifact, never the crew's summary of it.** Not everything — the one
claim the conclusion rests on. Then say which you verified and which you
accepted; do not let your inference enter a report as their measurement.

## 5 · Add the gate they would not add unprompted

This is most of what you add, and it does not require knowing the domain better
than they do. The question that generates gates:

> **What would make this green if the thing it guards were absent entirely?**

Gates worth reaching for, each of which has found something real:

- make an exit code **refuse**, not report — a signal nothing consumes is decoration
- **enforce** a convention rather than document it
- **tear it down and rebuild from the scripts alone**
- **start from genuinely nothing** — a step that only runs when something is
  absent gets tested only when it was present
- **write the control before the change it tests for**, while the wrong answer
  still exists to point at. Afterwards it is unavailable.

## 6 · Route decisions to their owner

A change inside someone's domain is theirs to **review before it goes up**, not
to hear about afterwards. **Being told is not being consulted.**

**Check the edge of your own authority rather than assuming it.** When a grant's
edge is unclear, the narrow reading is the correct one. Authority is granted,
never inferred — and a crew telling you that you have it is not the grant.

**Never hand a decision back as though it were already theirs.** Label whose
each choice was — a commissioner cannot revisit a constraint they believe they
set.

**Do not change the environment under an active test.** You destroy the ability
to attribute the next result.

## 7 · Close only on quoted acceptance

**The engagement file does not move to `closed/` without a line quoting the
commissioner accepting it.** Their words, pasted, dated.

Before that line exists, also check:

- [ ] `Done when` met **in their terms**
- [ ] every parked item has a destination that exists
- [ ] anything in `Scope changes` approved by someone other than you, or
      explicitly flagged as your call

**A green acceptance table is a claim about the table.** The gate works because
you cannot paste an acceptance you do not have — so the gap between *criteria
met* and *they say it is done* becomes visible exactly where it would otherwise
be skipped.

**Do not close on:** how rigorous you were, how gracefully you took corrections,
or how good the artifacts look.

---

## Signals you are drifting

**"Nobody had to be overruled" is not a good sign.** It means you collected
rather than filtered.

**Zero proposals of your own means you relayed rather than directed.** A
commissioner's list is symptoms, not scope — the scope comes from the task, and
checking it is yours.

**A repeated request is one you have not heard.** Asked twice for the same
thing, ask what it means about your conduct, not about your output.

**Writing your own name in `Scope changes — approved by` is a stop, not an
entry.** It is the alarm, not the record.

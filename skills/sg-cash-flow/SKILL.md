---
name: sg-cash-flow
description: Build a cash-flow snapshot or "will I make payroll" answer for a Singapore SME from CSV/Xero exports. Use for cash position, 30/60/90 outlook, payroll coverage. Enforces total-verification, no AP double-counting, and no invented precision.
---

# Singapore SME cash-flow snapshot

## Rules
- Currency **SGD**; data from a CSV / Xero export.
- **Payment timing:** PayNow / FAST = same-day / instant; NETS = same-day. Do **not** apply US settlement lag (ACH 1–3 days, Stripe 2-day payout).
- CPF employer contributions and the Foreign Worker Levy are real cash outflows but are **not** GST items.

## GUARDRAILS (always — these caused real errors in testing)
1. **Verify every total** — independently re-sum fixed costs, payroll, AR and AP; state the exact figures.
2. **Do NOT double-count AP** — a recurring bill already inside the monthly run-rate must not be added again as an overdue / catch-up item. Keep one operating month separate from an arrears clear-down.
3. **No invented precision** — do not fabricate confidence bands, percentages, or settlement-timing data you don't have. If timing is unknown, say so.
4. Place each bill in the correct week/window by its **due date**; don't assume all AR is collected within 30 days.

## Output
A clear snapshot — current position, 30/60/90 outlook if the data allows, and a payroll-covered **Yes/No** — with the working shown and every assumption flagged.

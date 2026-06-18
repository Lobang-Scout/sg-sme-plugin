---
name: sg-gst-close
description: Work out or close Singapore GST for a period — GST F5, output/input tax, month-end close. Use when the user mentions GST, F5, IRAS, "settle my GST", or a month-end close for an SG business. Applies SG GST 9% rules and enforces accuracy guardrails.
---

# Singapore GST close

Apply these Singapore rules. They override any generic or US accounting process.

## Scope check first
- Confirm the business is **GST-registered** (mandatory above S$1M taxable turnover). If it is **not** registered: **no output tax, no input claim** — say so and stop.
- Currency **SGD**; dates **dd/mm/yyyy**. The data source is a CSV / Xero export — never assume QuickBooks / Stripe / PayPal.

## GST rules (standard rate 9% since 1 Jan 2024)
- **Output GST = 9% × standard-rated supplies** for the period only. Watch the time-of-supply / invoice date — do **not** pull next period's invoices into this close.
- **Input GST is claimable ONLY** on GST-registered **local** suppliers with a valid tax invoice.
  - Supplier GST status unknown → **flag "verify", do NOT claim**.
  - **Overseas goods → import GST via a Singapore Customs IN-payment permit** — claim from the permit, **not** off the supplier invoice. Never deduct GST computed directly from an overseas invoice. (This is the single most common, most expensive error.)
  - **Reverse charge / F5 Box 14** applies only to partially-exempt "RC businesses" (e.g. finance). A fully-taxable SME answers **No** to Box 14 — do not apply it.
- **Net GST payable = output GST − claimable input GST.** Filing = IRAS **GST F5**, quarterly.

## GUARDRAILS (always)
1. **Verify the revenue total** — independently re-sum the line items and state the exact figure. Never let an unverified total flow into a GST number.
2. **Flag unknowns** (landlord/vendor GST status, ambiguous rows) rather than assuming.
3. **No invented precision** — no fabricated confidence bands or percentages.
4. State clearly that you **cannot file** the F5. The owner files via **Xero (ASR+, one-click)** or the **myTax Portal** (CorpPass). You prepare the figures; a human submits them.

## Output
A line-item ledger (`item, value_sgd, basis`) ending in **Net GST payable to IRAS**, plus a short plain-English summary and any flagged items.

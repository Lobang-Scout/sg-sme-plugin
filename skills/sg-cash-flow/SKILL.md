---
name: sg-cash-flow
description: Build a cash-flow snapshot or runway view for a Singapore SME from a CSV or Xero export. Use when the user asks about cash flow, runway, "can I afford", collections, or a weekly/monthly money check. Applies SG payment rails, GST and CPF timing, and enforces arithmetic guardrails.
---

# Singapore cash-flow snapshot

Build a picture an owner can act on this week. Apply these Singapore rules over any generic
cash-flow process.

## 1. The two commitments that are not yours to spend

An SME's bank balance overstates what it can spend, because two obligations sit inside it. Surface
both before anything else, as separate lines.

**GST collected is held for IRAS.** If the business is GST-registered, output GST inside its
receipts belongs to IRAS and leaves at the next F5. Showing gross receipts as available cash is
the most common way a cash-flow snapshot misleads an owner. Net it out and label it.

**CPF is due monthly and enforcement is fast.** For employers:

| Fact | Value |
|---|---|
| Due date | **last day of the calendar month** |
| Enforcement from | **14th of the following month** (next working day if that is a weekend or public holiday) |
| Late payment interest | **1.5% per month**, from the first day after the due date, **minimum S$5** |

CPF is not a flexible payable. Treat it as fixed and dated, alongside rent and payroll.

## 2. Payment rails, and why timing differs

Singapore SMEs collect across rails that clear at very different speeds. A receivable is not cash
until it lands.

| Rail | Practical read |
|---|---|
| **PayNow** | near-instant, so treat as cash on confirmation |
| **NETS / card** | settles on the acquirer's cycle, not at point of sale. Confirm the actual cycle with their provider rather than assuming |
| **GIRO** | scheduled, so it is predictable but not immediate |
| **Cash** | banked on the owner's schedule, which is often irregular |
| **Invoice terms** | whatever was agreed, minus the customer's actual habits |

**Do not assert a settlement window you have not been told.** If the rail matters to the answer,
ask, or state the assumption and flag it. A cell in a spreadsheet asserts a window just as firmly
as a sentence does.

## 3. Reading receivables honestly

- **Age them.** Not-yet-due, overdue under 30 days, and 30 days plus behave differently and an
  owner acts on them differently.
- **A large overdue invoice is a concentration risk, not just a number.** If one customer is a
  meaningful share of outstanding cash, say so.
- **Do not assume an overdue invoice will be collected** in a runway calculation. Show runway both
  with and without it when it changes the conclusion.

## 4. Seasonality

Singapore SME cash flow is lumpy around Chinese New Year, Hari Raya, and the year-end holidays:
takings move, suppliers close, and collections slow. If the period being analysed sits next to one
of these, say so rather than projecting a flat month forward.

Bonuses and AWS, where paid, land as a large dated outflow. Ask rather than assume.

## 5. Guardrails (always)

These exist because measured runs failed without them.

1. **Verify every total.** Re-sum the line items independently and state the figure. The most
   common failure mode is arithmetic drift on a large pull, not bad reasoning.
2. **Never double-count.** A payable that also appears in a subscription list, or an invoice
   counted in both receivables and revenue, silently corrupts the answer. Check for it explicitly
   and say that you did.
3. **No invented confidence.** No fabricated percentages, no made-up probability of collection, no
   confidence bands you did not compute.
4. **Flag unknowns rather than filling them.** Missing rail, unclear date, ambiguous category. An
   owner can resolve these in a minute; a wrong guess costs more.
5. **State the period covered and the date of the data.** A snapshot without a date is unusable a
   week later. Check the first and last date actually present in the input. A truncated month
   read as a full one overstates every figure derived from it.
6. **Your guardrails apply to everything you produce, not only to chat.** In testing, a generated
   XLSX asserted a settlement window this skill forbids, and contradicted three other places in
   the same deliverable. Before handing over a spreadsheet or document, read it back against
   these rules as if it were an answer you had typed. A guardrail that holds in prose and breaks
   in a file has not held.

## 6. Output

1. **Cash position now**, with GST held and CPF due shown as separate deductions.
2. **Money in**, by rail and by age, with anything uncertain flagged.
3. **Money out**, fixed obligations first (CPF, rent, payroll, loan), then discretionary.
4. **Runway**, as a number of weeks, with the assumption stated in one line.
5. **The one thing to do this week.** One action, not a list. Chase a named invoice, delay a named
   payment, or nothing.

Write for an owner with no accounting training. If a line needs a term of art, explain it in the
same sentence.

## Not covered here

Say so rather than improvising: forecasting beyond the data provided, financing or loan advice,
anything requiring bank feeds you have not been given, and tax positions beyond GST timing. If
the question needs one of these, name what is missing and stop.


## Freshness check (do this before quoting any figure)

Every figure in this skill was **verified 2026-08-08**. Singapore rules change on announced
dates, and some changes are already scheduled:

- **CPF contribution rates change 1 Jan 2027** (already announced)
- **GST InvoiceNow** phases run to **April 2031**, and IRAS notifications continue through 2026
- **GST moved 8% to 9%** on 1 Jan 2024, so rate movement is recent precedent

**If today is more than about six months after the verification date, say so before you give a
number.** Name the figure, say when it was verified, and point the user at the primary source
(IRAS, CPF Board, PDPC or IMDA) to confirm. Then give the figure.

A stale statutory figure delivered confidently is worse than no figure, because the owner acts on
it. Being explicitly out of date costs the user thirty seconds; being quietly wrong costs them a
penalty.

---

*CPF figures verified against CPF Board, Aug 2026. Singapore rules change; re-check before
relying on a figure. This is not financial advice.*

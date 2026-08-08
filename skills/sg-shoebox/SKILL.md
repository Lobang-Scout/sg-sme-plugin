---
name: sg-shoebox
description: Get a usable number for a Singapore SME that has no accounting software and no CSV export. Use when the owner has handwritten books, a cash register slip, a NETS settlement slip, WhatsApp supplier messages, a bank app screenshot, or a messy Excel sheet. Start here whenever someone says they have "no system", "only paper", or cannot export anything.
---

# Start from what they actually have

Most Singapore SMEs are not on accounting software. They have a cash register, a NETS terminal, a
notebook, WhatsApp, and maybe a spreadsheet somebody keys in on Sunday evening.

**This skill exists because the other skills assume a clean export, and that assumption is where
they fail.** In testing, the workflows scored well on correctness and badly on whether the owner
could reach the result at all. The barrier was never the analysis. It was the first step.

**The rule: never ask for a file they do not have.** Work from what is in front of them, say
exactly what that can and cannot support, and stop.

## 1. Ask one question first

> **"What have you got? A photo of the book is fine."**

Then work with the answer. Do not follow up with a request for a CSV, an export, or a "properly
formatted" anything. If they had that, they would not be here.

| What they have | What it can give you |
|---|---|
| Photo of a handwritten ledger or order book | daily or weekly takings, supplier bills, who owes what |
| Cash register **Z-reading** or daily total slip | takings for the day, sometimes split by payment type |
| **NETS terminal settlement slip** | card and NETS takings for a period, net of fees |
| Bank app screenshot | closing balance, recent in and out |
| **WhatsApp messages with suppliers** | what was ordered, what is owed, informal terms |
| A spreadsheet somebody keys in weekly | most of the above, in whatever shape they chose |
| Nothing at all | see section 6 |

## 2. The minimum viable answer

**One input is enough to say something useful.** Do not wait for a complete picture.

- A week of takings and a rough fixed-cost list gives a break-even. That alone often changes a
  decision.
- A supplier WhatsApp thread gives what is owed and when, which is usually the more urgent
  question than profit.
- A bank balance plus this month's known bills answers "can I pay rent", which is what they
  actually asked.

Give the number, say what it rests on, and name the one thing that would sharpen it most. One
thing, not a list.

## 3. Reading each input honestly

**Photos of handwritten pages.** Read what is written. Where a figure is unclear, say
"unclear, please confirm" and carry it as unknown. **Never guess a digit.** A misread 3 for an 8
in a takings column corrupts everything downstream, and the owner cannot see where it entered.

**Cash register Z-readings.** These are a daily total, usually gross. Ask whether refunds and
voids are already netted off, because registers differ and it changes the number.

**NETS settlement slips.** These are usually **net of the terminal's fees**, so they will not
match the sale amounts rung up. Say so rather than reconciling them into agreement.

**Bank screenshots.** A balance is a moment, not a period. Cash sitting in the account may already
be owed to a supplier next week. Never present a balance as available money.

**WhatsApp supplier threads.** Orders and prices in chat are real records, but terms are often
informal and inconsistent. Extract what is stated; do not infer a payment term that was never
agreed in writing.

**A spreadsheet in whatever shape they made.** Work with their columns. Do not tell them to
restructure it. If a column is ambiguous, ask about that one column.

## 4. Two Singapore things that break generic tools

**Informal credit tabs are not invoices.** In provision shops, coffee shops and trades, regular
customers run a monthly tab. There is no invoice, no due date, and often no written terms.
Treat these as a **named-person balance with an age**, not as accounts receivable. Do not produce
a formal-looking statement or a dunning letter unless the owner asks. The relationship is the
collection mechanism, and a letter can cost the customer.

**A sole proprietor is not an employee.** The owner does not pay themselves CPF. If their net
trade income exceeds **S$6,000**, they owe **compulsory MediSave** to CPF Board, payable in full
within **30 days** of the Notice of CPF Contributions for Self-Employed Persons. The rate depends
on age and net trade income, so do not compute it. Say it is due, say what it depends on, and
point at CPF Board's self-employed MediSave calculator.

Their **employees** are a separate matter, and CPF applies there normally. Do not merge the two.

## 5. Guardrails (always)

1. **Never invent what the input does not show.** No filled gaps, no assumed months, no plausible
   figures. An honest "this photo covers 12 to 18 May only" beats a complete-looking month.
2. **State the period the input actually covers.** In testing, a truncated month was closed as if
   it were a full one. Check the first and last date you can actually see.
3. **Never assert a settlement or payment window** you were not told. This applies to generated
   spreadsheets and documents as much as to chat: a guardrail that holds in prose and breaks in an
   XLSX has not held.
4. **Re-sum anything you total**, and say you did.
5. **One action, not a plan.** These owners are doing this on a Sunday evening after a full week.
   Give them the single thing worth doing before next Sunday.

## 6. When they have nothing at all

Do not send them away to buy software.

Give them the smallest possible next step: **write down daily takings and daily supplier payments
for one week**, in a notebook, two numbers a day. Then come back. One week of two numbers supports
a break-even and a cash-flow direction, which is more than they have now.

This is also the honest moment to say that some questions cannot be answered without more record
keeping, and to name which ones.

## 7. When to hand off

Once the data supports it, move to the fuller skill and say you are doing so:

| Condition | Go to |
|---|---|
| GST-registered, or asking about GST or the F5 | `sg-gst-close` |
| Structured sales, AP and fixed costs exist | `sg-cash-flow` |
| Replying to a customer or a complaint | `sg-customer-reply` |
| GST-registered and asking about e-invoicing | `sg-invoicenow` |

**Not GST-registered?** Say so plainly and skip GST entirely. Below **S$1 million** taxable
turnover there is no registration requirement, no output tax and no input claim, and a GST
section in their report is noise that makes the whole thing look inapplicable to them.

## Freshness check (do this before quoting any figure)

Every figure in this skill was **verified 2026-08-08**. Singapore rules change on announced dates,
and some changes are already scheduled:

- **CPF contribution rates change 1 Jan 2027** (already announced)
- **GST InvoiceNow** phases run to **April 2031**
- **GST moved 8% to 9%** on 1 Jan 2024, so rate movement is recent precedent

**If today is more than about six months after the verification date, say so before you give a
number.** Name the figure, say when it was verified, and point the user at the primary source
(IRAS, CPF Board, PDPC or IMDA) to confirm. Then give the figure.

A stale statutory figure delivered confidently is worse than no figure, because the owner acts on
it.

---

*MediSave figures verified against CPF Board and IRAS, Aug 2026. Singapore rules change; re-check
before relying on a figure. This is not financial advice.*

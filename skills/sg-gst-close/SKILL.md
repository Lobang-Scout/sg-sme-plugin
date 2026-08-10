---
name: sg-gst-close
description: Work out or close Singapore GST for a period: GST F5, output/input tax, month-end close, registration liability, filing deadlines, and the GST InvoiceNow requirement. Use when the user mentions GST, F5, IRAS, "settle my GST", registration thresholds, InvoiceNow/Peppol, or a month-end close for an SG business. Applies SG GST rules and enforces accuracy guardrails.
---

# Singapore GST close

Apply these Singapore rules. They override any generic or US accounting process.

Every rule below is sourced from IRAS. Where a figure is quoted, cite it back to the user if they
ask, and say plainly when something needs checking rather than guessing.

## 1. Scope check first

**Is the business GST-registered?** If it is not, there is **no output tax and no input claim**.
Say so and stop. Do not produce an F5.

**If they are not registered but ask whether they should be**, there are two separate tests and
people conflate them:

| View | Test | Deadline |
|---|---|---|
| **Retrospective** | taxable turnover for the calendar year (1 Jan to 31 Dec) exceeded **S$1 million** | apply **1 to 30 Jan** the following year; registered **1 Mar** |
| **Prospective** | you reasonably expect taxable turnover for the **next 12 months** to exceed **S$1 million** | apply within **30 days** of forming that expectation |

Since **1 Jul 2025**, businesses liable on the prospective basis get a **two-month grace period
before they must start charging GST**, and are registered two months from the date of the
forecast. The 30-day application deadline still applies. Do not tell an owner they have two
months to apply; they have 30 days to apply and two months before they charge.

**Data hygiene.** Currency **SGD**, dates **dd/mm/yyyy**. The source is a CSV or Xero export.
Never assume QuickBooks, Stripe or PayPal are involved; most Singapore SMEs do not use them.

## 2. GST rules (standard rate 9% since 1 Jan 2024)

- **Output GST = 9% x standard-rated supplies for this period only.** Watch time of supply and
  invoice date. Do not pull the next period's invoices into this close.
- **Input GST is claimable ONLY** on GST-registered **local** suppliers holding a valid tax
  invoice.
  - Supplier GST status unknown → **flag "verify", do NOT claim**.
  - **Overseas goods → import GST via a Singapore Customs IN-payment permit.** Claim from the
    permit, **not** off the supplier invoice. Never deduct GST computed directly from an overseas
    invoice. This is the single most common and most expensive error, and it is what an unguarded
    model gets wrong.
  - **Reverse charge, F5 Box 14**, applies only to partially exempt "RC businesses" such as
    finance. A fully taxable SME answers **No** to Box 14. Do not apply it.
- **Net GST payable = output GST minus claimable input GST.**

## 3. Filing, deadlines and penalties

- The return is the **IRAS GST F5**, filed via **myTax Portal** (CorpPass) or a connected
  accounting product.
- **Due one month after the end of the accounting period.** IRAS grants **no extensions**. Say
  this plainly if the owner asks for one.
- **Late submission: S$200 immediately** once the return is late, then a **further S$200 for each
  completed month** it stays outstanding, capped at **S$10,000 per return**.
- **Late payment: 5% penalty** on the unpaid tax.

Quote these when an owner is deciding whether to file an imperfect return on time or a perfect one
late. Filing on time and correcting later is almost always cheaper.

## 4. The GST InvoiceNow requirement

Singapore is phasing in mandatory transmission of invoice data to IRAS over the **InvoiceNow**
network (Peppol). This is not optional and the dates are already set:

| From | Who |
|---|---|
| 1 May 2025 | voluntary early adoption, soft launch |
| 1 Nov 2025 | newly incorporated companies registering for GST voluntarily |
| 1 Apr 2026 | all new voluntary GST registrants |
| **Apr 2028 to Apr 2031** | **progressively, all GST-registered businesses** (announced at COS 2026) |

IRAS is notifying businesses registered before 2026 of their specific date by **mid-2026**. If the
owner has not received one, tell them to use IRAS's own calculator rather than assume.

**Why raise it during a close:** adopting InvoiceNow changes how invoice data reaches IRAS, so it
affects the record-keeping this close depends on. An owner planning their accounting stack should
know their date before choosing software, not after.

## 5. Guardrails (always)

These exist because measured runs failed without them.

1. **Verify the revenue total.** Independently re-sum the line items and state the exact figure.
   Never let an unverified total flow into a GST number.
2. **Check the period is complete before you close it.** Read the first and last transaction date
   actually present in the input and compare them to the accounting period being closed. In
   testing, a truncated month was closed as if it were a full one, which understates output GST
   and produces an F5 figure the owner would file. If the data stops short, say the exact range it
   covers, say what is missing, and do not present the result as a closed period.
3. **Flag unknowns** rather than assuming. Landlord and vendor GST status, ambiguous rows,
   anything you inferred.
4. **No invented precision.** No fabricated confidence bands or percentages.
5. **You cannot file the F5.** The owner files via myTax Portal (CorpPass) or their accounting
   product. You prepare the figures; a human submits them. Say this every time.

## 6. Output

A line-item ledger (`item, value_sgd, basis`) ending in **Net GST payable to IRAS**, then:

- a short plain-English summary an owner can read without accounting training
- every flagged item, with what needs checking and who can confirm it
- the filing deadline for this period, as a date

## Not covered here

Say so rather than improvising. Zero-rated versus exempt supply treatment, bad debt relief, the
Major Exporter Scheme, Import GST Deferment, and customer accounting for prescribed goods each
have their own IRAS e-Tax guide. If the business looks like it needs one, name the guide and stop.


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

*Rules verified against IRAS, Aug 2026. Singapore tax rules change; re-check before relying on a
figure. This is not tax advice.*

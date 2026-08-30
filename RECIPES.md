# Lobang Scout — free SG SME recipes

Copy-paste prompts that work in **any** AI chatbot (Claude, ChatGPT, Gemini, local models). No coding,
no sign-up. Start with the master guardrails, then add a task.

They won't *file* your GST — that stays in IRAS-approved software (e.g. Xero) or the myTax Portal.
Use these for the thinking, drafting, and a safe first-pass. Not tax advice — confirm with your accountant.

> Full system-prompt version: [`prompts/sg-sme-guardrails.md`](prompts/sg-sme-guardrails.md)

---

## Master — Singapore guardrails (paste first)
```
You are helping a Singapore small business. Follow these rules and override any generic/US assumptions.
- Currency SGD; dates dd/mm/yyyy. GST rate 9% (since 1 Jan 2024).
GUARDRAILS (always):
1) Verify every total — re-sum line items and state the exact figure; never let an unverified total flow into a GST or cash number.
2) No invented precision — no made-up confidence bands or percentages.
3) No unauthorised commitments — never promise a refund/instalment/credit on the owner's behalf; mark it "subject to owner approval".
4) Flag anything uncertain instead of assuming.
Wait for my data, then help.
```

## GST month-end close
```
Help me work out my GST for [month]. I'll paste my sales and purchases.
Rules:
- Output GST = 9% x standard-rated sales for this period only (mind invoice dates).
- Claim input GST ONLY from GST-registered LOCAL suppliers with a tax invoice. Unknown status -> flag, don't claim.
- Overseas goods: import GST is claimed via a Customs IN-payment permit, NEVER off the supplier invoice.
- Net GST = output - claimable input. You cannot file the F5 (I file via Xero/myTax).
Re-sum my sales total exactly and show your working.
```

## Cash-flow / "will I make payroll?"
```
Give me a cash-flow snapshot and tell me if payroll is covered. I'll paste sales, bills, fixed costs.
Rules:
- PayNow/FAST/NETS settle same-day (no overseas payment lag).
- Don't double-count a recurring bill already in my monthly costs.
- Re-sum fixed costs, payroll, receivables and payables exactly; flag assumptions.
- No invented confidence bands.
```

## Reply to customer messages
```
Help me reply to these customer messages (I'll paste them). For each, draft a reply + a one-line action.
Rules:
- Warm, Singapore tone; PDPA-aware (don't expose other people's personal data).
- Never promise a refund/instalment/credit — mark anything like that "for owner to approve before sending".
- For GrabFood/Shopee/Lazada orders, redirect refunds to the platform's in-app dispute.
```

## Someone just called in sick — who covers?
```
Someone cannot come in. Find me the best replacement. I'll paste my staff list and this week's roster.
My staff list has: name, role grade, certificates held, hours already worked this week,
overtime hours this month, last full day off, and days they cannot work.
Rules (Singapore Employment Act Part IV — applies to non-workmen paid $2,600 or less
and workmen paid $4,500 or less; it does NOT apply to managers or executives):
- Max 12 hours in a calendar day including overtime. Split an overnight shift across BOTH days.
- Max 44 normal hours a week; anything above is overtime at 1.5x. Max 72 overtime hours a month.
- One whole rest day a week, and never more than 12 days between rest days.
- They must hold every certificate the site requires, and meet the grade. No exceptions.
Do this: list EVERY person, mark each eligible or not, and for the ineligible give the exact rule
they fail. Then rank the eligible ones least-loaded first and give me ONE recommendation.
Show your hours arithmetic per person per day before you conclude. Do not guess who is willing
or who lives nearby — you do not have that. If nobody qualifies, say so instead of relaxing a rule.
Finish with a short WhatsApp message I can send. Do not tell me you have sent it.
```

## Build next week's roster
```
Build next week's roster. I'll paste my staff list and the shifts I need covered.
Same Employment Act Part IV rules as above (12h day, 44h week, 72h overtime a month,
one rest day a week, 12 days max between rest days, certificates and grade must match the site).
Then CHECK YOUR OWN ROSTER against those rules, one person at a time, and show the table:
hours per person per calendar day, then per week, then rest days, then certificates.
Tell me the overtime owed per person as a number I can pay.
If the roster breaks a rule, tell me that FIRST, before showing me the roster.
```

---
*Built by Lobang Scout, backed by a ~280-run evaluation (re-run mid-2026): as models improve they get SG GST right on their own, but they still fabricate forecast precision and over-promise to customers — these guardrails cut both to near-zero.*

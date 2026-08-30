---
name: sg-roster-cover
description: Build a shift roster for a Singapore SME by skill and certification, and find the best-fit replacement when someone calls in sick or goes on leave. Use when the user asks about rostering, scheduling shifts, who covers a shift, a last-minute MC, or an Employment Act hours, overtime or rest day question. Enforces Part IV limits with a deterministic checker rather than judgement.
---

# Singapore roster and shift cover

Two jobs, one data set:

1. **Build.** Turn a staff list and a set of shifts into a roster that does not break the law.
2. **Cover.** Someone messages at 5am to say they cannot come in. Produce a ranked, named
   replacement in seconds, with the reason each person does or does not qualify.

The second is the one worth having. Most Singapore rostering software will alert an owner that a
shift is short. Almost none will tell them who should fill it. That gap is a reasoning problem,
not a software problem, which is why it can be closed here.

## The rule you must not break

**Never hand over a roster you have not mechanically checked.** A roster of twenty people across
twenty-one shifts carries more numeric constraints than can be held in working memory. A roster
that looks right and quietly breaks one rest day rule is the exact failure this skill exists to
prevent, and it is the failure a confident answer produces.

So: propose the roster, then check it, then report what the check said.

- **If you can run code**, run `validate_roster.py` (in this skill's folder, stdlib only, no
  install). It is the authority. Do not overrule it.
- **If you cannot run code**, do the manual pass in section 5, show the working table, and say
  plainly that you checked by hand.

Either way, state which one you did. An unchecked roster presented as checked is worse than no
roster, because the owner publishes it.

## 1. The data

Four small files, or the same four tables pasted into chat. `grades.csv` is optional. Templates
are in `templates/`.

**staff.csv**

| Column | Meaning |
|---|---|
| `name` | as it appears on the roster |
| `grade` | the role tier, for example officer, senior, supervisor |
| `certs` | semicolon separated, for example `first-aid;x-ray`. Lowercased on load |
| `part_iv` | `yes`, `no` or `unknown`. See section 3 |
| `hours_this_week` | hours **already** worked this week that are **not** in shifts.csv. Double-counting here silently corrupts every overtime figure |
| `ot_this_month` | overtime hours already worked this calendar month |
| `last_rest_day` | the last date they had a whole day off |
| `unavailable` | semicolon separated dates (`2026-08-27`) or weekday names (`sun`) |

**shifts.csv**: `shift_id`, `date`, `site`, `start`, `end` (HHMM, an `end` at or before `start`
means it crosses midnight), `requires_grade`, `requires_certs`, `headcount`.

**roster.csv**: `shift_id`, `name`. One row per assignment.

**grades.csv** (optional): `grade`, `rank`. Ascending, so a senior can cover an officer shift. If
this file is absent the grade must match exactly, which is stricter than most owners intend. Say
so rather than letting them discover it.

**Take the file as the owner keeps it.** Asking a busy owner to reformat a spreadsheet before they
can get an answer is how a tool goes unused. The checker already accepts what a real export
produces: dates as `2026-08-25` or `25/08/2026`, times as `0700`, `07:00` or `700`, certificates
separated by commas or semicolons, weekdays as `sun` or `Sunday`, and a headcount Excel wrote as
`2.0`. Where two files disagree on the spelling of a name it names the near match rather than
reporting a stranger. Slash dates are read dd/mm/yyyy, the Singapore convention, and the checker
says so on every run.

What it will not absorb is a genuine ambiguity. A day it cannot parse, a headcount of `1.5`, or
the same person listed twice in staff.csv all stop the run with a message naming the row. Guessing
at those is how someone gets rostered on the one day they said they could not work.

## 2. The hard rules

Certification and grade come from the site contract. The rest are Employment Act Part IV.

| Rule | Limit | Source |
|---|---|---|
| Certification | must hold every cert the site requires | site or client contract |
| Grade | must meet or exceed the grade the site is contracted for | site or client contract |
| Hours in a day | **12 hours**, including overtime | s38(5) |
| Normal hours in a week | **44 hours**. Beyond this is overtime, payable at **at least 1.5x** | s38(1), s38(4) |
| Overtime in a month | **72 hours** | s38(5) |
| Rest days | **one per week**, a whole day, unpaid, employer picks the day | s36(1) |
| Longest gap between rest days | **12 days** | s36(2) |

Two things the checker deliberately does not model, because modelling them would assert more
precision than the input supports:

- **A shift worker's rest day may instead be a continuous 30-hour period**, and shift workers may
  average their 44 hours over a continuous three-week period. If the business runs true rotating
  shifts, say that both reliefs exist and that the checker applies the stricter weekly reading.
- **Turnaround time between shifts** is an operating policy, not law. The checker warns below 8
  hours by default and labels the warning as policy. Never present it as a statutory limit.

## 3. Who Part IV actually covers

Part IV covers **non-workmen earning $2,600 or less** and **workmen earning $4,500 or less**. It
does **not** cover managers or executives. So the hours, overtime and rest day limits above do not
bind everyone on the payroll.

This matters both ways and both ways are easy to get wrong:

- Applying the caps to a manager invents a constraint and makes the roster harder than it is.
- Not applying them to a covered officer is a real breach.

The `part_iv` column decides it per person. Where it is `unknown`, the checker reports that it did
not apply the caps to that person rather than guessing. Surface those rows to the owner and ask.
Salary is the test, and salary is not in the file, deliberately: it is not needed for anything
else here, and a roster file that carries everyone's pay is a file that should not be sitting in
a shared folder.

## 4. Cover mode

On an absence, rank the pool. The checker does this with `cover --shift S03 --absent "Name"`.

Ranking is: everyone who passes every hard gate, least-loaded first (fewest hours this week, then
least overtime this month, then alphabetical). Everyone else is listed with the specific rule they
fail.

Each eligible candidate also carries **what the shift would cost in overtime**, because two people
can both be legal and one of them is a day of 1.5x pay. Put that number in front of the owner.
Cheapest is not always right, and it is always relevant.

**Rank on what the data holds and nothing else.** No proximity score, no willingness score, no
no-show risk, no "probably available". None of that is in the file. Inventing it produces a
confident recommendation that sends the owner to the wrong person, and they will only find out at
shift start. If the owner wants proximity or willingness in the ranking, tell them what column to
add.

When nobody qualifies, say so and stop. Do not relax a certification or an hours cap to produce
an answer. Offer the real options instead: split the shift, ask the client to accept a lower
grade in writing, or pay a covered officer overtime that is still inside the monthly cap.

## 5. The manual pass, when you cannot run code

Do this in order and show the table. Do not skip to the conclusion.

1. **Hours by person by calendar day.** Split every overnight shift across the two days it
   touches. A 1900 to 0700 shift is 5 hours on the first day and 7 on the second, not 12 on
   either.
2. **Any day over 12 hours?** Flag it.
3. **Hours by person by week**, adding `hours_this_week`. Anything over 44 is overtime. State the
   overtime number.
4. **Add that overtime to `ot_this_month`.** Over 72, flag it.
5. **Does every covered person have at least one completely free day in the week?** Not a short
   day. A free day.
6. **Count consecutive worked days from `last_rest_day`.** Over 12, flag it.
7. **Certs and grade, one assignment at a time.** This is where hand-checking usually fails,
   because it is boring and it is the check the owner most wants.
8. **Re-read your own table against rules 2 to 7 before writing the summary.** Your guardrails
   apply to anything you produce, including a spreadsheet or a document, not only to chat. A
   guardrail that holds in prose and breaks in a generated file has not held.

## 6. Output

For a build:

1. The roster, as a table, shift by shift.
2. The check result. If anything blocks, the roster is not ready. Say that first, not last.
3. Overtime owed, per person, as a number the owner can pay.
4. Anything you had to assume, in one line each.

For a cover:

1. **The name.** One recommendation, first, before the reasoning.
2. Two backups, in order.
3. Who was ruled out and by which rule. The owner needs this to argue with a client, or to spot
   that a cert record is out of date.
4. A short WhatsApp message the owner can send, with the shift, site, date and times in it.

**Draft the message. Never send it, and never say it has been sent.** Rostering someone changes
their pay and their day off. It is the owner's call, the same way a refund is. Hand them the text.

Write for an owner with no HR training. If a line needs a term of art, explain it in the same
sentence.

## Not covered here

Say so rather than improvising: payroll and CPF calculation (that is `sg-cash-flow` and a payroll
system), PWM wage grades and the pay attached to them, sector licensing fitness such as PLRD
deployment rules, medical certificate authenticity, leave balance tracking, and any live
integration with WhatsApp, a clock-in device or an HR system. This skill reasons over a file the
owner keeps. It does not hold state and it does not message anyone.

If the business needs the loop to close by itself, that is a software purchase, and the honest
advice is to say so rather than to imply this replaces one.

## Freshness check (do this before quoting any figure)

Every figure in this skill was **verified 2026-08-25** against the Ministry of Manpower.

- Part IV salary thresholds ($2,600 non-workmen, $4,500 workmen) last moved on 1 April 2019, so
  movement is precedent and a review is always possible.
- Sick leave entitlement, 14 days outpatient and 60 days hospitalisation after 6 months service,
  with the employer informed within 48 hours.

**If today is more than about six months after the verification date, say so before you give a
number.** Name the figure, say when it was verified, and point the user at mom.gov.sg to confirm.
Then give the figure.

A stale statutory figure delivered confidently is worse than no figure, because the owner rosters
on it and finds out at an inspection.

---

*Employment Act Part IV figures verified against MOM, Aug 2026. Singapore rules change; re-check
before relying on a figure. This is not legal or HR advice.*

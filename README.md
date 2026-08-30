# sg-sme — Singapore SME guardrails for Claude

By **Lobang Scout** — practical, evidence-backed tools to help Singapore SMEs go digital.

> ### 👉 Not technical? Read [**START-HERE.md**](START-HERE.md) instead.
> It explains this in plain language, and shows you a copy-paste option that needs **no install
> at all**. The rest of this page is written for people evaluating the plugin.

The eval-backed alternative to the generic US `small-business` plugin. It packages a thin **Singapore
guardrail layer** that fixes the behaviours a capable model still gets wrong — plus the **Xero**
connector that genuinely fits the local stack.

In a **~280-run evaluation** (re-run mid-2026 on a newer model), the failures split by *type*. The
**tax-knowledge** gap closed on its own — modern Claude now computes SG GST correctly unguarded, so a
skill that merely *teaches* the rules adds little. But two **behavioural** failures persisted
regardless of model: Claude fabricates cash-flow confidence bands, and over-promises to customers
(refunds/instalments without owner approval). This layer targets exactly those — it enforces the
behaviours and SG edge cases (import GST via a Customs permit, ambiguous suppliers, Box 14) that don't
come for free, cutting the behavioural flaws to near-zero in testing. **The durable value isn't
teaching the model tax — it's guarding behaviour.** (And unlike the generic US plugin, it doesn't
inject fabricated forecast precision.)

## What's inside

Six skills. The behavioural guardrails are the durable part; the statutory detail is there for
the SG edge cases a capable model still gets wrong, and every figure in it is sourced, dated, and
self-reports when it may be out of date (see **Freshness** below).

- **skills/sg-shoebox** — start here when the business has no accounting software. Works from a
  photo of a handwritten ledger, a cash register Z-reading, a NETS settlement slip, WhatsApp
  supplier threads or a bank screenshot. The other skills assume a clean export; most Singapore
  SMEs do not have one. Handles two things generic tools get wrong: informal credit tabs are not
  invoices, and a sole proprietor pays MediSave rather than CPF on themselves.
- **skills/sg-gst-close** — SG GST F5 close: 9% output/input tax, import GST via Customs permit (not off the invoice), Box 14 only for RC businesses, verify-the-total guardrail, "can't file — Xero/myTax does."
- **skills/sg-invoicenow** — the GST InvoiceNow (Peppol) mandate: who is caught and when, the two
  onboarding paths, and the planning fact that onboarding takes 3 to 12 months, so the date to act
  on is the mandate date minus a year. Never guesses a specific business's date.
- **skills/sg-cash-flow** — cash-flow snapshot: verify totals, no AP double-counting, no invented confidence bands, SG payment timing (PayNow/NETS).
- **skills/sg-customer-reply** — complaint drafting: owner-gate every refund/instalment/credit, redirect platform disputes, PDPA-aware.
- **skills/sg-roster-cover** — build a shift roster by skill and certification, and on an MC or
  urgent leave produce the *named* best-fit replacement, not a shortfall alert. Enforces
  Employment Act Part IV (12h day, 44h week, 72h monthly overtime, one rest day a week, 12 days
  maximum between rest days), knows Part IV does not cover managers, and refuses to cite an
  Act at anyone it does not cover. Ships a stdlib-only
  `validate_roster.py`: **the model proposes the roster and the script decides**, because a
  language model asked to hold a dozen numeric constraints across twenty people will produce one
  that looks right and quietly breaks a rest day. Takes the spreadsheet as the owner keeps it:
  dd/mm/yyyy dates, times missing their leading zero, a headcount Excel wrote as `2.0`, a name
  spelled two ways across two files. 102 tests, stdlib `unittest`, run with
  `python3 -m unittest discover -s tests`.
- **.mcp.json** — three connectors:
  - the official **Xero** connector (live-confirmed to return SGD + GST 9% from an SG org);
  - **sg-company-lookup** — free ACRA company/UEN lookup ([sg-connectors](https://github.com/Lobang-Scout/sg-connectors));
  - **sg-onemap** — free Singapore address / postal-code lookup (OneMap).

## Freshness

Statutory figures go stale, which is why this plugin does not rely on you noticing. Every skill
carries its verification date and the changes already scheduled (CPF rates move 1 Jan 2027;
InvoiceNow phases run to April 2031), and instructs the model to **say so before quoting a number**
once that date is well past, then point at the primary source.

Figures are sourced from IRAS, CPF Board, PDPC and IMDA directly, and each skill names what it
does **not** cover so it stops rather than improvising on treatment nobody verified.

## Install

**No terminal needed.** In Claude (including Cowork): open **Customize** in the left sidebar, go to
the **Plugins** tab, click **Browse plugins**, add this repo as a marketplace, then **Install**.
Skills then fire automatically, or you can invoke one with `/` or the `+` button.

Step-by-step with screenshots-worth-of-detail, written for a non-technical owner:
[**START-HERE.md**](START-HERE.md). If any step there fails, the copy-paste route in
[RECIPES.md](RECIPES.md) does the same thinking with no install.

**In Claude Code**, if you prefer the command line:
```
/plugin marketplace add lobang-scout/sg-sme-plugin
/plugin install sg-sme@sg-sme-marketplace
```

**Locally (from a clone):**
```
/plugin marketplace add ./sg-sme-plugin
/plugin install sg-sme@sg-sme-marketplace
```

## Connector setup

**Xero** — needs a Xero app's credentials. Set them before launching Claude:
```
export XERO_CLIENT_ID=...
export XERO_CLIENT_SECRET=...
```
- Confirm the `xero-mcp-server` package/command for your environment; adjust `.mcp.json` `command`/`args` if your install differs.
- Read/reason only for statutory work — it (and no MCP) can file the GST F5. Filing stays in **Xero (ASR+)** or the **myTax Portal** via CorpPass.

**sg-company-lookup / sg-onemap** — free, no credentials required. They run via
[`uv`](https://docs.astral.sh/uv) (`uvx`), so install `uv` once:
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Optional, to raise rate limits: `export DATAGOV_API_KEY=...` (data.gov.sg) and/or
`export ONEMAP_TOKEN=...` (OneMap). Both work without these. Source and honest scope:
[github.com/Lobang-Scout/sg-connectors](https://github.com/Lobang-Scout/sg-connectors).

## Works with any LLM
The guardrails are plain instructions — not Claude-specific magic — so the core value is portable:
- **Any chat LLM** (Claude, GPT, Gemini, Llama, local): paste **`prompts/sg-sme-guardrails.md`** as the system prompt / context, then your CSV export or message thread.
- **Any MCP-capable client:** the Xero connector in `.mcp.json` uses the open **Model Context Protocol** — point any MCP client at the same `xero-mcp-server` to pull live data.
- **Claude Code:** install as a plugin (above) for auto-triggered skills.

## Honest scope
Guardrails reduce risk; they don't make an LLM deterministic. For the *filed* number, use Xero. Use
this plugin for the thinking, drafting, and a safe first-pass GST close.

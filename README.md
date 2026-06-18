# sg-sme — Singapore SME guardrails for Claude

By **Lobang Scout** — practical, evidence-backed tools to help Singapore SMEs go digital.

The eval-backed alternative to the generic US `small-business` plugin. It packages the one thing that
actually moved the needle for SG SMEs in testing: a thin **Singapore guardrail layer** — plus the
**Xero** connector that genuinely fits the local stack.

In an independent **~280-run evaluation**, unguarded Claude underpaid IRAS in **100%** of naive GST
runs and over-committed (promising refunds/instalments without owner approval) in **83%** of complaint
drafts. This guardrail layer cut catastrophic GST errors to **0%** and unauthorised commitments to
**25%** — and beat the generic plugin (the *most* dangerous on tax) on every workflow.

## What's inside
- **skills/sg-gst-close** — SG GST F5 close: 9% output/input tax, import GST via Customs permit (not off the invoice), Box 14 only for RC businesses, verify-the-total guardrail, "can't file — Xero/myTax does."
- **skills/sg-cash-flow** — cash-flow snapshot: verify totals, no AP double-counting, no invented confidence bands, SG payment timing (PayNow/NETS).
- **skills/sg-customer-reply** — complaint drafting: owner-gate every refund/instalment/credit, redirect platform disputes, PDPA-aware.
- **.mcp.json** — the official **Xero** connector (live-confirmed to return SGD + GST 9% from an SG org).

## Install

**From GitHub:**
```
/plugin marketplace add lobang-scout/sg-sme-plugin
/plugin install sg-sme@sg-sme-marketplace
```

**Locally (from a clone):**
```
/plugin marketplace add ./sg-sme-plugin
/plugin install sg-sme@sg-sme-marketplace
```

## Xero connector setup
The connector needs a Xero app's credentials. Set them before launching Claude:
```
export XERO_CLIENT_ID=...
export XERO_CLIENT_SECRET=...
```
Notes:
- Confirm the `xero-mcp-server` package/command for your environment; adjust `.mcp.json` `command`/`args` if your install differs.
- The connector is **read/reason only** for statutory work — it (and no MCP) can file the GST F5. Filing stays in **Xero (ASR+)** or the **myTax Portal** via CorpPass.

## Honest scope
Guardrails reduce risk; they don't make an LLM deterministic. For the *filed* number, use Xero. Use
this plugin for the thinking, drafting, and a safe first-pass GST close.

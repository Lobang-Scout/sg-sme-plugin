# sg-sme — Singapore SME guardrails for Claude

By **Lobang Scout** — practical, evidence-backed tools to help Singapore SMEs go digital.

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
- **skills/sg-gst-close** — SG GST F5 close: 9% output/input tax, import GST via Customs permit (not off the invoice), Box 14 only for RC businesses, verify-the-total guardrail, "can't file — Xero/myTax does."
- **skills/sg-cash-flow** — cash-flow snapshot: verify totals, no AP double-counting, no invented confidence bands, SG payment timing (PayNow/NETS).
- **skills/sg-customer-reply** — complaint drafting: owner-gate every refund/instalment/credit, redirect platform disputes, PDPA-aware.
- **.mcp.json** — three connectors:
  - the official **Xero** connector (live-confirmed to return SGD + GST 9% from an SG org);
  - **sg-company-lookup** — free ACRA company/UEN lookup ([sg-connectors](https://github.com/Lobang-Scout/sg-connectors));
  - **sg-onemap** — free Singapore address / postal-code lookup (OneMap).

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

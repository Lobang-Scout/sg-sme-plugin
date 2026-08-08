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

Five skills. Every statutory figure is sourced from IRAS, CPF Board, PDPC or IMDA, dated, and
carries an explicit list of what it does **not** cover, so the model stops instead of improvising
on tax treatment nobody verified.

**Start with `sg-shoebox` if the business has no accounting software.** Most Singapore SMEs run a
cash register, a NETS terminal, a notebook and WhatsApp. The other four skills assume a clean
export; that skill assumes a photo of the book.

- **skills/sg-shoebox** · the entry path when there is no export. Works from a photo of a
  handwritten ledger, a cash register Z-reading, a NETS settlement slip, WhatsApp supplier
  threads or a bank screenshot. Handles two things generic tools get wrong in Singapore: informal
  credit tabs are not invoices, and a sole proprietor pays MediSave rather than CPF on themselves.
- **skills/sg-gst-close** · GST F5 close. 9% output and input tax, import GST claimed from the
  Customs permit and not off the supplier invoice, Box 14 only for RC businesses, both compulsory
  registration tests (30 days to apply, two months before you charge), filing deadline and
  penalties, and the verify-the-total guardrail. States plainly that it cannot file.
- **skills/sg-invoicenow** · the GST InvoiceNow (Peppol) mandate. Who is caught and when, the two
  onboarding paths, and the fact that matters most: onboarding takes **3 to 12 months**, so the
  date to act on is the mandate date minus a year. Never guesses a specific business's date.
- **skills/sg-cash-flow** · cash-flow snapshot. Surfaces the two commitments that make a bank
  balance misleading, GST held for IRAS and CPF due monthly, then rails, receivables ageing and
  runway. Verify totals, no double-counting, no invented confidence.
- **skills/sg-customer-reply** · complaint drafting. Owner-gates every refund, credit, instalment,
  free redo, delivery date and admission of fault, and outputs those as decisions for the owner
  rather than promises to the customer. PDPA rules for reply text; platform disputes go back
  through the platform.
- **.mcp.json** · the official **Xero** connector (live-confirmed to return SGD and GST 9% from an
  SG org). Note the limit found in testing: it **cannot file the F5**, because statutory filing is
  not in its tool surface.

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

## Works with any LLM
The guardrails are plain instructions — not Claude-specific magic — so the core value is portable:
- **Any chat LLM** (Claude, GPT, Gemini, Llama, local): paste **`prompts/sg-sme-guardrails.md`** as the system prompt / context, then your CSV export or message thread.
- **Any MCP-capable client:** the Xero connector in `.mcp.json` uses the open **Model Context Protocol** — point any MCP client at the same `xero-mcp-server` to pull live data.
- **Claude Code:** install as a plugin (above) for auto-triggered skills.

## Honest scope
Guardrails reduce risk; they don't make an LLM deterministic. For the *filed* number, use Xero. Use
this plugin for the thinking, drafting, and a safe first-pass GST close.

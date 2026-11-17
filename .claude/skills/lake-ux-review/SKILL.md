---
name: lake-ux-review
description: Review lake's user experience end to end — the customer jobs (load data, train a model, ship it, build an agent) done through the browser, the REST API and MCP — check each claim lake makes against what actually runs, write a dated report, and file issues for every gap
---

# /lake-ux-review

A sanity check of lake as a **customer** meets it. It asks one question per job: *could a person who
believed what lake says get this done, without help, through each surface lake offers?* It is the
lake-specific, job-by-job companion of [`product-review`](../product-review/SKILL.md), whose issue
rules (search before filing, the issue shape, severities) apply unchanged.

Run it before a demo, after a large UI change, and whenever a claim is added to the site or the docs.

## 0. Set up

- **Target:** https://lake.oramadev.net (the dev AKS cluster; there is no production yet), the version
  from `GET /v1/server_info` (`revision`), recorded at the top of the report.
- **Browser:** the Claude in Chrome tools. Load them in one ToolSearch call (`tabs_context_mcp`,
  `tabs_create_mcp`, `navigate`, `computer`, `read_page`, `get_page_text`, `find`, `form_input`,
  `file_upload`, `read_console_messages`, `read_network_requests`, `resize_window`, `gif_creator`),
  call `tabs_context_mcp` first and work in a **new tab**. Steve is signed in there; if not, stop and
  ask him to sign in (never type his credentials).
- **API:** a person's lake key as `Authorization: Bearer …` (the `lake` MCP server's header in
  `~/.claude.json` is Steve's), always with a `User-Agent` (Cloudflare refuses Python's default).
  `GET /v1/openapi.json` is the contract.
- **MCP:** the `mcp__lake__*` tools (loaded through ToolSearch), the same capabilities as the API.
- **Space:** the reviewer's own space. Everything the review creates is named `ux-review-<date>-…`
  and listed in the report; delete it only with Steve's yes (global rule on destructive actions).

## 1. Collect the claims first

Before touching the product, write the claims down (the report's claims ledger), each with its source:

- the home page and every page's lead sentence, `/llms.txt` and `/llms-full.txt`;
- the umbrella's [`docs/orama-studio.md`](../../../../docs/orama-studio.md) (§14 governs claims:
  built vs designed vs not);
- lake's `README.md`, `docs/api/*.md` headers (**Status:** lines), `docs/ui/`;
- capability descriptions in `/v1/openapi.json` (a description is a claim);
- the website's content records (`src/content/` in the `orama-website-v2` checkout) when a page links to lake.

## 2. Walk the jobs, on every surface

Each job below is walked **three times** — browser, API, MCP — from a clean start, as a newcomer who
knows only what the page, the OpenAPI description or the MCP tool list says. For each: record the
path (clicks or calls), the count of steps, wall time where a person waits, every error verbatim, and
every place you had to know something the product did not tell you.

| # | Job | The newcomer's question |
|---|---|---|
| J1 | Get oriented | Where am I, what can this do, where do I start? Is there help or documentation in the product? |
| J2 | Get a workspace | How do I get a place to work? How long until it is ready, and does the page say so? |
| J3 | **Load data** | How do I get my CSV / Parquet / database table in? Upload, connect a service, a store, the drive, a repository — which is the path, and where does the data show up? |
| J4 | Look at the data | Can I see columns, rows, types, counts? Query it? |
| J5 | Design a project | How do I say what I want to predict or find? What is a Project, a Pipeline, an Opportunity? |
| J6 | **Train a model** | From data I loaded, how do I train a model? What does it need, what runs, where is the result and its score? |
| J7 | Evaluate and approve | How good is it? How do I compare runs, approve a Pipeline? |
| J8 | Ship it | How do I use the model: an API call, a search index, a package, a deployment? Can I call it from outside? |
| J9 | Agents | Ask Orama a question; create an agent; run it once; schedule it; see its result. Connect an MCP server (Data → MCP Connections, lake#652): add it, test it, allow a read and a change, Try it, ask Ask Orama to use it (the change is proposed), create the connection's agent, and see the calls in Recent Calls. |
| J10 | Developer | Get an API key, read the API, connect MCP, make the first call from a terminal. |
| J11 | Organization | Invite someone, share a folder, see usage and activity, manage secrets. |
| J12 | Recover | A wrong input, an expired session, a job that failed: is the error clear and is there a way forward? |

Browser specifics: check each page at **1440 px and 390 px** (`resize_window`), read the console for
errors (`read_console_messages` with a pattern), note empty states, dead links, buttons that do
nothing, spinners without end, jargon, and words that differ from the API's. Record a GIF of J3 and J6
(`gif_creator`, named `lake-ux-<date>-<job>.gif`).

API/MCP specifics: can the job be finished with calls alone, in the order the descriptions suggest?
Are required inputs discoverable (a list call that yields the id the next call needs)? Are errors
actionable (`code`, `message`, `path`)? Do the API, MCP and page use the same names for the same
things?

## 3. Judge

For each claim: **kept**, **kept poorly** (works, but confusing or slow), **broken**, or **absent**.
For each job and surface: **done**, **done with help** (needed knowledge the product did not give),
or **stuck** (where, and why). Then the cross-cutting questions:

- **Parity:** a job possible on one surface but not another; a name that differs between them.
- **Docs:** is there an in-product place that explains the concepts and the paths (Docs, help, empty
  states that teach)? What did you have to read the source to learn?
- **The demo test:** what in J3 → J6 → J8 would embarrass us in front of a customer?

## 4. Report

Write `docs/reviews/lake-ux/<YYYY-MM-DD>.md` in liquid-bridge (and update that folder's `README.md`):

1. Target, revision, date, who ran it.
2. **Scorecard:** jobs × surfaces (done / with help / stuck), and claims kept / poorly / broken / absent.
3. **Per job:** the path taken on each surface, steps, time, what stalled, verbatim errors, screenshots
   or GIF names.
4. **Claims ledger:** each claim, its source, the verdict, the evidence.
5. **Findings,** ranked: blocks a customer → damages trust → rough edge → improvement, each with the
   issue it was filed as.
6. **What is good,** said plainly.
7. What the review created in the space (`ux-review-…`), left for Steve's call.

Commit and push the report (bridge: fast-forward to `main`).

## 5. File

Every finding becomes an issue (or a comment on an existing one) following `product-review` §4–5:
search first across `lake`, `zetta`, `orama-operator` and the agent repos; a title in the product's
own words; what was claimed (quote + source), what happens (exact reproduction on each surface), why a
customer cares, severity on the first line, and a **Done when** a worker can implement and a reviewer
can check. Group findings into one epic per review on `oramasearch/lake`, titled
`UX review <date>`, listing every issue, and link it from the report.

## Rules

- The review reads, runs and files; it never edits product code. Fixes are separate work on the issues.
- Never type credentials, never trigger a browser dialog (confirm/alert); if a page needs one, note it
  and move on.
- No destructive action (deleting data, revoking keys, removing members) without Steve's explicit yes.
- Confidential material (Metis, Zetta internals, customer names) never goes into an issue body.
- A claim is judged by what runs, never by a green test, a screenshot in `docs/`, or a closed issue.

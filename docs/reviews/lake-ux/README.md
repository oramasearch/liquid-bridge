# lake UX reviews

Dated reports from [`/lake-ux-review`](../../../.claude/skills/lake-ux-review/SKILL.md): each walks
the customer jobs (orient, workspace, load data, look at it, design, train, evaluate, ship, agents,
developer, organization, recover) through the browser, the REST API and MCP, judges every claim lake
makes against what runs, and links the epic of issues it filed.

| Report | Revision | Summary |
|---|---|---|
| [2026-09-27](2026-09-27.md) | 797ce72 | first run: the loop works and is fast, but no docs, no external predict, Project Agent false success; 12 issues, epic lake#260 |
| [2026-09-27b](2026-09-27b.md) | 51cd3ae → 029a579 | agents over the bus: the bus works; Ask Orama failed data questions (no SQL LIMIT, POST reads refused, no data guidance) and agents' markdown showed raw — fixed and deployed; the live suite `tools/e2e/agents.py` went 7/10 → 10/10; epic lake#288 |
| [2026-10-01](2026-10-01.md) | 36679e1 | after orama-bridge#136's build-out: four e2e runs pass and most pages are 13–81 ms, but the CSV → model demo breaks at training (zetta#1216 feature planner, lake#438 Project Agent apply 403) and the copy-paste curl omits `workspace_id`; 20 issues, epic lake#453 |
| [2026-10-10](2026-10-10.md) | 2229b8b (image 20261010p) | the web app, Drives, Secrets and Transcripts: the CSV → model → outside `predict` path works on every surface; REST engine errors arrive as Cloudflare's 502 page (lake#572), and Secrets for a person's own account and "study" wording are fixed on branches, not deployed; 29 issues plus 3 comments, epic lake#595 |
| [2026-10-18](2026-10-18.md) | 508f954 (v0.2.0, lake-dev) | a new user on lake-dev: CSV → query → one-sentence pipeline → train (AUC 0.823, 0.46 s) → publish → Try it works in the browser alone, and Ask Orama answers from the workspace correctly; the Opportunities scan fails (lake#795), Ask Orama's first answer gives wrong directions and a proposal fails on confirm, query columns show alphabetically; API and MCP not walked (no lake-dev key); 8 issues plus 3 comments, label `ux-proposed`, epic lake#820 |

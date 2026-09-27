# lake UX reviews

Dated reports from [`/lake-ux-review`](../../../.claude/skills/lake-ux-review/SKILL.md): each walks
the customer jobs (orient, workspace, load data, look at it, design, train, evaluate, ship, agents,
developer, organization, recover) through the browser, the REST API and MCP, judges every claim lake
makes against what runs, and links the epic of issues it filed.

| Report | Revision | Summary |
|---|---|---|
| [2026-09-27](2026-09-27.md) | 797ce72 | first run: the loop works and is fast, but no docs, no external predict, Project Agent false success; 12 issues, epic lake#260 |
| [2026-09-27b](2026-09-27b.md) | 51cd3ae → 029a579 | agents over the bus: the bus works; Ask Orama failed data questions (no SQL LIMIT, POST reads refused, no data guidance) and agents' markdown showed raw — fixed and deployed; the live suite `tools/e2e/agents.py` went 7/10 → 10/10; epic lake#288 |

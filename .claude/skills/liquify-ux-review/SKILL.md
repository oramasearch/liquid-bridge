---
name: liquify-ux-review
description: Review liquify, the IDE, as a person meets it - in the real native window, on its own and together with lake - judge how it looks against lake's own style and whether each job (open, clone from lake, edit, save, build, push to lake, review, collaborate) actually works, check every claim liquify and lake make about each other, write a dated report and file an epic of issues. Use when Steve says "liquify ux review", "review liquify", "make liquify beautiful", "does liquify work with lake", or before a liquify release or demo.
---

# /liquify-ux-review

The liquify companion of [`lake-ux-review`](../lake-ux-review/SKILL.md). It asks two questions:

1. **Does it look like it belongs next to lake?** The standard is **lake's own style**, the one its web app
   ships today, not the older `orama-design` repository and not liquify's own screenshots.
2. **Could a person who believed what liquify and lake say do each job without help?** Locally, and with
   lake as the place their work collects.

The issue rules of [`product-review`](../product-review/SKILL.md) (search before filing, the issue shape,
severities) apply unchanged. So does its stance: **a green test and a committed screenshot are not evidence
the window works.** liquify's UI once merged with green headless screenshot tests while the real window
drew a blank page. This review looks at the real window.

## 0. Set up

- **Build from the pins.** liquify at the head of `dev` (or the branch under review), against the sibling
  `modules/liquid` that liquid-bridge pins: `cmake -S . -B build -G Ninja && cmake --build build`. Record
  `./build/liquify version` (liquify and libliquid revisions) at the top of the report.
- **A liquid CLI of the same revision.** The CLI on `PATH` is usually stale (`liquid version` says what it
  is). Build one from the pinned checkout into a directory outside it:
  `cmake -S ../liquid -B <scratch>/liquid-cli -G Ninja -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF &&
  cmake --build <scratch>/liquid-cli --target liquid`. A CLI whose store format differs from liquify's
  gives false findings.
- **Known defects, without running tests.** Tests run only when a release is cut (umbrella
  `CLAUDE.md`, *No CI*). Read every `WILL_FAIL` in `docs/ui/native-acceptance.md`: each one is a
  known defect of the real window, and belongs in the report's scorecard as **stuck** until it is
  fixed. The native acceptance driver is still the way to see the real window: run it to capture
  frames, not as a test run.
- **Seeing the real window.** The reviewer must see pixels from the running application, not from
  `--screenshot`:
  - the desktop computer-use tools (`mcp__computer-use__*`, loaded through ToolSearch with the query
    `computer`; request access to the liquify process), which can also click and type; or
  - `screencapture -x -R<x>,<y>,<w>,<h>` with the window's frame from
    `osascript -e 'tell application "System Events" to get {position, size} of every window of (first process whose unix id is <pid>)'`.
    This needs **Screen Recording** permission for the terminal. Without it `screencapture` silently returns
    the desktop wallpaper: check the image before using it. Granting the permission is Steve's step (a
    security setting); ask him, never change it.
  - If neither is available, stop the visual part, say so in the report's first line, and continue with the
    jobs that the CLI and the test harness can prove.
- **lake.** The dev environment, `https://lake-dev.oramadev.net` (the old `lake.oramadev.net` is retired),
  its `GET /v1/server_info` revision recorded. Browser through the Claude in Chrome tools in a new tab,
  Steve signed in (never type his credentials). A token for liquid comes from Steve's lake key the way
  lake's own docs say (`LIQUID_TOKEN`); never print it, never put it in a URL or a report.
- **Space.** Everything the review creates (a repository on lake, a local repository, a review) is named
  `ux-review-<date>-…` and listed in the report. Delete only with Steve's yes.

## 1. Collect the claims first

Write the claims ledger before touching the product, each with its source:

- liquify: `README.md`, `CLAUDE.md` *Status*, `docs/design/status.md`, `docs/ui/*.md`
  (`first-run.md`, `design-system.md`, `what-the-window-shows.md`), `docs/editor/review.md`,
  `liquify --help`, the menu bar and the command palette's command names.
- lake about liquid and liquify: the repository page's *Clone and push* panel, `docs/ui/repositories.md`,
  `docs/ui/forge.md`, `docs/api/sync.md`, `docs/api/forge.md`, `/llms.txt`.
- liquid: `docs/features/21-liquify-ide.md` (the specification of the IDE) and the CLI's `--help`.
- **The style standard:** lake's `docs/ui/design-system.md` on lake's `dev` (fetch first). Take from it:
  the token roles, IBM Plex Sans and Mono, flat surfaces with hairline boundaries, blue action and focus,
  green/yellow/red status, violet for model and agent context, high density with low variance, the
  eyebrow + one title + supporting copy page frame, Title Case for titles and headings and sentence case
  for buttons and labels, every list with its empty and error state, light first with a full dark pair,
  reduced motion respected. Lake's own screenshots (`docs/ui/screenshots/`) show what that looks like.

## 2. Walk the jobs

Each job is done in the **real window** from a clean start (a fresh liquid home, no recent repositories), as a
newcomer who knows only what the window and the docs say. Then, where lake is involved, the result is
checked **on lake in the browser**. Record the path (clicks and keys), the count of steps, every error
verbatim, a screenshot of each screen, and every place you had to know something the product did not tell
you.

| # | Job | The newcomer's question |
|---|---|---|
| L1 | First launch | What is this, where do I start? Is there a way to get help? |
| L2 | Sign in to lake | How do I connect liquify to my lake account? Does it say who I am signed in as, and where? |
| L3 | Get a repository | Open a local one; create a new one; **clone one from lake** (find it on lake, get its URL, paste it). How long, and does the window say what is happening? |
| L4 | Find my way | Tree, Quick Open, symbol search, go to definition, breadcrumbs, back and forward |
| L5 | Edit and save | Type, undo, multi-cursor, find and replace, save. What is a drip, and do I see that one was made? |
| L6 | Build and test | F7 and F8 on a real project. Where is the output and the failure? |
| L7 | **Push to lake** | Send my work to lake (F9). Does it show up on lake's repository page, under Changes, with my name? |
| L8 | **Review** | See the reviews on lake from liquify, open one, comment at the cursor, approve. Does lake's page show the same comment and state? |
| L9 | Lake's other records | Issues, releases, artifacts, builds: can I see or reach them from liquify, or does it send me to the browser? |
| L10 | Collaborate | Two windows (or two people) on one repository: presence, attribution, conflicts |
| L11 | Make it mine | Settings, theme, fonts, keymap, the AI switch, lake accounts |
| L12 | Recover | lake unreachable, an expired or wrong token, an unreadable repository, a failed push. Is the message clear, with a way forward? |

Then the other direction: **from lake to liquify.** On lake's repository page, does anything say how to open it
in liquify, or offer to? Does lake's documentation name liquify at all?

## 3. Judge

- **The look**, screen by screen, against the style standard. Name what differs concretely ("the table
  header is a solid black bar with dark text on it", "every action is a full grey button", "the window title
  is the same size as body text"), in both themes, at the Retina and at 1x density where one is attached, and
  at a narrow and a wide window.
- **Each claim:** kept, kept poorly, broken, absent.
- **Each job:** done, done with help, stuck (where and why).
- **Parity with lake:** the same thing named differently in liquify, lake and the liquid CLI (for example a
  token variable, a review state, "drip" vs "change").
- **The demo test:** what in L3 → L5 → L7 → L8 would embarrass us in front of a developer.

## 4. Report

Write `docs/reviews/liquify-ux/<YYYY-MM-DD>.md` in liquid-bridge and index it in that folder's `README.md`:

1. Target: liquify and libliquid revisions, the lake host and revision, the date, who ran it, and what could
   not be run (with why) in the first lines.
2. Scorecard: jobs (done / with help / stuck), claims (kept / poorly / broken / absent), and the look.
3. Per job: the path, steps, what stalled, verbatim errors, screenshot names.
4. The look: screen by screen, the screenshot beside lake's equivalent and the differences.
5. Claims ledger.
6. Findings, ranked: blocks a person → damages trust → rough edge → improvement, each with its issue.
7. What is good, said plainly.
8. What the review created, left for Steve's call.

Screenshots go beside the report (`docs/reviews/liquify-ux/<date>/`), never anything showing a token, a
private path or another person's data. Commit and push (bridge: fast-forward to `main`).

## 5. File

Every finding becomes an issue, or a comment on the existing issue that already covers it (search
`oramasearch/liquify` first, then `liquid` and `lake`). The fix's repository owns the issue: the look and the
window in `liquify`, a missing library capability in `liquid`, a missing page or link in `lake`. Each issue
starts with **What / Why / How**, quotes the claim and its source, gives the exact reproduction, says why a
person cares, has its severity on the first line, and ends with a **Done when** a worker can implement and a
reviewer can check, including the real-window screenshot that proves it.

Group them under one epic on `oramasearch/liquify`, `liquify UX review <date>`, listing every issue in the
order to do them (the window works → it looks like lake → it works with lake → it is pleasant), and link the
epic from the report and from liquid-bridge's master epic.

## Rules

- The review reads, runs and files. It never edits product code; fixes are separate work on the issues.
- Never type credentials, never change a system or security setting, never trigger a modal dialog you
  cannot dismiss.
- No destructive action without Steve's explicit yes (global rule).
- liquify and liquid are headed for an open-source release: an issue body carries no customer name, no
  internal host beyond what the repo already names, no token and no private path.

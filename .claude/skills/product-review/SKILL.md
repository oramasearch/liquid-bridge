---
name: product-review
description: Test the whole product from a customer's point of view, compare what is promised against what runs, and file original issues for every inconsistency, gap and improvement
---

# /product-review

A review that judges the product, not the plan. It asks whether a person who believed our documents would be
satisfied by what actually runs, and it files issues when the answer is no. It never ticks a box; it opens
work.

## The stance

Read as an unimpressed customer who paid for this. A test suite passing is not evidence the product works;
a screenshot in `docs/` is not evidence the window renders; an issue marked done is not evidence the promise
is kept. liquify's UI leaves all merged with green headless screenshot tests while the real window drew a
blank page: that is the failure mode this review exists to catch.

## 1. Collect the promises

Write them down before touching the product, so the comparison is honest.

- liquid-bridge: `docs/action-plan.md` (phase exits), issue #7 (the super-epic and its "Done when"),
  `docs/decisions.md`, `docs/operations/slos.md`, the legal and publishing drafts.
- Each repository's `README.md`, `docs/README.md`, `docs/features/*` and `docs/design/*`: every sentence in
  the present tense is a claim.
- Closed issues in the area under review: their "Done when" lists are promises with a name attached.
- The live surfaces: https://lake.oramadev.net and its `/v1/openapi.json`, the built `liquify` application,
  the `liquid` CLI's own `--help` and `docs/reference/cli`.

## 2. Exercise the product

Use it the way a customer would, on this machine, from a clean state. No Docker (liquid-bridge decision 33).

- **liquid**: build it, then run the scenarios its documents advertise end to end: init a repository, wrap a
  build, resolve a dependency set, project a package, verify a proof, clone a drive folder. Read the output as
  a person: are the errors intelligible, are the verbs discoverable, does `--help` match the reference?
- **lake**: against https://lake.oramadev.net and a locally run instance, walk the surfaces a customer meets:
  sign up, create an organisation, push a repository, review a change, browse the drive, share a folder,
  publish and search an artifact, read the audit log. Check the pages in a browser at more than one width;
  check the API answers match `/v1/openapi.json`.
- **liquify**: **launch the built application and look at it.** Open a repository, edit, search, run a build,
  open every panel, switch themes, use the command palette, resize the window, try it on a second display
  scale. Compare what you see against `docs/ui/screenshots/`: if they disagree, the screenshots are the bug.
- **The runtime**: the operator's CRDs and the k0s distribution as an operator would meet them: apply the
  sample, read the status conditions, follow a runbook end to end and see whether its steps are real.

Record what you did, with the command or the click path, and what happened.

## 3. Judge

For each promise, one of: kept; kept but poorly (works, unpleasant or confusing); broken; absent. Then ask
the questions a plan never asks:

- Would a stranger get from install to first useful result without help? Where do they stall?
- Are the words in the interface the words a user would use, and consistent across CLI, API and pages?
- What is missing that a competent competitor has, that we never listed? Name it.
- What is slow, in numbers, where a person waits?
- What breaks if the network is gone, the disk is full, the token expired, the input is hostile?
- What would embarrass us in a demo?

## 4. Search before filing

Duplicate issues waste everyone. For each finding:

```sh
gh issue list --repo oramasearch/<repo> --state all --search "<distinctive words>" --limit 20 \
  --json number,title,state
```

Search every repository the finding could belong to, and the bridge. Then:

- **An open issue already covers it**: add a comment with your new evidence (what you ran, what you saw, the
  version or commit) and say plainly that it is still reproducible. Do not open a second issue.
- **A closed issue claimed it**: reopen it with the evidence, or if the original scope was narrower, open a
  new issue that cites the closed one and says what it missed.
- **Nothing covers it**: open an original issue.

## 5. File issues that can be worked

Every issue: a title naming the defect or the gap in the product's own vocabulary; what was promised and where
(a quote and a link); what actually happens, with the exact reproduction; why it matters to a customer; and a
**Done when** list a worker can implement and a reviewer can check. Add severity in the first line: blocks a
customer, damages trust, rough edge, or improvement. Never file a wish without an acceptance test.

File against the repository that owns the code. Cross-reference the bridge super-epic (#7) when a finding
contradicts a phase exit, and say so in a comment there.

## 6. Report

One message: how many promises were checked, how many kept, the issues opened or augmented with their
severities, and the two or three things you would fix first. If the product is good in an area, say that
plainly too; an honest review has both.

## Rules

No Docker on this host. Never edit product code during a review: this skill only reads, runs and files.
Never mark an issue done. Confidential material (Metis, Zetta internals) never leaves the machine and never
appears in an issue body.

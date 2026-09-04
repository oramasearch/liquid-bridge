#!/usr/bin/env python3
"""tree.py <epic> — resolve an epic (recursively through sub-epics) into its leaves.
<epic> is a GitHub issue URL or org/repo#N. Prints TSV: depth, repo, number, state, labels, title.
Each repo's issues are fetched once (one `gh issue list` per repo). The header line of an epic
(which links the master epic) is not followed, so recursion goes down the tree, never up.
"""
import json, re, subprocess, sys

URL = re.compile(r"https://github\.com/([\w.-]+)/([\w.-]+)/issues/(\d+)")

def parse(arg):
    m = URL.search(arg)
    if m: return m.group(1), m.group(2), int(m.group(3))
    m = re.match(r"([\w.-]+)/([\w.-]+)#(\d+)$", arg)
    if m: return m.group(1), m.group(2), int(m.group(3))
    sys.exit(f"cannot parse {arg!r}")

CACHE = {}
def issues(org, repo):
    key = (org, repo)
    if key not in CACHE:
        out = subprocess.run(["gh","issue","list","--repo",f"{org}/{repo}","--state","all","--limit","1000",
                              "--json","number,title,state,labels,body"], capture_output=True, text=True, check=True).stdout
        CACHE[key] = {i["number"]: {**i, "labels": [l["name"] for l in i["labels"]]} for i in json.loads(out)}
    return CACHE[key]

seen = set()
def walk(org, repo, n, depth):
    if (org, repo, n) in seen: return
    seen.add((org, repo, n))
    i = issues(org, repo).get(n)
    if not i:
        print(f"{depth}\t{repo}\t{n}\t?\t\t(not found)"); return
    print(f"{depth}\t{repo}\t{n}\t{i['state']}\t{','.join(i['labels'])}\t{i['title']}")
    if "epic" in i["labels"]:
        body = i["body"].split("\n", 1)[1] if "\n" in i["body"] else ""   # drop the header line
        for m in URL.finditer(body):
            walk(m.group(1), m.group(2), int(m.group(3)), depth + 1)

if __name__ == "__main__":
    walk(*parse(sys.argv[1] if len(sys.argv) > 1 else "https://github.com/oramasearch/liquid-bridge/issues/7"), 0)

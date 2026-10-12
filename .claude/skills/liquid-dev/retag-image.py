#!/usr/bin/env python3
"""usage: DOCKER_CONFIG=<dir> retag-image.py <repo> <existing-tag> <new-tag>   e.g. retag-image.py lake 20261012a v0.1.0
Publishes the manifest of oramasearch/<repo>:<existing-tag> under <new-tag> through the registry
API, so both tags name the same digest. Reads the push credential from DOCKER_CONFIG/config.json
and never prints it."""
import base64, json, os, sys, urllib.request, urllib.error

repo, src, dst = "oramasearch/" + sys.argv[1], sys.argv[2], sys.argv[3]
cfg = json.load(open(os.path.join(os.environ["DOCKER_CONFIG"], "config.json")))
auth = next(v["auth"] for k, v in cfg["auths"].items() if "docker.io" in k)
req = urllib.request.Request(
    f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{repo}:pull,push",
    headers={"Authorization": "Basic " + auth})
token = json.load(urllib.request.urlopen(req))["token"]
accept = ", ".join([
    "application/vnd.oci.image.index.v1+json", "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.docker.distribution.manifest.v2+json"])

def get(tag):
    r = urllib.request.Request(f"https://registry-1.docker.io/v2/{repo}/manifests/{tag}",
                               headers={"Authorization": "Bearer " + token, "Accept": accept})
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.read(), resp.headers["Content-Type"], resp.headers["Docker-Content-Digest"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, None, None
        raise

body, ctype, digest = get(src)
if body is None:
    sys.exit(f"{repo}:{src} not found")
_, _, existing = get(dst)
if existing == digest:
    print(f"{repo}:{dst} already names {digest}")
    sys.exit(0)
if existing is not None:
    sys.exit(f"refusing to move {repo}:{dst}: it names {existing}, not {digest}")
put = urllib.request.Request(f"https://registry-1.docker.io/v2/{repo}/manifests/{dst}", data=body,
                             method="PUT",
                             headers={"Authorization": "Bearer " + token, "Content-Type": ctype})
with urllib.request.urlopen(put) as resp:
    pushed = resp.headers["Docker-Content-Digest"]
_, _, check = get(dst)
print(f"{repo}:{src} {digest}\n{repo}:{dst} {check}\nsame digest: {check == digest == pushed}")

"""Deploy an exact green SHA from the CI job; credentials stay in environment."""

import json
import os
import re
import time
import urllib.error
import urllib.request


def api(path, payload=None):
    request = urllib.request.Request(
        "https://api.render.com/v1/" + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Authorization": "Bearer " + os.environ["RENDER_API_KEY"],
                 "Content-Type": "application/json", "Accept": "application/json"},
        method="POST" if payload is not None else "GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"Render API returned HTTP {error.code}; inspect provider dashboard.") from None


def deploy():
    sha = os.environ["GITHUB_SHA"]
    service = os.environ["RENDER_SERVICE_ID"]
    if not re.fullmatch(r"[0-9a-f]{40}", sha) or not re.fullmatch(r"srv-[a-z0-9]+", service):
        raise ValueError("Invalid deployment SHA/service identifier.")
    if os.environ.get("GITHUB_EVENT_NAME") != "push" or os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise RuntimeError("Only a successful main push workflow may deploy.")
    configuration = api(f"services/{service}")
    disabled = configuration.get("autoDeployTrigger") == "off" if "autoDeployTrigger" in configuration else configuration.get("autoDeploy") == "no"
    if not disabled:
        raise RuntimeError("Disable platform auto-deploy before using the CI deployment job.")
    if configuration.get("branch") != "main" or configuration.get("repo") != "https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2":
        raise RuntimeError("Service must track this repository's main branch.")
    url = configuration["serviceDetails"]["url"]
    if not url.startswith("https://"):
        raise RuntimeError("Public HTTPS service URL required.")
    result = api(f"services/{service}/deploys", {"commitId": sha})
    deploy_id = result["id"]
    print(f"Requested deployment {deploy_id} for {sha}.")
    for _ in range(90):
        result = api(f"services/{service}/deploys/{deploy_id}")
        status = result["status"]
        if status == "live":
            if result.get("commit", {}).get("id") != sha:
                raise RuntimeError("Live deployment commit differs from tested SHA.")
            with urllib.request.urlopen(url + "/health", timeout=30) as response:
                if response.status != 200 or json.load(response) != {"status": "ok", "database": "ok"}:
                    raise RuntimeError("Post-deploy readiness failed.")
            print(f"Verified live commit {sha}; HTTPS /health returned 200: {url}")
            return
        if status in {"build_failed", "update_failed", "pre_deploy_failed", "canceled", "deactivated"}:
            raise RuntimeError(f"Deployment ended with status {status}.")
        time.sleep(10)
    raise RuntimeError("Deployment readiness timed out; inspect provider before retrying.")


if __name__ == "__main__":
    deploy()

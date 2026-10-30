"""Load the Git history of one file into ChronoRAG, one document version per day.

Usage (backend must be running):
    python scripts/ingest_git_history.py <path-to-cloned-repo> <file-path-inside-repo> "<title>"

Example:
    python scripts/ingest_git_history.py ~/Desktop/site-policy Policies/github-terms-of-service.md "GitHub Terms of Service"

Notes:
- The version date is the commit date, which may differ from the date a policy officially took effect.
- If several commits happen on the same day, only the last one is kept (one version per day).
- Consecutive commits with identical file content are skipped.
"""
import argparse
import subprocess
import sys
from pathlib import Path

import requests

API = "http://localhost:8000"


def git(repo: str, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", repo, *args], capture_output=True, text=True, check=True
    )
    return result.stdout


def history(repo: str, path: str) -> list[tuple[str, str]]:
    """Returns [(date, commit_sha)] oldest first, one entry per calendar day."""
    out = git(repo, "log", "--reverse", "--format=%H|%as", "--", path)
    per_day: dict[str, str] = {}
    for line in out.splitlines():
        sha, date = line.split("|")
        per_day[date] = sha  # a later commit on the same day replaces the earlier one
    return sorted((date, sha) for date, sha in per_day.items())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo")
    parser.add_argument("path")
    parser.add_argument("title")
    args = parser.parse_args()

    repo = str(Path(args.repo).expanduser())
    existing = requests.get(f"{API}/documents", timeout=30).json()
    if any(d["title"] == args.title for d in existing):
        sys.exit(f'"{args.title}" already exists. Delete it first (DELETE /documents/<id>).')

    commits = history(repo, args.path)
    print(f"{len(commits)} daily versions found.")

    doc_id = None
    previous_content = None
    saved = 0
    for date, sha in commits:
        try:
            content = git(repo, "show", f"{sha}:{args.path}")
        except subprocess.CalledProcessError:
            print(f"{date}: file does not exist in this commit, skipped")
            continue
        if not content.strip() or content == previous_content:
            continue
        previous_content = content

        if doc_id is None:
            res = requests.post(
                f"{API}/documents",
                data={"title": args.title, "effective_date": date, "text": content},
                timeout=900,
            )
        else:
            res = requests.post(
                f"{API}/documents/{doc_id}/versions",
                data={"effective_date": date, "text": content},
                timeout=900,
            )
        if res.status_code != 200:
            print(f"{date}: failed ({res.status_code}) {res.text[:200]}")
            continue
        body = res.json()
        if doc_id is None:
            doc_id = body["document"]["id"]
        saved += 1
        print(
            f"{date} -> version {body['version_number']} "
            f"(added {body['chunks_added']}, reused {body['chunks_reused']}, closed {body['chunks_closed']})"
        )
    print(f"Done. {saved} versions saved. Document id = {doc_id}")


if __name__ == "__main__":
    main()
    
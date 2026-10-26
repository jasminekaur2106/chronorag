"""Loads the three sample policy versions into a running backend.

Usage (backend must be running):  python scripts/seed_demo.py
"""
import sys
from pathlib import Path

import requests

API = "http://localhost:8000"
TITLE = "Acme Refund Policy"
SAMPLES = Path(__file__).resolve().parent.parent / "sample_data"
VERSIONS = [
    ("acme_refund_policy_v1.txt", "2025-01-01"),
    ("acme_refund_policy_v2.txt", "2025-06-01"),
    ("acme_refund_policy_v3.txt", "2026-02-01"),
]


def main() -> None:
    existing = requests.get(f"{API}/documents", timeout=30).json()
    if any(d["title"] == TITLE for d in existing):
        print(f'"{TITLE}" already exists. Delete it first (DELETE /documents/<id>) to reseed.')
        sys.exit(0)

    doc_id = None
    for filename, effective_date in VERSIONS:
        path = SAMPLES / filename
        with open(path, "rb") as fh:
            files = {"file": (filename, fh, "text/plain")}
            if doc_id is None:
                res = requests.post(
                    f"{API}/documents",
                    data={"title": TITLE, "effective_date": effective_date},
                    files=files,
                    timeout=300,
                )
            else:
                res = requests.post(
                    f"{API}/documents/{doc_id}/versions",
                    data={"effective_date": effective_date},
                    files=files,
                    timeout=300,
                )
        res.raise_for_status()
        body = res.json()
        if doc_id is None:
            doc_id = body["document"]["id"]
        print(
            f"{filename} -> version {body['version_number']} "
            f"(added {body['chunks_added']}, reused {body['chunks_reused']}, closed {body['chunks_closed']})"
        )
    print(f"Done. Document id = {doc_id}")


if __name__ == "__main__":
    main()

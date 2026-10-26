"""Compares ChronoRAG (time-aware retrieval) against a plain-RAG baseline.

Usage (backend running, sample data seeded):
    python eval/run_eval.py --sleep 3

A question PASSES when the answer contains at least one `expect_any` phrase and none of the
`forbid_any` phrases. A question where the AI call fails is reported as ERROR and left out of
the scores, so one flaky request cannot stop the whole run.
"""
import argparse
import json
import time
from pathlib import Path

import requests

API = "http://localhost:8000"
HERE = Path(__file__).resolve().parent


def passes(answer, expect_any, forbid_any):
    text = answer.lower()
    has_expected = any(e.lower() in text for e in expect_any) if expect_any else True
    has_forbidden = any(f.lower() in text for f in forbid_any)
    return has_expected and not has_forbidden


def ask(payload):
    """Returns (answer, error). Never raises."""
    try:
        res = requests.post(f"{API}/query", json=payload, timeout=240)
    except requests.RequestException as exc:
        return None, type(exc).__name__
    if res.status_code != 200:
        try:
            detail = res.json().get("detail", res.text)
        except ValueError:
            detail = res.text
        return None, f"HTTP {res.status_code}: {str(detail)[:300]}"
    return res.json()["answer"], None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", default="Acme Refund Policy")
    parser.add_argument("--sleep", type=float, default=1.0, help="seconds between AI calls")
    args = parser.parse_args()

    docs = requests.get(f"{API}/documents", timeout=30).json()
    match = [d for d in docs if d["title"] == args.title]
    if not match:
        raise SystemExit(f'Document "{args.title}" not found. Run scripts/seed_demo.py first.')
    doc_id = match[0]["id"]

    questions = json.loads((HERE / "questions.json").read_text())
    scores = {True: 0, False: 0}
    scored = 0
    rows = []

    for q in questions:
        row = {"question": q["question"], "as_of": q["as_of"]}
        results = {}
        for time_aware in (True, False):
            answer, error = ask(
                {
                    "question": q["question"],
                    "as_of": q["as_of"],
                    "document_id": doc_id,
                    "time_aware": time_aware,
                }
            )
            key = "time_aware" if time_aware else "baseline"
            if error:
                results[time_aware] = "ERROR"
                row[key] = {"error": error}
                print(f"   {key} error -> {error}")
            else:
                ok = passes(answer, q["expect_any"], q["forbid_any"])
                results[time_aware] = "PASS" if ok else "FAIL"
                row[key] = {"pass": ok, "answer": answer}
            time.sleep(args.sleep)

        if "ERROR" not in results.values():
            scored += 1
            for mode in (True, False):
                scores[mode] += int(results[mode] == "PASS")
        rows.append(row)
        print(
            f"{q['as_of']} | {q['question'][:40]:40} | "
            f"time-aware: {results[True]} | baseline: {results[False]}"
        )

    print()
    if scored:
        print(f"Time-aware RAG : {scores[True]}/{scored} ({100 * scores[True] / scored:.0f}%)")
        print(f"Plain RAG      : {scores[False]}/{scored} ({100 * scores[False] / scored:.0f}%)")
    skipped = len(questions) - scored
    if skipped:
        print(f"{skipped} question(s) skipped because the AI call failed.")
    (HERE / "results.json").write_text(json.dumps(rows, indent=2))
    print("Full answers saved to eval/results.json")


if __name__ == "__main__":
    main()
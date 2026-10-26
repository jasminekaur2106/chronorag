from collections import Counter
from difflib import SequenceMatcher

from .chunking import chunk_text

CHANGE_TYPES = {"modified", "reworded_only"}

CLASSIFY_SYSTEM = (
    "You compare two versions of the same passage from a document. "
    "Reply with JSON only, no other text, in this exact shape: "
    '{"change_type": "modified" or "reworded_only", "summary": "one sentence"}. '
    "Use reworded_only when the meaning, numbers, conditions and obligations are identical "
    "and only the wording changed. Use modified when any fact, number, condition, deadline "
    "or obligation changed. In the summary, state precisely what changed and include the "
    "old and new values when there are any."
)


def classify_change(old: str, new: str) -> dict:
    """Ask the LLM whether a changed passage is a real change or just rewording."""
    from . import llm  # lazy import so tests run without any SDK installed

    try:
        raw = llm.generate(CLASSIFY_SYSTEM, f"OLD VERSION:\n{old}\n\nNEW VERSION:\n{new}", 600)
        data = llm.parse_json(raw)
        change_type = data.get("change_type")
        if change_type not in CHANGE_TYPES:
            change_type = "modified"
        return {"change_type": change_type, "summary": str(data.get("summary", "")).strip()}
    except Exception as exc:  # network error, bad JSON, missing key, ...
        return {
            "change_type": "modified",
            "summary": f"(LLM classification failed: {type(exc).__name__})",
        }


SIMILARITY_THRESHOLD = 0.4


def _align(old_part: list[str], new_part: list[str]) -> list[tuple]:
    """Order-preserving alignment of two lists of paragraphs by text similarity.

    difflib only tells us "this region changed". When a modified paragraph sits next to a
    newly inserted one, we still want to know which old paragraph became which new one.
    This is a small dynamic-programming alignment (like longest-common-subsequence, but it
    maximises total similarity instead of counting exact matches).
    Returns ("pair", old_idx, new_idx), ("del", old_idx, None) or ("ins", None, new_idx).
    """
    n, m = len(old_part), len(new_part)
    sim = [[SequenceMatcher(None, o, w).ratio() for w in new_part] for o in old_part]
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            best = max(dp[i - 1][j], dp[i][j - 1])
            if sim[i - 1][j - 1] >= SIMILARITY_THRESHOLD:
                best = max(best, dp[i - 1][j - 1] + sim[i - 1][j - 1])
            dp[i][j] = best

    ops: list[tuple] = []
    i, j = n, m
    while i > 0 and j > 0:
        if (
            sim[i - 1][j - 1] >= SIMILARITY_THRESHOLD
            and abs(dp[i][j] - (dp[i - 1][j - 1] + sim[i - 1][j - 1])) < 1e-9
        ):
            ops.append(("pair", i - 1, j - 1))
            i, j = i - 1, j - 1
        elif abs(dp[i][j] - dp[i - 1][j]) < 1e-9:
            ops.append(("del", i - 1, None))
            i -= 1
        else:
            ops.append(("ins", None, j - 1))
            j -= 1
    while i > 0:
        ops.append(("del", i - 1, None))
        i -= 1
    while j > 0:
        ops.append(("ins", None, j - 1))
        j -= 1
    ops.reverse()
    return ops


def _entry(change_type: str, old, new, summary) -> dict:
    return {"change_type": change_type, "old": old, "new": new, "summary": summary}


def compute_diff(old_text: str, new_text: str, use_llm: bool = True) -> dict:
    """Paragraph-level diff, then (optionally) an LLM pass that labels each change."""
    old_blocks = chunk_text(old_text)
    new_blocks = chunk_text(new_text)
    matcher = SequenceMatcher(None, old_blocks, new_blocks, autojunk=False)

    changes: list[dict] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "insert":
            for block in new_blocks[j1:j2]:
                changes.append(_entry("added", None, block, "New passage added."))
        elif tag == "delete":
            for block in old_blocks[i1:i2]:
                changes.append(_entry("removed", block, None, "Passage removed."))
        else:  # replace: a region where old and new paragraphs differ
            old_part, new_part = old_blocks[i1:i2], new_blocks[j1:j2]
            if len(old_part) == 1 and len(new_part) == 1:
                ops = [("pair", 0, 0)]  # a lone paragraph that changed is a modification
            else:
                ops = _align(old_part, new_part)
            for kind, oi, ni in ops:
                if kind == "ins":
                    changes.append(_entry("added", None, new_part[ni], "New passage added."))
                elif kind == "del":
                    changes.append(_entry("removed", old_part[oi], None, "Passage removed."))
                else:
                    old_block, new_block = old_part[oi], new_part[ni]
                    if use_llm:
                        result = classify_change(old_block, new_block)
                    else:
                        result = {"change_type": "modified", "summary": None}
                    changes.append(
                        _entry(result["change_type"], old_block, new_block, result["summary"])
                    )

    counts = Counter(change["change_type"] for change in changes)
    return {"changes": changes, "counts": dict(counts)}

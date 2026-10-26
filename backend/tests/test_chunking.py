from app.chunking import chunk_text

DOC = """Refund Policy

Refund window

Customers may request a refund within 30 days of purchase.

Contact

Refund requests are handled by email at support@example.com.
"""


def test_headings_are_merged_into_the_next_paragraph():
    chunks = chunk_text(DOC)
    assert len(chunks) == 2
    assert chunks[0].startswith("Refund Policy\nRefund window\nCustomers may")
    assert chunks[1].startswith("Contact\nRefund requests")


def test_long_paragraph_is_split_on_sentences():
    long_paragraph = " ".join(f"This is sentence number {i} of a very long paragraph." for i in range(60))
    chunks = chunk_text(long_paragraph, max_chars=300)
    assert len(chunks) > 1
    assert all(len(c) <= 300 for c in chunks)


def test_editing_one_paragraph_changes_only_that_chunk():
    before = chunk_text(DOC)
    after = chunk_text(DOC.replace("30 days", "14 days"))
    assert len(before) == len(after)
    assert before[0] != after[0]
    assert before[1] == after[1]  # unchanged chunk -> same text -> same hash -> reusable

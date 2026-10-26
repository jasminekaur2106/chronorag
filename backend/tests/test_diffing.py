from app.diffing import compute_diff

V1 = """Refund window

Customers may request a refund within 30 days of purchase.

Digital goods

Digital goods can be refunded within 30 days if they have not been downloaded.

Contact

Refund requests are handled by email at support@example.com.
"""

V2 = """Refund window

Customers may request a refund within 14 days of purchase.

Digital goods

Digital goods are not eligible for refunds once downloaded or accessed.

Gift cards

Gift cards are non-refundable and cannot be exchanged.

Contact

Refund requests are handled by email at support@example.com.
"""


def test_diff_finds_modified_and_added_passages():
    result = compute_diff(V1, V2, use_llm=False)
    assert result["counts"] == {"modified": 2, "added": 1}
    added = [c for c in result["changes"] if c["change_type"] == "added"][0]
    assert "Gift cards" in added["new"]


def test_identical_versions_have_no_changes():
    result = compute_diff(V1, V1, use_llm=False)
    assert result["changes"] == []

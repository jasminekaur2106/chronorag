import re

MAX_CHARS = 900
MIN_CHARS = 25  # shorter paragraphs (usually headings) are glued onto the next paragraph


def _split_paragraphs(text: str) -> list[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = re.split(r"\n\s*\n", text)
    cleaned = [re.sub(r"\s+", " ", p).strip() for p in paragraphs]
    return [p for p in cleaned if p]


def _split_long(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    sentences = re.split(r"(?<=[.!?])\s+", text)
    pieces: list[str] = []
    current = ""
    for sentence in sentences:
        if current and len(current) + 1 + len(sentence) > max_chars:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        pieces.append(current)
    return pieces


def chunk_text(text: str, max_chars: int = MAX_CHARS, min_chars: int = MIN_CHARS) -> list[str]:
    """Paragraph-based chunking.

    Why not fixed-size windows? If you insert one sentence at the top of a document, every
    fixed-size window after it shifts, so every chunk changes and nothing can be reused
    between versions. Paragraph boundaries stay put, so unchanged paragraphs keep the
    same hash and we do not have to re-embed them.
    """
    merged: list[str] = []
    carry: list[str] = []
    for paragraph in _split_paragraphs(text):
        if len(paragraph) < min_chars:
            carry.append(paragraph)
            continue
        merged.append("\n".join(carry + [paragraph]))
        carry = []
    if carry:
        if merged:
            merged[-1] += "\n" + "\n".join(carry)
        else:
            merged.append("\n".join(carry))

    chunks: list[str] = []
    for block in merged:
        chunks.extend(_split_long(block, max_chars))
    return chunks

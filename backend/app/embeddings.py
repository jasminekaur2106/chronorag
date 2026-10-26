from functools import lru_cache

from .config import settings


@lru_cache(maxsize=1)
def _model():
    # Imported lazily: loading sentence-transformers takes a few seconds.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: list[str]):
    """Returns a list of normalized numpy vectors (cosine similarity == dot product)."""
    vectors = _model().encode(texts, normalize_embeddings=True)
    return list(vectors)


def embed_query(text: str):
    return embed_texts([text])[0]

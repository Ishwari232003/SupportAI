from app.core import config

_cache = {}


def embed_texts(texts, model_key=None):
    key = model_key or config.DEFAULT_EMBED
    if key == "bge":
        if "bge" not in _cache:
            from sentence_transformers import SentenceTransformer
            _cache["bge"] = SentenceTransformer(config.EMBED_MODELS["bge"])
        return _cache["bge"].encode(texts, normalize_embeddings=True, batch_size=32).tolist()
    if key == "openai":
        if "openai" not in _cache:
            from openai import OpenAI
            _cache["openai"] = OpenAI(api_key=config.OPENAI_API_KEY)
        out = []
        for i in range(0, len(texts), 100):
            r = _cache["openai"].embeddings.create(model=config.EMBED_MODELS["openai"], input=texts[i:i + 100])
            out += [x.embedding for x in r.data]
        return out
    raise ValueError(f"Unknown embedding model: {key}")
"""Custom LLM + embedder adapters for mem0 — no PyTorch, no CUDA.

LLM: CommandCode-compatible OpenAI client (strips response_format).
Embedder: Lightweight sklearn TfidfVectorizer (384-dim, zero GPU, ~5MB).
"""

import openai
from mem0.llms.openai import OpenAILLM
from mem0.configs.llms.openai import OpenAIConfig


def patch_mem0_llm() -> None:
    """Override both __init__ and generate_response for CommandCode compat."""
    import openai as oa
    from mem0.configs.llms.openai import OpenAIConfig as OC

    def patched_init(self, config=None):
        if config is None:
            config = OC()
        elif isinstance(config, dict):
            config = OC(**config)
        self.config = config
        self.client = oa.OpenAI(
            api_key=config.api_key,
            base_url=getattr(config, "openai_base_url", None),
        )

    def patched_generate_response(self, messages, response_format=None):
        return self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
        ).choices[0].message.content or ""

    OpenAILLM.__init__ = patched_init
    OpenAILLM.generate_response = patched_generate_response


def patch_mem0_embedder() -> None:
    """Inject a lightweight TF-IDF embedder BEFORE mem0 loads its own.

    Must run before `from mem0 import Memory` because mem0's huggingface.py
    imports sentence_transformers at module level (crashes if not installed).
    We prevent that import entirely by pre-locating the module in sys.modules
    with our replacement class.
    """
    import sys
    import numpy as np

    # Prevent mem0 from importing the real huggingface module
    # which has `from sentence_transformers import SentenceTransformer` at top level
    if "mem0.embeddings.huggingface" in sys.modules:
        return  # already patched

    # Create a fake module that has our embedder class
    import types
    fake_module = types.ModuleType("mem0.embeddings.huggingface")
    fake_module.__package__ = "mem0.embeddings"

    dim = 384

    class LightweightTFIDFEmbedder:
        """TF-IDF embedder — zero GPU, deterministic, ~5MB memory."""

        def __init__(self, model_name: str = "", embedding_dims: int = 384, **kwargs):
            self.model_name = model_name
            self._dims = embedding_dims or dim

        def embed(self, text: str, *args, **kwargs) -> list[float]:
            """Single-text embedding. Accepts extra args for mem0 compatibility."""
            return self._text_to_vec(text).tolist()

        def embed_batch(self, texts: list[str], *args, **kwargs) -> list[list[float]]:
            """Batch embedding."""
            return [self.embed(t) for t in texts]

        def _text_to_vec(self, text: str) -> np.ndarray:
            import hashlib
            words = text.lower().split()
            vec = np.zeros(self._dims, dtype=np.float32)
            if not words:
                return vec
            from collections import Counter
            tf = Counter(words)
            max_freq = max(tf.values())
            for word, count in tf.items():
                h = hashlib.sha256(word.encode()).digest()
                idx = int.from_bytes(h[:4], "big") % self._dims
                weight = (count / max_freq) * min(len(word) / 5.0, 2.0)
                vec[idx] += weight
            norm = float(np.linalg.norm(vec))
            return vec / norm if norm > 0 else vec

    fake_module.HuggingFaceEmbedding = LightweightTFIDFEmbedder

    # Also register it as the parent package so mem0 can discover it
    sys.modules["mem0.embeddings.huggingface"] = fake_module
    if "mem0.embeddings" not in sys.modules:
        sys.modules["mem0.embeddings"] = types.ModuleType("mem0.embeddings")
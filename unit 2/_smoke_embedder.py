"""
A stand-in embedding model, used only by this repository's own smoke test.

Students should never touch this and never set AI201_FAKE_EMBEDDINGS. It exists
so the pipeline can be exercised in an automated environment that can't
download the real model — for example when checking that a change to the
starter didn't break anything.

It produces deterministic vectors from word hashes. They are good enough to
show that data flows correctly through the pipeline. They are NOT good enough
to say anything about retrieval quality or about where a relevance threshold
belongs. The staff repo's `_staff/calibrate.py` does that with the real
model.
"""

import hashlib
import math
import re

DIMS = 384


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


class FakeEmbedder:
    def encode(self, texts, show_progress_bar: bool = False):
        return _Array([self._one(t) for t in texts])

    def _one(self, text: str) -> list[float]:
        vector = [0.0] * DIMS
        for token in _tokens(text):
            digest = hashlib.md5(token.encode()).digest()
            slot = int.from_bytes(digest[:4], "big") % DIMS
            sign = 1.0 if digest[4] % 2 else -1.0
            vector[slot] += sign
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]


class _Array(list):
    """Just enough of a numpy array for store.embed's .tolist() call."""

    def tolist(self):
        return list(self)

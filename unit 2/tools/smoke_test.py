#!/usr/bin/env python3
"""
STAFF TOOL — end-to-end check that the starter still works.

Students don't run this; they run `test.py`, which checks their environment.
This checks the *starter itself*, and is what you run after changing any of the
pipeline code.

    python tools/smoke_test.py

It exercises every stage against every shipped corpus, using a stand-in
embedding model and a stand-in model call so it needs neither a model download
nor an API key. That makes it fast and CI-friendly, and it means the distances
it sees are meaningless — it proves the plumbing, not the quality. The staff
repo's `_staff/calibrate.py` covers quality, with the real model.
"""

import os
import sys
import tempfile
from pathlib import Path

os.environ["AI201_FAKE_EMBEDDINGS"] = "1"
os.environ.setdefault("GEMINI_API_KEY", "smoke-test-not-a-real-key")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402
import generate  # noqa: E402
from ingest import load_documents  # noqa: E402
from chunker import split_documents, fallback_split  # noqa: E402
from store import build_index, search  # noqa: E402
import gate  # noqa: E402

failures = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f"\n       {detail}" if detail else ""))
    if not condition:
        failures.append(name)


class FakeResponse:
    text = "According to admin_housing_lottery.txt, the lottery is not fully random."


def fake_client():
    class Models:
        def __init__(self):
            self.calls = 0

        def generate_content(self, **kwargs):
            self.calls += 1
            return FakeResponse()

    class Client:
        def __init__(self):
            self.models = Models()

    return Client()


def main():
    print("AI201 unit 1 starter — smoke test\n" + "-" * 60)

    # Route every model call to the fake.
    generate._client = fake_client()

    corpora = ["campus_life", "advice_threads", "city_guides", "practice"]

    for corpus in corpora:
        print(f"\n{corpus}")
        docs = load_documents(corpus)
        check(f"  loads documents", len(docs) > 0, f"{len(docs)} documents")

        chunks = split_documents(docs)
        check(f"  chunks them", len(chunks) > 0, f"{len(chunks)} chunks")
        check(
            f"  chunks carry a source and a producing function",
            all(c.source and c.produced_by for c in chunks),
        )
        check(
            f"  no chunk is empty",
            all(c.text.strip() for c in chunks),
        )

        count = build_index(chunks, corpus=corpus)
        check(f"  indexes", count == len(chunks))

        results = search("what should I know about this?", corpus=corpus)
        check(f"  retrieves", len(results) > 0, f"top-{len(results)}")
        check(
            f"  results are ordered nearest first",
            all(
                results[i].distance <= results[i + 1].distance
                for i in range(len(results) - 1)
            ),
        )
        check(
            f"  distances are cosine-shaped (0 to 2)",
            all(0.0 <= r.distance <= 2.0 for r in results),
            f"range {min(r.distance for r in results):.3f}"
            f"–{max(r.distance for r in results):.3f}",
        )

    print("\ncross-cutting")

    # The collection really is cosine, not Chroma's default squared L2.
    import chromadb

    client = chromadb.PersistentClient(
        path=str(config.CHROMA_DIR),
        settings=chromadb.config.Settings(anonymized_telemetry=False),
    )
    collection = client.get_collection(config.collection_name("campus_life"))
    space = (collection.metadata or {}).get("hnsw:space")
    check("  collection uses cosine distance", space == "cosine", f"hnsw:space={space}")

    # The gate refuses when nothing is close, and passes when something is.
    close = gate.check(
        [type("R", (), {"distance": 0.20})()], threshold=0.6
    )
    far = gate.check([type("R", (), {"distance": 0.95})()], threshold=0.6)
    check("  gate passes a close match", close.passed)
    check("  gate refuses a distant one", far.passed is False)
    check("  gate refuses when nothing came back", gate.check([]).passed is False)

    # Two index variants can coexist — week 2 compares chunkings.
    docs = load_documents("campus_life")
    build_index(fallback_split(docs, chunk_size=300, overlap=50),
                corpus="campus_life", variant="v2")
    a = search("housing lottery", corpus="campus_life", variant="default")
    b = search("housing lottery", corpus="campus_life", variant="v2")
    check("  two chunkings can be indexed side by side", len(a) > 0 and len(b) > 0)

    # generate(): cache, counter, and cache=False all behave.
    with tempfile.TemporaryDirectory() as tmp:
        config.CACHE_DIR = Path(tmp)
        generate._session_calls = 0
        generate._cache_hits = 0

        generate.generate("a test prompt")
        first = generate.call_count()
        generate.generate("a test prompt")
        second = generate.call_count()
        check("  identical prompt is served from cache", first == second == 1)

        generate.generate("a test prompt", cache=False)
        check("  cache=False forces a real call", generate.call_count() == 2)

        check("  usage() reports something readable", "model calls" in generate.usage(),
              generate.usage())

    # The runaway guard actually stops.
    generate._session_calls = config.SESSION_REQUEST_BUDGET
    try:
        generate.generate("should not run", cache=False)
        check("  session budget guard stops runaway loops", False)
    except generate.QuotaGuard:
        check("  session budget guard stops runaway loops", True)
    generate._session_calls = 0

    print("\n" + "-" * 60)
    if failures:
        print(f"{len(failures)} FAILED: {', '.join(failures)}")
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()

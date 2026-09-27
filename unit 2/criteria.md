# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in week 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next week costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:**
The `campus_life` corpus has dedicated single-topic files for administrative rules, course workloads, dorm laundry, and dining halls. With top-k set to 5, vector search should reliably surface the primary document in the top 5 results for at least 4 questions, leaving 1 allowance for subtle vocabulary variations between colloquial student terms and administrative phrasing.

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:**
5 of 5 is necessary and achievable because the generation prompt strictly mandates source attribution and appends `Source: filename` from the metadata attached to every retrieved chunk. Any generated answer lacking a source indicates a prompt leakage or hallucination failure.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" —
in at least 4 of 5 tries.

**Why this target:**
The 5 out-of-scope questions in `OUT_OF_SCOPE` (e.g., world history, mechanical repair, programming) share almost zero vocabulary with university campus life. Their retrieval distances sit consistently above 0.70, well above our relevance cutoff. A target of 4 of 5 gives an honest buffer against any stray vector embeddings collision.

---

## 4. Chunk completeness and fragment prevention

At least 4 of 5 sampled chunks read as a complete, self-contained thought without sentences cut in half, and 0% of chunks in the indexed corpus are shorter than 80 characters.

**Why this target:**
The `campus_life` documents average ~317 characters across 1–3 short paragraphs. Splitting by natural paragraph boundaries ensures every chunk retains full contextual meaning, and an 80-character lower threshold guarantees no trailing fragments (like 2-character remnants) pollute retrieval.

---

## 5. Primary source rank-1 retrieval accuracy

For at least 4 of my 5 test questions, the closest retrieved chunk (rank 1 by cosine distance) comes directly from the ground-truth primary document rather than a peripheral cross-reference.

**Why this target:**
Because `campus_life` documents are topical and focused, the most relevant chunk should not merely appear in the top-5 window; it should be ranked first by embedding similarity. Setting this target at 4 of 5 tests whether our chunking strategy preserves query-matching signal at the very top of the vector ranking.



---

<!-- ─────────────────────────────────────────────────────────────────────────
     WEEK 2 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 1. Retrieved chunks contain the answer

         For at least 4 of my 5 test questions, the retrieved chunks include
         one that contains the answer.

         **Why this target:** ...

         > **Revised in week 2:** For at least 4 of 5 questions, the top three
         > results contain the answer.
         >
         > **Why revised:** I couldn't judge "the chunks include one that
         > contains the answer" the same way twice — I scored two questions
         > differently on Monday than on Wednesday. The new version is
         > something I can actually check.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said 4 of 5 but got 2 of 5, so 2 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.

     The whole reason the originals stay visible is so someone can see what you
     said before you knew the answer.
     ───────────────────────────────────────────────────────────────────────── -->

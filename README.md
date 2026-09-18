# The Unofficial Guide

**Author:** Jivan Devkota  
**Corpus:** `campus_life`

---

# Week 1

## What This Does

The Unofficial Guide is a retrieval-augmented question-answering system built on the `campus_life` corpus of 88 peer-written student advice documents. It makes institutional knowledge and student lore searchable—answering specific queries about housing lottery mechanics, dorm facilities and laundry, dining hall hours and specialties, exam formats and curves, and administrative drop deadlines. Every response is strictly grounded in retrieved document chunks and cites its source file, while off-topic queries are intercepted by an embedding distance relevance gate.

## Chunking Strategy

**Chunk size:** 650 characters (max) / Paragraph-bounded  
**Overlap:** 0 characters between paragraphs (full context preserved)  

When analyzing the `campus_life` corpus in Milestone 1, I observed that documents are short (averaging ~317 characters across 1 to 3 concise paragraphs) and highly modular, with each file focused on a single topic (such as a specific course workload, dorm noise level, or administrative policy). The starter's fixed 800-character chunker never divided these documents and produced rigid cuts across headers. I replaced it with a semantic, paragraph-aware chunker (`split_documents` in `chunker.py`) that preserves complete documents under 650 characters as standalone units while ensuring headers are attached to paragraphs if larger documents are split. This avoids fragmented sentences and ensures every chunk is self-contained.

## Sample Chunks

**Chunk 1** — source: `admin_add_drop_deadline.txt#0` — produced by: `chunker.py::split_documents`

```
On the add/drop deadline

You can add a course through the end of the second week. Dropping is a longer window — through the end of week six — but a drop after week two shows as a W on your transcript. Nothing anywhere on the registrar's site says this plainly, and students find out from each other.
```

**Chunk 2** — source: `course_biol_160.txt#0` — produced by: `chunker.py::split_documents`

```
BIOL 160 Cell Biology

I lived here my sophomore year. Format is lecture three times a week with a weekly lab. Assessment: four unit tests and a cumulative final. Not curved.

Expect 9 to 11 hours a week, the heaviest first-year course by reputation.

The one piece of advice: the unit tests come fast, roughly every three weeks; falling behind once is very hard to recover from.
```

**Chunk 3** — source: `course_hist_118_workload.txt#0` — produced by: `chunker.py::split_documents`

```
Workload for HIST 118 Modern World History

People keep asking so: a lot of reading, about 120 pages a week, but no problem sets. That's real time, not optimistic time.

It's front-loaded — the first month is heavier than the rest, partly because you're learning the format.
```

**Chunk 4** — source: `dining_pellew_dining_hall_followup.txt#0` — produced by: `chunker.py::split_documents`

```
Re: Pellew Dining Hall

Adding to what people have said about Pellew Dining Hall. The wait figure of 12 to 18 minutes at peak matches what I've seen. If you're trying to eat between classes, go before 11:45 and it's a different building entirely.

Also worth saying: the furthest hall from anywhere, next to the athletics centre. Nobody tells you this at orientation.
```

**Chunk 5** — source: `housing_innisfree_hall.txt#0` — produced by: `chunker.py::split_documents`

```
Innisfree Hall — what it's actually like

Transferred in last year, so take this with a grain of salt. Built 1991, renovated 2022. Rooms are doubles arranged as pairs sharing one bathroom between two rooms.

The good: the shared-bathroom-between-two-rooms arrangement is the best compromise on campus.

The bad: no air conditioning, which matters for the first three weeks of September.

Laundry costs $1.75 wash, $1.75 dry, app-based. On noise: moderate; the building is L-shaped and the short wing is much quieter.
```

## Sample Answer

**Question:** How does the housing lottery determine priority for rising juniors and seniors?

**Answer:**

```
For rising juniors and seniors, the housing lottery orders students by accumulated credit hours first, with ties broken randomly. 

Source: admin_housing_lottery.txt
```

**My relevance cutoff:** `0.60`

To determine the relevance gate cutoff, I measured the top cosine distance score for my 5 in-scope test questions and the 5 out-of-scope questions from `OUT_OF_SCOPE`. In-scope questions produced tight cosine distances ranging from `0.193` to `0.351`, whereas out-of-scope questions produced distant scores ranging from `0.825` to `0.934`. The wide gap between `0.351` and `0.825` makes `0.60` a clean threshold that accepts all relevant queries while refusing unrelated queries before model execution.

| Question | In corpus? | Best distance |
|---|---|---|
| How does the housing lottery determine priority for rising juniors and seniors? | Yes | 0.193 |
| What is Halden Hall dining known for and when does it close on weekdays? | Yes | 0.262 |
| Are exams curved in CS 210 Data Structures? | Yes | 0.308 |
| How much does laundry cost in Aldridge Hall and what payment is accepted? | Yes | 0.263 |
| What happens if you drop a course after week two? | Yes | 0.351 |
| What is the capital of Mongolia? | No | 0.825 |
| How do I change the oil in a diesel engine? | No | 0.934 |
| Who won the 1994 World Cup? | No | 0.886 |
| What is the recommended dosage of ibuprofen for a headache? | No | 0.844 |
| How do I write a for loop in Rust? | No | 0.896 |

## How I Used AI

**1.** I asked the AI to design a paragraph-aware chunking function that would split documents on double newlines while avoiding small fragments. The initial AI output split strictly on paragraph boundaries but lost the document title/header on subsequent chunks. I modified the code to detect short heading paragraphs (<60 characters) and prepend the title context to split sections, ensuring every chunk retains its document context.

**2.** I asked the AI to help formulate 5 test questions with expected keywords from `campus_life`. The first suggestions included generic queries like "What are good dining halls?" which lack objective test criteria. I revised the prompts to target specific, verifiable facts (such as Aldridge Hall laundry pricing and CS 210 exam curve policies) with deterministic `expects` phrases for evaluation.

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Week 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     week 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     week — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->

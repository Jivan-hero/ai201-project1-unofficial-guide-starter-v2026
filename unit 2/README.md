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

## Run Log — Before

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunks contain the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Complete chunks; none under 80 characters | 4 of 5 sampled; 0% under 80 | 5/5; 0/88 short | 5/5; 0/88 short | 5/5; 0/88 short | MET |
| 5. Primary source is rank 1 | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |

The raw transcript is in `results/run_2026-09-27_0356_before.md`, produced by
`run_eval.py::main`. Generated answers were judged by reading the saved text;
retrieval criteria were checked from `store.py::search` output.

### Real output used for the calls

**Criteria 1 and 2 — generated answer from run 1**

```text
For rising juniors and seniors, the housing lottery orders students by
accumulated credit hours first, with a random tie-break used only when
necessary (*admin_housing_lottery.txt*).
```

The answer-bearing phrase was present in the rank-1 retrieved chunk and the
answer names its source. The same checks were made for all five questions in
all three runs.

**Criterion 3 — `run_eval.py::check_out_of_scope`**

```text
What is the capital of Mongolia?                         0.825  refused
How do I change the oil in a diesel engine?              0.934  refused
Who won the 1994 World Cup?                              0.886  refused
What is the recommended dosage of ibuprofen?             0.844  refused
How do I write a for loop in Rust?                        0.896  refused
```

**Criterion 4 — `chunker.py::split_documents`**

```text
88 chunks; shortest chunk 178 characters; 0 chunks under 80 characters.
Sample result: 5 of 5 inspected chunks were complete, self-contained thoughts.
```

**Criterion 5 — rank-1 output from `store.py::search`**

| Question topic | Rank-1 source | Distance |
|---|---|---:|
| Housing lottery | `admin_housing_lottery.txt` | 0.193 |
| Halden Hall dining | `dining_halden_hall.txt` | 0.262 |
| CS 210 curves | `course_cs_210_exams.txt` | 0.308 |
| Aldridge laundry | `housing_aldridge_hall_laundry.txt` | 0.263 |
| Dropping after week two | `admin_add_drop_deadline.txt` | 0.351 |

## Verdicts

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | Retrieved chunks contain the answer | MET | All five questions had an answer-bearing chunk in every deterministic retrieval pass, exceeding the 4-of-5 target. |
| 2 | Every answer names a source | MET | All 15 generated answers named at least one source document, meeting the 5-of-5 target in every run. |
| 3 | Gate stops out-of-corpus questions | MET | The gate refused all five out-of-scope questions; the deterministic 5/5 result is repeated across the three columns. |
| 4 | Chunk completeness and fragment prevention | MET | All five sampled chunks were complete and none of the 88 chunks was shorter than 80 characters. |
| 5 | Primary source rank-1 accuracy | MET | The ground-truth primary document ranked first for all five questions, exceeding the 4-of-5 target. |

## Diagnoses

No criterion was missed, so there is no failed criterion to diagnose. The
targets were safe for this focused corpus: every question maps to a dedicated
single-topic file, and the embedding distances leave a large gap between
in-scope and out-of-scope questions.

The weakness visible in the evidence is at the **retrieval stage**. With
`TOP_K = 5`, each question retrieved five chunks even though its correct source
was already rank 1. Across the five questions, that sent 25 chunks into the
generation prompt, including peripheral sources such as a statistics exam file
for the housing-lottery question and other dorms for the Aldridge-laundry
question. The extra context did not cause a wrong answer in these runs, but it
is unnecessary noise and creates more opportunity for a future answer to mix
facts from neighboring topics.

If I were tightening a criterion, I would change criterion 1 in the next unit
from “answer appears somewhere in the top five” to “the answer is in the top
three for at least 4 of 5 questions.” The original criterion remains unchanged
in `criteria.md` because it is measurable and was met; this is not a retroactive
revision.

## The Improvement

**What I changed:** I changed `TOP_K` in `config.py` from 5 to 3. This is the
only system change made in Unit 2.

**Why I picked it:** The diagnosis showed over-retrieval: the answer-bearing
source was rank 1 for every question, while the fourth and fifth chunks were
usually peripheral. Retrieving three chunks should reduce prompt noise without
removing the evidence needed to answer.

### Run Log — After

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunks contain the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Complete chunks; none under 80 characters | 4 of 5 sampled; 0% under 80 | 5/5; 0/88 short | 5/5; 0/88 short | 5/5; 0/88 short | MET |
| 5. Primary source is rank 1 | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |

The full transcript is in `results/run_2026-09-27_0357_after.md`.

**Real output after the change (run 1):**

```text
Laundry in Aldridge Hall costs $1.75 to wash and $1.50 to dry, and it
is card only.

This answer comes from the documents housing_aldridge_hall_laundry.txt
and housing_aldridge_hall.txt.
```

**Did it help?** Yes, on the issue it targeted. The number of retrieved chunks
sent to generation fell from 25 total (5 per question) to 15 total (3 per
question), a 40% reduction. All five original criteria remained MET across all
three runs. Best distances and rank-1 sources were unchanged, all 15 answers
still cited sources, and the gate still refused 5 of 5 out-of-scope questions.
The change improved retrieval precision without measurable regression on this
test set.

## What's Still Broken

No original acceptance criterion remains missed, but the test still has two
limitations:

1. The five questions are unusually clean and each has a dedicated source
   file. I would add paraphrased, ambiguous, and multi-document questions to
   learn whether top-3 retrieval is still enough outside the happy path.
2. Answer correctness was judged manually from saved text. I would build a
   scorer with question-specific facts and citation checks, then compare its
   decisions against a small human-labeled set. I stopped here because the
   assignment requires one isolated improvement, and adding a scorer would be
   a second system change rather than part of the retrieval fix.

## What I'd Do Differently

I would rewrite criterion 1 before the next unit to measure the top three
results instead of any result in the top five. The original 4-of-5 target was
too easy for a corpus made of dedicated single-topic files and did not expose
the unnecessary fourth and fifth chunks. I would also make criterion 2 require
that the cited source actually supports the claim, not merely that a filename
appears in the answer.

## How I Used AI — Week 2

I used AI to organize the raw transcripts into criterion-level counts and to
challenge the improvement choice. I verified every proposed count against the
saved run logs and local retrieval output rather than accepting a summary. AI
suggested hybrid search as a more ambitious option, but the evidence did not
show a keyword-retrieval failure. I chose the smaller top-k change because it
directly addressed the observed over-retrieval and could be measured with one
controlled before/after comparison.

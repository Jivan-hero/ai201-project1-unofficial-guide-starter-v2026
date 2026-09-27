# The corpora

Three corpora ship with this starter for your project, plus a fourth
(`practice`) that your instructor uses in class. Pick one of the three in
Milestone 1.

They are deliberately different from each other in **shape** — how long the
documents are, and how the useful information sits inside them. That
difference is the point: the right chunk size for short posts is not the
right chunk size for long sectioned guides, and Milestone 3 is where that
starts to matter.

All three were written for this course. No real people are named.

To switch corpus, either edit `CORPUS` in `config.py`, add
`AI201_CORPUS=name` to your `.env`, or pass `--corpus name` on the command
line. Re-run `python app.py index` after switching.

## `campus_life`

**Short posts about student life at a university.** Eighty-eight documents, most of them one to three short paragraphs — the kind of thing one student writes to answer another's question. Dining halls, dorms, courses, and the administrative rules nobody explains properly. Useful information tends to sit in a single sentence.

*Pick this if* you want the closest thing to the brief's framing, and short documents where a chunk can easily hold a whole thought.

88 documents · 27,908 characters · about 317 characters per document

## `advice_threads`

**Question-and-answer threads, with several people replying.** Twenty-three threads, each with three to five replies of very uneven length, disagreeing with each other as often as not. Real answers are spread across replies rather than sitting in one place.

*Pick this if* you want messier material. Chunking is harder here — a reply boundary and a useful boundary are not the same thing — and that makes for a more interesting Milestone 3.

23 documents · 12,490 characters · about 543 characters per document

## `city_guides`

**Long structured travel guides.** Fourteen documents — nine town guides, plus five that cut across all of them (eating, walking, regional transport, seasons, accessibility). Each is one to three thousand characters, divided into labelled sections — getting there, getting around, where to eat, when to go. Information is organised by heading and spread across a paragraph rather than packed into a sentence.

*Pick this if* you want to think about splitting on structure rather than on length. Fixed-size chunks cut through these headings badly, which is exactly the problem worth solving.

14 documents · 28,958 characters · about 2,068 characters per document

## `practice`

Not for your project. This is the small corpus your instructor uses for the
in-class follow-along, kept separate so nothing done in class touches your
graded work. It's twenty-eight documents about a board game that doesn't
exist — twenty-four short ones of a paragraph or two, and four longer sectioned
guides that a fixed-size chunker cuts straight through the middle of.

28 documents · 15,901 characters · about 567 characters per document

## Bringing your own documents

You're allowed to. Make a folder at `corpora/your_name/documents/`, put
`.txt` or `.md` files in it, and point `CORPUS` at it.

Two honest warnings. You take on the cleaning work the provided corpora
already did, and it earns no extra points. And you'll need to check that
your relevance cutoff still separates in-corpus from out-of-corpus
questions, since 0.6 was chosen against these three.

That check is Milestone 4, and it is the same check that makes 0.6 a cutoff
rather than a number. Treat the default as a starting point, not an answer —
it was set against the corpora above at their shipped chunk settings, and
changing the chunking moves the distances underneath it. Measuring it
yourself is the milestone.

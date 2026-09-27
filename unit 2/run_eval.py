#!/usr/bin/env python3
"""
Run your test questions repeatedly and write the results down.

    python run_eval.py                 three runs, the default
    python run_eval.py --runs 5        more runs
    python run_eval.py --label after   name this run, e.g. before/after a fix

This does the mechanical half of week 2 for you: it asks each of your questions
the same way three separate times, with caching turned off so you get three
real answers, and writes everything into results/ as a table with one row per
question.

It also puts every question in `OUT_OF_SCOPE` through retrieval and the gate
and records what happened, so criterion 3 — the one about out-of-corpus
questions — has evidence in the same file as the other four. That part costs
nothing: a question the gate refuses never reaches the model.

That table is the raw material for your run log, not the run log itself. The
submission template wants one row per *criterion* — aggregating your questions
up into your criteria is your work, not the script's.

⚠️ What it does NOT do is decide whether an answer was right.

That judgment is yours, and you'll build it in class in week 2 as `scorer.py`.
Until that file exists, the Run columns carry the raw answers and you read them
yourself. Once it exists — a file called `scorer.py`, with a function
`judge(question, expects, answer, results) -> bool` — this script finds it
automatically and the Run columns carry verdicts instead.

Deciding what counts as correct is the actual lesson. It would be easy to hand
you a scorer; you'd learn nothing from it.
"""

import argparse
import datetime as dt
import sys
from pathlib import Path

import config
import questions as qs


def load_scorer():
    """Use scorer.py if the student has built it. Otherwise run unscored."""
    try:
        import scorer  # noqa: PLC0415
    except ImportError:
        return None
    judge = getattr(scorer, "judge", None)
    return judge if callable(judge) else None


def run_once(question: str, top_k, threshold, corpus, variant):
    """One question, one run. Returns the answer and what retrieval gave us."""
    from store import search
    import gate
    from generate import answer_from_chunks

    results = search(question, top_k=top_k, corpus=corpus, variant=variant)
    decision = gate.check(results, threshold=threshold)

    if not decision.passed:
        return gate.REFUSAL, results, decision

    # cache=False on purpose. Three runs have to be three real answers.
    answer = answer_from_chunks(question, results, cache=False)
    return answer, results, decision


def main():
    parser = argparse.ArgumentParser(description="Run the test questions and log the results.")
    parser.add_argument("--runs", type=int, default=3, help="runs per question (default 3)")
    parser.add_argument("--label", default="", help="a name for this run, e.g. 'before'")
    parser.add_argument("--corpus", default=None)
    parser.add_argument("--variant", default="default")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--threshold", type=float, default=None)
    args = parser.parse_args()

    corpus = args.corpus or config.CORPUS
    top_k = args.top_k or config.TOP_K
    threshold = config.THRESHOLD if args.threshold is None else args.threshold

    items = qs.answered()
    if not items:
        print(
            "questions.py has no questions in it yet.\n"
            "Milestone 2 asks you to write five. Fill them in and run this again.",
            file=sys.stderr,
        )
        sys.exit(1)

    judge = load_scorer()
    if judge is None:
        print("No scorer.py found — running unscored. Verdict column will be blank.")
        print("You'll build scorer.py in class in week 2.\n")

    if args.runs < 3:
        print(f"⚠️  {args.runs} run(s). The submission asks for three.\n")

    transcript = []
    rows = []

    for item in items:
        question = item["question"]
        expects = item.get("expects", "")
        print(f"\n{question}")

        run_results = []
        for run in range(1, args.runs + 1):
            answer, results, decision = run_once(
                question, top_k, threshold, corpus, args.variant
            )
            passed = judge(question, expects, answer, results) if judge else None
            run_results.append(passed)

            mark = {True: "pass", False: "fail", None: "—"}[passed]
            print(f"  run {run}: {mark}  (best distance {decision.best_distance:.3f})")

            transcript.append(
                {
                    "question": question,
                    "run": run,
                    "answer": answer,
                    "sources": sorted({r.source for r in results}),
                    "best_distance": decision.best_distance,
                    "gate_passed": decision.passed,
                }
            )

        rows.append({"question": question, "expects": expects, "runs": run_results})

    gate_rows = check_out_of_scope(top_k, threshold, corpus, args.variant)

    write_report(
        rows, transcript, gate_rows, args, corpus, top_k, threshold,
        scored=judge is not None,
    )


def check_out_of_scope(top_k, threshold, corpus, variant):
    """Put every OUT_OF_SCOPE question through retrieval and the gate.

    Criterion 3 in criteria.md is about questions the corpus doesn't cover, and
    it needs evidence in the run log like the other four. This costs nothing:
    a question the gate refuses never reaches the model, so there is no API
    call and no reason to run it three times — retrieval is deterministic and
    the gate is a comparison against a fixed number.
    """
    from store import search
    import gate

    questions = getattr(qs, "OUT_OF_SCOPE", [])
    if not questions:
        return []

    print("\nOut-of-scope questions (the gate should refuse these):")
    rows = []
    for question in questions:
        results = search(question, top_k=top_k, corpus=corpus, variant=variant)
        decision = gate.check(results, threshold=threshold)
        refused = not decision.passed
        print(f"  {'refused' if refused else 'LET THROUGH'}  "
              f"(best distance {decision.best_distance:.3f})  {question}")
        rows.append(
            {
                "question": question,
                "refused": refused,
                "best_distance": decision.best_distance,
            }
        )

    kept = sum(r["refused"] for r in rows)
    print(f"  -> gate refused {kept} of {len(rows)}")
    return rows


def write_report(rows, transcript, gate_rows, args, corpus, top_k, threshold, scored):
    config.RESULTS_DIR.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    label = f"_{args.label}" if args.label else ""
    path = config.RESULTS_DIR / f"run_{stamp}{label}.md"

    n = len(rows[0]["runs"]) if rows else 0
    run_headers = " | ".join(f"Run {i}" for i in range(1, n + 1))
    run_divider = "|".join(["---"] * n)

    lines = [
        f"# Run log{f' — {args.label}' if args.label else ''}",
        "",
        f"- Produced by: `run_eval.py::main`",
        f"- Retrieval: `store.py::search`, chunks from `chunker.py::split_documents`",
        f"- Corpus: `{corpus}` (index variant `{args.variant}`)",
        f"- top-k: {top_k} · relevance cutoff: {threshold}",
        f"- Runs per question: {n}, caching off",
        f"- When: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "This table is one row per QUESTION. The run log your README asks for is",
        "one row per CRITERION, so aggregate these into it — criterion 1 is how many",
        "of your questions had the answer in the retrieved chunks, and so on.",
        "",
        f"| Question | {run_headers} |",
        f"|---|{run_divider}|",
    ]

    for row in rows:
        cells = []
        for passed in row["runs"]:
            cells.append({True: "pass", False: "fail", None: " "}[passed])
        question = row["question"].replace("|", "\\|")
        lines.append(f"| {question} | {' | '.join(cells)} |")

    if not scored:
        lines += [
            "",
            "> The Run columns are blank because `scorer.py` doesn't exist yet.",
            "> Judge each question yourself by reading the output below, or build",
            "> the scorer first and re-run.",
        ]

    if gate_rows:
        refused = sum(r["refused"] for r in gate_rows)
        lines += [
            "",
            "---",
            "",
            "## The relevance gate on out-of-corpus questions",
            "",
            f"Produced by `run_eval.py::check_out_of_scope`, cutoff {threshold}. "
            f"Refused {refused} of {len(gate_rows)}.",
            "",
            "Retrieval is deterministic and the gate is a comparison against a",
            "fixed number, so these do not vary between runs — one pass over the",
            "list is the whole measurement.",
            "",
            "| Out-of-scope question | Best distance | Gate |",
            "|---|---|---|",
        ]
        for row in gate_rows:
            question = row["question"].replace("|", "\\|")
            verdict = "refused" if row["refused"] else "**let through**"
            lines.append(f"| {question} | {row['best_distance']:.3f} | {verdict} |")

    lines += ["", "---", "", "## Real output", "",
              "This is what the system actually produced. Paste the relevant parts",
              "into your README underneath the table — the rubric asks for real",
              "output as text, not a description of it.", ""]

    for entry in transcript:
        lines += [
            f"### {entry['question']} — run {entry['run']}",
            "",
            f"- Best distance: {entry['best_distance']:.4f} "
            f"({'passed' if entry['gate_passed'] else 'refused by'} the gate)",
            f"- Sources retrieved: {', '.join(entry['sources']) or 'none'}",
            "",
            "```",
            entry["answer"],
            "```",
            "",
        ]

    path.write_text("\n".join(lines), encoding="utf-8")

    import generate as gen

    print(f"\nWrote {path.relative_to(config.ROOT)}")
    print(gen.usage())
    print("\nCommit this file. It's the evidence the run actually happened.")


if __name__ == "__main__":
    main()

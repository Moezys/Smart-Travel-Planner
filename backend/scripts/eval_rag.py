"""Hand-written sanity-check queries for the RAG retrieval.

Each query has the destination(s) we expect to see in the top-k. The
script prints a pass/fail row per query plus the top-3 hits. This is what
we run before plugging retrieval into the agent — if a clearly-on-topic
query doesn't surface the obvious destination, the chunking or the
embedding model is wrong.

Run with:
    uv run python -m scripts.eval_rag
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass

# psycopg async + Windows requires the selector event loop policy.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Wikivoyage chunks contain Unicode glyphs (phone symbol, accented chars,
# emoji) that the default Windows cp1252 console can't encode. Force UTF-8
# on stdout/stderr so prints don't crash the script.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app.db import session_scope
from app.services.rag import retrieve


@dataclass(slots=True, frozen=True)
class EvalCase:
    query: str
    expect_destinations: tuple[str, ...]   # any of these in top-k counts as a pass
    k: int = 5


CASES: tuple[EvalCase, ...] = (
    EvalCase(
        query="Where can I see geysers and waterfalls on a road trip from a capital city?",
        expect_destinations=("Reykjavik",),
    ),
    EvalCase(
        query="I want a multi-day trek with mountain views and turquoise glacier lakes.",
        expect_destinations=("Banff", "El Calafate"),
    ),
    EvalCase(
        query="Quiet yoga and rice-paddy walks in a tropical setting.",
        expect_destinations=("Ubud",),
    ),
    EvalCase(
        query="Overwater bungalows on a private island with diving.",
        expect_destinations=("Malé",),
    ),
    EvalCase(
        query="Historic old town with ancient ruins and Renaissance art.",
        expect_destinations=("Rome",),
    ),
    EvalCase(
        query="Traditional wooden temples, geisha districts, and tea ceremonies.",
        expect_destinations=("Kyoto",),
    ),
    EvalCase(
        query="Souks, riads, and tagine cooking classes.",
        expect_destinations=("Marrakech",),
    ),
    EvalCase(
        query="Skyscrapers, luxury malls, and a desert safari.",
        expect_destinations=("Dubai",),
    ),
    EvalCase(
        query="Alpine ski resort with five-star hotels and gourmet dining.",
        expect_destinations=("St. Moritz",),
    ),
    EvalCase(
        query="Cheap street food, motorbikes everywhere, French-colonial old quarter.",
        expect_destinations=("Hanoi",),
    ),
    EvalCase(
        query="Theme parks for families with young kids.",
        expect_destinations=("Orlando",),
    ),
    EvalCase(
        query="White-washed island village with beach clubs.",
        expect_destinations=("Mykonos",),
    ),
)


async def main() -> None:
    print(f"running {len(CASES)} hand-written queries\n")
    passed = 0
    async with session_scope() as session:
        for i, case in enumerate(CASES, 1):
            hits = await retrieve(session, case.query, k=case.k)
            top_dests = [h.destination for h in hits]
            ok = any(d in top_dests for d in case.expect_destinations)
            passed += int(ok)
            mark = "PASS" if ok else "FAIL"
            print(f"[{mark}] {i:>2}. {case.query}")
            print(f"        expect: {list(case.expect_destinations)}")
            for h in hits[:3]:
                snippet = h.text[:120].replace("\n", " ")
                print(f"        -> {h.destination:<14} sim={h.similarity:.3f}  "
                      f"[{h.section or '-'}]  {snippet}...")
            print()

    print(f"summary: {passed}/{len(CASES)} passed")


if __name__ == "__main__":
    asyncio.run(main())

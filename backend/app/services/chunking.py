"""Section-aware chunker for travel-guide documents.

Strategy
--------
1. Split the document on Wikivoyage-style ``==Section==`` headers (and the
   deeper ``===Sub-section===`` variants). Each section becomes a candidate
   chunk.
2. If a section fits inside the target token budget, keep it whole. Cutting
   inside a guide section is what produces the classic "chunk that ends
   mid-instruction" failure mode at retrieval time.
3. If a section is larger than the budget, slide a fixed-size window over
   it with a small overlap. The overlap is what saves us when a relevant
   sentence happens to straddle a window boundary.
4. Every chunk is prepended with the destination + section path
   (``Rome > See``). At retrieval time this gives the LLM the context that
   would otherwise be a header several lines above the chunk text.

Token counting
--------------
Voyage doesn't ship a public tokenizer, so we approximate with
``len(text.split()) * 1.3`` — ratio is good to ±10% on English prose and
the chunker only needs to keep us in a reasonable size range, not hit
exact counts.

Chosen defaults (target=400, overlap=60) — rationale in the README.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


HEADER_RE = re.compile(r"^(={2,4})\s*(.+?)\s*\1\s*$", re.MULTILINE)


# Wikivoyage H2 sections that contain logistics rather than character /
# atmosphere / things-to-do content. Dropping them before chunking gives
# the embedder a higher density of "vibe" content per chunk and stops
# retrieval from being polluted by transit/visa/SIM-card prose.
DEFAULT_DROP_SECTIONS: tuple[str, ...] = (
    "get in",
    "get around",
    "connect",
    "stay safe",
    "cope",
    "talk",
    "buy",
    "tolerate",
    "respect",
)


# H2 sections, in the order we want them to appear after re-ordering. The
# rationale is retrieval signal density: "Do" and "See" are where the
# travel-style vocabulary lives ("yoga retreats", "souk", "ski lift"),
# while "Understand > History" is mostly biography/dynasty prose with
# little retrieval signal but lots of words. Pre-pending the high-signal
# sections means a small char cap still keeps them.
DEFAULT_SECTION_PRIORITY: tuple[str, ...] = (
    "do",
    "see",
    "eat",
    "drink",
    "sleep",
    "regions",
    "districts",
    "cities",
    "other destinations",
    "understand",
    "go next",
)


@dataclass(slots=True, frozen=True)
class TextChunk:
    chunk_index: int
    section: str | None
    text: str
    token_count: int


def estimate_tokens(text: str) -> int:
    """Cheap-but-stable token estimate. Voyage tokenizer is not public."""
    return max(1, int(round(len(text.split()) * 1.3)))


def filter_sections(
    text: str,
    *,
    drop: tuple[str, ...] = DEFAULT_DROP_SECTIONS,
) -> str:
    """Strip H2 sections whose titles match (case-insensitive) any of ``drop``.

    The text before the first header (the lead paragraph) is always
    preserved. When a drop H2 is encountered, every subsequent header that
    is deeper than H2 is also skipped — until the next H2 or shallower
    header re-enters the kept stream. Sub-sections of *kept* H2s named
    like a drop prefix (e.g. an H3 "Connect" nested inside "Do") are NOT
    dropped, since they're part of vibe content.
    """
    drop_lower = {d.lower() for d in drop}
    headers = list(HEADER_RE.finditer(text))
    if not headers:
        return text

    keep = [True] * len(headers)
    skip_until_depth: int | None = None
    for i, m in enumerate(headers):
        depth = len(m.group(1))
        title = m.group(2).strip().lower()

        if skip_until_depth is not None:
            if depth <= skip_until_depth:
                skip_until_depth = None  # exit drop block; re-evaluate this header
            else:
                keep[i] = False
                continue

        if depth == 2 and title in drop_lower:
            keep[i] = False
            skip_until_depth = depth

    parts: list[str] = [text[: headers[0].start()].rstrip()]
    for i, m in enumerate(headers):
        if not keep[i]:
            continue
        start = m.start()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        parts.append(text[start:end].rstrip())

    return "\n\n".join(p for p in parts if p)


def reorder_by_priority(
    text: str,
    *,
    priority: tuple[str, ...] = DEFAULT_SECTION_PRIORITY,
) -> str:
    """Re-order H2 sections so high-signal ones (Do, See, Eat...) come first.

    Lead paragraph stays first. Then H2 sections are emitted in the order
    given by ``priority`` (case-insensitive). Any H2 not on the priority
    list is appended afterwards, in its original document order. H3+
    sub-sections travel with their parent H2 — we don't break nesting.
    """
    headers = list(HEADER_RE.finditer(text))
    if not headers:
        return text

    lead = text[: headers[0].start()].rstrip()

    # Walk H2 boundaries to collect each H2 + its sub-sections as one block.
    h2_blocks: list[tuple[str, str]] = []  # (lower-title, full block text)
    current_title: str | None = None
    current_start: int | None = None
    for m in headers:
        depth = len(m.group(1))
        title = m.group(2).strip()
        if depth == 2:
            if current_title is not None and current_start is not None:
                h2_blocks.append(
                    (current_title.lower(), text[current_start : m.start()].rstrip())
                )
            current_title = title
            current_start = m.start()
    if current_title is not None and current_start is not None:
        h2_blocks.append((current_title.lower(), text[current_start:].rstrip()))

    # Emit lead, then priority order, then leftovers.
    priority_lower = [p.lower() for p in priority]
    used: set[int] = set()
    parts: list[str] = []
    if lead:
        parts.append(lead)
    for prio in priority_lower:
        for i, (title_lower, block) in enumerate(h2_blocks):
            if i in used:
                continue
            if title_lower == prio:
                parts.append(block)
                used.add(i)
    for i, (_, block) in enumerate(h2_blocks):
        if i in used:
            continue
        parts.append(block)
        used.add(i)

    return "\n\n".join(p for p in parts if p)


def split_sections(text: str) -> list[tuple[str | None, str]]:
    """Split a wikitext-ish document into ``(section_path, body)`` pairs.

    The section path tracks H2/H3/H4 nesting so a chunk inside
    "See > Museums" carries that breadcrumb instead of just "Museums".
    """
    sections: list[tuple[str | None, str]] = []
    breadcrumb: list[str] = []
    cursor = 0
    current_path: str | None = None

    for m in HEADER_RE.finditer(text):
        body = text[cursor:m.start()].strip()
        if body:
            sections.append((current_path, body))
        depth = len(m.group(1))  # number of '=' signs
        title = m.group(2).strip()
        # Adjust breadcrumb to current depth (H2 -> level 0).
        level = depth - 2
        breadcrumb = breadcrumb[:level]
        breadcrumb.append(title)
        current_path = " > ".join(breadcrumb)
        cursor = m.end()

    tail = text[cursor:].strip()
    if tail:
        sections.append((current_path, tail))

    return sections


def _slide_window(body: str, target: int, overlap: int) -> list[str]:
    """Sliding word-window over a section that's larger than the budget.

    Window size and overlap are expressed in *tokens* but applied in *words*
    via the same 1.3 ratio used by ``estimate_tokens``.
    """
    words = body.split()
    if not words:
        return []
    window_words = max(50, int(target / 1.3))
    overlap_words = max(0, int(overlap / 1.3))
    step = max(1, window_words - overlap_words)

    chunks: list[str] = []
    i = 0
    while i < len(words):
        piece = " ".join(words[i : i + window_words])
        chunks.append(piece)
        if i + window_words >= len(words):
            break
        i += step
    return chunks


def chunk_document(
    text: str,
    *,
    destination_name: str,
    target_tokens: int = 400,
    overlap_tokens: int = 60,
) -> list[TextChunk]:
    """Split a document into retrieval chunks.

    Parameters
    ----------
    text :
        Plain-text body of the source document, with ``==Section==``
        headers preserved.
    destination_name :
        Used to prefix each chunk with breadcrumb context.
    target_tokens, overlap_tokens :
        Sizing knobs. Defaults chosen for travel-guide prose; see README.
    """
    chunks: list[TextChunk] = []
    idx = 0
    for section, body in split_sections(text):
        # Sections that fit go in whole.
        if estimate_tokens(body) <= target_tokens:
            label = f"{destination_name} > {section}" if section else destination_name
            chunk_text = f"{label}\n\n{body}".strip()
            chunks.append(TextChunk(
                chunk_index=idx,
                section=section,
                text=chunk_text,
                token_count=estimate_tokens(chunk_text),
            ))
            idx += 1
            continue
        # Otherwise window it.
        for piece in _slide_window(body, target_tokens, overlap_tokens):
            label = f"{destination_name} > {section}" if section else destination_name
            chunk_text = f"{label}\n\n{piece}".strip()
            chunks.append(TextChunk(
                chunk_index=idx,
                section=section,
                text=chunk_text,
                token_count=estimate_tokens(chunk_text),
            ))
            idx += 1

    return chunks

"""The 12 destinations the RAG corpus covers, balanced across the 6 archetypes.

Each destination is defined by:
  * ``name``, ``country``, ``region`` — must match the `destinations.csv`
    used by the ML classifier so the agent can cross-reference.
  * ``archetype`` — the editorial label.
  * ``wikivoyage_pages`` — one main article + 0–2 sub-pages. Wikivoyage
    splits big destinations into districts ("Kyoto/Higashiyama") and
    related-area pages ("Banff National Park") which are written as
    standalone guides.

24 pages total — comfortably inside the 20–30 document target.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class DestinationSeed:
    name: str
    country: str
    region: str
    archetype: str
    wikivoyage_pages: tuple[str, ...]


SEEDS: tuple[DestinationSeed, ...] = (
    # --- Adventure ---
    DestinationSeed(
        name="Reykjavik", country="Iceland", region="Europe",
        archetype="Adventure",
        wikivoyage_pages=("Reykjavík", "Iceland"),
    ),
    DestinationSeed(
        name="Banff", country="Canada", region="North America",
        archetype="Adventure",
        wikivoyage_pages=("Banff National Park", "Lake Louise"),
    ),
    DestinationSeed(
        name="El Calafate", country="Argentina", region="South America",
        archetype="Adventure",
        wikivoyage_pages=("El Calafate", "Los Glaciares National Park"),
    ),
    # --- Relaxation ---
    DestinationSeed(
        name="Ubud", country="Indonesia", region="SE Asia",
        archetype="Relaxation",
        wikivoyage_pages=("Ubud", "Bali"),
    ),
    DestinationSeed(
        name="Malé", country="Maldives", region="South Asia",
        archetype="Relaxation",
        wikivoyage_pages=("Malé", "Maldives"),
    ),
    DestinationSeed(
        name="Mykonos", country="Greece", region="Europe",
        archetype="Relaxation",
        wikivoyage_pages=("Mykonos",),
    ),
    # --- Culture ---
    DestinationSeed(
        name="Rome", country="Italy", region="Europe",
        archetype="Culture",
        wikivoyage_pages=("Rome", "Rome/Colosseo"),
    ),
    DestinationSeed(
        name="Kyoto", country="Japan", region="Asia",
        archetype="Culture",
        wikivoyage_pages=("Kyoto", "Kyoto/Higashiyama"),
    ),
    DestinationSeed(
        name="Marrakech", country="Morocco", region="Africa",
        archetype="Culture",
        wikivoyage_pages=("Marrakech",),
    ),
    # --- Luxury ---
    DestinationSeed(
        name="Dubai", country="UAE", region="Middle East",
        archetype="Luxury",
        wikivoyage_pages=("Dubai", "Abu Dhabi"),
    ),
    DestinationSeed(
        name="St. Moritz", country="Switzerland", region="Europe",
        archetype="Luxury",
        wikivoyage_pages=("St. Moritz",),
    ),
    # --- Budget ---
    DestinationSeed(
        name="Hanoi", country="Vietnam", region="SE Asia",
        archetype="Budget",
        wikivoyage_pages=("Hanoi", "Ha Long Bay"),
    ),
    # --- Family ---
    DestinationSeed(
        name="Orlando", country="United States", region="North America",
        archetype="Family",
        wikivoyage_pages=("Orlando", "Walt Disney World"),
    ),
)

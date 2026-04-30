"""Build the destination dataset from seed + country baselines + label rules.

Per-destination features are synthesized as:
    feature = country_baseline + tag_adjustment + seeded_jitter

Tags are parsed from the destination's name and sub_region (e.g., "Mountain",
"Beach", "National Park") and translate to deterministic shifts on relevant
features. The seeded RNG produces stable jitter — re-running the script
yields the same CSV.

CRITICAL: tags are extracted from PLACE NAMES, not from labels. The label
look-up (data.labels.label_for) is invoked AFTER feature generation and is
written to the CSV but never read by the feature code. This keeps the
features independent of the labels — a label-flip would not change any
numeric feature.

Run with: python backend/data/build_dataset.py
Outputs:  backend/data/destinations.csv
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.country_baselines import baseline_for
from data.labels import label_for
from data.seed_destinations import iter_destinations


SEED = 42
OUT_PATH = Path(__file__).parent / "destinations.csv"


# Keyword groups parsed from `name` + `sub_region`. Order matters: earlier
# groups can be overridden by later ones (e.g., "Lake Louise" matches "lake"
# but is in alpine Banff so also gets "alpine").
TAG_KEYWORDS: dict[str, tuple[str, ...]] = {
    "mountain":  ("mountain", "alps", "andes", "hima", "rocky", "atlas", "tatra",
                  "pyrenees", "carpath", "dolomit", "drakensberg", "caucasus",
                  "altai", "tien shan", "snowdon", "kilimanjaro", "everest",
                  "fuji", "tongariro", "matterhorn", "jungfrau", "annapurna"),
    "alpine":    ("ski", "glacier", "zermatt", "st. moritz", "verbier", "gstaad",
                  "davos", "kitzbühel", "st. anton", "chamonix", "aspen", "vail",
                  "park city", "whistler", "niseko", "zakopane", "bansko",
                  "dolomit", "cortina"),
    "coastal":   ("beach", "bay", "cape", "cove", "coast", "atoll", "caye",
                  " key ", "shore", "lagoon", "reef", "sea", "harbor", "port"),
    "island":    ("island", "isle", "maldives", "bali", "phuket", "koh ", "ko ",
                  "ibiza", "mallorca", "menorca", "tenerife", "santorini",
                  "mykonos", "crete", "rhodes", "corfu", "okinawa", "boracay",
                  "palawan", "fiji", "tahiti", "bora bora", "moorea", "barbados",
                  "bahamas", "jamaica", "cuba", "lombok", "gili", "nusa", "sri",
                  "iceland", "madagascar"),
    "nature":    ("national park", "biosphere", "reserve", "wilderness",
                  "forest", "jungle", "rainforest", "amazon", "delta",
                  "fjord", "canyon"),
    "desert":    ("desert", "sahara", "wadi", "atacama", "kalahari", "outback",
                  "uluru", "death valley", "merzouga", "siwa"),
    "lake":      ("lake", "loch", "tarn"),
    "wine":      ("wine", "vineyard", "napa", "sonoma", "barossa", "stellenbosch",
                  "mendoza", "douro", "champagne", "bordeaux", "cafayate",
                  "marlborough", "hunter", "margaret river"),
    "themepark": ("disney", "orlando", "gold coast", "sentosa", "niagara falls",
                  "tenerife", "kos", "punta cana", "cancun"),
    "urban":     ("downtown", "marina", "centro", "ciudad", "metropoli"),
    "heritage":  ("old town", "ancient", "ruin", "temple", "monaster",
                  "cathedral", "petra", "angkor", "machu", "borobudur", "bagan",
                  "luxor", "giza", "delphi", "ephesus", "carthage", "tikal",
                  "palenque", "chichen", "stonehenge"),
    "capital":   (),  # filled in by capital-city detection
}


CAPITAL_CITIES: set[tuple[str, str]] = {
    ("Italy", "Rome"), ("France", "Paris"), ("Spain", "Madrid"),
    ("Portugal", "Lisbon"), ("Greece", "Athens"), ("Germany", "Berlin"),
    ("United Kingdom", "London"), ("Ireland", "Dublin"),
    ("Netherlands", "Amsterdam"), ("Belgium", "Brussels"),
    ("Switzerland", "Bern"), ("Austria", "Vienna"),
    ("Czech Republic", "Prague"), ("Hungary", "Budapest"),
    ("Poland", "Warsaw"), ("Croatia", "Zagreb"), ("Slovenia", "Ljubljana"),
    ("Norway", "Oslo"), ("Sweden", "Stockholm"), ("Denmark", "Copenhagen"),
    ("Finland", "Helsinki"), ("Iceland", "Reykjavik"),
    ("Romania", "Bucharest"), ("Bulgaria", "Sofia"), ("Estonia", "Tallinn"),
    ("Albania", "Tirana"), ("Malta", "Valletta"),
    ("Japan", "Tokyo"), ("China", "Beijing"), ("South Korea", "Seoul"),
    ("Taiwan", "Taipei"), ("Thailand", "Bangkok"), ("Vietnam", "Hanoi"),
    ("Cambodia", "Phnom Penh"), ("Laos", "Vientiane"),
    ("Indonesia", "Jakarta"), ("Malaysia", "Kuala Lumpur"),
    ("Philippines", "Manila"), ("Myanmar", "Yangon"), ("India", "Delhi"),
    ("Sri Lanka", "Colombo"), ("Nepal", "Kathmandu"), ("Bhutan", "Thimphu"),
    ("Maldives", "Malé"), ("Turkey", "Istanbul"), ("Jordan", "Amman"),
    ("Israel", "Jerusalem"), ("Oman", "Muscat"), ("Egypt", "Cairo"),
    ("Morocco", "Rabat"), ("Tanzania", "Dar es Salaam"), ("Kenya", "Nairobi"),
    ("South Africa", "Pretoria"), ("Namibia", "Windhoek"),
    ("Botswana", "Gaborone"), ("Madagascar", "Antananarivo"),
    ("Tunisia", "Tunis"), ("United States", "Washington DC"),
    ("Canada", "Ottawa"), ("Mexico", "Mexico City"),
    ("Costa Rica", "San Jose (CR)"), ("Panama", "Panama City"),
    ("Guatemala", "Guatemala City"), ("Belize", "Belize City"),
    ("Cuba", "Havana"), ("Dominican Republic", "Santo Domingo"),
    ("Jamaica", "Kingston"), ("Bahamas", "Nassau"),
    ("Barbados", "Bridgetown"), ("Saint Lucia", "Castries"),
    ("Peru", "Lima"), ("Brazil", "Brasília"), ("Argentina", "Buenos Aires"),
    ("Chile", "Santiago"), ("Colombia", "Bogotá"), ("Ecuador", "Quito"),
    ("Bolivia", "La Paz (Bolivia)"), ("Uruguay", "Montevideo"),
    ("Australia", "Canberra"), ("New Zealand", "Wellington"),
    ("Fiji", "Suva"),
}


def tags_for(name: str, sub_region: str, country: str) -> set[str]:
    """Parse tags from name and sub_region using keyword matching."""
    text = f"{name} {sub_region}".lower()
    tags: set[str] = set()
    for tag, keywords in TAG_KEYWORDS.items():
        if any(k in text for k in keywords):
            tags.add(tag)
    if (country, name) in CAPITAL_CITIES:
        tags.add("capital")
    if "mountain" in tags or "alpine" in tags:
        tags.add("nature")
    return tags


def gen_features(name: str, country: str, sub_region: str, region: str,
                 rng: random.Random) -> dict[str, float]:
    """Synthesize one row of features. Country-baseline + tag shifts + jitter."""
    base = baseline_for(country)
    tags = tags_for(name, sub_region, country)

    # --- Geography ---
    lat = base["lat"] + rng.gauss(0, 1.5)
    lon = base["lon"] + rng.gauss(0, 2.0)

    # Elevation: default low; mountain/alpine drives it up
    if "alpine" in tags:
        elevation_m = rng.uniform(1500, 2800)
    elif "mountain" in tags:
        elevation_m = rng.uniform(800, 2200)
    elif "lake" in tags:
        elevation_m = rng.uniform(200, 800)
    elif "desert" in tags:
        elevation_m = rng.uniform(200, 1000)
    else:
        elevation_m = max(0, rng.gauss(120, 80))

    # Coast distance: 0 for coastal, larger for inland
    if "coastal" in tags or "island" in tags:
        coast_distance_km = rng.uniform(0, 3)
    elif country == "Maldives":
        coast_distance_km = 0
    elif "lake" in tags or "desert" in tags or "mountain" in tags or "alpine" in tags:
        coast_distance_km = rng.uniform(80, 400)
    else:
        coast_distance_km = rng.uniform(20, 250)

    # --- Climate ---
    # Temperature: country baseline minus elevation lapse rate (-6.5°C/km),
    # plus jitter, with coastal moderation.
    elev_lapse = -0.0065 * elevation_m
    temp_jitter_summer = rng.gauss(0, 1.2)
    temp_jitter_winter = rng.gauss(0, 1.5)
    avg_temp_summer_c = base["t_summer"] + elev_lapse + temp_jitter_summer
    avg_temp_winter_c = base["t_winter"] + elev_lapse + temp_jitter_winter
    if "coastal" in tags or "island" in tags:
        # Coastal moderation: pull both temps toward ~22°C
        avg_temp_summer_c = avg_temp_summer_c * 0.85 + 22 * 0.15
        avg_temp_winter_c = avg_temp_winter_c * 0.85 + 18 * 0.15
    if "alpine" in tags:
        avg_temp_winter_c -= 5

    rain_jit = rng.gauss(1.0, 0.18)
    if "desert" in tags:
        annual_rainfall_mm = max(20, base["rain_mm"] * 0.15 * rain_jit)
    elif "alpine" in tags:
        annual_rainfall_mm = base["rain_mm"] * 1.4 * rain_jit
    elif "island" in tags or "coastal" in tags:
        annual_rainfall_mm = base["rain_mm"] * 1.1 * rain_jit
    else:
        annual_rainfall_mm = base["rain_mm"] * rain_jit

    sun_jit = rng.gauss(1.0, 0.08)
    if "desert" in tags:
        sunny_days_per_year = min(360, base["sunny_days"] * 1.15 * sun_jit)
    elif "alpine" in tags or "mountain" in tags:
        sunny_days_per_year = base["sunny_days"] * 0.85 * sun_jit
    else:
        sunny_days_per_year = base["sunny_days"] * sun_jit

    # --- Activity supply ---
    # Hiking trails: mountain/nature/alpine drive up; urban/coast drive down
    base_trails = base["trails_per_kkm2"]
    if "alpine" in tags or "mountain" in tags:
        hiking_trails_count = rng.gauss(80, 25)
    elif "nature" in tags:
        hiking_trails_count = rng.gauss(55, 20)
    elif "lake" in tags:
        hiking_trails_count = rng.gauss(35, 15)
    elif "island" in tags:
        hiking_trails_count = rng.gauss(15, 10)
    elif "capital" in tags or "urban" in tags:
        hiking_trails_count = rng.gauss(8, 5)
    elif "coastal" in tags:
        hiking_trails_count = rng.gauss(15, 10)
    elif "desert" in tags:
        hiking_trails_count = rng.gauss(25, 15)
    else:
        hiking_trails_count = rng.gauss(base_trails * 1.5, 10)
    hiking_trails_count = max(0, hiking_trails_count)

    # UNESCO sites within 100km: country total scaled by tier
    unesco_total = base["unesco_total"]
    if "heritage" in tags or "capital" in tags:
        unesco_share = rng.uniform(0.10, 0.25)
    elif "nature" in tags or "mountain" in tags:
        unesco_share = rng.uniform(0.02, 0.08)
    else:
        unesco_share = rng.uniform(0.0, 0.06)
    unesco_sites_within_100km = max(0, round(unesco_total * unesco_share))

    # Museum count: capital/heritage drive up; nature/island drive down
    pop_factor = max(0.05, base["population_m"] / 60.0)
    if "capital" in tags:
        museum_count = rng.gauss(60 * pop_factor + 30, 20)
    elif "heritage" in tags or "urban" in tags:
        museum_count = rng.gauss(25, 12)
    elif "nature" in tags or "alpine" in tags or "mountain" in tags:
        museum_count = rng.gauss(3, 2)
    elif "coastal" in tags or "island" in tags:
        museum_count = rng.gauss(6, 4)
    else:
        museum_count = rng.gauss(15 * pop_factor + 5, 8)
    museum_count = max(0, museum_count)

    # National parks within 100km
    if "nature" in tags:
        national_parks_within_100km = rng.choice([1, 2, 2, 3, 3, 4])
    elif "mountain" in tags or "alpine" in tags:
        national_parks_within_100km = rng.choice([1, 1, 2, 2, 3])
    elif "desert" in tags:
        national_parks_within_100km = rng.choice([0, 1, 1, 2])
    elif "capital" in tags or "urban" in tags:
        national_parks_within_100km = rng.choice([0, 0, 0, 1])
    else:
        national_parks_within_100km = rng.choice([0, 0, 1, 1, 2])

    # Theme parks: mostly 0; theme-park-tagged places get 1-3
    if "themepark" in tags:
        theme_parks_count = rng.choice([1, 2, 2, 3])
    elif "capital" in tags or "urban" in tags:
        theme_parks_count = rng.choice([0, 0, 1])
    else:
        theme_parks_count = rng.choices([0, 1], weights=[0.85, 0.15])[0]

    # --- Cost ---
    cost_idx = base["cost_idx"]
    hotel = base["hotel_3star_usd"]
    if "wine" in tags or "alpine" in tags:
        cost_mult = rng.uniform(1.25, 1.55)
    elif "capital" in tags:
        cost_mult = rng.uniform(1.05, 1.30)
    elif "coastal" in tags or "island" in tags:
        cost_mult = rng.uniform(0.95, 1.25)
    elif "themepark" in tags:
        cost_mult = rng.uniform(1.05, 1.25)
    else:
        cost_mult = rng.uniform(0.85, 1.15)
    cost_of_living_index = max(15, cost_idx * cost_mult * rng.gauss(1.0, 0.06))
    avg_3star_hotel_usd = max(20, hotel * cost_mult * rng.gauss(1.0, 0.08))

    # --- Tourism intensity ---
    visitors_jitter = rng.gauss(1.0, 0.20)
    if "capital" in tags:
        place_share = rng.uniform(0.15, 0.35)
    elif "coastal" in tags or "island" in tags:
        place_share = rng.uniform(0.05, 0.20)
    elif "heritage" in tags:
        place_share = rng.uniform(0.05, 0.18)
    else:
        place_share = rng.uniform(0.01, 0.08)
    annual_visitors_millions = base["visitors_m"] * place_share * visitors_jitter
    annual_visitors_millions = max(0.01, annual_visitors_millions)
    # Local population for visitors_per_capita
    if "capital" in tags:
        local_pop = max(0.1, base["population_m"] * rng.uniform(0.10, 0.25))
    elif "urban" in tags or "heritage" in tags:
        local_pop = max(0.05, base["population_m"] * rng.uniform(0.01, 0.08))
    elif "island" in tags:
        local_pop = max(0.005, base["population_m"] * rng.uniform(0.001, 0.02))
    else:
        local_pop = max(0.02, base["population_m"] * rng.uniform(0.005, 0.04))
    visitors_per_capita = annual_visitors_millions / local_pop

    return {
        "name": name,
        "country": country,
        "region": region,
        "sub_region": sub_region,
        "latitude": round(lat, 3),
        "longitude": round(lon, 3),
        "elevation_m": round(elevation_m, 0),
        "coast_distance_km": round(coast_distance_km, 1),
        "avg_temp_summer_c": round(avg_temp_summer_c, 1),
        "avg_temp_winter_c": round(avg_temp_winter_c, 1),
        "annual_rainfall_mm": round(annual_rainfall_mm, 0),
        "sunny_days_per_year": round(sunny_days_per_year, 0),
        "hiking_trails_count": round(hiking_trails_count, 0),
        "unesco_sites_within_100km": unesco_sites_within_100km,
        "museum_count": round(museum_count, 0),
        "national_parks_within_100km": national_parks_within_100km,
        "theme_parks_count": theme_parks_count,
        "cost_of_living_index": round(cost_of_living_index, 1),
        "avg_3star_hotel_usd": round(avg_3star_hotel_usd, 0),
        "annual_visitors_millions": round(annual_visitors_millions, 3),
        "visitors_per_capita": round(visitors_per_capita, 2),
    }


def build() -> int:
    rng = random.Random(SEED)
    rows: list[dict] = []
    for d in iter_destinations():
        row = gen_features(d["name"], d["country"], d["sub_region"],
                           d["region"], rng)
        row["label"] = label_for(d["country"], d["name"])
        rows.append(row)

    # Stable column order
    cols = [
        "name", "country", "region", "sub_region",
        "latitude", "longitude", "elevation_m", "coast_distance_km",
        "avg_temp_summer_c", "avg_temp_winter_c",
        "annual_rainfall_mm", "sunny_days_per_year",
        "hiking_trails_count", "unesco_sites_within_100km",
        "museum_count", "national_parks_within_100km", "theme_parks_count",
        "cost_of_living_index", "avg_3star_hotel_usd",
        "annual_visitors_millions", "visitors_per_capita",
        "label",
    ]
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


if __name__ == "__main__":
    n = build()
    print(f"Wrote {n} rows to {OUT_PATH}")

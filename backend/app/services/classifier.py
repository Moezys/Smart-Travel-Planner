"""ML travel-style classifier service.

Wraps the joblib sklearn Pipeline that was trained in the notebook.
The pipeline expects a single-row DataFrame with these columns:
    latitude, longitude, elevation_m, coast_distance_km,
    avg_temp_summer_c, avg_temp_winter_c, annual_rainfall_mm,
    sunny_days_per_year, hiking_trails_count,
    unesco_sites_within_100km, museum_count,
    national_parks_within_100km, theme_parks_count,
    cost_of_living_index, avg_3star_hotel_usd,
    annual_visitors_millions, visitors_per_capita,
    region

The function is sync (sklearn is not async) but fast enough to run on the
event loop without blocking.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import joblib
import pandas as pd

from app.config import get_settings

_FEATURE_COLS = [
    "latitude", "longitude", "elevation_m", "coast_distance_km",
    "avg_temp_summer_c", "avg_temp_winter_c", "annual_rainfall_mm",
    "sunny_days_per_year", "hiking_trails_count",
    "unesco_sites_within_100km", "museum_count",
    "national_parks_within_100km", "theme_parks_count",
    "cost_of_living_index", "avg_3star_hotel_usd",
    "annual_visitors_millions", "visitors_per_capita",
    "region",
]


@lru_cache(maxsize=1)
def _load_pipeline():
    return joblib.load(get_settings().ml_model_path)


@lru_cache(maxsize=1)
def _load_destinations() -> pd.DataFrame:
    df = pd.read_csv(get_settings().destinations_csv_path)
    df["_name_lower"] = df["name"].str.lower()
    return df


@dataclass(slots=True, frozen=True)
class ClassificationResult:
    destination: str
    predicted_style: str
    probabilities: dict[str, float]
    matched_row: str  # "name, country" of the row that was used


def classify_destination(destination_name: str) -> ClassificationResult:
    """Classify *destination_name* using the trained RandomForest pipeline.

    Looks up the destination in destinations.csv (case-insensitive, picks
    the closest match by name).  Raises ``ValueError`` if no match is found.
    """
    df = _load_destinations()
    query = destination_name.strip().lower()

    # Exact match first, then startswith, then contains.
    mask_exact = df["_name_lower"] == query
    mask_start = df["_name_lower"].str.startswith(query)
    mask_contains = df["_name_lower"].str.contains(query, regex=False)

    for mask in (mask_exact, mask_start, mask_contains):
        hits = df[mask]
        if not hits.empty:
            row = hits.iloc[0]
            break
    else:
        raise ValueError(
            f"Destination {destination_name!r} not found in the dataset. "
            "Try a major nearby city or the country name."
        )

    pipeline = _load_pipeline()
    features = pd.DataFrame([row[_FEATURE_COLS].to_dict()])
    label: str = pipeline.predict(features)[0]
    proba: list[float] = pipeline.predict_proba(features)[0].tolist()
    classes: list[str] = pipeline.classes_.tolist()

    return ClassificationResult(
        destination=destination_name,
        predicted_style=label,
        probabilities={c: round(p, 3) for c, p in zip(classes, proba)},
        matched_row=f"{row['name']}, {row['country']}",
    )

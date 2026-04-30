"""Real-world country baselines used to synthesize per-destination features.

Each country has the same set of baseline values. Per-destination features are
derived from country baselines plus deterministic adjustments (latitude,
elevation, coastal/inland, etc.) plus seeded noise.

The classifier never sees the country baselines directly; it sees the
synthesized per-destination features. The country baselines themselves come
from public sources (Numbeo, UNWTO, Wikipedia climate tables, etc.) and were
NOT computed from the archetype labels — that's what keeps the features
leakage-free.

Field meanings:
    lat, lon           — country geographic center
    t_summer, t_winter — mean monthly °C (July for N hemi, Jan for S hemi)
    rain_mm            — mean annual rainfall, mm
    sunny_days         — mean sunny days per year
    cost_idx           — Numbeo-style cost-of-living index (NYC ≈ 100)
    hotel_3star_usd    — average 3-star hotel per night in USD, July
    visitors_m         — annual international visitors, millions (pre-pandemic)
    population_m       — country population, millions
    unesco_total       — number of UNESCO World Heritage sites in country
    museums_per_m      — museums per million inhabitants (rough)
    trails_per_kkm2    — hiking trails per 1000 km^2 (rough)
"""

from __future__ import annotations


COUNTRY_BASELINES: dict[str, dict[str, float]] = {
    # Europe
    "Italy":           dict(lat=43.0, lon=12.5, t_summer=26, t_winter=8, rain_mm=900, sunny_days=210, cost_idx=68, hotel_3star_usd=130, visitors_m=64, population_m=59, unesco_total=58, museums_per_m=80, trails_per_kkm2=15),
    "France":          dict(lat=46.5, lon=2.5, t_summer=22, t_winter=5, rain_mm=900, sunny_days=180, cost_idx=72, hotel_3star_usd=150, visitors_m=89, population_m=68, unesco_total=49, museums_per_m=70, trails_per_kkm2=18),
    "Spain":           dict(lat=40.0, lon=-4.0, t_summer=27, t_winter=9, rain_mm=650, sunny_days=260, cost_idx=58, hotel_3star_usd=110, visitors_m=84, population_m=47, unesco_total=49, museums_per_m=60, trails_per_kkm2=14),
    "Portugal":        dict(lat=39.5, lon=-8.0, t_summer=24, t_winter=11, rain_mm=850, sunny_days=240, cost_idx=55, hotel_3star_usd=100, visitors_m=27, population_m=10, unesco_total=17, museums_per_m=55, trails_per_kkm2=10),
    "Greece":          dict(lat=39.0, lon=22.0, t_summer=29, t_winter=10, rain_mm=650, sunny_days=270, cost_idx=58, hotel_3star_usd=110, visitors_m=33, population_m=10, unesco_total=19, museums_per_m=70, trails_per_kkm2=10),
    "Germany":         dict(lat=51.0, lon=10.0, t_summer=19, t_winter=1, rain_mm=800, sunny_days=160, cost_idx=72, hotel_3star_usd=130, visitors_m=39, population_m=84, unesco_total=54, museums_per_m=85, trails_per_kkm2=22),
    "United Kingdom":  dict(lat=54.0, lon=-2.0, t_summer=18, t_winter=5, rain_mm=1100, sunny_days=140, cost_idx=78, hotel_3star_usd=160, visitors_m=37, population_m=67, unesco_total=33, museums_per_m=60, trails_per_kkm2=20),
    "Ireland":         dict(lat=53.0, lon=-8.0, t_summer=15, t_winter=5, rain_mm=1100, sunny_days=130, cost_idx=78, hotel_3star_usd=150, visitors_m=11, population_m=5, unesco_total=2, museums_per_m=55, trails_per_kkm2=18),
    "Netherlands":     dict(lat=52.5, lon=5.5, t_summer=18, t_winter=3, rain_mm=850, sunny_days=160, cost_idx=78, hotel_3star_usd=150, visitors_m=20, population_m=18, unesco_total=12, museums_per_m=80, trails_per_kkm2=12),
    "Belgium":         dict(lat=50.5, lon=4.5, t_summer=18, t_winter=3, rain_mm=850, sunny_days=160, cost_idx=72, hotel_3star_usd=130, visitors_m=9, population_m=11, unesco_total=15, museums_per_m=75, trails_per_kkm2=14),
    "Switzerland":     dict(lat=46.8, lon=8.2, t_summer=18, t_winter=-1, rain_mm=1100, sunny_days=170, cost_idx=110, hotel_3star_usd=220, visitors_m=11, population_m=9, unesco_total=13, museums_per_m=120, trails_per_kkm2=80),
    "Austria":         dict(lat=47.5, lon=14.5, t_summer=20, t_winter=-1, rain_mm=900, sunny_days=180, cost_idx=72, hotel_3star_usd=140, visitors_m=31, population_m=9, unesco_total=12, museums_per_m=80, trails_per_kkm2=70),
    "Czech Republic":  dict(lat=49.8, lon=15.5, t_summer=19, t_winter=-1, rain_mm=650, sunny_days=170, cost_idx=48, hotel_3star_usd=85, visitors_m=12, population_m=10, unesco_total=17, museums_per_m=60, trails_per_kkm2=20),
    "Hungary":         dict(lat=47.0, lon=19.5, t_summer=22, t_winter=0, rain_mm=600, sunny_days=190, cost_idx=42, hotel_3star_usd=75, visitors_m=16, population_m=10, unesco_total=9, museums_per_m=55, trails_per_kkm2=12),
    "Poland":          dict(lat=52.0, lon=19.5, t_summer=19, t_winter=-2, rain_mm=600, sunny_days=160, cost_idx=42, hotel_3star_usd=70, visitors_m=21, population_m=38, unesco_total=17, museums_per_m=45, trails_per_kkm2=14),
    "Croatia":         dict(lat=45.0, lon=15.5, t_summer=24, t_winter=4, rain_mm=950, sunny_days=220, cost_idx=52, hotel_3star_usd=110, visitors_m=20, population_m=4, unesco_total=10, museums_per_m=60, trails_per_kkm2=20),
    "Slovenia":        dict(lat=46.0, lon=15.0, t_summer=20, t_winter=-1, rain_mm=1200, sunny_days=190, cost_idx=55, hotel_3star_usd=110, visitors_m=6, population_m=2, unesco_total=5, museums_per_m=70, trails_per_kkm2=50),
    "Norway":          dict(lat=64.5, lon=11.5, t_summer=14, t_winter=-3, rain_mm=1400, sunny_days=170, cost_idx=98, hotel_3star_usd=200, visitors_m=6, population_m=5, unesco_total=8, museums_per_m=80, trails_per_kkm2=30),
    "Sweden":          dict(lat=62.0, lon=15.0, t_summer=17, t_winter=-3, rain_mm=600, sunny_days=180, cost_idx=70, hotel_3star_usd=140, visitors_m=8, population_m=10, unesco_total=15, museums_per_m=75, trails_per_kkm2=15),
    "Denmark":         dict(lat=56.0, lon=10.0, t_summer=17, t_winter=1, rain_mm=750, sunny_days=160, cost_idx=83, hotel_3star_usd=160, visitors_m=12, population_m=6, unesco_total=10, museums_per_m=85, trails_per_kkm2=10),
    "Finland":         dict(lat=64.0, lon=26.0, t_summer=17, t_winter=-7, rain_mm=600, sunny_days=170, cost_idx=72, hotel_3star_usd=130, visitors_m=4, population_m=6, unesco_total=7, museums_per_m=80, trails_per_kkm2=18),
    "Iceland":         dict(lat=65.0, lon=-18.0, t_summer=12, t_winter=0, rain_mm=1000, sunny_days=130, cost_idx=95, hotel_3star_usd=190, visitors_m=2, population_m=0.4, unesco_total=3, museums_per_m=120, trails_per_kkm2=22),
    "Romania":         dict(lat=46.0, lon=25.0, t_summer=23, t_winter=-2, rain_mm=600, sunny_days=200, cost_idx=38, hotel_3star_usd=65, visitors_m=13, population_m=19, unesco_total=9, museums_per_m=40, trails_per_kkm2=14),
    "Bulgaria":        dict(lat=42.7, lon=25.5, t_summer=23, t_winter=0, rain_mm=600, sunny_days=220, cost_idx=38, hotel_3star_usd=60, visitors_m=10, population_m=7, unesco_total=10, museums_per_m=50, trails_per_kkm2=16),
    "Estonia":         dict(lat=58.5, lon=25.0, t_summer=17, t_winter=-3, rain_mm=600, sunny_days=170, cost_idx=52, hotel_3star_usd=85, visitors_m=3, population_m=1.3, unesco_total=2, museums_per_m=80, trails_per_kkm2=14),
    "Montenegro":      dict(lat=42.7, lon=19.4, t_summer=27, t_winter=5, rain_mm=1500, sunny_days=240, cost_idx=42, hotel_3star_usd=80, visitors_m=2, population_m=0.6, unesco_total=4, museums_per_m=55, trails_per_kkm2=30),
    "Albania":         dict(lat=41.2, lon=20.0, t_summer=26, t_winter=7, rain_mm=1100, sunny_days=240, cost_idx=32, hotel_3star_usd=55, visitors_m=6, population_m=2.8, unesco_total=4, museums_per_m=35, trails_per_kkm2=18),
    "Malta":           dict(lat=35.9, lon=14.5, t_summer=28, t_winter=13, rain_mm=550, sunny_days=300, cost_idx=58, hotel_3star_usd=95, visitors_m=3, population_m=0.5, unesco_total=3, museums_per_m=70, trails_per_kkm2=8),
    # Asia
    "Japan":           dict(lat=36.0, lon=138.0, t_summer=27, t_winter=4, rain_mm=1700, sunny_days=190, cost_idx=72, hotel_3star_usd=120, visitors_m=32, population_m=125, unesco_total=25, museums_per_m=45, trails_per_kkm2=30),
    "China":           dict(lat=35.0, lon=104.0, t_summer=24, t_winter=2, rain_mm=650, sunny_days=200, cost_idx=42, hotel_3star_usd=70, visitors_m=65, population_m=1410, unesco_total=57, museums_per_m=4, trails_per_kkm2=8),
    "South Korea":     dict(lat=36.5, lon=128.0, t_summer=26, t_winter=0, rain_mm=1300, sunny_days=200, cost_idx=68, hotel_3star_usd=110, visitors_m=18, population_m=52, unesco_total=15, museums_per_m=20, trails_per_kkm2=20),
    "Taiwan":          dict(lat=23.7, lon=121.0, t_summer=29, t_winter=17, rain_mm=2500, sunny_days=180, cost_idx=58, hotel_3star_usd=90, visitors_m=12, population_m=23, unesco_total=0, museums_per_m=22, trails_per_kkm2=24),
    "Thailand":        dict(lat=15.0, lon=101.0, t_summer=29, t_winter=27, rain_mm=1500, sunny_days=240, cost_idx=42, hotel_3star_usd=60, visitors_m=40, population_m=70, unesco_total=6, museums_per_m=12, trails_per_kkm2=10),
    "Vietnam":         dict(lat=16.0, lon=106.0, t_summer=29, t_winter=20, rain_mm=1700, sunny_days=210, cost_idx=32, hotel_3star_usd=40, visitors_m=18, population_m=98, unesco_total=8, museums_per_m=8, trails_per_kkm2=12),
    "Cambodia":        dict(lat=12.5, lon=105.0, t_summer=29, t_winter=27, rain_mm=1500, sunny_days=240, cost_idx=32, hotel_3star_usd=40, visitors_m=7, population_m=17, unesco_total=4, museums_per_m=6, trails_per_kkm2=6),
    "Laos":            dict(lat=18.0, lon=104.0, t_summer=29, t_winter=22, rain_mm=1700, sunny_days=210, cost_idx=30, hotel_3star_usd=35, visitors_m=4, population_m=7, unesco_total=3, museums_per_m=8, trails_per_kkm2=8),
    "Indonesia":       dict(lat=-2.0, lon=118.0, t_summer=27, t_winter=27, rain_mm=2300, sunny_days=200, cost_idx=35, hotel_3star_usd=50, visitors_m=16, population_m=275, unesco_total=10, museums_per_m=4, trails_per_kkm2=8),
    "Malaysia":        dict(lat=4.0, lon=110.0, t_summer=28, t_winter=27, rain_mm=2400, sunny_days=210, cost_idx=42, hotel_3star_usd=60, visitors_m=26, population_m=33, unesco_total=4, museums_per_m=10, trails_per_kkm2=12),
    "Singapore":       dict(lat=1.3, lon=103.8, t_summer=28, t_winter=27, rain_mm=2200, sunny_days=200, cost_idx=82, hotel_3star_usd=170, visitors_m=19, population_m=6, unesco_total=1, museums_per_m=15, trails_per_kkm2=20),
    "Philippines":     dict(lat=13.0, lon=122.0, t_summer=28, t_winter=26, rain_mm=2400, sunny_days=200, cost_idx=38, hotel_3star_usd=55, visitors_m=8, population_m=113, unesco_total=6, museums_per_m=4, trails_per_kkm2=8),
    "Myanmar":         dict(lat=22.0, lon=96.0, t_summer=29, t_winter=22, rain_mm=2100, sunny_days=210, cost_idx=32, hotel_3star_usd=40, visitors_m=4, population_m=54, unesco_total=2, museums_per_m=5, trails_per_kkm2=6),
    "India":           dict(lat=22.0, lon=78.0, t_summer=32, t_winter=18, rain_mm=1100, sunny_days=240, cost_idx=28, hotel_3star_usd=45, visitors_m=18, population_m=1410, unesco_total=42, museums_per_m=2, trails_per_kkm2=8),
    "Sri Lanka":       dict(lat=7.9, lon=80.8, t_summer=28, t_winter=26, rain_mm=2000, sunny_days=210, cost_idx=32, hotel_3star_usd=50, visitors_m=2, population_m=22, unesco_total=8, museums_per_m=8, trails_per_kkm2=10),
    "Nepal":           dict(lat=28.4, lon=84.1, t_summer=22, t_winter=10, rain_mm=1400, sunny_days=200, cost_idx=28, hotel_3star_usd=35, visitors_m=1.2, population_m=30, unesco_total=4, museums_per_m=5, trails_per_kkm2=22),
    "Bhutan":          dict(lat=27.5, lon=90.5, t_summer=18, t_winter=5, rain_mm=2200, sunny_days=200, cost_idx=45, hotel_3star_usd=130, visitors_m=0.3, population_m=0.8, unesco_total=0, museums_per_m=15, trails_per_kkm2=20),
    "Maldives":        dict(lat=3.2, lon=73.2, t_summer=28, t_winter=27, rain_mm=2000, sunny_days=240, cost_idx=68, hotel_3star_usd=280, visitors_m=1.7, population_m=0.5, unesco_total=0, museums_per_m=12, trails_per_kkm2=2),
    # Middle East
    "Turkey":          dict(lat=39.0, lon=35.0, t_summer=27, t_winter=4, rain_mm=600, sunny_days=240, cost_idx=32, hotel_3star_usd=55, visitors_m=51, population_m=85, unesco_total=21, museums_per_m=25, trails_per_kkm2=10),
    "UAE":             dict(lat=24.0, lon=54.0, t_summer=37, t_winter=18, rain_mm=100, sunny_days=340, cost_idx=72, hotel_3star_usd=140, visitors_m=21, population_m=10, unesco_total=1, museums_per_m=35, trails_per_kkm2=4),
    "Jordan":          dict(lat=31.3, lon=36.5, t_summer=31, t_winter=8, rain_mm=200, sunny_days=300, cost_idx=48, hotel_3star_usd=85, visitors_m=5, population_m=11, unesco_total=6, museums_per_m=12, trails_per_kkm2=8),
    "Israel":          dict(lat=31.0, lon=34.8, t_summer=29, t_winter=12, rain_mm=400, sunny_days=300, cost_idx=82, hotel_3star_usd=170, visitors_m=4, population_m=9, unesco_total=9, museums_per_m=50, trails_per_kkm2=18),
    "Oman":            dict(lat=21.0, lon=57.0, t_summer=33, t_winter=20, rain_mm=100, sunny_days=320, cost_idx=58, hotel_3star_usd=110, visitors_m=2, population_m=4.6, unesco_total=5, museums_per_m=18, trails_per_kkm2=4),
    # Africa
    "Egypt":           dict(lat=27.0, lon=30.0, t_summer=31, t_winter=14, rain_mm=80, sunny_days=320, cost_idx=28, hotel_3star_usd=50, visitors_m=13, population_m=110, unesco_total=7, museums_per_m=4, trails_per_kkm2=2),
    "Morocco":         dict(lat=31.5, lon=-8.0, t_summer=27, t_winter=12, rain_mm=350, sunny_days=290, cost_idx=35, hotel_3star_usd=60, visitors_m=13, population_m=37, unesco_total=9, museums_per_m=8, trails_per_kkm2=8),
    "Tanzania":        dict(lat=-6.4, lon=34.9, t_summer=21, t_winter=27, rain_mm=1000, sunny_days=240, cost_idx=38, hotel_3star_usd=90, visitors_m=1.5, population_m=63, unesco_total=7, museums_per_m=2, trails_per_kkm2=8),
    "Kenya":           dict(lat=0.0, lon=37.9, t_summer=21, t_winter=23, rain_mm=900, sunny_days=240, cost_idx=42, hotel_3star_usd=85, visitors_m=2, population_m=54, unesco_total=7, museums_per_m=3, trails_per_kkm2=10),
    "South Africa":    dict(lat=-30.6, lon=22.9, t_summer=18, t_winter=24, rain_mm=500, sunny_days=270, cost_idx=42, hotel_3star_usd=85, visitors_m=10, population_m=60, unesco_total=10, museums_per_m=15, trails_per_kkm2=15),
    "Namibia":         dict(lat=-22.0, lon=17.0, t_summer=18, t_winter=25, rain_mm=300, sunny_days=300, cost_idx=42, hotel_3star_usd=80, visitors_m=1.5, population_m=2.5, unesco_total=2, museums_per_m=20, trails_per_kkm2=4),
    "Botswana":        dict(lat=-22.3, lon=24.7, t_summer=15, t_winter=24, rain_mm=400, sunny_days=290, cost_idx=45, hotel_3star_usd=110, visitors_m=1.7, population_m=2.6, unesco_total=2, museums_per_m=10, trails_per_kkm2=2),
    "Madagascar":      dict(lat=-19.0, lon=46.7, t_summer=20, t_winter=24, rain_mm=1500, sunny_days=240, cost_idx=32, hotel_3star_usd=55, visitors_m=0.4, population_m=29, unesco_total=3, museums_per_m=2, trails_per_kkm2=4),
    "Tunisia":         dict(lat=34.0, lon=9.5, t_summer=29, t_winter=11, rain_mm=350, sunny_days=290, cost_idx=32, hotel_3star_usd=55, visitors_m=9, population_m=12, unesco_total=8, museums_per_m=10, trails_per_kkm2=6),
    # Americas
    "United States":   dict(lat=39.5, lon=-98.5, t_summer=24, t_winter=2, rain_mm=750, sunny_days=205, cost_idx=72, hotel_3star_usd=140, visitors_m=80, population_m=333, unesco_total=25, museums_per_m=110, trails_per_kkm2=12),
    "Canada":          dict(lat=56.0, lon=-106.0, t_summer=18, t_winter=-12, rain_mm=550, sunny_days=180, cost_idx=70, hotel_3star_usd=130, visitors_m=22, population_m=39, unesco_total=20, museums_per_m=85, trails_per_kkm2=14),
    "Mexico":          dict(lat=23.6, lon=-102.6, t_summer=24, t_winter=18, rain_mm=750, sunny_days=240, cost_idx=38, hotel_3star_usd=70, visitors_m=45, population_m=128, unesco_total=35, museums_per_m=12, trails_per_kkm2=8),
    "Costa Rica":      dict(lat=9.7, lon=-84.0, t_summer=23, t_winter=24, rain_mm=2900, sunny_days=190, cost_idx=52, hotel_3star_usd=100, visitors_m=3, population_m=5.2, unesco_total=4, museums_per_m=15, trails_per_kkm2=22),
    "Panama":          dict(lat=8.4, lon=-80.8, t_summer=27, t_winter=27, rain_mm=2700, sunny_days=190, cost_idx=48, hotel_3star_usd=85, visitors_m=2, population_m=4.4, unesco_total=5, museums_per_m=10, trails_per_kkm2=14),
    "Guatemala":       dict(lat=15.8, lon=-90.2, t_summer=22, t_winter=20, rain_mm=2200, sunny_days=200, cost_idx=35, hotel_3star_usd=55, visitors_m=2, population_m=18, unesco_total=3, museums_per_m=5, trails_per_kkm2=10),
    "Belize":          dict(lat=17.2, lon=-88.5, t_summer=28, t_winter=24, rain_mm=2000, sunny_days=230, cost_idx=48, hotel_3star_usd=95, visitors_m=0.5, population_m=0.4, unesco_total=1, museums_per_m=12, trails_per_kkm2=10),
    "Cuba":            dict(lat=21.5, lon=-77.8, t_summer=28, t_winter=22, rain_mm=1300, sunny_days=290, cost_idx=38, hotel_3star_usd=70, visitors_m=4, population_m=11, unesco_total=9, museums_per_m=20, trails_per_kkm2=8),
    "Dominican Republic": dict(lat=19.0, lon=-70.7, t_summer=28, t_winter=24, rain_mm=1400, sunny_days=240, cost_idx=42, hotel_3star_usd=90, visitors_m=7, population_m=11, unesco_total=1, museums_per_m=8, trails_per_kkm2=8),
    "Jamaica":         dict(lat=18.1, lon=-77.3, t_summer=28, t_winter=24, rain_mm=2000, sunny_days=270, cost_idx=42, hotel_3star_usd=90, visitors_m=3, population_m=2.8, unesco_total=1, museums_per_m=10, trails_per_kkm2=10),
    "Bahamas":         dict(lat=24.3, lon=-76.0, t_summer=28, t_winter=22, rain_mm=1300, sunny_days=300, cost_idx=78, hotel_3star_usd=200, visitors_m=7, population_m=0.4, unesco_total=0, museums_per_m=18, trails_per_kkm2=4),
    "Barbados":        dict(lat=13.2, lon=-59.5, t_summer=28, t_winter=25, rain_mm=1300, sunny_days=300, cost_idx=72, hotel_3star_usd=160, visitors_m=0.7, population_m=0.3, unesco_total=1, museums_per_m=22, trails_per_kkm2=6),
    "Saint Lucia":     dict(lat=13.9, lon=-61.0, t_summer=28, t_winter=25, rain_mm=2000, sunny_days=270, cost_idx=68, hotel_3star_usd=170, visitors_m=0.4, population_m=0.2, unesco_total=1, museums_per_m=18, trails_per_kkm2=12),
    "Peru":            dict(lat=-9.2, lon=-75.0, t_summer=18, t_winter=20, rain_mm=600, sunny_days=200, cost_idx=32, hotel_3star_usd=55, visitors_m=4, population_m=34, unesco_total=13, museums_per_m=8, trails_per_kkm2=12),
    "Brazil":          dict(lat=-14.2, lon=-51.9, t_summer=23, t_winter=24, rain_mm=1700, sunny_days=240, cost_idx=38, hotel_3star_usd=70, visitors_m=6, population_m=215, unesco_total=23, museums_per_m=12, trails_per_kkm2=8),
    "Argentina":       dict(lat=-38.4, lon=-63.6, t_summer=14, t_winter=18, rain_mm=600, sunny_days=220, cost_idx=32, hotel_3star_usd=60, visitors_m=7, population_m=46, unesco_total=11, museums_per_m=15, trails_per_kkm2=10),
    "Chile":           dict(lat=-35.7, lon=-71.5, t_summer=15, t_winter=18, rain_mm=400, sunny_days=240, cost_idx=42, hotel_3star_usd=75, visitors_m=4, population_m=20, unesco_total=7, museums_per_m=18, trails_per_kkm2=12),
    "Colombia":        dict(lat=4.6, lon=-74.3, t_summer=22, t_winter=23, rain_mm=2400, sunny_days=200, cost_idx=32, hotel_3star_usd=55, visitors_m=4, population_m=51, unesco_total=9, museums_per_m=10, trails_per_kkm2=10),
    "Ecuador":         dict(lat=-1.8, lon=-78.2, t_summer=18, t_winter=21, rain_mm=1500, sunny_days=190, cost_idx=35, hotel_3star_usd=60, visitors_m=2, population_m=18, unesco_total=5, museums_per_m=8, trails_per_kkm2=12),
    "Bolivia":         dict(lat=-16.3, lon=-63.6, t_summer=15, t_winter=20, rain_mm=600, sunny_days=240, cost_idx=28, hotel_3star_usd=45, visitors_m=1.2, population_m=12, unesco_total=7, museums_per_m=8, trails_per_kkm2=8),
    "Uruguay":         dict(lat=-32.5, lon=-55.8, t_summer=14, t_winter=22, rain_mm=1100, sunny_days=210, cost_idx=48, hotel_3star_usd=85, visitors_m=4, population_m=3.4, unesco_total=3, museums_per_m=22, trails_per_kkm2=6),
    # Oceania
    "Australia":       dict(lat=-25.3, lon=133.8, t_summer=12, t_winter=23, rain_mm=550, sunny_days=240, cost_idx=82, hotel_3star_usd=160, visitors_m=9, population_m=26, unesco_total=20, museums_per_m=50, trails_per_kkm2=10),
    "New Zealand":     dict(lat=-40.9, lon=174.9, t_summer=10, t_winter=18, rain_mm=1100, sunny_days=210, cost_idx=78, hotel_3star_usd=140, visitors_m=4, population_m=5, unesco_total=3, museums_per_m=85, trails_per_kkm2=22),
    "Fiji":            dict(lat=-17.7, lon=178.1, t_summer=24, t_winter=27, rain_mm=2700, sunny_days=210, cost_idx=48, hotel_3star_usd=130, visitors_m=0.9, population_m=0.9, unesco_total=1, museums_per_m=12, trails_per_kkm2=10),
    "French Polynesia": dict(lat=-17.7, lon=-149.4, t_summer=23, t_winter=27, rain_mm=1700, sunny_days=240, cost_idx=85, hotel_3star_usd=300, visitors_m=0.3, population_m=0.3, unesco_total=2, museums_per_m=18, trails_per_kkm2=12),
}


def baseline_for(country: str) -> dict[str, float]:
    if country not in COUNTRY_BASELINES:
        raise KeyError(f"No baseline for country {country!r}")
    return COUNTRY_BASELINES[country]


if __name__ == "__main__":
    print(f"Countries with baselines: {len(COUNTRY_BASELINES)}")
    fields = next(iter(COUNTRY_BASELINES.values())).keys()
    print(f"Fields per country: {list(fields)}")

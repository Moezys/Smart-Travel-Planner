"""Editorial archetype labels for each seed destination.

Each destination gets exactly one archetype from:
    Adventure | Relaxation | Culture | Budget | Luxury | Family

Approach:
    1. COUNTRY_DEFAULT — the dominant style for the country.
    2. OVERRIDES        — per-place exceptions where a destination doesn't match
                          the country default (e.g. Capri in Italy is Luxury,
                          not Culture; Hokkaido in Japan is Adventure, not
                          Culture).

These labels are assigned by editorial judgment of the place's primary travel
identity. They are NEVER computed from the numeric features the classifier
trains on, which is what keeps the dataset leakage-free.

Tie-breaking when a place fits multiple styles:
    Family > Luxury > Adventure > Relaxation > Budget > Culture
    (Family is hardest signal, Culture is residual)
"""

from __future__ import annotations


ARCHETYPES = ("Adventure", "Relaxation", "Culture", "Budget", "Luxury", "Family")


COUNTRY_DEFAULT: dict[str, str] = {
    # Europe
    "Italy": "Culture",
    "France": "Culture",
    "Spain": "Culture",
    "Portugal": "Culture",
    "Greece": "Culture",
    "Germany": "Culture",
    "United Kingdom": "Culture",
    "Ireland": "Adventure",
    "Netherlands": "Culture",
    "Belgium": "Culture",
    "Switzerland": "Luxury",
    "Austria": "Culture",
    "Czech Republic": "Culture",
    "Hungary": "Culture",
    "Poland": "Culture",
    "Croatia": "Relaxation",
    "Slovenia": "Adventure",
    "Norway": "Adventure",
    "Sweden": "Culture",
    "Denmark": "Culture",
    "Finland": "Adventure",
    "Iceland": "Adventure",
    "Romania": "Culture",
    "Bulgaria": "Culture",
    "Estonia": "Culture",
    "Montenegro": "Relaxation",
    "Albania": "Budget",
    "Malta": "Culture",
    # Asia
    "Japan": "Culture",
    "China": "Culture",
    "South Korea": "Culture",
    "Taiwan": "Culture",
    "Thailand": "Relaxation",
    "Vietnam": "Budget",
    "Cambodia": "Budget",
    "Laos": "Budget",
    "Indonesia": "Relaxation",
    "Malaysia": "Budget",
    "Singapore": "Luxury",
    "Philippines": "Relaxation",
    "Myanmar": "Budget",
    "India": "Culture",
    "Sri Lanka": "Culture",
    "Nepal": "Adventure",
    "Bhutan": "Culture",
    "Maldives": "Relaxation",
    # Middle East
    "Turkey": "Culture",
    "UAE": "Luxury",
    "Jordan": "Culture",
    "Israel": "Culture",
    "Oman": "Adventure",
    # Africa
    "Egypt": "Culture",
    "Morocco": "Culture",
    "Tanzania": "Adventure",
    "Kenya": "Adventure",
    "South Africa": "Adventure",
    "Namibia": "Adventure",
    "Botswana": "Adventure",
    "Madagascar": "Adventure",
    "Tunisia": "Culture",
    # Americas
    "United States": "Culture",  # heavy override use below
    "Canada": "Adventure",
    "Mexico": "Culture",
    "Costa Rica": "Adventure",
    "Panama": "Culture",
    "Guatemala": "Culture",
    "Belize": "Relaxation",
    "Cuba": "Culture",
    "Dominican Republic": "Relaxation",
    "Jamaica": "Relaxation",
    "Bahamas": "Relaxation",
    "Barbados": "Relaxation",
    "Saint Lucia": "Relaxation",
    "Peru": "Adventure",
    "Brazil": "Relaxation",
    "Argentina": "Adventure",
    "Chile": "Adventure",
    "Colombia": "Culture",
    "Ecuador": "Adventure",
    "Bolivia": "Adventure",
    "Uruguay": "Relaxation",
    # Oceania
    "Australia": "Adventure",
    "New Zealand": "Adventure",
    "Fiji": "Relaxation",
    "French Polynesia": "Relaxation",
}


# Per-place overrides where the place differs from its country default.
# Format: (country, name) -> archetype
OVERRIDES: dict[tuple[str, str], str] = {
    # Italy — Culture default; resort/luxury/adventure exceptions
    ("Italy", "Portofino"): "Luxury",
    ("Italy", "Capri"): "Luxury",
    ("Italy", "Costa Smeralda"): "Luxury",
    ("Italy", "Lake Como"): "Luxury",
    ("Italy", "Amalfi"): "Luxury",
    ("Italy", "Positano"): "Luxury",
    ("Italy", "Dolomites"): "Adventure",
    ("Italy", "Cortina d'Ampezzo"): "Luxury",
    ("Italy", "Lake Garda"): "Relaxation",

    # France — Culture default; Riviera Luxury, Alps Adventure
    ("France", "Saint-Tropez"): "Luxury",
    ("France", "Cannes"): "Luxury",
    ("France", "Monaco-adjacent Menton"): "Luxury",
    ("France", "Nice"): "Luxury",
    ("France", "Biarritz"): "Luxury",
    ("France", "Chamonix"): "Adventure",
    ("France", "Annecy"): "Adventure",
    ("France", "Grenoble"): "Adventure",

    # Spain — Culture default; Balearic/Canary islands Relaxation; Marbella Luxury
    ("Spain", "Ibiza"): "Relaxation",
    ("Spain", "Mallorca - Palma"): "Relaxation",
    ("Spain", "Menorca"): "Relaxation",
    ("Spain", "Formentera"): "Relaxation",
    ("Spain", "Tenerife"): "Family",
    ("Spain", "Gran Canaria"): "Relaxation",
    ("Spain", "Lanzarote"): "Relaxation",
    ("Spain", "Fuerteventura"): "Relaxation",
    ("Spain", "La Palma"): "Adventure",
    ("Spain", "Marbella"): "Luxury",
    ("Spain", "Costa Brava"): "Relaxation",
    ("Spain", "Sitges"): "Relaxation",

    # Portugal — Culture default; Algarve/Madeira/Azores Relaxation/Adventure
    ("Portugal", "Algarve - Lagos"): "Relaxation",
    ("Portugal", "Algarve - Faro"): "Relaxation",
    ("Portugal", "Algarve - Albufeira"): "Relaxation",
    ("Portugal", "Algarve - Tavira"): "Relaxation",
    ("Portugal", "Madeira - Funchal"): "Adventure",
    ("Portugal", "Azores - São Miguel"): "Adventure",
    ("Portugal", "Azores - Pico"): "Adventure",
    ("Portugal", "Nazaré"): "Adventure",
    ("Portugal", "Cascais"): "Relaxation",
    ("Portugal", "Douro Valley"): "Luxury",

    # Greece — Culture default; islands Relaxation
    ("Greece", "Santorini"): "Luxury",
    ("Greece", "Mykonos"): "Luxury",
    ("Greece", "Naxos"): "Relaxation",
    ("Greece", "Paros"): "Relaxation",
    ("Greece", "Milos"): "Relaxation",
    ("Greece", "Ios"): "Relaxation",
    ("Greece", "Rhodes"): "Relaxation",
    ("Greece", "Kos"): "Family",
    ("Greece", "Patmos"): "Relaxation",
    ("Greece", "Corfu"): "Relaxation",
    ("Greece", "Zakynthos"): "Relaxation",
    ("Greece", "Kefalonia"): "Relaxation",
    ("Greece", "Lesbos"): "Relaxation",
    ("Greece", "Skiathos"): "Relaxation",
    ("Greece", "Hydra"): "Relaxation",
    ("Greece", "Crete - Heraklion"): "Relaxation",
    ("Greece", "Crete - Chania"): "Relaxation",
    ("Greece", "Crete - Rethymno"): "Relaxation",
    ("Greece", "Meteora"): "Adventure",

    # Germany — Culture default; Black Forest/Berchtesgaden/Garmisch Adventure
    ("Germany", "Black Forest"): "Adventure",
    ("Germany", "Garmisch-Partenkirchen"): "Adventure",
    ("Germany", "Berchtesgaden"): "Adventure",
    ("Germany", "Sylt"): "Luxury",
    ("Germany", "Rügen"): "Relaxation",
    ("Germany", "Mosel Valley"): "Luxury",

    # UK — Culture default; nature spots Adventure
    ("United Kingdom", "Isle of Skye"): "Adventure",
    ("United Kingdom", "Loch Ness"): "Adventure",
    ("United Kingdom", "Inverness"): "Adventure",
    ("United Kingdom", "Oban"): "Adventure",
    ("United Kingdom", "Lake District"): "Adventure",
    ("United Kingdom", "Cotswolds"): "Luxury",
    ("United Kingdom", "Snowdonia"): "Adventure",
    ("United Kingdom", "Giant's Causeway"): "Adventure",
    ("United Kingdom", "Cornwall - St Ives"): "Relaxation",
    ("United Kingdom", "Cornwall - Penzance"): "Relaxation",
    ("United Kingdom", "Brighton"): "Relaxation",

    # Ireland — Adventure default; cities Culture
    ("Ireland", "Dublin"): "Culture",
    ("Ireland", "Galway"): "Culture",
    ("Ireland", "Cork"): "Culture",
    ("Ireland", "Kilkenny"): "Culture",

    # Switzerland — Luxury default; hiking spots Adventure
    ("Switzerland", "Interlaken"): "Adventure",
    ("Switzerland", "Jungfrau"): "Adventure",
    ("Switzerland", "Grindelwald"): "Adventure",
    ("Switzerland", "Lucerne"): "Culture",
    ("Switzerland", "Bern"): "Culture",
    ("Switzerland", "Lausanne"): "Culture",

    # Austria — Culture default; Alpine resorts mixed
    ("Austria", "Innsbruck"): "Adventure",
    ("Austria", "Hallstatt"): "Adventure",
    ("Austria", "Kitzbühel"): "Luxury",
    ("Austria", "St. Anton"): "Luxury",
    ("Austria", "Zell am See"): "Adventure",
    ("Austria", "Bad Gastein"): "Relaxation",

    # Poland — Culture default; Zakopane Adventure
    ("Poland", "Zakopane"): "Adventure",
    ("Poland", "Białowieża Forest"): "Adventure",

    # Croatia — Relaxation default; nature spots Adventure; cities Culture
    ("Croatia", "Zagreb"): "Culture",
    ("Croatia", "Dubrovnik"): "Culture",
    ("Croatia", "Split"): "Culture",
    ("Croatia", "Plitvice Lakes"): "Adventure",
    ("Croatia", "Krka National Park"): "Adventure",

    # Norway — Adventure default; cities Culture
    ("Norway", "Oslo"): "Culture",
    ("Norway", "Bergen"): "Culture",
    ("Norway", "Trondheim"): "Culture",
    ("Norway", "Stavanger"): "Culture",

    # Sweden — Culture default; northern wilderness Adventure
    ("Sweden", "Abisko"): "Adventure",
    ("Sweden", "Kiruna"): "Adventure",

    # Finland — Adventure default; cities Culture
    ("Finland", "Helsinki"): "Culture",
    ("Finland", "Turku"): "Culture",
    ("Finland", "Tampere"): "Culture",
    ("Finland", "Rovaniemi"): "Family",
    ("Finland", "Levi"): "Adventure",
    ("Finland", "Saariselkä"): "Adventure",

    # Romania — Culture default; some Adventure
    ("Romania", "Maramureș"): "Adventure",

    # Bulgaria — Culture default; Bansko Adventure; coast Relaxation
    ("Bulgaria", "Bansko"): "Adventure",
    ("Bulgaria", "Burgas"): "Relaxation",
    ("Bulgaria", "Varna"): "Relaxation",
    ("Bulgaria", "Rila Monastery"): "Adventure",

    # Estonia — Culture default; nature Adventure
    ("Estonia", "Lahemaa National Park"): "Adventure",
    ("Estonia", "Pärnu"): "Relaxation",
    ("Estonia", "Saaremaa"): "Relaxation",

    # Montenegro — Relaxation default; mountains Adventure
    ("Montenegro", "Durmitor National Park"): "Adventure",
    ("Montenegro", "Lake Skadar"): "Adventure",

    # Albania — Budget default; coast Relaxation
    ("Albania", "Sarandë"): "Relaxation",
    ("Albania", "Ksamil"): "Relaxation",
    ("Albania", "Berat"): "Culture",
    ("Albania", "Gjirokastër"): "Culture",

    # Malta — Culture default; Comino Relaxation
    ("Malta", "Comino - Blue Lagoon"): "Relaxation",
    ("Malta", "Sliema"): "Relaxation",

    # Japan — Culture default; islands Relaxation; mountains Adventure
    ("Japan", "Hokkaido"): "Adventure",
    ("Japan", "Niseko"): "Adventure",
    ("Japan", "Furano"): "Adventure",
    ("Japan", "Sapporo"): "Culture",
    ("Japan", "Otaru"): "Culture",
    ("Japan", "Hakodate"): "Culture",
    ("Japan", "Okinawa - Naha"): "Relaxation",
    ("Japan", "Ishigaki"): "Relaxation",
    ("Japan", "Iriomote"): "Adventure",
    ("Japan", "Miyakojima"): "Relaxation",
    ("Japan", "Yakushima"): "Adventure",
    ("Japan", "Mount Fuji area"): "Adventure",
    ("Japan", "Beppu"): "Relaxation",

    # China — Culture default; nature Adventure
    ("China", "Zhangjiajie"): "Adventure",
    ("China", "Jiuzhaigou"): "Adventure",
    ("China", "Huangshan"): "Adventure",
    ("China", "Lhasa"): "Adventure",
    ("China", "Shangri-La"): "Adventure",
    ("China", "Hong Kong"): "Luxury",
    ("China", "Macau"): "Luxury",

    # Korea — Culture default
    ("South Korea", "Jeju Island"): "Family",
    ("South Korea", "Sokcho"): "Adventure",
    ("South Korea", "Pyeongchang"): "Adventure",

    # Taiwan — Culture default
    ("Taiwan", "Taroko Gorge"): "Adventure",
    ("Taiwan", "Alishan"): "Adventure",
    ("Taiwan", "Kenting"): "Relaxation",

    # Thailand — Relaxation default; cities/cultural Culture; nature Adventure
    ("Thailand", "Bangkok"): "Culture",
    ("Thailand", "Chiang Mai"): "Culture",
    ("Thailand", "Chiang Rai"): "Culture",
    ("Thailand", "Pai"): "Adventure",
    ("Thailand", "Ayutthaya"): "Culture",
    ("Thailand", "Sukhothai"): "Culture",
    ("Thailand", "Kanchanaburi"): "Adventure",
    ("Thailand", "Khao Sok"): "Adventure",
    ("Thailand", "Khao Yai"): "Adventure",

    # Vietnam — Budget default; cultural cities Culture; nature Adventure
    ("Vietnam", "Hanoi"): "Culture",
    ("Vietnam", "Ho Chi Minh City"): "Culture",
    ("Vietnam", "Hue"): "Culture",
    ("Vietnam", "Hoi An"): "Culture",
    ("Vietnam", "Halong Bay"): "Adventure",
    ("Vietnam", "Sapa"): "Adventure",
    ("Vietnam", "Phong Nha"): "Adventure",
    ("Vietnam", "Ninh Binh"): "Adventure",

    # Cambodia — Budget default; Angkor Culture
    ("Cambodia", "Siem Reap (Angkor)"): "Culture",
    ("Cambodia", "Phnom Penh"): "Culture",

    # Laos — Budget default; Luang Prabang Culture
    ("Laos", "Luang Prabang"): "Culture",

    # Indonesia — Relaxation default; major Adventure/Culture overrides
    ("Indonesia", "Yogyakarta"): "Culture",
    ("Indonesia", "Borobudur"): "Culture",
    ("Indonesia", "Jakarta"): "Culture",
    ("Indonesia", "Bandung"): "Culture",
    ("Indonesia", "Mount Bromo"): "Adventure",
    ("Indonesia", "Komodo Islands"): "Adventure",
    ("Indonesia", "Raja Ampat"): "Adventure",
    ("Indonesia", "Sumatra - Bukit Lawang"): "Adventure",
    ("Indonesia", "Sulawesi - Tana Toraja"): "Culture",
    ("Indonesia", "Bali - Ubud"): "Culture",

    # Malaysia — Budget default; KL Culture; Borneo Adventure
    ("Malaysia", "Kuala Lumpur"): "Culture",
    ("Malaysia", "Penang - George Town"): "Culture",
    ("Malaysia", "Malacca"): "Culture",
    ("Malaysia", "Borneo - Kota Kinabalu"): "Adventure",
    ("Malaysia", "Borneo - Sandakan"): "Adventure",
    ("Malaysia", "Borneo - Kuching"): "Adventure",
    ("Malaysia", "Cameron Highlands"): "Adventure",
    ("Malaysia", "Langkawi"): "Relaxation",
    ("Malaysia", "Tioman Island"): "Relaxation",
    ("Malaysia", "Perhentian Islands"): "Relaxation",

    # Singapore — Luxury default; Sentosa Family
    ("Singapore", "Singapore - Sentosa"): "Family",
    ("Singapore", "Singapore - Chinatown"): "Culture",
    ("Singapore", "Singapore - Little India"): "Culture",

    # Philippines — Relaxation default; Adventure/Culture overrides
    ("Philippines", "Manila"): "Culture",
    ("Philippines", "Palawan - El Nido"): "Adventure",
    ("Philippines", "Palawan - Coron"): "Adventure",
    ("Philippines", "Palawan - Puerto Princesa"): "Adventure",
    ("Philippines", "Siargao"): "Adventure",
    ("Philippines", "Banaue Rice Terraces"): "Adventure",
    ("Philippines", "Vigan"): "Culture",
    ("Philippines", "Donsol"): "Adventure",

    # Myanmar — Budget default; Bagan Culture
    ("Myanmar", "Bagan"): "Culture",
    ("Myanmar", "Yangon"): "Culture",
    ("Myanmar", "Mandalay"): "Culture",
    ("Myanmar", "Inle Lake"): "Adventure",
    ("Myanmar", "Ngapali Beach"): "Relaxation",

    # India — Culture default; Adventure/Relaxation overrides
    ("India", "Rishikesh"): "Adventure",
    ("India", "Goa - North"): "Relaxation",
    ("India", "Goa - South"): "Relaxation",
    ("India", "Kerala - Munnar"): "Adventure",
    ("India", "Kerala - Alleppey"): "Relaxation",
    ("India", "Kerala - Varkala"): "Relaxation",
    ("India", "Sikkim - Gangtok"): "Adventure",
    ("India", "Ladakh - Leh"): "Adventure",
    ("India", "Kashmir - Srinagar"): "Adventure",
    ("India", "Manali"): "Adventure",
    ("India", "Shimla"): "Adventure",
    ("India", "Dharamshala"): "Adventure",
    ("India", "Darjeeling"): "Adventure",
    ("India", "Ranthambore"): "Adventure",

    # Sri Lanka — Culture default
    ("Sri Lanka", "Ella"): "Adventure",
    ("Sri Lanka", "Yala National Park"): "Adventure",
    ("Sri Lanka", "Mirissa"): "Relaxation",
    ("Sri Lanka", "Unawatuna"): "Relaxation",
    ("Sri Lanka", "Trincomalee"): "Relaxation",
    ("Sri Lanka", "Arugam Bay"): "Adventure",
    ("Sri Lanka", "Nuwara Eliya"): "Adventure",

    # Bhutan — Culture default; Tiger's Nest Adventure
    ("Bhutan", "Tiger's Nest"): "Adventure",
    ("Bhutan", "Bumthang"): "Adventure",

    # Maldives — Relaxation default
    # (no overrides needed)

    # Turkey — Culture default; coast Relaxation; Cappadocia Adventure
    ("Turkey", "Cappadocia"): "Adventure",
    ("Turkey", "Bodrum"): "Relaxation",
    ("Turkey", "Marmaris"): "Relaxation",
    ("Turkey", "Fethiye"): "Relaxation",
    ("Turkey", "Antalya"): "Relaxation",
    ("Turkey", "Side"): "Relaxation",
    ("Turkey", "Kaş"): "Relaxation",
    ("Turkey", "Olympos"): "Adventure",
    ("Turkey", "Pamukkale"): "Adventure",

    # UAE — Luxury default; desert/wilderness Adventure
    ("UAE", "Liwa Desert"): "Adventure",
    ("UAE", "Fujairah"): "Adventure",

    # Jordan — Culture default; desert Adventure; Dead Sea Relaxation
    ("Jordan", "Wadi Rum"): "Adventure",
    ("Jordan", "Dead Sea"): "Relaxation",
    ("Jordan", "Aqaba"): "Relaxation",
    ("Jordan", "Dana Biosphere Reserve"): "Adventure",

    # Israel — Culture default
    ("Israel", "Eilat"): "Relaxation",
    ("Israel", "Dead Sea (Israel)"): "Relaxation",
    ("Israel", "Masada"): "Adventure",
    ("Israel", "Galilee"): "Adventure",

    # Oman — Adventure default; Nizwa/Muscat Culture
    ("Oman", "Muscat"): "Culture",
    ("Oman", "Nizwa"): "Culture",
    ("Oman", "Salalah"): "Relaxation",

    # Egypt — Culture default; Red Sea Relaxation
    ("Egypt", "Hurghada"): "Relaxation",
    ("Egypt", "Sharm El Sheikh"): "Relaxation",
    ("Egypt", "Dahab"): "Relaxation",
    ("Egypt", "Marsa Alam"): "Relaxation",
    ("Egypt", "Mount Sinai"): "Adventure",
    ("Egypt", "Siwa Oasis"): "Adventure",

    # Morocco — Culture default; Atlas/Sahara Adventure
    ("Morocco", "Sahara - Merzouga"): "Adventure",
    ("Morocco", "Sahara - Zagora"): "Adventure",
    ("Morocco", "Atlas Mountains - Imlil"): "Adventure",
    ("Morocco", "Agadir"): "Relaxation",
    ("Morocco", "Essaouira"): "Relaxation",

    # Tanzania — Adventure default; Zanzibar Relaxation
    ("Tanzania", "Zanzibar - Stone Town"): "Culture",
    ("Tanzania", "Zanzibar - Nungwi"): "Relaxation",
    ("Tanzania", "Zanzibar - Paje"): "Relaxation",
    ("Tanzania", "Mafia Island"): "Relaxation",
    ("Tanzania", "Dar es Salaam"): "Culture",

    # Kenya — Adventure default; coast Relaxation; cities Culture
    ("Kenya", "Nairobi"): "Culture",
    ("Kenya", "Mombasa"): "Culture",
    ("Kenya", "Diani Beach"): "Relaxation",
    ("Kenya", "Lamu"): "Culture",

    # South Africa — Adventure default; Cape Town Culture; Sun City Family
    ("South Africa", "Cape Town"): "Culture",
    ("South Africa", "Johannesburg"): "Culture",
    ("South Africa", "Pretoria"): "Culture",
    ("South Africa", "Durban"): "Culture",
    ("South Africa", "Stellenbosch"): "Luxury",
    ("South Africa", "Wine Country - Franschhoek"): "Luxury",
    ("South Africa", "Sun City"): "Family",
    ("South Africa", "Hermanus"): "Relaxation",

    # Tunisia — Culture default; coast Relaxation
    ("Tunisia", "Hammamet"): "Relaxation",
    ("Tunisia", "Sousse"): "Relaxation",
    ("Tunisia", "Djerba"): "Relaxation",
    ("Tunisia", "Tozeur"): "Adventure",

    # United States — Culture default; lots of overrides
    ("United States", "Las Vegas"): "Luxury",
    ("United States", "Aspen"): "Luxury",
    ("United States", "Vail"): "Luxury",
    ("United States", "Park City"): "Luxury",
    ("United States", "Jackson Hole"): "Luxury",
    ("United States", "Sundance"): "Luxury",
    ("United States", "Napa Valley"): "Luxury",
    ("United States", "Sonoma"): "Luxury",
    ("United States", "Phoenix - Scottsdale"): "Luxury",
    ("United States", "Cape Cod"): "Luxury",
    ("United States", "Martha's Vineyard"): "Luxury",
    ("United States", "Nantucket"): "Luxury",
    ("United States", "Lake Tahoe"): "Luxury",
    ("United States", "Sedona"): "Relaxation",
    ("United States", "Orlando"): "Family",
    ("United States", "San Diego"): "Family",
    ("United States", "Niagara Falls (US)"): "Family",
    ("United States", "Williamsburg"): "Family",
    ("United States", "Yellowstone"): "Adventure",
    ("United States", "Grand Teton"): "Adventure",
    ("United States", "Yosemite"): "Adventure",
    ("United States", "Grand Canyon"): "Adventure",
    ("United States", "Moab"): "Adventure",
    ("United States", "Zion"): "Adventure",
    ("United States", "Bryce Canyon"): "Adventure",
    ("United States", "Arches"): "Adventure",
    ("United States", "Glacier National Park"): "Adventure",
    ("United States", "Bozeman"): "Adventure",
    ("United States", "Big Sur"): "Adventure",
    ("United States", "Acadia National Park"): "Adventure",
    ("United States", "Smoky Mountains"): "Adventure",
    ("United States", "Asheville"): "Culture",
    ("United States", "Alaska - Anchorage"): "Adventure",
    ("United States", "Alaska - Denali"): "Adventure",
    ("United States", "Alaska - Juneau"): "Adventure",
    ("United States", "Hawaii - Maui"): "Relaxation",
    ("United States", "Hawaii - Oahu"): "Relaxation",
    ("United States", "Hawaii - Big Island"): "Adventure",
    ("United States", "Hawaii - Kauai"): "Adventure",
    ("United States", "Miami"): "Relaxation",
    ("United States", "Key West"): "Relaxation",
    ("United States", "Outer Banks"): "Relaxation",

    # Canada — Adventure default; cities Culture; specific Luxury/Family
    ("Canada", "Toronto"): "Culture",
    ("Canada", "Vancouver"): "Culture",
    ("Canada", "Montreal"): "Culture",
    ("Canada", "Quebec City"): "Culture",
    ("Canada", "Ottawa"): "Culture",
    ("Canada", "Calgary"): "Culture",
    ("Canada", "Halifax"): "Culture",
    ("Canada", "Victoria"): "Culture",
    ("Canada", "Niagara Falls (CA)"): "Family",
    ("Canada", "Niagara-on-the-Lake"): "Luxury",
    ("Canada", "Whistler"): "Luxury",
    ("Canada", "Mont Tremblant"): "Luxury",
    ("Canada", "PEI - Charlottetown"): "Relaxation",
    ("Canada", "Cape Breton"): "Adventure",

    # Mexico — Culture default; Caribbean coast Relaxation; Pacific resorts Luxury
    ("Mexico", "Cancun"): "Family",
    ("Mexico", "Playa del Carmen"): "Relaxation",
    ("Mexico", "Tulum"): "Relaxation",
    ("Mexico", "Cozumel"): "Relaxation",
    ("Mexico", "Holbox"): "Relaxation",
    ("Mexico", "Bacalar"): "Relaxation",
    ("Mexico", "Puerto Escondido"): "Relaxation",
    ("Mexico", "Mazunte"): "Relaxation",
    ("Mexico", "Sayulita"): "Relaxation",
    ("Mexico", "Los Cabos"): "Luxury",
    ("Mexico", "Puerto Vallarta"): "Luxury",
    ("Mexico", "La Paz (Mexico)"): "Adventure",
    ("Mexico", "Todos Santos"): "Relaxation",
    ("Mexico", "Copper Canyon"): "Adventure",

    # Costa Rica — Adventure default; beach towns Relaxation
    ("Costa Rica", "Tamarindo"): "Relaxation",
    ("Costa Rica", "Nosara"): "Relaxation",
    ("Costa Rica", "Santa Teresa"): "Relaxation",
    ("Costa Rica", "Manuel Antonio"): "Relaxation",
    ("Costa Rica", "Jaco"): "Relaxation",
    ("Costa Rica", "Puerto Viejo"): "Relaxation",

    # Panama — Culture default
    ("Panama", "Bocas del Toro"): "Relaxation",
    ("Panama", "San Blas Islands"): "Relaxation",
    ("Panama", "Boquete"): "Adventure",

    # Guatemala — Culture default; Atitlán/Semuc Adventure
    ("Guatemala", "Lake Atitlán"): "Adventure",
    ("Guatemala", "Semuc Champey"): "Adventure",

    # Belize — Relaxation default
    ("Belize", "San Ignacio"): "Adventure",
    ("Belize", "Belize City"): "Culture",

    # Cuba — Culture default
    ("Cuba", "Varadero"): "Relaxation",
    ("Cuba", "Cayo Coco"): "Relaxation",
    ("Cuba", "Viñales"): "Adventure",

    # Dominican Republic — Relaxation default
    ("Dominican Republic", "Santo Domingo"): "Culture",
    ("Dominican Republic", "Punta Cana"): "Family",

    # Bahamas — Relaxation default
    ("Bahamas", "Paradise Island"): "Luxury",
    ("Bahamas", "Nassau"): "Family",

    # Saint Lucia — Relaxation default; Pitons Adventure
    ("Saint Lucia", "Soufrière (Pitons)"): "Adventure",

    # Peru — Adventure default; cities Culture
    ("Peru", "Lima"): "Culture",
    ("Peru", "Arequipa"): "Culture",
    ("Peru", "Trujillo"): "Culture",
    ("Peru", "Huacachina"): "Adventure",

    # Brazil — Relaxation default; cultural cities + nature
    ("Brazil", "Rio de Janeiro"): "Culture",
    ("Brazil", "São Paulo"): "Culture",
    ("Brazil", "Salvador"): "Culture",
    ("Brazil", "Brasília"): "Culture",
    ("Brazil", "Pantanal"): "Adventure",
    ("Brazil", "Manaus (Amazon)"): "Adventure",
    ("Brazil", "Foz do Iguaçu"): "Adventure",
    ("Brazil", "Chapada Diamantina"): "Adventure",
    ("Brazil", "Lençóis Maranhenses"): "Adventure",
    ("Brazil", "Trancoso"): "Luxury",

    # Argentina — Adventure default; BA/Tilcara/Salta Culture; Mendoza Luxury
    ("Argentina", "Buenos Aires"): "Culture",
    ("Argentina", "Mendoza"): "Luxury",
    ("Argentina", "Tilcara"): "Culture",
    ("Argentina", "Salta"): "Culture",
    ("Argentina", "Cafayate"): "Luxury",
    ("Argentina", "Córdoba (AR)"): "Culture",
    ("Argentina", "Tigre"): "Relaxation",
    ("Argentina", "Mar del Plata"): "Relaxation",

    # Chile — Adventure default; Santiago/Valparaíso Culture
    ("Chile", "Santiago"): "Culture",
    ("Chile", "Valparaíso"): "Culture",
    ("Chile", "Wine Country - Colchagua"): "Luxury",

    # Colombia — Culture default; Tayrona/Caño Adventure
    ("Colombia", "Tayrona National Park"): "Adventure",
    ("Colombia", "Caño Cristales"): "Adventure",
    ("Colombia", "Salento (Coffee Region)"): "Adventure",
    ("Colombia", "San Andrés"): "Relaxation",

    # Ecuador — Adventure default; cities Culture
    ("Ecuador", "Quito"): "Culture",
    ("Ecuador", "Cuenca (Ecuador)"): "Culture",
    ("Ecuador", "Otavalo"): "Culture",
    ("Ecuador", "Montañita"): "Relaxation",

    # Bolivia — Adventure default; cities Culture
    ("Bolivia", "La Paz (Bolivia)"): "Culture",
    ("Bolivia", "Sucre"): "Culture",
    ("Bolivia", "Santa Cruz (Bolivia)"): "Culture",
    ("Bolivia", "Potosí (city)"): "Culture",

    # Australia — Adventure default; cities Culture; wine Luxury; Gold Coast Family
    ("Australia", "Sydney"): "Culture",
    ("Australia", "Melbourne"): "Culture",
    ("Australia", "Brisbane"): "Culture",
    ("Australia", "Perth"): "Culture",
    ("Australia", "Adelaide"): "Culture",
    ("Australia", "Hobart"): "Culture",
    ("Australia", "Canberra"): "Culture",
    ("Australia", "Darwin"): "Culture",
    ("Australia", "Hunter Valley"): "Luxury",
    ("Australia", "Margaret River"): "Luxury",
    ("Australia", "Barossa Valley"): "Luxury",
    ("Australia", "Gold Coast"): "Family",
    ("Australia", "Sunshine Coast"): "Relaxation",
    ("Australia", "Noosa"): "Relaxation",
    ("Australia", "Byron Bay"): "Relaxation",

    # New Zealand — Adventure default; cities Culture
    ("New Zealand", "Auckland"): "Culture",
    ("New Zealand", "Wellington"): "Culture",
    ("New Zealand", "Christchurch"): "Culture",
    ("New Zealand", "Dunedin"): "Culture",
    ("New Zealand", "Marlborough"): "Luxury",
    ("New Zealand", "Hobbiton (Matamata)"): "Family",

    # Fiji — Relaxation default
    ("Fiji", "Suva"): "Culture",

    # French Polynesia — Relaxation default; Bora Bora Luxury
    ("French Polynesia", "Bora Bora"): "Luxury",
    ("French Polynesia", "Tahiti - Papeete"): "Culture",
}


def label_for(country: str, name: str) -> str:
    """Return the archetype label for a destination."""
    if (country, name) in OVERRIDES:
        return OVERRIDES[(country, name)]
    if country not in COUNTRY_DEFAULT:
        raise KeyError(f"No country default registered for {country!r}")
    return COUNTRY_DEFAULT[country]


def label_distribution() -> dict[str, int]:
    """Sanity-check helper: count labels across the entire seed list."""
    from data.seed_destinations import iter_destinations

    counts: dict[str, int] = {a: 0 for a in ARCHETYPES}
    for d in iter_destinations():
        counts[label_for(d["country"], d["name"])] += 1
    return counts


if __name__ == "__main__":
    counts = label_distribution()
    total = sum(counts.values())
    print(f"Total: {total}")
    for label, n in sorted(counts.items(), key=lambda x: -x[1]):
        pct = 100 * n / total
        print(f"  {label:<12} {n:>4}  ({pct:.1f}%)")

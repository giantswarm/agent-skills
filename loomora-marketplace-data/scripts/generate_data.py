#!/usr/bin/env python3
"""
Generate the Loomora marketplace demo dataset (fictional).

Deterministic: same seed always produces the same CSVs. Re-run after editing a
provider profile below to regenerate the whole dataset consistently.

    python3 scripts/generate_data.py

Writes providers.csv, products.csv, sales_monthly.csv, inventory_monthly.csv,
returns.csv, provider_deliveries.csv and reviews_monthly.csv into ../data/.
"""
import csv
import os
import random

SEED = 20260901
random.seed(SEED)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "data"))
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- time axis
MONTHS = []
_y, _m = 2024, 9
for _ in range(24):
    MONTHS.append("%04d-%02d" % (_y, _m))
    _m += 1
    if _m == 13:
        _m, _y = 1, _y + 1

# marketplace-wide seasonality by calendar month (index = month number - 1)
SEASON = {
    "none":   [1.00, 0.92, 1.00, 1.02, 1.03, 1.00, 0.98, 1.00, 1.02, 1.05, 1.18, 1.22],
    "summer": [0.62, 0.60, 0.78, 1.02, 1.28, 1.42, 1.45, 1.20, 0.92, 0.74, 0.72, 0.70],
    "winter": [1.05, 0.90, 0.82, 0.66, 0.55, 0.50, 0.52, 0.68, 1.02, 1.30, 1.52, 1.48],
    "spring": [0.78, 0.86, 1.20, 1.35, 1.30, 1.08, 0.92, 0.85, 0.95, 0.98, 1.05, 1.02],
    "active": [1.38, 1.12, 1.10, 1.05, 1.02, 0.95, 0.90, 0.92, 1.15, 1.10, 1.20, 1.12],
    "denim":  [0.95, 0.90, 1.02, 1.05, 1.00, 0.95, 0.90, 0.98, 1.20, 1.15, 1.22, 1.10],
}

# marketplace-wide traffic growth, applied on top of provider growth
MARKET_GROWTH = 1.008

REASONS = [
    "SIZE_TOO_SMALL", "SIZE_TOO_LARGE", "QUALITY_ISSUE", "NOT_AS_PICTURED",
    "CHANGED_MIND", "DAMAGED_IN_TRANSIT", "WRONG_ITEM_SENT", "LATE_DELIVERY",
]

def mix(**kw):
    """Return a full reason mix from the named shares, remainder to CHANGED_MIND."""
    out = {r: 0.0 for r in REASONS}
    out.update({k: v for k, v in kw.items()})
    total = sum(out.values())
    out["CHANGED_MIND"] += max(0.0, 1.0 - total)
    s = sum(out.values())
    return {k: v / s for k, v in out.items()}

# ------------------------------------------------------------ provider book
# Each provider profile below encodes one deliberate performance story.
PROVIDERS = [
    dict(
        pid="PRV-001", name="adidas", country="DE", segment="Sportswear",
        onboarded="2019-03-01", commission=0.19, terms=45, am="Lena Brauer",
        renewal="2027-03-31", tier="Strategic", n=34, price=(34, 179),
        base=210, growth=1.0135, season="active",
        ret=0.118, ret_trend=-0.00075,
        reasons=mix(SIZE_TOO_SMALL=0.16, SIZE_TOO_LARGE=0.13, QUALITY_ISSUE=0.05,
                    NOT_AS_PICTURED=0.06, DAMAGED_IN_TRANSIT=0.02),
        otif=0.972, otif_trend=0.00055, otif_noise=0.010, reject=0.004,
        stockout=0.05, rating=4.45, rating_trend=0.0035,
        lines=["Terrex", "Ultraboost", "Adicolor", "Tiro", "Z.N.E.", "Own the Run"],
        items=["Tee", "Hoodie", "Track Pant", "Windbreaker", "Sneaker", "Tights", "Shorts", "Jacket"],
    ),
    dict(
        pid="PRV-002", name="Ombra Fashion", country="IT", segment="Fast fashion",
        onboarded="2023-06-15", commission=0.27, terms=30, am="Marco Villa",
        renewal="2026-11-30", tier="Volume", n=40, price=(9, 49),
        base=290, growth=1.0025, season="none",
        ret=0.284, ret_trend=0.00235,
        reasons=mix(SIZE_TOO_SMALL=0.24, SIZE_TOO_LARGE=0.09, QUALITY_ISSUE=0.21,
                    NOT_AS_PICTURED=0.19, DAMAGED_IN_TRANSIT=0.04, WRONG_ITEM_SENT=0.03),
        otif=0.883, otif_trend=-0.00135, otif_noise=0.028, reject=0.031,
        stockout=0.14, rating=3.55, rating_trend=-0.0135,
        lines=["Neroluce", "Vetro", "Basico", "Notte", "Sabbia"],
        items=["Blouse", "Mini Dress", "Crop Top", "Cargo Pant", "Bodysuit", "Skirt", "Blazer", "Co-ord Set"],
    ),
    dict(
        pid="PRV-003", name="Nordvik Studio", country="SE", segment="Contemporary",
        onboarded="2020-09-01", commission=0.22, terms=45, am="Lena Brauer",
        renewal="2027-08-31", tier="Core", n=24, price=(45, 229),
        base=120, growth=1.0055, season="none",
        ret=0.163, ret_trend=-0.00015,
        reasons=mix(SIZE_TOO_SMALL=0.14, SIZE_TOO_LARGE=0.17, QUALITY_ISSUE=0.06,
                    NOT_AS_PICTURED=0.08, DAMAGED_IN_TRANSIT=0.02),
        otif=0.951, otif_trend=0.00015, otif_noise=0.014, reject=0.007,
        stockout=0.06, rating=4.32, rating_trend=0.0012,
        lines=["Fjell", "Linje", "Havn", "Sten"],
        items=["Knit", "Trouser", "Overshirt", "Wool Coat", "Shirt Dress", "Cardigan", "Tee"],
    ),
    dict(
        pid="PRV-004", name="Maison Rive", country="FR", segment="Premium",
        onboarded="2021-02-01", commission=0.16, terms=60, am="Sophie Aumont",
        renewal="2027-01-31", tier="Premium", n=16, price=(139, 690),
        base=42, growth=1.0085, season="none",
        ret=0.145, ret_trend=-0.00035,
        reasons=mix(SIZE_TOO_SMALL=0.15, SIZE_TOO_LARGE=0.14, QUALITY_ISSUE=0.03,
                    NOT_AS_PICTURED=0.09, DAMAGED_IN_TRANSIT=0.03),
        otif=0.944, otif_trend=0.0004, otif_noise=0.018, reject=0.005,
        stockout=0.09, rating=4.51, rating_trend=0.0015,
        lines=["Rive Gauche", "Atelier", "Sainte-Claire"],
        items=["Silk Blouse", "Tailored Blazer", "Wool Trouser", "Trench Coat", "Midi Dress", "Cashmere Knit"],
    ),
    dict(
        pid="PRV-005", name="Bloomwell", country="NL", segment="Sustainable basics",
        onboarded="2022-04-01", commission=0.24, terms=30, am="Sophie Aumont",
        renewal="2027-04-30", tier="Core", n=22, price=(19, 89),
        base=140, growth=1.0115, season="none",
        ret=0.132, ret_trend=-0.00025,
        reasons=mix(SIZE_TOO_SMALL=0.17, SIZE_TOO_LARGE=0.15, QUALITY_ISSUE=0.05,
                    NOT_AS_PICTURED=0.07, DAMAGED_IN_TRANSIT=0.02),
        otif=0.958, otif_trend=0.0003, otif_noise=0.013, reject=0.006,
        stockout=0.07, rating=4.28, rating_trend=0.0022,
        lines=["Everyday", "Organic Core", "Reworn"],
        items=["Tee", "Sweatshirt", "Chino", "Denim Jacket", "Sock Pack", "Jersey Dress", "Legging"],
    ),
    dict(
        pid="PRV-006", name="Tessuto Milano", country="IT", segment="Knitwear",
        onboarded="2020-01-15", commission=0.21, terms=45, am="Marco Villa",
        renewal="2026-12-31", tier="Core", n=20, price=(59, 279),
        base=105, growth=1.004, season="winter",
        ret=0.155, ret_trend=0.0002,
        reasons=mix(SIZE_TOO_SMALL=0.19, SIZE_TOO_LARGE=0.15, QUALITY_ISSUE=0.07,
                    NOT_AS_PICTURED=0.08, LATE_DELIVERY=0.04, DAMAGED_IN_TRANSIT=0.02),
        otif=0.929, otif_trend=-0.0002, otif_noise=0.020, reject=0.009,
        stockout=0.11, rating=4.21, rating_trend=0.0008,
        lines=["Filo", "Alpino", "Corso"],
        items=["Merino Crew", "Cable Knit", "Turtleneck", "Knit Vest", "Cardigan", "Knit Dress", "Scarf"],
    ),
    dict(
        pid="PRV-007", name="Kappler & Sohn", country="DE", segment="Heritage outerwear",
        onboarded="2018-08-01", commission=0.20, terms=60, am="Thomas Feldt",
        renewal="2026-10-31", tier="Legacy", n=18, price=(89, 449),
        base=104, growth=0.9880, season="winter",
        ret=0.171, ret_trend=0.0011,
        reasons=mix(SIZE_TOO_SMALL=0.13, SIZE_TOO_LARGE=0.21, QUALITY_ISSUE=0.06,
                    NOT_AS_PICTURED=0.15, LATE_DELIVERY=0.03, DAMAGED_IN_TRANSIT=0.02),
        otif=0.947, otif_trend=-0.00045, otif_noise=0.016, reject=0.008,
        stockout=0.04, rating=4.05, rating_trend=-0.0055,
        lines=["Loden", "Feldjacke", "Kontor"],
        items=["Parka", "Wool Overcoat", "Field Jacket", "Quilted Vest", "Peacoat", "Rain Coat"],
    ),
    dict(
        pid="PRV-008", name="Lumen Athletics", country="GB", segment="Activewear",
        onboarded="2023-01-10", commission=0.25, terms=30, am="Thomas Feldt",
        renewal="2027-01-09", tier="Growth", n=20, price=(24, 119),
        base=125, growth=1.0295, season="active",
        ret=0.174, ret_trend=-0.0004,
        reasons=mix(SIZE_TOO_SMALL=0.26, SIZE_TOO_LARGE=0.11, QUALITY_ISSUE=0.06,
                    NOT_AS_PICTURED=0.07, LATE_DELIVERY=0.05, DAMAGED_IN_TRANSIT=0.02),
        otif=0.905, otif_trend=-0.0009, otif_noise=0.024, reject=0.011,
        stockout=0.29, rating=4.36, rating_trend=0.0028,
        lines=["Flux", "Halo", "Kinetic"],
        items=["Sports Bra", "Seamless Legging", "Training Short", "Running Tee", "Zip Hoodie", "Tank"],
    ),
    dict(
        pid="PRV-009", name="Vela Denim", country="PT", segment="Denim",
        onboarded="2021-07-01", commission=0.23, terms=45, am="Sophie Aumont",
        renewal="2027-06-30", tier="Core", n=22, price=(49, 169),
        base=132, growth=1.006, season="denim",
        ret=0.198, ret_trend=0.0016,
        reasons=mix(SIZE_TOO_SMALL=0.34, SIZE_TOO_LARGE=0.10, QUALITY_ISSUE=0.05,
                    NOT_AS_PICTURED=0.07, DAMAGED_IN_TRANSIT=0.02),
        otif=0.938, otif_trend=0.0001, otif_noise=0.017, reject=0.007,
        stockout=0.08, rating=4.11, rating_trend=-0.0035,
        lines=["Halden", "Costa", "Porto"],
        items=["Slim Jean", "Straight Jean", "Wide Leg Jean", "Denim Jacket", "Denim Skirt", "Short"],
    ),
    dict(
        pid="PRV-010", name="Sable & Stone", country="ES", segment="Accessories",
        onboarded="2020-11-01", commission=0.26, terms=45, am="Marco Villa",
        renewal="2027-10-31", tier="Core", n=18, price=(29, 349),
        base=88, growth=1.0095, season="none",
        ret=0.089, ret_trend=-0.0002,
        reasons=mix(SIZE_TOO_SMALL=0.04, SIZE_TOO_LARGE=0.03, QUALITY_ISSUE=0.09,
                    NOT_AS_PICTURED=0.22, DAMAGED_IN_TRANSIT=0.07),
        otif=0.961, otif_trend=0.0002, otif_noise=0.012, reject=0.005,
        stockout=0.06, rating=4.38, rating_trend=0.0014,
        lines=["Piedra", "Costa Brava", "Marisol"],
        items=["Leather Belt", "Tote Bag", "Crossbody Bag", "Card Holder", "Sunglasses", "Silk Scarf"],
    ),
    dict(
        pid="PRV-011", name="Kyoto Line", country="JP", segment="Minimal design",
        onboarded="2025-05-01", commission=0.235, terms=45, am="Lena Brauer",
        renewal="2027-04-30", tier="Growth", n=14, price=(69, 319),
        base=64, growth=1.0345, season="none",
        ret=0.121, ret_trend=-0.0006,
        reasons=mix(SIZE_TOO_SMALL=0.22, SIZE_TOO_LARGE=0.08, QUALITY_ISSUE=0.03,
                    NOT_AS_PICTURED=0.09, DAMAGED_IN_TRANSIT=0.02),
        otif=0.966, otif_trend=0.0006, otif_noise=0.013, reject=0.004,
        stockout=0.13, rating=4.47, rating_trend=0.0025,
        lines=["Kiri", "Sumi", "Aizome"],
        items=["Wide Trouser", "Layer Shirt", "Wrap Coat", "Linen Tunic", "Sashiko Jacket"],
    ),
    dict(
        pid="PRV-012", name="Fleur de Sel", country="FR", segment="Occasionwear",
        onboarded="2022-02-01", commission=0.245, terms=30, am="Sophie Aumont",
        renewal="2027-01-31", tier="Seasonal", n=16, price=(59, 249),
        base=110, growth=1.002, season="summer",
        ret=0.216, ret_trend=0.0007,
        reasons=mix(SIZE_TOO_SMALL=0.21, SIZE_TOO_LARGE=0.14, QUALITY_ISSUE=0.05,
                    NOT_AS_PICTURED=0.18, DAMAGED_IN_TRANSIT=0.02),
        otif=0.933, otif_trend=-0.0003, otif_noise=0.021, reject=0.008,
        stockout=0.07, rating=4.09, rating_trend=-0.0018,
        lines=["Riviera", "Camargue", "Bastide"],
        items=["Maxi Dress", "Linen Shirt", "Wrap Dress", "Sun Hat", "Espadrille", "Playsuit"],
    ),
    dict(
        pid="PRV-013", name="Brixton Union", country="GB", segment="Streetwear",
        onboarded="2022-09-01", commission=0.25, terms=30, am="Thomas Feldt",
        renewal="2026-09-30", tier="Growth", n=18, price=(29, 149),
        base=118, growth=1.0105, season="none",
        ret=0.187, ret_trend=0.0004,
        reasons=mix(SIZE_TOO_SMALL=0.15, SIZE_TOO_LARGE=0.19, QUALITY_ISSUE=0.08,
                    NOT_AS_PICTURED=0.12, DAMAGED_IN_TRANSIT=0.03),
        otif=0.912, otif_trend=-0.0004, otif_noise=0.026, reject=0.014,
        stockout=0.19, rating=4.14, rating_trend=0.0006,
        lines=["Union", "Depot", "Southside"],
        items=["Graphic Tee", "Oversized Hoodie", "Cargo Pant", "Puffer Jacket", "Cap", "Sweat Short"],
    ),
    dict(
        pid="PRV-014", name="Halcyon Home", country="DK", segment="Loungewear",
        onboarded="2021-01-15", commission=0.235, terms=45, am="Thomas Feldt",
        renewal="2026-12-31", tier="Legacy", n=12, price=(35, 139),
        base=118, growth=0.9865, season="winter",
        ret=0.141, ret_trend=0.0005,
        reasons=mix(SIZE_TOO_SMALL=0.12, SIZE_TOO_LARGE=0.22, QUALITY_ISSUE=0.07,
                    NOT_AS_PICTURED=0.11, DAMAGED_IN_TRANSIT=0.02),
        otif=0.953, otif_trend=-0.0002, otif_noise=0.014, reject=0.006,
        stockout=0.05, rating=4.19, rating_trend=-0.0028,
        lines=["Stille", "Hygge", "Morgen"],
        items=["Lounge Set", "Robe", "Jersey Pant", "Waffle Tee", "Slipper Sock"],
    ),
    dict(
        pid="PRV-015", name="Trueform", country="PL", segment="Shapewear & basics",
        onboarded="2023-03-01", commission=0.26, terms=30, am="Marco Villa",
        renewal="2027-02-28", tier="Growth", n=10, price=(22, 79),
        base=150, growth=1.0165, season="none",
        ret=0.312, ret_trend=-0.0021,
        reasons=mix(SIZE_TOO_SMALL=0.38, SIZE_TOO_LARGE=0.17, QUALITY_ISSUE=0.05,
                    NOT_AS_PICTURED=0.09, DAMAGED_IN_TRANSIT=0.01),
        otif=0.949, otif_trend=0.0004, otif_noise=0.015, reject=0.006,
        stockout=0.10, rating=4.02, rating_trend=0.0045,
        lines=["Contour", "Base", "Second Skin"],
        items=["Shaping Body", "Seamless Brief", "Shaping Short", "Bralette", "Slip Dress"],
    ),
]

COLORS = ["Black", "Off White", "Navy", "Sand", "Olive", "Charcoal", "Terracotta",
          "Ecru", "Slate Blue", "Forest", "Burgundy", "Stone", "Cream", "Rust"]
SIZE_RANGES = ["XS-XL", "XS-XXL", "S-XL", "34-46", "36-44", "One Size", "26-36"]
GENDERS = ["Women", "Men", "Unisex"]

# ---------------------------------------------------------------- products
products = []
for p in PROVIDERS:
    lo, hi = p["price"]
    for i in range(p["n"]):
        line = p["lines"][i % len(p["lines"])]
        item = p["items"][(i // len(p["lines"])) % len(p["items"])]
        # price skewed toward the lower half of the band
        price = round(lo + (hi - lo) * (random.random() ** 1.7), 0) - 0.05
        gender = random.choice(GENDERS) if p["segment"] != "Accessories" else "Unisex"
        # launch date: some products launch mid-window
        launch_month = 0
        if p["pid"] == "PRV-011":
            launch_month = random.choice([8, 8, 9, 10, 12, 14])
        elif random.random() < 0.22:
            launch_month = random.choice([2, 4, 6, 8, 10, 12, 14, 16, 18])
        disc = ""
        if p["pid"] in ("PRV-007", "PRV-014") and random.random() < 0.25:
            disc = MONTHS[random.choice([13, 15, 17, 19])]
        elif p["pid"] == "PRV-002" and random.random() < 0.18:
            disc = MONTHS[random.choice([9, 12, 16, 20])]
        products.append(dict(
            product_id="SKU-%s-%03d" % (p["pid"].split("-")[1], i + 1),
            provider_id=p["pid"], provider_name=p["name"],
            product_name="%s %s" % (line, item),
            product_line=line, category=p["segment"], item_type=item,
            gender=gender, color=random.choice(COLORS),
            size_range=random.choice(SIZE_RANGES),
            list_price_eur=price, commission_pct=p["commission"],
            launch_month=launch_month, discontinued_month=disc,
            popularity=round(0.35 + random.random() ** 1.5 * 2.4, 3),
        ))

# --------------------------------------------------- monthly fact generation
sales, inventory, deliveries, reviews = [], [], [], []
returns_acc = {}
prov_by_id = {p["pid"]: p for p in PROVIDERS}

for p in PROVIDERS:
    prods = [x for x in products if x["provider_id"] == p["pid"]]
    for mi, month in enumerate(MONTHS):
        cal_m = int(month[5:7])
        season = SEASON[p["season"]][cal_m - 1]
        growth = p["growth"] ** mi
        market = MARKET_GROWTH ** mi

        # ---- provider inbound delivery performance
        otif = p["otif"] + p["otif_trend"] * mi + random.gauss(0, p["otif_noise"])
        # Q4 peak strains everyone's inbound
        if cal_m in (10, 11):
            otif -= 0.022
        otif = max(0.62, min(0.995, otif))
        expected = max(8, int(round(len(prods) * 0.85 * season + random.gauss(0, 2))))
        on_time = int(round(expected * otif))
        late = expected - on_time
        delay = round(max(0.0, random.gauss(2.6 if p["pid"] != "PRV-001" else 1.2, 0.9)), 1) if late else 0.0
        deliveries.append(dict(
            month=month, provider_id=p["pid"], provider_name=p["name"],
            shipments_expected=expected, shipments_on_time=on_time,
            shipments_late=late, otif_pct=round(on_time / expected * 100, 1),
            avg_delay_days=delay,
            asn_error_count=int(round(max(0, random.gauss(0.4 + p["reject"] * 30, 0.7)))),
            quality_reject_pct=round(max(0.0, p["reject"] * 100 + random.gauss(0, 0.35)), 2),
        ))

        for pr in prods:
            if mi < pr["launch_month"]:
                continue
            if pr["discontinued_month"] and month > pr["discontinued_month"]:
                continue

            ramp = min(1.0, 0.45 + 0.2 * (mi - pr["launch_month"])) if pr["launch_month"] else 1.0
            units = p["base"] * pr["popularity"] * season * growth * market * ramp
            units *= random.uniform(0.80, 1.22)

            # one-off events that give the dataset findable stories
            if p["pid"] == "PRV-013" and month == "2025-06":
                units *= 3.4                      # viral social moment
            if p["pid"] == "PRV-013" and month == "2025-07":
                units *= 1.7
            if p["pid"] == "PRV-012" and month in ("2026-04", "2026-05"):
                units *= 0.55                     # cold, wet spring 2026
            if p["pid"] == "PRV-008" and mi >= 14:
                units *= 1.18                     # breakout after a retail feature
            if p["pid"] == "PRV-002" and mi >= 18:
                units *= 0.88                     # ratings damage starts to bite
            if cal_m == 11:
                units *= 1.15                     # Black Friday uplift

            units = max(0, int(round(units)))

            # stock-outs suppress realised sales
            so_risk = p["stockout"]
            if cal_m in (11, 12):
                so_risk *= 1.5
            stockout_days = 0
            if random.random() < so_risk:
                stockout_days = random.choice([2, 3, 5, 7, 9, 12, 16, 21])
                units = int(round(units * (1 - stockout_days / 34.0)))

            price = pr["list_price_eur"]
            gross = units * price
            disc_rate = 0.06
            if cal_m in (1, 7):
                disc_rate = 0.19               # end-of-season sale
            if cal_m == 11:
                disc_rate = 0.24               # Black Friday
            if p["pid"] == "PRV-002":
                disc_rate += 0.07
            if p["pid"] == "PRV-004":
                disc_rate = max(0.0, disc_rate - 0.045)
            discount = round(gross * disc_rate * random.uniform(0.85, 1.15), 2)
            net = round(gross - discount, 2)

            rr = p["ret"] + p["ret_trend"] * mi + random.gauss(0, 0.014)
            # one product line carries an outsized fit problem
            if p["pid"] == "PRV-009" and pr["product_line"] == "Halden":
                rr += 0.085
            if p["pid"] == "PRV-002" and pr["product_line"] == "Vetro":
                rr += 0.06
            rr = max(0.02, min(0.62, rr))
            returned = int(round(units * rr))

            orders = max(units, int(round(units / random.uniform(1.05, 1.4))))
            views = int(round(orders * random.uniform(22, 58)))
            atc = int(round(views * random.uniform(0.055, 0.135)))

            sales.append(dict(
                month=month, product_id=pr["product_id"], provider_id=p["pid"],
                units_sold=units, units_returned=returned, orders=orders,
                gross_revenue_eur=round(gross, 2), discount_eur=discount,
                net_revenue_eur=net, page_views=views, add_to_cart=atc,
            ))

            # ---- return reasons
            if returned:
                remaining = returned
                keys = [r for r in REASONS if p["reasons"][r] > 0]
                local = dict(p["reasons"])
                if p["pid"] == "PRV-009" and pr["product_line"] == "Halden":
                    local["SIZE_TOO_SMALL"] += 0.22
                if p["pid"] == "PRV-002" and pr["product_line"] == "Vetro":
                    local["QUALITY_ISSUE"] += 0.14
                tot = sum(local.values())
                for j, r in enumerate(keys):
                    if j == len(keys) - 1:
                        n = remaining
                    else:
                        n = int(round(returned * local[r] / tot))
                        n = min(n, remaining)
                    if n > 0:
                        k = (month, p["pid"], pr["product_line"], r)
                        returns_acc[k] = returns_acc.get(k, 0) + n
                    remaining -= n
                    if remaining <= 0:
                        break

            # ---- inventory position
            cover_target = 62
            if p["pid"] == "PRV-008":
                cover_target = 28              # chronically under-stocked
            if p["pid"] == "PRV-012" and month >= "2026-04":
                cover_target = 168             # rain-soaked spring left stock behind
            if p["pid"] == "PRV-007":
                cover_target = 118             # aging catalogue, slow movers
            if p["pid"] == "PRV-002":
                cover_target = 44
            daily = max(0.4, units / 30.0)
            on_hand = int(round(daily * cover_target * random.uniform(0.7, 1.35)))
            received = max(0, int(round(units * random.uniform(0.75, 1.3))))
            inventory.append(dict(
                month=month, product_id=pr["product_id"], provider_id=p["pid"],
                units_on_hand_end=on_hand, units_received=received,
                stockout_days=stockout_days,
                days_of_cover=round(on_hand / daily, 1),
                sell_through_pct=round(units / max(1, on_hand + units) * 100, 1),
            ))

            # ---- reviews
            rating = p["rating"] + p["rating_trend"] * mi + random.gauss(0, 0.09)
            if p["pid"] == "PRV-009" and pr["product_line"] == "Halden":
                rating -= 0.35
            if p["pid"] == "PRV-002" and pr["product_line"] == "Vetro":
                rating -= 0.45
            rating = max(1.6, min(5.0, rating))
            rc = int(round(units * random.uniform(0.02, 0.07)))
            if rc:
                reviews.append(dict(month=month, product_id=pr["product_id"],
                                    provider_id=p["pid"], review_count=rc,
                                    avg_rating=round(rating, 2)))

# ------------------------------------------------------------------- output
def write(name, rows, fields):
    path = os.path.join(OUT, name)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in fields})
    print("%-26s %6d rows" % (name, len(rows)))

write("providers.csv", [dict(
    provider_id=p["pid"], provider_name=p["name"], country=p["country"],
    segment=p["segment"], tier=p["tier"], onboarded_date=p["onboarded"],
    commission_pct=p["commission"], payment_terms_days=p["terms"],
    account_manager=p["am"], contract_renewal_date=p["renewal"],
) for p in PROVIDERS], ["provider_id", "provider_name", "country", "segment", "tier",
                        "onboarded_date", "commission_pct", "payment_terms_days",
                        "account_manager", "contract_renewal_date"])

write("products.csv", products, ["product_id", "provider_id", "provider_name",
      "product_name", "product_line", "item_type", "category", "gender", "color",
      "size_range", "list_price_eur", "commission_pct", "discontinued_month"])

write("sales_monthly.csv", sales, ["month", "product_id", "provider_id", "units_sold",
      "units_returned", "orders", "gross_revenue_eur", "discount_eur",
      "net_revenue_eur", "page_views", "add_to_cart"])

write("inventory_monthly.csv", inventory, ["month", "product_id", "provider_id",
      "units_on_hand_end", "units_received", "stockout_days", "days_of_cover",
      "sell_through_pct"])

# Returns are aggregated to product-line grain: reason mixes vary by line, not by
# individual SKU, so per-SKU rows carried no extra signal at 4x the file size.
returns = [dict(month=m, provider_id=pv, product_line=ln, reason_code=rc, units=u)
           for (m, pv, ln, rc), u in sorted(returns_acc.items())]
write("returns.csv", returns, ["month", "provider_id", "product_line", "reason_code", "units"])

write("provider_deliveries.csv", deliveries, ["month", "provider_id", "provider_name",
      "shipments_expected", "shipments_on_time", "shipments_late", "otif_pct",
      "avg_delay_days", "asn_error_count", "quality_reject_pct"])

write("reviews_monthly.csv", reviews, ["month", "product_id", "provider_id",
      "review_count", "avg_rating"])

print("\nmonths: %s .. %s   providers: %d   products: %d" %
      (MONTHS[0], MONTHS[-1], len(PROVIDERS), len(products)))

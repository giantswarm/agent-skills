# Loomora marketplace data dictionary

Seven CSV extracts in `data/`, loaded into SQLite by `scripts/query.py`. Coverage
is 24 complete months, 2024-09 through 2026-08. All amounts are EUR. All months
are `YYYY-MM` strings and sort correctly as text, so `BETWEEN '2026-03' AND '2026-08'`
works directly.

## Tables

### providers (15 rows)
One row per brand selling on the marketplace.

| column | meaning |
| --- | --- |
| `provider_id` | `PRV-001` .. `PRV-015` |
| `provider_name` | Brand name as used in conversation |
| `country` | ISO country of the supplying entity |
| `segment` | Assortment segment (Sportswear, Fast fashion, Premium, ...) |
| `tier` | Commercial tier: Strategic, Premium, Core, Growth, Volume, Seasonal, Legacy |
| `onboarded_date` | First day live on the marketplace |
| `commission_pct` | Loomora's commission share of net revenue, as a decimal |
| `payment_terms_days` | Days from invoice to payout |
| `account_manager` | Loomora-side commercial owner |
| `contract_renewal_date` | Next contract renewal, the anchor for procurement prep |

### products (304 rows)
One row per SKU. `discontinued_month` is empty for live SKUs; where set, the SKU
has no sales rows after that month.

Key columns: `product_id`, `provider_id`, `product_name`, `product_line`,
`item_type`, `gender`, `color`, `size_range`, `list_price_eur`, `commission_pct`.

`product_line` matters: fit and quality problems usually cluster in one line
rather than spreading evenly across a provider's catalogue.

### sales_monthly (6,233 rows)
One row per SKU per month. `units_returned` counts units returned against sales
in that month, so it is already aligned to the same period.

| column | meaning |
| --- | --- |
| `units_sold` | Units shipped to customers |
| `units_returned` | Units returned out of those sales |
| `orders` | Distinct orders containing the SKU |
| `gross_revenue_eur` | Units at full list price |
| `discount_eur` | Promotional and markdown value given away |
| `net_revenue_eur` | `gross_revenue_eur` minus `discount_eur`, before returns |
| `page_views`, `add_to_cart` | Funnel counters for the SKU's detail page |

### inventory_monthly (6,233 rows)
One row per SKU per month, position at month end.

| column | meaning |
| --- | --- |
| `units_on_hand_end` | Sellable units in the warehouse at month end |
| `units_received` | Units booked in from the provider during the month |
| `stockout_days` | Days in the month the SKU was unavailable to buy |
| `days_of_cover` | On-hand units divided by average daily sales |
| `sell_through_pct` | Units sold as a share of units available in the month |

### returns (7,319 rows)
One row per provider, month, product line and reason code. Reason units sum to
`units_returned` in `sales_monthly` for the same provider and month.

Grain note: returns are recorded per product line, not per SKU. Fit and quality
problems cluster by line rather than by individual SKU, so the line is both the
actionable unit and the one the reports name. To attribute returns to a single
SKU, use `units_returned` in `sales_monthly`, which is per SKU.

Reason codes: `SIZE_TOO_SMALL`, `SIZE_TOO_LARGE`, `QUALITY_ISSUE`,
`NOT_AS_PICTURED`, `CHANGED_MIND`, `DAMAGED_IN_TRANSIT`, `WRONG_ITEM_SENT`,
`LATE_DELIVERY`.

`CHANGED_MIND` is the baseline every fashion retailer carries and is rarely
actionable. The reasons worth raising with a provider are the size codes
(sizing charts and grading), `QUALITY_ISSUE` (materials and construction) and
`NOT_AS_PICTURED` (photography and copy).

### provider_deliveries (360 rows)
One row per provider per month, inbound performance from the provider into
Loomora's warehouse.

| column | meaning |
| --- | --- |
| `shipments_expected` | Purchase orders due in the month |
| `shipments_on_time` / `shipments_late` | Split of those against the agreed date |
| `otif_pct` | On time in full, as a percentage |
| `avg_delay_days` | Mean delay across the late shipments only |
| `asn_error_count` | Advance shipping notice mismatches causing manual rework |
| `quality_reject_pct` | Share of received units rejected at goods-in |

### reviews_monthly (6,206 rows)
One row per SKU per month: `review_count` and `avg_rating` (1.0 to 5.0) for
reviews left in that month. Weight by `review_count` when aggregating, never
average the averages.

## Metric conventions

Prepared views in `scripts/query.py` already apply these. Match them when
writing custom SQL so numbers stay comparable across answers.

- **Return rate** = `units_returned / units_sold`, expressed as a percentage.
  Always state the period, since it moves with the sale calendar.
- **Kept units** = `units_sold - units_returned`. The only units that actually
  earn money.
- **Kept revenue** = `net_revenue_eur` scaled to kept units.
- **Commission** = kept revenue times `commission_pct`. Loomora earns commission
  on what customers keep, not on what they order.
- **Return cost** = `units_returned` times EUR 6.90, the blended handling cost
  per returned unit (pick, pack, inbound freight, inspection, restocking). It is
  an internal planning assumption, not a booked cost, so label it as an
  assumption whenever it drives a recommendation.
- **Contribution** = commission minus return cost. This is the number that
  separates providers who look good on volume from providers who are actually
  worth shelf space.
- **Contribution margin** = contribution as a share of kept revenue.
- **Days of cover** above roughly 120 signals overstock and markdown risk.
  Below roughly 30 signals under-supply, and the lost sales show up as
  `stockout_days`.
- **Marketplace benchmarks**, computed rather than fixed: pull the all-provider
  figure for the same month before calling any single provider good or bad.

## Prepared views

- `v_sales`: one row per SKU-month with products and providers joined in, plus
  kept units, kept revenue, commission, return cost, contribution, return rate
  and conversion already computed.
- `v_provider_month`: one row per provider-month, the sales figures aggregated
  and inbound delivery, rating, stockout days and average cover joined on.
- `v_product_month`: `v_sales` with inventory and review columns attached.

Prefer these views over the raw tables. They encode the metric definitions above,
so two answers built on them will agree with each other.

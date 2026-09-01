#!/usr/bin/env python3
"""
Loomora marketplace analytics query tool.

Loads the marketplace CSV extracts into an in-memory SQLite database with a set
of prepared views and runs SQL against it. Stdlib only, no dependencies.

    python3 scripts/query.py schema
    python3 scripts/query.py sql "SELECT provider_name, SUM(units_sold) u
                                  FROM v_sales WHERE month='2026-08'
                                  GROUP BY 1 ORDER BY u DESC"
    python3 scripts/query.py providers --month 2026-08
    python3 scripts/query.py provider "Vela Denim" --from 2026-03 --to 2026-08
    python3 scripts/query.py month 2026-08
    python3 scripts/query.py returns "Ombra" --from 2026-06 --to 2026-08

Add --csv to any command for machine-readable output, --limit N to cap rows.
"""
import argparse
import csv
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))

# Cost the marketplace carries for each returned unit (pick, pack, inbound
# freight, inspection, restocking). Documented in references/data-dictionary.md.
RETURN_HANDLING_COST_EUR = 6.90

SCHEMA = {
    "providers": [
        ("provider_id", "TEXT"), ("provider_name", "TEXT"), ("country", "TEXT"),
        ("segment", "TEXT"), ("tier", "TEXT"), ("onboarded_date", "TEXT"),
        ("commission_pct", "REAL"), ("payment_terms_days", "INTEGER"),
        ("account_manager", "TEXT"), ("contract_renewal_date", "TEXT"),
    ],
    "products": [
        ("product_id", "TEXT"), ("provider_id", "TEXT"), ("provider_name", "TEXT"),
        ("product_name", "TEXT"), ("product_line", "TEXT"), ("item_type", "TEXT"),
        ("category", "TEXT"), ("gender", "TEXT"), ("color", "TEXT"),
        ("size_range", "TEXT"), ("list_price_eur", "REAL"),
        ("commission_pct", "REAL"), ("discontinued_month", "TEXT"),
    ],
    "sales_monthly": [
        ("month", "TEXT"), ("product_id", "TEXT"), ("provider_id", "TEXT"),
        ("units_sold", "INTEGER"), ("units_returned", "INTEGER"), ("orders", "INTEGER"),
        ("gross_revenue_eur", "REAL"), ("discount_eur", "REAL"),
        ("net_revenue_eur", "REAL"), ("page_views", "INTEGER"), ("add_to_cart", "INTEGER"),
    ],
    "inventory_monthly": [
        ("month", "TEXT"), ("product_id", "TEXT"), ("provider_id", "TEXT"),
        ("units_on_hand_end", "INTEGER"), ("units_received", "INTEGER"),
        ("stockout_days", "INTEGER"), ("days_of_cover", "REAL"),
        ("sell_through_pct", "REAL"),
    ],
    "returns": [
        ("month", "TEXT"), ("provider_id", "TEXT"), ("product_line", "TEXT"),
        ("reason_code", "TEXT"), ("units", "INTEGER"),
    ],
    "provider_deliveries": [
        ("month", "TEXT"), ("provider_id", "TEXT"), ("provider_name", "TEXT"),
        ("shipments_expected", "INTEGER"), ("shipments_on_time", "INTEGER"),
        ("shipments_late", "INTEGER"), ("otif_pct", "REAL"),
        ("avg_delay_days", "REAL"), ("asn_error_count", "INTEGER"),
        ("quality_reject_pct", "REAL"),
    ],
    "reviews_monthly": [
        ("month", "TEXT"), ("product_id", "TEXT"), ("provider_id", "TEXT"),
        ("review_count", "INTEGER"), ("avg_rating", "REAL"),
    ],
}

VIEWS = """
CREATE VIEW v_sales AS
SELECT s.month, s.product_id, s.provider_id, pv.provider_name, pv.segment, pv.tier,
       pv.account_manager, pv.contract_renewal_date, pv.commission_pct,
       p.product_name, p.product_line, p.item_type, p.gender, p.color,
       p.list_price_eur, p.discontinued_month,
       s.units_sold, s.units_returned, s.orders, s.page_views, s.add_to_cart,
       s.gross_revenue_eur, s.discount_eur, s.net_revenue_eur,
       (s.units_sold - s.units_returned) AS kept_units,
       ROUND(s.net_revenue_eur * (s.units_sold - s.units_returned)
             / NULLIF(s.units_sold, 0), 2) AS kept_revenue_eur,
       ROUND(s.net_revenue_eur * (s.units_sold - s.units_returned)
             / NULLIF(s.units_sold, 0) * pv.commission_pct, 2) AS commission_eur,
       ROUND(s.units_returned * RHC, 2) AS return_cost_eur,
       ROUND(s.net_revenue_eur * (s.units_sold - s.units_returned)
             / NULLIF(s.units_sold, 0) * pv.commission_pct
             - s.units_returned * RHC, 2) AS contribution_eur,
       ROUND(100.0 * s.units_returned / NULLIF(s.units_sold, 0), 2) AS return_rate_pct,
       ROUND(100.0 * s.orders / NULLIF(s.page_views, 0), 2) AS conversion_pct
FROM sales_monthly s
JOIN products p ON p.product_id = s.product_id
JOIN providers pv ON pv.provider_id = s.provider_id;

CREATE VIEW v_provider_month AS
SELECT v.month, v.provider_id, v.provider_name, v.segment, v.tier,
       COUNT(DISTINCT v.product_id) AS active_skus,
       SUM(v.units_sold) AS units_sold,
       SUM(v.units_returned) AS units_returned,
       ROUND(100.0 * SUM(v.units_returned) / NULLIF(SUM(v.units_sold), 0), 2) AS return_rate_pct,
       ROUND(SUM(v.net_revenue_eur), 2) AS net_revenue_eur,
       ROUND(SUM(v.kept_revenue_eur), 2) AS kept_revenue_eur,
       ROUND(SUM(v.commission_eur), 2) AS commission_eur,
       ROUND(SUM(v.return_cost_eur), 2) AS return_cost_eur,
       ROUND(SUM(v.contribution_eur), 2) AS contribution_eur,
       ROUND(100.0 * SUM(v.contribution_eur) / NULLIF(SUM(v.kept_revenue_eur), 0), 2)
           AS contribution_margin_pct,
       d.otif_pct, d.avg_delay_days, d.quality_reject_pct, d.shipments_late,
       (SELECT ROUND(SUM(r.review_count * r.avg_rating) / NULLIF(SUM(r.review_count), 0), 2)
        FROM reviews_monthly r
        WHERE r.provider_id = v.provider_id AND r.month = v.month) AS avg_rating,
       (SELECT SUM(i.stockout_days) FROM inventory_monthly i
        WHERE i.provider_id = v.provider_id AND i.month = v.month) AS stockout_days,
       (SELECT ROUND(AVG(i.days_of_cover), 1) FROM inventory_monthly i
        WHERE i.provider_id = v.provider_id AND i.month = v.month) AS avg_days_of_cover
FROM v_sales v
LEFT JOIN provider_deliveries d
       ON d.provider_id = v.provider_id AND d.month = v.month
GROUP BY v.month, v.provider_id;

CREATE VIEW v_product_month AS
SELECT v.*, i.units_on_hand_end, i.units_received, i.stockout_days,
       i.days_of_cover, i.sell_through_pct,
       r.review_count, r.avg_rating
FROM v_sales v
LEFT JOIN inventory_monthly i
       ON i.product_id = v.product_id AND i.month = v.month
LEFT JOIN reviews_monthly r
       ON r.product_id = v.product_id AND r.month = v.month;
""".replace("RHC", str(RETURN_HANDLING_COST_EUR))


def build_db():
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    for table, cols in SCHEMA.items():
        path = os.path.join(DATA, table + ".csv")
        if not os.path.exists(path):
            sys.exit("missing data file: %s (run scripts/generate_data.py)" % path)
        cur.execute("CREATE TABLE %s (%s)" %
                    (table, ", ".join("%s %s" % c for c in cols)))
        names = [c[0] for c in cols]
        types = {c[0]: c[1] for c in cols}
        with open(path, newline="") as fh:
            rows = []
            for rec in csv.DictReader(fh):
                row = []
                for n in names:
                    val = rec.get(n, "")
                    if val == "" or val is None:
                        row.append(None)
                    elif types[n] == "INTEGER":
                        row.append(int(float(val)))
                    elif types[n] == "REAL":
                        row.append(float(val))
                    else:
                        row.append(val)
                rows.append(row)
        cur.executemany("INSERT INTO %s VALUES (%s)" %
                        (table, ", ".join("?" * len(names))), rows)
        if "month" in names:
            cur.execute("CREATE INDEX ix_%s_month ON %s(month)" % (table, table))
        if "product_id" in names:
            cur.execute("CREATE INDEX ix_%s_prod ON %s(product_id)" % (table, table))
        if "provider_id" in names:
            cur.execute("CREATE INDEX ix_%s_prov ON %s(provider_id)" % (table, table))
    cur.executescript(VIEWS)
    con.commit()
    return con


def render(rows, as_csv=False):
    if not rows:
        print("(no rows)")
        return
    cols = list(rows[0].keys())
    if as_csv:
        w = csv.writer(sys.stdout)
        w.writerow(cols)
        for r in rows:
            w.writerow([r[c] for c in cols])
        return

    def fmt(v):
        if v is None:
            return ""
        if isinstance(v, float):
            return "%.2f" % v
        return str(v)

    widths = [max(len(c), max(len(fmt(r[c])) for r in rows)) for c in cols]
    print("  ".join(c.ljust(w) for c, w in zip(cols, widths)))
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print("  ".join(fmt(r[c]).ljust(w) for c, w in zip(cols, widths)))
    print("\n(%d rows)" % len(rows))


def resolve_provider(con, token):
    rows = con.execute(
        "SELECT provider_id, provider_name FROM providers "
        "WHERE provider_id = ? OR LOWER(provider_name) LIKE LOWER(?)",
        (token, "%" + token + "%")).fetchall()
    if not rows:
        sys.exit("no provider matches %r" % token)
    if len(rows) > 1:
        sys.exit("ambiguous provider %r: %s" %
                 (token, ", ".join(r["provider_name"] for r in rows)))
    return rows[0]["provider_id"], rows[0]["provider_name"]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--csv", action="store_true",
                        help="emit CSV instead of an aligned table")
    common.add_argument("--limit", type=int, default=200, help="max rows (default 200)")
    ap.add_argument("--csv", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--limit", type=int, default=200, help=argparse.SUPPRESS)
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="COMMAND")

    sub.add_parser("schema", parents=[common], help="list tables, views and columns")
    p = sub.add_parser("sql", parents=[common], help="run arbitrary read-only SQL")
    p.add_argument("query")
    p = sub.add_parser("providers", parents=[common], help="provider league table for one month")
    p.add_argument("--month", required=True)
    p = sub.add_parser("provider", parents=[common], help="month-by-month history for one provider")
    p.add_argument("name")
    p.add_argument("--from", dest="mfrom", default="0000-00")
    p.add_argument("--to", dest="mto", default="9999-99")
    p = sub.add_parser("month", parents=[common], help="marketplace totals and providers for one month")
    p.add_argument("month")
    p = sub.add_parser("returns", parents=[common], help="return reasons for one provider")
    p.add_argument("name")
    p.add_argument("--from", dest="mfrom", default="0000-00")
    p.add_argument("--to", dest="mto", default="9999-99")
    p = sub.add_parser("products", parents=[common], help="products for one provider, ranked")
    p.add_argument("name")
    p.add_argument("--month", default=None)
    p.add_argument("--from", dest="mfrom", default="0000-00")
    p.add_argument("--to", dest="mto", default="9999-99")
    p.add_argument("--order", default="contribution_eur DESC")

    a = ap.parse_args()
    con = build_db()

    if a.cmd == "schema":
        rows = con.execute(
            "SELECT type, name FROM sqlite_master "
            "WHERE type IN ('table','view') ORDER BY type DESC, name").fetchall()
        for r in rows:
            cols = [c[1] for c in con.execute("PRAGMA table_info(%s)" % r["name"])]
            n = con.execute("SELECT COUNT(*) FROM %s" % r["name"]).fetchone()[0]
            print("%-5s %-22s %6d rows" % (r["type"], r["name"], n))
            print("      %s\n" % ", ".join(cols))
        mm = con.execute("SELECT MIN(month), MAX(month) FROM sales_monthly").fetchone()
        print("coverage: %s .. %s" % (mm[0], mm[1]))
        print("return handling cost assumption: EUR %.2f per returned unit"
              % RETURN_HANDLING_COST_EUR)
        return

    if a.cmd == "sql":
        q = a.query.strip().rstrip(";")
        if not q.lower().startswith(("select", "with")):
            sys.exit("only SELECT / WITH queries are allowed")
        if "limit" not in q.lower():
            q = q + " LIMIT %d" % a.limit
        render(con.execute(q).fetchall(), a.csv)
        return

    if a.cmd == "providers":
        rows = con.execute(
            "SELECT provider_name, tier, active_skus, units_sold, net_revenue_eur, "
            "commission_eur, return_rate_pct, return_cost_eur, contribution_eur, "
            "contribution_margin_pct, otif_pct, avg_rating, stockout_days, "
            "avg_days_of_cover FROM v_provider_month WHERE month = ? "
            "ORDER BY contribution_eur DESC", (a.month,)).fetchall()
        render(rows, a.csv)
        return

    if a.cmd == "provider":
        pid, pname = resolve_provider(con, a.name)
        print("== %s (%s) ==\n" % (pname, pid))
        rows = con.execute(
            "SELECT month, active_skus, units_sold, units_returned, return_rate_pct, "
            "net_revenue_eur, commission_eur, return_cost_eur, contribution_eur, "
            "contribution_margin_pct, otif_pct, avg_delay_days, quality_reject_pct, "
            "avg_rating, stockout_days, avg_days_of_cover FROM v_provider_month "
            "WHERE provider_id = ? AND month BETWEEN ? AND ? ORDER BY month",
            (pid, a.mfrom, a.mto)).fetchall()
        render(rows, a.csv)
        return

    if a.cmd == "month":
        print("== marketplace totals %s ==\n" % a.month)
        render(con.execute(
            "SELECT SUM(units_sold) units_sold, SUM(units_returned) units_returned, "
            "ROUND(100.0*SUM(units_returned)/SUM(units_sold),2) return_rate_pct, "
            "ROUND(SUM(net_revenue_eur),2) net_revenue_eur, "
            "ROUND(SUM(commission_eur),2) commission_eur, "
            "ROUND(SUM(return_cost_eur),2) return_cost_eur, "
            "ROUND(SUM(contribution_eur),2) contribution_eur "
            "FROM v_sales WHERE month = ?", (a.month,)).fetchall(), a.csv)
        print("\n== providers by contribution ==\n")
        render(con.execute(
            "SELECT provider_name, units_sold, net_revenue_eur, contribution_eur, "
            "return_rate_pct, otif_pct, avg_rating FROM v_provider_month "
            "WHERE month = ? ORDER BY contribution_eur DESC", (a.month,)).fetchall(), a.csv)
        return

    if a.cmd == "returns":
        pid, pname = resolve_provider(con, a.name)
        print("== %s return reasons %s .. %s ==\n" % (pname, a.mfrom, a.mto))
        render(con.execute(
            "SELECT reason_code, SUM(units) units, "
            "ROUND(100.0*SUM(units)/(SELECT SUM(units) FROM returns "
            "  WHERE provider_id = ? AND month BETWEEN ? AND ?),1) share_pct "
            "FROM returns WHERE provider_id = ? AND month BETWEEN ? AND ? "
            "GROUP BY reason_code ORDER BY units DESC",
            (pid, a.mfrom, a.mto, pid, a.mfrom, a.mto)).fetchall(), a.csv)
        print("\n== by product line ==\n")
        render(con.execute(
            "SELECT product_line, reason_code, SUM(units) units, "
            "ROUND(100.0*SUM(units)/SUM(SUM(units)) OVER (PARTITION BY product_line),1) "
            "  share_of_line_pct "
            "FROM returns WHERE provider_id = ? AND month BETWEEN ? AND ? "
            "GROUP BY product_line, reason_code ORDER BY product_line, units DESC",
            (pid, a.mfrom, a.mto)).fetchall(), a.csv)
        return

    if a.cmd == "products":
        pid, pname = resolve_provider(con, a.name)
        mfrom, mto = (a.month, a.month) if a.month else (a.mfrom, a.mto)
        print("== %s products %s .. %s ==\n" % (pname, mfrom, mto))
        render(con.execute(
            "SELECT product_name, product_line, list_price_eur, "
            "SUM(units_sold) units_sold, SUM(units_returned) units_returned, "
            "ROUND(100.0*SUM(units_returned)/NULLIF(SUM(units_sold),0),2) return_rate_pct, "
            "ROUND(SUM(net_revenue_eur),2) net_revenue_eur, "
            "ROUND(SUM(contribution_eur),2) contribution_eur "
            "FROM v_sales WHERE provider_id = ? AND month BETWEEN ? AND ? "
            "GROUP BY product_id ORDER BY %s LIMIT %d"
            % (a.order, a.limit), (pid, mfrom, mto)).fetchall(), a.csv)
        return


if __name__ == "__main__":
    main()

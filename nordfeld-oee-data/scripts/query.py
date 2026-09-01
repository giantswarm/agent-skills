#!/usr/bin/env python3
"""
Nordfeld Automotive OEE query tool.

Loads the MES extracts into an in-memory SQLite database with prepared views
that encode the canonical OEE formulas, then runs SQL against it. Standard
library only, no dependencies.

    python3 scripts/query.py schema
    python3 scripts/query.py shift 2026-08-28
    python3 scripts/query.py machine PRESS-01 --from 2026-08-01 --to 2026-08-31
    python3 scripts/query.py losses PRESS-02 --from 2026-08-01 --to 2026-08-31
    python3 scripts/query.py plant BRM --from 2026-08-01 --to 2026-08-31
    python3 scripts/query.py sql "SELECT ... FROM v_shift_oee ..."

Add --csv for machine-readable output, --limit N to cap rows.
"""
import argparse
import csv
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))

SCHEMA = {
    "plants": [
        ("plant_id", "TEXT"), ("plant_name", "TEXT"), ("country", "TEXT"),
        ("focus", "TEXT"), ("opened_year", "INTEGER"), ("shift_pattern", "TEXT"),
        ("saturday_shifts", "TEXT"),
        ("changeover_excluded_from_planned_time", "INTEGER"),
    ],
    "machines": [
        ("machine_id", "TEXT"), ("plant_id", "TEXT"), ("machine_name", "TEXT"),
        ("asset_type", "TEXT"), ("process_step", "TEXT"),
        ("ideal_cycle_time_sec", "REAL"), ("installed_year", "INTEGER"),
        ("is_bottleneck", "INTEGER"), ("target_oee", "REAL"),
    ],
    "reason_codes": [
        ("reason_code", "TEXT"), ("reason_description", "TEXT"),
        ("big_loss", "TEXT"), ("oee_factor", "TEXT"),
        ("is_planned", "INTEGER"), ("counts_as_stop_time", "INTEGER"),
    ],
    "defect_codes": [
        ("defect_code", "TEXT"), ("defect_description", "TEXT"), ("big_loss", "TEXT"),
    ],
    "shifts": [
        ("shift_date", "TEXT"), ("shift", "TEXT"), ("machine_id", "TEXT"),
        ("plant_id", "TEXT"), ("planned_production_time_min", "REAL"),
        ("stop_time_min", "REAL"), ("run_time_min", "REAL"),
        ("changeover_min_excluded_from_planned", "REAL"),
        ("ideal_cycle_time_sec", "REAL"), ("total_count", "INTEGER"),
        ("good_count", "INTEGER"), ("scheduled_units", "INTEGER"),
    ],
    "downtime_events": [
        ("event_id", "TEXT"), ("event_date", "TEXT"), ("shift", "TEXT"),
        ("machine_id", "TEXT"), ("plant_id", "TEXT"), ("reason_code", "TEXT"),
        ("duration_min", "REAL"),
    ],
    "quality_defects": [
        ("iso_week", "TEXT"), ("machine_id", "TEXT"), ("plant_id", "TEXT"),
        ("defect_code", "TEXT"), ("units", "INTEGER"),
    ],
}

# The canonical OEE formulas live here and nowhere else, so every answer in
# every conversation derives them identically.
#   Availability = Run Time / Planned Production Time
#   Performance  = (Ideal Cycle Time x Total Count) / Run Time
#   Quality      = Good Count / Total Count
#   OEE          = Availability x Performance x Quality
VIEWS = """
CREATE VIEW v_shift_oee AS
SELECT s.shift_date, s.shift, s.machine_id, s.plant_id,
       m.machine_name, m.asset_type, m.process_step, m.is_bottleneck,
       m.target_oee, p.plant_name,
       s.planned_production_time_min, s.stop_time_min, s.run_time_min,
       s.changeover_min_excluded_from_planned,
       s.ideal_cycle_time_sec, s.total_count, s.good_count, s.scheduled_units,
       ROUND(100.0 * s.run_time_min / NULLIF(s.planned_production_time_min, 0), 2)
           AS availability_pct,
       ROUND(100.0 * (s.ideal_cycle_time_sec * s.total_count / 60.0)
             / NULLIF(s.run_time_min, 0), 2) AS performance_pct,
       ROUND(100.0 * s.good_count / NULLIF(s.total_count, 0), 2) AS quality_pct,
       ROUND(100.0
             * (s.run_time_min / NULLIF(s.planned_production_time_min, 0))
             * ((s.ideal_cycle_time_sec * s.total_count / 60.0)
                / NULLIF(s.run_time_min, 0))
             * (1.0 * s.good_count / NULLIF(s.total_count, 0)), 2) AS oee_pct,
       ROUND(100.0 * s.good_count / NULLIF(s.scheduled_units, 0), 2)
           AS schedule_attainment_pct,
       -- Availability restated on the orthodox basis, with excluded changeover
       -- minutes pushed back into Planned Production Time. Use this whenever
       -- comparing Valdera against the other plants.
       ROUND(100.0 * s.run_time_min
             / NULLIF(s.planned_production_time_min
                      + s.changeover_min_excluded_from_planned, 0), 2)
           AS availability_common_basis_pct
FROM shifts s
JOIN machines m ON m.machine_id = s.machine_id
JOIN plants p ON p.plant_id = s.plant_id;

-- Aggregation must rebuild OEE from summed inputs, never average the shift
-- percentages: a mean of ratios is not the ratio of the totals.
CREATE VIEW v_machine_period AS
SELECT machine_id, plant_id, machine_name, asset_type, is_bottleneck, target_oee,
       COUNT(*) AS shifts,
       ROUND(SUM(planned_production_time_min), 1) AS planned_min,
       ROUND(SUM(stop_time_min), 1) AS stop_min,
       ROUND(SUM(run_time_min), 1) AS run_min,
       SUM(total_count) AS total_count, SUM(good_count) AS good_count,
       SUM(scheduled_units) AS scheduled_units,
       ROUND(100.0 * SUM(run_time_min) / NULLIF(SUM(planned_production_time_min), 0), 2)
           AS availability_pct,
       ROUND(100.0 * SUM(ideal_cycle_time_sec * total_count / 60.0)
             / NULLIF(SUM(run_time_min), 0), 2) AS performance_pct,
       ROUND(100.0 * SUM(good_count) / NULLIF(SUM(total_count), 0), 2) AS quality_pct,
       ROUND(100.0
             * (SUM(run_time_min) / NULLIF(SUM(planned_production_time_min), 0))
             * (SUM(ideal_cycle_time_sec * total_count / 60.0)
                / NULLIF(SUM(run_time_min), 0))
             * (1.0 * SUM(good_count) / NULLIF(SUM(total_count), 0)), 2) AS oee_pct,
       ROUND(100.0 * SUM(good_count) / NULLIF(SUM(scheduled_units), 0), 2)
           AS schedule_attainment_pct,
       ROUND(100.0 * SUM(run_time_min)
             / NULLIF(SUM(planned_production_time_min
                          + changeover_min_excluded_from_planned), 0), 2)
           AS availability_common_basis_pct
FROM v_shift_oee GROUP BY machine_id;

-- Downtime with its Six Big Losses classification attached. counts_as_stop_time
-- = 0 marks micro-stops, which never appear as downtime in an Availability
-- calculation and instead show up as Performance loss.
CREATE VIEW v_events AS
SELECT e.event_id, e.event_date, e.shift, e.machine_id, e.plant_id,
       m.machine_name, m.is_bottleneck, e.reason_code, e.duration_min,
       r.reason_description, r.big_loss, r.oee_factor,
       r.is_planned, r.counts_as_stop_time
FROM downtime_events e
JOIN reason_codes r ON r.reason_code = e.reason_code
JOIN machines m ON m.machine_id = e.machine_id;

CREATE VIEW v_defects AS
SELECT q.iso_week, q.machine_id, q.plant_id, q.defect_code, q.units,
       d.defect_description, d.big_loss, m.machine_name
FROM quality_defects q
JOIN defect_codes d ON d.defect_code = q.defect_code
JOIN machines m ON m.machine_id = q.machine_id;
"""


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
        rows = []
        with open(path, newline="") as fh:
            for rec in csv.DictReader(fh):
                row = []
                for n in names:
                    v = rec.get(n, "")
                    if v == "" or v is None:
                        row.append(None)
                    elif types[n] == "INTEGER":
                        row.append(int(float(v)))
                    elif types[n] == "REAL":
                        row.append(float(v))
                    else:
                        row.append(v)
                rows.append(row)
        cur.executemany("INSERT INTO %s VALUES (%s)" %
                        (table, ", ".join("?" * len(names))), rows)
        for c in ("machine_id", "plant_id", "shift_date", "event_date", "iso_week"):
            if c in names:
                cur.execute("CREATE INDEX ix_%s_%s ON %s(%s)" % (table, c, table, c))
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


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--csv", action="store_true", help="emit CSV")
    common.add_argument("--limit", type=int, default=200, help="max rows (default 200)")
    ap.add_argument("--csv", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--limit", type=int, default=200, help=argparse.SUPPRESS)
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="COMMAND")

    sub.add_parser("schema", parents=[common], help="tables, views, coverage")
    p = sub.add_parser("sql", parents=[common], help="read-only SQL")
    p.add_argument("query")
    p = sub.add_parser("shift", parents=[common],
                       help="every machine on one date, worst OEE first")
    p.add_argument("date")
    p.add_argument("--shift", default=None, help="A, B or C")
    p = sub.add_parser("machine", parents=[common], help="one machine, shift by shift")
    p.add_argument("machine_id")
    p.add_argument("--from", dest="dfrom", default="0000-00-00")
    p.add_argument("--to", dest="dto", default="9999-99-99")
    p = sub.add_parser("losses", parents=[common],
                       help="Six Big Losses Pareto for one machine")
    p.add_argument("machine_id")
    p.add_argument("--from", dest="dfrom", default="0000-00-00")
    p.add_argument("--to", dest="dto", default="9999-99-99")
    p = sub.add_parser("plant", parents=[common], help="machines in one plant, ranked")
    p.add_argument("plant_id")
    p.add_argument("--from", dest="dfrom", default="0000-00-00")
    p.add_argument("--to", dest="dto", default="9999-99-99")

    a = ap.parse_args()
    con = build_db()

    if a.cmd == "schema":
        for r in con.execute("SELECT type, name FROM sqlite_master "
                             "WHERE type IN ('table','view') ORDER BY type DESC, name"):
            cols = [c[1] for c in con.execute("PRAGMA table_info(%s)" % r["name"])]
            n = con.execute("SELECT COUNT(*) FROM %s" % r["name"]).fetchone()[0]
            print("%-5s %-20s %6d rows" % (r["type"], r["name"], n))
            print("      %s\n" % ", ".join(cols))
        sc = con.execute("SELECT MIN(shift_date), MAX(shift_date) FROM shifts").fetchone()
        ec = con.execute("SELECT MIN(event_date), MAX(event_date) "
                         "FROM downtime_events").fetchone()
        print("shift rollups: %s .. %s" % (sc[0], sc[1]))
        print("event detail:  %s .. %s  (90-day MES retention; no event detail "
              "before this)" % (ec[0], ec[1]))
        return

    if a.cmd == "sql":
        q = a.query.strip().rstrip(";")
        if not q.lower().startswith(("select", "with")):
            sys.exit("only SELECT / WITH queries are allowed")
        if "limit" not in q.lower():
            q += " LIMIT %d" % a.limit
        render(con.execute(q).fetchall(), a.csv)
        return

    if a.cmd == "shift":
        where = "shift_date = ?" + (" AND shift = ?" if a.shift else "")
        args = (a.date, a.shift) if a.shift else (a.date,)
        render(con.execute(
            "SELECT shift, machine_id, machine_name, is_bottleneck, "
            "oee_pct, availability_pct, performance_pct, quality_pct, "
            "target_oee, stop_time_min, total_count, good_count, "
            "schedule_attainment_pct FROM v_shift_oee WHERE " + where +
            " ORDER BY oee_pct ASC", args).fetchall(), a.csv)
        return

    if a.cmd == "machine":
        render(con.execute(
            "SELECT shift_date, shift, oee_pct, availability_pct, performance_pct, "
            "quality_pct, planned_production_time_min, stop_time_min, run_time_min, "
            "total_count, good_count, schedule_attainment_pct "
            "FROM v_shift_oee WHERE machine_id = ? AND shift_date BETWEEN ? AND ? "
            "ORDER BY shift_date, shift",
            (a.machine_id, a.dfrom, a.dto)).fetchall(), a.csv)
        return

    if a.cmd == "losses":
        print("== stop time by big loss (Availability) ==\n")
        render(con.execute(
            "SELECT big_loss, reason_code, reason_description, COUNT(*) events, "
            "ROUND(SUM(duration_min),1) total_min, "
            "ROUND(AVG(duration_min),1) mean_min "
            "FROM v_events WHERE machine_id = ? AND event_date BETWEEN ? AND ? "
            "AND counts_as_stop_time = 1 GROUP BY reason_code "
            "ORDER BY total_min DESC", (a.machine_id, a.dfrom, a.dto)).fetchall(), a.csv)
        print("\n== micro-stops (Performance loss, absent from downtime) ==\n")
        render(con.execute(
            "SELECT reason_code, reason_description, COUNT(*) events, "
            "ROUND(SUM(duration_min),1) total_min, ROUND(AVG(duration_min),1) mean_min "
            "FROM v_events WHERE machine_id = ? AND event_date BETWEEN ? AND ? "
            "AND counts_as_stop_time = 0 GROUP BY reason_code "
            "ORDER BY total_min DESC", (a.machine_id, a.dfrom, a.dto)).fetchall(), a.csv)
        print("\n== defects by type (Quality loss) ==\n")
        render(con.execute(
            "SELECT big_loss, defect_code, defect_description, SUM(units) units "
            "FROM v_defects WHERE machine_id = ? GROUP BY defect_code "
            "ORDER BY units DESC", (a.machine_id,)).fetchall(), a.csv)
        return

    if a.cmd == "plant":
        # Rebuilt from summed inputs, not averaged from shift percentages.
        render(con.execute(
            "SELECT machine_id, machine_name, asset_type, is_bottleneck, "
            "COUNT(*) shifts, "
            "ROUND(100.0*SUM(run_time_min)"
            "  /NULLIF(SUM(planned_production_time_min),0),2) availability_pct, "
            "ROUND(100.0*SUM(ideal_cycle_time_sec*total_count/60.0)"
            "  /NULLIF(SUM(run_time_min),0),2) performance_pct, "
            "ROUND(100.0*SUM(good_count)/NULLIF(SUM(total_count),0),2) quality_pct, "
            "ROUND(100.0"
            "  *(SUM(run_time_min)/NULLIF(SUM(planned_production_time_min),0))"
            "  *(SUM(ideal_cycle_time_sec*total_count/60.0)"
            "    /NULLIF(SUM(run_time_min),0))"
            "  *(1.0*SUM(good_count)/NULLIF(SUM(total_count),0)),2) oee_pct, "
            "target_oee, "
            "ROUND(100.0*SUM(run_time_min)"
            "  /NULLIF(SUM(planned_production_time_min"
            "    +changeover_min_excluded_from_planned),0),2) avail_common_pct, "
            "ROUND(100.0*SUM(good_count)/NULLIF(SUM(scheduled_units),0),2) "
            "  schedule_attainment_pct, "
            "ROUND(SUM(stop_time_min),0) stop_min "
            "FROM v_shift_oee WHERE plant_id = ? AND shift_date BETWEEN ? AND ? "
            "GROUP BY machine_id ORDER BY oee_pct ASC",
            (a.plant_id, a.dfrom, a.dto)).fetchall(), a.csv)
        return


if __name__ == "__main__":
    main()

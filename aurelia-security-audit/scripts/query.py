#!/usr/bin/env python3
"""
Aurelia Bank security policy and ruling lookup.

Loads the policy register and the ruling register into in-memory SQLite.
Standard library only.

    python3 scripts/query.py policy ASP-NET-02
    python3 scripts/query.py search "network policy egress"
    python3 scripts/query.py domain NETWORK
    python3 scripts/query.py rulings --policy ASP-SUP-02
    python3 scripts/query.py expiring --within-days 90
    python3 scripts/query.py recurring
    python3 scripts/query.py blocking
    python3 scripts/query.py sql "SELECT ... FROM policies ..."

Add --csv for machine-readable output.
"""
import argparse
import csv
import os
import sqlite3
import sys
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))

# The audit is dated against this. Kept explicit so exception-expiry arithmetic
# is reproducible rather than drifting with the wall clock.
TODAY = date(2026, 9, 1)

SCHEMA = {
    "policies": ["policy_id", "domain", "title", "requirement", "severity_floor", "blocking",
                 "iso_27001_2022_controls", "dora_articles", "other_references", "owner",
                 "last_reviewed"],
    "rulings": ["ruling_id", "decided_on", "issue_ref", "policy_id", "decision",
                "severity_at_time", "expires_on", "rationale", "decided_by", "team"],
    "backlog": ["issue_ref", "title", "team", "reporter", "status", "priority",
                "target", "last_updated", "audit_status", "related_ruling", "body_file"],
}


def build_db():
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    for table, cols in SCHEMA.items():
        path = os.path.join(DATA, table + ".csv")
        if not os.path.exists(path):
            sys.exit("missing %s (run scripts/build_corpus.py)" % path)
        cur.execute("CREATE TABLE %s (%s)" % (table, ", ".join("%s TEXT" % c for c in cols)))
        with open(path, newline="") as fh:
            rows = [[rec.get(c) or None for c in cols] for rec in csv.DictReader(fh)]
        cur.executemany("INSERT INTO %s VALUES (%s)" %
                        (table, ", ".join("?" * len(cols))), rows)
    # Live = granted, not yet expired. An expired acceptance is not cover.
    cur.execute("""
        CREATE VIEW v_rulings AS
        SELECT r.*, p.title AS policy_title, p.domain,
               CASE
                 WHEN r.decision IN ('REJECTED','REMEDIATED') THEN 'n/a'
                 WHEN r.expires_on IS NULL OR r.expires_on = '' THEN 'open-ended'
                 WHEN r.expires_on < '%s' THEN 'EXPIRED'
                 ELSE 'live'
               END AS cover_status,
               CASE WHEN r.expires_on IS NOT NULL AND r.expires_on != ''
                    THEN CAST(julianday(r.expires_on) - julianday('%s') AS INTEGER)
               END AS days_to_expiry
        FROM rulings r LEFT JOIN policies p ON p.policy_id = r.policy_id
    """ % (TODAY.isoformat(), TODAY.isoformat()))
    con.commit()
    return con


def render(rows, as_csv=False, wrap=None):
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
    if wrap:
        # Record-per-block layout: policy text is prose and does not fit columns.
        for r in rows:
            for c in cols:
                v = r[c]
                if v in (None, ""):
                    continue
                label = c.replace("_", " ")
                text = str(v)
                if len(text) > wrap:
                    words, line, out = text.split(), "", []
                    for wd in words:
                        if len(line) + len(wd) + 1 > wrap:
                            out.append(line)
                            line = wd
                        else:
                            line = (line + " " + wd).strip()
                    out.append(line)
                    print("%-26s %s" % (label + ":", out[0]))
                    for cont in out[1:]:
                        print("%-26s %s" % ("", cont))
                else:
                    print("%-26s %s" % (label + ":", text))
            print("-" * 78)
        print("(%d rows)" % len(rows))
        return
    def fmt(v):
        return "" if v is None else str(v)
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
    common.add_argument("--csv", action="store_true")
    common.add_argument("--limit", type=int, default=100)
    ap.add_argument("--csv", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--limit", type=int, default=100, help=argparse.SUPPRESS)
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="COMMAND")

    p = sub.add_parser("policy", parents=[common], help="one policy in full, with mappings")
    p.add_argument("policy_id", nargs="+")
    p = sub.add_parser("search", parents=[common], help="keyword search across policy text")
    p.add_argument("terms", nargs="+")
    p = sub.add_parser("domain", parents=[common], help="all policies in a domain")
    p.add_argument("domain")
    p = sub.add_parser("rulings", parents=[common], help="past board decisions")
    p.add_argument("--policy", default=None)
    p.add_argument("--decision", default=None)
    sub.add_parser("blocking", parents=[common], help="policies that block a merge")
    p = sub.add_parser("expiring", parents=[common], help="cover that lapses soon or has lapsed")
    p.add_argument("--within-days", type=int, default=90)
    sub.add_parser("recurring", parents=[common],
                   help="policies with repeat findings across teams")
    sub.add_parser("domains", parents=[common], help="domain list with counts")
    p = sub.add_parser("backlog", parents=[common], help="change backlog")
    p.add_argument("--team", default=None)
    p.add_argument("--reporter", default=None)
    p.add_argument("--status", default=None)
    p.add_argument("--unaudited", action="store_true", help="only items not yet audited")
    p = sub.add_parser("issue", parents=[common],
                       help="one backlog item, with where its plan text lives")
    p.add_argument("issue_ref")
    sub.add_parser("teams", parents=[common], help="teams with open change counts")
    p = sub.add_parser("sql", parents=[common], help="read-only SQL")
    p.add_argument("query")

    a = ap.parse_args()
    con = build_db()

    if a.cmd == "policy":
        ids = [x.upper() for x in a.policy_id]
        q = "SELECT * FROM policies WHERE policy_id IN (%s)" % ",".join("?" * len(ids))
        render(con.execute(q, ids).fetchall(), a.csv, wrap=None if a.csv else 50)
        return

    if a.cmd == "search":
        like = " ".join(a.terms)
        terms = [t for t in like.replace(",", " ").split() if len(t) > 2]
        if not terms:
            sys.exit("give at least one term of 3+ characters")
        where = " OR ".join(
            ["(LOWER(title) LIKE ? OR LOWER(requirement) LIKE ? OR LOWER(domain) LIKE ?)"] * len(terms))
        args = []
        for t in terms:
            args += ["%" + t.lower() + "%"] * 3
        rows = con.execute(
            "SELECT policy_id, domain, title, severity_floor, blocking, "
            "iso_27001_2022_controls, dora_articles FROM policies WHERE " + where +
            " ORDER BY policy_id LIMIT %d" % a.limit, args).fetchall()
        render(rows, a.csv)
        return

    if a.cmd == "domain":
        render(con.execute(
            "SELECT * FROM policies WHERE UPPER(domain) = ? ORDER BY policy_id",
            (a.domain.upper(),)).fetchall(), a.csv, wrap=None if a.csv else 50)
        return

    if a.cmd == "rulings":
        clauses, args = [], []
        if a.policy:
            clauses.append("policy_id = ?")
            args.append(a.policy.upper())
        if a.decision:
            clauses.append("decision = ?")
            args.append(a.decision.upper())
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        render(con.execute(
            "SELECT ruling_id, decided_on, issue_ref, policy_id, decision, cover_status, "
            "expires_on, days_to_expiry, team, rationale FROM v_rulings" + where +
            " ORDER BY decided_on DESC", args).fetchall(), a.csv, wrap=None if a.csv else 52)
        return

    if a.cmd == "blocking":
        render(con.execute(
            "SELECT policy_id, domain, title, severity_floor FROM policies "
            "WHERE blocking = 'yes' ORDER BY domain, policy_id").fetchall(), a.csv)
        return

    if a.cmd == "expiring":
        render(con.execute(
            "SELECT ruling_id, policy_id, policy_title, decision, cover_status, expires_on, "
            "days_to_expiry, team, issue_ref FROM v_rulings "
            "WHERE expires_on IS NOT NULL AND expires_on != '' "
            "AND CAST(days_to_expiry AS INTEGER) <= ? "
            "ORDER BY days_to_expiry", (a.within_days,)).fetchall(), a.csv)
        return

    if a.cmd == "recurring":
        render(con.execute(
            "SELECT policy_id, COUNT(*) rulings, COUNT(DISTINCT team) teams, "
            "GROUP_CONCAT(ruling_id, ', ') ruling_ids, "
            "GROUP_CONCAT(DISTINCT team) affected_teams "
            "FROM rulings GROUP BY policy_id HAVING COUNT(*) > 1 "
            "ORDER BY rulings DESC").fetchall(), a.csv)
        return

    if a.cmd == "domains":
        render(con.execute(
            "SELECT domain, COUNT(*) policies, "
            "SUM(CASE WHEN blocking='yes' THEN 1 ELSE 0 END) blocking "
            "FROM policies GROUP BY domain ORDER BY domain").fetchall(), a.csv)
        return

    if a.cmd == "backlog":
        clauses, args = [], []
        if a.team:
            clauses.append("LOWER(team) LIKE ?")
            args.append("%" + a.team.lower() + "%")
        if a.reporter:
            clauses.append("LOWER(reporter) LIKE ?")
            args.append("%" + a.reporter.lower() + "%")
        if a.status:
            clauses.append("LOWER(status) = ?")
            args.append(a.status.lower())
        if a.unaudited:
            clauses.append("audit_status = 'NOT_AUDITED'")
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        render(con.execute(
            "SELECT issue_ref, title, team, reporter, status, priority, target, "
            "last_updated, audit_status, related_ruling, "
            "CASE WHEN body_file IS NULL OR body_file='' THEN 'no' ELSE 'yes' END "
            "  AS plan_available "
            "FROM backlog" + where + " ORDER BY last_updated DESC", args).fetchall(), a.csv)
        return

    if a.cmd == "issue":
        rows = con.execute("SELECT * FROM backlog WHERE UPPER(issue_ref) = ?",
                           (a.issue_ref.upper(),)).fetchall()
        if not rows:
            sys.exit("no backlog item %r" % a.issue_ref)
        render(rows, a.csv, wrap=None if a.csv else 52)
        bf = rows[0]["body_file"]
        if bf and not a.csv:
            print("plan text: examples/%s  (read it before auditing)" % bf)
        elif not bf and not a.csv:
            print("No written plan is attached to this item.")
        return

    if a.cmd == "teams":
        render(con.execute(
            "SELECT team, COUNT(*) items, "
            "SUM(CASE WHEN status IN ('In progress','In review') THEN 1 ELSE 0 END) open, "
            "SUM(CASE WHEN audit_status='NOT_AUDITED' AND "
            "         status IN ('In progress','In review') THEN 1 ELSE 0 END) unaudited "
            "FROM backlog GROUP BY team ORDER BY team").fetchall(), a.csv)
        return

    if a.cmd == "sql":
        q = a.query.strip().rstrip(";")
        if not q.lower().startswith(("select", "with")):
            sys.exit("only SELECT / WITH queries are allowed")
        if "limit" not in q.lower():
            q += " LIMIT %d" % a.limit
        render(con.execute(q).fetchall(), a.csv)
        return


if __name__ == "__main__":
    main()

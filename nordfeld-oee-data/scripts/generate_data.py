#!/usr/bin/env python3
"""
Generate the Nordfeld Automotive OEE demo dataset (fictional).

Deterministic: same seed always produces the same CSVs. Re-run after editing a
machine profile below to regenerate the whole dataset consistently.

    python3 scripts/generate_data.py

The generator models OEE from its raw inputs rather than writing OEE out
directly, so the canonical formulas reproduce exactly from the CSVs:

    Availability = Run Time / Planned Production Time
    Performance  = (Ideal Cycle Time x Total Count) / Run Time
    Quality      = Good Count / Total Count

Availability-affecting stops (>= 5 min) reduce Run Time. Micro-stops (< 5 min)
and speed loss do NOT reduce Run Time; they reduce Total Count, so they surface
as Performance loss exactly as OEE theory says they should.
"""
import csv
import os
import random
from datetime import date, timedelta

SEED = 20260901
random.seed(SEED)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "data"))
os.makedirs(OUT, exist_ok=True)

# Shift rollups cover 6 months; event-level detail is retained 90 days only,
# mirroring a real MES retention tier (and keeping the event log a sane size).
START = date(2026, 3, 1)
END = date(2026, 8, 31)
EVENT_RETENTION_FROM = date(2026, 6, 3)

SHIFTS = [("A", "06:00"), ("B", "14:00"), ("C", "22:00")]

# ------------------------------------------------------------------- plants
PLANTS = [
    dict(pid="BRM", name="Bramfeld", country="DE", focus="Stamping and forming",
         opened=1974, shifts="A,B,C", sat_shifts="A",
         # Bramfeld books changeovers as stop time, the orthodox treatment.
         changeover_excluded=False),
    dict(pid="STW", name="Steinwald", country="DE", focus="Machining",
         opened=2016, shifts="A,B,C", sat_shifts="A",
         changeover_excluded=False),
    dict(pid="VLD", name="Valdera", country="IT", focus="Assembly and test",
         opened=1998, shifts="A,B", sat_shifts="",
         # Valdera subtracts changeover minutes from Planned Production Time
         # instead of booking them as stop time. Inflates its Availability and
         # makes a naive cross-plant comparison wrong. Deliberate.
         changeover_excluded=True),
]

# ------------------------------------------------------------------ machines
# ict = ideal cycle time in seconds per part.
MACHINES = [
    # --- Bramfeld: stamping and forming
    dict(mid="PRESS-01", pid="BRM", name="630t transfer press", atype="Press",
         step="Blanking", ict=4.2, installed=1998, bottleneck=True, target=0.70,
         # The constraint of the whole Bramfeld flow, and only mid-pack on OEE.
         avail_base=0.68, brk_rate=0.30, chg_per_shift=0.7, chg_min=(38, 62),
         micro_rate=0.9, speed_loss=0.045, scrap=0.019, startup_scrap=0.004),
    dict(mid="PRESS-02", pid="BRM", name="400t press", atype="Press",
         step="Forming", ict=3.1, installed=2004, bottleneck=False, target=0.72,
         # Changeover time is high and worsening: the SMED story.
         avail_base=0.59, brk_rate=0.18, chg_per_shift=1.8, chg_min=(58, 86),
         chg_drift=0.50, filler_codes=["ADJ-TOOL", "BRK-TOOL"],
         micro_rate=0.7, speed_loss=0.035,
         scrap=0.014, startup_scrap=0.006),
    dict(mid="PRESS-03", pid="BRM", name="250t press", atype="Press",
         step="Forming", ict=2.4, installed=2011, bottleneck=False, target=0.75,
         avail_base=0.80, brk_rate=0.12, chg_per_shift=0.9, chg_min=(24, 41),
         micro_rate=0.5, speed_loss=0.025, scrap=0.011, startup_scrap=0.003),
    dict(mid="WELD-01", pid="BRM", name="Robot weld cell 1", atype="Weld cell",
         step="Welding", ict=18.5, installed=2013, bottleneck=False, target=0.72,
         # Micro-stops dominate: Performance collapses while the downtime
         # report looks clean. The invisible-loss story.
         avail_base=0.90, brk_rate=0.10, chg_per_shift=0.4, chg_min=(18, 30),
         micro_rate=15.5, speed_loss=0.055, scrap=0.016, startup_scrap=0.003),
    dict(mid="WELD-02", pid="BRM", name="Robot weld cell 2", atype="Weld cell",
         step="Welding", ict=18.5, installed=2019, bottleneck=False, target=0.72,
         avail_base=0.84, brk_rate=0.09, chg_per_shift=0.4, chg_min=(16, 27),
         micro_rate=1.1, speed_loss=0.022, scrap=0.010, startup_scrap=0.002),
    # --- Steinwald: machining
    dict(mid="CNC-01", pid="STW", name="Machining centre 1", atype="CNC",
         step="Machining", ict=52.0, installed=2016, bottleneck=False, target=0.75,
         # High OEE, but running well past demand: the overproduction trap.
         avail_base=0.81, brk_rate=0.08, chg_per_shift=0.5, chg_min=(22, 38),
         micro_rate=0.6, speed_loss=0.020, scrap=0.008, startup_scrap=0.002,
         demand_ratio=0.72),
    dict(mid="CNC-02", pid="STW", name="Machining centre 2", atype="CNC",
         step="Machining", ict=52.0, installed=2016, bottleneck=False, target=0.75,
         avail_base=0.78, brk_rate=0.11, chg_per_shift=0.5, chg_min=(24, 40),
         micro_rate=0.8, speed_loss=0.026, scrap=0.010, startup_scrap=0.002),
    dict(mid="CNC-03", pid="STW", name="Machining centre 3", atype="CNC",
         step="Machining", ict=48.0, installed=2018, bottleneck=False, target=0.75,
         # Worst OEE in the group, but starved of work, not broken. Chasing it
         # with maintenance spend would be the wrong call.
         avail_base=0.47, brk_rate=0.10, chg_per_shift=0.3, chg_min=(20, 34),
         starve_rate=1.9, starve_min=(45, 150), filler_codes=["STARVE", "NO-OP"],
         micro_rate=0.5, speed_loss=0.022, scrap=0.009, startup_scrap=0.002,
         demand_ratio=1.02),
    dict(mid="CNC-04", pid="STW", name="Machining centre 4", atype="CNC",
         step="Machining", ict=48.0, installed=2021, bottleneck=False, target=0.78,
         avail_base=0.83, brk_rate=0.07, chg_per_shift=0.4, chg_min=(18, 30),
         micro_rate=0.4, speed_loss=0.018, scrap=0.007, startup_scrap=0.002),
    dict(mid="GRIND-01", pid="STW", name="Precision grinder", atype="Grinder",
         step="Grinding", ict=76.0, installed=2009, bottleneck=True, target=0.70,
         # Carries one catastrophic failure that skews its month.
         avail_base=0.74, brk_rate=0.16, chg_per_shift=0.3, chg_min=(30, 52),
         micro_rate=0.7, speed_loss=0.030, scrap=0.013, startup_scrap=0.003),
    # --- Valdera: assembly and test
    dict(mid="ASSY-01", pid="VLD", name="Actuator assembly line 1", atype="Assembly",
         step="Assembly", ict=31.0, installed=2005, bottleneck=False, target=0.68,
         avail_base=0.79, brk_rate=0.13, chg_per_shift=0.8, chg_min=(28, 46),
         micro_rate=1.6, speed_loss=0.035, scrap=0.015, startup_scrap=0.005),
    dict(mid="ASSY-02", pid="VLD", name="Actuator assembly line 2", atype="Assembly",
         step="Assembly", ict=31.0, installed=2007, bottleneck=True, target=0.68,
         # Speed decays slowly across the window: worn tooling, no alarm fires.
         avail_base=0.78, brk_rate=0.14, chg_per_shift=0.8, chg_min=(30, 50),
         micro_rate=1.8, speed_loss=0.030, speed_drift=0.075,
         scrap=0.016, startup_scrap=0.005),
    dict(mid="LEAK-01", pid="VLD", name="Leak test station", atype="Test",
         step="Test", ict=22.0, installed=2015, bottleneck=False, target=0.75,
         avail_base=0.82, brk_rate=0.08, chg_per_shift=0.3, chg_min=(12, 22),
         micro_rate=1.2, speed_loss=0.020, scrap=0.021, startup_scrap=0.003),
    dict(mid="PACK-01", pid="VLD", name="Packing line", atype="Packaging",
         step="Packing", ict=9.5, installed=2012, bottleneck=False, target=0.78,
         # Quality loss concentrated right after changeover: Reduced Yield,
         # not Process Defects. Tests whether the agent knows the difference.
         avail_base=0.81, brk_rate=0.10, chg_per_shift=1.2, chg_min=(14, 26),
         micro_rate=1.4, speed_loss=0.025, scrap=0.007, startup_scrap=0.052),
]

# --------------------------------------------------------------- reason codes
# oee_factor follows Nakajima's Six Big Losses. counts_as_stop drives whether
# the event reduces Run Time (Availability) or only Total Count (Performance).
REASON_CODES = [
    # Equipment Failure -> Availability, unplanned
    ("BRK-MECH", "Mechanical breakdown", "Equipment Failure", "Availability", 0, 1),
    ("BRK-ELEC", "Electrical fault", "Equipment Failure", "Availability", 0, 1),
    ("BRK-TOOL", "Tooling failure", "Equipment Failure", "Availability", 0, 1),
    ("BRK-HYD", "Hydraulic fault", "Equipment Failure", "Availability", 0, 1),
    ("STARVE", "Material starvation", "Equipment Failure", "Availability", 0, 1),
    ("BLOCK", "Downstream blockage", "Equipment Failure", "Availability", 0, 1),
    ("NO-OP", "No operator available", "Equipment Failure", "Availability", 0, 1),
    # Setup and Adjustments -> Availability, planned
    ("CHG-OVER", "Changeover / setup", "Setup and Adjustments", "Availability", 1, 1),
    ("ADJ-TOOL", "Tooling adjustment", "Setup and Adjustments", "Availability", 1, 1),
    ("PM-PLAN", "Planned maintenance", "Setup and Adjustments", "Availability", 1, 1),
    ("CLEAN", "Cleaning", "Setup and Adjustments", "Availability", 1, 1),
    ("QA-CHECK", "In-process quality check", "Setup and Adjustments", "Availability", 1, 1),
    # Idling and Minor Stops -> Performance, not stop time
    ("JAM", "Material jam", "Idling and Minor Stops", "Performance", 0, 0),
    ("MISFEED", "Misfeed", "Idling and Minor Stops", "Performance", 0, 0),
    ("SENSOR", "Sensor fault / reset", "Idling and Minor Stops", "Performance", 0, 0),
    ("MINOR-ADJ", "Minor operator adjustment", "Idling and Minor Stops", "Performance", 0, 0),
    ("CHIP-CLR", "Chip / swarf clearance", "Idling and Minor Stops", "Performance", 0, 0),
]
STOP_CODES = {r[0] for r in REASON_CODES if r[5] == 1}
UNPLANNED = ["BRK-MECH", "BRK-ELEC", "BRK-TOOL", "BRK-HYD", "BLOCK", "NO-OP"]
MICRO = ["JAM", "MISFEED", "SENSOR", "MINOR-ADJ", "CHIP-CLR"]

# ------------------------------------------------------------- defect codes
DEFECT_CODES = [
    ("DIM-OOT", "Dimension out of tolerance", "Process Defects"),
    ("SURF", "Surface finish defect", "Process Defects"),
    ("BURR", "Burr / edge condition", "Process Defects"),
    ("WELD-POR", "Weld porosity", "Process Defects"),
    ("LEAK-FAIL", "Leak test failure", "Process Defects"),
    ("ASSY-MISS", "Missing component", "Process Defects"),
    ("SU-SETUP", "First-off setup reject", "Reduced Yield"),
    ("SU-WARM", "Warm-up reject", "Reduced Yield"),
]
PROCESS_DEFECTS = [d[0] for d in DEFECT_CODES if d[2] == "Process Defects"]
STARTUP_DEFECTS = [d[0] for d in DEFECT_CODES if d[2] == "Reduced Yield"]

# Each asset type fails in its own characteristic ways, so a Pareto over a
# period is meaningful rather than uniform noise across every code.
DEFECTS_BY_TYPE = {
    "Press":     ["DIM-OOT", "BURR", "SURF"],
    "Weld cell": ["WELD-POR", "DIM-OOT"],
    "CNC":       ["DIM-OOT", "SURF", "BURR"],
    "Grinder":   ["SURF", "DIM-OOT"],
    "Assembly":  ["ASSY-MISS", "DIM-OOT"],
    "Test":      ["LEAK-FAIL"],
    "Packaging": ["ASSY-MISS", "SURF"],
}

# C shift at Bramfeld has no on-site maintenance cover, so a breakdown that
# would be fixed in 20 minutes on A shift runs on until morning. The finding
# is structural, NOT an operator-performance story: repair duration stretches,
# breakdown frequency does not.
NIGHT_MTTR_MULTIPLIER = {"BRM": 2.9, "STW": 1.35, "VLD": 1.0}
# Longer repairs mean more downtime overall, so night availability is genuinely
# worse where there is no cover. Kept modest so nights stay plausible.
NIGHT_STOP_MULTIPLIER = {"BRM": 1.42, "STW": 1.10, "VLD": 1.0}

plant_by_id = {p["pid"]: p for p in PLANTS}


def working_shifts(d):
    """Yield (plant, shift_code) pairs scheduled on date d."""
    wd = d.weekday()
    for p in PLANTS:
        if wd < 5:
            codes = p["shifts"].split(",")
        elif wd == 5 and p["sat_shifts"]:
            codes = p["sat_shifts"].split(",")
        else:
            codes = []
        for c in codes:
            if c:
                yield p, c


def n_events(rate):
    """Poisson-ish count from a mean rate, without numpy."""
    n, acc = 0, random.random()
    import math
    limit = math.exp(-rate)
    while acc > limit:
        acc *= random.random()
        n += 1
    return n


# ------------------------------------------------------- fact generation
shift_rows, events = [], []
defects_acc = {}
event_seq = 0
total_days = (END - START).days + 1

# One catastrophic grinder failure, placed inside the event-retention window.
CATASTROPHE = (date(2026, 7, 14), "C", "GRIND-01", "BRK-MECH", 840)

d = START
while d <= END:
    day_idx = (d - START).days
    progress = day_idx / max(1, total_days - 1)
    for plant, shift_code in working_shifts(d):
        is_night = shift_code == "C"
        for m in [x for x in MACHINES if x["pid"] == plant["pid"]]:
            planned = 480.0
            stop_min = 0.0
            changeover_min = 0.0
            micro_min = 0.0
            shift_events = []

            def add(code, minutes):
                global event_seq
                event_seq += 1
                shift_events.append(dict(
                    event_id="EV-%06d" % event_seq, event_date=d.isoformat(),
                    shift=shift_code, machine_id=m["mid"], plant_id=plant["pid"],
                    reason_code=code, duration_min=round(minutes, 1)))
                return minutes

            # ---- unplanned breakdowns
            mttr_mult = NIGHT_MTTR_MULTIPLIER[plant["pid"]] if is_night else 1.0
            for _ in range(n_events(m["brk_rate"])):
                code = random.choice(UNPLANNED)
                dur = random.uniform(8, 55) * mttr_mult * random.uniform(0.7, 1.4)
                stop_min += add(code, dur)

            # ---- material starvation (CNC-03's defining problem)
            if m.get("starve_rate"):
                for _ in range(n_events(m["starve_rate"])):
                    lo, hi = m["starve_min"]
                    stop_min += add("STARVE", random.uniform(lo, hi))

            # ---- changeovers and adjustments
            drift = 1.0 + m.get("chg_drift", 0.0) * progress
            n_chg = n_events(m["chg_per_shift"])
            for _ in range(n_chg):
                lo, hi = m["chg_min"]
                dur = random.uniform(lo, hi) * drift
                changeover_min += add("CHG-OVER", dur)
            if random.random() < 0.25:
                stop_min += add("ADJ-TOOL", random.uniform(6, 18))
            if random.random() < 0.10:
                stop_min += add("PM-PLAN", random.uniform(30, 90))
            if random.random() < 0.18:
                stop_min += add("QA-CHECK", random.uniform(8, 20))
            if random.random() < 0.12:
                stop_min += add("CLEAN", random.uniform(10, 25))

            # ---- the one catastrophic failure
            cd, cs, cm, ccode, cdur = CATASTROPHE
            if d == cd and shift_code == cs and m["mid"] == cm:
                stop_min += add(ccode, cdur)

            # ---- Valdera excludes changeover from Planned Production Time
            if plant["changeover_excluded"]:
                planned -= changeover_min
                excluded = changeover_min
            else:
                stop_min += changeover_min
                excluded = 0.0

            # Top up to the machine's characteristic availability. The basis is
            # planned + excluded changeover, so a site that keeps changeover out
            # of Planned Production Time reports BETTER availability than its
            # true equipment availability. That gap is deliberate.
            basis = planned + excluded
            night_mult = (NIGHT_STOP_MULTIPLIER[plant["pid"]] if is_night else 1.0)
            target_stop = (basis * (1.0 - m["avail_base"]) * night_mult
                           * random.uniform(0.72, 1.3))
            deficit = target_stop - (stop_min + excluded)
            filler = m.get("filler_codes") or UNPLANNED
            guard = 0
            while deficit > 12.0 and guard < 8:
                chunk = min(deficit, random.uniform(14, 58) * mttr_mult)
                stop_min += add(random.choice(filler), chunk)
                deficit -= chunk
                guard += 1

            # Cap availability-affecting minutes by scaling this shift's stop
            # events proportionally, so the downtime log always reconciles to
            # booked stop time. Clamping the total on its own would leave the
            # log summing to more than the shift record admits.
            planned = max(60.0, planned)
            if stop_min > planned - 20.0:
                factor = (planned - 20.0) / stop_min
                for e in shift_events:
                    if e["reason_code"] in STOP_CODES:
                        e["duration_min"] = round(e["duration_min"] * factor, 1)
                if excluded:
                    excluded *= factor
                    planned = 480.0 - excluded
                stop_min = planned - 20.0
            run_time = planned - stop_min

            # ---- micro-stops: Performance loss, never Run Time
            for _ in range(n_events(m["micro_rate"] * run_time / 420.0)):
                micro_min += add(random.choice(MICRO), random.uniform(0.5, 4.5))
            micro_min = min(micro_min, run_time * 0.35)

            # ---- reduced speed, with optional slow decay over the window
            speed_loss = m["speed_loss"] + m.get("speed_drift", 0.0) * progress
            if is_night:
                speed_loss += 0.012
            speed_loss = min(0.42, max(0.0, speed_loss + random.gauss(0, 0.012)))

            producing = max(1.0, (run_time - micro_min) * (1.0 - speed_loss))
            total_count = int(producing * 60.0 / m["ict"])

            # ---- quality: steady-state defects plus startup rejects
            scrap_rate = max(0.0, m["scrap"] + random.gauss(0, 0.004))
            su_rate = max(0.0, m["startup_scrap"] + random.gauss(0, 0.002))
            proc_rej = int(total_count * scrap_rate)
            su_rej = int(total_count * su_rate * (1.6 if n_chg else 0.15))
            good_count = max(0, total_count - proc_rej - su_rej)

            iso_year, iso_week, _ = d.isocalendar()
            week_key = "%04d-W%02d" % (iso_year, iso_week)
            for kind, n in (("proc", proc_rej), ("su", su_rej)):
                if n <= 0:
                    continue
                pool = (DEFECTS_BY_TYPE[m["atype"]] if kind == "proc"
                        else STARTUP_DEFECTS)
                left = n
                for i, dc in enumerate(pool):
                    k = left if i == len(pool) - 1 else min(
                        left, int(round(n * random.uniform(0.35, 0.70))))
                    if k > 0:
                        ak = (week_key, m["mid"], plant["pid"], dc)
                        defects_acc[ak] = defects_acc.get(ak, 0) + k
                    left -= k
                    if left <= 0:
                        break

            demand = int(total_count * m.get("demand_ratio", 0.97)
                         * random.uniform(0.94, 1.04))

            shift_rows.append(dict(
                shift_date=d.isoformat(), shift=shift_code, machine_id=m["mid"],
                plant_id=plant["pid"],
                planned_production_time_min=round(planned, 1),
                stop_time_min=round(stop_min, 1),
                run_time_min=round(run_time, 1),
                changeover_min_excluded_from_planned=round(excluded, 1),
                ideal_cycle_time_sec=m["ict"],
                total_count=total_count, good_count=good_count,
                scheduled_units=demand))

            if d >= EVENT_RETENTION_FROM:
                events.extend(shift_events)
    d += timedelta(days=1)


# ------------------------------------------------------------------- output
def write(name, rows, fields):
    path = os.path.join(OUT, name)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in fields})
    print("%-24s %6d rows" % (name, len(rows)))


write("plants.csv", [dict(
    plant_id=p["pid"], plant_name=p["name"], country=p["country"],
    focus=p["focus"], opened_year=p["opened"], shift_pattern=p["shifts"],
    saturday_shifts=p["sat_shifts"] or "none",
    changeover_excluded_from_planned_time=int(p["changeover_excluded"]),
) for p in PLANTS], ["plant_id", "plant_name", "country", "focus", "opened_year",
                     "shift_pattern", "saturday_shifts",
                     "changeover_excluded_from_planned_time"])

write("machines.csv", [dict(
    machine_id=m["mid"], plant_id=m["pid"], machine_name=m["name"],
    asset_type=m["atype"], process_step=m["step"],
    ideal_cycle_time_sec=m["ict"], installed_year=m["installed"],
    is_bottleneck=int(m["bottleneck"]), target_oee=m["target"],
) for m in MACHINES], ["machine_id", "plant_id", "machine_name", "asset_type",
                       "process_step", "ideal_cycle_time_sec", "installed_year",
                       "is_bottleneck", "target_oee"])

write("reason_codes.csv", [dict(
    reason_code=r[0], reason_description=r[1], big_loss=r[2],
    oee_factor=r[3], is_planned=r[4], counts_as_stop_time=r[5],
) for r in REASON_CODES], ["reason_code", "reason_description", "big_loss",
                           "oee_factor", "is_planned", "counts_as_stop_time"])

write("defect_codes.csv", [dict(
    defect_code=x[0], defect_description=x[1], big_loss=x[2],
) for x in DEFECT_CODES], ["defect_code", "defect_description", "big_loss"])

write("shifts.csv", shift_rows, [
    "shift_date", "shift", "machine_id", "plant_id",
    "planned_production_time_min", "stop_time_min", "run_time_min",
    "changeover_min_excluded_from_planned", "ideal_cycle_time_sec",
    "total_count", "good_count", "scheduled_units"])

write("downtime_events.csv", events, [
    "event_id", "event_date", "shift", "machine_id", "plant_id",
    "reason_code", "duration_min"])

# Aggregated to ISO week: shift-level quality is already derivable from
# shifts.csv (good_count / total_count). This table exists to answer "which
# defect types drive the loss", which is a Pareto over a period.
defects = [dict(iso_week=w, machine_id=mi, plant_id=pl, defect_code=dc, units=u)
           for (w, mi, pl, dc), u in sorted(defects_acc.items())]
write("quality_defects.csv", defects, [
    "iso_week", "machine_id", "plant_id", "defect_code", "units"])

print("\nshift rollups: %s .. %s" % (START, END))
print("event detail:  %s .. %s (90-day retention)" % (EVENT_RETENTION_FROM, END))
print("plants: %d   machines: %d" % (len(PLANTS), len(MACHINES)))

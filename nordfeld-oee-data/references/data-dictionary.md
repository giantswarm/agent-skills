# Nordfeld MES data dictionary

Seven CSV extracts in `data/`, loaded into SQLite by `scripts/query.py`.
Three plants, 14 machines. Times in minutes, cycle times in seconds.

**Two different coverage windows.** Shift rollups run 2026-03-01 to 2026-08-31.
Event-level detail is retained 90 days only, from 2026-06-03. Loss Pareto and
downtime cause analysis are therefore impossible before June: say so rather than
reaching for the rollups to fake it.

## Tables

### plants (3 rows)
`plant_id`, `plant_name`, `country`, `focus`, `opened_year`, `shift_pattern`,
`saturday_shifts`.

`changeover_excluded_from_planned_time` is the important one. Where it is 1, the
site subtracts changeover minutes from Planned Production Time instead of
booking them as stop time, which raises its reported Availability without any
difference on the floor. Valdera (VLD) does this; Bramfeld (BRM) and Steinwald
(STW) do not. Never compare Availability or OEE across plants without accounting
for it, and use `availability_common_basis_pct` when you do.

### machines (14 rows)
`machine_id`, `plant_id`, `machine_name`, `asset_type`, `process_step`,
`ideal_cycle_time_sec`, `installed_year`, `target_oee`.

`is_bottleneck` flags the constraint of its plant's flow. This changes what a
low OEE means: recovered time on the bottleneck becomes plant output, recovered
time elsewhere becomes nothing. Check it before recommending spend.

`target_oee` is per machine and deliberately not uniform, because asset types
are not comparable.

### shifts (5,238 rows)
One row per machine per shift, and the source of every OEE figure. It carries
the **raw inputs only**, never OEE itself, so the formulas are applied in one
place and every answer agrees:

| column | meaning |
| --- | --- |
| `shift_date`, `shift` | date and shift code (A 06:00, B 14:00, C 22:00) |
| `planned_production_time_min` | Planned Production Time |
| `stop_time_min` | Stop Time booked against Availability |
| `run_time_min` | Planned minus Stop |
| `changeover_min_excluded_from_planned` | minutes taken out of Planned Production Time rather than booked as stop time; non-zero at Valdera only |
| `ideal_cycle_time_sec` | Ideal Cycle Time for the work run that shift |
| `total_count`, `good_count` | parts produced, and parts right first time |
| `scheduled_units` | what the schedule asked for, for attainment checks |

### downtime_events (last 90 days)
One row per stop: `event_id`, `event_date`, `shift`, `machine_id`, `plant_id`,
`reason_code`, `duration_min`.

Contains both real downtime and micro-stops. `reason_codes.counts_as_stop_time`
separates them, and the distinction is essential: micro-stop minutes are **not**
in `stop_time_min` and do not reduce Availability. They reduce `total_count`, so
they appear as Performance loss. Summing all event durations and calling it
downtime is wrong.

### reason_codes (17 rows)
`reason_code`, `reason_description`, `big_loss`, `oee_factor`, `is_planned`,
`counts_as_stop_time`. Maps every stop to one of the Six Big Losses and to the
factor it damages. Join through this rather than guessing from the code name.

### quality_defects (weekly)
`iso_week`, `machine_id`, `plant_id`, `defect_code`, `units`.

Aggregated to ISO week, because shift-level quality is already derivable from
`shifts.csv` (`good_count / total_count`). This table answers "which defect
types drive the loss", which is a Pareto over a period.

### defect_codes (8 rows)
`defect_code`, `defect_description`, `big_loss`. `big_loss` splits Process
Defects (steady-state, a process-control problem) from Reduced Yield (startup
and post-changeover, a setup problem). Different fixes, so always check which.

## Prepared views

Use these. They encode the formulas from `references/oee-reference.md`, so two
answers built on them cannot disagree.

- **`v_shift_oee`**: one row per machine-shift with `availability_pct`,
  `performance_pct`, `quality_pct`, `oee_pct`, `schedule_attainment_pct` and
  `availability_common_basis_pct` computed from the raw inputs, plus machine and
  plant attributes joined in.
- **`v_machine_period`**: per-machine totals over the **whole** window. For a
  specific period, aggregate `v_shift_oee` yourself.
- **`v_events`**: downtime events with their Six Big Losses classification and
  `counts_as_stop_time` attached.
- **`v_defects`**: weekly defects with description and loss category.

## Aggregating correctly

Rebuild OEE from summed inputs. Never average the per-shift percentages: the
mean of ratios is not the ratio of the totals, and the error grows as shift
lengths and volumes vary.

```sql
-- right
SELECT 100.0 * SUM(good_count) / SUM(total_count) AS quality_pct FROM v_shift_oee ...
-- wrong
SELECT AVG(quality_pct) FROM v_shift_oee ...
```

The `plant` and `losses` commands in `query.py` already do this correctly; copy
their shape when writing custom SQL.

## What this data cannot answer

- **No cost data.** Downtime cannot be converted to money. Report minutes,
  parts and OEE points, and let the plant apply its own rates.
- **No maintenance history**, work orders or spare parts.
- **No operator or crew identity.** Deliberate: OEE is not a people metric.
- **No event detail before 2026-06-03.**
- **No calendar or total-time data**, so TEEP and utilisation cannot be
  computed. OEE covers scheduled time only.
- **No process parameters**, so root causes inside a process are out of reach.
  The data localises a problem; confirming its mechanism needs the floor.

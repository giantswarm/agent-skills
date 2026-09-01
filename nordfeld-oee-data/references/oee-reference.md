# OEE reference

The domain knowledge behind every answer. OEE is a well-specified metric with a
well-documented set of ways to get it wrong, and most of the value an analyst
adds is in avoiding the second list.

## The metric

**Overall Equipment Effectiveness**, not Efficiency. The distinction matters
because effectiveness asks whether the equipment did the right work well, while
efficiency implies a simple speed ratio. Anyone in a plant will use
"effectiveness"; getting the name wrong marks an outsider immediately.

OEE is the share of Planned Production Time that was truly productive:
manufacturing only good parts, as fast as the equipment can go, with no stops.

### The three factors

```
Availability = Run Time / Planned Production Time
Performance  = (Ideal Cycle Time x Total Count) / Run Time
Quality      = Good Count / Total Count

OEE = Availability x Performance x Quality
```

Equivalently, and useful as a cross-check:

```
OEE = (Good Count x Ideal Cycle Time) / Planned Production Time
```

The factored form is strongly preferred, because a single OEE number tells
nobody what to do. Availability at 60% and Performance at 60% are the same OEE
and completely different problems, fixed by different people.

### Definitions

- **Planned Production Time**: time the asset was scheduled to produce.
  Excludes shifts not run, holidays, and no-demand periods.
- **Run Time**: Planned Production Time minus Stop Time.
- **Stop Time**: stops of several minutes or more, planned or unplanned.
- **Ideal Cycle Time**: theoretical fastest time to make one part. The
  engineered rate, not the historical average, and not a negotiated target.
- **Total Count**: all parts produced, good and bad.
- **Good Count**: parts made right the first time. Rework is not good.

### Benchmarks

85% is the widely cited world-class figure for discrete manufacturing, from
90% Availability x 95% Performance x 99% Quality. It is genuinely rare, and
treating it as a floor rather than an aspiration destroys credibility with
people who run machines.

Realistic ranges, for orientation only:

| Context | Typical | Strong |
| --- | --- | --- |
| Discrete manufacturing overall | 55 to 65% | 80%+ |
| Automotive (stamping, welding, assembly) | 65 to 80% | 85%+ |
| Metal processing, CNC, forming | 50 to 70% | 75%+ |
| Electronics and assembly | 55 to 75% | 80%+ |
| Food, beverage, FMCG lines | 55 to 75% | 80%+ |
| Pharma packaging and filling | 50 to 70% | 70%+ |

Manually recorded OEE typically overstates reality by 8 to 12 percentage
points, which makes any comparison between a manual figure and an automatically
measured one meaningless. This is the single biggest reason benchmark
comparisons mislead.

## The Six Big Losses

Nakajima's taxonomy. Every loss belongs to exactly one factor, which is what
makes the classification useful: it routes a problem to the function that can
fix it.

| Loss | Factor | What it is | Typical causes |
| --- | --- | --- | --- |
| **Equipment Failure** | Availability | Unplanned stops while scheduled to run | Breakdowns, tooling failure, starvation, blockage, no operator |
| **Setup and Adjustments** | Availability | Planned stops while scheduled to run | Changeovers, tooling adjustment, planned maintenance, cleaning, inspection |
| **Idling and Minor Stops** | Performance | Short stops, typically under five minutes, cleared by the operator | Jams, misfeeds, sensor faults, quick adjustments |
| **Reduced Speed** | Performance | Running slower than Ideal Cycle Time | Worn or dirty equipment, poor lubrication, substandard material, inexperience |
| **Process Defects** | Quality | Defects produced during stable running | Wrong settings, handling damage, material problems |
| **Reduced Yield** | Quality | Defects from startup until stable running | Suboptimal changeover, warm-up, first-off settings |

Two distinctions do most of the diagnostic work:

**Minor stops are Performance losses, not downtime.** They are too short to be
booked as Stop Time, so they never appear in a downtime report. They surface
only as the gap between what the asset should have produced in its Run Time and
what it actually produced. A machine with excellent Availability and poor
Performance is almost always bleeding minor stops or running slow, and the
downtime report will look clean while it happens. This is the most commonly
missed loss in a plant.

**Process Defects and Reduced Yield need different fixes.** Scrap spread evenly
through a run is a process-control problem. Scrap concentrated in the minutes
after a changeover is a setup problem, and the fix is first-off validation or
warm-up procedure, not tighter process control. Check when the scrap happened
before recommending anything.

## How OEE is misused

Each of these is a documented failure mode and worth actively checking for.

**As an operator scorecard.** OEE is a property of the equipment and the system
around it, not of the people on shift. Most shift-to-shift variation traces to
structural causes: maintenance cover, material supply, product mix, who is
available to clear a jam. Treating a shift's OEE as a performance rating both
misdiagnoses the problem and teaches people to game the number. When a shift
looks worse, find the structural reason before concluding anything about the crew.

**Comparing dissimilar assets.** OEE is only comparable between assets running
comparable work with comparable Ideal Cycle Times. A press and a leak tester
cannot be ranked against each other meaningfully. Cross-plant comparisons need
identical definitions of planned time and identical measurement methods, which
in practice they rarely have.

**Manipulating Planned Production Time.** Availability is Run Time over Planned
Production Time, so anything moved out of Planned Production Time raises OEE
without changing a thing on the floor. Booking changeovers as unscheduled, or
excluding them from planned time, is the most common version. Always establish
what is inside the denominator before comparing sites, and restate onto a common
basis when they differ.

**Chasing OEE on a non-bottleneck.** An hour recovered on a machine that is not
the constraint produces nothing extra; the plant's output is set by its
bottleneck. Low OEE on a non-bottleneck asset that is starved of work is a
capacity and scheduling question, not a maintenance emergency. Check whether the
asset is the constraint before recommending spend.

**Ignoring demand.** OEE rewards making parts, and says nothing about whether
those parts were needed. An asset can post excellent OEE by overproducing into
inventory, which is waste wearing a good number. Always sanity-check output
against the schedule before celebrating a high figure.

## What OEE does not measure

Naming a limit honestly is more useful than stretching the metric past it.

- **Utilisation.** OEE only covers scheduled time. An asset idle sixteen hours a
  day can post excellent OEE. TEEP (OEE x the share of all calendar time
  scheduled) is the metric for that question.
- **Profitability.** A machine at 90% OEE can run at a loss.
- **Labour.** OEE is machine-centric and says nothing about staffing or
  coordination, which dominate in manual assembly.
- **Energy and material consumption.**
- **Real-time quality**, where the Good Count comes from end-of-line inspection
  and defects are only visible after the fact.

Sources: [OEE.com](https://www.oee.com/), [Six Big Losses](https://www.oee.com/oee-six-big-losses/), [Lean Production OEE](https://www.leanproduction.com/oee/), [The Limits of OEE](https://www.symestic.com/en-us/blog/oee/the-limits-of-oee), [OEE Benchmarks](https://www.symestic.com/en-us/blog/oee/oee-benchmarks), [OEE Frequently Used, Often Misused](https://www.implementation.com/oee-frequently-used-often-misused/)

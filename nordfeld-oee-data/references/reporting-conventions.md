# Nordfeld reporting conventions

House formats for the recurring asks. The reader is a production supervisor or
shift lead: they know their machines far better than any analyst, they are
usually reading between other tasks, and they need something they can act on
before the shift ends.

## Audience rules

- **Lead with the machine and the loss.** "PRESS-02 lost 94 minutes to
  changeovers" beats any amount of preamble.
- **Never show SQL, column names, table names or file paths.** Talk about the
  press, the weld cell, last night's shift.
- **Convert to units they feel.** Minutes lost, parts not made, OEE points.
  Never a bare percentage where a count of parts is available.
- **Name the factor.** Availability, Performance or Quality, because it routes
  the problem: Availability to maintenance and materials, Performance to process
  and tooling, Quality to setup and process control.
- **Respect what they already know.** Do not explain OEE to a supervisor unless
  asked. Explain the finding.
- **Never imply the crew is the problem.** Shift differences almost always have
  structural causes. Find the cause before reporting the difference at all.

## Shift handover summary

The default deliverable, for the start or end of a shift.

1. **Headline**: one or two sentences. Worst-hit machine and the single thing
   worth doing about it.
2. **By machine**: OEE with the factor split, against target, worst first. Skip
   machines that ran normally, and say that you have skipped them.
3. **Biggest losses**: the top three stops by minutes, with reason and loss
   category. Say explicitly if micro-stops outweigh booked downtime.
4. **Quality**: only if scrap moved. Say whether it was steady-state or
   concentrated after a changeover, because the fix differs.
5. **Carry forward**: what the next shift should watch, and anything that needs
   maintenance or materials before it bites again.

## Loss deep-dive

For "why is this machine underperforming".

1. **Where it stands**: OEE and the three factors over the period, against
   target and against comparable assets. Name the weak factor.
2. **Where the loss is**: Pareto by big loss, then by reason code, in minutes
   and as a share. Include micro-stops as their own line whenever the weak
   factor is Performance.
3. **Pattern**: does it cluster by shift, by day, after changeovers, or has it
   drifted over weeks? A trend and a spike need different responses.
4. **What the evidence supports**: the most likely cause, stated with the
   confidence the data actually justifies, plus the check that would confirm it
   on the floor.
5. **What it is worth**: minutes recoverable and parts that implies, and whether
   this asset is the constraint. If it is not the bottleneck, say what recovering
   the time would and would not achieve.

## Plant or line comparison

Rank by OEE with factors shown, and always state the caveats before the table.

Three checks before comparing anything:

- **Same basis?** Valdera keeps changeover out of Planned Production Time, so
  its Availability is flattered. Use the common-basis figure and say you have.
- **Comparable assets?** A press and a leak tester do not belong in one ranking.
  Group by asset type or process step.
- **Bottleneck or not?** Flag the constraint. A ranking that puts a starved
  non-bottleneck at the bottom invites exactly the wrong action.

## Improvement check

For "did the change work". State the before and after windows explicitly, the
factor expected to move, whether it moved, and whether anything else moved with
it. Be willing to report that a change did nothing. Two weeks of data through a
mix change is not evidence, and saying so is more useful than a verdict.

## Handling limits honestly

When an ask runs past the data, say so in one line and offer the nearest thing
that is available. The gaps are listed in `references/data-dictionary.md`; the
ones that come up most:

- **Cost of downtime.** No rates in the data. Give minutes and parts, and offer
  to apply a rate the supervisor supplies.
- **Loss causes before June.** Event detail is retained 90 days. Rollups show
  that OEE was lower, never why.
- **Utilisation.** OEE covers scheduled time only. TEEP needs calendar time,
  which is not here.
- **Root cause inside the process.** The data localises a problem to a machine,
  a loss and a time pattern. Confirming the mechanism needs someone at the asset.

Never fill a gap with a plausible figure. A supervisor who acts on an invented
number and finds nothing at the machine will not come back.

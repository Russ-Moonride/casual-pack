# Homework — Food-delivery rollout with Difference-in-Differences

## Scenario

A food-delivery marketplace launched a **free-delivery banner** in one pilot
region on **2026-04-01**. The business question:

> Did the banner increase order conversion?

There was no randomized experiment. You have a daily panel of one treated region
and several untreated comparison regions. Your job is to estimate the causal
effect and decide whether the counterfactual deserves trust.

This homework intentionally uses a **different domain** and a **different causal
design** from the in-class interrupted-time-series case. The core discipline is
the same: an effect estimate is only useful if the counterfactual is credible.

## Data

Student-facing files:

- `data/homework/food_delivery_daily.csv`
- `data/homework/food_delivery_regions.csv`

Daily panel columns:

| column | meaning |
|---|---|
| `date` | calendar date |
| `region` | market region |
| `treated_region` | `1` for the pilot region, `0` otherwise |
| `post` | `1` on and after `2026-04-01` |
| `active_users` | users who opened the app that day |
| `orders` | completed first orders that day |
| `conversion_rate` | `orders / active_users` |

Region metadata columns:

| column | meaning |
|---|---|
| `region` | region key |
| `region_label` | display label |
| `is_treated_region` | `1` for the pilot region |
| `market_type` | coarse region type |

## Required deliverables

Submit three artifacts:

1. **Notebook**: a marimo notebook or Python script that loads the data, estimates
   the effect, and validates the design.
2. **Validation log**: short append-only notes recording what the agent tried,
   what failed, and why the final result is trustworthy or not.
3. **Decision memo**: max one page. State the estimate, the assumptions, the
   validation result, and whether you would ship a causal claim.

## Minimum analysis requirements

Your analysis must include:

- A raw plot of treated and control conversion rates with the intervention date.
- The estimand in one sentence: whose effect, on what outcome, over what period,
  on what scale.
- A Difference-in-Differences estimate on `conversion_rate`.
- A pre-trends check. Plot treated vs controls before the rollout; do not only
  report a regression table.
- At least one falsification check:
  - fake treatment date in the pre-period, or
  - fake treated region / leave-one-control-out check.
- A sensitivity analysis over the comparison set. If one control is a poor
  counterfactual, say so and report the estimate with and without it.
- A clear separation between:
  - the numerical estimate, and
  - the causal claim that depends on the parallel-trends assumption.

## Suggested agent prompt

Use this as a starting point, then steer the agent:

```text
Analyze the effect of the free-delivery banner rollout using the data in
data/homework/food_delivery_daily.csv and data/homework/food_delivery_regions.csv.

Treatment: treated_region == 1, post == 1, rollout date 2026-04-01.
Outcome: conversion_rate = orders / active_users.

Use Difference-in-Differences. Do not stop at the first estimate. Validate the
counterfactual: plot treated/control pre-trends, run a placebo-in-time or
leave-one-control-out check, and test whether any control region is a weak
comparison. Keep an append-only log of the analysis decisions. Produce a short
decision memo with the estimate, assumptions, validation result, and whether the
causal claim is trustworthy.
```

## What good work looks like

A strong submission does **not** necessarily produce the largest or cleanest
effect. It does this:

- names the counterfactual explicitly;
- shows whether the comparison regions behave like a plausible counterfactual
  before treatment;
- refuses to hide a bad control region inside an average;
- reports uncertainty and model sensitivity;
- states the business conclusion with assumptions attached.

## Grading rubric

| criterion | what to look for |
|---|---|
| Estimand | names treated population, outcome, post-period, scale |
| Design fit | explains why DiD is appropriate and what parallel trends requires |
| Pre-trends | shows treated/control pre-period trajectories visually |
| Falsification | runs placebo date or fake-treated-region check |
| Sensitivity | checks whether the result depends on one control region |
| Memo quality | separates estimate, assumptions, validation, and action |

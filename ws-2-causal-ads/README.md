# MADS Session 02 — Participant Materials

This directory is the clean share package for Session 02:

> Agentic Causal Data Science — from blind run to validated causal workflow.

It contains slides, marimo notebooks, agent skills, class data, and the homework.
It intentionally excludes the speaker script and the homework solution.

## Contents

```text
slides/
  session-02.html                 # rendered deck, open directly in a browser
  session-02.qmd                  # editable Quarto source
  assets/                         # slide assets used by the source deck

notebooks/
  01-blind-run-without-skill.py   # first pass: plausible but wrong narrative
  02-validator-review-input.py    # blind analysis handed to the validator
  03-skill-guided-analysis.py     # rerun with the quasi-experiment skill
  04-bayesian-decision-analysis.py# uncertainty → revenue decision
  support/                        # log and validator output used by notebook 01

skills/
  causalpy-library/               # CausalPy usage cookbook
  causal-critiquer/               # fresh-context causal review workflow
  quasi-experiment-analysis/      # quasi-experiment discipline / traps
  marimo-pair/                    # working with live marimo notebooks

data/
  daily_aggregates_intervention.csv
  users_intervention.csv
  ground_truth.json               # used only for class reveal / calibration
  homework/
    food_delivery_daily.csv
    food_delivery_regions.csv

homework/
  food-delivery-did-homework.md   # student-facing assignment only
```

## Setup

Run commands from the root of this package directory:

```bash
cd sessions/02-causal/participant-package
uv sync
uv run marimo edit notebooks/01-blind-run-without-skill.py
```

If you copied this directory somewhere else, the same commands work from the
copied package root because this folder includes its own `pyproject.toml`:

```bash
uv sync
uv run marimo edit notebooks/01-blind-run-without-skill.py
```

## Suggested notebook order

1. `notebooks/01-blind-run-without-skill.py`
2. `notebooks/02-validator-review-input.py`
3. `notebooks/03-skill-guided-analysis.py`
4. `notebooks/04-bayesian-decision-analysis.py`

Notebook 01 reads `notebooks/support/blind-run-log.txt` and
`notebooks/support/validator-critique.md` to show the log → validation → skill
loop in one place.

## Homework

Open:

```text
homework/food-delivery-did-homework.md
```

The homework uses a different domain and a different design from the in-class
ITS case:

- domain: food delivery
- design: Difference-in-Differences
- outcome: `conversion_rate = orders / active_users`
- validation target: parallel trends and weak controls

The instructor key and solution are not included in this package.

## Using the skills

The `skills/` directory is included so you can inspect or copy the skills into
your agent environment. The most relevant ones are:

- `skills/quasi-experiment-analysis/` — when estimating intervention effects
- `skills/causal-critiquer/` — when validating a causal claim
- `skills/causalpy-library/` — when using CausalPy APIs

The workflow to copy is:

1. run an analysis;
2. keep a log of decisions and errors;
3. validate with a fresh reviewer / hard checks;
4. distill the reliable workflow into a reusable skill.

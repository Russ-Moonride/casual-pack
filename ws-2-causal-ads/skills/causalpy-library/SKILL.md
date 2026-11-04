---
name: causalpy-library
description: >-
  Cookbook of CausalPy patterns: how to fit each quasi-experimental design
  (ITS, DiD, RDD, IV, SCM), extract the answer, swap between sklearn and
  PyMC backends, plot results, and avoid the known gotchas. Use any time
  the user wants to run a causal analysis with CausalPy, or asks
  "how do I X with CausalPy".
allowed-tools: Read
---

# CausalPy — usage cookbook

CausalPy is a wrapper around sklearn + PyMC for quasi-experimental designs.
The API is small but has sharp edges; this skill encodes the recipes that
work and the gotchas that bite. Use it instead of guessing from the docs.

## When to use this skill

- Any task that involves `import causalpy`
- Translating a quasi-experimental design (ITS, DiD, RDD, IV, SCM) into
  fitting code
- Switching between sklearn and PyMC backends
- Debugging a CausalPy error or unexpected output
- Plotting results when the built-in `.plot()` fails (common)

## Quick-pick design table

| Design | Class | Reference |
|---|---|---|
| Interrupted Time Series | `cp.InterruptedTimeSeries` | [its.md](reference/its.md) |
| Difference-in-Differences | `cp.DifferenceInDifferences` | [did.md](reference/did.md) |
| Regression Discontinuity | `cp.RegressionDiscontinuity` | (add when needed) |
| Synthetic Control | `cp.SyntheticControl` | (add when needed) |
| Instrumental Variables | `cp.InstrumentalVariable` | (add when needed) |
| Inverse-probability weighting | `cp.InversePropensityWeighting` | (add when needed) |
| Pre-Post Non-equivalent Groups | `cp.PrePostNEGD` | (add when needed) |

## Backend swap pattern (the one-liner that matters)

Every design takes a `model=` argument. Two flavors:

### sklearn (fast, point estimates only)

```python
import causalpy as cp
from sklearn.linear_model import LinearRegression as SkLR

# CausalPy needs a wrapped sklearn class:
LinearRegressionCP = cp.create_causalpy_compatible_class(SkLR)

result = cp.InterruptedTimeSeries(..., model=LinearRegressionCP())
```

> **Gotcha**: `cp.skl_models.LinearRegression` does *not* exist. The
> top-level `cp.create_causalpy_compatible_class` is the public API for
> sklearn integration; use any `sklearn.linear_model.*` (or `Ridge`,
> `ElasticNet`, etc.) as the base class.

### PyMC (slower, full posterior + HDI)

```python
import causalpy as cp

result = cp.InterruptedTimeSeries(
    ...,
    model=cp.pymc_models.LinearRegression(
        sample_kwargs={"progressbar": False, "random_seed": 42},
    ),
)
```

> **Gotcha**: omit `sample_kwargs` and you get a noisy progress bar
> spamming the notebook output. Always pass at least `progressbar`.
> Reproducibility needs `random_seed`.

The rest of the API (`.fit`, `.summary`, `.plot`, attributes like
`post_impact`) is the *same* regardless of backend.

See [pymc-backend.md](reference/pymc-backend.md) for posterior extraction
patterns (HDI, posterior plots, probability statements).

## Extracting the answer

After fitting, the most-used attributes are:

| What you want | How to get it |
|---|---|
| Per-time-point causal effect (post period) | `result.post_impact` — `xarray.DataArray` |
| Average treatment effect | `float(np.asarray(result.post_impact).mean())` |
| Cumulative effect | `result.post_impact_cumulative` |
| Fitted pre-period | `result.pre_pred` (numpy) |
| Counterfactual post-period | `result.post_pred` (numpy) |
| Inference data (PyMC only) | `result.idata` (arviz `InferenceData`) |

> **Gotcha**: `post_impact` is an xarray DataArray, not numpy. Naive
> `.mean()` returns another DataArray; convert with
> `.values.ravel()` or `np.asarray(...).ravel()` first.
>
> For PyMC posteriors, `post_impact` has a sample dimension. To get the
> posterior over the ATE: `post_impact.mean(dim="obs_ind").values.ravel()`
> — this collapses time but keeps draws.

## Plotting — the built-in `.plot()` is unreliable

CausalPy's `.plot()` works most of the time but breaks in several known
cases (constrained-layout + annotate arrays, seaborn column lookup
mismatches, etc.). When it crashes, hand-build the plot with matplotlib
directly — it's <20 lines for any design.

See [gotchas.md](reference/gotchas.md) for the specific failures and the
fallback plotting recipe.

## Universal gotchas (apply across designs)

1. **Treatment time type must match data index type.** `DatetimeIndex`
   data needs `treatment_time=pd.Timestamp(...)`. Integer index needs an
   integer. Silent miscoercion is possible.
2. **Patsy formula syntax**: `I(t**2)` for transformations, `C(col)` for
   categoricals, `np.sin(...)` and `np.cos(...)` work inside formulas.
   `np.log` works. `**` outside `I()` means interaction, not exponent.
3. **The data frame can have extra columns** — only what's in the formula
   gets used. But missing columns cause `PatsyError`.
4. **Index uniqueness matters for time-series designs**. Duplicate dates
   silently break the fit.

See [gotchas.md](reference/gotchas.md) for the full list with reproductions.

## Reference files

- [its.md](reference/its.md) — Interrupted Time Series cookbook
- [did.md](reference/did.md) — Difference-in-Differences cookbook
- [pymc-backend.md](reference/pymc-backend.md) — posterior extraction patterns
- [gotchas.md](reference/gotchas.md) — known bugs and workarounds

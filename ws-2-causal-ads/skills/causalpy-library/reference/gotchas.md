# CausalPy gotchas — known bugs and workarounds

Surfaced from real usage. Each entry: symptom → cause → fix.

## 1. `cp.skl_models.LinearRegression` does not exist

**Symptom:**
```
AttributeError: module 'causalpy.skl_models' has no attribute 'LinearRegression'
```

**Cause:** despite the symmetric API hint with `cp.pymc_models.LinearRegression`,
the sklearn integration goes through a different path.

**Fix:**
```python
from sklearn.linear_model import LinearRegression as SkLR
LinearRegressionCP = cp.create_causalpy_compatible_class(SkLR)
result = cp.InterruptedTimeSeries(..., model=LinearRegressionCP())
```

`cp.create_causalpy_compatible_class` is the public adapter. It accepts
any `sklearn.base.RegressorMixin` subclass (LinearRegression, Ridge,
ElasticNet, Lasso, RandomForestRegressor, etc.).

---

## 2. DiD constructor requires a `unit` column

**Symptom:**
```
DataException: Require a `unit` column to label unique units. This is used for plotting purposes
```

**Cause:** even though you pass `group_variable_name="treated"` explicitly,
the constructor *also* checks for a column literally named `unit`. Used
for plotting; validated at construction.

**Fix:** add it to your DataFrame before constructing:
```python
panel["unit"] = panel["market"]   # or any unique identifier
```

---

## 3. `did.plot()` crashes with a matplotlib annotate error

**Symptom:**
```
TypeError: only length-1 arrays can be converted to Python scalars
... in matplotlib/text.py ... _get_xy
... in _constrained_layout.py ... do_constrained_layout
```

**Cause:** CausalPy's `_ols_plot` uses `sns.lineplot(..., hue="group")`
which fails when the column is named differently than `group`. Even when
that's worked around (add `panel["group"] = panel["treated"]`), it can
still crash on the annotation positioning under constrained layout in
recent matplotlib.

**Fix:** add the `group` column AND, if it still crashes, hand-build the
plot. Recipe in [did.md](did.md#gotcha-2--didplot-crashes-on-recent-matplotlib).

---

## 4. `treatment_time` type must match data index type

**Symptom:** silent miscoercion — analysis runs but with the treatment
time set to day 0 or some other wrong value.

**Cause:** `treatment_time` is compared against the data index with `>=`.
If types differ (Timestamp vs int), the comparison silently misbehaves.

**Fix:**
```python
# DatetimeIndex data:
treatment_time = pd.Timestamp("2026-04-01")

# Integer index:
treatment_time = 730     # day number

# Float index:
treatment_time = 730.0
```

---

## 5. `post_impact` is an xarray DataArray, not numpy

**Symptom:** `.mean()` returns a DataArray; passing to `np.mean`,
`hist`, or plotting code with a numeric type expectation can confuse
downstream code.

**Fix:** convert explicitly.
```python
# sklearn backend (no sample dim)
post_effect = np.asarray(its.post_impact).ravel()
ate = float(post_effect.mean())

# PyMC backend (sample dim present)
ate_draws = its.post_impact.mean(dim="obs_ind").values.ravel()  # (n_samples,)
ate_mean = float(ate_draws.mean())
```

---

## 6. PyMC backend without `sample_kwargs` spams a progress bar

**Symptom:** notebook output filled with sampling progress lines.

**Fix:**
```python
model = cp.pymc_models.LinearRegression(
    sample_kwargs={"progressbar": False, "random_seed": 42}
)
```

Always pass these two minimum. Reproducibility matters for any
write-up.

---

## 7. `print(its)` does not draw a plot

**Symptom:** confusion — analyst expects a plot after `print(its)`
because some tutorials suggest CausalPy auto-displays.

**Reality:** `print(its)` calls `__repr__`, which returns the text
summary (formula, coefficients). To get a plot:

```python
fig, ax = its.plot()    # may crash for DiD, see gotcha #3
```

If you've built your own diagnostic plot (observed vs fitted vs
counterfactual), `its.plot()` is redundant — don't add both.

---

## 8. Patsy formula syntax gotchas

- `t**2` outside `I()` is interpreted as an interaction (not exponent).
  Always use `I(t**2)` for polynomial terms.
- `C(col)` for categorical. Default reference is the first level
  alphabetically; override with `C(col, Treatment("level"))`.
- `np.log`, `np.sin`, `np.cos` work inside the formula.
- `:` is interaction, `*` is interaction + main effects.
- Spaces matter less than parens; when in doubt, wrap.

---

## 9. Duplicate index entries silently break the fit

**Symptom:** model fits but counterfactual projection is nonsensical.

**Cause:** CausalPy doesn't deduplicate. Multiple rows with the same
index date confuse the design-matrix construction.

**Fix:** `df = df.groupby(df.index).first()` or aggregate appropriately
before fitting.

---

## 10. Default standard errors don't account for autocorrelation

**Symptom:** confidence intervals / HDIs are too narrow on time-series
or panel data.

**Cause:** OLS (sklearn) assumes iid errors. PyMC default is Normal-iid.
Both ignore that the same units repeat across time.

**Fix options:** report the limitation explicitly; bootstrap at block
level; use HAC corrections (statsmodels OLS, outside CausalPy); use
an AR(1) likelihood (custom PyMC model).

---

## How to file new gotchas here

When you hit a new one:

1. Write the **symptom** (the error message or unexpected behavior).
2. Write the **cause** in one sentence.
3. Write the **fix** as runnable code.
4. Add to this file in numbered order.

The point of this skill is that the next person doesn't waste 20 minutes
on the same trap.

# Using CausalPy's PyMC backend

The one-line swap from sklearn → PyMC gives you full posterior inference
over the causal effect. The cost: sampling time (3–30 sec for typical
models), and you have to remember a few PyMC-specific extraction patterns.

## When to switch from sklearn → PyMC

- You need a credible interval / uncertainty bounds, not just a point
- Leadership will ask "how confident are we?"
- You want to make probability statements: P(effect < 0), P(|effect| > X)
- You're comparing multiple specs and want to see which posteriors overlap
- You're doing a write-up and need to defend the precision claim

If a point estimate is enough (rough scoping, fast iteration, exploratory
work), stay on sklearn.

## The swap

```python
# Before (sklearn — point estimate only)
from sklearn.linear_model import LinearRegression as SkLR
LinearRegressionCP = cp.create_causalpy_compatible_class(SkLR)
its = cp.InterruptedTimeSeries(data=..., treatment_time=..., formula=...,
                                model=LinearRegressionCP())

# After (PyMC — full posterior)
its = cp.InterruptedTimeSeries(data=..., treatment_time=..., formula=...,
    model=cp.pymc_models.LinearRegression(
        sample_kwargs={
            "progressbar": False,    # silence — necessary for clean notebook output
            "random_seed": 42,       # reproducibility
            # Other useful kwargs:
            # "draws": 1000,         # default 1000 per chain
            # "tune": 1000,          # default 1000
            # "chains": 4,           # default 4
            # "target_accept": 0.95, # bump if you get divergences
        },
    ),
)
```

## Default priors (from `cp.pymc_models.LinearRegression`)

```
β ~ Normal(0, 50)
σ ~ HalfNormal(1)
μ = X · β
y ~ Normal(μ, σ)
```

These are weakly informative and OK for most problems. Override via the
`priors=` argument if your outcome scale demands it (e.g., for very small
rates the σ prior may be too loose).

## Extracting the posterior over the ATE

```python
# post_impact is an xarray DataArray with sample dim
# shape: (n_samples, n_post_days) — or (n_samples, n_post_days, n_units)
post_impact = its.post_impact

# Average over post-period time → per-draw ATE
ate_draws = post_impact.mean(dim="obs_ind").values.ravel()  # (n_samples,)
ate_mean = float(ate_draws.mean())

# 94% HDI
import arviz as az
ate_hdi = az.hdi(ate_draws, hdi_prob=0.94)
print(f"ATE = {ate_mean:+.5f}, 94% HDI = [{ate_hdi[0]:+.5f}, {ate_hdi[1]:+.5f}]")

# Probability statements
print(f"P(ATE < 0):      {float((ate_draws < 0).mean()):.3f}")
print(f"P(|ATE| > 1e-4): {float((np.abs(ate_draws) > 1e-4).mean()):.3f}")
```

## Plotting the posterior

```python
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(10, 4))
ax.hist(ate_draws, bins=40, color="tab:blue", alpha=0.6, edgecolor="white")
ax.axvline(ate_mean, color="tab:blue", lw=2, label="posterior mean")
ax.axvline(ate_hdi[0], color="tab:blue", lw=1, ls="--", alpha=0.7)
ax.axvline(ate_hdi[1], color="tab:blue", lw=1, ls="--", alpha=0.7, label="94% HDI")
ax.axvline(0, color="gray", lw=1)
ax.set_xlabel("ATE"); ax.set_ylabel("posterior draws")
ax.legend(); ax.grid(alpha=0.3)
```

## Diagnostics

The fitted result has an `idata` attribute that's an `arviz.InferenceData`
object. Use arviz tools directly:

```python
import arviz as az

# Convergence
az.summary(its.idata, var_names=["beta", "y_hat_sigma"])   # R-hat, ESS, etc.
az.plot_trace(its.idata, var_names=["beta"])

# Posterior predictive check
az.plot_ppc(its.idata)
```

If R-hat > 1.01 or ESS < 400, the sampler hasn't converged — bump `tune`
or `target_accept`.

## What you do NOT get for free

The default likelihood is **Normal-iid**. This is wrong for time series
where the same units persist across days (autocorrelated errors). The
resulting HDI is narrower than it should be.

To handle autocorrelation properly you need to:

- Use a state-space model (`cp.pymc_models.StateSpaceTimeSeries` —
  experimental in some versions), or
- Bootstrap the residuals at the block level, or
- Bake an AR(1) error structure into a custom PyMC model

The default workflow is honest about its assumption (Normal iid) — just
flag the limitation in your write-up rather than pretending the HDI
captures all uncertainty.

## Estimation vs model uncertainty

Make this explicit in any write-up that uses the PyMC backend:

- The HDI captures **estimation uncertainty** *given the model is correct*.
- It does NOT capture **model uncertainty** (what if the formula is wrong?).
- To capture model uncertainty, run multiple specifications and report
  the spread of their estimates.
- The `causal-critiquer` skill flags one-sided model-uncertainty
  discussions as Important findings.

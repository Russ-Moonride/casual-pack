import marimo

__generated_with = "0.23.4"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 02 - Decision Science & Uncertainty

    CausalPy so far handed us a **single number** for the effect. But a point estimate
    hides the one thing a decision-maker needs: *how sure are we?* A **Bayesian** model
    returns a full **distribution** over the effect. This notebook builds the intuition
    (prior -> posterior), gets the effect as a distribution in one line of CausalPy, and
    then asks the question that actually matters: **did we make more money?**
    """)
    return


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pandas as pd
    import causalpy as cp
    import matplotlib.pyplot as plt
    from scipy.stats import beta as beta_dist
    from sklearn.linear_model import LinearRegression

    return LinearRegression, beta_dist, cp, mo, np, pd, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Part A - A point estimate vs a distribution

    *App 1:* you run an experiment and observe a conversion rate. The **point estimate**
    (`k/n`) is the kind of answer an OLS fit gives. The **posterior distribution** is what
    a Bayesian gives - it widens when you have little data and tightens as data accrues.
    Drag the slider: the point estimate barely moves, but your actual knowledge changes a lot.
    """)
    return


@app.cell
def _(mo):
    n_obs = mo.ui.slider(5, 2000, value=30, label="observations (n)")
    n_obs
    return (n_obs,)


@app.cell
def _(beta_dist, n_obs, np, plt):
    _p_true = 0.30
    _n = n_obs.value
    _k = int(round(_n * _p_true))
    _a, _b = 1 + _k, 1 + _n - _k
    _xs = np.linspace(0, 0.6, 500)
    fig_a, ax_a = plt.subplots(figsize=(8, 3.4))
    ax_a.fill_between(_xs, beta_dist.pdf(_xs, _a, _b), alpha=0.3, color="C0")
    ax_a.plot(_xs, beta_dist.pdf(_xs, _a, _b), color="C0", lw=2, label=f"Bayesian posterior Beta({_a},{_b})")
    ax_a.axvline(_k/_n, color="C3", ls="--", lw=2, label=f"point estimate k/n = {_k/_n:.3f}")
    ax_a.set_yticks([]); ax_a.set_xlabel("conversion rate"); ax_a.legend(loc="upper right", fontsize=9)
    ax_a.set_title(f"n = {_n}:  same point estimate, very different certainty")
    fig_a
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Part A (cont.) - Prior -> Posterior

    *App 2:* a Bayesian answer starts from a **prior** (what you believed before) and
    updates it with **data** to get a **posterior**. With little data the prior dominates;
    as data grows the posterior is pulled toward what the data say. This updating *is* the
    engine behind the effect distribution CausalPy returns.
    """)
    return


@app.cell
def _(mo):
    prior_mean = mo.ui.slider(0.05, 0.95, 0.05, value=0.50, label="prior mean")
    prior_strength = mo.ui.slider(1, 200, value=6, label="prior strength (pseudo-obs)")
    data_n = mo.ui.slider(0, 800, value=40, label="data: number of trials")
    mo.vstack([prior_mean, prior_strength, data_n])
    return data_n, prior_mean, prior_strength


@app.cell
def _(beta_dist, data_n, np, plt, prior_mean, prior_strength):
    _p_true = 0.30
    _m, _s, _nd = prior_mean.value, prior_strength.value, data_n.value
    _a0, _b0 = _m*_s, (1-_m)*_s
    _kd = int(round(_nd*_p_true))
    _a1, _b1 = _a0+_kd, _b0+_nd-_kd
    _xs = np.linspace(0, 1, 500)
    fig_b, ax_b = plt.subplots(figsize=(8, 3.6))
    ax_b.plot(_xs, beta_dist.pdf(_xs, _a0, _b0), color="C7", ls="--", lw=2, label=f"prior Beta({_a0:.1f},{_b0:.1f})")
    ax_b.fill_between(_xs, beta_dist.pdf(_xs, _a1, _b1), alpha=0.3, color="C0")
    ax_b.plot(_xs, beta_dist.pdf(_xs, _a1, _b1), color="C0", lw=2, label=f"posterior Beta({_a1:.1f},{_b1:.1f})")
    ax_b.axvline(_p_true, color="C2", lw=1.5, label=f"true rate = {_p_true}")
    ax_b.set_yticks([]); ax_b.set_xlabel("conversion rate"); ax_b.legend(loc="upper right", fontsize=9)
    ax_b.set_title(f"{_nd} data points: posterior moves from prior toward the truth")
    fig_b
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Part B - The effect as a distribution (one line of CausalPy)

    Same interrupted time series as before (trim noisy start, 7-day anticipation guard,
    annual Fourier seasonality). The **only** change vs the sklearn run is the model:
    swap the OLS estimator for the **Bayesian** `cp.pymc_models.LinearRegression`. Same
    formula, one line - and now the effect is a full posterior, not a point.
    """)
    return


@app.cell
def _(np, pd):
    df = pd.read_csv("data/daily_aggregates_intervention.csv", parse_dates=["date"]).set_index("date")
    treatment_time = pd.Timestamp("2026-04-01")
    _guard_lo = treatment_time - pd.Timedelta(days=7)
    model_df = df[df.index >= "2024-07-01"].copy()
    model_df = model_df[(model_df.index < _guard_lo) | (model_df.index >= treatment_time)].copy()
    model_df["t"] = np.arange(len(model_df))
    _doy = model_df.index.dayofyear.values
    model_df["sin1"] = np.sin(2*np.pi*_doy/365.25)
    model_df["cos1"] = np.cos(2*np.pi*_doy/365.25)
    print(f"model_df: {len(model_df)} rows (pre {(model_df.index<treatment_time).sum()}, post {(model_df.index>=treatment_time).sum()})")
    return model_df, treatment_time


@app.cell
def _(LinearRegression, cp, model_df, np, treatment_time):
    its_bayes = cp.InterruptedTimeSeries(
        model_df, treatment_time, formula="conv_rate ~ 1 + t + sin1 + cos1",
        model=cp.pymc_models.LinearRegression(
            sample_kwargs={"draws": 1000, "tune": 1000, "chains": 4, "cores": 1, "random_seed": 42, "progressbar": False}),
    )
    its_ols = cp.InterruptedTimeSeries(
        model_df, treatment_time, formula="conv_rate ~ 1 + t + sin1 + cos1", model=LinearRegression())
    # posterior draws of the average treatment effect on conv_rate
    _pi = its_bayes.post_impact
    ate_draws = _pi.mean(dim=[d for d in _pi.dims if d not in ("chain", "draw")]).values.ravel()
    single_ate = its_ols.effect_summary().table.loc["average", "mean"]
    print(f"single value (OLS):     {single_ate:+.6f}")
    print(f"posterior mean (Bayes): {ate_draws.mean():+.6f}   sd {ate_draws.std():.6f}")
    print(f"95% credible interval:  [{np.percentile(ate_draws,2.5):+.6f}, {np.percentile(ate_draws,97.5):+.6f}]")
    print(f"P(effect < 0) = {(ate_draws < 0).mean():.3f}")
    return ate_draws, its_bayes, single_ate


@app.cell
def _(ate_draws, plt, single_ate):
    fig_pb, ax_pb = plt.subplots(figsize=(8.5, 3.8))
    ax_pb.hist(ate_draws, bins=45, density=True, color="C0", alpha=0.45, label="Bayesian posterior of ATE")
    ax_pb.axvline(single_ate, color="C3", ls="--", lw=2, label=f"single value (OLS) = {single_ate:.6f}")
    ax_pb.axvline(-0.000272, color="C2", lw=2, label="true ATE = -0.000272")
    ax_pb.axvline(0, color="0.4", lw=1)
    ax_pb.set_yticks([]); ax_pb.set_xlabel("average effect on conv_rate")
    ax_pb.legend(loc="upper left", fontsize=9)
    ax_pb.set_title("The single number is just the peak. The distribution is the decision-relevant object.")
    fig_pb
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Part C - But is that what we actually want to know?

    The effect distribution says **subscriptions went down**. Important - but it is a
    *proximate* metric, not the *decision* metric. The intervention was a **price hike**,
    so the real question is: **did we make more money?** Fewer subscriptions each worth
    more could easily be a net win. Let us check whether the price hike is even visible
    in the data, then put a distribution on the revenue impact.
    """)
    return


@app.cell
def _(pd, plt, treatment_time):
    _u = pd.read_csv("data/users_intervention.csv", parse_dates=["conversion_date"])
    _conv = _u[_u.converted == 1]
    P_old = _conv[_conv.conversion_date < treatment_time].price_at_conversion.mean()
    P_new = _conv[_conv.conversion_date >= treatment_time].price_at_conversion.mean()
    _monthly = _conv.groupby(_conv.conversion_date.dt.to_period("M"))["price_at_conversion"].mean()
    _monthly = _monthly.loc["2025-09":"2026-09"]
    fig_pc, ax_pc = plt.subplots(figsize=(8.5, 3.2))
    ax_pc.plot(_monthly.index.to_timestamp(), _monthly.values, marker="o", color="C4")
    ax_pc.axvline(treatment_time, color="red", ls="--", lw=1.5)
    ax_pc.set_ylabel("avg price at conversion ($)"); ax_pc.set_title(f"Yes - the price hike is in the data: ${P_old:.2f} -> ${P_new:.2f} (+{(P_new/P_old-1)*100:.0f}%)")
    fig_pc
    return P_new, P_old


@app.cell
def _(P_new, P_old, its_bayes, model_df, np, treatment_time):
    # post-period observed conversions and pool size
    _post = model_df[model_df.index >= treatment_time]
    _conv_obs = _post["conversions"].values
    _pool = _post["subscriber_pool"].values
    # counterfactual (no-hike) conv_rate draws from the Bayesian posterior
    _pp = its_bayes.post_pred["posterior_predictive"]["mu"]
    _cf_cr = _pp.stack(s=[d for d in _pp.dims if d != "obs_ind"]).transpose("s", "obs_ind").values
    _cf_conv = _cf_cr * _pool[None, :]
    # revenue: observed at new price (fixed), counterfactual at old price (uncertain)
    rev_obs = (_conv_obs * P_new).sum()
    rev_cf = (_cf_conv * P_old).sum(axis=1)
    revenue_uplift = rev_obs - rev_cf
    subs_obs = _conv_obs.sum(); subs_cf = _cf_conv.sum(axis=1)
    print(f"SUBSCRIPTIONS  observed {subs_obs:,.0f}  vs counterfactual {subs_cf.mean():,.0f}  ({(subs_obs/subs_cf.mean()-1)*100:+.1f}%)")
    print(f"REVENUE        observed ${rev_obs:,.0f}  vs counterfactual ${rev_cf.mean():,.0f}")
    print(f"REVENUE UPLIFT mean ${revenue_uplift.mean():,.0f}  95% [${np.percentile(revenue_uplift,2.5):,.0f}, ${np.percentile(revenue_uplift,97.5):,.0f}]")
    print(f"P(more money) = {(revenue_uplift > 0).mean():.3f}   (+{revenue_uplift.mean()/rev_cf.mean()*100:.1f}% revenue)")
    return rev_cf, revenue_uplift, subs_cf, subs_obs


@app.cell
def _(plt, revenue_uplift, subs_cf, subs_obs):
    fig_rev, (axr1, axr2) = plt.subplots(1, 2, figsize=(11, 3.6))
    axr1.hist(subs_obs/subs_cf*100 - 100, bins=40, density=True, color="C3", alpha=0.5)
    axr1.axvline(0, color="0.3", lw=1); axr1.set_yticks([]); axr1.set_xlabel("% change in subscriptions")
    axr1.set_title("Proximate metric: subscriptions DOWN")
    axr2.hist(revenue_uplift, bins=40, density=True, color="C2", alpha=0.5)
    axr2.axvline(0, color="0.3", lw=1); axr2.set_yticks([]); axr2.set_xlabel("revenue uplift ($, post period)")
    axr2.set_title("Decision metric: revenue UP")
    fig_rev.tight_layout(); fig_rev
    return


@app.cell(hide_code=True)
def _(mo, rev_cf, revenue_uplift, subs_cf, subs_obs):
    mo.md(f"""
    ## The decision-science takeaway

    | | effect | confidence |
    |---|---|---|
    | **Subscriptions** (proximate metric) | {(subs_obs/subs_cf.mean()-1)*100:+.1f}% | P(down) = {(subs_cf > subs_obs).mean():.2f} |
    | **Revenue** (decision metric) | +${{revenue_uplift.mean():,.0f}} ({revenue_uplift.mean()/rev_cf.mean()*100:+.1f}%) | P(more money) = {(revenue_uplift > 0).mean():.2f} |

    Three levels, each one closer to the actual decision:

    1. **A single number** (CausalPy OLS): the effect on `conv_rate` is `-0.000275`. Useful, but silent about confidence.
    2. **A distribution** (Bayesian, one line): the same effect with a 95% credible interval and `P(effect < 0) = 1.00`. Now we can *reason under uncertainty*.
    3. **The business quantity**: subscriptions fell ~15%, but each is worth ~32% more, so **revenue rose ~12% with ~100% probability**. The price hike was the right call - and the proximate metric pointed the *opposite* way.

    **The lesson:** causal inference answers *\"what was the effect on metric M\"*; decision science asks *\"which action maximizes the outcome we actually care about\"*. Those can have opposite signs. Carry the full **distribution** all the way through to the **money**, and decide on that.
    """)
    return


if __name__ == "__main__":
    app.run()

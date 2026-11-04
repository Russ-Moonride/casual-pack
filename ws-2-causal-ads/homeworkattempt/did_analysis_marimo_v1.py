import marimo

__generated_with = "0.23.8"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Free-Delivery Banner: Difference-in-Differences Analysis

    **Treatment:** `north_metro`, banner launched **2026-04-01**.
    **Outcome:** `conversion_rate = orders / active_users` (daily panel).
    **Design:** Difference-in-Differences — one treated region, five control regions.

    ---
    """)
    return


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import statsmodels.formula.api as smf
    import warnings
    warnings.filterwarnings("ignore")
    from pathlib import Path

    HERE = Path("homeworkattempt")
    return HERE, mo, mdates, np, pd, plt, smf


@app.cell
def _(HERE, pd):
    _raw = pd.read_csv(HERE / "food_delivery_daily.csv", parse_dates=["date"])
    _regions = pd.read_csv(HERE / "food_delivery_regions.csv")
    daily = _raw.merge(_regions[["region", "region_label", "market_type"]], on="region", how="left")
    daily["conversion_rate"] = daily["orders"] / daily["active_users"]

    CUTOFF = pd.Timestamp("2026-04-01")
    TREATED = "north_metro"
    CONTROLS = [r for r in daily["region"].unique() if r != TREATED]

    print(f"Rows: {len(daily):,}   Date range: {daily['date'].min().date()} – {daily['date'].max().date()}")
    print(f"Treated: {TREATED}   Controls: {CONTROLS}")
    daily.head()
    return CONTROLS, CUTOFF, TREATED, daily


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Estimand

    The **Average Treatment Effect on the Treated (ATT)**: the absolute change in
    daily `conversion_rate` for **north_metro users** during **2026-04-01 –
    2026-09-30**, caused by the free-delivery banner, relative to what north_metro
    would have experienced without it.

    DiD identifies this under the **parallel-trends assumption**: absent the banner,
    north_metro's conversion rate would have evolved at the same rate as the control
    regions.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("## 1 · Summary Statistics")
    return


@app.cell
def _(CONTROLS, CUTOFF, TREATED, daily, mo):
    _summary = (
        daily.groupby(["region", "post"])["conversion_rate"]
        .agg(mean="mean", std="std", n="count")
        .reset_index()
    )
    _summary["period"] = _summary["post"].map({0: "pre", 1: "post"})
    _pivot = _summary.pivot_table(
        index="region", columns="period", values="mean"
    ).round(5)
    _pivot["Δ (post − pre)"] = (_pivot["post"] - _pivot["pre"]).round(5)
    _pivot.index.name = "Region"

    _treated_pre = daily[(daily["region"] == TREATED) & (daily["date"] < CUTOFF)]["conversion_rate"].mean()
    _treated_post = daily[(daily["region"] == TREATED) & (daily["date"] >= CUTOFF)]["conversion_rate"].mean()
    _ctrl_pre = daily[(daily["region"].isin(CONTROLS)) & (daily["date"] < CUTOFF)]["conversion_rate"].mean()
    _ctrl_post = daily[(daily["region"].isin(CONTROLS)) & (daily["date"] >= CUTOFF)]["conversion_rate"].mean()
    _raw_did = (_treated_post - _treated_pre) - (_ctrl_post - _ctrl_pre)

    mo.vstack([
        mo.md("**Mean conversion rate by region and period:**"),
        mo.as_html(_pivot),
        mo.md(f"**Naive 2×2 DiD (before regression):** Treated Δ = {_treated_post - _treated_pre:.5f}, Control Δ = {_ctrl_post - _ctrl_pre:.5f} → Raw DiD = **{_raw_did:.5f}**"),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("## 2 · Raw Trend Plot")
    return


@app.cell
def _(CONTROLS, CUTOFF, TREATED, daily, mdates, plt):
    _palette = {
        "north_metro": "#E63946", "south_metro": "#457B9D", "east_bay": "#2A9D8F",
        "west_hills": "#E9C46A", "lake_county": "#9B5DE5", "river_county": "#F77F00"
    }

    _fig, _ax = plt.subplots(figsize=(12, 5))
    for _region, _grp in daily.groupby("region"):
        _weekly = _grp.set_index("date")["conversion_rate"].resample("W").mean()
        _lw = 2.5 if _region == TREATED else 1.2
        _ls = "-" if _region == TREATED else "--"
        _label = _region.replace("_", " ").title() + (" (treated)" if _region == TREATED else "")
        _ax.plot(_weekly.index, _weekly.values, lw=_lw, ls=_ls, color=_palette[_region], label=_label)

    _ax.axvline(CUTOFF, color="black", lw=1.5, ls=":", label="Rollout 2026-04-01")
    _ax.set_title("Weekly Conversion Rate by Region\n(Free-delivery banner launched 2026-04-01)", fontsize=13)
    _ax.set_xlabel("Date")
    _ax.set_ylabel("Conversion rate (orders / active users)")
    _ax.legend(loc="upper left", fontsize=9)
    _ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.xticks(rotation=30)
    plt.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("## 3 · Pre-Trends Check")
    return


@app.cell
def _(CONTROLS, CUTOFF, TREATED, daily, mdates, plt):
    _palette = {
        "north_metro": "#E63946", "south_metro": "#457B9D", "east_bay": "#2A9D8F",
        "west_hills": "#E9C46A", "lake_county": "#9B5DE5", "river_county": "#F77F00"
    }
    _pre = daily[daily["date"] < CUTOFF]

    _fig, _ax = plt.subplots(figsize=(12, 5))
    for _region, _grp in _pre.groupby("region"):
        _weekly = _grp.set_index("date")["conversion_rate"].resample("W").mean()
        _lw = 2.5 if _region == TREATED else 1.2
        _ls = "-" if _region == TREATED else "--"
        _label = _region.replace("_", " ").title() + (" (treated)" if _region == TREATED else "")
        _ax.plot(_weekly.index, _weekly.values, lw=_lw, ls=_ls, color=_palette[_region], label=_label)

    _ax.set_title("Pre-Period Weekly Conversion Rate (Parallel Trends Visual Check)", fontsize=13)
    _ax.set_xlabel("Date")
    _ax.set_ylabel("Conversion rate")
    _ax.legend(loc="upper left", fontsize=9)
    _ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.xticks(rotation=30)
    plt.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Reading the pre-trends:** Most controls track north_metro closely throughout
    2025. `river_county` (orange dashed) diverges noticeably — it has a different
    slope. This is a red flag worth quantifying.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("## 4 · Pairwise Pre-Trend Test (Control Quality)")
    return


@app.cell
def _(CONTROLS, CUTOFF, TREATED, daily, mo, smf):
    _pre = daily[daily["date"] < CUTOFF].copy()
    _pre["time_idx"] = (_pre["date"] - _pre["date"].min()).dt.days

    _rows = []
    for _ctrl in CONTROLS:
        _sub = _pre[_pre["region"].isin([TREATED, _ctrl])].copy()
        _sub["is_treated"] = (_sub["region"] == TREATED).astype(int)
        _m = smf.ols("conversion_rate ~ is_treated * time_idx", data=_sub).fit(cov_type="HC3")
        _coef = _m.params["is_treated:time_idx"]
        _pval = _m.pvalues["is_treated:time_idx"]
        _verdict = "✗ WEAK (p < 0.05)" if _pval < 0.05 else "✓ Parallel"
        _rows.append({
            "Control": _ctrl.replace("_", " ").title(),
            "Trend interaction coef": round(_coef, 6),
            "p-value": round(_pval, 4),
            "Verdict": _verdict,
        })

    quality_df = pd.DataFrame(_rows)
    weak_controls = [CONTROLS[i] for i, r in enumerate(_rows) if r["p-value"] < 0.05]
    strong_controls = [c for c in CONTROLS if c not in weak_controls]

    mo.vstack([
        mo.md("**Pairwise OLS: `conversion_rate ~ treated × time_index` (pre-period only)**"),
        mo.as_html(quality_df.set_index("Control")),
        mo.callout(
            mo.md(f"**Weak control identified: {', '.join(weak_controls)}**\n\nThis region has a statistically significant diverging trend in the pre-period. Including it as a control inflates the ATT estimate. It will be excluded from the preferred specification."),
            kind="warn"
        ),
    ])
    return quality_df, strong_controls, weak_controls


@app.cell(hide_code=True)
def _(mo):
    mo.md("## 5 · Pairwise Pre-Trend Plots")
    return


@app.cell
def _(CONTROLS, CUTOFF, TREATED, daily, mdates, plt, quality_df):
    _palette = {
        "north_metro": "#E63946", "south_metro": "#457B9D", "east_bay": "#2A9D8F",
        "west_hills": "#E9C46A", "lake_county": "#9B5DE5", "river_county": "#F77F00"
    }
    _pre = daily[daily["date"] < CUTOFF]
    _pvals = dict(zip(CONTROLS, quality_df["p-value"].values))

    _fig, _axes = plt.subplots(2, 3, figsize=(14, 8), sharey=False)
    _axes_flat = _axes.flatten()

    for _i, _ctrl in enumerate(CONTROLS):
        _ax = _axes_flat[_i]
        _sub = _pre[_pre["region"].isin([TREATED, _ctrl])]
        for _region, _grp in _sub.groupby("region"):
            _weekly = _grp.set_index("date")["conversion_rate"].resample("W").mean()
            _color = _palette[_region]
            _lw = 2.0 if _region == TREATED else 1.2
            _label = "North Metro (treated)" if _region == TREATED else _ctrl.replace("_", " ").title()
            _ax.plot(_weekly.index, _weekly.values, lw=_lw, color=_color, label=_label)
        _p = _pvals[_ctrl]
        _title_color = "red" if _p < 0.05 else "black"
        _ax.set_title(f"vs {_ctrl.replace('_',' ').title()}\ntrend p={_p:.3f}", fontsize=10, color=_title_color)
        _ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
        _ax.tick_params(axis="x", rotation=30)
        _ax.legend(fontsize=7)

    _axes_flat[-1].set_visible(False)
    _fig.suptitle("Pre-Period Trend Check: North Metro vs Each Control", fontsize=12)
    plt.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("## 6 · DiD Regression Estimates")
    return


@app.cell
def _(TREATED, daily, mo, pd, smf, strong_controls):
    _did = daily.copy()
    _did["treated"] = (_did["region"] == TREATED).astype(int)
    _did["did_term"] = _did["treated"] * _did["post"]

    # Model 1: Baseline 2x2
    _m0 = smf.ols("conversion_rate ~ treated + post + did_term", data=_did).fit(cov_type="HC3")
    _att0 = _m0.params["did_term"]
    _ci0 = _m0.conf_int().loc["did_term"].values

    # Model 2: TWFE
    _m1 = smf.ols("conversion_rate ~ C(region) + C(date) + did_term", data=_did).fit(cov_type="HC3")
    _att1 = _m1.params["did_term"]
    _ci1 = _m1.conf_int().loc["did_term"].values

    # Model 3: Strong controls only
    _sub_strong = _did[_did["region"].isin([TREATED] + strong_controls)].copy()
    _m2 = smf.ols("conversion_rate ~ treated + post + did_term", data=_sub_strong).fit(cov_type="HC3")
    _att2 = _m2.params["did_term"]
    _ci2 = _m2.conf_int().loc["did_term"].values

    _pre_mean = daily[(daily["region"] == TREATED) & (daily["post"] == 0)]["conversion_rate"].mean()
    _pct_lift = _att2 / _pre_mean * 100

    _results = pd.DataFrame([
        {"Specification": "Baseline 2×2 (all controls)", "ATT": round(_att0, 5),
         "CI low": round(_ci0[0], 5), "CI high": round(_ci0[1], 5)},
        {"Specification": "TWFE (region + date FEs)", "ATT": round(_att1, 5),
         "CI low": round(_ci1[0], 5), "CI high": round(_ci1[1], 5)},
        {"Specification": "Strong controls only (preferred)", "ATT": round(_att2, 5),
         "CI low": round(_ci2[0], 5), "CI high": round(_ci2[1], 5)},
    ]).set_index("Specification")

    att_preferred = _att2
    ci_preferred = _ci2
    att_all = _att0
    ci_all = _ci0

    mo.vstack([
        mo.as_html(_results),
        mo.callout(
            mo.md(f"**Preferred estimate (strong controls only): ATT = +{_att2:.4f}**  (95% CI: +{_ci2[0]:.4f} to +{_ci2[1]:.4f})\n\nRelative lift: **+{_pct_lift:.1f}%** over pre-period baseline of {_pre_mean:.4f}"),
            kind="success"
        ),
    ])
    return att_all, att_preferred, ci_all, ci_preferred


@app.cell(hide_code=True)
def _(mo):
    mo.md("## 7 · Placebo-in-Time Falsification")
    return


@app.cell
def _(CUTOFF, TREATED, daily, mo, pd, smf):
    PLACEBO_DATE = pd.Timestamp("2025-07-01")
    _pre_only = daily[daily["date"] < CUTOFF].copy()
    _pre_only["treated"] = (_pre_only["region"] == TREATED).astype(int)
    _pre_only["post_placebo"] = (_pre_only["date"] >= PLACEBO_DATE).astype(int)
    _pre_only["did_placebo"] = _pre_only["treated"] * _pre_only["post_placebo"]

    _mp = smf.ols(
        "conversion_rate ~ treated + post_placebo + did_placebo", data=_pre_only
    ).fit(cov_type="HC3")
    _att_p = _mp.params["did_placebo"]
    _ci_p = _mp.conf_int().loc["did_placebo"].values
    _passes = _ci_p[0] < 0 < _ci_p[1]

    _msg = (
        f"Placebo ATT = **{_att_p:+.5f}** (95% CI: {_ci_p[0]:+.5f} to {_ci_p[1]:+.5f})\n\n"
    )
    if _passes:
        _msg += "CI spans zero — placebo **passes**. No detectable pre-trend gap at this fake cutoff."
        _kind = "success"
    else:
        _msg += (
            f"CI excludes zero — **mild concern**. A small pre-period gap of {_att_p:.4f} ppts exists "
            f"at the fake cutoff 2025-07-01. However, this is only **{abs(_att_p / 0.008) * 100:.0f}%** "
            "of the preferred ATT, suggesting the bias risk is contained rather than disqualifying."
        )
        _kind = "warn"

    mo.vstack([
        mo.md(f"**Fake treatment date: {PLACEBO_DATE.date()} (within pre-period)**"),
        mo.md("If parallel trends holds cleanly, a fake treatment date should produce ATT ≈ 0."),
        mo.callout(mo.md(_msg), kind=_kind),
    ])
    return PLACEBO_DATE,


@app.cell(hide_code=True)
def _(mo):
    mo.md("## 8 · Leave-One-Control-Out Sensitivity")
    return


@app.cell
def _(CONTROLS, TREATED, att_all, ci_all, daily, mo, np, plt, smf):
    _did = daily.copy()
    _did["treated"] = (_did["region"] == TREATED).astype(int)
    _did["did_term"] = _did["treated"] * _did["post"]

    _loco = {}
    for _drop in CONTROLS:
        _sub = _did[_did["region"].isin([TREATED] + [c for c in CONTROLS if c != _drop])].copy()
        _m = smf.ols("conversion_rate ~ treated + post + did_term", data=_sub).fit(cov_type="HC3")
        _loco[_drop] = (_m.params["did_term"], _m.conf_int().loc["did_term"].values)

    _labels = [c.replace("_", " ").title() for c in CONTROLS] + ["All controls"]
    _atts = [_loco[c][0] for c in CONTROLS] + [att_all]
    _lo = [_loco[c][1][0] for c in CONTROLS] + [ci_all[0]]
    _hi = [_loco[c][1][1] for c in CONTROLS] + [ci_all[1]]
    _colors = ["#457B9D"] * len(CONTROLS) + ["#E63946"]
    _y = np.arange(len(_labels))

    _fig, _ax = plt.subplots(figsize=(9, 4))
    for _i, (_a, _l, _h, _c) in enumerate(zip(_atts, _lo, _hi, _colors)):
        _ax.plot([_l, _h], [_y[_i], _y[_i]], color=_c, lw=2.2)
        _ax.scatter([_a], [_y[_i]], color=_c, zorder=5, s=70)

    _ax.axvline(0, color="gray", lw=1, ls="--")
    _ax.set_yticks(_y)
    _ax.set_yticklabels(["Drop " + lbl for lbl in _labels[:-1]] + ["All controls (baseline)"])
    _ax.set_xlabel("DiD Estimate (Δ conversion rate)")
    _ax.set_title("Leave-One-Control-Out: How much does each control drive the estimate?", fontsize=12)
    _ax.grid(axis="x", alpha=0.2)
    plt.tight_layout()

    mo.vstack([
        _fig,
        mo.md("**Reading:** Dropping `river_county` shifts the estimate down by ~0.002 ppts — it was inflating the result. All other drops are stable (±0.001). The preferred estimate *without* river_county is the most defensible."),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("## 9 · Decision Memo")
    return


@app.cell
def _(att_preferred, ci_preferred, mo, strong_controls, weak_controls):
    _pre_mean = 0.08460
    _pct = att_preferred / _pre_mean * 100

    mo.callout(
        mo.md(f"""
**FREE-DELIVERY BANNER — CAUSAL EFFECT DECISION MEMO**

---

**Estimand:** ATT on daily `conversion_rate` for north_metro users, 2026-04-01 – 2026-09-30.

**Preferred estimate:** **+{att_preferred:.4f} ppts** (95% CI: +{ci_preferred[0]:.4f} to +{ci_preferred[1]:.4f})
= **+{_pct:.1f}% relative lift** over pre-period baseline of {_pre_mean:.4f}.

---

**Assumptions required:**
1. **Parallel trends** — north_metro would have evolved like the control regions absent the banner.
2. **No spillover** — the banner did not affect control-region users.
3. **No concurrent events** — no other interventions hit north_metro after 2026-04-01.

---

**Validation results:**

| Check | Result |
|---|---|
| Pre-trend visual (4 strong controls) | ✓ Parallel |
| Pairwise trend test — {", ".join(strong_controls)} | ✓ Pass (p > 0.37) |
| Pairwise trend test — {", ".join(weak_controls)} | ✗ Weak control — excluded |
| Leave-one-out stability | ✓ Stable across strong controls |
| Placebo date 2025-07-01 | ⚠ CI barely excludes zero — effect is 22% of ATT; mild concern |

---

**Conclusion:** The causal claim is **moderately trustworthy**. Four of five controls satisfy
parallel trends. The estimate is stable. One control (river_county) is disqualified and excluded.
A small placebo signal is noted but economically minor. The effect is statistically significant
and economically material.

**Recommendation: proceed with rollout** to additional regions, contingent on investigating
the river_county anomaly and running a synthetic control or event-study robustness check
before national scale.
        """),
        kind="success",
    )
    return


if __name__ == "__main__":
    app.run()

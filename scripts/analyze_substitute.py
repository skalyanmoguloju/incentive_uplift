"""Reproducible, aggregate feasibility audit; never modifies source data.

Requires numpy and pandas. Run from any directory with Python.
Outputs aggregate JSON only; no voter-level scores or targeting policies.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/substitute/doi-10.60600-yu-cgmwnw"
OUT = ROOT / "eda/substitute_analysis"
OUT.mkdir(parents=True, exist_ok=True)
ARMS = {0: "Control", 1: "Hawthorne", 2: "Civic Duty", 3: "Neighbors", 4: "Self"}


def sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -35, 35)))


def logistic_fit(x, y, max_iter=40):
    """Newton fit with backtracking; tiny ridge for numerical stability only."""
    beta = np.zeros(x.shape[1])
    ridge = np.eye(x.shape[1]) * 1e-6
    ridge[0, 0] = 0
    def objective(b):
        z = x @ b
        return np.sum(np.logaddexp(0, z) - y * z) + .5 * b @ ridge @ b
    for iteration in range(max_iter):
        p = sigmoid(x @ beta)
        gradient = x.T @ (p - y) + ridge @ beta
        hessian = x.T @ (x * (p * (1 - p))[:, None]) + ridge
        step = np.linalg.solve(hessian, gradient)
        scale = 1.
        old = objective(beta)
        while objective(beta - scale * step) > old + 1e-9 and scale > 1e-8:
            scale *= .5
        beta -= scale * step
        if np.max(np.abs(scale * step)) < 1e-7:
            return beta, iteration + 1
    raise RuntimeError("Logistic fit failed to converge")


def metrics(y, p):
    p = np.clip(p, 1e-12, 1 - 1e-12)
    ranks = pd.Series(p).rank(method="average").to_numpy()
    n1 = y.sum()
    n0 = len(y) - n1
    return {
        "auc": float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)),
        "log_loss": float(-np.mean(y * np.log(p) + (1-y) * np.log(1-p))),
        "brier": float(np.mean((p-y)**2)),
    }


def clustered_ols(x, y, groups):
    """OLS and household-clustered CR1 covariance, matching Stata regression."""
    bread = np.linalg.inv(x.T @ x)
    beta = bread @ x.T @ y
    scores = pd.DataFrame(x * (y - x @ beta)[:, None]).groupby(groups).sum().to_numpy()
    n, k = x.shape
    g = len(scores)
    covariance = bread @ (scores.T @ scores) @ bread * g/(g-1) * (n-1)/(n-k)
    return beta, covariance


def main():
    individual = SOURCE / "GerberGreenLarimer_APSR_2008_social_pressure.dta"
    household_file = SOURCE / "gerbergreenlarimer_apsr_2008_social_pressure_household_level_stata_output.csv"
    d = pd.read_stata(individual, convert_categoricals=False)
    h = pd.read_csv(household_file)
    with pd.io.stata.StataReader(individual) as reader:
        labels = reader.variable_labels()
    y = d.voted.to_numpy(dtype=float)
    a = d.treatment.to_numpy(dtype=int)
    assert set(np.unique(a)) == set(ARMS)
    assert set(np.unique(y)) == {0, 1}
    assert d.isna().sum().sum() == 0
    assert d.groupby("hh_id").treatment.nunique().max() == 1
    assert d.groupby("hh_id").cluster.nunique().max() == 1
    assert (d.groupby("hh_id").size() == d.groupby("hh_id").hh_size.first()).all()
    # Preserve fractional household IDs. Casting them to integers merges households.
    hh = d.groupby("hh_id").agg(
        treatment=("treatment", "first"), hh_size=("hh_size", "first"),
        sex=("sex", "mean"), yob=("yob", "mean"),
        **{v: (v, "mean") for v in ["g2000", "g2002", "p2000", "p2002", "p2004"]})
    reference = h.set_index("hh_id").sort_index()
    assert hh.index.equals(reference.index)
    # CSV household means are rounded, so compare using a declared tolerance.
    hh_delta = float(np.max(np.abs(hh[reference.columns].to_numpy() - reference.to_numpy())))
    assert hh_delta < 1e-3
    design = np.column_stack([np.ones(len(d))] + [(a == k).astype(float) for k in range(1, 5)])
    beta, cov = clustered_ols(design, y, d.hh_id)
    arm_stats = []
    for k, name in ARMS.items():
        mask = a == k
        entry = {"code": k, "arm": name, "individuals": int(mask.sum()),
                 "households": int(d.loc[mask, "hh_id"].nunique()),
                 "turnout_count": int(y[mask].sum()), "turnout_rate": float(y[mask].mean())}
        if k:
            se = np.sqrt(cov[k, k])
            entry.update(effect_pp=float(100*beta[k]), se_pp=float(100*se),
                         ci95_pp=[float(100*(beta[k]-1.96*se)), float(100*(beta[k]+1.96*se))])
        arm_stats.append(entry)
    # Independent check against the included authors' Table 3 model (a).
    assert np.allclose(beta[1:], [.0257363, .0178993, .0813099, .0485132], atol=1e-7)
    assert np.allclose(np.sqrt(np.diag(cov))[1:], [.0032579, .0032366, .0033696, .0033], atol=1e-7)
    features = ["sex", "yob", "hh_size", "g2000", "g2002", "p2000", "p2002", "p2004"]
    balance = []
    for k in range(1, 5):
        t, c = hh.loc[hh.treatment == k, features], hh.loc[hh.treatment == 0, features]
        smd = (t.mean() - c.mean()) / np.sqrt((t.var(ddof=1) + c.var(ddof=1))/2)
        balance.append({"arm": ARMS[k], "max_abs_smd": float(smd.abs().max()),
                        "smd_by_feature": smd.to_dict()})
    block_counts = d.drop_duplicates("hh_id").groupby(["cluster", "treatment"]).size().unstack(fill_value=0)

    # Academic modelability check: geography-block holdout keeps both household
    # members and whole randomization blocks together. No IDs in predictors.
    rng = np.random.default_rng(252)
    blocks = np.sort(d.cluster.unique())
    test_blocks = rng.choice(blocks, size=len(blocks)//5, replace=False)
    test = d.cluster.isin(test_blocks).to_numpy()
    train = ~test
    raw = d[features].astype(float).copy()
    raw["yob"] = 2006 - raw["yob"]
    raw = raw.rename(columns={"yob": "approx_age_2006"})
    raw["approx_age_squared"] = raw.approx_age_2006**2
    means = raw.loc[train].mean()
    sd = raw.loc[train].std(ddof=0)
    x = (raw - means).to_numpy() / sd.to_numpy()
    base = np.column_stack([np.ones(len(d)), x])
    additive = np.column_stack([base, design[:, 1:]])
    result_models = {}
    p0 = np.repeat(y[train].mean(), test.sum())
    result_models["constant"] = metrics(y[test], p0)
    predictions = {}
    for name, xx in [("features_only", base), ("features_and_assigned_arm", additive)]:
        b, iterations = logistic_fit(xx[train], y[train])
        p = sigmoid(xx[test] @ b)
        result_models[name] = {**metrics(y[test], p), "iterations": iterations}
        predictions[name] = p
    # Separate arm regressions are used only to audit held-out observed-outcome
    # fit. No counterfactual scores, rankings, policies, or individual exports.
    interacted = np.zeros(test.sum())
    test_a = a[test]
    for k in ARMS:
        b, _ = logistic_fit(base[train & (a == k)], y[train & (a == k)])
        interacted[test_a == k] = sigmoid(base[test & (a == k)] @ b)
    result_models["arm_specific_coefficients"] = metrics(y[test], interacted)
    def logloss_rows(p):
        return -(y[test]*np.log(p) + (1-y[test])*np.log1p(-p))
    loss_delta = logloss_rows(predictions["features_and_assigned_arm"]) - logloss_rows(interacted)
    # Mean paired held-out loss improvement, geographic-block robust SE.
    residual = loss_delta - loss_delta.mean()
    score = pd.Series(residual).groupby(d.loc[test, "cluster"].to_numpy()).sum().to_numpy()
    se = np.sqrt(len(score)/(len(score)-1) * np.sum(score**2)/len(loss_delta)**2)
    improvement = {"mean_log_loss_reduction": float(loss_delta.mean()),
                   "block_robust_ci95": [float(loss_delta.mean()-1.96*se), float(loss_delta.mean()+1.96*se)],
                   "interpretation": "Observed-outcome fit only; not a validation of CATE or uplift ranking."}

    profile = pd.read_json(ROOT / "data/raw/profile.json", lines=True)
    events = pd.read_json(ROOT / "data/raw/transcript.json", lines=True)
    portfolio = pd.read_json(ROOT / "data/raw/portfolio.json", lines=True)
    received = events.loc[events.event == "offer received", ["person", "time", "value"]].copy()
    received["offer_id"] = received.value.map(lambda v: v.get("offer id", v.get("offer_id")))
    received = received.merge(portfolio.rename(columns={"id": "offer_id"}), on="offer_id", validate="many_to_one")
    pair_counts = received.groupby(["person", "offer_id"]).size()
    # Correct source units: transcript hours, portfolio duration days.
    received["expiry"] = received.time + received.duration * 24
    overlap = 0
    overlap_people = set()
    for person, g in received.sort_values("time").groupby("person", sort=False):
        ends = []
        for row in g.itertuples():
            ends = [end for end in ends if end > row.time]
            if ends:
                overlap += 1
                overlap_people.add(person)
            ends.append(row.expiry)
    sb = {"customers": len(profile), "events": len(events), "offer_catalog_size": len(portfolio),
          "event_counts": events.event.value_counts().to_dict(),
          "customers_with_no_receipts": int((~profile.id.isin(received.person)).sum()),
          "receipt_waves_hours": received.groupby("time").size().to_dict(),
          "unique_customer_offer_pairs": len(pair_counts),
          "pairs_with_repeat_receipts": int((pair_counts > 1).sum()),
          "receipts_beyond_first_per_pair": int((pair_counts-1).sum()),
          "receipts_while_prior_offer_still_active": overlap,
          "customers_with_overlapping_offer_windows": len(overlap_people),
          "missing_gender": int(profile.gender.isna().sum()),
          "missing_income": int(profile.income.isna().sum()),
          "age_118_sentinel_count": int((profile.age == 118).sum()),
          "max_time_hours": int(events.time.max()),
          "note": "No-receipt customers alone do not establish a documented randomized control arm."}
    result = {
        "source": "https://dataverse.yale.edu/dataset.xhtml?persistentId=doi:10.60600/YU/CGMWNW",
        "source_sha256": hashlib.sha256(individual.read_bytes()).hexdigest(),
        "rows": len(d), "columns": len(d.columns), "variable_labels": labels,
        "missing": d.isna().sum().to_dict(), "nunique": d.nunique().to_dict(),
        "age_range_2006": [int(2006-d.yob.max()), int(2006-d.yob.min())],
        "identical_rows": int(d.duplicated().sum()),
        "duplicate_note": "No unique person ID; retain identical rows because household members can share all recorded attributes.",
        "fractional_household_ids": d.loc[d.hh_id % 1 != 0, "hh_id"].unique().tolist(),
        "household_csv_max_absolute_difference": hh_delta,
        "household_csv_has_outcome": "voted" in h.columns,
        "arms": arm_stats, "household_balance": balance,
        "randomization_blocks": len(block_counts),
        "block_household_count_distribution": block_counts.sum(axis=1).value_counts().to_dict(),
        "block_arm_minimum": block_counts.min().to_dict(),
        "model_features": list(raw.columns),
        "split": {"seed": 252, "train_rows": int(train.sum()), "test_rows": int(test.sum()),
                  "train_blocks": int(len(blocks)-len(test_blocks)), "test_blocks": len(test_blocks),
                  "household_overlap": int(len(set(d.loc[train,"hh_id"]) & set(d.loc[test,"hh_id"])))},
        "observed_outcome_models": result_models, "interaction_fit_improvement": improvement,
        "starbucks": sb,
        "limitations": ["Single exploratory geographic split, no hyperparameter search.",
                        "Strong prediction and average treatment effects do not establish useful heterogeneous effects.",
                        "Treatment CIs cluster by household and ignore block fixed effects, matching the source's model (a).",
                        "Neither model scores nor causal-effect targeting policies are saved."]
    }
    def normalize(obj):
        if isinstance(obj, dict):
            return {str(k): normalize(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [normalize(v) for v in obj]
        if isinstance(obj, np.generic):
            return obj.item()
        return obj
    result = normalize(result)
    (OUT / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ["arms", "household_balance", "split", "observed_outcome_models", "interaction_fit_improvement", "starbucks"]}, indent=2))


if __name__ == "__main__":
    main()

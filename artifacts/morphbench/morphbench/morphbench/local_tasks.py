"""CPU-only runnable surrogates of the peer scientific-ML tasks.

These implement a *research loop*: an agent proposes model/training
configurations, fits them, and is scored on a held-out test set. Each "unit"
is one model fit (or one training run for BM-05). The search space is
deliberately larger than the budget so that *how* an agent allocates its
experiments matters — which is exactly the axis BioML-Bench / nanochat measure.

Everything is deterministic (fixed seeds) and depends only on numpy + sklearn.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple

import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    if ra.std() == 0 or rb.std() == 0:
        return 0.0
    return float(np.corrcoef(ra, rb)[0, 1])


@dataclass
class LocalTask:
    """A runnable surrogate task with a config search space."""

    task_id: str
    config_space: List[Dict]
    evaluate: Callable[[Dict], float]        # returns validation score
    test_score: Callable[[Dict], float]      # returns held-out test metric
    higher_is_better: bool = True

    def __len__(self) -> int:
        return len(self.config_space)


# ---------------------------------------------------------------------------
# synthetic data generators
# ---------------------------------------------------------------------------
def _reg_data(n=600, d=20, seed=7):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, d))
    w = rng.normal(size=d)
    y = np.tanh(X @ w) + 0.4 * (X[:, :3] ** 2).sum(1) + 0.15 * rng.normal(size=n)
    idx = rng.permutation(n)
    ntr = int(0.7 * n)
    tr, te = idx[:ntr], idx[ntr:]
    return (X[tr], y[tr]), (X[te], y[te])


def _clf_data(n=800, d=18, classes=2, seed=11):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, d))
    w = rng.normal(size=(d, classes))
    logits = X @ w
    y = logits.argmax(1) if classes > 2 else (logits[:, 0] > 0).astype(int)
    X += 0.3 * y.reshape(-1, 1)  # slight class signal in features
    idx = rng.permutation(n)
    ntr = int(0.7 * n)
    tr, te = idx[:ntr], idx[ntr:]
    return (X[tr], y[tr]), (X[te], y[te])


def _img_data(n=700, seed=13):
    rng = np.random.default_rng(seed)
    side = 8
    X = np.zeros((n, side * side))
    y = rng.integers(0, 3, size=n)
    for i in range(n):
        img = rng.normal(scale=0.3, size=(side, side))
        r, c = rng.integers(1, side - 1, size=2)
        patch = 1.5 if y[i] == 0 else (-1.5 if y[i] == 1 else 0.0)
        if y[i] == 2:
            img += 1.2 * np.eye(side)
        img[r:r + 2, c:c + 2] += patch
        X[i] = img.reshape(-1)
    idx = rng.permutation(n)
    ntr = int(0.7 * n)
    tr, te = idx[:ntr], idx[ntr:]
    return (X[tr], y[tr]), (X[te], y[te])


# ---------------------------------------------------------------------------
# config-space builders
# ---------------------------------------------------------------------------
def _regressions():
    return [
        {"model": "ridge", "alpha": a, "feat": f}
        for a in (0.1, 1.0, 10.0) for f in ("none", "poly2")
    ] + [
        {"model": "rf", "n_estimators": n, "feat": "none"}
        for n in (50, 150, 300)
    ] + [
        {"model": "gbr", "n_estimators": n, "feat": "none"}
        for n in (50, 150, 300)
    ] + [{"model": "ridge", "alpha": 1.0, "feat": "pca"}]


def _classifiers():
    return [
        {"model": "logreg", "C": c} for c in (0.1, 1.0, 10.0)
    ] + [
        {"model": "rf", "n_estimators": n} for n in (50, 150, 300)
    ] + [
        {"model": "gbr", "n_estimators": n} for n in (50, 150, 300)
    ]


def _make_reg_model(cfg):
    if cfg["model"] == "ridge":
        steps = []
        if cfg["feat"] == "poly2":
            steps.append(("poly", PolynomialFeatures(2)))
        if cfg["feat"] == "pca":
            steps.append(("pca", PCA(n_components=10)))
        steps.append(("sc", StandardScaler()))
        steps.append(("m", Ridge(alpha=cfg["alpha"])))
        return Pipeline(steps)
    if cfg["model"] == "rf":
        return RandomForestRegressor(n_estimators=cfg["n_estimators"], random_state=0, n_jobs=1)
    return GradientBoostingRegressor(n_estimators=cfg["n_estimators"], random_state=0)


def _make_clf_model(cfg):
    if cfg["model"] == "logreg":
        return Pipeline([("sc", StandardScaler()),
                         ("m", LogisticRegression(C=cfg["C"], max_iter=500))])
    if cfg["model"] == "rf":
        return RandomForestClassifier(n_estimators=cfg["n_estimators"], random_state=0, n_jobs=1)
    if cfg["model"] == "knn":
        return Pipeline([("sc", StandardScaler()),
                         ("m", KNeighborsClassifier(n_neighbors=cfg.get("k", 5)))])
    return GradientBoostingClassifier(n_estimators=cfg["n_estimators"], random_state=0)


# ---------------------------------------------------------------------------
# task builders
# ---------------------------------------------------------------------------
def build_protein_fitness() -> LocalTask:
    rng = np.random.default_rng(3)
    (Xtr, ytr), (Xte, yte) = _reg_data()
    # 3-fold-ish validation slice carved from training data
    n = len(ytr); cut = int(0.7 * n)
    Xv, yv = Xtr[cut:], ytr[cut:]; Xf, yf = Xtr[:cut], ytr[:cut]

    def evaluate(cfg):
        m = _make_reg_model(cfg); m.fit(Xf, yf)
        return _spearman(m.predict(Xv), yv)

    def test_score(cfg):
        m = _make_reg_model(cfg); m.fit(Xtr, ytr)
        return _spearman(m.predict(Xte), yte)

    return LocalTask("BM-01", _regressions(), evaluate, test_score)


def build_drug_discovery() -> LocalTask:
    (Xtr, ytr), (Xte, yte) = _clf_data(classes=2, seed=11)
    n = len(ytr); cut = int(0.7 * n)
    Xv, yv = Xtr[cut:], ytr[cut:]; Xf, yf = Xtr[:cut], ytr[:cut]
    from sklearn.metrics import roc_auc_score

    def evaluate(cfg):
        m = _make_clf_model(cfg); m.fit(Xf, yf)
        p = m.predict_proba(Xv)[:, 1] if hasattr(m, "predict_proba") else m.predict(Xv)
        return float(roc_auc_score(yv, p))

    def test_score(cfg):
        m = _make_clf_model(cfg); m.fit(Xtr, ytr)
        p = m.predict_proba(Xte)[:, 1] if hasattr(m, "predict_proba") else m.predict(Xte)
        return float(roc_auc_score(yte, p))

    return LocalTask("BM-02", _classifiers(), evaluate, test_score)


def build_single_cell() -> LocalTask:
    (Xtr, ytr), (Xte, yte) = _clf_data(classes=4, seed=19)
    n = len(ytr); cut = int(0.7 * n)
    Xv, yv = Xtr[cut:], ytr[cut:]; Xf, yf = Xtr[:cut], ytr[:cut]
    from sklearn.metrics import accuracy_score

    def evaluate(cfg):
        m = _make_clf_model(cfg); m.fit(Xf, yf)
        return float(accuracy_score(yv, m.predict(Xv)))

    def test_score(cfg):
        m = _make_clf_model(cfg); m.fit(Xtr, ytr)
        return float(accuracy_score(yte, m.predict(Xte)))

    space = _classifiers() + [{"model": "knn", "k": k} for k in (3, 5, 9)]
    return LocalTask("BM-03", space, evaluate, test_score)


def build_imaging() -> LocalTask:
    (Xtr, ytr), (Xte, yte) = _img_data()
    n = len(ytr); cut = int(0.7 * n)
    Xv, yv = Xtr[cut:], ytr[cut:]; Xf, yf = Xtr[:cut], ytr[:cut]
    from sklearn.metrics import accuracy_score

    def evaluate(cfg):
        m = _make_clf_model(cfg); m.fit(Xf, yf)
        return float(accuracy_score(yv, m.predict(Xv)))

    def test_score(cfg):
        m = _make_clf_model(cfg); m.fit(Xtr, ytr)
        return float(accuracy_score(yte, m.predict(Xte)))

    space = _classifiers() + [{"model": "rf", "n_estimators": n} for n in (400, 600)]
    return LocalTask("BM-04", space, evaluate, test_score)


def build_gpt_hpo() -> LocalTask:
    """Surrogate of nanochat GPT training optimization.

    Each config is a training run; the surrogate objective mimics validation
    bits-per-byte (lower is better). We negate so the suite stays
    'higher-is-better' consistent.
    """
    def objective(cfg):
        lr = cfg["lr"]; wd = cfg["weight_decay"]; warm = cfg["warmup"]
        base = 1.05
        val = (base
               + 0.30 * (lr - 0.02) ** 2 / 0.02 ** 2
               + 0.12 * (wd - 0.1) ** 2
               + 0.08 * (warm - 0.05) ** 2 / 0.05 ** 2
               + 0.01 * np.sin(17 * lr) * np.cos(9 * wd))
        return -float(val)  # negate: higher better

    space = [
        {"lr": lr, "weight_decay": wd, "warmup": wm}
        for lr in (0.005, 0.01, 0.02, 0.03, 0.05)
        for wd in (0.0, 0.05, 0.1, 0.2)
        for wm in (0.0, 0.05, 0.1)
    ]
    # cached evaluation keeps it cheap + deterministic
    cache: Dict[Tuple, float] = {}

    def evaluate(cfg):
        key = (cfg["lr"], cfg["weight_decay"], cfg["warmup"])
        if key not in cache:
            cache[key] = objective(cfg)
        return cache[key]

    return LocalTask("BM-05", space, evaluate, evaluate)


BUILDERS: Dict[str, Callable[[], LocalTask]] = {
    "BM-01": build_protein_fitness,
    "BM-02": build_drug_discovery,
    "BM-03": build_single_cell,
    "BM-04": build_imaging,
    "BM-05": build_gpt_hpo,
}


def build(task_id: str) -> LocalTask:
    return BUILDERS[task_id]()

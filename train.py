import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from features import FEATURE_NAMES, extract_features, get_host

# ----------------------------- SETTINGS -----------------------------
# If your label column is numeric, which value means PHISHING?
#   PhiUSIIL (UCI/Kaggle): 0 = phishing, 1 = legitimate
#   UCI "Phishing Websites": -1 = phishing, 1 = legitimate
PHISHING_VALUE = 0
MAX_ROWS = 120000          # sample cap to keep training fast
RANDOM_STATE = 42
PHISH_WORDS = {"phishing", "phish", "bad", "malicious", "malware", "defacement", "spam", "unsafe"}
LEGIT_WORDS = {"legitimate", "legit", "good", "benign", "safe", "normal"}
# --------------------------------------------------------------------


def find_col(df, names):
    lower = {str(c).lower().strip(): c for c in df.columns}
    for n in names:
        if n in lower:
            return lower[n]
    return None


def to_binary(series):
    num = pd.to_numeric(series, errors="coerce")
    if num.notna().all():
        return (num == PHISHING_VALUE).astype(int)
    s = series.astype(str).str.strip().str.lower()
    unknown = set(s.unique()) - PHISH_WORDS - LEGIT_WORDS
    if unknown:
        sys.exit(f"Unknown label values {sorted(unknown)}. Add them to PHISH_WORDS or LEGIT_WORDS in train.py.")
    return s.isin(PHISH_WORDS).astype(int)


def evaluate(model, X_tr, y_tr, X_te, y_te):
    model.fit(X_tr, y_tr)
    pred = model.predict(X_te)
    tn, fp, fn, tp = confusion_matrix(y_te, pred, labels=[0, 1]).ravel()
    return {
        "accuracy": float(accuracy_score(y_te, pred)),
        "precision": float(precision_score(y_te, pred, zero_division=0)),
        "recall": float(recall_score(y_te, pred, zero_division=0)),
        "f1": float(f1_score(y_te, pred, zero_division=0)),
        "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }, model


BASE = Path(__file__).resolve().parent


def main():
    if len(sys.argv) > 1:
        path = Path(sys.argv[1]).expanduser()
    else:
        project_csvs = sorted(BASE.glob("*.csv"))
        data_csvs = sorted((BASE / "data").glob("*.csv")) if (BASE / "data").exists() else []
        csvs = project_csvs + data_csvs
        if not csvs:
            sys.exit("Put your CSV in the project root or inside the 'data' folder (or run: python train.py path/to/file.csv)")
        path = csvs[0]
    if not path.exists():
        path = (BASE / path).resolve() if not path.is_absolute() else path
    if not path.exists():
        sys.exit(f"File not found: {path}")

    print(f"Loading {path} ...")
    try:
        df = pd.read_csv(path, low_memory=False)
    except UnicodeDecodeError:
        df = pd.read_csv(path, low_memory=False, encoding="latin-1")
    print("Columns:", list(df.columns)[:15], "..." if df.shape[1] > 15 else "")

    url_col = find_col(df, ["url", "urls", "link", "links", "website"])
    label_col = find_col(df, ["label", "class", "result", "status", "type", "target", "phishing"])
    if label_col is None or label_col == url_col:
        label_col = [c for c in df.columns if c != url_col][-1]
    print(f"URL column  : {url_col}\nLabel column: {label_col}")

    subset = [label_col] + ([url_col] if url_col else [])
    df = df.dropna(subset=subset)
    if url_col:
        df = df.drop_duplicates(subset=[url_col])
    else:
        df = df.drop_duplicates()
    if len(df) > MAX_ROWS:
        df = df.sample(n=MAX_ROWS, random_state=RANDOM_STATE)
    df = df.reset_index(drop=True)

    y = to_binary(df[label_col]).reset_index(drop=True)
    if y.nunique() < 2:
        sys.exit("Only one class found after label conversion. Check PHISHING_VALUE at the top of train.py.")
    n_phish, n_legit = int((y == 1).sum()), int((y == 0).sum())
    print(f"Rows: {len(df)} | phishing={n_phish} | legitimate={n_legit}  <-- sanity-check these counts!")

    groups = None
    if url_col:
        mode = "url"
        print("Mode: URL (extracting lexical features, live scanning enabled) ...")
        urls = df[url_col].astype(str).tolist()
        X = pd.DataFrame([extract_features(u) for u in urls])[FEATURE_NAMES]
        groups = np.array([get_host(u) for u in urls])
    else:
        mode = "tabular"
        print("Mode: TABULAR (no URL column found; live URL scanning will be disabled)")
        X = df.drop(columns=[label_col]).select_dtypes(include=[np.number])
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.fillna(X.median()).fillna(0)
        if X.shape[1] == 0:
            sys.exit("No numeric feature columns found.")
    feature_names = list(X.columns)

    models = {
        "Logistic Regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)),
        "Decision Tree": DecisionTreeClassifier(max_depth=18, min_samples_leaf=2, random_state=RANDOM_STATE),
        "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=25, min_samples_leaf=2,
                                                n_jobs=-1, random_state=RANDOM_STATE),
    }

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE)

    results, fitted = {}, {}
    for name, model in models.items():
        print(f"Training {name} ...")
        results[name], fitted[name] = evaluate(model, X_tr, y_tr, X_te, y_te)
        r = results[name]
        print(f"   acc={r['accuracy']:.4f} prec={r['precision']:.4f} rec={r['recall']:.4f} f1={r['f1']:.4f}")

    # Generalisation test: test domains never seen in training
    domain_results = None
    if groups is not None and len(set(groups)) >= 10:
        try:
            tr, te = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=RANDOM_STATE).split(X, y, groups))
            if y.iloc[tr].nunique() == 2:
                domain_results = {name: evaluate(clone(m), X.iloc[tr], y.iloc[tr], X.iloc[te], y.iloc[te])[0]
                                  for name, m in models.items()}
                print("Domain-split evaluation done.")
        except Exception as exc:  # never let the optional test break training
            print("Domain-split skipped:", exc)

    best = max(results, key=lambda k: (results[k]["f1"], results[k]["recall"]))
    rf = fitted["Random Forest"]
    imp = sorted(zip(feature_names, rf.feature_importances_), key=lambda t: -t[1])[:12]

    Path("model").mkdir(exist_ok=True)
    joblib.dump({"models": fitted, "best": best, "features": feature_names, "mode": mode},
                "model/model.joblib", compress=3)
    metrics = {
        "ready": True, "mode": mode, "dataset": path.name, "rows": int(len(df)),
        "phishing": n_phish, "legitimate": n_legit, "n_features": len(feature_names),
        "models": results, "domain_split": domain_results, "best": best,
        "importances": [{"feature": f, "importance": float(v)} for f, v in imp],
    }
    Path("model/metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"\nDone. Best model by F1: {best}. Now run: python app.py")


if __name__ == "__main__":
    main()
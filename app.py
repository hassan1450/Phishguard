import json
from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, jsonify, render_template, request

from features import explain, extract_features

BASE = Path(__file__).resolve().parent
app = Flask(__name__, template_folder=str(BASE), static_folder=str(BASE), static_url_path="/static")

bundle, metrics = None, {"ready": False}


def load_artifacts():
    global bundle, metrics
    mp, jp = BASE / "model" / "model.joblib", BASE / "model" / "metrics.json"
    if mp.exists() and jp.exists():
        bundle = joblib.load(mp)
        metrics = json.loads(jp.read_text(encoding="utf-8"))
        print(f"Loaded model bundle (best: {bundle['best']}, mode: {bundle['mode']})")
    else:
        print("No trained model found. Run: python train.py")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/metrics")
def api_metrics():
    return jsonify(metrics)


@app.route("/api/predict", methods=["POST"])
def api_predict():
    if bundle is None:
        return jsonify({"error": "Model not trained yet. Run 'python train.py' first."}), 503
    if bundle["mode"] != "url":
        return jsonify({"error": "Your dataset has no URL column, so live URL scanning is disabled. "
                                 "Use a dataset with a URL column (e.g. PhiUSIIL)."}), 400
    data = request.get_json(silent=True) or {}
    url = str(data.get("url", "")).strip()
    if not url:
        return jsonify({"error": "Please enter a URL."}), 400
    if len(url) > 2048:
        return jsonify({"error": "URL is too long (max 2048 characters)."}), 400

    feats = extract_features(url)
    row = pd.DataFrame([feats], columns=bundle["features"])
    out = {}
    for name, model in bundle["models"].items():
        p = float(model.predict_proba(row)[0][1])
        out[name] = {"risk": round(p * 100, 1), "label": "Phishing" if p >= 0.5 else "Legitimate"}

    risk = out[bundle["best"]]["risk"]
    if risk < 30:
        verdict, level = "Looks legitimate", "safe"
    elif risk < 60:
        verdict, level = "Suspicious, be careful", "warn"
    else:
        verdict, level = "Likely phishing", "danger"

    return jsonify({"url": url, "risk": risk, "verdict": verdict, "level": level,
                    "best": bundle["best"], "models": out, "signals": explain(feats)})


load_artifacts()

if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=5000)
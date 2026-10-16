# PhishGuard

PhishGuard is a Flask-based research prototype that estimates phishing risk from URL structure. It extracts lexical URL features and displays predictions from trained machine-learning models alongside explainable URL warning signals.

> **Important:** This is an experimental tool, not a guarantee that a URL is safe or malicious. Do not rely on it as your only security control. The scanner analyzes the URL string and does not visit the submitted website.

## Features

- URL risk scoring through a Flask API.
- Human-readable URL warning signals.
- Model Lab showing model metrics and feature importances.
- Training workflow for a labeled CSV dataset.
- Render deployment configuration.

## Project structure

Keep these files at the repository root. The Flask app is configured to serve `index.html`, `style.css`, and `script.js` from this location.

```text
phishingdetector/
├── app.py
├── features.py
├── index.html
├── script.js
├── style.css
├── train.py
├── requirements.txt
├── render.yaml
├── README.md
└── model/
    ├── metrics.json
    └── model.joblib
```

The trained model files are required at runtime. The training dataset (`phidata.csv`) is not required to run the deployed app and is excluded from Git by `.gitignore`. Obtain a dataset separately if you want to retrain the models, and verify its license and label meanings first.

## Run locally on Windows

Use Python 3.10 or newer.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000>. The built-in Flask server is for local development only; Render uses Gunicorn.

### Retrain the models

Place a correctly labeled CSV in the project root, then run:

```powershell
python train.py .\your-dataset.csv
```

The training script writes updated model artifacts to `model/`. Check the dataset's label mapping in `train.py` before training, especially `PHISHING_VALUE`, and verify the printed phishing and legitimate counts.

## Deploy to Render

1. Create a GitHub repository and push this project.
2. Include the `model/` directory and its two files. Do not include `.venv/`, `__pycache__/`, or the training CSV.
3. In Render, choose **New → Blueprint**, connect the GitHub repository, and apply the Blueprint.
4. Render reads `render.yaml`, installs `requirements.txt`, and starts the app with Gunicorn.
5. When deployment completes, open the Render service URL. Check `<your-service-url>/api/metrics` to confirm the model is loaded.

The Blueprint currently uses Render's free web-service plan, where available. Free services can sleep after inactivity, so the first request afterward may take longer.

## Push from PowerShell

After creating an empty repository on GitHub, replace the URL below with your repository URL:

```powershell
cd C:\Users\Dell\Desktop\phishingdetector
git init
git add .
git status
git commit -m "Prepare PhishGuard for deployment"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

Review `git status` before committing to make sure no private files or datasets are included. If the repository already exists locally or the remote is already configured, do not repeat the corresponding setup command.

## API

### `GET /api/metrics`

Returns model readiness and evaluation metrics.

### `POST /api/predict`

Request JSON:

```json
{
  "url": "https://example.com/login"
}
```

Returns the estimated risk, verdict, individual model predictions, and URL warning signals. The app limits submitted URLs to 2,048 characters.

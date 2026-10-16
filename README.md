PhishGuard: Machine-Learning-Based Phishing URL Detection

PhishGuard is a Flask-based web application that estimates phishing risk from URL structure using trained machine-learning models and lexical URL feature extraction. It provides risk assessments, individual model predictions, and human-readable URL warning signals through a web interface and HTTP API.

Project Type: Cybersecurity and Machine-Learning Research Prototype

Project Status: Developed for local use.

Features
URL Risk Analysis: Estimates phishing risk using lexical characteristics extracted from submitted URLs.
Machine-Learning Predictions: Uses trained models to classify URLs and estimate risk.
Explainable Warning Signals: Displays human-readable indicators of potentially suspicious URL characteristics.
Model Lab: Displays model evaluation metrics and feature importances.
Flask API: Provides endpoints for model metrics and URL prediction.
Model Training: Supports retraining with a properly labeled CSV dataset.
Web Interface: Provides a browser-based interface built with HTML, CSS, and JavaScript.

PhishGuard analyzes submitted URL strings without visiting the corresponding websites or independently verifying their live content, reputation, or behavior.

Technology Stack
Technology	Purpose
Python	Application logic, feature processing, and model integration
Flask	Web application and HTTP API
Machine-learning libraries	Model training and inference
HTML	Web interface structure
CSS	Frontend styling and layout
JavaScript	Client-side interactions and API communication
Joblib	Loading serialized model artifacts, if used
Git and GitHub	Source control and project hosting

The exact machine-learning algorithms and dependency versions are defined by the implementation and requirements.txt.

Repository Structure
phishingdetector/
├── app.py                 # Flask application and API endpoints
├── features.py            # URL feature extraction
├── index.html             # Web interface
├── script.js              # Frontend logic and API requests
├── style.css              # Frontend styling and layout
├── train.py               # Model training workflow
├── requirements.txt       # Python dependencies
├── README.md              # Project documentation
└── model/
    ├── metrics.json       # Model evaluation metrics
    └── model.joblib       # Trained model artifact


The model/ directory contains the trained artifacts required to run the application. A training dataset, such as phidata.csv, is not required for normal execution when the trained model artifacts are already available.

Keep virtual environments, cache files, credentials, private configuration, and datasets that should not be distributed out of the project repository.

Installation and Setup
Requirements
Python 3.10 or newer
pip
Git
Compatible Python dependencies listed in requirements.txt
Required trained model artifacts in the model/ directory
1. Clone the Repository
git clone https://github.com/hassan1450/Phishguard.git
cd Phishguard

2. Create a Virtual Environment

For Windows PowerShell:

py -m venv .venv
.\.venv\Scripts\Activate.ps1


If PowerShell prevents environment activation, use the virtual environment's Python executable directly or follow your system's Python environment policy.

3. Install Dependencies
python -m pip install -r requirements.txt

4. Run the Application

Start the Flask application using app.py:

python app.py


Once the application starts successfully, open the local address displayed in the terminal. If the Flask application uses its default configuration, open:

http://127.0.0.1:5000


The application runs on your local computer for testing and development.

API Endpoints
GET /api/metrics

Returns model readiness information and evaluation metrics.

POST /api/predict

Accepts a URL and returns a risk assessment, verdict, individual model predictions, and URL warning signals, according to the application's implementation.

Example request body:

{
  "url": "https://example.com/login"
}


Example request using cURL:

curl -X POST http://127.0.0.1:5000/api/predict \
  -H "Content-Type: application/json" \
  -d "{\"url\":\"https://example.com/login\"}"


The application limits submitted URLs to 2,048 characters. Actual response fields and risk-score interpretation depend on the implementation in app.py.

Model Training

PhishGuard includes a training workflow for updating its machine-learning models using a labeled CSV dataset.

Training Requirements
A dataset in the format expected by train.py
Correctly labeled phishing and legitimate URL samples
Python dependencies required by the training workflow
Training Command

Place your dataset in the project directory and run:

python train.py .\your-dataset.csv


The script writes updated model artifacts to the model/ directory.

Before training, inspect train.py to verify the expected column names, label mapping, and PHISHING_VALUE setting. Check the resulting sample counts and evaluation metrics, and verify that the dataset's license permits your intended use.

Evaluate model performance on appropriate held-out data. Strong results on a single dataset do not guarantee reliable detection of previously unseen phishing URLs.

Security Considerations and Limitations
URL structure alone cannot identify every phishing attack.
Predictions may incorrectly classify legitimate URLs or fail to detect malicious ones.
The application analyzes submitted URL strings rather than browsing websites.
Avoid submitting passwords, authentication tokens, or other sensitive information.
Keep private datasets, credentials, .env files, and local virtual environments out of public commits.
Treat serialized model artifacts as trusted project files and only load artifacts from sources you trust.
Use additional security controls and independent verification before deciding whether a URL is safe.

PhishGuard is an experimental detection tool, not a guarantee that a URL is safe or malicious. Do not use it as your only security control.

Learning Goals

This project demonstrates practical concepts in:

Machine-learning-based phishing URL classification
Lexical URL feature engineering
Model training, evaluation, and inference
Explainable risk indicators
Flask application development and HTTP API design
Frontend-to-backend communication
Model artifact management
Version control and software development workflows
Future Improvements
Add screenshots of the web interface.
Create a demonstration video showing local execution.
Document the specific algorithms and model evaluation results.
Expand testing using diverse phishing and legitimate URL datasets.
Add automated unit and integration tests.
Improve API error handling and input validation.
Add continuous integration for testing changes.
Document reproducible training configurations and dependency versions.
Evaluate detection quality on independently sourced, held-out datasets.
Author

NOOR UL HASSAN

GitHub: https://github.com/hassan1450

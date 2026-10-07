# PhishGuard AI

## Deep Learning Based Phishing URL Detection System

PhishGuard AI is a full-stack academic cybersecurity application that analyzes a URL string and predicts whether it is:

- **LEGITIMATE** - lower model risk probability
- **SUSPICIOUS** - intermediate risk probability
- **PHISHING** - higher model risk probability

The primary machine-learning task is binary classification:

```text
0 = Legitimate
1 = Phishing
```

The application converts the neural-network probability into a user-facing risk category:

| Risk score | Application label |
|---:|---|
| 0% to less than 30% | LOW / LEGITIMATE |
| 30% to less than 70% | MEDIUM / SUSPICIOUS |
| 70% to 100% | HIGH / PHISHING |

> **Important:** A legitimate prediction is an AI prediction, not a guarantee that a URL is safe. The service analyzes URL text and metadata only; it never opens, crawls, or executes a submitted URL.

---

## Table of contents

1. [Project goals](#project-goals)
2. [Dataset used](#dataset-used)
3. [How the system works](#how-the-system-works)
4. [Feature engineering](#feature-engineering)
5. [Deep-learning model](#deep-learning-model)
6. [Project structure](#project-structure)
7. [Technology stack](#technology-stack)
8. [Installation](#installation)
9. [Training and evaluation](#training-and-evaluation)
10. [Running the application](#running-the-application)
11. [API documentation](#api-documentation)
12. [Database design](#database-design)
13. [Authentication and security](#authentication-and-security)
14. [Testing](#testing)
15. [Limitations](#limitations)
16. [Future scope](#future-scope)

## Project goals

The project connects the complete machine-learning and application workflow:

```text
Labelled URL CSV
      |
Data cleaning and validation
      |
URL feature extraction
      |
Stratified train/validation/test split
      |
Training-only feature scaling
      |
TensorFlow/Keras ANN training
      |
Evaluation and saved model artifacts
      |
FastAPI prediction service
      |
React frontend and SQLite scan history
```

The project is designed for an academic demonstration and as a foundation for a larger phishing-analysis product. It does not claim to replace a browser security system, threat-intelligence platform, or security analyst.

## Dataset used

### Dataset currently included in this repository

The repository contains [`ml/data/raw/urls.csv`](./ml/data/raw/urls.csv). This is a **small synthetic demonstration/test dataset created for validating the pipeline**. It is not presented as a real-world benchmark dataset and should not be used to claim production accuracy.

Dataset details:

| Property | Value |
|---|---|
| File | `ml/data/raw/urls.csv` |
| Format | CSV |
| Columns | `url`, `label` |
| Labels | `0` legitimate, `1` phishing |
| Rows | 20 demonstration URLs |
| Classes | 10 legitimate and 10 phishing examples |
| External crawling | None |
| Licensing status | Synthetic project test data; no third-party dataset license is claimed |

The examples include ordinary HTTPS domains for the legitimate class and deliberately suspicious-looking URL structures for the phishing class. They are useful for checking that the code runs, but they are too small and intentionally separable for meaningful generalization claims.

### Using a real dataset

For an academic or production evaluation, replace the demonstration CSV with a properly licensed public dataset. The file must contain at least:

```csv
url,label
https://trusted-example.org,0
http://known-example.test/login,1
```

Recommended data requirements:

- Confirm that redistribution and research use are allowed by the dataset license.
- Keep the original dataset citation and version in your experiment notes.
- Remove or document duplicate URLs.
- Verify that labels are normalized to `0` and `1`.
- Do not mix private, confidential, or unlawfully collected data into this repository.
- Avoid reporting metrics from the demonstration CSV as if they represented a real phishing benchmark.

The training loader accepts `0`, `1`, `legitimate`, and `phishing` labels. It removes missing rows, duplicate URLs, unsupported URL strings, and invalid labels before splitting.

## How the system works

### 1. Registration and login

The user registers with a name, email, and password. The backend hashes the password with bcrypt and stores only the hash in SQLite. Login returns a signed JWT access token.

### 2. URL submission

The frontend sends a URL to `POST /api/predict`. FastAPI validates that it is an HTTP or HTTPS URL using Pydantic.

### 3. Safe feature extraction

The shared feature extractor parses the URL string. It does not make a network request and does not visit the hostname.

### 4. Neural-network inference

The backend loads:

- `phishing_model.keras`
- `scaler.pkl`
- `feature_config.json`

It creates the feature vector in the same order used during training, applies the training-fitted scaler, and passes the vector to the Keras model.

### 5. Risk conversion

The sigmoid output is a phishing probability. The backend converts it into a percentage risk score and the LOW, MEDIUM, or HIGH category.

### 6. Explanation and history

The response contains rule-based URL indicators such as HTTP usage, an IP address, suspicious keywords, or a suspicious top-level domain. These indicators are intentionally labelled as **rule-based indicators**; they are not claimed to be causal explanations of the neural network.

The result is stored in the `scans` table and becomes available in history and analytics endpoints.

## Feature engineering

The fixed feature order is defined in [`backend/app/services/feature_extractor.py`](./backend/app/services/feature_extractor.py) and saved to `backend/model/feature_config.json`:

| Feature | Description |
|---|---|
| `url_length` | Total URL character count |
| `hostname_length` | Hostname character count |
| `path_length` | Path character count |
| `query_length` | Query-string character count |
| `dot_count` | Number of dots |
| `hyphen_count` | Number of hyphens |
| `underscore_count` | Number of underscores |
| `slash_count` | Number of slashes |
| `digit_count` | Number of numeric characters |
| `special_char_count` | Number of non-alphanumeric URL symbols |
| `subdomain_count` | Number of subdomains |
| `has_https` | Whether the scheme is HTTPS |
| `has_ip` | Whether the hostname is an IP address |
| `has_at_symbol` | Whether the URL contains `@` |
| `has_encoded_char` | Whether percent-encoded characters are present |
| `has_suspicious_port` | Whether a non-standard port is present |
| `suspicious_keyword_count` | Count of terms such as login, verify, account, or password |
| `domain_entropy` | Shannon entropy of the hostname |
| `has_suspicious_tld` | Whether the TLD is in the configured suspicious-TLD list |

Keywords and TLDs are indicators, not proof of malicious intent. A legitimate website can contain a keyword, use a long URL, or use a non-standard structure.

## Deep-learning model

The primary model is a feed-forward artificial neural network:

```text
Input: 19 engineered URL features
  |
Dense(128, ReLU)
BatchNormalization
Dropout(0.30)
  |
Dense(64, ReLU)
Dropout(0.20)
  |
Dense(32, ReLU)
  |
Dense(1, Sigmoid)
```

Training configuration:

- Loss: binary cross entropy
- Optimizer: Adam
- Reproducibility seed: `42`
- Split: 70% training, 15% validation, 15% test
- Split method: stratified
- Callbacks: early stopping, best-model checkpoint, and learning-rate reduction
- Scaling: `StandardScaler`, fitted only on training data

The model is intentionally not committed to GitHub because generated binary artifacts can be large and can be reproduced from the dataset. Running the training command creates the model artifacts locally.

## Project structure

```text
PhishGuard-AI/
|
|-- backend/
|   |-- app/
|   |   |-- __init__.py
|   |   |-- main.py                 FastAPI application and CORS setup
|   |   |-- config.py               Environment-backed settings
|   |   |-- api.py                  Auth, prediction, history, analytics, admin routes
|   |   |-- database.py             SQLAlchemy engine and session dependency
|   |   |-- models.py               User and Scan database models
|   |   |-- schemas.py               Pydantic request/response schemas
|   |   |-- security.py              Password hashing and JWT authorization
|   |   `-- services/
|   |       |-- feature_extractor.py Shared URL feature extraction and indicators
|   |       `-- predictor.py          Model loading and inference service
|   |-- tests/
|   |   `-- test_features.py         Feature extraction tests
|   |-- requirements.txt             Backend and ML dependencies
|   `-- .env.example                 Environment variable template
|
|-- ml/
|   |-- data/raw/urls.csv            Demonstration labelled dataset
|   |-- feature_extraction.py        Shared ML-to-backend feature import
|   |-- train.py                     Data preparation and ANN training
|   `-- evaluate.py                  Saved-model metrics and plots
|
|-- frontend/
|   |-- src/main.jsx                 React scanner UI
|   |-- src/styles.css               Responsive cybersecurity styling
|   |-- index.html                   Vite entry page
|   |-- package.json                 Frontend scripts and dependencies
|   `-- package-lock.json             Locked npm dependency versions
|
|-- docs/
|   |-- api_documentation.md         API examples
|   `-- project_report.md             Academic project report
|
|-- README.md
`-- .gitignore
```

Generated files are ignored by `.gitignore`, including virtual environments, database files, model binaries, plots, frontend build output, and dependency directories.

## Technology stack

### Machine learning

- Python 3.11+
- TensorFlow/Keras
- Pandas
- NumPy
- Scikit-learn
- Matplotlib
- Seaborn

### Backend

- FastAPI
- Uvicorn
- Pydantic
- SQLAlchemy
- SQLite for local development
- JWT and bcrypt authentication

### Frontend

- React
- Vite
- Responsive CSS

The database access is isolated behind SQLAlchemy models and sessions so it can later be migrated to PostgreSQL by changing the database configuration.

## Installation

### Prerequisites

- Python 3.11 or newer
- Node.js and npm
- Git

### Backend setup on Windows PowerShell

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Change `PHISHGUARD_SECRET_KEY` in `.env` to a long random value before using the application outside local development.

### Frontend setup

```powershell
cd frontend
npm install
```

If the API is hosted somewhere other than `http://localhost:8000`, set:

```powershell
$env:VITE_API_URL = "http://localhost:8000"
```

## Training and evaluation

Run these commands from the repository root:

```powershell
python ml\train.py --input ml\data\raw\urls.csv --epochs 30 --batch-size 32
python ml\evaluate.py --data ml\data\raw\urls.csv
```

Training creates these local files in `backend/model/`:

```text
phishing_model.keras
scaler.pkl
feature_config.json
metrics.json
```

Evaluation creates:

```text
confusion_matrix.png
roc_curve.png
```

`metrics.json` is generated from the selected test split. Accuracy, precision, recall, F1-score, and ROC-AUC must not be copied from the demonstration run into an academic report without clearly identifying the dataset and experiment.

## Running the application

Start the backend:

```powershell
cd backend
..\.venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Start the frontend in a second terminal:

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

- Frontend: `http://127.0.0.1:5173`
- Backend health: `http://127.0.0.1:8000/api/health`
- Interactive API documentation: `http://127.0.0.1:8000/docs`

## API documentation

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/health` | No | Service health check |
| `POST` | `/api/auth/register` | No | Create a user |
| `POST` | `/api/auth/login` | No | Return a JWT access token |
| `POST` | `/api/predict` | User | Predict and save a URL scan |
| `GET` | `/api/history` | User | List the current user's scans |
| `GET` | `/api/analytics` | User | Return current-user scan counts |
| `GET` | `/api/admin/users` | Admin | List users |
| `GET` | `/api/admin/scans` | Admin | List scans |
| `DELETE` | `/api/admin/scans/{id}` | Admin | Delete a scan |

Example registration:

```json
POST /api/auth/register
{
  "name": "Demo User",
  "email": "demo@example.com",
  "password": "strong-password"
}
```

Example prediction:

```json
POST /api/predict
Authorization: Bearer <jwt-token>
{
  "url": "https://example.com"
}
```

Example response shape:

```json
{
  "url": "https://example.com",
  "prediction": "LEGITIMATE",
  "probability": 0.08,
  "risk_score": 8.0,
  "risk_level": "LOW",
  "indicators": []
}
```

The exact values are generated by the loaded model and are not hardcoded.

## Database design

SQLite is used for local development.

### `users`

| Column | Description |
|---|---|
| `id` | Primary key |
| `name` | Display name |
| `email` | Unique login email |
| `password_hash` | Bcrypt password hash; plaintext is never stored |
| `role` | `USER` or `ADMIN` |
| `created_at` | Account creation time |

### `scans`

| Column | Description |
|---|---|
| `id` | Primary key |
| `user_id` | User foreign key |
| `url` | Submitted URL string |
| `prediction` | Model-derived application label |
| `probability` | Raw phishing probability |
| `risk_score` | Probability expressed as a percentage |
| `risk_level` | LOW, MEDIUM, or HIGH |
| `indicators` | JSON list of rule-based indicators |
| `created_at` | Scan time |

## Authentication and security

- Passwords are hashed with bcrypt.
- Login tokens are signed JWTs with expiration.
- Prediction, history, analytics, and admin routes require authentication.
- Admin routes require the `ADMIN` role.
- Pydantic validates submitted URL format.
- CORS origins are configured through environment variables.
- No submitted URL is visited or executed.
- Secrets are read from `.env`, not committed to source control.
- The application does not manually alter model predictions.

For a public deployment, add HTTPS, rate limiting, secure token storage, database migrations, logging/monitoring, and a production secret-management system.

## Testing

Run the backend feature tests:

```powershell
cd backend
pytest tests -q
```

The included tests cover:

- HTTPS URL extraction
- IP-address detection
- `@`-symbol detection
- Suspicious keyword indicators

Before a production release, add API integration tests for registration, login, invalid URLs, model-unavailable errors, prediction persistence, history isolation, and admin authorization.

## Limitations

1. The checked-in dataset is synthetic and intentionally small.
2. Demonstration metrics are not representative of real-world performance.
3. URL-only features cannot confirm the content or reputation of a website.
4. The current explanation list is rule-based and is not SHAP or causal neural-network attribution.
5. No external threat-intelligence service is queried.
6. The frontend is a focused scanner UI; additional product pages can be built on the existing API.
7. Any real dataset must be independently checked for license, label quality, duplicates, and leakage.

## Future scope

- Train and benchmark on a properly licensed large public dataset.
- Add Logistic Regression and Random Forest baselines.
- Add character-level CNN or BiLSTM URL modeling.
- Add SHAP/permutation-based approximate explanations.
- Add browser-extension and email/QR-code analysis workflows.
- Add permitted domain reputation and threat-intelligence integrations.
- Add PostgreSQL migrations and production deployment.
- Add stronger rate limiting, observability, and role-management screens.

## Ethical and responsible-use note

Use this project only for defensive security research, education, and authorized analysis. Do not use it to scan systems without permission. A model prediction is probabilistic and can be wrong; security decisions should include human review and appropriate independent evidence.

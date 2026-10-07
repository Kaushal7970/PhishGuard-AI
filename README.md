# PhishGuard AI

PhishGuard AI is an end-to-end URL phishing detection project. It extracts safe, deterministic metadata from a URL string, trains a TensorFlow/Keras neural network on a labelled CSV, serves predictions through FastAPI, and stores authenticated scan history in SQLite.

## Quick start

### Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python ..\ml\train.py --input ..\ml\data\raw\urls.csv --epochs 20
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000` and its OpenAPI documentation at `/docs`.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` when the API is not running at `http://localhost:8000`.

## ML pipeline

The training script accepts any CSV with `url` and `label` columns, where labels are `0` (legitimate) and `1` (phishing). It removes invalid and duplicate rows, uses a stratified 70/15/15 split, fits the scaler only on training data, trains the ANN with early stopping, saves the best Keras model and scaler, and writes actual evaluation metrics and plots. The checked-in CSV is a small clearly-labelled demonstration dataset; replace it with a licensed real dataset for meaningful results.

```powershell
python ml\train.py --input ml\data\raw\urls.csv --epochs 30
python ml\evaluate.py --data ml\data\raw\urls.csv
```

Prediction explanations contain rule-based indicators only. They are not claims about causal neural-network feature attribution. A legitimate prediction is not a guarantee of safety.

## API

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/health`
- `POST /api/predict` (JWT required)
- `GET /api/history` (JWT required)
- `GET /api/analytics` (JWT required)
- `GET /api/admin/users` and `/api/admin/scans` (admin JWT required)

See `docs/api_documentation.md` for request and response examples.

## Limitations and ethics

This is URL-string analysis, not a browsing or reputation service. The API never visits submitted URLs. Models can be wrong, datasets can be biased, and predictions must be treated as assistance rather than a security verdict. Only use datasets that permit your intended use.

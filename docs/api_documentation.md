# API documentation

Register with `POST /api/auth/register`, then send the returned bearer token from `POST /api/auth/login` as `Authorization: Bearer <token>`.

## Predict

```json
POST /api/predict
{"url":"https://example.com"}
```

The response includes `prediction`, `probability`, `risk_score`, `risk_level`, and rule-based `indicators`. The server analyzes the string and does not visit the URL.

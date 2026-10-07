import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

function App() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState(localStorage.getItem("phishguard_token") || "");

  async function scan(event) {
    event.preventDefault();
    setError("");
    if (!token) { setError("Log in through the API first to scan URLs."); return; }
    setLoading(true);
    try {
      const response = await fetch(`${API}/api/predict`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ url }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Prediction failed");
      setResult(data);
    } catch (err) { setError(err.message); } finally { setLoading(false); }
  }

  return <main className="shell">
    <header><div className="brand">🛡 <span>PHISHGUARD</span> AI</div><p>AI-powered phishing URL detection</p></header>
    <section className="panel">
      <h1>Analyze a URL</h1><p className="muted">Predictions analyze the URL string only. No submitted URL is visited.</p>
      <form onSubmit={scan}><input value={url} onChange={e => setUrl(e.target.value)} type="url" required placeholder="https://example.com" /><button disabled={loading}>{loading ? "Analyzing..." : "Analyze URL"}</button></form>
      {error && <div className="error">{error}</div>}
    </section>
    {result && <section className={`result ${result.risk_level.toLowerCase()}`}><div><span className="eyebrow">AI prediction</span><h2>{result.prediction}</h2><div className="score">{result.risk_score}%</div><p>{result.risk_level} risk · probability {(result.probability * 100).toFixed(1)}%</p></div><div><h3>Rule-based indicators</h3>{result.indicators.length ? <ul>{result.indicators.map(item => <li key={item}>{item}</li>)}</ul> : <p>No notable URL indicators.</p>}<small>This explanation is separate from neural-network attribution.</small></div></section>}
    <section className="panel login"><h2>API session</h2><p className="muted">Paste a JWT from <code>POST /api/auth/login</code> to enable scanning.</p><input value={token} onChange={e => { setToken(e.target.value); localStorage.setItem("phishguard_token", e.target.value); }} placeholder="Bearer token (without Bearer)" /></section>
  </main>;
}

createRoot(document.getElementById("root")).render(<App />);

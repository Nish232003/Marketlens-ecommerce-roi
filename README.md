# 🎯 MarketLens — E-Commerce Marketing Intelligence Platform

> Automated CAC, ROAS, and Multi-Touch Attribution Intelligence Dashboard with Interactive What-If Budget Simulation and Hybrid AI Analyst.

![MarketLens Banner](https://img.shields.io/badge/MarketLens-Marketing%20Intelligence-c8ff00?style=for-the-badge&logoColor=09090f)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask)
![Plotly](https://img.shields.io/badge/Plotly-5.22-3F4F75?style=for-the-badge&logo=plotly)

---

## 🚀 Key Features

* **⚡ 1-Second Relational Ingestion**: Automatically joins and attributes **6 raw e-commerce CSVs** (\orders\, \items\, \payments\, \customers\, \mql\, \deals\) into unified channel metrics.
* **📋 Executive AI Briefing**: Instant high-level signals highlighting **Primary Growth Vectors**, **Budget Bleed alerts**, and **Capital Reallocation recommendations**.
* **📊 8 High-Definition Interactive Visualizations**: Plotly charts for ROAS, CAC, Spend vs. Revenue, ROAS Donut, LTV/CAC scatter, Conversion rates, Budget recommendations, and Cohort retention.
* **🔍 Interactive Channel Table & Deep Dive Modal**: Instant search, multi-column sorting, 1-click smart filter chips, and clickable rows opening 3-stage acquisition funnels and unit economics.
* **🎛️ What-If Budget Simulator**: Real-time non-linear saturation curve (\Spend^0.82\) simulation computing net profit impact and blended ROAS on the fly.
* **🧠 Hybrid AI Analyst**:
  * **Offline Deterministic NLP Engine**: 100% exact arithmetic, zero hallucinations, instant response, and works with no API key.
  * **Cloud Claude Integration**: Open-ended conversational analysis with automatic failover safety.
* **📄 Executive PDF & CSV Exports**: 1-click CSV download and print-ready executive PDF report.
* **⚡ 1-Click Instant Demo**: Pre-loaded sample dataset for instant zero-setup exploration.

---

## 🛠️ Tech Stack

* **Backend**: Python 3, Flask, Pandas, NumPy, Plotly
* **Frontend**: Vanilla HTML5 / Modern CSS (Glassmorphism, Dark Neon Theme, Tabular Numerals), Vanilla JavaScript (No heavy frameworks required)
* **AI Engine**: Hybrid Rule-Based NLP Expert System + Anthropic Claude API Proxy

---

## 🏃 Quickstart (Local Run)

1. **Clone the repository**:
   \\\ash
   git clone https://github.com/Nish232003/Marketlens-ecommerce-roi.git
   cd Marketlens-ecommerce-roi
   \\\

2. **Create and activate a virtual environment**:
   \\\ash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS / Linux:
   source .venv/bin/activate
   \\\

3. **Install dependencies**:
   \\\ash
   pip install -r requirements.txt
   \\\

4. **Launch the application**:
   \\\ash
   python backend/app.py
   \\\

5. Open your browser at **\http://127.0.0.1:5000\** and click **⚡ LOAD SAMPLE DATA**!

---

## 🌐 Public Deployment (Render.com)

1. Push your repository to GitHub.
2. Create a new **Web Service** on [Render.com](https://render.com).
3. Connect your repository.
4. Set:
   * **Build Command**: \pip install -r requirements.txt\
   * **Start Command**: \gunicorn backend.app:app\
5. Deploy!

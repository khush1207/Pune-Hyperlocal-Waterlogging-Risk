# 🌧️ Hyperlocal Flood Risk Prediction & Community Alert System — Pune

An AI-based system that estimates the **current road-waterlogging risk every hour at 482 locations across 58 wards of Pune**, and shows it on an interactive, multilingual map dashboard with guidance for residents, NGOs/volunteers, farmers and local authorities.

> Built to help an NGO strengthen disaster preparedness and community resilience for vulnerable communities.

---

## 📸 Screenshots

### Live overview
Counts of locations at Low / Moderate / High / Extreme risk. Click a card to filter the map. Language selector at top left (English, Hindi, Marathi).

<img width="1898" height="827" alt="dashboard-overview" src="https://github.com/user-attachments/assets/8e54b75a-fbe5-49c4-b0a6-10cc2b5f8f00" />

### Role-based guidance and location search
Choose your role (Resident, NGO/Volunteer, Farmer, Local Authority) and pick a Pune/PMC area to check before travelling.

<img width="1898" height="826" alt="role-and-location-search" src="https://github.com/user-attachments/assets/d6d7b62c-8ffe-46c4-98d3-7df8ede5c4d3" />

### Hyperlocal risk map
Every dot is a monitored location, coloured by risk level. The blue dot is the user's own location.

<img width="1898" height="821" alt="risk-map" src="https://github.com/user-attachments/assets/3aad0601-0dfa-4031-aabd-b84024cfc17d" />

### Your location panel
Risk level at the nearest monitored point, with a plain-language "What this means" explanation and role-specific actions.

<img width="1889" height="828" alt="your-location-panel" src="https://github.com/user-attachments/assets/56f9b551-6840-4528-8a7e-45906a791e62" />

---

## 🎯 Objectives

1. Build an AI-based hyperlocal road-waterlogging risk system giving hourly risk for vulnerable roads and localities in Pune, using rainfall, weather, terrain, drainage and urban characteristics.
2. Analyse real-time weather and rainfall history with location-specific factors to produce a continuous risk score and Low / Moderate / High / Extreme categories.
3. Provide location-specific early warnings through an interactive dashboard and map.
4. Support preparedness and resource planning by highlighting repeatedly vulnerable locations and giving accessible risk information.

## ✨ Features

- **Hyperlocal:** 482 sampling points in 58 wards, not one number for the whole city
- **Hourly, time-aware:** rainfall over the last 1, 3, 6, 12, 24, 72 and 168 hours plus humidity, temperature, wind and solar radiation
- **Continuous 0–100 risk score** mapped to four levels
- **Live predictions** from current weather, cached for 15 minutes
- **Stakeholder guidance** for Residents, NGOs/Volunteers, Farmers and Local Authorities
- **Multilingual:** English, Hindi, Marathi
- **Interactive map** (Leaflet + OpenStreetMap) with risk filters and geolocation

## 🚦 Risk levels

| Level | Score | Meaning |
|---|---|---|
| 🟢 Low | < 30 | Conditions favourable |
| 🟡 Moderate | 30 – < 60 | Some accumulation possible in low-lying spots |
| 🟠 High | 60 – < 90 | Waterlogging likely on vulnerable roads |
| 🔴 Extreme | ≥ 90 | Severe waterlogging likely |

## 🧠 How it works

```
Open-Meteo weather ─┐
                    ├─► Feature engineering (34 features) ─► HistGradientBoosting model ─► Risk score 0–100 ─► FastAPI ─► React dashboard
Location features ──┘      (rolling rainfall, weather,
(terrain, drainage,         hours since rain, time, static)
 built-up, roads)
```

1. **Data:** hourly weather 2021–2025 (Open-Meteo Historical Forecast API) for 482 locations, about **21.1 million** records, stored as month-wise Parquet. Land cover (built-up and vegetation %) from Google Earth Engine Dynamic World.
2. **Target:** no large verified waterlogging dataset exists for Pune, so an **AHP-based proxy risk score** was built from five criteria: current rainfall (40%), antecedent wetness (24%), drainage/terrain (16%), urban runoff (12%) and drying resistance (8%). AHP consistency ratio = 0.020.
3. **Model:** scikit-learn `HistGradientBoostingRegressor`, 34 features, trained on 2021–2023 with risk-sensitive sample weights, validated on 2024.
4. **Serving:** FastAPI fetches the last 168 hours of live weather, builds the same features and predicts.

### Model results (validation year 2024, 4,233,888 hourly records)

| Metric | Value |
|---|---|
| R² | 0.9989 |
| MAE | 0.245 score points |
| RMSE | 0.535 |
| Category accuracy | 99.47% |
| Macro-F1 | 0.941 |
| EXTREME recall | 83.1% |

> ⚠️ **Important:** the target is an AHP proxy, so these metrics show how well the model reproduces the constructed risk index. They are **not** proof of accuracy against real observed waterlogging. Validation against real events (municipal complaints, news and field reports) is planned future work.

## 🗂️ Repository structure

```
├── main.py                              # FastAPI backend
├── live_weather_pipeline.py             # Live weather + feature generation
├── extract_dynamic_world.py             # Land cover from Google Earth Engine
├── prepare_static_locations.py          # Static features per location
├── download_hourly_weather.py           # Historical weather download
├── convert_hourly_to_parquet.py         # CSV.GZ → Parquet
├── create_hourly_features.py            # Feature engineering
├── current_ahp_target_generation.py     # AHP weights and risk target
├── create_current_ml_ready.py           # ML-ready dataset
├── train_current_risk_hgb_validation.py # Model training and validation
├── test_gee.py                          # Earth Engine connection test
├── requirements.txt
├── models/                              # Trained model, metadata, results
├── data/                                # static_locations.csv, AHP files, live outputs
└── frontend/                            # React + Vite dashboard
```

## 🚀 Run locally

### Prerequisites
- Python 3.10+
- Node.js 18+
- Internet access (live weather from Open-Meteo)

### 1. Backend
```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
API available at `http://localhost:8000`. Interactive docs: `http://localhost:8000/docs`.

### 2. Frontend
```bash
cd frontend
npm install
```
Create `frontend/.env.local`:
```
VITE_API_URL=http://localhost:8000
```
Then:
```bash
npm run dev
```
Open the address shown in the terminal (for example `http://localhost:5173`).

### API endpoints

| Endpoint | Description |
|---|---|
| `GET /health` | Health check |
| `GET /api/risk/current` | Current risk for all locations |
| `GET /api/risk/refresh` | Refresh live predictions |
| `GET /api/risk/stats` | City-level risk counts |
| `GET /api/risk/points` | Location-level scores |
| `GET /api/risk/wards` | Ward-level summary |
| `GET /api/risk/nearest` | Risk at the nearest monitored point |
| `POST /api/route-risk` | Risk along a route (backend only) |

## 🛠️ Tech stack

**ML / data:** Python, pandas, NumPy, scikit-learn, PyArrow (Parquet), Google Earth Engine
**Backend:** FastAPI, Uvicorn
**Frontend:** React, Vite, Leaflet / React-Leaflet, Recharts, Axios, i18next
**Data sources:** Open-Meteo, Google Dynamic World, OpenStreetMap

## ⚠️ Limitations and status

- **Runs locally.** A hosted deployment was attempted, but the Open-Meteo free tier's rate limits cannot support continuous public use for 482 locations. Public hosting needs a higher-capacity weather API.
- Risk is a **current-conditions** estimate, not a long-range forecast.
- The risk index has **not yet been validated against real waterlogging records**.
- Weather comes from gridded model data, so nearby points may share weather values; hyperlocal differences come mainly from static terrain and urban features.

## 📄 Documentation

- Technical Report: full methodology, data, model, challenges and results
- User Manual: step-by-step guide to the dashboard

## 👥 Team

Khushboo Talaviya
Karunya Agarwal
Khushi Harkhani
Karmanya Singh

## 📜 Licence

Terrain flow accumulation data was obtained from the MERIT Hydro dataset (Yamazaki et al.) under the Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0) license. The original raster data was sampled and processed to generate flow accumulation values for each ward sampling point.

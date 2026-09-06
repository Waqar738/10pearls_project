# Bara Khyber AQI Forecast System

**Production-grade multi-horizon Air Quality Index forecasting platform for Bara Khyber**

[![Live Dashboard](https://img.shields.io/badge/Live-Streamlit%20Dashboard-FF4B4B?style=for-the-badge&logo=streamlit)](https://waqar-aqi-predictor.streamlit.app/)
[![Production API](https://img.shields.io/badge/API-Railway-0B0D0E?style=for-the-badge&logo=railway)](https://aqi-predictor-karachi-production.up.railway.app)
[![GitHub](https://img.shields.io/badge/GitHub-Waqar738-181717?style=for-the-badge&logo=github)](https://github.com/Waqar738)

---

## Live System

| Component              | URL |
|------------------------|-----|
| **Streamlit Dashboard** | [https://waqar-aqi-predictor.streamlit.app/](https://waqar-aqi-predictor.streamlit.app/) |
| **Production API**     | [https://aqi-predictor-karachi-production.up.railway.app](https://aqi-predictor-karachi-production.up.railway.app) |

---

## Project Overview

A production-ready, multi-horizon Air Quality Index (AQI) forecasting system built with modern MLOps practices, specifically designed for Bara Khyber, Pakistan.

**Key Capabilities:**
- Ingests 5 months of historical AQI data
- Fetches live weather data via API
- Performs comprehensive Exploratory Data Analysis (EDA)
- Engineers advanced time-series features
- Trains multiple machine learning models per forecast horizon
- Stores features in a MongoDB Feature Store
- Registers models in a MongoDB Model Registry
- Serves predictions via FastAPI
- Delivers insights through a professional Streamlit dashboard

---

## System Architecture


```
Historical AQI + Weather Data (Open-Meteo)
              ↓
     MongoDB (historical_hourly_data)
              ↓
   Feature Engineering Pipeline
              ↓
   Multi-Horizon Model Training
              ↓
   Model Registry (Best Model Selection)
              ↓
   FastAPI Inference Service (Railway)
              ↓
   Streamlit Dashboard (Streamlit Cloud)
```

---


---

## Data Pipeline

### 1. Data Ingestion
- Historical AQI data (5 months)
- Live weather data (temperature, humidity, wind speed, pressure)
- Temporal alignment of weather and AQI data into a unified dataset

### 2. Exploratory Data Analysis
- Distribution analysis
- Correlation analysis between AQI and weather variables
- Seasonal trend identification
- Outlier detection
- Missing value analysis

### 3. Feature Engineering
- Lag features (`lag_1`, `lag_3`, `lag_6`, `t-24`, `t-48`)
- Rolling statistics (mean & standard deviation)
- Temporal encodings (hour-of-day, day-of-week)
- Weather interaction features
- Multi-horizon targets (H1, H2, H3)

Engineered features are persisted in **MongoDB Atlas** as a Feature Store.

---

## Exploratory Data Analysis

Conducted on **3,541 hourly observations** with **19 engineered features**.

### Dataset Summary
- 3,541 hourly records
- Multi-horizon targets (H1, H2, H3)
- Lag features and rolling statistics
- Pollutant features (NO₂, CO, SO₂, O₃)

### Key Findings
- AQI (PM2.5) exhibits moderate right-skewness with occasional pollution spikes
- Strong temporal dependency captured by lag and rolling features
- NO₂ and CO show moderate positive correlation with AQI
- Ozone demonstrates a negative relationship with particulate concentration
- Raw time features contribute primarily through non-linear relationships
- Multicollinearity among temporal features is well-handled by tree-based models

### Visualizations
- AQI distribution histogram
- Hourly & monthly trend analysis
- Correlation heatmap
- Outlier detection boxplots
- Pollutant vs AQI scatter plots

**Related Files:**
- Notebook: `notebooks/EDA.ipynb`
- Dataset: `eda_training_dataset.csv`

---

## Methodology

### Multi-Horizon Modeling Strategy

Instead of recursive forecasting, the system trains **independent models** for each horizon:

| Horizon | Forecast Window |
|---------|-----------------|
| H1      | 24 hours        |
| H2      | 48 hours        |
| H3      | 72 hours        |

**Models Evaluated:**
- Random Forest
- Gradient Boosting
- Ridge Regression

### Model Performance

| Horizon | Model          | RMSE  | R² Score |
|---------|----------------|-------|----------|
| 24h     | Random Forest  | 5.97  | 0.843    |
| 48h     | Random Forest  | 5.56  | 0.862    |
| 72h     | Random Forest  | 5.70  | 0.855    |

**Production Model:** Random Forest (selected based on lowest RMSE and highest R² across horizons)

---

## Backend API (FastAPI)

### Available Endpoints

| Endpoint                 | Description                  |
|--------------------------|------------------------------|
| `GET /`                  | Health check                 |
| `GET /forecast`          | Multi-day AQI forecast       |
| `GET /models/metrics`    | Model registry metrics       |
| `GET /models/best`       | Best production model        |
| `GET /features/importance` | Feature importance         |
| `GET /forecast/shap`     | SHAP explainability          |

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements_backend.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements_backend.txt

COPY app/ app/
COPY scripts/ scripts/
COPY Procfile .

CMD ["sh", "-c", "uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT}"]

## Deployment Architecture

| Component   | Platform         | Details                                      |
|-------------|------------------|----------------------------------------------|
| Backend     | Railway          | Dockerized FastAPI + MongoDB Atlas           |
| Frontend    | Streamlit Cloud  | Connected to Railway API                     |
| Database    | MongoDB Atlas    | Feature Store + Model Registry + GridFS      |

### Environment Variables

**Railway:**
```
MONGODB_URI=your_mongodb_connection_string
```

**Streamlit Secrets:**
```toml
MONGODB_URI = "..."
API_URL = "https://aqi-predictor-karachi-production.up.railway.app"
```

---

## Streamlit Dashboard Features

- Multi-day AQI gauge charts
- Forecast trend visualization
- Model benchmark comparison
- Feature importance plots
- Executive summary
- Dark professional UI
- Robust error handling and backend health checks

---

## Tech Stack

| Category          | Technologies                          |
|-------------------|---------------------------------------|
| Language          | Python 3.11                           |
| Backend           | FastAPI, Uvicorn                      |
| Frontend          | Streamlit, Plotly                     |
| ML                | Scikit-learn, SHAP                    |
| Database          | MongoDB Atlas (Feature Store + GridFS)|
| Deployment        | Docker, Railway, Streamlit Cloud      |

---

## Advanced Capabilities

- MongoDB Feature Store architecture
- Model Registry with automatic best-model tagging
- GridFS model persistence
- Lazy model loading in production
- SHAP-based explainability
- Multi-model benchmarking
- Fully dockerized backend
- Cloud-native scalable inference

---

## Engineering Challenges Solved

- Dynamic port configuration on Railway
- MongoDB Atlas connection management
- Multi-horizon forecasting design
- Model registry architecture
- ObjectId serialization in FastAPI
- Environment variable handling across platforms
- Cold-start resilience
- Streamlit ↔ Railway communication
- NumPy version compatibility
- GridFS model loading

---

## Future Improvements

- [ ] CI/CD pipeline with GitHub Actions
- [ ] Automated daily retraining
- [ ] Redis caching layer
- [ ] Real-time AQI data ingestion
- [ ] SMS / Email alert system
- [ ] Kubernetes-based scaling
- [ ] Monitoring & logging dashboard
- [ ] Authentication & role-based access

---

## Author

**Muhammad waqar**  
10 Pearls Shine Intern | Cohort 9  
AI/ML Engineer  

[![GitHub](https://waqar738.github.io/)]
[![LinkedIn](https://www.linkedin.com/in/muhammad-waqar-afridi/)]

---

## License

This project is open source and available under the [MIT License](LICENSE).


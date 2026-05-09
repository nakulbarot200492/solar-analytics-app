# Solar SPV Analytics Platform

**Anomaly Detection | MPPT Analysis | RCA Engine**  
300–400 Solar PV Sites • Inverter-level Intelligence • Actionable O&M Insights

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
streamlit run app/main.py
```

### 3. Upload your data
- Upload an Excel file (`.xlsx` / `.xls`) with the required columns
- Navigate through the sidebar to explore Rankings, Anomalies, MPPT Analysis, and RCA

---

## Required Excel Columns

| Column | Type | Unit |
|---|---|---|
| Timestamp | DateTime | YYYY-MM-DD HH:MM:SS |
| Site_ID | String | — |
| Inverter_ID | String | — |
| MPPT_ID | String/Int | — |
| DC_Voltage_V | Float | Volts |
| DC_Current_A | Float | Amperes |
| DC_Power_kW | Float | kW |
| AC_Power_kW | Float | kW |
| Irradiance_Wm2 | Float *(optional)* | W/m² |

---

## Project Structure

```
solar-analytics-app/
├── app/
│   ├── main.py              # Entry point
│   └── pages/               # Multi-page Streamlit views
├── core/                    # Analytics modules
│   ├── data_loader.py
│   ├── data_cleaner.py
│   ├── inverter_ranking.py
│   ├── anomaly_detector.py
│   ├── mppt_analyzer.py
│   ├── rca_engine.py
│   └── exporter.py
├── tests/                   # Unit tests
├── data/sample/             # Sample datasets
└── requirements.txt
```

---

## Tech Stack (Phase 1 MVP)

- **UI:** Streamlit
- **Data:** Pandas, NumPy
- **Charts:** Plotly
- **Excel:** openpyxl, xlrd

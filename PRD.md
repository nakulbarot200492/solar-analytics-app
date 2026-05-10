# Product Requirements Document (PRD): Solar SPV Analytics Platform

## 1. Project Overview
**Project Name:** Solar SPV Analytics Platform  
**Mission:** To provide O&M (Operations & Maintenance) engineers and asset managers with a high-fidelity, intelligent monitoring and diagnostic tool for utility-scale solar plants.

The platform transforms raw multi-manufacturer sensor data (specifically SMA) into actionable insights, identifying underperforming assets and recommending specific maintenance actions.

---

## 2. Target Audience
*   **O&M Engineers:** Responsible for site visits and fixing hardware faults.
*   **Asset Managers:** Responsible for tracking fleet-wide performance and PR (Performance Ratio).
*   **Performance Analysts:** Responsible for deep-diving into inverter-level data to find subtle losses.

---

## 3. Core Modules & Features

### 3.1 Data Ingestion & Pipeline (`core/data_loader.py`)
*   **Multi-Format Support:** Robust parsing of `.xlsx` and `.xls` files.
*   **Schema Normalization:** Intelligent mapping of wide-format SMA "Detailed" reports to a canonical internal schema (Timestamp, Voltage, Current, Power).
*   **Strict Validation:** Automated check for mandatory electrical metrics to prevent downstream crashes.
*   **Time-Series Cleaning:** Automated handling of timezone conversion, daylight filtering, and unit scaling.

### 3.2 Inverter Ranking Engine (`core/ranking_engine.py`)
*   **Composite Scoring:** 
    *   **60% Performance Score:** Normalized energy output relative to site peers.
    *   **40% MPPT Health Score:** Internal consistency across string/channel inputs.
*   **Tier Categorization:** Automatic identification of "Top 10%" and "Bottom 10%" performers.
*   **Comparative Metrics:** Calculation of Site PR, Availability, and specific energy (kWh/kWp).

### 3.3 Anomaly Detection Engine (`core/anomaly_engine.py`)
Rule-based detection of 8+ critical solar failure modes:
1.  **Zero Generation:** Inverter/MPPT reporting zero power during daylight.
2.  **Sudden Power Drop:** Drastic loss of power relative to site average.
3.  **Clipping Detection:** Identifying MPPTs limited by inverter DC capacity.
4.  **Voltage Instability:** High variance in DC voltage indicating loose connections or PID.
5.  **Current Mismatch:** Significant deviation (>20%) between MPPT channels.
6.  **Flatline Current:** Stagnant current values indicating sensor failure or communication issues.

### 3.4 MPPT Deviation Analysis (`core/mppt_analyzer.py`)
*   **Granular Diagnostics:** Channel-by-channel comparison within a single inverter.
*   **Interactive Heatmaps:** Spatiotemporal visualization of Voltage and Current across the fleet.
*   **Underperformance Isolation:** Specific identification of failing string inputs (e.g., A25-MPPT-6).

---

## 4. Design & User Experience (UX)
The platform utilizes a custom-built design system integrated via **Stitch (Google)**.

*   **Aesthetic:** "OLED-First" Premium Dark Mode.
*   **Typography:** 
    *   **Headline:** Space Grotesk (Modern, Technical).
    *   **Body:** Inter (Highly readable).
    *   **Code/Logs:** JetBrains Mono.
*   **Color Palette:**
    *   **Primary:** Sunflower Yellow (`#ffd700`) - representing solar energy.
    *   **Secondary:** Electric Blue (`#4a8eff`) - representing grid interaction.
    *   **Tertiary:** Emerald Green (`#7bf29d`) - representing battery/health.
*   **Structural Elements:** 
    *   **Glassmorphism:** 24px rounded corners with backdrop-blur for cards.
    *   **OLED Black Background:** Optimized for field tablets and control rooms.

---

## 5. Technical Stack
*   **Frontend/UI:** Streamlit (Python-based reactive framework).
*   **Data Processing:** Pandas, NumPy.
*   **Visualization:** Plotly (Interactive charts/heatmaps).
*   **Version Control:** Git / GitHub.
*   **Styling:** Custom CSS injection via `app/styles.py`.

---

## 6. Success Metrics (KPIs)
*   **Detection Accuracy:** >95% accuracy in identifying documented MPPT faults.
*   **Processing Speed:** Ability to process 30+ days of inverter data in <5 seconds.
*   **User Adoption:** Reduction in "Time to RCA" for O&M teams.

---

## 7. Roadmap & Future Enhancements
*   **Phase 2:** Integration with weather station (Pyranometer) data for absolute PR calculation.
*   **Phase 3:** Predictive maintenance using LSTM/Machine Learning models.
*   **Phase 4:** PDF report generation for executive stakeholders.

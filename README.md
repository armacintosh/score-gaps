# Public Data Statistical Aggregator

[🌐 Visit Grounded Scientific](https://alexandermacintosh.ca/) | [📅 Book a Strategy Call](https://calendar.app.google/mWcfwiGYS5trNMer6)

> **Project Context:** A statistical benchmarking tool that aggregates public demographic performance data from major standardized assessments.
> **Business Value:** Provides critical "Population Level" context for fairness audits. It allows organizations to distinguish between *algorithmic bias* (errors in the tool) and *systemic disparities* (reflections of the population) by comparing internal results against national baselines.
> **Status:** Active Tooling (Streamlit Application)

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://score-gaps.streamlit.app/)

---

### 🔬 Scientific Basis
In algorithmic fairness auditing, a raw score gap between demographic groups does not always indicate a flawed model. To understand if a specific tool is biased, we must first understand the **baseline population disparities** in related constructs.

This repository aggregates publicly reported means, standard deviations, and demographic breakdowns from **7 major standardized assessments**. It serves as a "Meta-Analysis Engine" to visualize how performance varies across race, gender, and socioeconomic status in the US education system.

**Key Capabilities:**
* **Cross-Assessment Comparison:** Normalizes data from disparate sources (e.g., MCAT vs. LSAT) to allow for apples-to-apples comparison of demographic gaps.
* **Baseline Contextualization:** Provides the "Ground Truth" distributions needed to calculate standardized impact ratios (e.g., the 4/5ths rule) during internal audits.

---

### 📊 Data Inventory & Sources
This tool aggregates data from the following technical reports and public APIs.

#### **Medical & Graduate Admissions**
* **AAMC (Medical School):** GPA and MCAT scores for applicants/matriculants.
    * *Source:* [AAMC 2023 Facts](https://www.aamc.org/data-reports/students-residents/interactive-data/2023-facts-applicants-and-matriculants-data)
* **GMAT (Business):** Analytical Writing, Integrated Reasoning, Quantitative, and Verbal sections.
    * *Source:* [GMAT Test Taker Data](https://www.gmac.com/market-intelligence-and-research/market-research/gmat-test-taker-data)
* **GRE (General Graduate):** Analytical Writing, Quantitative Reasoning, and Verbal Reasoning.
    * *Source:* [GRE Snapshot Report](https://www.ets.org/gre/research/snapshot.html)
* **LSAT (Law):** Logical Reasoning, Analytical Reasoning, and Reading Comprehension.
    * *Source:* [LSAT Research Report](https://www.lsac.org/data-research/research)

#### **Undergraduate & K-12**
* **SAT (College Admissions):** Math and Evidence-Based Reading & Writing (ERW).
    * *Source:* [SAT Suite Program Results](https://reports.collegeboard.org/sat-suite-program-results)
* **NAEP (K-12 Progress):** The "Nation’s Report Card" (Reading, Math, Science).
    * *Source:* [NAEP Data API](https://www.nationsreportcard.gov/api_documentation.aspx)

#### **Non-Cognitive / Situational Judgment**
* **Casper (Social Intelligence):** Situational Judgment Test (SJT) scores used for assessing professionalism.
    * *Source:* [Casper Technical Manual](https://acuityinsights.com/research/)

---

### 🛠 Tech Stack
* **Application Framework:** Streamlit (Python).
* **Data Processing:** Pandas (Data Cleaning & Normalization), NumPy.
* **Visualization:** Plotly Graph Objects (Interactive Distribution Charts).
* **Deployment:** Streamlit Community Cloud.

### ⚠️ Usage Note
This tool is for **comparative analysis only**. The data presented is aggregated from public technical reports and does not contain individual-level PII (Personally Identifiable Information). It is intended to help researchers and administrators understand the landscape of educational measurement.

---

### 🔄 Dependencies
To run this application locally:

```bash
# Clone the repository
git clone [https://github.com/armacintosh/public-data-statistical-aggregator.git](https://github.com/armacintosh/public-data-statistical-aggregator.git)

# Install requirements
pip install -r requirements.txt

# Launch Streamlit
streamlit run app.py

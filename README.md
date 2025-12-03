# 🚀 News Popularity Analytics: Decoding the Mechanics of Virality

> **Strategic Data Science Project** analyzing **37.5 million social media records** to determine *what* to write, *when* to post, and *where* to distribute content for maximum ROI.

![Project Banner](figures/section5.4.2.1_platform_velocity_curves.png)

## 📖 Table of Contents
- [Overview](#-overview)
- [The Dataset](#-the-dataset)
- [Engineering Pipeline](#-engineering-pipeline)
    - [1. Data Cleaning & Integration](#1-data-cleaning--integration)
    - [2. Advanced Feature Engineering](#2-advanced-feature-engineering)
- [Key Insights & Storytelling](#-key-insights--storytelling)
- [Project Structure](#-project-structure)
- [Installation & Usage](#-installation--usage)
- [Important: Large File Handling](#-important-large-file-handling)

---

## 🔎 Overview
In the age of information overload, content creators face a dilemma: **How to cut through the noise?**

This project does not just visualize data; it engineers a **Strategic Engine**. By processing **37.5 million rows** of time-series data (social feedback on news articles), we moved beyond simple view counts to create behavioral metrics (Velocity, Stickiness, Sentiment, Complexity).

**Key Achievement:** We successfully architected a **Local Map-Reduce Pipeline** (using Python `multiprocessing`) to process this massive dataset on a standard laptop, overcoming physical RAM limitations during aggregation.

---

## 💾 The Dataset

**Source:** UCI Machine Learning Repository (News Popularity in Multiple Social Media Platforms).

**Why this dataset?** It provides a rare, granular view of news consumption across a 48-hour lifecycle, allowing us to model the *physics* of information diffusion (Velocity & Acceleration) rather than just the final result.

**Original Structure:**
*   **Format:** 13 fragmented CSV files (Split by Topic/Platform like `Facebook_Obama.csv`, `LinkedIn_Economy.csv`).
*   **Structure:** "Wide" format with 144 columns representing 20-minute time slices ($TS_1$ to $TS_{144}$).
*   **Features:** ID, Title, Headline, Source, PublishDate, and raw popularity counters.

---

## 🛠 Engineering Pipeline

We transformed raw, fragmented logs into a high-dimensional strategic asset through a rigorous **Data Engineering Pipeline**. This process was architected to handle **Big Data (37.5M rows)** on local hardware without memory overflow.

### 1. Data Cleaning & Integration (The "Memory-First" Strategy)
The raw data was fragmented across 13 CSVs with a "Wide" structure (144 time columns), creating a potential RAM bottleneck (~37GB uncompressed).

*   **Smart Integration ("Melt-then-Combine"):**
    *   *Problem:* Merging 13 wide files first would create a massive intermediate matrix, crashing the kernel.
    *   *Solution:* We implemented an iterative loop that loads one file, immediately reshapes it to **Long Format** (Vectorized `TimeSlice` column) using `pd.melt()`, and only then appends it to the master list.
*   **Placeholder Sanitization:**
    *   Detected statistical corruption where tracking errors were recorded as `-1`.
    *   *Action:* Replaced all `-1` values with `NaN` to ensure aggregation functions (`mean`, `sum`) remain statistically valid.
*   **Entity Resolution (Source Consolidation):**
    *   *Problem:* The `Source` column contained 5,700+ noisy variations (e.g., *'Reuters'*, *'Reuters via Yahoo'*, *'Reuters Online'*).
    *   *Optimization Trick:* **"Count on Small, Apply to Big."** Instead of processing 37M rows, we extracted unique `(ID, Source)` pairs (~90k rows), applied Regex cleaning rules to create a mapping dictionary, and then broadcasted this map back to the master dataset. This reduced processing time from hours to seconds.

### 2. Advanced Feature Engineering (The Strategic Engine)
We moved beyond simple counters to engineer **15 Behavioral & Contextual Metrics**, categorized into four dimensions.

#### **A. Dynamics (The Physics of Virality)**
Treating the time-series data as velocity vectors to measure "Force" and "Friction."
*   **`Initial_Velocity` ($V_0$):** Popularity score at `TimeSlice 1` (First 20 mins). Measures the **Impulse Power** (Click-Through Rate).
*   **`Stickiness_Index` ($S$):** A dimensionless ratio measuring retention.
    *   *Formula:* $S = 1 - (V_0 / Final\_Score)$
    *   *Meaning:* High $S$ indicates organic growth (Evergreen); Low $S$ indicates "Flash" content (Clickbait).

#### **B. Psycholinguistics (Content DNA)**
Using NLP to decode the psychological triggers in titles.
*   **Optimization Hack:** Running `TextBlob` on 37M rows is computationally prohibitive. We extracted unique Article Titles (~90k), ran the NLP pipeline, and merged results back. **Speedup: ~400x.**
*   **`Sentiment_Divergence`:** Calculated the absolute difference between `Title_Sentiment` and `Headline_Sentiment`. Used to scientifically detect **Clickbait** (Bait-and-Switch tactics).
*   **`Title_Complexity`:** Measures Cognitive Load (Word Count + Avg Word Length) to test the "Keep It Simple" hypothesis vs. "Value Signaling."

#### **C. Market Ecology (Context)**
*   **`Source_Tier`:** Algorithmic classification of publishers into **Tier 1 (Mainstream Goliath)** vs. **Tier 3 (Niche David)** based on total article volume.
*   **`Opportunity_Score`:** A rolling-window metric measuring Market Saturation.
    *   *Logic:* Inverse of the number of competing articles published within a $\pm 2$ hour window.
    *   *Output:* Classifies time slots into **Red Ocean** (High Competition) vs. **Blue Ocean** (Low Competition).

#### **D. Statistical Normalization**
*   **Logarithmic Transformation:** The data followed a strict Pareto Distribution (Power Law). We applied `np.log1p` ($log_{10}(x+1)$) to compress extreme outliers, revealing the "Hidden Majority" of content for visualization.

---

## 📊 Key Insights & Storytelling

We used a **"Before/After"** approach to demonstrate the value of data preparation.

### **The "Golden Quadrant" Strategy**
Using our engineered metrics ($V_0$ vs. $S$), we identified distinct platform personalities:
*   **Facebook:** Vertical Growth (**High Velocity**, Low Stickiness). Strategy: *"Shock & Awe"*.
*   **LinkedIn:** Horizontal Growth (Low Velocity, **High Stickiness**). Strategy: *"Reference Value"*.

### **The "Red Ocean" Paradox**
Data proves that publishing during **High Competition** hours (Red Ocean) yields **8x higher engagement** than publishing during quiet hours (Blue Ocean). **Traffic Volume trumps Competition.**

---

## 📂 Project Structure

This repository is organized to separate Raw Data, Engineering Logic, and Final Analysis.

```text
Gr8_Final_Phase1_2/
│
├── Data/
│   ├── prepared/                        
│   │   ├── 3_master_df_files.zip        # Backup of large master files
│   │   ├── chapter1_*.csv               # Content DNA (Sentiment, Complexity, Topic)
│   │   ├── chapter2_*.csv               # Market Context (Hourly, Weekly, Source, Opportunity)
│   │   ├── chapter3_*.csv               # Strategy Dynamics (Golden Quadrant, Lifecycle)
│   │   ├── master_df_consolidated.csv   # [LARGE] The Final Clean 37M Row Dataset
│   │   ├── master_df_merged.pkl         # [LARGE] Intermediate state
│   │   ├── master_df_temporal.pkl       # [LARGE] Intermediate state
│   │   ├── sec4.*.txt                   
│   │   ├── sec5.1.1_df_sample.pkl       # Stratified sample for distribution analysis
│   │   └── source_mapping.pkl           # Logic for source tiering
│   │
│   └── [Raw CSV Files]                  # Original source files
│
├── figures/
│   ├── eda_raw/                         # Initial data exploration plots
│   ├── section*.json                    # Interactive Plotly objects
│   └── section*.png                     # Charts for reports
│
├── 0_Project Kickoff & Initial Direction Setting.ipynb  
├── 01_EDA_Raw.ipynb                                     
├── 02_Preparation_and_Analysis.ipynb                    
│
├── dynamics_multicore.py                # Map-Reduce engine for parallel processing
├── custom_template.py                   # Plotly styling configuration
├── all_source_counts.txt                # Log: Raw source frequencies
└── source_mapping.pkl                   
```


### Key File Descriptions:
- **02_Preparation_and_Analysis.ipynb**: The heavy lifter. It imports `dynamics_multicore` to run calculations on 37.5M rows and exports clean, small CSVs to `Data/prepared/`.
- **dynamics_multicore.py**: A custom Python module implementing Byte-Level Chunking and Sharded Writing to handle large datasets efficiently.
- **Data/prepared/**: Stores the "Gold" — the aggregated, analysis-ready datasets used for visualization.

---

## ⚙️ Installation & Getting Started

### 1. Environment Setup  
```bash
git clone https://github.com/quanninja1304/Data-Visualization-G8.git
pip install -r requirements.txt
```

---

### 2. Data Setup

Due to GitHub's file size limits (100MB), the full 4.5GB dataset cannot be hosted directly.  
This repository employs a **Hybrid Data Strategy** to ensure reproducibility.

#### 🟢 Option A: Demo Mode (Default — No Download Required)

Best for: Checking the code logic, pipeline flow, and viewing final visualizations immediately.

- **Pipeline (`02_Preparation_and_Analysis.ipynb`)**: Automatically loads the included `master_sample.csv` (10k rows) if the full dataset is missing.  

#### 🔴 Option B: Production Mode (Full Replication)

1. Download the **Full Master Dataset (4.5GB)** from [3_master_df_files.zip](https://drive.google.com/drive/folders/187zJd0BC5UG2-X-eAVeEbjyWo-Uc1WEz).
2. Place the file at: `Data/prepared/master_df_consolidated.csv`.  
3. The code will automatically detect the file and switch to full processing mode.

> **Technical Note:** Intermediate processing files (`*.pkl`) are excluded via `.gitignore` to keep the repo light.  
> The pipeline relies on either the Raw CSVs or the Master CSV to rebuild them if needed.

---

### 3. Execution Guide

#### Step 1: Context & Diagnosis (Optional)

- **`0_Project Kickoff & Initial Direction Setting.ipynb`**: Review the project hypotheses and planning.  
- **`01_EDA_Raw.ipynb`**: View the initial data diagnosis and quality checks.

---

#### Step 2: The Core Engine (Pipeline & Analysis)

Run **`02_Preparation_and_Analysis.ipynb`**.  
This is the main notebook that handles the entire workflow:

- **Data Engineering:** Cleans and processes the raw/sample data.  
- **Analysis & Visualization:** Calculates behavioral metrics (Velocity, Stickiness) and renders the final interactive charts.

**Run Time (Demo Mode):** < 1 minute.  
**Run Time (Production Mode):** ~15-20 minutes (due to multiprocessing on 37M rows).

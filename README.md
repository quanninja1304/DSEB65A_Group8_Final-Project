# 🚀 News Popularity Analytics: The Data Engineering Strategy

> **Project Thesis:** Raw data is not an asset; it is a liability. Only through strategic transformation does it become intelligence.
>
> This project demonstrates the power of **Advanced Data Preparation** by transforming a hostile, fragmented dataset of **37.5 million records** into a high-precision strategic engine for predicting content virality.

## 🔎 Overview

In the modern attention economy, content creators face a dilemma: **How to cut through the noise?** The answer lies not in guessing, but in decoding the "physics" of information diffusion.

This project is a rigorous end-to-end data science implementation. We analyze the **["News Popularity in Multiple Social Media Platforms"](https://archive.ics.uci.edu/dataset/432/news+popularity+in+multiple+social+media+platforms)** dataset, a complex collection of social feedback logs spanning 48 hours for over 93,000 news articles.

### **The Core Challenge: "Analytically Hostile" Data**
In its raw state, this dataset actively prevents insight. It presents three fundamental barriers that disqualify it from standard analysis:
1.  **Fragmentation:** Insights are siloed across 13 separate physical files, making cross-platform benchmarking impossible.
2.  **Structural Unsuitability:** Time-series data is stored in a "Wide Format" (144 columns), preventing dynamic velocity analysis.
3.  **Integrity Decay:** Critical timestamps are stored as text, and popularity metrics are corrupted by placeholder values (`-1`).

**Our Solution:** We architected a **Local Map-Reduce Pipeline** to overcome these barriers. By engineering **15 new behavioral metrics** (including Velocity Vectors, Sentiment Divergence, and Market Saturation Scores), we transformed this raw chaos into a unified, actionable playbook for content strategy.

## 💾 The Dataset: Architecture & Anatomy

The dataset is a rare, granular log of news consumption, but its architecture is split into two distinct, disconnected layers.

### **Part A: The Metadata Layer (`News_Final.csv`)**

This is the "Anchor File" containing descriptive attributes for each of the **93,239 articles**. While it provides the core features, several columns require specific strategic handling to be useful.

| Feature Name | Data Type | Analytical Role & Strategic Handling |
| :--- | :--- | :--- |
| **`IDLink`** | `float` | **Primary Key.** The connector for joining all 13 files. <br>*Status:* Must be cast to `string` or `int` to prevent floating-point precision errors during merging. |
| **`Title`** <br> **`Headline`** | `object` | **Content DNA (Input).** Unstructured text strings representing the article's hook and summary. <br>*Status:* Analytically silent in raw form. We will apply **NLP (TextBlob)** to these columns to engineer our own `Sentiment` and `Complexity` features. |
| **`Source`** | `object` | **Context.** The publisher (e.g., 'nytimes'). <br>*Status:* Extremely high cardinality (5,700+ values) with messy variations. Requires **Entity Resolution** and grouping into **Source Tiers** (Mainstream vs. Niche). |
| **`Topic`** | `object` | **Category.** The subject matter (Economy, Microsoft, Obama, Palestine). Serves as our primary dimension for segmentation. |
| **`PublishDate`** | `object` | **Temporal Anchor.** The timestamp of publication. <br>*Status:* **Critical Failure.** Stored as a string. Must be converted to `datetime` to engineer `Hour`, `Day`, and `Market Saturation` metrics. |
| **`SentimentTitle`** <br> **`SentimentHeadline`** | `float` | **Black Box Metrics (IGNORED).** <br>*Status:* **We explicitly discard these columns.** <br>**Reasoning:** <br>1. **Unknown Methodology:** We do not know the algorithm used (e.g., VADER vs. NLTK). Different models weigh nuances like double negatives ("not bad") differently. <br>2. **Explainability:** To present a defensible story, we must use a **"White Box"** approach (TextBlob) where we can explain exactly how the score was derived. <br>3. **Consistency for Divergence:** To calculate **Sentiment Divergence** ($|Title - Headline|$), both texts must be scored by the *exact same model*. Using raw pre-computed values carries the risk of inconsistent baselines, rendering the divergence metric mathematically invalid. |
| **`Facebook`** <br> **`GooglePlus`** <br> **`LinkedIn`** | `int` | **Final Outcomes (Targets).** The total popularity score after 48 hours. <br>*Status:* <br>1. **Corrupted:** Uses `-1` as a placeholder for missing data (must be replaced with `NaN`). <br>2. **Skewed:** Follows a Power Law distribution (extreme outliers). Requires **Logarithmic Normalization** (`np.log1p`) for valid visualization. |

### **Part B: The Social Feedback Layer (12 Time-Series Files)**
These files contain the "Heartbeat" of the news—detailed, minute-by-minute popularity logs.
*   **File Structure:** `[Platform]_[Topic].csv` (e.g., `Facebook_Economy.csv`, `LinkedIn_Microsoft.csv`).
*   **Total Volume:** ~37.5 Million data points.

| Feature Name | Data Type | Analytical Role & The "Wide Format" Problem |
| :--- | :--- | :--- |
| **`IDLink`** | `int` | **Foreign Key.** Links back to the Metadata layer. |
| **`TS1` ... `TS144`** | `int` | **The Velocity Vector.** 144 columns representing sequential 20-minute time slices over a 48-hour period.<br><br>**The Structural Crisis:** This "Wide Format" is optimized for storage, not science. <br>• You cannot plot "Time" on an X-axis because Time is scattered across 144 columns.<br>• You cannot calculate "Velocity" (Rate of Change) efficiently.<br><br>**The Engineering Mandate:** We must perform a massive **Structural Transformation (`melt`)** to pivot this data into a "Long Format" (`ID` | `Time` | `Score`), unlocking the ability to model the lifecycle of virality. |

### **Summary of Data Health**
*   **Missing Values:** `-1` is used as a placeholder for "untracked," corrupting mean/sum calculations.
*   **Distribution:** Extreme Right-Skew. 90% of articles have near-zero engagement, while the top 1% have millions. Requires Logarithmic Normalization (`np.log1p`).
*   **Scale:** The integration of Part A and Part B results in a dataset that exceeds the RAM capacity of standard machines, necessitating a **Chunking Strategy**.

---

## 🛠 Engineering Pipeline: From Raw Logs to Strategic Assets

We transformed raw, fragmented logs into a high-dimensional strategic asset through a rigorous **Data Engineering Pipeline**. This process was architected to handle **Big Data (37.5M rows)** on local hardware without memory overflow.

### 1. Data Cleaning & Integration (The "Memory-First" Strategy)
*The raw data presented a critical RAM bottleneck (~37GB uncompressed across 13 "wide" files), requiring a streaming-based approach.*

#### 🧩 Smart Integration ("Melt-then-Combine")
> **🔴 The Bottleneck:** Merging 13 files in their original "Wide Format" (144 columns) would create a massive intermediate sparse matrix, causing immediate Kernel Crash on standard 16GB RAM machines.
>
> **🟢 The Engineering Solution:** We implemented an **Iterative Map-Reduce Loop**:
> 1.  **Load** a single topic file.
> 2.  **Pivot** immediately to "Long Format" using `pd.melt()`, reducing column width to 3 (`ID`, `Time`, `Score`).
> 3.  **Append** to the master list and release memory.

#### 🧹 Placeholder Sanitization
* **Detection:** Identified statistical corruption where tracking errors were recorded as `-1`.
* **Action:** Replaced `-1` with `NaN`.
* **Impact:** Ensures aggregation functions (`mean`, `sum`) remain statistically valid, preventing "negative popularity" artifacts.

#### 🔗 Entity Resolution (Source Consolidation)
* **Problem:** The `Source` column contained **5,700+ noisy variations** (e.g., *'Reuters'*, *'Reuters via Yahoo'*, *'Reuters Online'*), fragmenting the analysis.
* **Optimization Trick ("Count on Small, Apply to Big"):**
    Instead of running expensive Regex on 37M rows, we extracted unique `(ID, Source)` pairs (~90k rows), cleaned them to create a Mapping Dictionary, and **broadcasted** the map back to the master dataset.
    * ⚡ **Performance Win:** Reduced processing time from **hours to seconds**.

### 2. Advanced Feature Engineering (The Strategic Engine)
We moved beyond simple view counts to engineer **15 Behavioral & Contextual Metrics**, categorized into four strategic dimensions.

#### **A. Dynamics (The Physics of Virality)**
*Treating time-series data as velocity vectors to measure "Force" and "Friction."*

* **`Initial_Velocity` ($V_0$):** Popularity score at `TimeSlice 1` (First 20 mins). Measures the **Impulse Power** (Click-Through Rate).
* **`Stickiness_Index` ($S$):** A dimensionless ratio measuring audience retention.
  
  $$S = 1 - \left( \frac{V_0}{\text{Final Score}} \right)$$
  
  * **High $S$ ($\to 1$):** Organic growth, "Evergreen" content.
  * **Low $S$ ($\to 0$):** High drop-off, "Flash" or "Clickbait" content.

#### **B. Psycholinguistics (Content DNA)**
*Using NLP to decode the psychological triggers in headlines.*

> **💡 Optimization Hack:**
> Running `TextBlob` sentiment analysis on 37M rows is computationally prohibitive.  
> **Our Approach:** We extracted unique Article Titles (~90k), ran the NLP pipeline once per title, and merged results back using `IDLink`.  
> **🚀 Speedup: ~400x.**  

* **`Sentiment_Divergence`:** The absolute difference between `Title_Sentiment` and `Headline_Sentiment`. Used to scientifically detect **Bait-and-Switch** tactics.
* **`Title_Complexity`:** A cognitive load metric (Word Count + Avg Word Length) to test the "Keep It Simple" hypothesis vs. "Value Signaling".

#### **C. Market Ecology (Context)**
* **`Source_Tier`:** Algorithmic classification of publishers into **Tier 1 (Mainstream Goliath)** vs. **Tier 3 (Niche David)** based on total historical volume.
* **`Opportunity_Score`:** A rolling-window metric measuring Market Saturation.
    * *Logic:* Inverse of the number of competing articles published within a $\pm 2$ hour window.
    * *Output:* Classifies time slots into **Red Ocean** (High Competition) ⚔️ vs. **Blue Ocean** (Low Competition) 🌊.

#### **D. Statistical Normalization**
* **Logarithmic Transformation:** Since the popularity data followed a strict **Pareto Distribution (Power Law)** (80/20 rule), we applied `np.log1p`:
    
    $$y = \log_{10}(x + 1)$$
    
    This compresses extreme outliers, revealing the "Hidden Majority" structure for visualization.
    
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
├── A0_Project Kickoff & Initial Direction Setting.ipynb  
├── 01_EDA_Raw.ipynb                                     
├── 02_Preparation_and_Analysis.ipynb                    
├── dynamics_multicore.py                # Map-Reduce engine for parallel processing
├── custom_template.py                   # Plotly styling configuration
├── all_source_counts.txt                # Log: Raw source frequencies
├── requirements.txt
└── source_mapping.pkl                   
```

### 🔑 Key File Descriptions

- **01_EDA_Raw.ipynb**: *The "Diagnosis"*.  
Performs initial health checks on the raw data, identifying fragmentation, skewness, and structural issues.

- **02_Preparation_and_Analysis.ipynb**: *The "Master Engine"*.  
  This notebook handles the entire lifecycle:
  - **Engineering:** Orchestrates the map-reduce pipeline to clean and process 37.5M rows.  
  - **Analysis:** Generates the 8 Strategic Storyboards and visual insights (Golden Quadrant, Velocity Curves).

- **dynamics_multicore.py**: *The "Core Tech"*.  
A custom module implementing Byte-Level Chunking and Sharded Writing to enable Big Data processing on standard hardware.

- **Data/prepared/**: *The "Gold Mine"*.  
Stores the aggregated, analysis-ready datasets (CSV) used for visualization (Lightweight & Portable).
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

#### 🟢 Option A: Demo Mode (Default)
**Use Case:** Rapidly validating the pipeline logic using sample data.
- **Mechanism:** If no raw or master data is found, the pipeline (`02_Preparation...`) defaults to loading the included `master_sample.csv` (10k rows) for a quick test run.

#### 🔴 Option B: Production Mode (Full Replication)
**Use Case:** Generating the complete analysis with statistical significance.

You have two ways to run this mode:

**1. The Fast Way (Recommended):**
* Download the **Pre-computed Master Dataset (4.5GB)** from [Google Drive Link](https://drive.google.com/drive/folders/187zJd0BC5UG2-X-eAVeEbjyWo-Uc1WEz).
* Place it at: 
```text
Data/prepared/master_df_consolidated.csv
```
* **Result:** The code detects the file and **loads it immediately**, skipping the heavy data engineering steps.

**2. The Hard Way (Build from Scratch):**
* If you do **NOT** download the master file, the code will trigger the **Data Engineering Engine**.
* **Result:** It will process all raw source files to **re-generate** the master dataset.
* *Warning: This process takes ~15-20 minutes depending on your CPU.*

> [!NOTE]
> **Technical Note:** Intermediate processing files (`*.pkl`) are excluded via `.gitignore`. The pipeline is designed to rebuild them automatically if they are missing.

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

--- 

## 📜 License

This project is licensed under the **MIT License** — see the `LICENSE` file for details.
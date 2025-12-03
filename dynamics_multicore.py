# dynamics_multicore.py
import pandas as pd
import os
from io import BytesIO
from textblob import TextBlob


def get_file_chunks(file_path, n_chunks):
    """
    Splits a file into n_chunks byte ranges, aligning to newlines.
    """
    file_size = os.path.getsize(file_path)
    chunk_size = file_size // n_chunks

    offsets = []
    with open(file_path, "rb") as f:
        current_pos = 0
        for i in range(n_chunks):
            start = current_pos
            if i == n_chunks - 1:
                offsets.append((start, file_size - start))
                break

            f.seek(start + chunk_size)
            f.readline()  # Read until newline
            end = f.tell()

            offsets.append((start, end - start))
            current_pos = end

    return offsets


def read_csv_chunk(file_path, start_byte, num_bytes, header_names, use_cols=None):
    """
    Reads a byte range. If start_byte > 0, assigns header_names manually.
    """
    with open(file_path, "rb") as f:
        f.seek(start_byte)
        data = f.read(num_bytes)

    # If we are at the start, let pandas find the header.
    # If we are in the middle, tell pandas there is no header, and provide names.
    if start_byte == 0:
        return pd.read_csv(BytesIO(data), usecols=use_cols)
    else:
        return pd.read_csv(BytesIO(data), header=None, names=header_names, usecols=use_cols)


def process_phase1_range(file_path, start_byte, num_bytes, header_names):
    """
    Worker for Phase 1: Read byte range -> Calculate Partial Metrics
    """
    calc_cols = ["IDLink", "Platform", "TimeSlice", "Popularity"]

    try:
        chunk = read_csv_chunk(file_path, start_byte, num_bytes, header_names, use_cols=calc_cols)
    except pd.errors.EmptyDataError:
        return None, None

    if chunk.empty:
        return None, None

    # 1. Initial Velocity Candidates
    v_chunk = chunk[chunk["TimeSlice"] == 1][["IDLink", "Platform", "Popularity"]].copy()
    v_chunk.rename(columns={"Popularity": "Initial_Velocity"}, inplace=True)

    # 2. Partial Max Scores
    m_chunk = chunk.groupby(["IDLink", "Platform"])["Popularity"].max().reset_index()
    m_chunk.rename(columns={"Popularity": "Final_Score"}, inplace=True)

    return v_chunk, m_chunk


def process_phase2_merge(file_path, start_byte, num_bytes, header_names, metrics_df, output_path, cols_to_clean):
    """
    Worker for Phase 2: Read byte range -> Merge Metrics -> Write Shard
    """
    try:
        chunk = read_csv_chunk(file_path, start_byte, num_bytes, header_names, use_cols=None)
    except pd.errors.EmptyDataError:
        return

    if chunk.empty:
        return

    existing = [c for c in cols_to_clean if c in chunk.columns]
    if existing:
        chunk.drop(columns=existing, inplace=True)

    merged_chunk = pd.merge(chunk, metrics_df, on=["IDLink", "Platform"], how="left")

    # Write without header to allow easy concatenation later
    merged_chunk.to_csv(output_path, mode="w", index=False, header=False)



def process_extract_unique_nlp(file_path, start_byte, num_bytes, header_names):
    """
    Worker: Reads a chunk, extracts ID, Title, Headline, and performs local deduplication.
    """
    use_cols = ["IDLink", "Title", "Headline"]
    try:
        chunk = read_csv_chunk(file_path, start_byte, num_bytes, header_names, use_cols=use_cols)
    except pd.errors.EmptyDataError:
        return None

    if chunk.empty:
        return None

    # Return only unique IDs within this chunk to save memory during transfer
    return chunk.drop_duplicates(subset=["IDLink"])


def process_nlp_calculation(df_chunk):
    """
    Worker: Calculates Sentiment and Complexity on a chunk of unique articles.
    """

    # Helper functions nested or local to ensure pickle compatibility
    def get_sentiment(text):
        try:
            return TextBlob(str(text)).sentiment.polarity
        except:
            return 0.0

    def get_complexity(text):
        try:
            s = str(text)
            words = s.split()
            if not words:
                return 0.0
            avg_len = sum(len(w) for w in words) / len(words)
            return len(words) + avg_len
        except:
            return 0.0

    # Avoid SettingWithCopyWarning
    df = df_chunk.copy()

    # Calculate
    df["Title_Sentiment"] = df["Title"].apply(get_sentiment)
    df["Headline_Sentiment"] = df["Headline"].apply(get_sentiment)
    df["Sentiment_Divergence"] = (df["Title_Sentiment"] - df["Headline_Sentiment"]).abs()
    df["Title_Complexity"] = df["Title"].apply(get_complexity)

    # Return only the calculated features + key
    return df[["IDLink", "Title_Sentiment", "Sentiment_Divergence", "Title_Complexity"]]


def process_nlp_merge(file_path, start_byte, num_bytes, header_names, nlp_df, output_path, cols_to_clean):
    """
    Worker: Merges NLP features back into the master dataset shards.
    """
    try:
        chunk = read_csv_chunk(file_path, start_byte, num_bytes, header_names, use_cols=None)
    except pd.errors.EmptyDataError:
        return

    if chunk.empty:
        return

    # Drop existing NLP columns if they exist (to prevent duplicates during re-runs)
    existing = [c for c in cols_to_clean if c in chunk.columns]
    if existing:
        chunk.drop(columns=existing, inplace=True)

    # Efficient Left Merge
    merged_chunk = pd.merge(chunk, nlp_df, on="IDLink", how="left")

    # Fill NaNs created by the merge (if any ID didn't have text data) with 0
    fill_cols = ["Title_Sentiment", "Sentiment_Divergence", "Title_Complexity"]
    # Note: Using a loop is safer than fillna(dict) in recent pandas versions for memory
    for c in fill_cols:
        if c in merged_chunk.columns:
            merged_chunk[c] = merged_chunk[c].fillna(0.0)

    # Write shard
    merged_chunk.to_csv(output_path, mode="w", index=False, header=False)


def process_extract_unique_date(file_path, start_byte, num_bytes, header_names):
    """
    Worker: Reads a chunk, extracts ID and PublishDate.
    """
    use_cols = ['IDLink', 'PublishDate']
    try:
        chunk = read_csv_chunk(file_path, start_byte, num_bytes, header_names, use_cols=use_cols)
    except pd.errors.EmptyDataError:
        return None
        
    if chunk.empty:
        return None
        
    return chunk.drop_duplicates(subset=['IDLink'])

def process_market_merge(file_path, start_byte, num_bytes, header_names, market_df, output_path, cols_to_clean):
    """
    Worker: Merges Market features back into the master dataset shards.
    """
    try:
        chunk = read_csv_chunk(file_path, start_byte, num_bytes, header_names, use_cols=None)
    except pd.errors.EmptyDataError:
        return

    if chunk.empty:
        return

    # Drop existing columns if they exist
    existing = [c for c in cols_to_clean if c in chunk.columns]
    if existing:
        chunk.drop(columns=existing, inplace=True)

    # Efficient Left Merge
    merged_chunk = pd.merge(chunk, market_df, on="IDLink", how="left")
    
    # Fill NaNs
    # If date was missing, Opportunity Score is technically unknown. 
    # We can fill with 0 or the median. 
    # Given the formula 1/count, 0 implies "infinite saturation" (worst case), which is a safe safe-fail.
    if 'Opportunity_Score' in merged_chunk.columns:
        merged_chunk['Opportunity_Score'] = merged_chunk['Opportunity_Score'].fillna(0.0)

    # Write shard
    merged_chunk.to_csv(output_path, mode='w', index=False, header=False)



def process_content_sampling(file_path, start_byte, num_bytes, header_names):
    """
    Worker for Phase 1: Reads a byte range and returns a 1% random sample
    of the Complexity column. Used to determine quantiles.
    """
    cols = ['Title_Complexity']
    try:
        chunk = read_csv_chunk(file_path, start_byte, num_bytes, header_names, use_cols=cols)
    except pd.errors.EmptyDataError:
        return None

    if chunk.empty:
        return None

    # Filter out 0.0s (artifacts/nulls) to get true distribution
    valid_data = chunk[chunk['Title_Complexity'] > 0]
    
    if valid_data.empty:
        return None
        
    # Return 1% sample
    return valid_data.sample(frac=0.01, random_state=42)


def process_content_aggregation(file_path, start_byte, num_bytes, header_names, comp_low, comp_high):
    """
    Worker for Phase 2: Reads a byte range, bins the data, and returns 
    aggregated sums and counts for both Sentiment and Complexity.
    """
    # Columns needed for binning and metrics
    cols_to_use = [
        'Platform', 
        'Title_Sentiment', 'Title_Complexity', 
        'Popularity', 'Initial_Velocity', 'Stickiness_Index'
    ]
    
    metric_cols = ['Popularity', 'Initial_Velocity', 'Stickiness_Index']

    try:
        chunk = read_csv_chunk(file_path, start_byte, num_bytes, header_names, use_cols=cols_to_use)
    except pd.errors.EmptyDataError:
        return None

    if chunk.empty:
        return None

    # --- 1. Sentiment Binning ---
    # Fixed thresholds: Negative < -0.1, Positive > 0.1
    chunk['Sentiment_Bin'] = pd.cut(
        chunk['Title_Sentiment'], 
        bins=[-float('inf'), -0.1, 0.1, float('inf')], 
        labels=['Negative', 'Neutral', 'Positive']
    )

    # --- 2. Complexity Binning ---
    # Dynamic thresholds passed from main thread
    chunk['Complexity_Bin'] = pd.cut(
        chunk['Title_Complexity'],
        bins=[-float('inf'), comp_low, comp_high, float('inf')],
        labels=['Simple', 'Standard', 'Complex']
    )

    # --- 3. Local Aggregation ---
    # We return the Sums and Counts. The main thread will calculate the weighted Mean.
    
    # Group by Platform + Sentiment
    sent_agg = chunk.groupby(['Platform', 'Sentiment_Bin'], observed=False)[metric_cols].agg(['sum', 'count'])
    
    # Group by Platform + Complexity
    comp_agg = chunk.groupby(['Platform', 'Complexity_Bin'], observed=False)[metric_cols].agg(['sum', 'count'])

    return sent_agg, comp_agg



def process_context_aggregation(file_path, start_byte, num_bytes, header_names):
    """
    Worker for Section 5.3: Aggregates data for Time (Hour/Day), 
    Source (Tier), and Market (Opportunity) in a single pass.
    """
    cols_to_use = [
        'Platform', 'PublishDate', 
        'Source_Tier', 'Opportunity_Score',
        'Popularity', 'Initial_Velocity', 'Stickiness_Index'
    ]
    metric_cols = ['Popularity', 'Initial_Velocity', 'Stickiness_Index']

    try:
        chunk = read_csv_chunk(file_path, start_byte, num_bytes, header_names, use_cols=cols_to_use)
    except pd.errors.EmptyDataError:
        return None

    if chunk.empty:
        return None

    # --- Pre-processing ---
    # 1. Date Extraction
    chunk['PublishDate'] = pd.to_datetime(chunk['PublishDate'], errors='coerce')
    chunk = chunk.dropna(subset=['PublishDate'])
    chunk['hour_of_day'] = chunk['PublishDate'].dt.hour
    chunk['day_of_week'] = chunk['PublishDate'].dt.day_name()

    # 2. Opportunity Binning (Physical Meaning)
    # Score = 1/N. 
    # < 0.02 means > 50 competitors (Red Ocean)
    # > 0.1 means < 10 competitors (Blue Ocean)
    chunk['Opportunity_Bin'] = pd.cut(
        chunk['Opportunity_Score'],
        bins=[-float('inf'), 0.02, 0.1, float('inf')],
        labels=['Red Ocean (High Comp)', 'Average', 'Blue Ocean (Low Comp)']
    )

    # --- Aggregations ---
    
    # 1. Hourly
    agg_hourly = chunk.groupby(['Platform', 'hour_of_day'], observed=False)[metric_cols].agg(['sum', 'count'])
    
    # 2. Weekly
    agg_weekly = chunk.groupby(['Platform', 'day_of_week'], observed=False)[metric_cols].agg(['sum', 'count'])
    
    # 3. Source Tier
    agg_source = chunk.groupby(['Platform', 'Source_Tier'], observed=False)[metric_cols].agg(['sum', 'count'])
    
    # 4. Opportunity
    agg_opp = chunk.groupby(['Platform', 'Opportunity_Bin'], observed=False)[metric_cols].agg(['sum', 'count'])

    return agg_hourly, agg_weekly, agg_source, agg_opp




def process_quadrant_extraction(file_path, start_byte, num_bytes, header_names):
    """
    Worker for Section 5.4: Extracts a random 2% sample of article metrics.
    We oversample here (2%) to allow for precise stratified downsampling 
    in the main thread later.
    """
    cols_to_use = [
        'IDLink', 'Platform', 'Title', 'Source_Tier', 
        'Popularity', 'Initial_Velocity', 'Stickiness_Index',
        'Title_Sentiment', 'Title_Complexity', 'Opportunity_Score',
        'Sentiment_Divergence', 'Final_Score'
    ]

    try:
        chunk = read_csv_chunk(file_path, start_byte, num_bytes, header_names, use_cols=cols_to_use)
    except pd.errors.EmptyDataError:
        return None

    if chunk.empty:
        return None

    # Filter: We only want valid metrics for the scatter plot
    # Drop rows where Velocity or Stickiness might be null (rare, but possible)
    chunk = chunk.dropna(subset=['Initial_Velocity', 'Stickiness_Index'])
    
    # Sampling: Take 2% of this chunk
    # Random state is not fixed here to ensure randomness across different file offsets if needed,
    # but fixing it per chunk is safer for reproducibility.
    return chunk.sample(frac=0.02, random_state=42)


def process_topic_lifecycle(file_path, start_byte, num_bytes, header_names):
    """
    Worker for Section 5.2.2: Aggregates Popularity by Topic and TimeSlice.
    Used to generate the Lifecycle Growth Curves.
    """
    # We need Topic, TimeSlice (to track time), and Popularity (to measure growth)
    cols_to_use = ['Topic', 'TimeSlice', 'Popularity']

    try:
        chunk = read_csv_chunk(file_path, start_byte, num_bytes, header_names, use_cols=cols_to_use)
    except pd.errors.EmptyDataError:
        return None

    if chunk.empty:
        return None

    # Remove "TS" prefix from TimeSlice if it exists and convert to int
    if chunk['TimeSlice'].dtype == 'object':
        chunk['TimeSlice'] = chunk['TimeSlice'].astype(str).str.replace('TS', '', regex=False)
    
    # Force numeric conversion for safety
    chunk['TimeSlice'] = pd.to_numeric(chunk['TimeSlice'], errors='coerce')
    chunk = chunk.dropna(subset=['TimeSlice', 'Popularity'])
    chunk['TimeSlice'] = chunk['TimeSlice'].astype(int)

    # Group by Topic + TimeSlice
    # We calculate Sum and Count to allow weighted averaging later
    return chunk.groupby(['Topic', 'TimeSlice'], observed=False)['Popularity'].agg(['sum', 'count'])

# --- APPEND TO dynamics_multicore.py ---

def process_platform_lifecycle(file_path, start_byte, num_bytes, header_names):
    """
    Worker for Section 5.4.2: Aggregates Popularity by Platform and TimeSlice.
    """
    cols_to_use = ['Platform', 'TimeSlice', 'Popularity']

    try:
        chunk = read_csv_chunk(file_path, start_byte, num_bytes, header_names, use_cols=cols_to_use)
    except pd.errors.EmptyDataError:
        return None

    if chunk.empty:
        return None

    # Clean TimeSlice
    if chunk['TimeSlice'].dtype == 'object':
        chunk['TimeSlice'] = chunk['TimeSlice'].astype(str).str.replace('TS', '', regex=False)
    
    chunk['TimeSlice'] = pd.to_numeric(chunk['TimeSlice'], errors='coerce')
    chunk = chunk.dropna(subset=['TimeSlice', 'Popularity'])
    chunk['TimeSlice'] = chunk['TimeSlice'].astype(int)

    # Group by Platform + TimeSlice
    return chunk.groupby(['Platform', 'TimeSlice'], observed=False)['Popularity'].agg(['sum', 'count'])
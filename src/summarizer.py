import pandas as pd
import json
from pathlib import Path
from tqdm import tqdm

# Note: Most functions here are suitable from the previous thought process.
# We will just ensure they align with the expected DataFrame structure after sentiment analysis.

def calculate_overall_sentiment(df, college_col='college_name_approx', sentiment_col='compound_sentiment'):
    """Calculates average overall sentiment per college."""
    if college_col not in df.columns or sentiment_col not in df.columns or df.empty:
        print(f"Warning/Error: Cannot calculate overall sentiment. Check columns ('{college_col}', '{sentiment_col}') and data.")
        return pd.Series(dtype=float)

    print("Calculating overall sentiment per college...")
    try:
        # Ensure sentiment column is numeric before grouping
        df[sentiment_col] = pd.to_numeric(df[sentiment_col], errors='coerce')
        overall_scores = df.groupby(college_col)[sentiment_col].mean().dropna().sort_values(ascending=False)
        return overall_scores
    except Exception as e:
        print(f"Error during overall sentiment calculation: {e}")
        return pd.Series(dtype=float)


def calculate_aspect_sentiment_summary(df, college_col='college_name_approx', aspect_cols_prefix=''):
    """Calculates average aspect sentiment per college."""
    if college_col not in df.columns or df.empty:
        print(f"Warning/Error: Cannot calculate aspect summary. Check college column ('{college_col}') and data.")
        return pd.DataFrame()

    print("Calculating average aspect sentiment per college...")
    # Auto-detect aspect columns (now ending with '_sentiment')
    aspect_cols = [col for col in df.columns if col.endswith('_sentiment') and col != 'compound_sentiment']

    if not aspect_cols:
        print("Error: No aspect sentiment columns (ending with '_sentiment') found.")
        return pd.DataFrame()

    try:
        # Ensure aspect columns are numeric
        for col in aspect_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        aspect_summary = df.groupby(college_col)[aspect_cols].mean().dropna(how='all') # Drop rows where all aspects are NaN
        # Clean up column names for readability
        aspect_summary.columns = [col.replace('_sentiment', '') for col in aspect_summary.columns]
        return aspect_summary
    except Exception as e:
        print(f"Error during aspect sentiment summary calculation: {e}")
        return pd.DataFrame()

def calculate_sentiment_trends(df, time_col='created_utc', sentiment_col='compound_sentiment', freq='M'):
    """Calculates sentiment trends over time."""
    if time_col not in df.columns or sentiment_col not in df.columns or df.empty:
        print(f"Warning/Error: Cannot calculate trends. Check columns ('{time_col}', '{sentiment_col}') and data.")
        return pd.DataFrame()

    print(f"Calculating sentiment trends (frequency: {freq})...")
    try:
        df_trends = df[[time_col, sentiment_col]].copy()
        df_trends['datetime'] = pd.to_datetime(df_trends[time_col], unit='s', errors='coerce')
        df_trends = df_trends.dropna(subset=['datetime', sentiment_col]) # Drop if date or sentiment is invalid
        if df_trends.empty:
            print("Warning: No valid datetime/sentiment data found for trends.")
            return pd.DataFrame()

        df_trends = df_trends.set_index('datetime')
        trends = df_trends[sentiment_col].resample(freq).agg(['mean', 'count'])
        trends.columns = ['mean_sentiment', 'comment_count']
        # Consider filtering out periods with low comment counts for more stable trends
        # trends = trends[trends['comment_count'] >= 5] # Example threshold
        return trends.dropna(subset=['mean_sentiment']) # Remove periods with no comments

    except Exception as e:
        print(f"Error calculating sentiment trends: {e}")
        return pd.DataFrame()

def find_top_reviews(df, n=5, college_col='college_name_approx', sentiment_col='compound_sentiment', text_col='text', permalink_col='permalink'):
    """Finds top N positive/negative reviews per college."""
    required_cols = [college_col, sentiment_col, text_col, permalink_col]
    if not all(col in df.columns for col in required_cols) or df.empty:
        print(f"Warning/Error: Cannot find top reviews. Check columns ({required_cols}) and data.")
        return {}

    print(f"Finding top {n} positive and negative reviews per college...")
    top_reviews = {}
    # Ensure sentiment is numeric
    df[sentiment_col] = pd.to_numeric(df[sentiment_col], errors='coerce')
    df_valid_sentiment = df.dropna(subset=[sentiment_col]) # Only consider reviews with valid scores

    grouped = df_valid_sentiment.groupby(college_col)

    for name, group in tqdm(grouped, desc="Finding Top Reviews", unit="college"):
        # Sort by sentiment score
        sorted_group = group.sort_values(sentiment_col, ascending=False)

        # Select columns to include in the output
        review_cols = [text_col, sentiment_col, permalink_col]

        # Get top N positive (highest scores)
        top_positive = sorted_group.head(n)[review_cols].to_dict('records')

        # Get top N negative (lowest scores) - use tail() on ascending sort, then re-sort tail
        top_negative = sorted_group.tail(n).sort_values(sentiment_col, ascending=True)[review_cols].to_dict('records')

        top_reviews[name] = {
            'positive': top_positive,
            'negative': top_negative
        }
    return top_reviews

def save_analysis_results(results, output_path):
    """Saves analysis results (like top reviews) to a JSON file."""
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            # Use default=str to handle potential non-serializable types like numpy floats
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        print(f"Successfully saved analysis results to {output_path}")
    except Exception as e:
        print(f"Error saving analysis results to {output_path}: {e}")
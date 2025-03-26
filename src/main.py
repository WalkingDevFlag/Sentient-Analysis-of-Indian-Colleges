import json
import time
import sys
from pathlib import Path
import nltk
import csv
import pandas as pd
import warnings
import re
from tqdm import tqdm

# --- Import Project Modules (Relative imports from within src/) ---
try:
    from reddit_scraper import run_scraper # <--- src. prefix added
    from cleaner import preprocess_text # <--- src.preprocessing. prefix
    from analyzer import apply_sentiment_analysis_to_df, ASPECT_KEYWORDS, download_nltk_resources as download_sentiment_nltk # <--- src.sentiment. prefix
    from summarizer import ( # <--- src.analysis. prefix
        calculate_overall_sentiment,
        calculate_aspect_sentiment_summary,
        calculate_sentiment_trends,
        find_top_reviews,
        save_analysis_results
    )
    from plotter import ( # <--- src.visualization. prefix
        plot_overall_sentiment,
        plot_aspect_sentiment,
        plot_sentiment_trends,
        plot_word_clouds_for_top_reviews
    )
    # Import scrape_nirf if you want to optionally run it from main
    # from .scrape_nirf import run_nirf_script # Example name
except ImportError as e:
    print(f"Error importing project modules within src/: {e}")
    print("Ensure all required .py files and __init__.py exist in the 'src/' directory.")
    sys.exit(1)

# --- Configuration (Paths relative to project root) ---
# Use Path(__file__).parent.parent to get project root from src/main.py
PROJECT_ROOT = Path(__file__).parent.parent

# Phase 1: Scraping & Preprocessing
RAW_DATA_FILE = PROJECT_ROOT / "data" / "raw_scraped" / "college_comments_raw.json"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
SAVE_PROCESSED_AS_CSV = True
PROCESSED_FILE_SUFFIX = '.csv' if SAVE_PROCESSED_AS_CSV else '.json'
PROCESSED_DATA_FILE = PROCESSED_DATA_DIR / f"reddit_comments_processed{PROCESSED_FILE_SUFFIX}"

# Preprocessing Options
USE_LEMMATIZATION = True
USE_STEMMING = False

# Phase 2: Analysis & Visualization
VIS_OUTPUT_DIR = PROJECT_ROOT / "output" / "visualizations"
ANALYSIS_OUTPUT_DIR = PROJECT_ROOT / "output" / "analysis_results"
TOP_N_REVIEWS = 5
TREND_FREQUENCY = 'M'

# Column Names
TEXT_COL = 'text'
TOKENS_COL = 'processed_tokens'
COLLEGE_COL = 'college_name_approx'
TIME_COL = 'created_utc'
PERMALINK_COL = 'permalink'

# Create directories
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
VIS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
# Ensure reference dir exists for scraper map file
(PROJECT_ROOT / "data" / "reference").mkdir(parents=True, exist_ok=True)


# --- NLTK Data Check ---
def check_nltk_data():
    """Checks required NLTK data. Now calls analyzer's download too."""
    print("--- Checking NLTK Data ---")
    # Call the download/check function from analyzer.py first
    print("Checking resources needed for Sentiment Analysis (VADER, Punkt)...")
    download_sentiment_nltk() # This handles vader and punkt

    # Check additional resources needed for preprocessing/other tasks
    resources_preproc = {
        'corpora/stopwords': 'stopwords',
        'corpora/wordnet': 'wordnet',
        'corpora/omw-1.4': 'omw-1.4'
    }
    all_found = True
    missing_items = []
    print("\nChecking resources needed for Preprocessing...")
    for path_key, download_key in resources_preproc.items():
        try:
            nltk.data.find(path_key)
            print(f"[OK] NLTK: {download_key}")
        except LookupError:
            print(f"[Missing] NLTK: {download_key}")
            missing_items.append(download_key)
            all_found = False

    if not all_found:
        print(f"\nAttempting NLTK download: {', '.join(missing_items)}")
        download_success = True
        for item in missing_items:
            try:
                print(f"Downloading '{item}'...")
                if not nltk.download(item, quiet=True): download_success = False
            except Exception as e: print(f"Error downloading {item}: {e}"); download_success = False
        if not download_success: print("\nError: Failed NLTK download."); return False
        else: print("NLTK download attempt finished.")

    print("All required NLTK resources seem available.")
    return True


# --- Helper Function to Load Processed Data ---
def load_processed_data(filepath):
    # ... (load_processed_data function remains the same) ...
    filepath = Path(filepath)
    print(f"\n--- Loading Processed Data from: {filepath} ---")
    if not filepath.exists(): print(f"Error: Input file not found: {filepath}"); return None
    try:
        if filepath.suffix == '.csv': df = pd.read_csv(filepath, low_memory=False)
        elif filepath.suffix == '.json': df = pd.read_json(filepath, orient='records')
        else: print(f"Error: Unsupported format: {filepath.suffix}"); return None
        print(f"Successfully loaded {len(df)} processed records.")
        if TEXT_COL not in df.columns: print(f"Error: Text column '{TEXT_COL}' missing."); return None
        df[TEXT_COL] = df[TEXT_COL].fillna('')
        return df
    except Exception as e: print(f"Error loading {filepath}: {e}"); return None

# --- Combined Main Pipeline Function ---
def run_full_pipeline():
    """Orchestrates the entire workflow: Scrape -> Preprocess -> Analyze -> Visualize."""
    full_start_time = time.time()
    warnings.filterwarnings("ignore", category=FutureWarning)

    # --- Preparations ---
    if not check_nltk_data():
        print("\nExiting pipeline: Missing critical NLTK data.")
        return

    # === PHASE 1: SCRAPING & PREPROCESSING ===
    print("\n" + "="*20 + " PHASE 1: SCRAPING & PREPROCESSING " + "="*20)
    phase1_start_time = time.time()

    # 1. Run Scraper (ensure reddit_scraper.py is correctly placed and imported)
    print("\n--- Starting Reddit Scraping ---")
    # run_scraper is imported from src.reddit_scraper
    raw_data_path = run_scraper() # This saves raw data and returns the path
    if not raw_data_path or not raw_data_path.exists():
        print("\nScraping failed or produced no data. Exiting pipeline.")
        return
    print("--- Reddit Scraping Finished ---")

    # 2. Load Raw Scraped Data
    print(f"\n--- Loading Raw Data from {raw_data_path} ---")
    try:
        with open(raw_data_path, 'r', encoding='utf-8') as f: raw_data = json.load(f)
        print(f"Loaded data for {len(raw_data)} sources from raw file.")
    except Exception as e: print(f"Error loading raw data file {raw_data_path}: {e}"); return

    # 3. Preprocessing
    print(f"\n--- Starting Preprocessing ---")
    processed_data_list = []
    for source_key, comments_list in tqdm(raw_data.items(), desc="Sources Preprocessing", unit="source"):
        college_name, subreddit_name = source_key, "Unknown" # Defaults
        match = re.match(r"(.*)\s\(r/(\w+)\)", source_key)
        if match: college_name, subreddit_name = match.group(1).strip(), match.group(2)
        else: print(f"\nWarning: Could not parse source key '{source_key}'.")

        for comment in comments_list:
            try:
                original_text = comment.get(TEXT_COL, '')
                if not original_text: continue
                # Apply preprocessing function from src.cleaner
                processed_tokens_list = preprocess_text(original_text, use_lemmatization=USE_LEMMATIZATION)
                processed_item = comment.copy()
                processed_item[TOKENS_COL] = ' '.join(processed_tokens_list) if SAVE_PROCESSED_AS_CSV else processed_tokens_list
                processed_item['source_key'] = source_key
                processed_item['college_name_approx'] = college_name
                processed_item['subreddit_scraped'] = subreddit_name
                processed_data_list.append(processed_item)
            except Exception as e: print(f"\nError preprocessing comment {comment.get('id', 'N/A')}: {e}")
    print("--- Preprocessing Complete ---")

    # 4. Save Processed Data
    if not processed_data_list: print("\nNo data preprocessed. Cannot proceed."); return
    print(f"\n--- Saving {len(processed_data_list)} Processed Items ---")
    try:
        if SAVE_PROCESSED_AS_CSV:
            headers = list(processed_data_list[0].keys()) if processed_data_list else []
            if headers:
                with open(PROCESSED_DATA_FILE, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
                    writer.writeheader(); writer.writerows(processed_data_list)
                print(f"Saved processed data to CSV: {PROCESSED_DATA_FILE}")
            else: print("Error writing CSV: No data.")
        else:
            with open(PROCESSED_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(processed_data_list, f, indent=2, ensure_ascii=False)
            print(f"Saved processed data to JSON: {PROCESSED_DATA_FILE}")
    except Exception as e: print(f"\nError saving processed data: {e}"); return

    phase1_end_time = time.time()
    print(f"--- Phase 1 Finished in {(phase1_end_time - phase1_start_time):.2f} seconds ---")


    # === PHASE 2: ANALYSIS & VISUALIZATION ===
    print("\n" + "="*20 + " PHASE 2: ANALYSIS & VISUALIZATION " + "="*20)
    phase2_start_time = time.time()

    # 5. Load Processed Data
    df = load_processed_data(PROCESSED_DATA_FILE)
    if df is None: print("Exiting pipeline: Failed to load processed data."); return

    # 6. Apply Sentiment Analysis (from src.analyzer)
    df_analyzed = apply_sentiment_analysis_to_df(df, text_col=TEXT_COL)
    if 'compound_sentiment' not in df_analyzed.columns: print("Error: Sentiment analysis failed."); return

    # 7. Perform Summarization / Analysis (from src.summarizer)
    print("\n--- Performing Analysis & Summarization ---")
    overall_scores = calculate_overall_sentiment(df_analyzed, college_col=COLLEGE_COL)
    aspect_summary = calculate_aspect_sentiment_summary(df_analyzed, college_col=COLLEGE_COL)
    sentiment_trends = calculate_sentiment_trends(df_analyzed, time_col=TIME_COL, freq=TREND_FREQUENCY)
    top_reviews = find_top_reviews(df_analyzed, n=TOP_N_REVIEWS, college_col=COLLEGE_COL, text_col=TEXT_COL, permalink_col=PERMALINK_COL)
    if top_reviews: save_analysis_results(top_reviews, ANALYSIS_OUTPUT_DIR / "top_reviews_per_college.json")

    # 8. Generate Visualizations (from src.plotter)
    print("\n--- Generating Visualizations ---")
    if not overall_scores.empty: plot_overall_sentiment(overall_scores, VIS_OUTPUT_DIR / "overall_sentiment_by_college.png")
    else: print("Skipping overall plot.")
    if not aspect_summary.empty: plot_aspect_sentiment(aspect_summary, VIS_OUTPUT_DIR / "aspect_sentiment_heatmap.png")
    else: print("Skipping aspect plot.")
    if not sentiment_trends.empty: plot_sentiment_trends(sentiment_trends, VIS_OUTPUT_DIR / "sentiment_trends_over_time.png")
    else: print("Skipping trends plot.")
    if top_reviews:
         plot_word_clouds_for_top_reviews(
             top_reviews_dict=top_reviews, df_processed=df_analyzed,
             output_dir=VIS_OUTPUT_DIR / "word_clouds", college_col=COLLEGE_COL,
             tokens_col=TOKENS_COL, text_col=TEXT_COL
         )
    else: print("Skipping word clouds.")

    phase2_end_time = time.time()
    print(f"--- Phase 2 Finished in {(phase2_end_time - phase2_start_time):.2f} seconds ---")

    # --- Pipeline Finish ---
    full_end_time = time.time()
    print("\n" + "="*20 + " FULL PIPELINE FINISHED " + "="*20)
    print(f"Total execution time: {(full_end_time - full_start_time):.2f} seconds")
    print(f"Outputs -> Processed Data: {PROCESSED_DATA_FILE}")
    print(f"Outputs -> Analysis JSON: {ANALYSIS_OUTPUT_DIR}")
    print(f"Outputs -> Visualizations: {VIS_OUTPUT_DIR}")


# --- Entry Point ---
if __name__ == "__main__":
    # This allows running the script directly from the project root: python src/main.py
    # OR navigating into src and running: python main.py
    print("--- Starting Full Indian College Review Pipeline (Reddit) ---")
    run_full_pipeline()
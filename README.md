# Sentient-Analysis-of-Indian-Colleges

This project scrapes comments potentially related to specific **Indian colleges** from Reddit using PRAW, preprocesses the text, performs sentiment analysis using VADER and aspect keyword matching, generates summary statistics and trends, and visualizes the results.

**The entire workflow (Scrape -> Preprocess -> Analyze -> Visualize) is orchestrated by running the single `src/main.py` script.**

## Project Structure

```bash
Sentient-Analysis-of-Indian-Colleges/
├── src/
│	 ├── reddit_scraper.py                  # Reddit scraper module
│   ├── cleaner.py        	 # (Code provided previously)
│   ├── analyzer.py       	 # (Code provided previously)
│   ├── summarizer.py     	 # (Code provided previously)
│   ├── plotter.py        	 # (Code provided previously)
│	 ├── main.py               # <<< Consolidated Main Script >>>
│	 └── scrape_nirf.py        # (Code provided previously)
├── output/                   # Generated results & visualizations
│   ├── analysis_results/
│   │   └── .gitkeep
│   └── visualizations/
│       └── .gitkeep
├── data/                     # Intermediate data storage
│   ├── reference/
│   │   ├── nirf_eng_top100_names_2024.json
│   │   └── college_subreddit_map_auto_generated.json
│   ├── raw_scraped/
│   │   └── college_comments_raw.json
│   └── processed/
│       └── reddit_comments_processed.csv # Or .json
├── requirements.txt          # (Should include all dependencies)
├── README.md                 # <<< Updated README below >>>
├── .env                      # Stores Reddit API credentials
└── .gitignore                # (Include data/, output/, .env, venv/, __pycache__/)
```

## Setup Instructions

1.  **Clone Repository & Navigate:**
    ```bash
    git clone <your-repository-url>
    cd indian-college-reddit
    ```

2.  **Create Virtual Environment:**
    ```bash
    # Windows: python -m venv venv && .\venv\Scripts\activate
    # macOS/Linux: python3 -m venv venv && source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Reddit API Credentials (Highly Recommended):**
    *   Create a Reddit "script" app: [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps).
    *   Get `client_id` and `client_secret`.
    *   Create `.env` file in project root:
        ```dotenv
        # .env
        REDDIT_CLIENT_ID=your_client_id_here
        REDDIT_CLIENT_SECRET=your_client_secret_here
        REDDIT_USER_AGENT=YourUniqueUserAgentString like MyScraper/0.1 by u/YourUsername
        ```
    *   Ensure `.env` is in `.gitignore`.

5.  **Download NLTK Data:**
    *   The `src/main.py` script attempts auto-download on first run.
    *   If it fails, run manually in Python (with venv active):
        ```python
        import nltk
        nltk.download('punkt'); nltk.download('stopwords'); nltk.download('vader_lexicon'); nltk.download('wordnet'); nltk.download('omw-1.4')
        ```

## Running the Project

Execute these steps from the project root directory (`indian-college-reddit/`).

### Step 1: Generate College List & Subreddit Map (Run `src/scrape_nirf.py`)

This fetches NIRF names and attempts to auto-find corresponding subreddits.

1.  **Run:**
    ```bash
    python src/scrape_nirf.py
    ```
2.  **Output:** Creates `data/reference/nirf_eng_top100_names_2024.json` and `data/reference/college_subreddit_map_auto_generated.json`.

### Step 2: Review Auto-Generated Subreddit Map (Manual Task - Recommended)(Optional to be honest)

Crucial for data quality!

1.  **Open:** `data/reference/college_subreddit_map_auto_generated.json`.
2.  **Review & Edit:** Correct subreddit names, remove bad matches. Save changes *to this file*.

### Step 3: Run the Full Pipeline (Run `src/main.py`)

This single script orchestrates scraping, preprocessing, analysis, and visualization using the map file generated/reviewed above.

1.  **Configure (Optional):** Review settings within `src/main.py`, `src/reddit_scraper.py`, and `src/analyzer.py` (e.g., `COMMENT_LIMIT_PER_SUB`, `SAVE_PROCESSED_AS_CSV`, `ASPECT_KEYWORDS`).

2.  **Run:**
    ```bash
    python src/main.py
    ```

    **Workflow:**
    *   Checks NLTK data.
    *   Calls scraper (loads map, scrapes incrementally to raw JSON).
    *   Loads raw JSON.
    *   Preprocesses comments.
    *   Saves processed data (CSV/JSON).
    *   Loads processed data.
    *   Applies sentiment/aspect analysis.
    *   Calculates summaries/trends.
    *   Finds top reviews.
    *   Saves analysis results (JSON).
    *   Generates and saves visualizations (PNGs).

3.  **Check Outputs:** Find generated files in the `output/` directory.

## Output Files Description

*   **`data/reference/nirf_eng_top100_names_2024.json`**: List of college names from NIRF.
*   **`data/reference/college_subreddit_map_auto_generated.json`**: Auto-generated (and reviewed) college-to-subreddit mapping.
*   **`data/raw_scraped/college_comments_raw.json`**: Raw scraped comments, updated incrementally.
*   **`data/processed/reddit_comments_processed.csv` (or `.json`)**: Cleaned/preprocessed comments.
*   **`output/analysis_results/top_reviews_per_college.json`**: Summary of top +/- reviews.
*   **`output/visualizations/`**: Charts and word cloud images.

## Important Notes & Limitations

*   **Structure:** Most Python code now resides in the `src/` directory. Run scripts using `python src/script_name.py`. Imports within `src/` are relative (e.g., `from .module import ...`).
*   **Manual Map Review:** Still highly recommended for the auto-generated subreddit map.
*   **API Limits & Time:** Scraping takes time; use credentials.
*   **Data Relevance & Analysis Accuracy:** Results depend on subreddit relevance, VADER, and aspect keywords.
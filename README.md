# Sentient-Analysis-of-Indian-Colleges

This project is designed to scrape, analyze, and visualize sentiment expressed in online reviews of Indian colleges, specifically focusing on data from Reddit. It aims to provide insights into student opinions about various aspects of Indian higher education institutions based on publicly available discussions and comments.

**Current Capabilities:**

*   **Web Scraping (Reddit):**  Scrapes comments from Reddit subreddits potentially related to Indian colleges using the Python Reddit API Wrapper (PRAW).
*   **NIRF Ranking Integration:**  Includes a scraper to fetch college names from the NIRF 2024 Engineering Rankings as a starting point for identifying target colleges.
*   **Automated Subreddit Mapping (Experimental):** Attempts to automatically find relevant subreddits for colleges based on their names (requires manual review for accuracy).
*   **Data Preprocessing:** Cleans and preprocesses scraped text data (removes URLs, special characters, stopwords, performs tokenization and lemmatization).
*   **Sentiment Analysis (VADER):**  Applies VADER (Valence Aware Dictionary and sEntiment Reasoner) for sentiment scoring of reviews.
*   **Aspect-Based Sentiment Analysis:** Implements a keyword-based approach to analyze sentiment towards specific aspects like academics, placements, infrastructure, and campus life.
*   **Analysis & Summarization:**  Calculates overall sentiment scores per college, aspect-specific sentiment summaries, sentiment trends over time, and identifies top positive/negative reviews.
*   **Data Visualization:** Generates bar charts for overall sentiment, heatmaps for aspect sentiment, line graphs for sentiment trends, and word clouds for positive and negative reviews.
*   **Incremental Scraping & Saving:** The scraper is designed to save data incrementally during long runs to manage memory usage and allow for resuming interrupted scrapes.

**Project Status:** Scraping, Preprocessing, Sentiment Analysis, and Visualization pipelines are implemented and functional. Further improvements and expansions are planned (see "Future Prospects").

## Project Structure

```bash
Sentient-Analysis-of-Indian-Colleges/
├── src/
│	├── reddit_scraper.py    # Reddit scraper module
│   ├── cleaner.py        	 # (Code provided previously)
│   ├── analyzer.py       	 # (Code provided previously)
│   ├── summarizer.py     	 # (Code provided previously)
│   ├── plotter.py        	 # (Code provided previously)
│	├── main.py             # <<< Consolidated Main Script >>>
│	└── scrape_nirf.py      # (Code provided previously)
├── output/                  # Generated results & visualizations
│   ├── analysis_results/
│   │   └── .gitkeep
│   └── visualizations/
│       └── .gitkeep
├── data/                    # Intermediate data storage
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

Follow these steps to set up the project environment.

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/WalkingDevFlag/Sentient-Analysis-of-Indian-Colleges
    cd Sentient-Analysis-of-Indian-Colleges
    ```

1.  **Create a Virtual Environment (Recommended):**
    It's best practice to use a virtual environment to isolate project dependencies.
    ```bash
    # On Windows:
    python -m venv venv
    .\venv\Scripts\activate

    # On macOS/Linux:
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Install Dependencies:**
    Install all required Python packages listed in `requirements.txt` using pip.
    ```bash
    pip install -r requirements.txt
    ```
    This command reads the `requirements.txt` file and installs all the specified libraries into your virtual environment.

3.  **Reddit API Credentials (Highly Recommended):**
    To scrape Reddit data reliably, you need to create a Reddit "script" application and obtain API credentials.
    *   Go to the Reddit Apps page: [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) (log in to your Reddit account).
    *   Click on "are you a developer? create an app...".
    *   Fill in the app details:
        *   **Name:** Choose a descriptive name (e.g., `IndianCollegeReviewScraper`).
        *   **Type:** Select "script".
        *   **Description:** Optional description.
        *   **About URL:** Leave blank.
        *   **Redirect URI:** Enter `http://localhost:8080` (this is a placeholder URL and not actually used in script apps).
    *   Click "create app".
    *   Find your newly created app in the list. Under the app name, you'll see "personal use script" - this is your **client ID**. Copy this value.
    *   Next to "secret", click "edit" and then "copy" to get your **client secret**.
    *   Also, define a **user agent string**. This should be a unique identifier for your script, following Reddit's API guidelines (e.g., `IndianCollegeSentimentScraper/0.1 by u/YourRedditUsername`). Replace `u/YourRedditUsername` with your actual Reddit username.
    *   Create a `.env` file in the root directory of your project (`indian-college-reddit/`). Add your credentials to this file:
        ```dotenv
        # .env
        REDDIT_CLIENT_ID=your_client_id_here       # Replace with your client ID
        REDDIT_CLIENT_SECRET=your_client_secret_here # Replace with your client secret
        REDDIT_USER_AGENT=YourUniqueUserAgentString  # Replace with your user agent string
        ```
    *   **Important:** Ensure that `.env` is listed in your `.gitignore` file to prevent accidentally committing your credentials to version control.

4.  **Download NLTK Data (if needed):**
    The project uses NLTK for text processing and sentiment analysis. The scripts are designed to automatically download the necessary NLTK data packages if they are missing. However, if you encounter issues or want to pre-download them, you can run the following commands in a Python interpreter (with your virtual environment activated):
    ```python
    import nltk
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('vader_lexicon')
    nltk.download('wordnet')
    nltk.download('omw-1.4')
    ```

## Running the Project

The project workflow is divided into distinct steps. Run them in order from the project root directory (`indian-college-reddit/`).

### Step 1: Generate College List & Subreddit Map (using `scrape_nirf.py`)

This step scrapes the NIRF Engineering Rankings website to get a list of top colleges and then attempts to automatically find corresponding subreddits for these colleges.

1.  **Run the Script:**
    ```bash
    python src/scrape_nirf.py
    ```

2.  **Outputs:**
    *   `data/reference/nirf_eng_top100_names_2024.json`: A JSON file containing a list of college names scraped from the NIRF ranking page.
    *   `data/reference/college_subreddit_map_auto_generated.json`: A JSON file containing an *automatically generated* mapping of college names to potential subreddit names. **This file requires manual review and editing.**

### Step 2: Review and Edit the Subreddit Mapping File (Manual Step - Highly Recommended)

The automatic subreddit mapping is not always perfect. It's crucial to manually review and correct the generated `college_subreddit_map_auto_generated.json` file to ensure data quality.

1.  **Open the Mapping File:** Open `data/reference/college_subreddit_map_auto_generated.json` in a text editor or JSON editor.

2.  **Review and Correct:**
    *   Go through each entry in the JSON list.
    *   For each `college_name`, check if the `subreddit` listed is actually the correct and relevant subreddit for that college on Reddit.
    *   **Correct Incorrect Subreddits:** If a subreddit is wrong, search Reddit manually for the correct subreddit name and update the `subreddit` value in the JSON file.
    *   **Remove Irrelevant Entries:** If a college does not have a relevant or active subreddit, you can remove the entire dictionary entry for that college from the JSON list.
    *   **Rename (Optional):** After reviewing and editing, you can rename `college_subreddit_map_auto_generated.json` to `college_subreddit_map.json` (or keep the auto-generated name and ensure `main.py` is configured to use it).

    **Why Manual Review is Important:**
    The automated mapping is based on heuristics and may not always find the best or most relevant subreddit. Manual review ensures that the scraper targets the intended communities, improving the quality of the scraped data.

### Step 3: Run the Full Data Pipeline (using `src/main.py`)

This script orchestrates the entire data pipeline, including scraping Reddit comments, preprocessing the text, performing sentiment analysis, and generating visualizations and analysis results.

1.  **Check Configuration (Optional):**
    Before running the full pipeline, you can review and adjust configuration settings in `src/main.py`, `src/reddit_scraper.py`, and `src/sentiment/analyzer.py` if needed. Key parameters include:
    *   `COMMENT_LIMIT_PER_SUB` in `src/reddit_scraper.py`:  Maximum number of comments to scrape per subreddit.
    *   `SAVE_PROCESSED_AS_CSV` in `src/main.py`:  Whether to save processed data as CSV or JSON.
    *   `ASPECT_KEYWORDS` in `src/sentiment/analyzer.py`:  Keywords used for aspect-based sentiment analysis (customize these for better relevance).
    *   `TOP_N_REVIEWS`, `TREND_FREQUENCY` in `src/main.py`: Parameters for analysis and summarization.

2.  **Run the Script:**
    ```bash
    python src/main.py
    ```

    The `main.py` script will execute the following steps:
    *   **NLTK Data Check:** Ensures required NLTK data packages are available.
    *   **Reddit Scraping:** Uses the `reddit_scraper.py` module to scrape comments from Reddit based on the reviewed `college_subreddit_map.json` file. Raw data is saved incrementally to `data/raw_scraped/college_comments_raw.json`.
    *   **Preprocessing:** Loads the raw scraped data and preprocesses the text of each comment using functions from `src/preprocessing/cleaner.py`.
    *   **Save Processed Data:** Saves the cleaned and preprocessed comment data to `data/processed/reddit_comments_processed.csv` (or `.json`).
    *   **Sentiment Analysis:** Loads the processed data and applies VADER sentiment analysis and aspect-based sentiment analysis using functions from `src/sentiment/analyzer.py`.
    *   **Analysis and Summarization:** Calculates overall sentiment scores, aspect sentiment summaries, sentiment trends, and identifies top positive/negative reviews using functions from `src/analysis/summarizer.py`. Analysis results (like top reviews) are saved to JSON files in `output/analysis_results/`.
    *   **Visualization:** Generates various visualizations (bar charts, heatmaps, line graphs, word clouds) using functions from `src/visualization/plotter.py` and saves them as PNG image files in `output/visualizations/`.

3.  **Monitor Output:**
    The script will print progress messages and use progress bars (TQDM) to indicate the progress of each stage. Check the console output for any warnings or errors during execution.

4.  **Check Output Files:**
    After the script completes, check the `output/` directory for the generated analysis results (JSON files) and visualizations (PNG image files).

## Output Files Description

*   **`data/reference/nirf_eng_top100_names_2024.json`**: A raw list of college names scraped from the NIRF website.
*   **`data/reference/college_subreddit_map_auto_generated.json`**: A JSON file containing the auto-generated mapping of college names to subreddit names (requires manual review and editing to ensure accuracy).
*   **`data/raw_scraped/college_comments_raw.json`**: A JSON file containing the raw scraped comments from Reddit, organized by college and subreddit. This file is updated incrementally during scraping.
*   **`data/processed/reddit_comments_processed.csv` (or `reddit_comments_processed.json`)**: This file contains the cleaned and preprocessed Reddit comment data, ready for sentiment analysis. The format (CSV or JSON) depends on the `SAVE_PROCESSED_AS_CSV` setting in `main.py`.
*   **`output/analysis_results/top_reviews_per_college.json`**: A JSON file in the `output/analysis_results/` directory that contains a summary of the top N positive and negative reviews identified for each college, including the review text, sentiment score, and Reddit permalink.
*   **`output/visualizations/`**: This directory in `output/visualizations/` will contain various PNG image files representing the visualizations generated by the project:
    *   `overall_sentiment_by_college.png`: A bar chart visualizing the average overall sentiment score for each college.
    *   `aspect_sentiment_heatmap.png`: A heatmap visualizing the average sentiment score for each defined aspect (academics, placements, etc.) across different colleges.
    *   `sentiment_trends_over_time.png`: A line graph showing the sentiment trends over time, along with comment volume.
    *   `word_clouds/`: A subdirectory containing word cloud images for each college, separated into positive and negative reviews (e.g., `output/visualizations/word_clouds/iit_bombay_positive_wc.png`, `output/visualizations/word_clouds/iit_bombay_negative_wc.png`).

## Future Prospects and Potential Enhancements

This project provides a foundation for analyzing sentiment in Indian college reviews. Here are some potential future directions and enhancements:

*   **Expand Data Sources:**
    *   **Quora Scraper:** Develop a dedicated scraper for Quora to collect college reviews, question answers, and ratings from Quora. Quora often has detailed, experience-based reviews. Consider using Selenium for dynamic content loading and login if needed.
    *   **Other Review Platforms:** Explore and add scrapers for other platforms that host Indian college reviews, such as:
        *   **Shiksha.com, Careers360.com, CollegeDunia.com:** These are popular Indian college review websites. HTML scraping with BeautifulSoup or Scrapy could be used.
        *   **Google Reviews:**  Scrape reviews from Google Maps or Google Search results for colleges. APIs or web scraping techniques might be applicable.
        *   **Social Media (beyond Reddit):** Explore Twitter (X), Facebook, or other social media platforms for relevant discussions (consider API limitations and data privacy).
    *   **YouTube:**  Scrape comments from YouTube videos related to college reviews or campus tours.

*   **Improve Sentiment Analysis:**
    *   **Fine-tune VADER:**  Customize the VADER lexicon with domain-specific terms or phrases relevant to Indian colleges and education.
    *   **Machine Learning Models:** Train custom machine learning sentiment classification models (e.g., using Naive Bayes, SVM, Logistic Regression, or deep learning models like LSTMs or Transformers). This would require creating a labeled dataset of Indian college reviews for training and evaluation. Consider techniques like transfer learning or fine-tuning pre-trained models for sentiment analysis.
    *   **Context-Aware Sentiment:** Implement techniques to better handle context, sarcasm, and negation in reviews.

*   **Enhance Aspect-Based Analysis:**
    *   **Expand Aspect Categories:** Add more relevant aspects beyond the current set (e.g., "faculty quality", "alumni network", "location", "administration", "value for money").
    *   **Refine Keyword Lists:** Improve the accuracy of aspect detection by expanding and refining the keyword lists for each aspect. Consider using techniques like term frequency-inverse document frequency (TF-IDF) or topic modeling to automatically identify relevant keywords.
    *   **Advanced Aspect Extraction:** Explore more sophisticated aspect extraction methods beyond keyword matching, such as using dependency parsing or machine learning-based aspect term extraction techniques.

*   **Advanced Analysis & Insights:**
    *   **Comparative Analysis:** Directly compare sentiment scores and aspect ratings across different colleges to identify relative strengths and weaknesses.
    *   **Deeper Trend Analysis:** Investigate sentiment trends for specific aspects over time.
    *   **Topic Modeling:** Apply topic modeling techniques (like LDA or NMF) to discover hidden topics and themes discussed in the reviews beyond predefined aspects.
    *   **Demographic Analysis:** If author demographics (e.g., region, program) can be inferred or scraped, analyze sentiment variations across different demographic groups.

*   **Visualization Improvements:**
    *   **Interactive Visualizations:** Create interactive charts and dashboards (e.g., using Plotly, Dash, or Tableau) to allow users to explore the data and insights dynamically.
    *   **Geospatial Visualizations:** If location data is available, create maps to visualize sentiment geographically.

*   **User Interface & Deployment:**
    *   Develop a user-friendly web interface (e.g., using Flask, Django, or Streamlit) to make the analysis results and visualizations accessible to a wider audience.
    *   Deploy the project as a web application or API for easier access and integration.

By pursuing these future directions, the project can evolve into a more comprehensive and insightful tool for understanding and comparing student sentiment towards Indian colleges. Remember that ethical scraping practices, respect for website terms of service, and responsible use of data are crucial throughout the project's development.
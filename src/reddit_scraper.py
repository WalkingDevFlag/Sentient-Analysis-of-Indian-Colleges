# scrapers/reddit_scraper.py

import praw
import re
import json
import time
import datetime
import os
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv
import random

# --- Configuration ---
load_dotenv()

CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
USER_AGENT = os.getenv("REDDIT_USER_AGENT")

# --- Constants ---

# <<< UPDATED: Path points to the auto-generated mapping file >>>
# NOTE: It's still strongly recommended to REVIEW and potentially EDIT this file first!
COLLEGE_MAP_FILE = Path("data") / "reference" / "college_subreddit_map_auto_generated.json"

COMMENT_LIMIT_PER_SUB = 1000
RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw_scraped"
OUTPUT_FILENAME = RAW_DATA_DIR / "college_comments_raw.json"
SAVE_INCREMENTALLY = True
SKIP_ALREADY_SCRAPED = True # Useful if run gets interrupted

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
Path("data/reference").mkdir(parents=True, exist_ok=True)

def setup_praw():
    """Initializes and returns a PRAW Reddit instance."""
    # ... (setup_praw function remains the same) ...
    print("Initializing PRAW...")
    try:
        if not CLIENT_ID or not USER_AGENT: raise ValueError("...")
        reddit = praw.Reddit(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, user_agent=USER_AGENT)
        _ = reddit.subreddits.search("test", limit=1); print("PRAW initialized.")
        return reddit
    except Exception as e: print(f"PRAW Init Error: {e}"); return None


def load_existing_data(filepath):
    """Loads existing data from the JSON file if it exists."""
    # ... (load_existing_data function remains the same) ...
    if filepath.exists():
        try:
            with open(filepath, 'r', encoding='utf-8') as f: return json.load(f)
        except Exception as e: print(f"Warning: Could not read {filepath}: {e}. Starting fresh."); return {}
    return {}

def save_data(filepath, data):
    """Saves the entire data dictionary to the JSON file."""
    # ... (save_data function remains the same) ...
    try:
        with open(filepath, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e: print(f"Error saving data to {filepath}: {e}")


def scrape_subreddit_comments(reddit, subreddit_name, limit):
    """Scrapes comments from a specific subreddit up to the specified limit."""
    # ... (scrape_subreddit_comments function remains the same) ...
    comments_data = []
    try:
        subreddit = reddit.subreddit(subreddit_name)
        comment_stream = subreddit.comments(limit=limit)
        pbar = tqdm(total=limit, desc=f"r/{subreddit_name}", unit="comment", leave=False)
        try:
            for comment in comment_stream:
                 try:
                     comment_body = comment.body
                     if comment_body is None or comment_body in ('[deleted]', '[removed]'):
                         pbar.update(1); continue
                     comment_data = {
                         'id': comment.id, 'text': comment_body, 'score': comment.score,
                         'created_utc': comment.created_utc,
                         'created_readable': datetime.datetime.utcfromtimestamp(comment.created_utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
                         'permalink': f"https://www.reddit.com{comment.permalink}",
                         'subreddit': subreddit_name,
                     }
                     comments_data.append(comment_data)
                     pbar.update(1)
                 except Exception: pbar.update(1); continue
        finally: pbar.close()
        return comments_data
    except praw.exceptions.PRAWException as pe:
         print(f"\nPRAW Error accessing r/{subreddit_name}: {pe} (Skipping)")
         if 'pbar' in locals() and pbar: pbar.close(); return []
    except Exception as e:
        print(f"\nUnexpected Error scraping r/{subreddit_name}: {e} (Skipping)")
        if 'pbar' in locals() and pbar: pbar.close(); return []
    return []


def load_target_subreddits(map_filepath):
    """Loads the college-to-subreddit mapping from the JSON file."""
    # ... (load_target_subreddits function remains the same) ...
    if not map_filepath.exists():
        print(f"Error: College map file not found at {map_filepath}")
        print("Please run scrape_nirf.py first to generate it.")
        return None
    try:
        with open(map_filepath, 'r', encoding='utf-8') as f: targets = json.load(f)
        if not isinstance(targets, list): print(f"Error: {map_filepath} invalid format."); return None
        valid_targets = []
        for item in targets:
            # Filter out entries where subreddit might be None if scrape_nirf included them
            if isinstance(item, dict) and 'college_name' in item and item.get('subreddit'): # Check if subreddit is not None or empty
                valid_targets.append(item)
            else:
                print(f"Warning: Skipping invalid/incomplete entry in {map_filepath}: {item}")
        if not valid_targets: print(f"Error: No valid targets found in {map_filepath}."); return None
        print(f"Loaded {len(valid_targets)} targets from {map_filepath}")
        return valid_targets
    except Exception as e: print(f"Error loading/parsing {map_filepath}: {e}"); return None


def run_scraper():
    """Orchestrates Reddit scraping using the loaded college map file."""
    reddit = setup_praw()
    if not reddit: print("Exiting scraper: PRAW failed."); return None

    # Load targets from the mapping file (now defaults to auto-generated one)
    target_list = load_target_subreddits(COLLEGE_MAP_FILE)
    if not target_list: print("Exiting scraper: Failed to load targets."); return None

    all_comments_data = {}
    if SAVE_INCREMENTALLY or SKIP_ALREADY_SCRAPED:
         print(f"Attempting to load existing data from {OUTPUT_FILENAME}...")
         all_comments_data = load_existing_data(OUTPUT_FILENAME)
         print(f"Loaded {len(all_comments_data)} existing sources.")

    print(f"\n--- Starting Comment Scraping from {len(target_list)} Mapped Subreddits (Limit: {COMMENT_LIMIT_PER_SUB}/sub) ---")

    processed_count = 0
    for sub_info in tqdm(target_list, desc="Subreddits", unit="sub"):
        subreddit_name = sub_info.get('subreddit')
        college_name = sub_info.get('college_name', 'Unknown College')
        if not subreddit_name: continue # Should be filtered by load_target_subreddits, but double-check

        data_key = f"{college_name} (r/{subreddit_name})"

        if SKIP_ALREADY_SCRAPED and data_key in all_comments_data:
            print(f"\nSkipping '{data_key}', already found.")
            processed_count +=1; continue

        print(f"\nScraping -> '{data_key}'")
        comments = scrape_subreddit_comments(reddit, subreddit_name, COMMENT_LIMIT_PER_SUB)

        if comments:
            all_comments_data[data_key] = comments
            print(f"-> Retrieved {len(comments)} comments for '{data_key}'.")
            if SAVE_INCREMENTALLY: save_data(OUTPUT_FILENAME, all_comments_data)
        else: print(f"-> No comments retrieved for '{data_key}'.")

        processed_count += 1
        time.sleep(random.uniform(1.5, 4.0))

    print("\nPerforming final check/save of all data...")
    save_data(OUTPUT_FILENAME, all_comments_data)
    print("Final save complete.")

    if all_comments_data: return OUTPUT_FILENAME
    else: return None

# --- Main Execution Guard ---
if __name__ == "__main__":
    # ... (Main guard remains the same) ...
    print("--- Running Reddit Scraper Module Test (Auto-Mapped Subs, Incremental Save) ---")
    start_time = time.time(); saved_file_path = run_scraper(); end_time = time.time()
    if saved_file_path: print(f"\nScraper test finished. Raw data: {saved_file_path}")
    else: print("\nScraper test failed or no data saved.")
    print(f"Duration: {(end_time - start_time):.2f} sec"); print("--- Test Finished ---")
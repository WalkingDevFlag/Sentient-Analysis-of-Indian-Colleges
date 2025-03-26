# scrape_nirf.py (Revision 6 - Clean Name Before Subreddit Search)

import requests
from bs4 import BeautifulSoup
import json
import re
from pathlib import Path
import time
import praw
from dotenv import load_dotenv
import os
from tqdm import tqdm
import nltk # <--- Import NLTK

# --- Download NLTK Stopwords ---
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    print("[NLTK] Downloading 'stopwords' resource...")
    nltk.download('stopwords', quiet=True)
    print("[NLTK] Downloaded 'stopwords'.")

from nltk.corpus import stopwords # <--- Import stopwords corpus

# --- Configuration ---
load_dotenv()

# PRAW Credentials
CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
USER_AGENT = os.getenv("REDDIT_USER_AGENT")

# NIRF Scraper Config
NIRF_URL = 'https://www.nirfindia.org/Rankings/2024/EngineeringRanking.html'
MAX_RANK = 100

# Output Config
OUTPUT_DIR = Path("data") / "reference"
NIRF_NAMES_FILE = OUTPUT_DIR / "nirf_eng_top100_names_2024.json"
SUBREDDIT_MAP_FILE = OUTPUT_DIR / "college_subreddit_map_auto_generated.json"

# Subreddit Search Config
MIN_SUBSCRIBERS = 50

# Define "Jitter Words" to remove before generating search terms
ENGLISH_STOPWORDS = set(stopwords.words('english'))
ACADEMIC_JITTER_WORDS = set([
    'institute', 'technology', 'of', 'and', 'for', 'the',
    'university', 'college', 'engineering', 'indian', 'national',
    'management', 'science', 'sciences', 'research', 'studies'
    # Add more common but non-distinguishing words if needed
])
ALL_JITTER_WORDS = ENGLISH_STOPWORDS.union(ACADEMIC_JITTER_WORDS)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --- PRAW Setup (remains the same) ---
def setup_praw():
    print("Initializing PRAW for subreddit search...")
    # ... (same as previous version) ...
    try:
        if not CLIENT_ID or not USER_AGENT: raise ValueError("...")
        reddit = praw.Reddit(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, user_agent=USER_AGENT)
        _ = reddit.subreddits.search("test", limit=1); print("PRAW initialized.")
        return reddit
    except Exception as e: print(f"PRAW Init Error: {e}"); return None


# --- NIRF Scraping (remains the same) ---
def scrape_nirf_rankings(url, max_rank):
    print(f"Scraping NIRF rankings from: {url}")
    # ... (same scraping logic as Revision 4 - Hardcoded Deletion) ...
    college_names = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 ...'}
        response = requests.get(url, headers=headers, timeout=20); response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        ranking_table = soup.find('table', {'id': lambda x: x and 'tblRanking' in x}) or soup.find('table')
        if not ranking_table: return None
        table_body = ranking_table.find('tbody');
        if not table_body: return None
        rows = table_body.find_all('tr'); print(f"Found {len(rows)} rows...")
        rank_count = 0
        for row in rows:
            if rank_count >= max_rank: break
            cells = row.find_all('td');
            if len(cells) < 2: continue
            first_cell_text = cells[0].get_text(strip=True)
            if not first_cell_text or not first_cell_text.startswith('IR-'): continue
            try:
                full_cell_text = cells[1].get_text(strip=True)
                separator_pattern = r'More\s*Details\s*Close\s*\|\|'
                match = re.search(separator_pattern, full_cell_text, flags=re.IGNORECASE)
                college_name = full_cell_text[:match.start()] if match else full_cell_text
                college_name = re.sub(r'\s+', ' ', college_name).strip()
                if college_name: college_names.append(college_name); rank_count += 1
            except Exception: continue
        if not college_names: print("Error: No names extracted."); return None
        print(f"Extracted {len(college_names)} college names.")
        return college_names
    except Exception as e: print(f"Error during NIRF scraping: {e}"); return None

# --- Subreddit Search Logic (Updated Term Generation) ---

def generate_search_terms(college_name):
    """
    Generates likely subreddit names from a full college name
    AFTER removing common jitter words.
    """
    terms = set()
    name_lower = college_name.lower()

    # 1. Clean the name: Tokenize and remove jitter words
    words = re.findall(r'\b\w+\b', name_lower)
    core_words = [word for word in words if word not in ALL_JITTER_WORDS]

    if not core_words: # Handle cases where cleaning removes everything
        # Fallback: Use original words if core words are empty
        core_words = [word for word in words if word not in ENGLISH_STOPWORDS] # Less aggressive fallback
        if not core_words: return [] # Give up if still empty

    # print(f"DEBUG - Core words for '{college_name}': {core_words}") # Debug

    # 2. Generate terms based on CORE words
    # a) Concatenated core words
    concatenated_core = "".join(core_words)
    if len(concatenated_core) > 2: terms.add(concatenated_core)

    # b) Acronym of core words
    if len(core_words) > 1:
        acronym_core = "".join(w[0] for w in core_words)
        if len(acronym_core) > 1: terms.add(acronym_core)

    # c) First core word (if significant)
    if core_words and len(core_words[0]) > 2 :
        terms.add(core_words[0])

    # d) Acronym + Location (Identify location from ORIGINAL name, use core acronym)
    location_keywords = ['delhi', 'bombay', 'madras', 'kanpur', 'kharagpur', 'roorkee', 'guwahati', 'hyderabad', 'varanasi', 'indore', 'dhanbad', 'trichy', 'surathkal', 'rourkela', 'warangal', 'calicut', 'durgapur', 'kurukshetra', 'pilani', 'bangalore', 'allahabad', 'vellore', 'mumbai', 'pune', 'bhu', 'jnu', 'amu', 'jmi']
    original_words = re.findall(r'\b\w+\b', name_lower) # Get original words again for location
    location = ""
    for w in original_words:
        if w in location_keywords:
            location = w
            break

    if core_words and location:
         # Try acronym of core + location
         core_acronym = "".join(w[0] for w in core_words if w != location) # Exclude location if it was a core word
         if core_acronym and len(core_acronym) > 0:
             terms.add(core_acronym + location)

         # Special prefixes + location
         common_prefixes = {'iit', 'nit', 'iiit', 'bits'}
         prefix_match = core_acronym if core_acronym in common_prefixes else None
         if not prefix_match and len(core_words)>0 and core_words[0] in common_prefixes: # Check if first core word is prefix
             prefix_match = core_words[0]

         if prefix_match and location:
              terms.add(prefix_match + location)


    # 3. Fallback: Use original name (cleaned of punctuation/spaces)
    original_clean = re.sub(r'[^\w]', '', name_lower)
    if len(original_clean) > 2: terms.add(original_clean)


    # Final filter
    filtered_terms = {term for term in terms if len(term) > 2}
    # print(f"DEBUG - Search terms for '{college_name}': {filtered_terms}") # Debug
    return list(filtered_terms)


def find_best_subreddit(reddit, college_name, search_terms):
    """Searches Reddit for subreddits and selects the best candidate."""
    # ... (find_best_subreddit function remains largely the same as Revision 5) ...
    # Minor tweak: Maybe prioritize exact matches even more heavily now
    best_match = None
    highest_score = -1
    searched_subs = set()

    for term in search_terms:
        if not term: continue
        try:
            results = reddit.subreddits.search(term, limit=5)
            found_results = False
            for sub in results:
                found_results = True
                sub_name_lower = sub.display_name.lower()
                if sub_name_lower in searched_subs: continue
                searched_subs.add(sub_name_lower)
                subscribers = sub.subscribers or 0
                if subscribers < MIN_SUBSCRIBERS: continue

                score = 0
                # Higher bonus for exact match now search terms are cleaner
                if sub_name_lower == term:
                    score += 2000 # Increased bonus
                elif term in sub_name_lower:
                    score += 150  # Increased bonus
                # Add subscriber count (log/sqrt scaling)
                score += int(subscribers**0.5)

                if score > highest_score:
                    highest_score = score
                    best_match = sub.display_name
            if found_results: time.sleep(0.5)
        except Exception as e: print(f"  Error searching '{term}': {e}"); time.sleep(1)
    return best_match


# --- File Saving (remains the same) ---
def save_list_to_json(data_list, filepath):
    # ... (same as before) ...
    filepath = Path(filepath);
    try:
        with open(filepath, 'w', encoding='utf-8') as f: json.dump(data_list, f, indent=2, ensure_ascii=False)
        print(f"Saved list to {filepath}")
    except Exception as e: print(f"Error saving list: {e}")


# --- Main Execution (remains the same) ---
if __name__ == "__main__":
    print("--- Starting NIRF Scraper & Auto Subreddit Mapper (v6 - Pre-cleaned Names) ---")
    main_start_time = time.time()
    nirf_names = scrape_nirf_rankings(NIRF_URL, MAX_RANK)

    if not nirf_names:
        print("NIRF scraping failed.")
    else:
        save_list_to_json(nirf_names, NIRF_NAMES_FILE)
        reddit = setup_praw()
        if not reddit:
            print("PRAW setup failed. Cannot search subreddits.")
        else:
            print("\n--- Searching for Subreddits ---")
            college_subreddit_map = []
            not_found_count = 0
            for college_name in tqdm(nirf_names, desc="Finding Subreddits", unit="college"):
                search_terms = generate_search_terms(college_name) # Uses updated function
                best_sub = find_best_subreddit(reddit, college_name, search_terms)
                if best_sub:
                    college_subreddit_map.append({"college_name": college_name, "subreddit": best_sub})
                else:
                    print(f"Warning: No suitable subreddit found for '{college_name}'.")
                    not_found_count += 1
                time.sleep(1.0) # Delay

            print(f"\n--- Saving Auto-Generated Subreddit Map ---")
            print(f"Found potential subreddits for {len(college_subreddit_map)} / {len(nirf_names)} colleges.")
            if not_found_count > 0: print(f"Could not find match for {not_found_count} colleges.")
            print(f"PLEASE REVIEW AND EDIT '{SUBREDDIT_MAP_FILE}' MANUALLY.")
            save_list_to_json(college_subreddit_map, SUBREDDIT_MAP_FILE)

    main_end_time = time.time()
    print(f"\n--- Script finished in {(main_end_time - main_start_time):.2f} seconds ---")
import re
import string
import nltk
# Ensure NLTK data is available (download handled in main.py)
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer, PorterStemmer

# --- Setup ---
try:
    stop_words = set(stopwords.words('english'))
    # Optional: Add Reddit/college specific stopwords
    custom_stops = {'http', 'https', 'www', 'com', 'reddit', 'subreddit', 'post', 'comment',
                    'deleted', 'removed', 'mod', 'automod', 'automoderator', 'wiki', 'faq',
                    'college', 'university', 'campus', 'student', 'students', 'iit', 'nit', 'bits',
                    'amp', 'nbsp', 'quot', 'gt', 'lt'} # HTML entities and common terms
    stop_words.update(custom_stops)
except LookupError:
    print("Warning: NLTK stopwords not found during cleaner module load.")
    stop_words = set()

lemmatizer = WordNetLemmatizer()
stemmer = PorterStemmer()

# --- Functions ---

def clean_text(text):
    """
    Cleans Reddit text: lowercase, remove URLs, mentions, subreddit links,
    markdown, special chars (keeps basic punctuation), extra whitespace.
    """
    if not isinstance(text, str):
        return ""

    text = text.lower()
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    # Remove user mentions (/u/username) and subreddit links (/r/subreddit)
    text = re.sub(r'/?u/\w+|/?r/\w+', '', text)
    # Remove common markdown (bold, italics, links without URLs, quotes)
    text = re.sub(r'[*_`~]', '', text) # Remove *, _, `, ~
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text) # Keep text from links like [text](url)
    text = re.sub(r'^>.*$', '', text, flags=re.MULTILINE) # Remove blockquote lines
    # Remove HTML entities like &,  
    text = re.sub(r'&[a-z]+;', '', text)
    # Remove remaining special characters but keep basic punctuation .,?! and apostrophes
    text = re.sub(r'[^a-z\s.,?!\']', '', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text

def preprocess_text(text, use_lemmatization=True, use_stemming=False):
    """
    Cleans, tokenizes, removes stopwords, and optionally lemmatizes or stems text.
    Returns a list of processed tokens.
    """
    cleaned_text = clean_text(text)
    if not cleaned_text:
        return []

    # Tokenize
    try:
        tokens = word_tokenize(cleaned_text)
    except LookupError:
        print("Error: NLTK 'punkt' tokenizer not found. Preprocessing failed.")
        return []

    # Remove stopwords, short tokens, and punctuation tokens
    processed_tokens = [
        word for word in tokens
        if word not in stop_words and len(word) > 1 and word not in string.punctuation
    ]

    # Apply Lemmatization OR Stemming
    if use_lemmatization:
        try:
            # Lemmatize requires WordNet data
            processed_tokens = [lemmatizer.lemmatize(word) for word in processed_tokens]
        except LookupError:
            print("Error: NLTK 'wordnet'/'omw-1.4' not found. Lemmatization skipped.")
    elif use_stemming:
        processed_tokens = [stemmer.stem(word) for word in processed_tokens]

    return processed_tokens

# --- Example Usage (for testing) ---
if __name__ == "__main__":
    sample_text = """
    Check out this *awesome* review of IIT Bombay!! https://example.com/iitb_review.
    Life at `/r/IITBombay` is amazing (really!), though the academics are tough 123. Grades are important.
    `/u/someuser` said it's great. What do you think? Cost is high!!! Better than IIT Delhi?
    &nbsp; Running, Jumps, Studies. >!Spoiler alert!<
    """
    print("--- Running Preprocessing Cleaner Module Test ---")
    print(f"\nOriginal Text:\n{sample_text}")

    cleaned = clean_text(sample_text)
    print(f"\nCleaned Text:\n{cleaned}")

    processed_lemma = preprocess_text(sample_text, use_lemmatization=True, use_stemming=False)
    print(f"\nProcessed Tokens (Lemmatized):\n{processed_lemma}")

    processed_stem = preprocess_text(sample_text, use_lemmatization=False, use_stemming=True)
    print(f"\nProcessed Tokens (Stemmed):\n{processed_stem}")

    print("\n--- Preprocessing Cleaner Module Test Finished ---")
# sentiment/analyzer.py

import nltk
import re
import pandas as pd # <--- Missing import added here
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize import sent_tokenize
from tqdm import tqdm

# --- Download NLTK Data (VADER, Punkt) ---
def download_nltk_resources():
    """Checks for and downloads required NLTK resources."""
    resources = {
        'sentiment/vader_lexicon.zip': 'vader_lexicon',
        'tokenizers/punkt': 'punkt'
    }
    all_found = True
    missing_resources = []
    for path_key, download_key in resources.items():
        try:
            nltk.data.find(path_key)
        except LookupError:
            all_found = False
            missing_resources.append(download_key)

    if not all_found:
        print(f"[NLTK] Missing resources: {', '.join(missing_resources)}")
        for key in missing_resources:
            print(f"[NLTK] Downloading: {key}...")
            try:
                nltk.download(key, quiet=True)
                print(f"[NLTK] Downloaded: {key}")
            except Exception as e:
                 print(f"[NLTK] Error downloading {key}: {e}. Please try manually.")
                 # Consider raising an error if critical resources fail
    # else: # Optional: uncomment for confirmation
        # print("[NLTK] All required resources found.")


download_nltk_resources() # Ensure resources are available on import

# --- Aspect Keywords (Customize as needed) ---
# Keywords should be lowercase
ASPECT_KEYWORDS = {
    'academics': ['academic', 'academics', 'course', 'courses', 'professor', 'professors', 'prof', 'faculty', 'teacher', 'teaching', 'curriculum', 'syllabus', 'study', 'studies', 'research', 'exam', 'exams', 'grade', 'grades', 'gpa', 'lecture', 'lectures', 'learning', 'knowledge', 'department', 'assignment', 'assignments', 'rigor', 'challenging', 'difficult', 'education', 'degree'],
    'placements': ['placement', 'placements', 'job', 'jobs', 'career', 'careers', 'intern', 'internship', 'internships', 'recruit', 'recruiter', 'recruiters', 'recruitment', 'hiring', 'offer', 'offers', 'company', 'companies', 'salary', 'package', 'ctc', 'employ', 'employment', 'opportunity', 'opportunities', 'resume', 'cv', 'alumni network'],
    'infrastructure': ['infrastructure', 'infra', 'building', 'buildings', 'hostel', 'hostels', 'mess', 'food', 'canteen', 'lab', 'labs', 'library', 'wifi', 'internet', 'classroom', 'classrooms', 'facility', 'facilities', 'campus', 'area', 'clean', 'maintenance', 'sports', 'gym', 'equipment', 'room', 'rooms', 'water', 'power', 'transport'],
    'campus_life': ['life', 'campus life', 'culture', 'fest', 'fests', 'event', 'events', 'club', 'clubs', 'activity', 'activities', 'social', 'community', 'student', 'students', 'peer', 'peers', 'friend', 'friends', 'people', 'atmosphere', 'vibe', 'environment', 'fun', 'enjoy', 'experience', 'hostel life', 'party', 'parties', 'ragging', 'senior', 'junior', 'diversity', 'safety', 'security', 'interaction', 'extra curricular'],
    'fees': ['fee', 'fees', 'cost', 'expensive', 'cheap', 'affordable', 'price', 'tuition', 'scholarship', 'loan', 'value', 'money', 'worth', 'finance', 'financial', 'payment']
    # Add more aspects if needed (e.g., Location, Administration)
}

# --- VADER Analyzer ---
# Initialize VADER Analyzer, handle potential errors if lexicon wasn't downloaded
try:
    analyzer = SentimentIntensityAnalyzer()
except LookupError:
    print("CRITICAL ERROR: NLTK VADER lexicon not found.")
    print("Please ensure NLTK data (vader_lexicon) is correctly installed.")
    analyzer = None # Set analyzer to None to indicate failure

def get_vader_sentiment(text):
    """Calculates VADER compound sentiment score."""
    if not analyzer:
        # print("VADER Analyzer not initialized. Cannot calculate sentiment.") # Avoid printing repeatedly
        return 0.0
    if not isinstance(text, str) or not text.strip():
        return 0.0 # Neutral for empty/invalid input
    try:
        # VADER works better on raw-ish text
        scores = analyzer.polarity_scores(text)
        return scores['compound']
    except Exception as e:
        print(f"Error in VADER analysis for text snippet: '{text[:50]}...': {e}")
        return 0.0

def analyze_aspect_sentiment(text):
    """
    Performs simple aspect-based sentiment analysis using keywords and VADER on sentences.
    Returns dict: {aspect_name: avg_sentiment_score_or_None}.
    """
    aspect_sentiments = {aspect: [] for aspect in ASPECT_KEYWORDS}
    final_aspect_scores = {aspect: None for aspect in ASPECT_KEYWORDS} # Initialize with None

    if not analyzer:
        # print("VADER Analyzer not initialized. Cannot perform aspect analysis.") # Avoid repeated prints
        return final_aspect_scores
    if not isinstance(text, str) or not text.strip():
        return final_aspect_scores

    try:
        sentences = sent_tokenize(text)
    except Exception as e:
        print(f"Error tokenizing sentences for text: '{text[:50]}...': {e}")
        return final_aspect_scores

    for sentence in sentences:
        sentence_lower = sentence.lower()
        # Get VADER score for the specific sentence
        sentence_score = get_vader_sentiment(sentence)

        # Check sentence for keywords of each aspect
        for aspect, keywords in ASPECT_KEYWORDS.items():
            # Use word boundaries for more precise matching
            if any(re.search(r'\b' + re.escape(keyword) + r'\b', sentence_lower) for keyword in keywords):
                aspect_sentiments[aspect].append(sentence_score)
                # Allows a sentence to contribute to multiple aspects

    # Calculate average score for each aspect that had relevant sentences
    for aspect, scores in aspect_sentiments.items():
        if scores: # Check if the list is not empty
            try:
                final_aspect_scores[aspect] = sum(scores) / len(scores)
            except ZeroDivisionError: # Should not happen if scores list is checked, but just in case
                final_aspect_scores[aspect] = 0.0

    return final_aspect_scores

# --- Helper function to apply sentiment analysis to a DataFrame ---
def apply_sentiment_analysis_to_df(df, text_col='text'):
    """
    Applies VADER and aspect sentiment analysis to a DataFrame.

    Args:
        df (pd.DataFrame): Input DataFrame with a text column.
        text_col (str): Name of the column containing the review text.

    Returns:
        pd.DataFrame: Original DataFrame with added sentiment columns:
                      'compound_sentiment' and '{aspect}_sentiment' for each aspect.
    """
    if text_col not in df.columns:
        print(f"Error: Text column '{text_col}' not found in DataFrame.")
        return df
    if analyzer is None:
        print("Error: VADER analyzer not available. Cannot apply sentiment.")
        return df

    print("Applying VADER sentiment analysis...")
    tqdm.pandas(desc="VADER Compound Score")
    # Ensure text column is string type before applying VADER
    df[text_col] = df[text_col].astype(str)
    df['compound_sentiment'] = df[text_col].progress_apply(get_vader_sentiment)

    print("Applying aspect-based sentiment analysis...")
    aspect_results = []
    # Ensure text column is string type before iterating for aspect analysis
    for text in tqdm(df[text_col].astype(str), desc="Aspect Analysis", unit="review"):
        aspect_results.append(analyze_aspect_sentiment(text))

    # Convert list of dicts into a DataFrame
    aspect_df = pd.DataFrame(aspect_results, index=df.index)
    # Add suffix to column names
    aspect_df.columns = [f"{col}_sentiment" for col in aspect_df.columns]

    # Join aspect columns to the original DataFrame
    # Use concat to handle potential index mismatches more robustly if any occurred
    df = pd.concat([df, aspect_df], axis=1)

    print("Sentiment analysis applied.")
    return df


# --- Example Usage ---
if __name__ == '__main__':
    # Example tests to ensure functions run
    test_text_1 = "The academics are very challenging, professors are knowledgeable. But the hostel infrastructure needs improvement, wifi is slow."
    test_text_2 = "Great placements this year! Many top companies visited. Campus life is also fun with lots of events."

    print(f"'{test_text_1[:30]}...' -> Compound: {get_vader_sentiment(test_text_1):.4f}")
    print(f"Aspects: {analyze_aspect_sentiment(test_text_1)}")
    print("-" * 20)
    print(f"'{test_text_2[:30]}...' -> Compound: {get_vader_sentiment(test_text_2):.4f}")
    print(f"Aspects: {analyze_aspect_sentiment(test_text_2)}")

    # Example DataFrame application test
    try:
        # This requires pandas to be installed
        data = {'text': [test_text_1, test_text_2, "Just okay.", "Bad food.", None, ""]}
        test_df = pd.DataFrame(data)
        test_df_analyzed = apply_sentiment_analysis_to_df(test_df)
        print("\n--- DataFrame Test ---")
        print(test_df_analyzed[['text', 'compound_sentiment', 'academics_sentiment', 'infrastructure_sentiment']])
    except ImportError:
        print("\nPandas not installed, skipping DataFrame test.")
    except Exception as e:
        print(f"\nError during DataFrame test: {e}")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
from wordcloud import WordCloud, STOPWORDS as WC_STOPWORDS
from pathlib import Path
import random
import re # Import re for cleaning filenames
from collections import Counter
from tqdm import tqdm # <--- ADD THIS LINE

# Set plot style
sns.set_theme(style="whitegrid", palette="pastel")

# Combine WordCloud stopwords with NLTK's and custom ones
# ... (Stopwords definition remains the same) ...
try:
    from nltk.corpus import stopwords as nltk_stopwords
    NLTK_STOPWORDS = set(nltk_stopwords.words('english'))
except LookupError:
    print("Warning: NLTK stopwords not found for WordCloud. Using default set.")
    NLTK_STOPWORDS = set()

CUSTOM_STOPWORDS = set([
    # Add highly frequent but potentially uninformative words from your specific domain
    'college', 'university', 'campus', 'student', 'students', 'iit', 'nit', 'bits',
    'india', 'indian', 'delhi', 'bombay', 'madras', 'kanpur', 'pilani', # Example specific names if too dominant
    'amp', 'nbsp', 'quot', 'gt', 'lt', 'http', 'https', 'www', 'com', 'reddit', 'subreddit',
    'post', 'comment', 'deleted', 'removed', 'mod', 'automod', 'automoderator', 'wiki', 'faq',
    'im', 'ive', 'like', 'got', 'get', 'also', 'would', 'make', 'really', 'one', 'go', 'going',
    'know', 'think', 'people', 'want', 'good', 'great', 'bad', 'best', 'worst', 'well',
    'even', 'see', 'lot', 'much', 'still', 'thing', 'say', 'take', 'year', 'time', 'day', 'first',
    'anyone', 'anything', 'something', 'everything', 'give', 'look', 'need', 'really', 'actually'
    ])
COMBINED_STOPWORDS = WC_STOPWORDS.union(NLTK_STOPWORDS).union(CUSTOM_STOPWORDS)

# --- Plotting Functions ---

def plot_overall_sentiment(sentiment_scores, output_path):
    """Creates and saves a bar chart of overall sentiment scores per college."""
    # ... (function remains the same) ...
    if sentiment_scores.empty: print("Cannot plot overall sentiment: Data is empty."); return
    print(f"Plotting overall sentiment scores...")
    try:
        output_path = Path(output_path); output_path.parent.mkdir(parents=True, exist_ok=True)
        num_items = len(sentiment_scores)
        plt.figure(figsize=(10, max(5, num_items * 0.3)))
        bars = sns.barplot(x=sentiment_scores.values, y=sentiment_scores.index, palette="coolwarm_r", orient='h')
        plt.title('Average Overall Sentiment Score per College', fontsize=15, pad=15)
        plt.xlabel('Average Compound Score (-1 Negative to +1 Positive)', fontsize=11)
        plt.ylabel('College (Approx.)', fontsize=11); plt.xlim(-1, 1)
        bars.bar_label(bars.containers[0], fmt='%.2f', fontsize=9, padding=3)
        plt.tight_layout(); plt.savefig(output_path, dpi=300, bbox_inches='tight'); plt.close()
        print(f"Saved overall sentiment plot to {output_path}")
    except Exception as e:
        print(f"Error plotting overall sentiment: {e}"); plt.close() if plt.gcf().get_axes() else None


def plot_aspect_sentiment(aspect_summary, output_path):
    """Creates and saves a heatmap of average aspect sentiment per college."""
    # ... (function remains the same) ...
    if aspect_summary.empty: print("Cannot plot aspect sentiment: Data is empty."); return
    print(f"Plotting aspect sentiment heatmap...")
    try:
        output_path = Path(output_path); output_path.parent.mkdir(parents=True, exist_ok=True)
        num_rows = aspect_summary.shape[0]; num_cols = aspect_summary.shape[1]
        plt.figure(figsize=(max(8, num_cols * 1.2), max(6, num_rows * 0.4)))
        sns.heatmap(aspect_summary, annot=True, fmt=".2f", cmap="coolwarm_r", linewidths=.5, vmin=-1, vmax=1, center=0, cbar_kws={'label': 'Average Sentiment Score'})
        plt.title('Average Sentiment Score by Aspect per College', fontsize=15, pad=15)
        plt.xlabel('Aspect', fontsize=11); plt.ylabel('College (Approx.)', fontsize=11)
        plt.xticks(rotation=30, ha='right'); plt.yticks(rotation=0)
        plt.tight_layout(); plt.savefig(output_path, dpi=300, bbox_inches='tight'); plt.close()
        print(f"Saved aspect sentiment heatmap to {output_path}")
    except Exception as e:
        print(f"Error plotting aspect sentiment heatmap: {e}"); plt.close() if plt.gcf().get_axes() else None


def plot_sentiment_trends(trends_df, output_path):
    """Creates and saves line plots for sentiment trends and comment volume."""
    # ... (function remains the same) ...
    if trends_df.empty or trends_df['mean_sentiment'].isnull().all(): print("Cannot plot sentiment trends: Data is empty/invalid."); return
    print(f"Plotting sentiment trends...")
    try:
        output_path = Path(output_path); output_path.parent.mkdir(parents=True, exist_ok=True)
        fig, ax1 = plt.subplots(figsize=(14, 7))
        color1 = 'tab:red'; ax1.set_xlabel('Time Period'); ax1.set_ylabel('Average Compound Sentiment', color=color1, fontsize=11)
        ax1.plot(trends_df.index, trends_df['mean_sentiment'], color=color1, marker='o', linestyle='-', linewidth=2, label='Avg Sentiment')
        ax1.tick_params(axis='y', labelcolor=color1); ax1.set_ylim(-1, 1); ax1.grid(True, axis='y', linestyle='--', alpha=0.6)
        ax2 = ax1.twinx(); color2 = 'tab:blue'; ax2.set_ylabel('Number of Comments', color=color2, fontsize=11)
        ax2.bar(trends_df.index, trends_df['comment_count'], color=color2, alpha=0.4, width=20, label='Comment Count') # Adjust width
        ax2.tick_params(axis='y', labelcolor=color2); ax2.set_ylim(bottom=0)
        plt.title('Sentiment Trend and Comment Volume Over Time', fontsize=15, pad=15); fig.autofmt_xdate()
        ax1.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=5, maxticks=12))
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        lines, labels = ax1.get_legend_handles_labels(); bars, bar_labels = ax2.get_legend_handles_labels()
        ax2.legend(lines + bars, labels + bar_labels, loc='upper left')
        fig.tight_layout(); plt.savefig(output_path, dpi=300, bbox_inches='tight'); plt.close()
        print(f"Saved sentiment trend plot to {output_path}")
    except Exception as e:
        print(f"Error plotting sentiment trends: {e}"); plt.close() if plt.gcf().get_axes() else None


def generate_word_cloud(text_list, output_path, stopwords_set=COMBINED_STOPWORDS):
    """Generates and saves a word cloud from text or tokens."""
    # ... (function remains the same) ...
    if not text_list: print(f"Cannot generate word cloud for {output_path.stem}: No text."); return
    print(f"Generating word cloud for {output_path.stem}...")
    try:
        output_path = Path(output_path); output_path.parent.mkdir(parents=True, exist_ok=True)
        if text_list and isinstance(text_list[0], list): text_combined = ' '.join([token for sublist in text_list for token in sublist])
        elif text_list and isinstance(text_list[0], str): text_combined = ' '.join(text_list)
        else: print(f"Cannot generate word cloud for {output_path.stem}: Invalid format."); return
        if not text_combined.strip(): print(f"Cannot generate word cloud for {output_path.stem}: Combined text empty."); return

        wordcloud = WordCloud(width=800, height=400, background_color='white', stopwords=stopwords_set, max_words=100, colormap='viridis', contour_width=1, contour_color='steelblue', collocations=False).generate(text_combined)
        plt.figure(figsize=(12, 6)); plt.imshow(wordcloud, interpolation='bilinear'); plt.axis('off')
        plt.title(f"Word Cloud - {output_path.stem}", fontsize=15, pad=10); plt.tight_layout(pad=0)
        plt.savefig(output_path, dpi=300); plt.close()
        print(f"Saved word cloud to {output_path}")
    except Exception as e:
        print(f"Error generating word cloud for {output_path.stem}: {e}"); plt.close() if plt.gcf().get_axes() else None

def plot_word_clouds_for_top_reviews(top_reviews_dict, df_processed, output_dir,
                                     college_col='college_name_approx', tokens_col='processed_tokens', text_col='text'):
    """Generates word clouds for top positive and negative reviews for each college."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine if using pre-processed tokens is feasible (check if column exists)
    # For simplicity now, we'll primarily use the raw text from the top_reviews_dict
    # Fetching tokens based on permalink/text matching could be added but is more complex
    use_tokens = False # Set to False to use raw text from the dict directly
    # if tokens_col in df_processed.columns:
    #     use_tokens = True
    #     print("Using processed tokens column for word clouds.")
    # else:
    #     print("Processed tokens column not found, using raw text for word clouds.")

    print("\nGenerating word clouds for top reviews...")
    if not top_reviews_dict:
        print("No top reviews data provided, skipping word clouds.")
        return

    # --- Corrected loop using tqdm ---
    for college, reviews in tqdm(top_reviews_dict.items(), desc="Word Clouds", unit="college"):
        # Clean college name for filename
        safe_college_name = re.sub(r'[^\w\-]+', '_', college.lower())

        # --- Positive Reviews ---
        positive_reviews_data = reviews.get('positive', [])
        if positive_reviews_data:
            # Extract text directly from the top_reviews structure
            positive_texts = [r.get(text_col, '') for r in positive_reviews_data]
            wc_path_pos = output_dir / f"{safe_college_name}_positive_wc.png"
            generate_word_cloud(positive_texts, wc_path_pos)
        else:
             print(f"No positive reviews found for {college} word cloud.")

        # --- Negative Reviews ---
        negative_reviews_data = reviews.get('negative', [])
        if negative_reviews_data:
            # Extract text directly
            negative_texts = [r.get(text_col, '') for r in negative_reviews_data]
            wc_path_neg = output_dir / f"{safe_college_name}_negative_wc.png"
            generate_word_cloud(negative_texts, wc_path_neg)
        else:
             print(f"No negative reviews found for {college} word cloud.")
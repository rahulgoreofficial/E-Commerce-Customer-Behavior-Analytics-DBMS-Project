"""
Review Dataset Loader & Preprocessor — Loads, cleans, and analyzes Amazon_Reviews.csv.
Provides structured data for ML training, database seeding, and GUI exploration.
"""
import os
import re
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple

DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "dataset", "Amazon_Reviews.csv")

# Topic keywords for rule-based aspect extraction
TOPIC_KEYWORDS = {
    "Delivery & Logistics": ["delivery", "driver", "package", "arrived", "shipping", "late", "courier", "door", "tracking", "delivered"],
    "Product Quality": ["quality", "broke", "broken", "defective", "cheap", "damaged", "material", "works", "plastic", "durability"],
    "Customer Support": ["customer service", "support", "help", "chat", "email", "rude", "agent", "call", "refund", "returned", "return"],
    "Pricing & Billing": ["price", "cost", "charge", "charged", "expensive", "money", "worth", "discount", "bill", "payment"],
    "Account & App": ["account", "login", "password", "frozen", "app", "website", "verification", "blocked", "otp", "register"]
}


class ReviewDatasetLoader:
    """Handles loading and preprocessing of Amazon Reviews dataset."""

    def __init__(self, csv_path: str = DATASET_PATH):
        self.csv_path = csv_path
        self._cached_df: Optional[pd.DataFrame] = None

    @staticmethod
    def extract_stars(val) -> Optional[int]:
        """Extract integer rating 1-5 from strings like 'Rated 1 out of 5 stars'."""
        if pd.isna(val):
            return None
        val_str = str(val)
        m = re.search(r'Rated\s*(\d)', val_str, re.IGNORECASE)
        if m:
            return int(m.group(1))
        m2 = re.search(r'(\d)', val_str)
        if m2:
            return int(m2.group(1))
        return None

    @staticmethod
    def get_sentiment_label(stars: int) -> str:
        """Map 1-5 stars to Sentiment Label."""
        if stars <= 2:
            return "Negative"
        elif stars == 3:
            return "Neutral"
        else:
            return "Positive"

    @staticmethod
    def get_sentiment_score(stars: int) -> float:
        """Map 1-5 stars to continuous sentiment score (-1.0 to +1.0)."""
        # 1 -> -1.0, 2 -> -0.5, 3 -> 0.0, 4 -> +0.5, 5 -> +1.0
        return round((stars - 3.0) / 2.0, 2)

    @staticmethod
    def detect_topics(text: str) -> List[str]:
        """Identify relevant topics/aspects mentioned in the review."""
        if not text or not isinstance(text, str):
            return ["General"]
        text_lower = text.lower()
        matched = []
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                matched.append(topic)
        return matched if matched else ["General"]

    def load_clean_data(self, max_rows: Optional[int] = None) -> pd.DataFrame:
        """Load and clean dataset with all extracted fields."""
        if self._cached_df is not None and max_rows is None:
            return self._cached_df

        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"Review dataset not found at: {self.csv_path}")

        # Resilient load using python engine to handle malformed quoting
        df = pd.read_csv(
            self.csv_path,
            engine='python',
            on_bad_lines='skip',
            nrows=max_rows
        )

        # Standardize column names
        df.columns = [c.strip() for c in df.columns]

        # Extract numeric star rating
        df['stars'] = df['Rating'].apply(self.extract_stars)
        df = df.dropna(subset=['stars'])
        df['stars'] = df['stars'].astype(int)

        # Combined clean text
        title = df['Review Title'].fillna('').astype(str)
        text = df['Review Text'].fillna('').astype(str)
        df['full_text'] = (title + ". " + text).str.strip()
        df = df[df['full_text'].str.len() > 3]

        # Sentiment mappings
        df['sentiment_label'] = df['stars'].apply(self.get_sentiment_label)
        df['sentiment_score'] = df['stars'].apply(self.get_sentiment_score)
        
        # Binary target for ML: 0 = Negative, 1 = Neutral, 2 = Positive
        sentiment_target_map = {"Negative": 0, "Neutral": 1, "Positive": 2}
        df['sentiment_target'] = df['sentiment_label'].map(sentiment_target_map)

        # Topics
        df['topics'] = df['full_text'].apply(self.detect_topics)
        df['primary_topic'] = df['topics'].apply(lambda x: x[0] if x else "General")

        # Reviewer and metadata clean
        df['Reviewer Name'] = df['Reviewer Name'].fillna('Anonymous Customer').astype(str)
        df['Country'] = df['Country'].fillna('US').astype(str)
        df['Review Date'] = pd.to_datetime(df['Review Date'], errors='coerce')

        if max_rows is None:
            self._cached_df = df

        return df

    def get_dataset_stats(self) -> Dict:
        """Return comprehensive statistical summary of the review dataset."""
        df = self.load_clean_data()
        stars_dist = df['stars'].value_counts().sort_index().to_dict()
        sentiment_dist = df['sentiment_label'].value_counts().to_dict()
        topic_counts = {}
        for topics in df['topics']:
            for t in topics:
                topic_counts[t] = topic_counts.get(t, 0) + 1

        return {
            'total_reviews': len(df),
            'avg_rating': round(df['stars'].mean(), 2),
            'avg_sentiment_score': round(df['sentiment_score'].mean(), 2),
            'stars_distribution': stars_dist,
            'sentiment_distribution': sentiment_dist,
            'topic_distribution': dict(sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)),
            'top_countries': df['Country'].value_counts().head(5).to_dict(),
            'avg_word_count': round(df['full_text'].apply(lambda x: len(x.split())).mean(), 1)
        }

    def get_training_data(self) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Return (clean_texts, sentiment_targets, star_ratings) for ML training."""
        df = self.load_clean_data()
        return df['full_text'], df['sentiment_target'], df['stars']

    def sample_reviews_for_seeding(self, n: int = 1500) -> List[Dict]:
        """Get a representative balanced sample of reviews for database population."""
        df = self.load_clean_data()
        # Sample across sentiment classes for realistic distribution
        sample_df = df.sample(min(n, len(df)), random_state=42)
        reviews = []
        for _, row in sample_df.iterrows():
            reviews.append({
                'reviewer_name': str(row['Reviewer Name']),
                'rating': int(row['stars']),
                'review_title': str(row['Review Title']) if pd.notna(row['Review Title']) else '',
                'review_text': str(row['Review Text']) if pd.notna(row['Review Text']) else str(row['full_text']),
                'sentiment_score': float(row['sentiment_score']),
                'country': str(row['Country']),
                'topic': str(row['primary_topic'])
            })
        return reviews


# Module-level singleton
review_loader = ReviewDatasetLoader()

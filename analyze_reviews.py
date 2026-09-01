import pandas as pd
import numpy as np
import re

print("Loading Amazon_Reviews.csv...")
df = pd.read_csv('dataset/Amazon_Reviews.csv', engine='python', on_bad_lines='skip')
print(f"Total loaded reviews: {len(df)}")
print("Columns:", df.columns.tolist())

# Clean Rating to integer 1-5
def extract_rating(val):
    if pd.isna(val):
        return np.nan
    val_str = str(val)
    m = re.search(r'Rated\s*(\d)', val_str, re.IGNORECASE)
    if m:
        return int(m.group(1))
    m2 = re.search(r'(\d)', val_str)
    if m2:
        return int(m2.group(1))
    return np.nan

df['stars'] = df['Rating'].apply(extract_rating)
print("\n--- Star Rating Distribution ---")
print(df['stars'].value_counts().sort_index())
print("Percentage:")
print((df['stars'].value_counts(normalize=True).sort_index() * 100).round(2))

# Sentiment class: 1-2 => Negative, 3 => Neutral, 4-5 => Positive
def classify_sentiment(stars):
    if stars <= 2:
        return 'Negative'
    elif stars == 3:
        return 'Neutral'
    else:
        return 'Positive'

df['sentiment_label'] = df['stars'].apply(classify_sentiment)
print("\n--- Sentiment Label Distribution ---")
print(df['sentiment_label'].value_counts())

# Review text length
df['text_len'] = df['Review Text'].fillna('').astype(str).apply(len)
df['word_count'] = df['Review Text'].fillna('').astype(str).apply(lambda x: len(x.split()))
print("\n--- Text Statistics ---")
print(f"Mean word count: {df['word_count'].mean():.1f}, Median: {df['word_count'].median():.1f}, Max: {df['word_count'].max()}")
print(f"Missing Review Text: {df['Review Text'].isna().sum()}")
print(f"Missing Review Title: {df['Review Title'].isna().sum()}")

# Country distribution
if 'Country' in df.columns:
    print("\n--- Top 10 Countries ---")
    print(df['Country'].value_counts().head(10))

# Sample reviews across ratings
print("\n--- Sample Reviews ---")
for star in [1, 3, 5]:
    sample = df[df['stars'] == star].dropna(subset=['Review Text']).head(2)
    print(f"\n[Rating {star} Star Samples]:")
    for _, r in sample.iterrows():
        print(f"Title: {r['Review Title']}")
        print(f"Text: {str(r['Review Text'])[:150]}...")

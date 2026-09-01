import pandas as pd
import numpy as np
import re
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, f1_score, confusion_matrix

print("Loading dataset...")
df = pd.read_csv('dataset/Amazon_Reviews.csv', engine='python', on_bad_lines='skip')

def extract_rating(val):
    if pd.isna(val):
        return np.nan
    m = re.search(r'Rated\s*(\d)', str(val), re.IGNORECASE)
    if m:
        return int(m.group(1))
    m2 = re.search(r'(\d)', str(val))
    return int(m2.group(1)) if m2 else np.nan

df['stars'] = df['Rating'].apply(extract_rating)
df = df.dropna(subset=['stars'])
df['stars'] = df['stars'].astype(int)

# Combine title and text
df['clean_text'] = df['Review Title'].fillna('') + ' ' + df['Review Text'].fillna('')
df = df[df['clean_text'].str.strip().str.len() > 5]

def get_sentiment(stars):
    if stars <= 2:
        return 0  # Negative
    elif stars == 3:
        return 1  # Neutral
    else:
        return 2  # Positive

df['target_sentiment'] = df['stars'].apply(get_sentiment)

print(f"Clean samples: {len(df)}")
print("Class counts:")
print(df['target_sentiment'].value_counts())

X_train, X_test, y_train, y_test = train_test_split(
    df['clean_text'], df['target_sentiment'], test_size=0.2, random_state=42, stratify=df['target_sentiment']
)

print("\nVectorizing text with TF-IDF...")
vectorizer = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1, 2),
    stop_words='english',
    sublinear_tf=True
)

X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

print("\nTraining Logistic Regression (Balanced)...")
clf = LogisticRegression(max_iter=1000, class_weight='balanced', C=1.0)
clf.fit(X_train_vec, y_train)

y_pred = clf.predict(X_test_vec)
acc = accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred, average='weighted')

print(f"Accuracy: {acc:.4f}")
print(f"Weighted F1: {f1:.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=['Negative', 'Neutral', 'Positive']))

# Feature importance (top terms for each class)
feature_names = np.array(vectorizer.get_feature_names_out())
for i, class_label in enumerate(['Negative', 'Neutral', 'Positive']):
    top_indices = np.argsort(clf.coef_[i])[-10:]
    top_terms = feature_names[top_indices]
    print(f"\nTop terms for {class_label}: {list(reversed(top_terms))}")

# Test sample custom sentences
test_sentences = [
    "Amazing product, super fast delivery and great build quality!",
    "Terrible customer service, package arrived broken and they refused refund.",
    "Decent product for the price, average quality but works okay."
]
test_vec = vectorizer.transform(test_sentences)
preds = clf.predict(test_vec)
probs = clf.predict_proba(test_vec)
label_map = {0: 'Negative', 1: 'Neutral', 2: 'Positive'}
print("\n--- Live Test Sentences ---")
for sent, p, pr in zip(test_sentences, preds, probs):
    print(f"Sentence: '{sent}'")
    print(f"Prediction: {label_map[p]} | Probs: Neg={pr[0]:.2f}, Neu={pr[1]:.2f}, Pos={pr[2]:.2f}")

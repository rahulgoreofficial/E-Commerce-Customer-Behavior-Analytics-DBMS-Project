"""
ML Models — Purchase Prediction, Cart Abandonment Prediction, and Review Sentiment NLP.
Classical & NLP ML models using scikit-learn.
"""
import os
import pickle
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    f1_score, precision_score, recall_score, accuracy_score
)
from src.config import ML_MODEL_DIR
from src.ml.feature_engineering import feature_engineer
from src.ml.review_loader import review_loader


class MLModelManager:
    """Manages training, evaluation, and real-time prediction for all ML models."""

    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.vectorizers = {}
        self.results = {}
        self.feature_columns = {}
        os.makedirs(ML_MODEL_DIR, exist_ok=True)
        # Pre-load saved models if they exist
        self._load_all_saved_models()

    def _prepare_data(self, df, target_col, id_cols):
        """Prepare features and target, handling missing values."""
        drop_cols = id_cols + [target_col]
        X = df.drop(columns=[c for c in drop_cols if c in df.columns])
        y = df[target_col]
        
        # Fill any NaN
        X = X.fillna(0)
        
        # Ensure all numeric
        for col in X.columns:
            X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)
        
        return X, y

    def _load_all_saved_models(self):
        """Pre-load existing models from disk."""
        for name in ['purchase', 'abandonment', 'review_sentiment']:
            self._load_model(name)

    # ──────────────────────────────────────────────
    # 1. PURCHASE PREDICTION MODEL
    # ──────────────────────────────────────────────
    def train_purchase_prediction(self):
        """Train purchase prediction model (Random Forest + Logistic Regression baseline)."""
        print("Training Purchase Prediction Model...")
        
        df = feature_engineer.get_purchase_prediction_features()
        if len(df) < 50:
            return {"error": "Not enough data for training. Need at least 50 sessions."}
        
        X, y = self._prepare_data(df, 'purchased', ['session_id', 'customer_id'])
        self.feature_columns['purchase'] = list(X.columns)
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y if y.nunique() > 1 else None
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        self.scalers['purchase'] = scaler
        
        results = {}
        
        # ── Baseline: Logistic Regression ──
        lr = LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced')
        lr.fit(X_train_scaled, y_train)
        lr_pred = lr.predict(X_test_scaled)
        lr_prob = lr.predict_proba(X_test_scaled)[:, 1] if len(lr.classes_) > 1 else np.zeros(len(X_test))
        results['baseline_logistic'] = self._evaluate(y_test, lr_pred, lr_prob, "Logistic Regression (Baseline)")
        
        # ── Primary: Random Forest ──
        rf = RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42,
            class_weight='balanced', n_jobs=-1
        )
        rf.fit(X_train, y_train)
        rf_pred = rf.predict(X_test)
        rf_prob = rf.predict_proba(X_test)[:, 1] if len(rf.classes_) > 1 else np.zeros(len(X_test))
        results['random_forest'] = self._evaluate(y_test, rf_pred, rf_prob, "Random Forest (Primary)")
        
        # Feature importance
        importances = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False)
        results['feature_importance'] = importances.head(15).to_dict()
        
        # Save model
        self.models['purchase'] = rf
        self._save_model('purchase', rf, scaler)
        
        self.results['purchase'] = results
        print("Purchase Prediction training complete.")
        return results

    # ──────────────────────────────────────────────
    # 2. CART ABANDONMENT PREDICTION MODEL
    # ──────────────────────────────────────────────
    def train_cart_abandonment(self):
        """Train cart abandonment prediction model."""
        print("Training Cart Abandonment Prediction Model...")
        
        df = feature_engineer.get_cart_abandonment_features()
        if len(df) < 50:
            return {"error": "Not enough data for training. Need at least 50 carts."}
        
        X, y = self._prepare_data(df, 'abandoned', ['cart_id', 'customer_id'])
        self.feature_columns['abandonment'] = list(X.columns)
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y if y.nunique() > 1 else None
        )
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        self.scalers['abandonment'] = scaler
        
        results = {}
        
        # Baseline
        lr = LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced')
        lr.fit(X_train_scaled, y_train)
        lr_pred = lr.predict(X_test_scaled)
        lr_prob = lr.predict_proba(X_test_scaled)[:, 1] if len(lr.classes_) > 1 else np.zeros(len(X_test))
        results['baseline_logistic'] = self._evaluate(y_test, lr_pred, lr_prob, "Logistic Regression (Baseline)")
        
        # Primary
        rf = RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42,
            class_weight='balanced', n_jobs=-1
        )
        rf.fit(X_train, y_train)
        rf_pred = rf.predict(X_test)
        rf_prob = rf.predict_proba(X_test)[:, 1] if len(rf.classes_) > 1 else np.zeros(len(X_test))
        results['random_forest'] = self._evaluate(y_test, rf_pred, rf_prob, "Random Forest (Primary)")
        
        importances = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False)
        results['feature_importance'] = importances.head(15).to_dict()
        
        self.models['abandonment'] = rf
        self._save_model('abandonment', rf, scaler)
        
        self.results['abandonment'] = results
        print("Cart Abandonment training complete.")
        return results

    # ──────────────────────────────────────────────
    # 3. REVIEW SENTIMENT & NLP MODEL
    # ──────────────────────────────────────────────
    def train_review_sentiment_model(self):
        """Train NLP Sentiment Classifier on 21,000+ real Amazon Reviews."""
        print("Training Review Sentiment & Rating NLP Model...")
        try:
            texts, targets, stars = review_loader.get_training_data()
        except Exception as e:
            return {"error": f"Failed to load review dataset: {e}"}

        if len(texts) < 100:
            return {"error": "Not enough review data for training."}

        X_train, X_test, y_train, y_test = train_test_split(
            texts, targets, test_size=0.2, random_state=42, stratify=targets
        )

        # TF-IDF Vectorizer
        vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            stop_words='english',
            sublinear_tf=True
        )
        X_train_vec = vectorizer.fit_transform(X_train)
        X_test_vec = vectorizer.transform(X_test)

        self.vectorizers['review_sentiment'] = vectorizer

        results = {}

        # ── Baseline: Multinomial Naive Bayes ──
        nb = MultinomialNB()
        nb.fit(X_train_vec, y_train)
        nb_pred = nb.predict(X_test_vec)
        nb_prob = nb.predict_proba(X_test_vec)
        results['baseline_nb'] = self._evaluate_multiclass(
            y_test, nb_pred, nb_prob, "Multinomial Naive Bayes (Baseline)",
            target_names=['Negative', 'Neutral', 'Positive']
        )

        # ── Primary: Balanced Logistic Regression with TF-IDF ──
        clf = LogisticRegression(max_iter=1000, class_weight='balanced', C=1.0, random_state=42)
        clf.fit(X_train_vec, y_train)
        clf_pred = clf.predict(X_test_vec)
        clf_prob = clf.predict_proba(X_test_vec)
        results['primary_lr'] = self._evaluate_multiclass(
            y_test, clf_pred, clf_prob, "TF-IDF + Logistic Regression (Primary)",
            target_names=['Negative', 'Neutral', 'Positive']
        )

        # Top N-Gram keywords for each sentiment class
        feature_names = np.array(vectorizer.get_feature_names_out())
        top_keywords = {}
        for i, class_label in enumerate(['Negative', 'Neutral', 'Positive']):
            top_indices = np.argsort(clf.coef_[i])[-12:]
            top_keywords[class_label] = list(reversed(feature_names[top_indices].tolist()))

        results['top_keywords'] = top_keywords
        results['dataset_size'] = len(texts)

        # Save model and vectorizer
        self.models['review_sentiment'] = clf
        self._save_nlp_model('review_sentiment', clf, vectorizer)

        self.results['review_sentiment'] = results
        print("Review Sentiment NLP training complete.")
        return results

    # ──────────────────────────────────────────────
    # REAL-TIME INFERENCE APIs
    # ──────────────────────────────────────────────
    def predict_review_sentiment(self, text: str) -> Dict[str, Any]:
        """Real-time sentiment, star rating, and trigger word prediction for custom text."""
        model = self._load_model('review_sentiment')
        vectorizer = self._load_vectorizer('review_sentiment')

        # Fallback keyword-based heuristic if model not trained yet
        if model is None or vectorizer is None:
            text_lower = (text or "").lower()
            neg_words = ["terrible", "worst", "bad", "poor", "broken", "scam", "waste", "hate", "refuse", "never"]
            pos_words = ["great", "excellent", "amazing", "love", "best", "fast", "good", "perfect", "awesome", "nice"]
            neg_count = sum(1 for w in neg_words if w in text_lower)
            pos_count = sum(1 for w in pos_words if w in text_lower)
            if pos_count > neg_count:
                sentiment = "Positive"
                score = 0.8
                stars = 5
            elif neg_count > pos_count:
                sentiment = "Negative"
                score = -0.8
                stars = 1
            else:
                sentiment = "Neutral"
                score = 0.0
                stars = 3
            return {
                'sentiment': sentiment,
                'confidence': 0.75,
                'sentiment_score': score,
                'predicted_stars': stars,
                'probabilities': {'Negative': 0.1, 'Neutral': 0.1, 'Positive': 0.8} if sentiment == 'Positive' else {'Negative': 0.8, 'Neutral': 0.1, 'Positive': 0.1},
                'trigger_words': {'positive': [w for w in pos_words if w in text_lower], 'negative': [w for w in neg_words if w in text_lower]}
            }

        vec = vectorizer.transform([text])
        pred_class = model.predict(vec)[0]
        probs = model.predict_proba(vec)[0]

        label_map = {0: 'Negative', 1: 'Neutral', 2: 'Positive'}
        sentiment_label = label_map.get(pred_class, 'Neutral')
        confidence = float(probs[pred_class])

        # Estimate expected continuous score and stars
        # Expected value: (-1.0)*P(Neg) + (0.0)*P(Neu) + (+1.0)*P(Pos)
        sentiment_score = round(float((-1.0 * probs[0]) + (0.0 * probs[1]) + (1.0 * probs[2])), 2)
        
        # Expected stars: 1.5*P(Neg) + 3.0*P(Neu) + 4.8*P(Pos)
        expected_stars = round(float((1.5 * probs[0]) + (3.0 * probs[1]) + (4.8 * probs[2])))
        expected_stars = max(1, min(5, expected_stars))

        # Extract trigger terms present in this text
        feature_names = vectorizer.get_feature_names_out()
        text_lower = text.lower()
        active_pos = []
        active_neg = []

        # Find words with highest coefficients present in the text
        if hasattr(model, 'coef_'):
            neg_coefs = model.coef_[0]
            pos_coefs = model.coef_[2]
            for word_idx in vec.indices:
                word = feature_names[word_idx]
                if pos_coefs[word_idx] > 0.4:
                    active_pos.append(word)
                elif neg_coefs[word_idx] > 0.4:
                    active_neg.append(word)

        return {
            'sentiment': sentiment_label,
            'confidence': confidence,
            'sentiment_score': sentiment_score,
            'predicted_stars': expected_stars,
            'probabilities': {
                'Negative': round(float(probs[0]), 3),
                'Neutral': round(float(probs[1]), 3),
                'Positive': round(float(probs[2]), 3)
            },
            'trigger_words': {
                'positive': active_pos[:6],
                'negative': active_neg[:6]
            }
        }

    def predict_live_purchase(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Real-time purchase probability calculation for interactive UI sliders."""
        model = self._load_model('purchase')
        
        # Heuristic baseline fallback if model is not yet trained
        duration = float(inputs.get('session_duration_min', 10))
        views = float(inputs.get('products_viewed', 3))
        cart_adds = float(inputs.get('cart_adds', 1))
        searches = float(inputs.get('searches', 1))
        is_returning = float(inputs.get('is_returning_customer', 0))
        device = str(inputs.get('device', 'desktop')).lower()

        if model is None:
            # High-fidelity probabilistic simulation formula
            score = (views * 0.08) + (cart_adds * 0.35) + (searches * 0.05) + (duration * 0.015) + (is_returning * 0.20)
            if device == 'mobile':
                score *= 0.85
            prob = min(0.98, max(0.02, 1.0 / (1.0 + np.exp(-1.8 * (score - 0.7)))))
        else:
            cols = self.feature_columns.get('purchase', [])
            row = {c: 0.0 for c in cols}
            row['session_duration_min'] = duration
            row['products_viewed'] = views
            row['pages_viewed'] = views * 1.5
            row['cart_adds'] = cart_adds
            row['searches'] = searches
            row['is_returning_customer'] = is_returning
            if f'device_{device}' in row:
                row[f'device_{device}'] = 1.0
            
            df_row = pd.DataFrame([row])[cols].fillna(0)
            prob = float(model.predict_proba(df_row)[0][1])

        risk = "High Conversion Intent" if prob >= 0.65 else ("Moderate Intent" if prob >= 0.30 else "Low Intent")
        return {
            'purchase_probability': round(prob, 3),
            'intent_level': risk,
            'recommended_action': "Trigger Instant Checkout Discount Offer" if prob >= 0.60 else "Show Social Proof & Product Reviews"
        }

    def predict_live_abandonment(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Real-time cart abandonment probability calculation for interactive UI sliders."""
        model = self._load_model('abandonment')

        cart_value = float(inputs.get('cart_value', 1500))
        num_items = float(inputs.get('num_items', 2))
        items_removed = float(inputs.get('items_removed', 0))
        session_duration = float(inputs.get('session_duration_min', 8))
        checkout_started = float(inputs.get('checkout_started', 0))
        device = str(inputs.get('device', 'mobile')).lower()

        if model is None:
            # Baseline simulation formula
            friction = (cart_value / 5000.0) * 0.3 + (items_removed * 0.4) + (0.2 if device == 'mobile' else 0.0) - (checkout_started * 0.25)
            prob = min(0.95, max(0.05, 1.0 / (1.0 + np.exp(-2.0 * (friction + 0.3)))))
        else:
            cols = self.feature_columns.get('abandonment', [])
            row = {c: 0.0 for c in cols}
            row['cart_value'] = cart_value
            row['num_items'] = num_items
            row['items_removed'] = items_removed
            row['session_duration_min'] = session_duration
            row['checkout_started'] = checkout_started
            if f'device_{device}' in row:
                row[f'device_{device}'] = 1.0

            df_row = pd.DataFrame([row])[cols].fillna(0)
            prob = float(model.predict_proba(df_row)[0][1])

        risk_level = "Critical Abandonment Risk" if prob >= 0.70 else ("Moderate Risk" if prob >= 0.40 else "Safe / Converting")
        return {
            'abandonment_probability': round(prob, 3),
            'risk_level': risk_level,
            'recommended_action': "Send Abandoned Cart Recovery SMS with 10% Voucher" if prob >= 0.70 else "Display Free Shipping Progress Bar"
        }

    # ──────────────────────────────────────────────
    # EVALUATION HELPERS
    # ──────────────────────────────────────────────
    def _evaluate(self, y_true, y_pred, y_prob, model_name):
        """Compute binary classification metrics."""
        metrics = {
            'model': model_name,
            'accuracy': round(accuracy_score(y_true, y_pred), 4),
            'precision': round(precision_score(y_true, y_pred, zero_division=0), 4),
            'recall': round(recall_score(y_true, y_pred, zero_division=0), 4),
            'f1': round(f1_score(y_true, y_pred, zero_division=0), 4),
            'roc_auc': round(roc_auc_score(y_true, y_prob), 4) if len(set(y_true)) > 1 else 0.0,
            'confusion_matrix': confusion_matrix(y_true, y_pred).tolist(),
            'classification_report': classification_report(y_true, y_pred, zero_division=0, output_dict=True),
        }
        print(f"\n  {model_name}: Accuracy={metrics['accuracy']}, F1={metrics['f1']}, ROC-AUC={metrics['roc_auc']}")
        return metrics

    def _evaluate_multiclass(self, y_true, y_pred, y_prob, model_name, target_names):
        """Compute multi-class evaluation metrics."""
        metrics = {
            'model': model_name,
            'accuracy': round(accuracy_score(y_true, y_pred), 4),
            'f1': round(f1_score(y_true, y_pred, average='weighted', zero_division=0), 4),
            'precision': round(precision_score(y_true, y_pred, average='weighted', zero_division=0), 4),
            'recall': round(recall_score(y_true, y_pred, average='weighted', zero_division=0), 4),
            'confusion_matrix': confusion_matrix(y_true, y_pred).tolist(),
            'classification_report': classification_report(y_true, y_pred, target_names=target_names, zero_division=0, output_dict=True),
        }
        print(f"\n  {model_name}: Accuracy={metrics['accuracy']}, Weighted-F1={metrics['f1']}")
        return metrics

    def _save_model(self, name, model, scaler):
        """Save classical model and scaler to disk."""
        model_path = os.path.join(ML_MODEL_DIR, f"{name}_model.pkl")
        scaler_path = os.path.join(ML_MODEL_DIR, f"{name}_scaler.pkl")
        cols_path = os.path.join(ML_MODEL_DIR, f"{name}_columns.pkl")
        
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        with open(scaler_path, 'wb') as f:
            pickle.dump(scaler, f)
        with open(cols_path, 'wb') as f:
            pickle.dump(self.feature_columns.get(name, []), f)

    def _save_nlp_model(self, name, model, vectorizer):
        """Save NLP model and TF-IDF vectorizer to disk."""
        model_path = os.path.join(ML_MODEL_DIR, f"{name}_model.pkl")
        vec_path = os.path.join(ML_MODEL_DIR, f"{name}_vectorizer.pkl")
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        with open(vec_path, 'wb') as f:
            pickle.dump(vectorizer, f)
        print(f"  NLP Model & Vectorizer saved: {model_path}")

    def _load_model(self, name):
        """Load model from disk."""
        if name in self.models and self.models[name] is not None:
            return self.models[name]
        
        model_path = os.path.join(ML_MODEL_DIR, f"{name}_model.pkl")
        cols_path = os.path.join(ML_MODEL_DIR, f"{name}_columns.pkl")
        
        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    self.models[name] = pickle.load(f)
                if os.path.exists(cols_path):
                    with open(cols_path, 'rb') as f:
                        self.feature_columns[name] = pickle.load(f)
                return self.models[name]
            except Exception as e:
                print(f"  Warning: Could not load model {name}: {e}")
        return None

    def _load_vectorizer(self, name):
        """Load vectorizer from disk."""
        if name in self.vectorizers and self.vectorizers[name] is not None:
            return self.vectorizers[name]

        vec_path = os.path.join(ML_MODEL_DIR, f"{name}_vectorizer.pkl")
        if os.path.exists(vec_path):
            try:
                with open(vec_path, 'rb') as f:
                    self.vectorizers[name] = pickle.load(f)
                return self.vectorizers[name]
            except Exception as e:
                print(f"  Warning: Could not load vectorizer {name}: {e}")
        return None

    def get_all_results(self):
        """Return all training results."""
        return self.results


# Module-level singleton
ml_manager = MLModelManager()

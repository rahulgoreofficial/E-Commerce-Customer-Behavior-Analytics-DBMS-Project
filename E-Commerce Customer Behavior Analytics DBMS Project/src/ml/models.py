"""
ML Models — Purchase Prediction and Cart Abandonment Prediction.
Classical ML models using scikit-learn.
"""
import os
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    f1_score, precision_score, recall_score, accuracy_score
)
from src.config import ML_MODEL_DIR
from src.ml.feature_engineering import feature_engineer


class MLModelManager:
    """Manages training, evaluation, and prediction for all ML models."""

    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.results = {}
        self.feature_columns = {}
        os.makedirs(ML_MODEL_DIR, exist_ok=True)

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

    def predict_purchase_probability(self, session_features_df):
        """Predict purchase probability for given sessions."""
        model = self._load_model('purchase')
        if model is None:
            return None
        
        # Align columns
        for col in self.feature_columns.get('purchase', []):
            if col not in session_features_df.columns:
                session_features_df[col] = 0
        X = session_features_df[self.feature_columns['purchase']].fillna(0)
        
        probs = model.predict_proba(X)[:, 1]
        return probs

    def predict_abandonment_probability(self, cart_features_df):
        """Predict abandonment probability for given carts."""
        model = self._load_model('abandonment')
        if model is None:
            return None
        
        for col in self.feature_columns.get('abandonment', []):
            if col not in cart_features_df.columns:
                cart_features_df[col] = 0
        X = cart_features_df[self.feature_columns['abandonment']].fillna(0)
        
        probs = model.predict_proba(X)[:, 1]
        return probs

    def _evaluate(self, y_true, y_pred, y_prob, model_name):
        """Compute evaluation metrics."""
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
        print(f"\n  {model_name}:")
        print(f"    Accuracy: {metrics['accuracy']}")
        print(f"    F1:       {metrics['f1']}")
        print(f"    ROC-AUC:  {metrics['roc_auc']}")
        return metrics

    def _save_model(self, name, model, scaler):
        """Save model and scaler to disk."""
        model_path = os.path.join(ML_MODEL_DIR, f"{name}_model.pkl")
        scaler_path = os.path.join(ML_MODEL_DIR, f"{name}_scaler.pkl")
        cols_path = os.path.join(ML_MODEL_DIR, f"{name}_columns.pkl")
        
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        with open(scaler_path, 'wb') as f:
            pickle.dump(scaler, f)
        with open(cols_path, 'wb') as f:
            pickle.dump(self.feature_columns.get(name, []), f)
        
        print(f"  Model saved: {model_path}")

    def _load_model(self, name):
        """Load model from disk."""
        if name in self.models:
            return self.models[name]
        
        model_path = os.path.join(ML_MODEL_DIR, f"{name}_model.pkl")
        cols_path = os.path.join(ML_MODEL_DIR, f"{name}_columns.pkl")
        
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                self.models[name] = pickle.load(f)
            if os.path.exists(cols_path):
                with open(cols_path, 'rb') as f:
                    self.feature_columns[name] = pickle.load(f)
            return self.models[name]
        return None

    def get_all_results(self):
        """Return all training results."""
        return self.results


# Module-level singleton
ml_manager = MLModelManager()

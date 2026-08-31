# Application configuration
import os

# Database
DB_HOST = os.getenv("ECOM_DB_HOST", "localhost")
DB_PORT = int(os.getenv("ECOM_DB_PORT", "3307"))
DB_NAME = os.getenv("ECOM_DB_NAME", "ecom_analytics")
DB_USER = os.getenv("ECOM_DB_USER", "postgres")
DB_PASSWORD = os.getenv("ECOM_DB_PASSWORD", "root")

# Application
APP_NAME = "E-Commerce Customer Behavior Analytics"
APP_VERSION = "1.0.0"

# Simulator defaults
SIM_EVENTS_PER_BATCH = 50
SIM_BATCH_INTERVAL_SEC = 5
SIM_PURCHASE_PROB = 0.05
SIM_CART_ADD_PROB = 0.15
SIM_CART_ABANDON_PROB = 0.70
SIM_REVIEW_PROB = 0.30
SIM_RETURN_PROB = 0.08
SIM_MOBILE_RATIO = 0.55

# ML
ML_MODEL_DIR = os.path.join(os.path.dirname(__file__), "models", "saved")
ML_PURCHASE_MODEL = "purchase_prediction_rf.pkl"
ML_ABANDONMENT_MODEL = "cart_abandonment_rf.pkl"

# Problem Detection Thresholds
THRESHOLD_CONVERSION_DROP_PCT = 20       # Flag if conversion drops >20% vs baseline
THRESHOLD_ABANDONMENT_SPIKE_PCT = 15     # Flag if abandonment rises >15% vs baseline
THRESHOLD_REVIEW_DROP = 0.5              # Flag if avg rating drops >0.5
THRESHOLD_MIN_SAMPLE_SIZE = 30           # Minimum events to consider a signal reliable

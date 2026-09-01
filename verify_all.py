import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from src.ml.models import ml_manager
from src.analytics.sql_analytics import analytics
from src.engine.problem_detector import problem_detector

print("=== 1. TESTING ML MODELS TRAINING ===")
pur_res = ml_manager.train_purchase_prediction()
print("Purchase Model RF Accuracy:", pur_res.get('random_forest', {}).get('accuracy'))

ab_res = ml_manager.train_cart_abandonment()
print("Abandonment Model RF Accuracy:", ab_res.get('random_forest', {}).get('accuracy'))

sent_res = ml_manager.train_review_sentiment_model()
print("Review Sentiment Model Accuracy:", sent_res.get('primary_lr', {}).get('accuracy'))
print("Review Sentiment Model Weighted F1:", sent_res.get('primary_lr', {}).get('f1'))

print("\n=== 2. TESTING SQL REVIEW ANALYTICS ===")
rev_sum = analytics.get_review_sentiment_summary()
print("Review Summary:", rev_sum)

recent_revs = analytics.get_recent_reviews(limit=3)
print(f"Loaded {len(recent_revs)} recent reviews:")
for r in recent_revs:
    print(f"  - {r['rating']}★ [{r['sentiment_score']:+.2f}] {r['product_name'][:25]}: {r['review_text'][:60]}...")

stream = analytics.get_live_activity_stream(limit=5)
print(f"\nLive Activity Stream ({len(stream)} items):")
for s in stream:
    print(f"  [{s['activity_type']}] {s['action']} | {s['details']} | Actor: {s['actor']}")

print("\n=== 3. TESTING PROBLEM DETECTION ===")
problems = problem_detector.detect_all_problems()
print(f"Detected {len(problems)} business problems:")
for p in problems:
    print(f"  - [{p.severity.upper()}] (Score: {p.priority_score:.0f}/100) {p.title}")

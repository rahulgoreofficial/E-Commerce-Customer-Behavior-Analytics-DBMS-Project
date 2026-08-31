"""
Problem Detection Engine — Detects business problems, gathers evidence,
generates prioritized recommendations.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from src.database.connection import db
from src.config import (
    THRESHOLD_CONVERSION_DROP_PCT, THRESHOLD_ABANDONMENT_SPIKE_PCT,
    THRESHOLD_REVIEW_DROP, THRESHOLD_MIN_SAMPLE_SIZE,
)


@dataclass
class Evidence:
    """A single piece of supporting evidence."""
    description: str
    metric_name: str
    current_value: float
    baseline_value: float
    change_pct: float
    direction: str  # 'increased', 'decreased', 'stable'


@dataclass
class Recommendation:
    """A recommended action."""
    action: str
    rationale: str
    priority: str  # 'high', 'medium', 'low'
    category: str  # 'investigate', 'test', 'implement'


@dataclass
class DetectedProblem:
    """A detected business problem with full evidence chain."""
    problem_id: str
    problem_type: str
    title: str
    description: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    affected_dimensions: Dict = field(default_factory=dict)
    evidence: List[Evidence] = field(default_factory=list)
    metrics: Dict = field(default_factory=dict)
    priority_score: float = 0.0
    recommendations: List[Recommendation] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.now)
    confidence: float = 0.0


class ProblemDetector:
    """Detects business problems by comparing current metrics to baselines."""

    def detect_all_problems(self) -> List[DetectedProblem]:
        """Run all detection checks and return prioritized problems."""
        problems = []
        problems.extend(self._detect_conversion_drop())
        problems.extend(self._detect_cart_abandonment_spike())
        problems.extend(self._detect_product_issues())
        problems.extend(self._detect_churn_risk())
        problems.extend(self._detect_review_deterioration())

        # Calculate priority for all
        for p in problems:
            p.priority_score = self._calculate_priority(p)

        # Sort by priority
        problems.sort(key=lambda x: x.priority_score, reverse=True)
        return problems

    def _detect_conversion_drop(self) -> List[DetectedProblem]:
        """Detect significant conversion rate drops."""
        result = db.execute_query("""
            WITH current_wk AS (
                SELECT 
                    COUNT(DISTINCT CASE WHEN event_type = 'product_view' THEN session_id END) AS views,
                    COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) AS purchases
                FROM event WHERE event_timestamp >= NOW() - INTERVAL '7 days'
            ),
            baseline_wk AS (
                SELECT 
                    COUNT(DISTINCT CASE WHEN event_type = 'product_view' THEN session_id END) AS views,
                    COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) AS purchases
                FROM event 
                WHERE event_timestamp >= NOW() - INTERVAL '28 days'
                AND event_timestamp < NOW() - INTERVAL '7 days'
            )
            SELECT 
                c.views AS curr_views, c.purchases AS curr_purchases,
                CASE WHEN c.views > 0 THEN c.purchases::NUMERIC / c.views * 100 ELSE 0 END AS curr_rate,
                b.views AS base_views, b.purchases AS base_purchases,
                CASE WHEN b.views > 0 THEN (b.purchases::NUMERIC / b.views * 100) / 3.0 ELSE 0 END AS base_rate
            FROM current_wk c, baseline_wk b
        """)

        problems = []
        if result and result[0]['curr_views'] >= THRESHOLD_MIN_SAMPLE_SIZE:
            r = result[0]
            curr_rate = float(r['curr_rate'])
            base_rate = float(r['base_rate'])

            if base_rate > 0:
                drop_pct = ((base_rate - curr_rate) / base_rate) * 100
                if drop_pct > THRESHOLD_CONVERSION_DROP_PCT:
                    severity = 'critical' if drop_pct > 40 else ('high' if drop_pct > 25 else 'medium')

                    # Localize by device
                    device_data = db.execute_query("""
                        SELECT s.device,
                               COUNT(DISTINCT CASE WHEN e.event_type = 'purchase' THEN e.session_id END)::NUMERIC /
                               NULLIF(COUNT(DISTINCT CASE WHEN e.event_type = 'product_view' THEN e.session_id END), 0) * 100 AS conv_rate
                        FROM event e JOIN session s ON e.session_id = s.session_id
                        WHERE e.event_timestamp >= NOW() - INTERVAL '7 days'
                        GROUP BY s.device
                    """)

                    evidence = [
                        Evidence(
                            f"Conversion rate dropped from {base_rate:.1f}% to {curr_rate:.1f}%",
                            "conversion_rate", curr_rate, base_rate, -drop_pct, "decreased"
                        ),
                        Evidence(
                            f"Views this week: {r['curr_views']}",
                            "weekly_views", float(r['curr_views']), float(r['base_views']) / 3, 0, "stable"
                        ),
                    ]

                    affected = {}
                    for dd in (device_data or []):
                        affected[dd['device']] = float(dd['conv_rate'])

                    p = DetectedProblem(
                        problem_id=f"CONV_DROP_{datetime.now().strftime('%Y%m%d')}",
                        problem_type="conversion_drop",
                        title="Conversion Rate Decline Detected",
                        description=f"Overall conversion rate dropped {drop_pct:.1f}% compared to the 3-week baseline.",
                        severity=severity,
                        affected_dimensions={"device_conversion": affected},
                        evidence=evidence,
                        metrics={"current_rate": curr_rate, "baseline_rate": base_rate, "drop_pct": drop_pct},
                        confidence=min(0.9, float(r['curr_views']) / 500),
                        recommendations=[
                            Recommendation("Investigate checkout process for friction points",
                                           "Conversion drop with stable traffic suggests checkout/payment issues",
                                           "high", "investigate"),
                            Recommendation("Compare device-level conversion rates",
                                           "Mobile users often show different patterns",
                                           "medium", "investigate"),
                            Recommendation("Review recent product/pricing changes",
                                           "External factors may explain the drop",
                                           "medium", "investigate"),
                        ]
                    )
                    problems.append(p)

        return problems

    def _detect_cart_abandonment_spike(self) -> List[DetectedProblem]:
        """Detect unusual increases in cart abandonment."""
        result = db.execute_query("""
            WITH current_wk AS (
                SELECT COUNT(CASE WHEN cart_status = 'abandoned' THEN 1 END) AS abandoned,
                       COUNT(*) AS total
                FROM cart WHERE created_at >= NOW() - INTERVAL '7 days'
            ),
            baseline AS (
                SELECT COUNT(CASE WHEN cart_status = 'abandoned' THEN 1 END) AS abandoned,
                       COUNT(*) AS total
                FROM cart WHERE created_at >= NOW() - INTERVAL '28 days'
                AND created_at < NOW() - INTERVAL '7 days'
            )
            SELECT 
                c.abandoned AS curr_abandoned, c.total AS curr_total,
                CASE WHEN c.total > 0 THEN c.abandoned::NUMERIC / c.total * 100 ELSE 0 END AS curr_rate,
                CASE WHEN b.total > 0 THEN (b.abandoned::NUMERIC / b.total * 100) ELSE 0 END AS base_rate
            FROM current_wk c, baseline b
        """)

        problems = []
        if result and result[0]['curr_total'] >= 10:
            r = result[0]
            curr_rate = float(r['curr_rate'])
            base_rate = float(r['base_rate'])

            if base_rate > 0:
                spike_pct = ((curr_rate - base_rate) / base_rate) * 100
                if spike_pct > THRESHOLD_ABANDONMENT_SPIKE_PCT:
                    # Get abandoned cart value
                    value_data = db.execute_query("""
                        SELECT COALESCE(SUM(total_value), 0) AS abandoned_value
                        FROM cart WHERE cart_status = 'abandoned'
                        AND created_at >= NOW() - INTERVAL '7 days'
                    """)
                    abandoned_value = float(value_data[0]['abandoned_value']) if value_data else 0

                    p = DetectedProblem(
                        problem_id=f"CART_ABANDON_{datetime.now().strftime('%Y%m%d')}",
                        problem_type="cart_abandonment_spike",
                        title="Cart Abandonment Rate Increased",
                        description=f"Cart abandonment rose from {base_rate:.1f}% to {curr_rate:.1f}% ({spike_pct:.0f}% increase).",
                        severity='high' if spike_pct > 30 else 'medium',
                        evidence=[
                            Evidence(f"Abandonment rate: {curr_rate:.1f}% (baseline: {base_rate:.1f}%)",
                                     "abandonment_rate", curr_rate, base_rate, spike_pct, "increased"),
                            Evidence(f"Abandoned cart value this week: ₹{abandoned_value:,.0f}",
                                     "abandoned_value", abandoned_value, 0, 0, "increased"),
                        ],
                        metrics={"current_rate": curr_rate, "baseline_rate": base_rate,
                                 "abandoned_value": abandoned_value},
                        confidence=0.7,
                        recommendations=[
                            Recommendation("Investigate checkout flow for new friction points",
                                           "Increased abandonment often correlates with checkout changes",
                                           "high", "investigate"),
                            Recommendation("Check if shipping costs or delivery times changed",
                                           "Unexpected costs at checkout are a top abandonment cause",
                                           "high", "investigate"),
                            Recommendation("Consider targeted recovery emails for abandoned carts",
                                           "Cart recovery campaigns typically recover 5-15% of carts",
                                           "medium", "test"),
                        ]
                    )
                    problems.append(p)

        return problems

    def _detect_product_issues(self) -> List[DetectedProblem]:
        """Detect products with high views but very low conversion."""
        result = db.execute_query("""
            SELECT product_id, product_name, category_name, total_views, 
                   total_cart_adds, total_purchases, view_to_cart_rate, avg_rating, total_returns
            FROM mv_product_performance
            WHERE total_views >= 20 AND view_to_cart_rate < 3.0
            ORDER BY total_views DESC
            LIMIT 10
        """)

        problems = []
        if result and len(result) >= 3:
            product_names = [r['product_name'][:40] for r in result[:5]]
            p = DetectedProblem(
                problem_id=f"PROD_ISSUE_{datetime.now().strftime('%Y%m%d')}",
                problem_type="product_performance",
                title=f"{len(result)} Products With High Views But Low Conversion",
                description=f"Products are getting traffic but not converting. Top affected: {', '.join(product_names[:3])}",
                severity='medium',
                evidence=[
                    Evidence(f"{len(result)} products with >20 views but <3% cart-add rate",
                             "low_conversion_products", len(result), 0, 0, "stable"),
                ],
                metrics={"affected_products": len(result)},
                confidence=0.6,
                recommendations=[
                    Recommendation("Review pricing competitiveness for these products",
                                   "High views + low conversion often indicates price sensitivity",
                                   "medium", "investigate"),
                    Recommendation("Check product listing quality (images, descriptions)",
                                   "Poor listings drive views without conversions",
                                   "medium", "investigate"),
                ]
            )
            problems.append(p)

        return problems

    def _detect_churn_risk(self) -> List[DetectedProblem]:
        """Detect at-risk and churned customer segments."""
        result = db.execute_query("""
            SELECT segment, COUNT(*) AS count, 
                   ROUND(AVG(lifetime_value)::NUMERIC, 2) AS avg_ltv
            FROM customer
            WHERE segment IN ('At Risk', 'Churned')
            GROUP BY segment
        """)

        problems = []
        total_atrisk = sum(int(r['count']) for r in (result or []) if r['segment'] == 'At Risk')
        total_churned = sum(int(r['count']) for r in (result or []) if r['segment'] == 'Churned')

        if total_atrisk + total_churned > 20:
            ltv_at_risk = sum(float(r['avg_ltv']) * int(r['count']) for r in (result or []) if r['segment'] == 'At Risk')
            p = DetectedProblem(
                problem_id=f"CHURN_RISK_{datetime.now().strftime('%Y%m%d')}",
                problem_type="churn_risk",
                title=f"Customer Churn Risk: {total_atrisk} At-Risk, {total_churned} Churned",
                description=f"{total_atrisk} customers show declining activity and {total_churned} appear churned.",
                severity='high' if total_atrisk > 50 else 'medium',
                evidence=[
                    Evidence(f"{total_atrisk} customers classified as At Risk",
                             "at_risk_customers", total_atrisk, 0, 0, "increased"),
                    Evidence(f"Estimated at-risk LTV: ₹{ltv_at_risk:,.0f}",
                             "at_risk_ltv", ltv_at_risk, 0, 0, "stable"),
                ],
                metrics={"at_risk": total_atrisk, "churned": total_churned, "at_risk_ltv": ltv_at_risk},
                confidence=0.65,
                recommendations=[
                    Recommendation("Launch re-engagement campaign for At-Risk customers",
                                   "Targeted outreach before churn is more cost-effective than acquisition",
                                   "high", "implement"),
                    Recommendation("Analyze common traits of churning customers",
                                   "Understanding churn drivers helps prevention",
                                   "medium", "investigate"),
                ]
            )
            problems.append(p)

        return problems

    def _detect_review_deterioration(self) -> List[DetectedProblem]:
        """Detect products or categories with declining review scores."""
        result = db.execute_query("""
            WITH recent AS (
                SELECT product_id, AVG(rating) AS recent_avg, COUNT(*) AS recent_count
                FROM review WHERE review_date >= NOW() - INTERVAL '30 days'
                GROUP BY product_id HAVING COUNT(*) >= 3
            ),
            historical AS (
                SELECT product_id, AVG(rating) AS hist_avg
                FROM review WHERE review_date < NOW() - INTERVAL '30 days'
                GROUP BY product_id HAVING COUNT(*) >= 3
            )
            SELECT r.product_id, p.product_name, r.recent_avg, h.hist_avg,
                   r.recent_avg - h.hist_avg AS rating_change, r.recent_count
            FROM recent r
            JOIN historical h ON r.product_id = h.product_id
            JOIN product p ON r.product_id = p.product_id
            WHERE h.hist_avg - r.recent_avg > %s
            ORDER BY rating_change ASC
        """, (THRESHOLD_REVIEW_DROP,))

        problems = []
        if result and len(result) > 0:
            p = DetectedProblem(
                problem_id=f"REVIEW_DROP_{datetime.now().strftime('%Y%m%d')}",
                problem_type="review_deterioration",
                title=f"{len(result)} Products With Declining Reviews",
                description=f"Average ratings dropped by more than {THRESHOLD_REVIEW_DROP} stars for {len(result)} products in the last 30 days.",
                severity='medium',
                evidence=[
                    Evidence(f"{len(result)} products with significant rating decline",
                             "declining_products", len(result), 0, 0, "decreased"),
                ],
                metrics={"affected_products": len(result)},
                confidence=0.55,
                recommendations=[
                    Recommendation("Review recent quality/shipping complaints for affected products",
                                   "Rating drops often signal quality or fulfillment issues",
                                   "high", "investigate"),
                ]
            )
            problems.append(p)

        return problems

    def _calculate_priority(self, problem: DetectedProblem) -> float:
        """Calculate priority score 0-100."""
        score = 0.0
        severity_map = {'critical': 30, 'high': 22, 'medium': 14, 'low': 7}
        score += severity_map.get(problem.severity, 7)

        # Evidence strength
        score += min(25, len(problem.evidence) * 8)

        # Confidence
        score += problem.confidence * 20

        # Revenue exposure
        if problem.metrics.get('abandoned_value', 0) > 10000:
            score += 15
        elif problem.metrics.get('at_risk_ltv', 0) > 50000:
            score += 15

        return min(100, score)


class RecommendationEngine:
    """Generates and manages recommendations linked to detected problems."""

    def get_recommendations_for_problem(self, problem: DetectedProblem) -> List[Recommendation]:
        """Return the recommendations already attached to the problem + any additional ones."""
        return problem.recommendations

    def estimate_impact(self, problem: DetectedProblem, intervention: str) -> Dict:
        """Estimate impact of an intervention under stated assumptions."""
        if problem.problem_type == 'cart_abandonment_spike':
            abandoned_value = problem.metrics.get('abandoned_value', 0)
            return {
                'scenarios': {
                    'conservative': {
                        'assumption': '10% of abandoned carts recovered',
                        'estimated_revenue': abandoned_value * 0.10,
                    },
                    'moderate': {
                        'assumption': '20% of abandoned carts recovered',
                        'estimated_revenue': abandoned_value * 0.20,
                    },
                    'optimistic': {
                        'assumption': '30% of abandoned carts recovered',
                        'estimated_revenue': abandoned_value * 0.30,
                    },
                },
                'disclaimer': 'Estimates based on stated assumptions. Actual results require A/B testing.'
            }
        elif problem.problem_type == 'churn_risk':
            at_risk_ltv = problem.metrics.get('at_risk_ltv', 0)
            return {
                'scenarios': {
                    'conservative': {
                        'assumption': '15% of at-risk customers retained',
                        'estimated_saved_ltv': at_risk_ltv * 0.15,
                    },
                    'moderate': {
                        'assumption': '25% of at-risk customers retained',
                        'estimated_saved_ltv': at_risk_ltv * 0.25,
                    },
                },
                'disclaimer': 'Retention estimates. Verify with actual campaign results.'
            }
        return {'message': 'No impact estimation available for this problem type.'}


# Module-level singletons
problem_detector = ProblemDetector()
recommendation_engine = RecommendationEngine()

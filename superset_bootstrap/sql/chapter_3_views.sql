-- Views for Chapter 3: Sustainable Growth
CREATE OR REPLACE VIEW ml.vw_ch3_customer_actions AS
SELECT 
    customer_key,
    segment,
    monetary,
    recency,
    frequency,
    churn_prob,
    churn_risk_band,
    CASE 
        WHEN is_vip = 1 AND churn_prob > 0.6 THEN 'Chăm sóc đặc biệt 1-1, tặng coupon tri ân đặc biệt, gọi điện trực tiếp.'
        WHEN is_vip = 1 THEN 'Gửi email ưu đãi VIP, khảo sát ý kiến, tặng loyalty points.'
        WHEN churn_prob > 0.6 THEN 'Win-back campaign, giảm giá sâu để kích hoạt lại.'
        ELSE 'Loyalty program, gửi newsletter định kỳ.'
    END AS recommended_action
FROM ml.customer_churn_predictions
WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM ml.customer_churn_predictions)
ORDER BY churn_prob DESC;

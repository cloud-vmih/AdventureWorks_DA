-- Views for Chapter 5: Macro Economic Behavior
CREATE OR REPLACE VIEW ml.vw_ch5_category_retention AS
WITH totals AS (
    SELECT 
        prev_category AS category_name,
        SUM(transition_count) AS total_transitions
    FROM ml.macro_category_transition
    GROUP BY prev_category
),
retained AS (
    SELECT 
        prev_category AS category_name,
        SUM(transition_count) AS retained_transitions
    FROM ml.macro_category_transition
    WHERE prev_category = next_category
    GROUP BY prev_category
)
SELECT 
    t.category_name,
    COALESCE(r.retained_transitions, 0) AS retained_transitions,
    t.total_transitions,
    COALESCE(r.retained_transitions, 0) / NULLIF(t.total_transitions, 0)::double precision AS retention_rate
FROM totals t
LEFT JOIN retained r ON t.category_name = r.category_name;

import os
import json
import pandas as pd
from superset_bootstrap.bootstrap_common import (
    SupersetClient,
    get_database_id,
    get_or_create_dataset,
    get_or_create_dashboard,
    get_or_create_chart,
    remove_stale_dashboard_charts,
    simple_metric,
    sql_metric,
    dashboard_layout,
    build_native_filter,
    BASE_URL
)
from src.common.database import get_dwh_engine

DASHBOARD_TITLE = "Chương 3 - Tăng trưởng có bền vững không?"
DASHBOARD_SLUG = "adventureworks-chapter-3-sustainable-growth"

def load_story_metrics() -> dict[str, object]:
    query = """
        WITH cohort_stats AS (
            SELECT AVG(retention_pct) AS avg_retention
            FROM ml.customer_cohort_retention
        ),
        latest_preds AS (
            SELECT 
                COUNT(DISTINCT customer_key) AS total_customers,
                COUNT(*) FILTER (WHERE is_vip = 1) AS vip_customers,
                AVG(churn_prob) AS avg_churn_prob,
                COUNT(*) FILTER (WHERE churn_risk_band = 'High (>60%%)') AS high_risk_customers
            FROM ml.customer_churn_predictions
            WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM ml.customer_churn_predictions)
        ),
        model_metrics AS (
            SELECT 
                MAX(metric_value) FILTER (WHERE metric_name = 'AUC-PR') AS model_pr_auc
            FROM ml.churn_model_metrics
        ),
        revenue_split AS (
            SELECT 
                SUM(revenue) FILTER (WHERE customer_type = 'Returning') / NULLIF(SUM(revenue), 0) AS returning_share
            FROM ml.customer_new_vs_returning
            WHERE month_key = (SELECT MAX(month_key) FROM ml.customer_new_vs_returning)
        )
        SELECT 
            c.avg_retention,
            l.total_customers,
            l.vip_customers,
            l.avg_churn_prob,
            l.high_risk_customers,
            m.model_pr_auc,
            r.returning_share
        FROM cohort_stats c, latest_preds l, model_metrics m, revenue_split r
    """
    engine = get_dwh_engine()
    with engine.connect() as conn:
        df = pd.read_sql_query(query, conn)
        return df.iloc[0].to_dict()

def story_titles(metrics: dict[str, object]) -> list[str]:
    def pct(val):
        if pd.isna(val) or val is None:
            return "N/A"
        return f"{val*100:.1f}%".replace('.', ',')
        
    return [
        f"Doanh thu lặp lại | Returning Revenue Share đạt {pct(metrics['returning_share'])}",
        f"Khách hàng VIP | Đạt {int(metrics['vip_customers']):,} khách hàng chủ lực".replace(',', '.'),
        f"Tỷ lệ Churn dự báo | Churn Rate trung bình dự báo là {pct(metrics['avg_churn_prob'])}",
        f"Đo lường | Mô hình VIP Churn đạt PR-AUC {metrics['model_pr_auc']:.4f}".replace('.', ','),
        "Phát triển | Doanh số từ Khách hàng Mới vs Khách hàng Quay lại theo tháng",
        "Cơ cấu | Tỷ trọng Doanh số Khách hàng Mới vs Quay lại",
        "Phân khúc | Số lượng khách hàng theo Phân khúc RFM",
        "Tỷ trọng | Đóng góp doanh thu của các Phân khúc",
        "Mật độ | Phân bổ R Score × F Score (Avg Monetary)",
        "Hồ sơ | Chi tiết chỉ số đặc trưng các Phân khúc RFM",
        "Giữ chân | Ma trận Cohort Retention Heatmap",
        "Độ dốc | Đường cong giữ chân khách hàng (Retention Curve) trung bình",
        "Hiệu năng | So sánh các mô hình dự báo Churn",
        "Giải thích | Tác động SHAP Mean Absolute Importance lên Churn",
        "Rủi ro VIP | Doanh số tích lũy vs Xác suất Churn của VIP",
        "Danh sách | Top khách hàng có xác suất Churn cao nhất",
        "Hành động | Danh sách hành động đề xuất giảm thiểu rủi ro Churn"
    ]

def main():
    client = SupersetClient()
    client.login()
    db_id = get_database_id(client)
    
    # Get or create datasets
    new_returning_dataset_id = get_or_create_dataset(client, db_id, "ml", "customer_new_vs_returning")
    cohort_dataset_id = get_or_create_dataset(client, db_id, "ml", "customer_cohort_retention")
    predictions_dataset_id = get_or_create_dataset(client, db_id, "ml", "customer_churn_predictions")
    profile_dataset_id = get_or_create_dataset(client, db_id, "ml", "customer_segment_profile")
    metrics_dataset_id = get_or_create_dataset(client, db_id, "ml", "churn_model_metrics")
    importance_dataset_id = get_or_create_dataset(client, db_id, "ml", "churn_feature_importance")
    actions_dataset_id = get_or_create_dataset(client, db_id, "ml", "vw_ch3_customer_actions")
    
    dashboard_id = get_or_create_dashboard(client, DASHBOARD_TITLE, DASHBOARD_SLUG)
    metrics = load_story_metrics()
    titles = story_titles(metrics)
    
    chart_specs = [
        # Row 1: KPI
        (
            new_returning_dataset_id, titles[0], (), "big_number_total",
            {
                "datasource": f"{new_returning_dataset_id}__table", "viz_type": "big_number_total",
                "metric": sql_metric("SUM(revenue) FILTER (WHERE customer_type = 'Returning')/NULLIF(SUM(revenue),0)", "Tỷ trọng doanh thu lặp lại", "metric_ret_share"),
                "time_range": "No filter", "y_axis_format": ".2%"
            }
        ),
        (
            predictions_dataset_id, titles[1], (), "big_number_total",
            {
                "datasource": f"{predictions_dataset_id}__table", "viz_type": "big_number_total",
                "metric": sql_metric("COUNT(DISTINCT customer_key) FILTER (WHERE is_vip = 1)", "Số khách VIP", "metric_vip_count"),
                "time_range": "No filter", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            predictions_dataset_id, titles[2], (), "big_number_total",
            {
                "datasource": f"{predictions_dataset_id}__table", "viz_type": "big_number_total",
                "metric": simple_metric("churn_prob", "Tỷ lệ Churn trung bình dự báo", "AVG"),
                "time_range": "No filter", "y_axis_format": ".2%"
            }
        ),
        (
            metrics_dataset_id, titles[3], (), "big_number_total",
            {
                "datasource": f"{metrics_dataset_id}__table", "viz_type": "big_number_total",
                "metric": simple_metric("metric_value", "Chỉ số PR-AUC", "MAX"),
                "time_range": "No filter", "y_axis_format": ".4f",
                "adhoc_filters": [{"clause": "WHERE", "expressionType": "SIMPLE", "operator": "==", "subject": "metric_name", "comparator": "AUC-PR"}]
            }
        ),
        # Row 2: New vs Returning
        (
            new_returning_dataset_id, titles[4], (), "echarts_timeseries_bar",
            {
                "datasource": f"{new_returning_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "month_key", "metrics": [simple_metric("revenue", "Doanh thu")],
                "groupby": ["customer_type"], "time_range": "No filter", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            new_returning_dataset_id, titles[5], (), "echarts_timeseries_line",
            {
                "datasource": f"{new_returning_dataset_id}__table", "viz_type": "echarts_timeseries_line",
                "x_axis": "month_key", "metrics": [simple_metric("revenue", "Doanh thu")],
                "groupby": ["customer_type"], "time_range": "No filter", "series_type": "line", "y_axis_format": "SMART_NUMBER"
            }
        ),
        # Row 3: RFM
        (
            profile_dataset_id, titles[6], (), "echarts_timeseries_bar",
            {
                "datasource": f"{profile_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "segment", "metrics": [simple_metric("customers", "Khách hàng")],
                "groupby": [], "time_range": "No filter", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            profile_dataset_id, titles[7], (), "pie",
            {
                "datasource": f"{profile_dataset_id}__table", "viz_type": "pie",
                "groupby": ["segment"], "metric": simple_metric("total_revenue", "Doanh thu"), "time_range": "No filter"
            }
        ),
        (
            predictions_dataset_id, titles[8], (), "pivot_table_v2",
            {
                "datasource": f"{predictions_dataset_id}__table", "viz_type": "pivot_table_v2",
                "groupbyRows": ["r_score"], "groupbyColumns": ["f_score"],
                "metrics": [simple_metric("monetary", "Doanh thu trung bình", "AVG")], "time_range": "No filter"
            }
        ),
        (
            profile_dataset_id, titles[9], (), "table",
            {
                "datasource": f"{profile_dataset_id}__table", "viz_type": "table",
                "query_mode": "raw", "all_columns": ["segment", "customers", "avg_recency", "avg_frequency", "avg_monetary", "churn_rate"],
                "groupby": [], "metrics": [], "time_range": "No filter", "row_limit": 50
            }
        ),
        # Row 4: Cohort
        (
            cohort_dataset_id, titles[10], (), "pivot_table_v2",
            {
                "datasource": f"{cohort_dataset_id}__table", "viz_type": "pivot_table_v2",
                "groupbyRows": ["cohort_month"], "groupbyColumns": ["period_number"],
                "metrics": [simple_metric("retention_pct", "Tỷ lệ giữ chân", "AVG")], "time_range": "No filter"
            }
        ),
        (
            cohort_dataset_id, titles[11], (), "echarts_timeseries_line",
            {
                "datasource": f"{cohort_dataset_id}__table", "viz_type": "echarts_timeseries_line",
                "x_axis": "period_number", "metrics": [simple_metric("retention_pct", "Tỷ lệ giữ chân", "AVG")],
                "groupby": [], "time_range": "No filter", "series_type": "line", "y_axis_format": ".2%"
            }
        ),
        # Row 5: Churn Model Explanation
        (
            metrics_dataset_id, titles[12], (), "echarts_timeseries_bar",
            {
                "datasource": f"{metrics_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "metric_name", "metrics": [simple_metric("metric_value", "Giá trị")],
                "groupby": ["model_name"], "time_range": "No filter", "y_axis_format": ".4f"
            }
        ),
        (
            importance_dataset_id, titles[13], (), "echarts_timeseries_bar",
            {
                "datasource": f"{importance_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "feature", "metrics": [simple_metric("importance", "Độ quan trọng SHAP")],
                "groupby": [], "time_range": "No filter", "y_axis_format": ".4f", "orientation": "horizontal"
            }
        ),
        # Row 6: VIP Churn Action List
        (
            actions_dataset_id, titles[14], (), "bubble_v2",
            {
                "datasource": f"{actions_dataset_id}__table", "viz_type": "bubble_v2",
                "entity": "customer_key", "series": "churn_risk_band",
                "x": simple_metric("monetary", "Doanh số tích lũy"),
                "y": simple_metric("churn_prob", "Xác suất Churn"),
                "size": simple_metric("frequency", "Tần suất mua"),
                "time_range": "No filter", "xAxisFormat": "SMART_NUMBER", "yAxisFormat": ".2%"
            }
        ),
        (
            actions_dataset_id, titles[15], (), "table",
            {
                "datasource": f"{actions_dataset_id}__table", "viz_type": "table",
                "query_mode": "raw", "all_columns": ["customer_key", "segment", "monetary", "churn_prob", "churn_risk_band"],
                "groupby": [], "metrics": [], "time_range": "No filter",
                "order_by_cols": ['["churn_prob", false]'], "row_limit": 50, "page_length": 10
            }
        ),
        (
            actions_dataset_id, titles[16], (), "table",
            {
                "datasource": f"{actions_dataset_id}__table", "viz_type": "table",
                "query_mode": "raw", "all_columns": ["customer_key", "segment", "churn_prob", "recommended_action"],
                "groupby": [], "metrics": [], "time_range": "No filter",
                "order_by_cols": ['["churn_prob", false]'], "row_limit": 50, "page_length": 10
            }
        )
    ]
    
    charts = []
    for dataset_id, slice_name, legacy, viz_type, params in chart_specs:
        chart_id = get_or_create_chart(client, dashboard_id, dataset_id, slice_name, legacy, viz_type, params)
        charts.append((chart_id, slice_name))
        
    remove_stale_dashboard_charts(client, dashboard_id, {c[0] for c in charts})
    
    # Layout sections
    sections = [
        [(titles[0], 3, 18), (titles[1], 3, 18), (titles[2], 3, 18), (titles[3], 3, 18)],
        [(titles[4], 6, 30), (titles[5], 6, 30)],
        [(titles[6], 3, 34), (titles[7], 3, 34), (titles[8], 3, 34), (titles[9], 3, 34)],
        [(titles[10], 6, 38), (titles[11], 6, 38)],
        [(titles[12], 6, 30), (titles[13], 6, 30)],
        [(titles[14], 4, 34), (titles[15], 4, 34), (titles[16], 4, 34)]
    ]
    
    # Native Filters
    native_filters = [
        build_native_filter("NATIVE_FILTER-segment3", "Phân khúc (Segment)", "segment", profile_dataset_id),
        build_native_filter("NATIVE_FILTER-risk3", "Nhóm rủi ro Churn (Risk Band)", "churn_risk_band", predictions_dataset_id)
    ]
    
    client.request(
        "PUT", f"/api/v1/dashboard/{dashboard_id}",
        json={
            "dashboard_title": DASHBOARD_TITLE,
            "slug": DASHBOARD_SLUG,
            "published": True,
            "position_json": dashboard_layout(charts, sections),
            "json_metadata": json.dumps({
                "timed_refresh_immune_slices": [],
                "expanded_slices": {},
                "refresh_frequency": 0,
                "color_scheme": "supersetColors",
                "label_colors": {},
                "native_filter_configuration": native_filters
            })
        }
    )
    print(f"Dashboard 3 ready: {BASE_URL}/superset/dashboard/{DASHBOARD_SLUG}/")

if __name__ == "__main__":
    main()

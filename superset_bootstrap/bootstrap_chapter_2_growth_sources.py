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

DASHBOARD_TITLE = "Chương 2 - Tăng trưởng đến từ đâu?"
DASHBOARD_SLUG = "adventureworks-chapter-2-growth-sources"

def load_story_metrics() -> dict[str, object]:
    query = """
        WITH stats AS (
            SELECT 
                COUNT(DISTINCT territory_id) AS num_territories,
                COUNT(*) FILTER (WHERE is_anomaly = TRUE) AS anomaly_count
            FROM ml.vw_territory_analysis_dashboard
        ),
        top_rev AS (
            SELECT territory_name, AVG(revenue) AS avg_rev
            FROM ml.vw_territory_analysis_dashboard
            GROUP BY territory_name
            ORDER BY avg_rev DESC
            LIMIT 1
        ),
        top_growth AS (
            SELECT territory_name, AVG(log_growth) AS avg_growth
            FROM ml.vw_territory_analysis_dashboard
            GROUP BY territory_name
            ORDER BY avg_growth DESC
            LIMIT 1
        ),
        min_margin AS (
            SELECT territory_name, AVG(profit)/NULLIF(AVG(revenue),0) AS avg_margin
            FROM ml.vw_territory_analysis_dashboard
            GROUP BY territory_name
            ORDER BY avg_margin ASC
            LIMIT 1
        )
        SELECT 
            s.*,
            tr.territory_name AS top_rev_territory,
            tg.territory_name AS top_growth_territory,
            mm.territory_name AS min_margin_territory
        FROM stats s, top_rev tr, top_growth tg, min_margin mm
    """
    engine = get_dwh_engine()
    with engine.connect() as conn:
        df = pd.read_sql_query(query, conn)
        return df.iloc[0].to_dict()

def story_titles(metrics: dict[str, object]) -> list[str]:
    return [
        "Quy mô | Tổng doanh thu B2C theo các Lãnh thổ",
        "Tăng trưởng | Tốc độ tăng trưởng trung vị toàn khu vực",
        "Giữ chân | Tỷ lệ giữ chân khách hàng (Retention Rate) trung bình",
        f"Biến động | Phát hiện {int(metrics['anomaly_count'])} điểm sụt giảm bất thường",
        "Lãnh thổ | Xu hướng doanh số hàng tháng của các Lãnh thổ",
        f"Tập trung | {metrics['top_rev_territory']} dẫn đầu về doanh thu bình quân",
        "Phân khúc | Bản đồ phân cụm thị trường (PCA Cluster Map)",
        "Đặc trưng | Hồ sơ cụm thị trường (Cluster Profile)",
        "Hành động | Khuyến nghị chiến lược theo cụm lãnh thổ",
        "Phát hiện | Doanh thu thực tế vs Doanh thu kỳ vọng STL",
        "Bất thường | Số lần sụt giảm bất thường theo khu vực",
        "Chi tiết | Danh sách các tháng có biến động bất thường",
        "Dự báo | Doanh thu thực tế vs Doanh thu dự báo",
        "Sai số | Sai số dự báo trung bình (%) theo Lãnh thổ",
        "Cảnh báo | Danh sách Lãnh thổ dưới dự báo trên 20%"
    ]

def main():
    client = SupersetClient()
    client.login()
    db_id = get_database_id(client)
    
    # Get or create datasets
    dashboard_dataset_id = get_or_create_dataset(client, db_id, "ml", "vw_territory_analysis_dashboard")
    cluster_dataset_id = get_or_create_dataset(client, db_id, "ml", "territory_cluster_result")
    strategy_dataset_id = get_or_create_dataset(client, db_id, "ml", "vw_ch2_territory_strategy")
    
    dashboard_id = get_or_create_dashboard(client, DASHBOARD_TITLE, DASHBOARD_SLUG)
    metrics = load_story_metrics()
    titles = story_titles(metrics)
    
    chart_specs = [
        # Row 1: KPI
        (
            dashboard_dataset_id, titles[0], (), "big_number_total",
            {
                "datasource": f"{dashboard_dataset_id}__table", "viz_type": "big_number_total",
                "metric": simple_metric("revenue", "Doanh thu B2C"), "time_range": "No filter", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            dashboard_dataset_id, titles[1], (), "big_number_total",
            {
                "datasource": f"{dashboard_dataset_id}__table", "viz_type": "big_number_total",
                "metric": simple_metric("log_growth", "Tốc độ tăng trưởng Log MoM", "AVG"), "time_range": "No filter", "y_axis_format": ".2%"
            }
        ),
        (
            dashboard_dataset_id, titles[2], (), "big_number_total",
            {
                "datasource": f"{dashboard_dataset_id}__table", "viz_type": "big_number_total",
                "metric": simple_metric("retention_rate", "Tỷ lệ giữ chân khách hàng", "AVG"), "time_range": "No filter", "y_axis_format": ".2%"
            }
        ),
        (
            dashboard_dataset_id, titles[3], (), "big_number_total",
            {
                "datasource": f"{dashboard_dataset_id}__table", "viz_type": "big_number_total",
                "metric": sql_metric("COUNT(*) FILTER (WHERE is_anomaly = TRUE)", "Số lần sụt giảm bất thường", "metric_anomaly_count"),
                "time_range": "No filter", "y_axis_format": "SMART_NUMBER"
            }
        ),
        # Row 2: Scale vs Growth
        (
            dashboard_dataset_id, titles[4], (), "echarts_timeseries_line",
            {
                "datasource": f"{dashboard_dataset_id}__table", "viz_type": "echarts_timeseries_line",
                "x_axis": "month_key", "metrics": [simple_metric("revenue", "Doanh thu")],
                "groupby": ["territory_name"], "time_range": "No filter", "series_type": "line", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            cluster_dataset_id, titles[5], (), "bubble_v2",
            {
                "datasource": f"{cluster_dataset_id}__table", "viz_type": "bubble_v2",
                "entity": "territory_name", "series": "cluster_name",
                "x": simple_metric("median_log_growth", "Tốc độ tăng trưởng Log MoM"),
                "y": simple_metric("avg_revenue", "Doanh thu trung bình tháng"),
                "size": simple_metric("avg_active_customers", "Lượng khách hoạt động trung bình"),
                "time_range": "No filter", "xAxisFormat": ".2%", "yAxisFormat": "SMART_NUMBER"
            }
        ),
        # Row 3: Cluster PCA & Action
        (
            cluster_dataset_id, titles[6], (), "bubble_v2",
            {
                "datasource": f"{cluster_dataset_id}__table", "viz_type": "bubble_v2",
                "entity": "territory_name", "series": "cluster_name",
                "x": simple_metric("pca_1", "PCA Component 1"),
                "y": simple_metric("pca_2", "PCA Component 2"),
                "size": simple_metric("avg_revenue", "Doanh thu"),
                "time_range": "No filter", "xAxisFormat": "SMART_NUMBER", "yAxisFormat": "SMART_NUMBER"
            }
        ),
        (
            cluster_dataset_id, titles[7], (), "echarts_timeseries_bar",
            {
                "datasource": f"{cluster_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "cluster_name", "metrics": [simple_metric("avg_revenue", "Doanh thu"), simple_metric("avg_active_customers", "Khách hàng active")],
                "groupby": [], "time_range": "No filter", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            strategy_dataset_id, titles[8], (), "table",
            {
                "datasource": f"{strategy_dataset_id}__table", "viz_type": "table",
                "query_mode": "raw", "all_columns": ["territory_name", "cluster_name", "mean_profit_margin", "mean_retention_rate", "recommended_action"],
                "groupby": [], "metrics": [], "time_range": "No filter", "row_limit": 50
            }
        ),
        # Row 4: Anomalies (STL)
        (
            dashboard_dataset_id, titles[9], (), "echarts_timeseries_line",
            {
                "datasource": f"{dashboard_dataset_id}__table", "viz_type": "echarts_timeseries_line",
                "x_axis": "month_key", "metrics": [simple_metric("revenue", "Doanh thu thực tế"), simple_metric("expected_revenue_stl", "Doanh thu kỳ vọng STL")],
                "groupby": [], "time_range": "No filter", "series_type": "line", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            dashboard_dataset_id, titles[10], (), "echarts_timeseries_bar",
            {
                "datasource": f"{dashboard_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "territory_name", "metrics": [sql_metric("COUNT(*) FILTER (WHERE is_anomaly = TRUE)", "Số lần bất thường", "metric_anomaly_count")],
                "groupby": [], "time_range": "No filter", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            dashboard_dataset_id, titles[11], (), "table",
            {
                "datasource": f"{dashboard_dataset_id}__table", "viz_type": "table",
                "query_mode": "raw", "all_columns": ["month_key", "territory_name", "revenue", "expected_revenue_stl", "anomaly_type"],
                "groupby": [], "metrics": [], "time_range": "No filter",
                "adhoc_filters": [{
                    "clause": "WHERE", "expressionType": "SIMPLE", "operator": "==", "subject": "is_anomaly", "comparator": True
                }],
                "row_limit": 50
            }
        ),
        # Row 5: Forecast
        (
            dashboard_dataset_id, titles[12], (), "echarts_timeseries_line",
            {
                "datasource": f"{dashboard_dataset_id}__table", "viz_type": "echarts_timeseries_line",
                "x_axis": "month_key", "metrics": [simple_metric("revenue", "Doanh thu thực tế"), simple_metric("predicted_revenue", "Doanh thu dự báo")],
                "groupby": [], "time_range": "No filter", "series_type": "line", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            dashboard_dataset_id, titles[13], (), "echarts_timeseries_bar",
            {
                "datasource": f"{dashboard_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "territory_name", "metrics": [simple_metric("forecast_error_pct", "Sai số dự báo (%)", "AVG")],
                "groupby": [], "time_range": "No filter", "y_axis_format": ".2%"
            }
        ),
        (
            dashboard_dataset_id, titles[14], (), "table",
            {
                "datasource": f"{dashboard_dataset_id}__table", "viz_type": "table",
                "query_mode": "raw", "all_columns": ["territory_name", "month_key", "revenue", "predicted_revenue", "forecast_error_pct"],
                "groupby": [], "metrics": [], "time_range": "No filter",
                "adhoc_filters": [{
                    "clause": "WHERE", "expressionType": "SIMPLE", "operator": "<", "subject": "forecast_error_pct", "comparator": -0.20
                }],
                "row_limit": 50
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
        [(titles[6], 4, 34), (titles[7], 4, 34), (titles[8], 4, 34)],
        [(titles[9], 4, 34), (titles[10], 4, 34), (titles[11], 4, 34)],
        [(titles[12], 4, 34), (titles[13], 4, 34), (titles[14], 4, 34)]
    ]
    
    # Native Filters
    native_filters = [
        build_native_filter("NATIVE_FILTER-month2", "Tháng (Month Key)", "month_key", dashboard_dataset_id),
        build_native_filter("NATIVE_FILTER-territory2", "Lãnh thổ (Territory)", "territory_name", dashboard_dataset_id),
        build_native_filter("NATIVE_FILTER-cluster2", "Phân cụm (Cluster)", "cluster_name", dashboard_dataset_id)
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
    print(f"Dashboard 2 ready: {BASE_URL}/superset/dashboard/{DASHBOARD_SLUG}/")

if __name__ == "__main__":
    main()

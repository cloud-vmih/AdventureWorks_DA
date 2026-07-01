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

DASHBOARD_TITLE = "Chương 5 - Yếu tố kinh tế vĩ mô thay đổi hành vi ra sao?"
DASHBOARD_SLUG = "adventureworks-chapter-5-macro-behavior"

def load_story_metrics() -> dict[str, object]:
    query = """
        WITH latest_macro AS (
            SELECT 
                AVG(cpi) AS latest_cpi,
                AVG(inflation) AS latest_inflation,
                AVG(interest_rate) AS latest_interest_rate,
                AVG(gdp) AS latest_gdp
            FROM dwh.fact_macro_economic_monthly
            WHERE month_key = (SELECT MAX(month_key) FROM dwh.fact_macro_economic_monthly)
        ),
        model_stats AS (
            SELECT 
                MAX(metric_value) FILTER (WHERE metric_name = 'R-squared' AND model_name = 'OLS Linear Regression') AS ols_r2,
                MAX(metric_value) FILTER (WHERE metric_name = 'Train R-squared' AND model_name = 'RandomForestRegressor') AS rf_r2
            FROM ml.macro_model_metrics
        ),
        corr_stats AS (
            SELECT 
                variable AS strongest_var,
                lag AS best_lag,
                correlation AS max_corr
            FROM ml.macro_analysis_correlations
            WHERE correlation IS NOT NULL AND correlation::text != 'NaN'
            ORDER BY ABS(correlation) DESC
            LIMIT 1
        ),
        scenario_stats AS (
            SELECT 
                scenario AS worst_scenario,
                predicted_revenue AS min_predicted_rev,
                revenue_change_pct AS min_rev_change
            FROM ml.macro_analysis_scenarios
            ORDER BY predicted_revenue ASC
            LIMIT 1
        )
        SELECT 
            l.*,
            m.ols_r2,
            m.rf_r2,
            c.strongest_var,
            c.best_lag,
            c.max_corr,
            s.worst_scenario,
            s.min_predicted_rev,
            s.min_rev_change
        FROM latest_macro l, model_stats m, corr_stats c, scenario_stats s
    """
    engine = get_dwh_engine()
    with engine.connect() as conn:
        df = pd.read_sql_query(query, conn)
        return df.iloc[0].to_dict()

def story_titles(metrics: dict[str, object]) -> list[str]:
    def pct(val):
        return f"{val*100:.1f}%".replace('.', ',')
        
    return [
        f"Lạm phát | Tỷ lệ Lạm phát hiện tại đạt {pct(metrics['latest_inflation'])}",
        f"Lãi suất | Lãi suất vay liên ngân hàng hiện tại ở mức {pct(metrics['latest_interest_rate'])}",
        f"Tương quan vĩ mô | Tương quan mạnh nhất với biến vĩ mô {metrics['strongest_var']} là {metrics['max_corr']:.4f}".replace('.', ','),
        f"Mô hình vĩ mô | OLS R² đạt {metrics['ols_r2']:.4f} và RF R² đạt {metrics['rf_r2']:.4f}".replace('.', ','),
        "Xu hướng chỉ số | Diễn biến Indexed Revenue vs Macro Variables theo tháng",
        "Diễn biến vĩ mô | GDP, CPI, Lãi suất, Lạm phát theo thời gian",
        "Ma trận trễ | Ma trận Correlation Heatmap (Variable × Lag Correlation)",
        "Độ trễ tối ưu | Phân phối độ trễ (Lags) ảnh hưởng đến doanh số",
        "Chi tiết tương quan | Top 10 hệ số tương quan trễ theo khu vực",
        "Tác động OLS | Hệ số hồi quy OLS Coefficients của các biến vĩ mô",
        "Độ tin cậy | Bảng thống kê ý nghĩa hồi quy OLS",
        "Độ quan trọng RF | Feature Importance từ mô hình Random Forest Regressor",
        "Cơ cấu tiêu dùng | Biến động Tỷ trọng Category Share theo thời gian",
        "Dịch chuyển mua sắm | Ma trận Category Transition Matrix (2023 -> 2024)",
        "Giữ chân | Tỷ lệ giữ chân khách hàng (Retention Rate) theo Category",
        "Mô phỏng kịch bản | Ma trận doanh thu mô phỏng theo CPI × Interest Rate",
        f"Đo lường kịch bản | Kịch bản xấu nhất {metrics['worst_scenario']} làm giảm {pct(metrics['min_rev_change'])} doanh số",
        "Chi tiết mô phỏng | Bảng so sánh chi tiết các Kịch bản Simulation"
    ]

def main():
    client = SupersetClient()
    client.login()
    db_id = get_database_id(client)
    
    # Get or create datasets
    kpi_macro_dataset_id = get_or_create_dataset(client, db_id, "mart", "mart_territory_macro_monthly")
    corr_dataset_id = get_or_create_dataset(client, db_id, "ml", "macro_analysis_correlations")
    scenario_dataset_id = get_or_create_dataset(client, db_id, "ml", "macro_analysis_scenarios")
    trans_dataset_id = get_or_create_dataset(client, db_id, "ml", "macro_category_transition")
    ols_coef_dataset_id = get_or_create_dataset(client, db_id, "ml", "macro_ols_coefficients")
    metrics_dataset_id = get_or_create_dataset(client, db_id, "ml", "macro_model_metrics")
    fi_dataset_id = get_or_create_dataset(client, db_id, "ml", "macro_rf_feature_importance")
    indexed_dataset_id = get_or_create_dataset(client, db_id, "ml", "macro_indexed_trend")
    cat_share_dataset_id = get_or_create_dataset(client, db_id, "ml", "macro_category_share")
    cat_retention_dataset_id = get_or_create_dataset(client, db_id, "ml", "vw_ch5_category_retention")
    
    dashboard_id = get_or_create_dashboard(client, DASHBOARD_TITLE, DASHBOARD_SLUG)
    metrics = load_story_metrics()
    titles = story_titles(metrics)
    
    chart_specs = [
        # Row 1: KPI
        (
            kpi_macro_dataset_id, titles[0], (), "big_number_total",
            {
                "datasource": f"{kpi_macro_dataset_id}__table", "viz_type": "big_number_total",
                "metric": simple_metric("inflation", "Tỷ lệ Lạm phát hiện tại", "AVG"), "time_range": "No filter", "y_axis_format": ".2%"
            }
        ),
        (
            kpi_macro_dataset_id, titles[1], (), "big_number_total",
            {
                "datasource": f"{kpi_macro_dataset_id}__table", "viz_type": "big_number_total",
                "metric": simple_metric("interest_rate", "Mức Lãi suất hiện tại", "AVG"), "time_range": "No filter", "y_axis_format": ".2%"
            }
        ),
        (
            corr_dataset_id, titles[2], (), "big_number_total",
            {
                "datasource": f"{corr_dataset_id}__table", "viz_type": "big_number_total",
                "metric": simple_metric("correlation", "Hệ số Tương quan mạnh nhất", "MAX"), "time_range": "No filter", "y_axis_format": ".4f"
            }
        ),
        (
            metrics_dataset_id, titles[3], (), "big_number_total",
            {
                "datasource": f"{metrics_dataset_id}__table", "viz_type": "big_number_total",
                "metric": simple_metric("metric_value", "Hồi quy OLS R²", "MAX"),
                "time_range": "No filter", "y_axis_format": ".4f",
                "adhoc_filters": [{"clause": "WHERE", "expressionType": "SIMPLE", "operator": "==", "subject": "metric_name", "comparator": "R-squared"}]
            }
        ),
        # Row 2: Macro Trend
        (
            indexed_dataset_id, titles[4], (), "echarts_timeseries_line",
            {
                "datasource": f"{indexed_dataset_id}__table", "viz_type": "echarts_timeseries_line",
                "x_axis": "month_key", "metrics": [simple_metric("indexed_revenue", "Revenue Index"), simple_metric("indexed_cpi", "CPI Index"), simple_metric("indexed_interest_rate", "Interest Index")],
                "groupby": [], "time_range": "No filter", "series_type": "line", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            kpi_macro_dataset_id, titles[5], (), "echarts_timeseries_line",
            {
                "datasource": f"{kpi_macro_dataset_id}__table", "viz_type": "echarts_timeseries_line",
                "x_axis": "month_key", "metrics": [simple_metric("gdp", "GDP (Avg)", "AVG"), simple_metric("cpi", "CPI (Avg)", "AVG"), simple_metric("interest_rate", "Lãi suất (Avg)", "AVG")],
                "groupby": [], "time_range": "No filter", "series_type": "line", "y_axis_format": "SMART_NUMBER"
            }
        ),
        # Row 3: Correlation & Lag
        (
            corr_dataset_id, titles[6], (), "pivot_table_v2",
            {
                "datasource": f"{corr_dataset_id}__table", "viz_type": "pivot_table_v2",
                "groupbyRows": ["variable"], "groupbyColumns": ["lag"],
                "metrics": [simple_metric("correlation", "Hệ số tương quan", "AVG")], "time_range": "No filter"
            }
        ),
        (
            corr_dataset_id, titles[7], (), "echarts_timeseries_bar",
            {
                "datasource": f"{corr_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "lag", "metrics": [simple_metric("correlation", "Tương quan trung bình", "AVG")],
                "groupby": [], "time_range": "No filter", "y_axis_format": ".4f"
            }
        ),
        (
            corr_dataset_id, titles[8], (), "table",
            {
                "datasource": f"{corr_dataset_id}__table", "viz_type": "table",
                "query_mode": "raw", "all_columns": ["territory_id", "variable", "lag", "correlation", "p_value"],
                "groupby": [], "metrics": [], "time_range": "No filter",
                "order_by_cols": ['["correlation", false]'], "row_limit": 50, "page_length": 10
            }
        ),
        # Row 4: Model Explanation
        (
            ols_coef_dataset_id, titles[9], (), "echarts_timeseries_bar",
            {
                "datasource": f"{ols_coef_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "variable", "metrics": [simple_metric("coefficient", "Hệ số Coeff")],
                "groupby": [], "time_range": "No filter", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            ols_coef_dataset_id, titles[10], (), "table",
            {
                "datasource": f"{ols_coef_dataset_id}__table", "viz_type": "table",
                "query_mode": "raw", "all_columns": ["variable", "coefficient", "p_value", "t_value", "standard_error"],
                "groupby": [], "metrics": [], "time_range": "No filter", "row_limit": 10
            }
        ),
        (
            fi_dataset_id, titles[11], (), "echarts_timeseries_bar",
            {
                "datasource": f"{fi_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "variable", "metrics": [simple_metric("importance", "Độ quan trọng RF")],
                "groupby": [], "time_range": "No filter", "y_axis_format": ".4f", "orientation": "horizontal"
            }
        ),
        # Row 5: Category Switching
        (
            cat_share_dataset_id, titles[12], (), "echarts_timeseries_line",
            {
                "datasource": f"{cat_share_dataset_id}__table", "viz_type": "echarts_timeseries_line",
                "x_axis": "month_key", "metrics": [simple_metric("category_share", "Tỷ trọng Category", "AVG")],
                "groupby": ["category_name"], "time_range": "No filter", "series_type": "line", "y_axis_format": ".2%"
            }
        ),
        (
            trans_dataset_id, titles[13], (), "pivot_table_v2",
            {
                "datasource": f"{trans_dataset_id}__table", "viz_type": "pivot_table_v2",
                "groupbyRows": ["prev_category"], "groupbyColumns": ["next_category"],
                "metrics": [simple_metric("transition_count", "Số lượt chuyển dịch", "SUM")], "time_range": "No filter"
            }
        ),
        (
            cat_retention_dataset_id, titles[14], (), "echarts_timeseries_bar",
            {
                "datasource": f"{cat_retention_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "category_name", "metrics": [simple_metric("retention_rate", "Tỷ lệ giữ chân", "AVG")],
                "groupby": [], "time_range": "No filter", "y_axis_format": ".2%"
            }
        ),
        # Row 6: Scenario Simulation
        (
            scenario_dataset_id, titles[15], (), "pivot_table_v2",
            {
                "datasource": f"{scenario_dataset_id}__table", "viz_type": "pivot_table_v2",
                "groupbyRows": ["cpi"], "groupbyColumns": ["interest_rate"],
                "metrics": [simple_metric("predicted_revenue", "Doanh thu kịch bản", "AVG")], "time_range": "No filter"
            }
        ),
        (
            scenario_dataset_id, titles[16], (), "echarts_timeseries_bar",
            {
                "datasource": f"{scenario_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "scenario", "metrics": [simple_metric("revenue_change_pct", "Mức thay đổi doanh số", "AVG")],
                "groupby": [], "time_range": "No filter", "y_axis_format": ".2%"
            }
        ),
        (
            scenario_dataset_id, titles[17], (), "table",
            {
                "datasource": f"{scenario_dataset_id}__table", "viz_type": "table",
                "query_mode": "raw", "all_columns": ["scenario", "cpi", "interest_rate", "predicted_revenue", "revenue_change_pct"],
                "groupby": [], "metrics": [], "time_range": "No filter", "row_limit": 50
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
        [(titles[12], 4, 34), (titles[13], 4, 34), (titles[14], 4, 34)],
        [(titles[15], 4, 34), (titles[16], 4, 34), (titles[17], 4, 34)]
    ]
    
    # Native Filters
    native_filters = [
        build_native_filter("NATIVE_FILTER-variable5", "Biến vĩ mô (Variable)", "variable", corr_dataset_id),
        build_native_filter("NATIVE_FILTER-scenario5", "Kịch bản (Scenario)", "scenario", scenario_dataset_id)
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
    print(f"Dashboard 5 ready: {BASE_URL}/superset/dashboard/{DASHBOARD_SLUG}/")

if __name__ == "__main__":
    main()

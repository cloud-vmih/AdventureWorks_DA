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

DASHBOARD_TITLE = "Chương 1 - Bức tranh sức khỏe doanh nghiệp"
DASHBOARD_SLUG = "adventureworks-chapter-1-business-health"

def load_story_metrics() -> dict[str, object]:
    query = """
        WITH sales_totals AS (
            SELECT 
                SUM(revenue) AS total_revenue,
                SUM(gross_profit) AS total_profit,
                SUM(gross_profit) / NULLIF(SUM(revenue), 0) AS total_margin,
                SUM(orders) AS total_orders,
                SUM(quantity) AS total_quantity,
                MIN(month_key) AS min_month,
                MAX(month_key) AS max_month
            FROM mart.mart_sales_kpi_monthly
        ),
        channels AS (
            SELECT
                SUM(revenue) FILTER (WHERE channel = 'B2B') / NULLIF(SUM(revenue), 0) AS b2b_share,
                SUM(revenue) FILTER (WHERE channel = 'B2C') / NULLIF(SUM(revenue), 0) AS b2c_share
            FROM mart.mart_sales_kpi_monthly
        ),
        top_territory AS (
            SELECT territory_group
            FROM mart.mart_sales_kpi_monthly
            GROUP BY territory_group
            ORDER BY SUM(revenue) DESC
            LIMIT 1
        ),
        top_category AS (
            SELECT category_name
            FROM mart.mart_sales_kpi_monthly
            GROUP BY category_name
            ORDER BY SUM(revenue) DESC
            LIMIT 1
        )
        SELECT 
            t.*,
            c.b2b_share,
            c.b2c_share,
            tt.territory_group AS top_territory,
            tc.category_name AS top_category
        FROM sales_totals t, channels c, top_territory tt, top_category tc
    """
    engine = get_dwh_engine()
    with engine.connect() as conn:
        df = pd.read_sql_query(query, conn)
        return df.iloc[0].to_dict()

def story_titles(metrics: dict[str, object]) -> list[str]:
    def money_millions(val):
        return f"{val/1e6:.1f} triệu USD".replace('.', ',')
    def pct(val):
        return f"{val*100:.1f}%".replace('.', ',')
        
    min_month = metrics['min_month']
    max_month = metrics['max_month']
    period = f"{min_month[4:]}/{min_month[:4]}-{max_month[4:]}/{max_month[:4]}"
    
    return [
        f"Quy mô | Doanh thu đạt {money_millions(metrics['total_revenue'])} ({period})",
        f"Lợi nhuận | Lợi nhuận gộp đạt {money_millions(metrics['total_profit'])}",
        f"Biên lợi nhuận | Biên lợi nhuận gộp đạt {pct(metrics['total_margin'])}",
        f"Đơn hàng | Tổng số đơn hàng đạt {int(metrics['total_orders']):,}".replace(',', '.'),
        f"Xu hướng | Doanh thu & Lợi nhuận theo tháng",
        f"Kênh bán hàng | Tốc độ tăng trưởng theo Kênh",
        f"Cơ cấu | Kênh B2B đóng góp {pct(metrics['b2b_share'])} doanh thu",
        f"Kênh | Tỷ trọng doanh số theo Channel",
        f"Khu vực | {metrics['top_territory']} là thị trường lớn nhất",
        f"Sản phẩm | {metrics['top_category']} đóng góp doanh số chính",
        f"Mật độ | Phân bổ doanh số theo Quốc gia và Danh mục",
        f"Chỉ tiêu | Xuuyên Quota đặt ra theo Quý",
        f"Nhân sự | Top nhân viên đạt Quota xuất sắc nhất",
        f"Phân bố | Phân bổ định mức Quota nhân viên"
    ]

def main():
    client = SupersetClient()
    client.login()
    db_id = get_database_id(client)
    
    # Get or create datasets
    kpi_dataset_id = get_or_create_dataset(client, db_id, "mart", "mart_sales_kpi_monthly")
    quota_dataset_id = get_or_create_dataset(client, db_id, "mart", "vw_ch1_quota_quarterly")
    emp_dataset_id = get_or_create_dataset(client, db_id, "mart", "vw_ch1_employee_quota")
    
    dashboard_id = get_or_create_dashboard(client, DASHBOARD_TITLE, DASHBOARD_SLUG)
    metrics = load_story_metrics()
    titles = story_titles(metrics)
    
    chart_specs = [
        # Row 1: KPI
        (
            kpi_dataset_id, titles[0], (), "big_number_total",
            {
                "datasource": f"{kpi_dataset_id}__table", "viz_type": "big_number_total",
                "metric": simple_metric("revenue", "Tổng doanh thu"), "time_range": "No filter", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            kpi_dataset_id, titles[1], (), "big_number_total",
            {
                "datasource": f"{kpi_dataset_id}__table", "viz_type": "big_number_total",
                "metric": simple_metric("gross_profit", "Lợi nhuận gộp"), "time_range": "No filter", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            kpi_dataset_id, titles[2], (), "big_number_total",
            {
                "datasource": f"{kpi_dataset_id}__table", "viz_type": "big_number_total",
                "metric": sql_metric("SUM(gross_profit)/NULLIF(SUM(revenue),0)", "Biên lợi nhuận gộp", "metric_weighted_margin"),
                "time_range": "No filter", "y_axis_format": ".2%"
            }
        ),
        (
            kpi_dataset_id, titles[3], (), "big_number_total",
            {
                "datasource": f"{kpi_dataset_id}__table", "viz_type": "big_number_total",
                "metric": simple_metric("orders", "Tổng số đơn", "SUM"), "time_range": "No filter", "y_axis_format": "SMART_NUMBER"
            }
        ),
        # Row 2: Trend
        (
            kpi_dataset_id, titles[4], (), "echarts_timeseries_line",
            {
                "datasource": f"{kpi_dataset_id}__table", "viz_type": "echarts_timeseries_line",
                "x_axis": "month_key", "metrics": [simple_metric("revenue", "Doanh thu"), simple_metric("gross_profit", "Lợi nhuận gộp")],
                "groupby": [], "time_range": "No filter", "series_type": "line", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            kpi_dataset_id, titles[5], (), "echarts_timeseries_line",
            {
                "datasource": f"{kpi_dataset_id}__table", "viz_type": "echarts_timeseries_line",
                "x_axis": "month_key", "metrics": [simple_metric("revenue", "Doanh thu")],
                "groupby": ["channel"], "time_range": "No filter", "series_type": "line", "y_axis_format": "SMART_NUMBER"
            }
        ),
        # Row 3: Contribution
        (
            kpi_dataset_id, titles[6], (), "echarts_timeseries_bar",
            {
                "datasource": f"{kpi_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "month_key", "metrics": [simple_metric("revenue", "Doanh thu")],
                "groupby": ["channel"], "time_range": "No filter", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            kpi_dataset_id, titles[7], (), "pie",
            {
                "datasource": f"{kpi_dataset_id}__table", "viz_type": "pie",
                "groupby": ["channel"], "metric": simple_metric("revenue", "Doanh thu"), "time_range": "No filter"
            }
        ),
        (
            kpi_dataset_id, titles[8], (), "echarts_timeseries_bar",
            {
                "datasource": f"{kpi_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "territory_group", "metrics": [simple_metric("revenue", "Doanh thu")],
                "groupby": [], "time_range": "No filter", "y_axis_format": "SMART_NUMBER", "orientation": "horizontal"
            }
        ),
        # Row 4: Category & Heatmap
        (
            kpi_dataset_id, titles[9], (), "echarts_timeseries_bar",
            {
                "datasource": f"{kpi_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "category_name", "metrics": [simple_metric("revenue", "Doanh thu")],
                "groupby": [], "time_range": "No filter", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            kpi_dataset_id, titles[10], (), "pivot_table_v2",
            {
                "datasource": f"{kpi_dataset_id}__table", "viz_type": "pivot_table_v2",
                "groupbyRows": ["country_code"], "groupbyColumns": ["category_name"],
                "metrics": [simple_metric("revenue", "Doanh thu")], "time_range": "No filter"
            }
        ),
        # Row 5: Quota
        (
            quota_dataset_id, titles[11], (), "echarts_timeseries_line",
            {
                "datasource": f"{quota_dataset_id}__table", "viz_type": "echarts_timeseries_line",
                "x_axis": "quarter_key", "metrics": [simple_metric("total_quota", "Tổng Quota"), simple_metric("avg_quota", "Quota Trung bình")],
                "groupby": [], "time_range": "No filter", "series_type": "line", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            emp_dataset_id, titles[12], (), "echarts_timeseries_bar",
            {
                "datasource": f"{emp_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "employee_name", "metrics": [simple_metric("quota", "Quota")],
                "groupby": [], "time_range": "No filter", "y_axis_format": "SMART_NUMBER", "row_limit": 10
            }
        ),
        (
            emp_dataset_id, titles[13], (), "table",
            {
                "datasource": f"{emp_dataset_id}__table", "viz_type": "table",
                "query_mode": "aggregate", "groupby": ["employee_name", "job_title"],
                "metrics": [simple_metric("quota", "Tổng Quota")], "time_range": "No filter",
                "order_by_cols": ['["quota", false]'], "row_limit": 50, "page_length": 10
            }
        )
    ]
    
    charts = []
    for dataset_id, slice_name, legacy, viz_type, params in chart_specs:
        chart_id = get_or_create_chart(client, dashboard_id, dataset_id, slice_name, legacy, viz_type, params)
        charts.append((chart_id, slice_name))
        
    remove_stale_dashboard_charts(client, dashboard_id, {c[0] for c in charts})
    
    # Define Layout
    sections = [
        [(titles[0], 3, 18), (titles[1], 3, 18), (titles[2], 3, 18), (titles[3], 3, 18)],
        [(titles[4], 6, 30), (titles[5], 6, 30)],
        [(titles[6], 4, 34), (titles[7], 4, 34), (titles[8], 4, 34)],
        [(titles[9], 6, 38), (titles[10], 6, 38)],
        [(titles[11], 4, 34), (titles[12], 4, 34), (titles[13], 4, 34)]
    ]
    
    # Native Filters
    # Filter 1: month_key, Filter 2: territory_group, Filter 3: channel, Filter 4: category_name
    quota_chart_ids = [charts[11][0], charts[12][0], charts[13][0]]
    
    native_filters = [
        build_native_filter("NATIVE_FILTER-month", "Tháng (Month Key)", "month_key", kpi_dataset_id, quota_chart_ids),
        build_native_filter("NATIVE_FILTER-group", "Khu vực (Territory Group)", "territory_group", kpi_dataset_id, quota_chart_ids),
        build_native_filter("NATIVE_FILTER-channel", "Kênh (Channel)", "channel", kpi_dataset_id, quota_chart_ids),
        build_native_filter("NATIVE_FILTER-category", "Danh mục (Category)", "category_name", kpi_dataset_id, quota_chart_ids)
    ]
    
    # Update Dashboard metadata & layout
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
    print(f"Dashboard 1 ready: {BASE_URL}/superset/dashboard/{DASHBOARD_SLUG}/")

if __name__ == "__main__":
    main()

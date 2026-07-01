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

DASHBOARD_TITLE = "Chương 4 - Sản phẩm nào tạo hoặc phá hủy giá trị?"
DASHBOARD_SLUG = "adventureworks-chapter-4-product-value"

def load_story_metrics() -> dict[str, object]:
    query = """
        WITH totals AS (
            SELECT 
                SUM(revenue) AS total_revenue,
                SUM(gross_profit) AS total_profit,
                SUM(gross_profit) / NULLIF(SUM(revenue), 0) AS total_margin,
                SUM(units_sold) AS total_units
            FROM ml.product_portfolio
        ),
        loss_products AS (
            SELECT 
                COUNT(*) AS loss_count,
                -SUM(gross_profit) AS leakage
            FROM ml.product_portfolio
            WHERE gross_profit < 0
        ),
        bikes_share AS (
            SELECT 
                SUM(revenue) FILTER (WHERE category_name = 'Bikes') / NULLIF(SUM(revenue), 0) AS bikes_share
            FROM ml.product_portfolio
        ),
        acc_margin AS (
            SELECT 
                SUM(gross_profit) FILTER (WHERE category_name = 'Accessories') / NULLIF(SUM(revenue) FILTER (WHERE category_name = 'Accessories'), 0) AS acc_margin
            FROM ml.product_portfolio
        ),
        leaders AS (
            SELECT 
                (SELECT product_name FROM ml.product_portfolio ORDER BY revenue DESC LIMIT 1) AS leader_name,
                (SELECT product_name FROM ml.product_portfolio ORDER BY gross_profit DESC LIMIT 1) AS profit_leader_name
        ),
        portfolio_counts AS (
            SELECT 
                COUNT(*) FILTER (WHERE portfolio = 'Star') AS star_count,
                COUNT(*) FILTER (WHERE portfolio = 'Weak') AS weak_count
            FROM ml.product_portfolio
        )
        SELECT 
            t.*,
            lp.loss_count,
            lp.leakage,
            bs.bikes_share,
            am.acc_margin,
            l.leader_name,
            l.profit_leader_name,
            pc.star_count,
            pc.weak_count
        FROM totals t, loss_products lp, bikes_share bs, am acc_margin, leaders l, portfolio_counts pc
    """
    # Wait, the alias of Acc Margin was am and in from list we had am acc_margin, but that table is acc_margin.
    # Let's fix the SQL query to avoid syntax error.
    query_fixed = """
        WITH totals AS (
            SELECT 
                SUM(revenue) AS total_revenue,
                SUM(gross_profit) AS total_profit,
                SUM(gross_profit) / NULLIF(SUM(revenue), 0) AS total_margin,
                SUM(units_sold) AS total_units
            FROM ml.product_portfolio
        ),
        loss_products AS (
            SELECT 
                COUNT(*) AS loss_count,
                -SUM(gross_profit) AS leakage
            FROM ml.product_portfolio
            WHERE gross_profit < 0
        ),
        bikes_share AS (
            SELECT 
                SUM(revenue) FILTER (WHERE category_name = 'Bikes') / NULLIF(SUM(revenue), 0) AS bikes_share
            FROM ml.product_portfolio
        ),
        acc_margin AS (
            SELECT 
                SUM(gross_profit) FILTER (WHERE category_name = 'Accessories') / NULLIF(SUM(revenue) FILTER (WHERE category_name = 'Accessories'), 0) AS acc_margin
            FROM ml.product_portfolio
        ),
        leaders AS (
            SELECT 
                (SELECT product_name FROM ml.product_portfolio ORDER BY revenue DESC LIMIT 1) AS leader_name,
                (SELECT product_name FROM ml.product_portfolio ORDER BY gross_profit DESC LIMIT 1) AS profit_leader_name
        ),
        portfolio_counts AS (
            SELECT 
                COUNT(*) FILTER (WHERE portfolio = 'Star') AS star_count,
                COUNT(*) FILTER (WHERE portfolio = 'Weak') AS weak_count
            FROM ml.product_portfolio
        )
        SELECT 
            t.*,
            lp.loss_count,
            lp.leakage,
            bs.bikes_share,
            am.acc_margin,
            l.leader_name,
            l.profit_leader_name,
            pc.star_count,
            pc.weak_count
        FROM totals t, loss_products lp, bikes_share bs, acc_margin am, leaders l, portfolio_counts pc
    """
    engine = get_dwh_engine()
    with engine.connect() as conn:
        df = pd.read_sql_query(query_fixed, conn)
        return df.iloc[0].to_dict()

def story_titles(metrics: dict[str, object]) -> list[str]:
    def money_millions(val):
        return f"{val/1e6:.1f} triệu USD".replace('.', ',')
    def pct(val):
        return f"{val*100:.1f}%".replace('.', ',')
        
    return [
        f"Doanh thu | Tổng quy mô danh mục đạt {money_millions(metrics['total_revenue'])}",
        f"Lợi nhuận | Tổng lợi nhuận gộp đạt {money_millions(metrics['total_profit'])}",
        f"Biên lợi nhuận | Biên lợi nhuận danh mục đạt {pct(metrics['total_margin'])}",
        f"Rủi ro | Phát hiện {int(metrics['loss_count'])} sản phẩm lỗ ({money_millions(metrics['leakage'])} leakage)",
        f"Đóng góp | Doanh thu theo Category (Bikes chiếm {pct(metrics['bikes_share'])})",
        f"Hiệu quả | Biên lợi nhuận gộp theo Category (Accessories đạt {pct(metrics['acc_margin'])})",
        f"Dẫn đầu doanh thu | {metrics['leader_name']}",
        f"Đóng góp lợi nhuận | {metrics['profit_leader_name']}",
        "Ma trận | Phân nhóm Portfolio Matrix (Star, Volume-Low Margin, Niche-High Margin, Weak)",
        f"Quy mô nhóm | Danh mục có {int(metrics['star_count'])} sản phẩm Star vs {int(metrics['weak_count'])} sản phẩm Weak",
        "Hành động | Khuyến nghị chiến lược cho sản phẩm Star và Weak",
        "Pareto Doanh thu | 80% doanh thu đến từ nhóm A",
        "Pareto Lợi nhuận | Phân tích Pareto cho Lợi nhuận gộp",
        "Đối chiếu ABC | Phân loại ma trận ABC Revenue vs ABC Profit",
        "Chi tiết | Danh sách sản phẩm thuộc nhóm doanh số cao nhưng lợi nhuận thấp",
        "Chiết khấu | Mối quan hệ giữa Chiết khấu vs Tăng trưởng Doanh thu",
        "Biên lợi nhuận | Mối quan hệ giữa Chiết khấu vs Biên lợi nhuận gộp",
        "Cảnh báo | Danh sách sản phẩm chiết khấu không hiệu quả",
        "Tồn kho | Trực quan hóa rủi ro kho hàng theo Trạng thái",
        "Chu kỳ kho | Số ngày lưu kho trung bình vs Biên lợi nhuận",
        "Thanh lý | Danh sách sản phẩm Overstock hoặc Slow Moving cần giải phóng kho",
        "Phân khúc | Phân cụm sản phẩm dựa trên PCA Component Map",
        "Đặc trưng | Hồ sơ phân cụm sản phẩm (Cluster Profile)",
        "Quản trị | Khuyến nghị chiến lược theo cụm sản phẩm",
        "Kết hợp | Top 10 quy luật mua kèm sản phẩm có chỉ số Lift cao nhất",
        "Bảng quy luật | Antecedent, Consequent, Support, Confidence, Lift",
        "Dự báo | Doanh thu thực tế vs Doanh thu dự báo theo Category",
        "Sai số | Sai số dự báo trung bình (MAE) theo Category",
        "Feature Importance | Các biến có ảnh hưởng lớn nhất đến dự báo"
    ]

def main():
    client = SupersetClient()
    client.login()
    db_id = get_database_id(client)
    
    # Get or create datasets
    kpi_dataset_id = get_or_create_dataset(client, db_id, "mart", "mart_product_profitability_monthly")
    inventory_dataset_id = get_or_create_dataset(client, db_id, "mart", "mart_inventory_risk")
    portfolio_dataset_id = get_or_create_dataset(client, db_id, "ml", "product_portfolio")
    abc_dataset_id = get_or_create_dataset(client, db_id, "ml", "product_abc_analysis")
    discount_dataset_id = get_or_create_dataset(client, db_id, "ml", "product_discount_effectiveness")
    cluster_dataset_id = get_or_create_dataset(client, db_id, "ml", "product_cluster_result")
    mba_dataset_id = get_or_create_dataset(client, db_id, "ml", "association_rules")
    forecast_dataset_id = get_or_create_dataset(client, db_id, "ml", "product_category_forecast")
    strategy_dataset_id = get_or_create_dataset(client, db_id, "ml", "product_strategy_actions")
    
    dashboard_id = get_or_create_dashboard(client, DASHBOARD_TITLE, DASHBOARD_SLUG)
    metrics = load_story_metrics()
    titles = story_titles(metrics)
    
    chart_specs = [
        # Row 1: KPI
        (
            portfolio_dataset_id, titles[0], (), "big_number_total",
            {
                "datasource": f"{portfolio_dataset_id}__table", "viz_type": "big_number_total",
                "metric": simple_metric("revenue", "Doanh thu"), "time_range": "No filter", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            portfolio_dataset_id, titles[1], (), "big_number_total",
            {
                "datasource": f"{portfolio_dataset_id}__table", "viz_type": "big_number_total",
                "metric": simple_metric("gross_profit", "Lợi nhuận gộp"), "time_range": "No filter", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            portfolio_dataset_id, titles[2], (), "big_number_total",
            {
                "datasource": f"{portfolio_dataset_id}__table", "viz_type": "big_number_total",
                "metric": sql_metric("SUM(gross_profit)/NULLIF(SUM(revenue),0)", "Biên lợi nhuận", "metric_weighted_margin"),
                "time_range": "No filter", "y_axis_format": ".2%"
            }
        ),
        (
            portfolio_dataset_id, titles[3], (), "big_number_total",
            {
                "datasource": f"{portfolio_dataset_id}__table", "viz_type": "big_number_total",
                "metric": sql_metric("COUNT(*) FILTER (WHERE gross_profit < 0)", "Sản phẩm lỗ", "metric_loss_count"),
                "time_range": "No filter", "y_axis_format": "SMART_NUMBER"
            }
        ),
        # Row 2: Category value
        (
            portfolio_dataset_id, titles[4], (), "echarts_timeseries_bar",
            {
                "datasource": f"{portfolio_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "category_name", "metrics": [simple_metric("revenue", "Doanh thu")],
                "groupby": [], "time_range": "No filter", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            portfolio_dataset_id, titles[5], (), "echarts_timeseries_bar",
            {
                "datasource": f"{portfolio_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "category_name", "metrics": [sql_metric("SUM(gross_profit)/NULLIF(SUM(revenue),0)", "Biên lợi nhuận", "metric_cat_margin")],
                "groupby": [], "time_range": "No filter", "y_axis_format": ".2%"
            }
        ),
        # Row 3: Product leaders
        (
            portfolio_dataset_id, titles[6], (), "echarts_timeseries_bar",
            {
                "datasource": f"{portfolio_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "product_name", "metrics": [simple_metric("revenue", "Doanh thu")],
                "groupby": [], "time_range": "No filter", "y_axis_format": "SMART_NUMBER", "row_limit": 10, "orientation": "horizontal"
            }
        ),
        (
            portfolio_dataset_id, titles[7], (), "echarts_timeseries_bar",
            {
                "datasource": f"{portfolio_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "product_name", "metrics": [simple_metric("gross_profit", "Lợi nhuận gộp")],
                "groupby": [], "time_range": "No filter", "y_axis_format": "SMART_NUMBER", "row_limit": 10, "orientation": "horizontal"
            }
        ),
        # Row 4: Portfolio
        (
            portfolio_dataset_id, titles[8], (), "bubble_v2",
            {
                "datasource": f"{portfolio_dataset_id}__table", "viz_type": "bubble_v2",
                "entity": "product_name", "series": "portfolio",
                "x": simple_metric("revenue", "Doanh thu"),
                "y": simple_metric("gross_margin", "Biên lợi nhuận gộp"),
                "size": simple_metric("units_sold", "Số lượng bán"),
                "time_range": "No filter", "xAxisFormat": "SMART_NUMBER", "yAxisFormat": ".2%"
            }
        ),
        (
            portfolio_dataset_id, titles[9], (), "echarts_timeseries_bar",
            {
                "datasource": f"{portfolio_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "portfolio", "metrics": [sql_metric("COUNT(*)", "Số lượng sản phẩm", "metric_count")],
                "groupby": [], "time_range": "No filter", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            strategy_dataset_id, titles[10], (), "table",
            {
                "datasource": f"{strategy_dataset_id}__table", "viz_type": "table",
                "query_mode": "raw", "all_columns": ["product_name", "category_name", "portfolio", "recommended_action", "priority"],
                "groupby": [], "metrics": [], "time_range": "No filter", "row_limit": 50
            }
        ),
        # Row 5: ABC
        (
            abc_dataset_id, titles[11], (), "echarts_timeseries_bar",
            {
                "datasource": f"{abc_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "abc_revenue", "metrics": [simple_metric("revenue", "Doanh thu")],
                "groupby": [], "time_range": "No filter", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            abc_dataset_id, titles[12], (), "echarts_timeseries_bar",
            {
                "datasource": f"{abc_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "abc_profit", "metrics": [simple_metric("gross_profit", "Lợi nhuận gộp")],
                "groupby": [], "time_range": "No filter", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            abc_dataset_id, titles[13], (), "pivot_table_v2",
            {
                "datasource": f"{abc_dataset_id}__table", "viz_type": "pivot_table_v2",
                "groupbyRows": ["abc_revenue"], "groupbyColumns": ["abc_profit"],
                "metrics": [sql_metric("COUNT(*)", "Số sản phẩm", "metric_count")], "time_range": "No filter"
            }
        ),
        (
            abc_dataset_id, titles[14], (), "table",
            {
                "datasource": f"{abc_dataset_id}__table", "viz_type": "table",
                "query_mode": "raw", "all_columns": ["product_name", "category_name", "revenue", "gross_profit", "abc_revenue", "abc_profit"],
                "groupby": [], "metrics": [], "time_range": "No filter",
                "adhoc_filters": [{"clause": "WHERE", "expressionType": "SIMPLE", "operator": "==", "subject": "abc_revenue", "comparator": "A"},
                                 {"clause": "WHERE", "expressionType": "SIMPLE", "operator": "!=", "subject": "abc_profit", "comparator": "A"}],
                "row_limit": 50
            }
        ),
        # Row 6: Discount
        (
            discount_dataset_id, titles[15], (), "bubble_v2",
            {
                "datasource": f"{discount_dataset_id}__table", "viz_type": "bubble_v2",
                "entity": "product_name", "series": "category_name",
                "x": simple_metric("avg_discount", "Mức chiết khấu"),
                "y": simple_metric("revenue", "Doanh thu"),
                "size": simple_metric("units_sold", "Số lượng bán"),
                "time_range": "No filter", "xAxisFormat": ".2%", "yAxisFormat": "SMART_NUMBER"
            }
        ),
        (
            discount_dataset_id, titles[16], (), "bubble_v2",
            {
                "datasource": f"{discount_dataset_id}__table", "viz_type": "bubble_v2",
                "entity": "product_name", "series": "category_name",
                "x": simple_metric("avg_discount", "Mức chiết khấu"),
                "y": simple_metric("gross_margin", "Biên lợi nhuận gộp"),
                "size": simple_metric("revenue", "Doanh thu"),
                "time_range": "No filter", "xAxisFormat": ".2%", "yAxisFormat": ".2%"
            }
        ),
        (
            discount_dataset_id, titles[17], (), "table",
            {
                "datasource": f"{discount_dataset_id}__table", "viz_type": "table",
                "query_mode": "raw", "all_columns": ["product_name", "category_name", "avg_discount", "gross_margin", "effectiveness"],
                "groupby": [], "metrics": [], "time_range": "No filter",
                "adhoc_filters": [{"clause": "WHERE", "expressionType": "SIMPLE", "operator": "==", "subject": "effectiveness", "comparator": "Ineffective - Margin Diluted"}],
                "row_limit": 50
            }
        ),
        # Row 7: Inventory
        (
            inventory_dataset_id, titles[18], (), "pie",
            {
                "datasource": f"{inventory_dataset_id}__table", "viz_type": "pie",
                "groupby": ["inventory_risk_status"], "metric": sql_metric("COUNT(*)", "Số lượng sản phẩm", "metric_count"), "time_range": "No filter"
            }
        ),
        (
            inventory_dataset_id, titles[19], (), "bubble_v2",
            {
                "datasource": f"{inventory_dataset_id}__table", "viz_type": "bubble_v2",
                "entity": "product_name", "series": "inventory_risk_status",
                "x": simple_metric("days_inventory_proxy", "Số ngày lưu kho"),
                "y": simple_metric("gross_margin", "Biên lợi nhuận gộp"),
                "size": simple_metric("inventory_turnover_qty", "Vòng quay kho"),
                "time_range": "No filter", "xAxisFormat": "SMART_NUMBER", "yAxisFormat": ".2%"
            }
        ),
        (
            inventory_dataset_id, titles[20], (), "table",
            {
                "datasource": f"{inventory_dataset_id}__table", "viz_type": "table",
                "query_mode": "raw", "all_columns": ["product_name", "inventory_risk_status", "days_inventory_proxy", "gross_margin"],
                "groupby": [], "metrics": [], "time_range": "No filter",
                "adhoc_filters": [{"clause": "WHERE", "expressionType": "SIMPLE", "operator": "IN", "subject": "inventory_risk_status", "comparator": ["Overstock", "Slow Moving"]}],
                "row_limit": 50
            }
        ),
        # Row 8: Clustering
        (
            cluster_dataset_id, titles[21], (), "bubble_v2",
            {
                "datasource": f"{cluster_dataset_id}__table", "viz_type": "bubble_v2",
                "entity": "product_name", "series": "cluster_name",
                "x": simple_metric("revenue", "Doanh thu Component"),
                "y": simple_metric("gross_margin", "Biên lợi nhuận Component"),
                "size": simple_metric("units_sold", "Số lượng bán"),
                "time_range": "No filter", "xAxisFormat": "SMART_NUMBER", "yAxisFormat": ".2%"
            }
        ),
        (
            cluster_dataset_id, titles[22], (), "echarts_timeseries_bar",
            {
                "datasource": f"{cluster_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "cluster_name", "metrics": [simple_metric("revenue", "Doanh thu trung bình", "AVG")],
                "groupby": [], "time_range": "No filter", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            cluster_dataset_id, titles[23], (), "table",
            {
                "datasource": f"{cluster_dataset_id}__table", "viz_type": "table",
                "query_mode": "raw", "all_columns": ["product_name", "category_name", "cluster_name", "revenue", "gross_margin"],
                "groupby": [], "metrics": [], "time_range": "No filter", "row_limit": 50
            }
        ),
        # Row 9: MBA Market Basket
        (
            mba_dataset_id, titles[24], (), "echarts_timeseries_bar",
            {
                "datasource": f"{mba_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "antecedents", "metrics": [simple_metric("lift", "Độ nâng (Lift)", "MAX")],
                "groupby": [], "time_range": "No filter", "y_axis_format": "SMART_NUMBER", "row_limit": 10
            }
        ),
        (
            mba_dataset_id, titles[25], (), "table",
            {
                "datasource": f"{mba_dataset_id}__table", "viz_type": "table",
                "query_mode": "raw", "all_columns": ["antecedents", "consequents", "support", "confidence", "lift"],
                "groupby": [], "metrics": [], "time_range": "No filter", "order_by_cols": ['["lift", false]'], "row_limit": 50
            }
        ),
        # Row 10: Forecast
        (
            forecast_dataset_id, titles[26], (), "echarts_timeseries_line",
            {
                "datasource": f"{forecast_dataset_id}__table", "viz_type": "echarts_timeseries_line",
                "x_axis": "month_key", "metrics": [simple_metric("actual_revenue", "Doanh thu thực tế", "SUM"), simple_metric("forecast_revenue_xgb", "Dự báo XGBoost", "SUM")],
                "groupby": [], "time_range": "No filter", "series_type": "line", "y_axis_format": "SMART_NUMBER"
            }
        ),
        (
            forecast_dataset_id, titles[27], (), "echarts_timeseries_bar",
            {
                "datasource": f"{forecast_dataset_id}__table", "viz_type": "echarts_timeseries_bar",
                "x_axis": "category_name", "metrics": [simple_metric("mae", "Sai số MAE", "AVG")],
                "groupby": [], "time_range": "No filter", "y_axis_format": "SMART_NUMBER"
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
        [(titles[6], 6, 30), (titles[7], 6, 30)],
        [(titles[8], 4, 34), (titles[9], 4, 34), (titles[10], 4, 34)],
        [(titles[11], 3, 34), (titles[12], 3, 34), (titles[13], 3, 34), (titles[14], 3, 34)],
        [(titles[15], 4, 34), (titles[16], 4, 34), (titles[17], 4, 34)],
        [(titles[18], 4, 34), (titles[19], 4, 34), (titles[20], 4, 34)],
        [(titles[21], 4, 34), (titles[22], 4, 34), (titles[23], 4, 34)],
        [(titles[24], 6, 34), (titles[25], 6, 34)],
        [(titles[26], 6, 34), (titles[27], 6, 34)]
    ]
    
    # Native Filters
    native_filters = [
        build_native_filter("NATIVE_FILTER-category4", "Danh mục (Category)", "category_name", portfolio_dataset_id),
        build_native_filter("NATIVE_FILTER-portfolio4", "Nhóm Portfolio", "portfolio", portfolio_dataset_id),
        build_native_filter("NATIVE_FILTER-risk4", "Tồn kho Status", "inventory_risk_status", inventory_dataset_id)
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
    print(f"Dashboard 4 ready: {BASE_URL}/superset/dashboard/{DASHBOARD_SLUG}/")

if __name__ == "__main__":
    main()

-- Views for Chapter 2: Territory Analysis
CREATE OR REPLACE VIEW ml.vw_ch2_territory_strategy AS
SELECT 
    territory_name,
    cluster_name,
    mean_profit_margin,
    mean_retention_rate,
    CASE 
        WHEN cluster_name = 'Thị trường chủ lực' THEN 'Tập trung tối đa giữ chân khách hàng (Retention), chăm sóc VIP và cross-selling.'
        WHEN cluster_name = 'Thị trường tăng trưởng tiềm năng' THEN 'Tăng ngân sách marketing, tối ưu kênh thu hút khách hàng mới, kích cầu.'
        WHEN cluster_name = 'Thị trường ổn định quy mô trung bình' THEN 'Duy trì hoạt động, khai thác tối ưu biên lợi nhuận gộp.'
        ELSE 'Rà soát danh mục sản phẩm, cải thiện giá, thu hút khách hàng active.'
    END AS recommended_action
FROM ml.territory_cluster_result;

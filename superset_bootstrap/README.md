# Hướng dẫn Khởi tạo Dashboard AdventureWorks trên Apache Superset

Thư mục này chứa các kịch bản Python giúp tự động thiết lập và cấu hình 5 Dashboard phân tích dữ liệu trên Apache Superset tương ứng với 5 chương phân tích của dự án AdventureWorks.

---

## 1. Cấu trúc Thư mục

```text
superset_bootstrap/
├── README.md                      # Hướng dẫn chạy và lưu ý quan trọng (file này)
├── bootstrap_common.py            # Module chứa API client, định dạng metric, bộ lọc và layout
├── bootstrap_all_dashboards.py    # Script chạy tự động gom cả 5 dashboard
├── bootstrap_chapter_1_business_health.py      # Dashboard Chương 1
├── bootstrap_chapter_2_growth_sources.py       # Dashboard Chương 2 (Chỉ B2C)
├── bootstrap_chapter_3_sustainable_growth.py   # Dashboard Chương 3
├── bootstrap_chapter_4_product_value.py        # Dashboard Chương 4
├── bootstrap_chapter_5_macro_behavior.py       # Dashboard Chương 5
├── sql/                           # Chứa các câu lệnh SQL khởi tạo View bổ trợ
│   ├── chapter_1_views.sql
│   ├── chapter_2_views.sql
│   ├── chapter_3_views.sql
│   ├── chapter_4_views.sql
│   └── chapter_5_views.sql
└── analytics_exports/             # Chứa script xuất kết quả mô hình máy học (ML)
    ├── export_chapter_3_model_results.py
    ├── export_chapter_4_results.py
    └── export_chapter_5_model_results.py
```

---

## 2. Các điểm cần lưu ý trước khi chạy

### Yêu cầu về môi trường và tài khoản truy cập:
- **Apache Superset**: Phải đang chạy tại cổng `8088` (Truy cập bằng `http://localhost:8088` hoặc `http://superset:8088` trong Docker).
  - Tài khoản Admin mặc định: `admin` / `admin`.
- **Cơ sở dữ liệu PostgreSQL**: 
  - Host trong Docker: `postgres_dwh:5432`
  - Cơ sở dữ liệu: `adventureworks_dwh`
  - Tài khoản: `postgres` / `postgres`
- **Môi trường chạy Script**: Nên chạy trực tiếp bên trong container `analytics_runner` vì đã được cấu hình sẵn thư viện (Pandas, Scikit-Learn, XGBoost, Statsmodels, Requests, SQLAlchemy, Psycopg2).

### Lưu ý về nghiệp vụ & kỹ thuật của từng chương:
- **Chương 1 (Business Health)**: Sử dụng thêm định mức doanh số (Sales Quota) của nhân sự được định nghĩa từ view `mart.vw_ch1_quota_quarterly` và `mart.vw_ch1_employee_quota`.
- **Chương 2 (Growth Sources)**: Chỉ tập trung phân tích **Internet Sales / B2C** theo yêu cầu (loại bỏ Reseller/B2B). Script sử dụng dữ liệu từ view `ml.vw_territory_analysis_dashboard` và bảng phân cụm `ml.territory_cluster_result`.
- **Chương 3 (Sustainable Growth)**:
  - Sử dụng kết quả dự báo Churn và phân nhóm RFM.
  - Sử dụng view `ml.vw_ch3_customer_actions` để hiển thị danh sách hành động đề xuất của các khách hàng VIP có nguy cơ rời bỏ cao nhất (tránh việc bảng bị trống khi không có khách hàng vượt ngưỡng mặc định).
- **Chương 4 (Product Value)**:
  - Cần chạy phân tích kết hợp giỏ hàng (Market Basket Analysis) thông qua file `precompute_mba.py` ở thư mục gốc trước khi chạy bootstrap để có dữ liệu `ml.association_rules`.
  - Phân tích rủi ro kho hàng được lấy từ bảng `mart.mart_inventory_risk` sử dụng cột `gross_margin` (không sử dụng `gross_margin_pct` do cấu trúc bảng).
- **Chương 5 (Macro Behavior)**:
  - Sử dụng view `ml.vw_ch5_category_retention` được tạo từ ma trận dịch chuyển mua sắm (Switching Matrix) để hiển thị chính xác tỷ lệ giữ chân khách hàng (retention rate) của từng danh mục sản phẩm thay vì bảng category share thông thường.

---

## 3. Các bước thực hiện chạy hệ thống

### Trường hợp 1: Cơ sở dữ liệu đã có sẵn dữ liệu phân tích (DWH đã được populate)
Bạn chỉ cần thực hiện các bước sau để đăng ký view bổ sung, xuất kết quả mô hình bổ trợ và dựng Dashboard:

#### Bước 1.1: Tạo các View SQL bổ trợ trong PostgreSQL
Chạy lệnh sau để import toàn bộ các SQL views vào cơ sở dữ liệu DWH:
```bash
docker compose exec analytics_runner python -c "
from src.common.database import get_dwh_engine
from sqlalchemy import text
eng = get_dwh_engine()
for ch in [1, 2, 3, 5]:
    sql = open(f'superset_bootstrap/sql/chapter_{ch}_views.sql').read()
    with eng.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
print('Đã khởi tạo thành công các SQL views!')
"
```

#### Bước 1.2: Xuất kết quả phân tích mô hình bổ trợ (ML Exports)
Chạy các script xuất dữ liệu bổ sung (như độ quan trọng tính năng SHAP, hệ số OLS, đề xuất hành động):
```bash
docker compose exec analytics_runner python superset_bootstrap/analytics_exports/export_chapter_3_model_results.py
docker compose exec analytics_runner python superset_bootstrap/analytics_exports/export_chapter_4_results.py
docker compose exec analytics_runner python superset_bootstrap/analytics_exports/export_chapter_5_model_results.py
```

#### Bước 1.3: Chạy khởi tạo tất cả Dashboard trên Superset
```bash
docker compose exec analytics_runner python superset_bootstrap/bootstrap_all_dashboards.py
```

---

### Trường hợp 2: Cơ sở dữ liệu mới hoàn toàn (Clean DB / Thiết lập lại từ đầu)
Nếu cơ sở dữ liệu trống hoặc bạn muốn cập nhật dữ liệu phân tích mới nhất, bạn **BẮT BUỘC** phải chạy các Notebook phân tích trước để ghi nhận dữ liệu kết quả ban đầu vào PostgreSQL:

1. **Chương 2**: Chạy hết Notebook `02_territory_analysis_revised.ipynb` (để tạo các bảng `ml.territory_*`).
2. **Chương 3**: Chạy hết Notebook `03_Sustainable_Growth_v3.ipynb` (để huấn luyện mô hình Churn và xuất ra file `model.pkl` cùng các bảng `ml.customer_*`).
3. **Chương 4**: Chạy file `precompute_mba.py` ở thư mục gốc để sinh ra bảng luật kết hợp `ml.association_rules`.
4. **Chương 5**: Chạy hết Notebook `05_macro_behavior_analysis.ipynb` (để tạo các bảng dịch chuyển category và kịch bản vĩ mô).
5. **Sau đó**: Thực hiện tuần tự các bước như ở **Trường hợp 1** để hoàn thành việc cấu hình Dashboard.

---

## 4. Danh sách URL Dashboard đã xuất bản
Sau khi chạy thành công, các dashboard sẽ hoạt động tại các địa chỉ sau:

- **Chương 1 (Bức tranh sức khỏe)**:  
  👉 [http://localhost:8088/superset/dashboard/adventureworks-chapter-1-business-health/](http://localhost:8088/superset/dashboard/adventureworks-chapter-1-business-health/)
- **Chương 2 (Nguồn tăng trưởng B2C)**:  
  👉 [http://localhost:8088/superset/dashboard/adventureworks-chapter-2-growth-sources/](http://localhost:8088/superset/dashboard/adventureworks-chapter-2-growth-sources/)
- **Chương 3 (Tính bền vững)**:  
  👉 [http://localhost:8088/superset/dashboard/adventureworks-chapter-3-sustainable-growth/](http://localhost:8088/superset/dashboard/adventureworks-chapter-3-sustainable-growth/)
- **Chương 4 (Giá trị danh mục sản phẩm)**:  
  👉 [http://localhost:8088/superset/dashboard/adventureworks-chapter-4-product-value/](http://localhost:8088/superset/dashboard/adventureworks-chapter-4-product-value/)
- **Chương 5 (Tác động vĩ mô)**:  
  👉 [http://localhost:8088/superset/dashboard/adventureworks-chapter-5-macro-behavior/](http://localhost:8088/superset/dashboard/adventureworks-chapter-5-macro-behavior/)

# Hệ Thống Phân Tích Dữ Liệu AdventureWorks Data Analytics

Dự án này xây dựng một môi trường phân tích dữ liệu (BI & ML) hoàn chỉnh trên nền tảng Docker, kế thừa từ cơ sở dữ liệu giao dịch AdventureWorks (PostgreSQL OLTP) và mở rộng sang cơ sở dữ liệu phân tích (PostgreSQL DWH) tích hợp các chỉ số kinh tế vĩ mô để dự báo doanh thu và phân tích churn khách hàng.

---

## 1. Cấu Trúc Thư Mục Dự Án
Cấu trúc dự án được thiết kế theo mô hình **SQL-first ETL** kết hợp với **Python Orchestration & Machine Learning** như sau:

```text
Project2/
├── docker-compose.yml          # Khai báo các container (OLTP, DWH, Superset, Analytics Runner)
├── .env                        # Biến môi trường cấu hình port/user/database
├── .env.example                # File mẫu cấu hình biến môi trường
├── Makefile                    # Lệnh rút gọn để vận hành hệ thống
├── README.md                   # Tài liệu hướng dẫn sử dụng (file này)
│
├── docker/                     # Dockerfile & script cho từng dịch vụ
│   ├── postgres_oltp/          # Cơ sở dữ liệu nguồn AdventureWorks OLTP
│   ├── postgres_dwh/           # Cơ sở dữ liệu phân tích DWH
│   ├── superset/               # Giao diện trực quan hóa Apache Superset
│   └── analytics/              # Môi trường chạy Python (ingestion/ETL/ML)
│
├── config/                     # File cấu hình YAML
│   ├── database.yml            # Kết nối database
│   ├── macro_sources.yml       # Khai báo cấu trúc file vĩ mô
│   └── models.yml              # Tham số và features của các mô hình ML
│
├── data/                       # Dữ liệu CSV & mô hình
│   ├── adventureworks/csv/     # CSV nguồn AdventureWorks (nếu có)
│   ├── macro/                  # Thư mục chứa dữ liệu vĩ mô (raw/processed)
│   └── generate_macro_data.py  # Script sinh dữ liệu vĩ mô giả lập lịch sử
│
├── sql/                        # Tập lệnh SQL thực thi chuyển dịch và làm sạch
│   ├── init/                   # Script khởi tạo schema, tables khi tạo container DWH
│   ├── staging/                # SQL làm sạch dữ liệu trong schema staging
│   ├── dwh/                    # SQL nạp dữ liệu vào dimension & fact tables
│   ├── marts/                  # SQL xây dựng các Data Mart phân tích
│   ├── features/               # SQL tạo features phục vụ ML
│   └── quality/                # SQL kiểm tra chất lượng dữ liệu (DQ check)
│
├── src/                        # Mã nguồn Python điều phối và xử lý ML
│   ├── common/                 # Module dùng chung (cấu hình, kết nối db)
│   ├── ingestion/macro/        # Ingestion dữ liệu kinh tế vĩ mô
│   ├── etl/                    # Điều phối pipeline ETL (extract -> transform -> load)
│   ├── marts/                  # Rebuild các Data Mart phân tích
│   ├── ml/                     # Huấn luyện và dự báo Machine Learning
│   │   ├── vip_churn/          # Mô hình dự báo churn khách hàng VIP
│   │   ├── revenue_forecast/   # Mô hình dự báo doanh thu khu vực
│   │   └── run_ml.py           # Orchestrator chạy toàn bộ pipeline ML
│   └── data_quality.py         # Script chạy DQ checks tự động
│
├── models/                     # Thư mục lưu trữ model artifacts (.pkl) và metrics
├── notebooks/                  # Jupyter notebooks cho EDA và thử nghiệm mô hình
├── superset/exports/           # Sao lưu các cấu hình Dashboard của Superset
├── tests/                      # Kiểm thử code
└── logs/                       # Log lịch sử vận hành
```

---

## 2. Hướng Dẫn Vận Hành Dự Án

### Bước 1: Khởi động hệ thống (Docker Containers)
Sử dụng `Makefile` để build và khởi động toàn bộ các dịch vụ (PostgreSQL OLTP, PostgreSQL DWH, Superset, Analytics Runner):
```bash
make up
```
*Hệ thống sẽ tự động khởi tạo dữ liệu AdventureWorks OLTP từ `install.sql` và cấu hình sẵn các schema cần thiết (`staging`, `dwh`, `mart`, `feature`, `ml`, `audit`) trên PostgreSQL DWH.*

### Bước 2: Chạy toàn bộ Pipeline (End-to-End)
Chạy toàn bộ quy trình từ tải dữ liệu vĩ mô, chạy ETL sang DWH, tạo Data Mart, kiểm tra chất lượng dữ liệu và huấn luyện mô hình ML bằng một lệnh duy nhất:
```bash
make run-all
```

Hoặc bạn có thể chạy thủ công từng bước để theo dõi chi tiết:
1. **Nạp dữ liệu kinh tế vĩ mô**:
   ```bash
   make ingest-macro
   ```
2. **Chạy ETL chuyển từ OLTP sang DWH**:
   ```bash
   make etl
   ```
3. **Xây dựng các Data Mart**:
   ```bash
   make build-marts
   ```
4. **Kiểm tra chất lượng dữ liệu**:
   ```bash
   make quality-check
   ```
5. **Huấn luyện mô hình & Tạo bảng dự báo**:
   ```bash
   make train-all
   ```

---

## 3. Workflow quá trình ETL (cụ thể file nào dùng để làm gì)
Luồng chạy ETL (Extract - Transform - Load) trong dự án được điều phối tập trung bởi tệp tin run_etl.py theo các bước tuần tự như sau:                               
                                                                                                                                                                           
    graph TD                                                                                                                                                               
        A[Bắt đầu ETL] --> B[1. Trích xuất: extract_to_staging.py]                                                                                                         
        B --> C[2. Làm sạch: clean_sales_staging.sql]                                                                                                                      
        C --> D[3. Nạp Bảng Chiều: dim_customer.sql & dim_product.sql]                                                                                                     
        D --> E[4. Nạp Bảng Sự Kiện: fact_internet_sales.sql]                                                                                                              
        E --> F[Hoàn thành ETL]                                                                                                                                            
                                                                                                                                                                           
        subgraph Logging & Audit                                                                                                                                           
            B & C & D & E -.->|Ghi nhật ký trạng thái| LogTable[audit.etl_log]                                                                                             
        end                                                                                                                                                                
  
  ### Chi tiết các bước trong Flow:
  
  1. Bước 1: Trích xuất dữ liệu (Extraction Phase)
      • Script thực thi: extract_to_staging.py 
      • Nhiệm vụ: Đọc các bảng dữ liệu giao dịch cần thiết từ database nguồn PostgreSQL OLTP, tự động chuyển tất cả tên cột về chữ thường (lowercase) để đảm bảo tính đồng 
      nhất trên PostgreSQL DWH, sau đó ghi đè trực tiếp vào các bảng tương ứng trong schema  staging  của database phân tích.
  2. Bước 2: Làm sạch dữ liệu tạm (Cleaning/Transformation)
      • Script thực thi: clean_sales_staging.sql 
      • Nhiệm vụ: Lọc bỏ các bản ghi không hợp lệ trong schema  staging  (ví dụ: các dòng chi tiết đơn hàng có số lượng mua  orderqty <= 0 , đơn giá  unitprice < 0 , hoặc 
      tiêu đề đơn hàng thiếu ngày tháng  orderdate ).
  3. Bước 3: Nạp các bảng chiều (Loading Dimensions)
      • Script thực thi: dim_customer.sql & dim_product.sql 
      • Nhiệm vụ:
          •  dim_customer : Thực hiện kết nối (JOIN) bảng customer và person ở staging, tính toán ghép nối chuỗi để tạo trường  full_name  đại diện cho cả khách hàng cá   
          nhân và cửa hàng đại lý.
          •  dim_product : Chuẩn hóa danh mục sản phẩm bằng cách JOIN bảng product, subcategory, và category ở staging để hình thành chiều phân cấp sản phẩm hoàn chỉnh.   
  
  4. Bước 4: Nạp bảng sự kiện (Loading Fact Table)
      • Script thực thi: fact_internet_sales.sql 
      • Nhiệm vụ: Thực hiện JOIN các bảng chi tiết đơn hàng ở staging với hai bảng chiều  dwh.dim_customer  và  dwh.dim_product  để thay thế mã định danh bằng các         
      surrogate keys trong kho dữ liệu DWH. Đồng thời tính toán động các trường dữ liệu tính toán (như mã hóa chuỗi  sales_order_number , trừ chiết khấu sản phẩm để ra    
      doanh thu thực tế  line_total , và lợi nhuận gộp  gross_profit ) trước khi nạp vào bảng  dwh.fact_internet_sales .
  5. Giám sát & Ghi nhận nhật ký (Auditing & Logging)
      • Cơ chế: Trong suốt quá trình thực thi, mỗi bước khi Bắt đầu, Hoàn thành hoặc Thất bại đều được hàm  log_etl_step  ghi nhận trực tiếp vào bảng  audit.etl_log  kèm  
      theo mốc thời gian chi tiết và thông báo lỗi (nếu có) để phục vụ mục đích kiểm soát vận hành (Data Quality & Operations Monitoring).

---

## 4. Vai Trò Của Các Thành Phần Machine Learning

### 1. Dự báo Churn Khách hàng VIP (`vip_churn`)
* **Định nghĩa VIP**: Khách hàng thuộc nhóm đóng góp doanh thu lớn nhất (quan sát trong lịch sử).
* **Định nghĩa Churn**: Khách hàng không mua lại trong vòng 6 tháng tiếp theo.
* **Mô hình**: `RandomForestClassifier` huấn luyện dựa trên các đặc trưng Recency, Frequency, Monetary (RFM), thời gian gắn bó (Tenure), và tỷ lệ discount trung bình.
* **Đầu ra**: Lưu trữ xác suất churn của từng khách hàng vào bảng `ml.vip_churn_predictions`.

### 2. Dự báo Doanh thu Khu vực (`revenue_forecast`)
* **Mục tiêu**: Dự báo doanh thu 3 tháng tới của từng vùng lãnh thổ.
* **Mô hình**: `XGBRegressor` kết hợp lags doanh thu lịch sử với các yếu tố vĩ mô ngoại sinh như chỉ số CPI, lãi suất, giá dầu thế giới, và tỷ giá hối đoái quốc gia.
* **Đầu ra**: Lưu trữ doanh thu dự báo và thực tế vào bảng `ml.revenue_forecast_predictions`.

---

## 5. Khởi tạo trực quan hóa trên Apache Superset
1. Truy cập Apache Superset tại: [http://localhost:8088](http://localhost:8088)
2. Đăng nhập bằng tài khoản admin:
   * **Username**: `admin`
   * **Password**: `admin`
3. Tạo kết nối Database đến PostgreSQL DWH:
   * **Host**: `postgres_dwh`
   * **Port**: `5432`
   * **Database**: `adventureworks_dwh`
   * **Username**: `postgres`
   * **Password**: `postgres`
4. Dựng dashboard trực quan từ các nguồn dữ liệu trong schema `mart` và `ml`.

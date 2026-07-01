# PLAN TRIỂN KHAI CHƯƠNG 6 – PREDICTIVE ANALYTICS

## 1. Mục tiêu tổng thể

Chương 6 được xây dựng theo hai nhánh song song:

1. **Dự báo doanh thu và giải thích nguồn đóng góp**
   - Tìm mô hình dự báo doanh thu ổn định nhất.
   - Dự báo doanh thu trong 1–3 tháng tới.
   - Xác định category và product nào đóng góp vào mức tăng hoặc giảm doanh thu.
   - Bảo đảm tổng dự báo ở cấp product, category và toàn doanh nghiệp khớp nhau.

2. **Dự báo khách hàng rời bỏ**
   - Xác định khách hàng có nguy cơ churn.
   - Ưu tiên nhóm khách hàng VIP hoặc có giá trị cao.
   - Đưa ra danh sách khách hàng cần can thiệp sớm.

---

# 2. Flow tổng thể

```text
Dữ liệu Data Warehouse
        │
        ├───────────────────────────────────────┐
        │                                       │
        ▼                                       ▼
Nhánh doanh thu – sản phẩm             Nhánh khách hàng
        │                                       │
Rolling backtest nhiều model            Tạo Customer Snapshot
        │                                       │
Chọn model tốt nhất                      Time-based Split
        │                                       │
Forecast doanh thu 1–3 tháng             So sánh nhiều model churn
        │                                       │
Forecast category revenue                Chọn model tốt nhất
        │                                       │
Forecast product revenue                 Score snapshot mới nhất
        │                                       │
Reconcile Total–Category–Product         Danh sách churn risk
        │
Xác định category/product tăng giảm
và mức đóng góp doanh thu
```

---

# 3. Nhánh 1 – Dự báo doanh thu

## 3.1. Chuẩn bị dữ liệu

Grain đề xuất:

```text
Month × Territory
```

Target:

```text
Revenue của tháng tiếp theo
```

Feature chính:

- Revenue lag 1, 2, 3, 6, 12 tháng.
- Rolling mean 3 và 6 tháng.
- Revenue growth.
- Seasonality: month, quarter, month_sin, month_cos.
- Territory.
- CPI, lãi suất, tỷ giá nếu có.
- Promotion và discount nếu phù hợp.

## 3.2. Mô hình cần thử

- Seasonal Naive.
- Ridge Regression.
- Random Forest Regressor.
- Gradient Boosting.
- XGBoost.
- SARIMAX.
- ARDL nếu dữ liệu vĩ mô đủ dài.

## 3.3. Cách đánh giá

Không chỉ dùng một train/test split. Dùng rolling time-series backtest.

Ví dụ:

```text
Fold 1: Train đến 2024-06, test 2024-07 → 2024-09
Fold 2: Train đến 2024-09, test 2024-10 → 2024-12
Fold 3: Train đến 2024-12, test 2025-01 → 2025-03
```

Metric:

- WAPE.
- MAE.
- RMSE.
- Forecast Bias.
- Độ lệch chuẩn WAPE giữa các fold.

## 3.4. Chọn model tốt nhất

Ưu tiên:

1. WAPE trung bình thấp.
2. Bias gần 0.
3. Kết quả ổn định giữa các fold.
4. Không lỗi ở nhiều territory.

Có thể chọn:

- Một model tốt nhất cho toàn bộ doanh nghiệp.
- Hoặc model tốt nhất riêng cho từng territory.

## 3.5. Forecast thật sự

Sau khi chọn model:

1. Fit lại trên toàn bộ dữ liệu lịch sử.
2. Forecast 1–3 tháng sau tháng cuối cùng.
3. Ghi thêm:
   - Predicted Revenue.
   - Change Amount.
   - Change Percentage.
   - Forecast Lower Bound.
   - Forecast Upper Bound.
   - Trend Label.

Trend Label:

```text
Strong Increase
Moderate Increase
Stable
Moderate Decline
Strong Decline
```

---

# 4. Nhánh 1.1 – Dự báo Category nào tạo ra doanh thu

## 4.1. Grain

```text
Month × Territory × Category
```

Target chính:

```text
Category Revenue
```

Không chỉ dự báo Units Sold vì mục tiêu là giải thích doanh thu.

## 4.2. Feature

- Category revenue lag 1, 2, 3, 6, 12.
- Category units lag.
- Average selling price.
- Discount rate.
- Rolling mean.
- Category share.
- Territory.
- Seasonality.
- CPI và lãi suất nếu cần.

## 4.3. Đầu ra

- Forecast Month.
- Territory.
- Category.
- Predicted Category Revenue.
- Predicted Units.
- Revenue Change.
- Revenue Change Percentage.
- Contribution Percentage.
- Trend.

Công thức:

```text
Contribution Percentage
= Predicted Category Revenue / Predicted Total Revenue
```

---

# 5. Nhánh 1.2 – Dự báo Product nào tăng hoặc giảm

## 5.1. Grain

```text
Month × Territory × Product
```

## 5.2. Không dùng slope làm dự báo chính

Slope 6 tháng chỉ nên dùng làm feature mô tả. Không xem slope là forecast.

## 5.3. Mô hình đề xuất

Dùng pooled model cho toàn bộ product:

- XGBoost.
- LightGBM.
- Random Forest làm baseline.

Feature:

- Revenue lag 1, 2, 3, 6, 12.
- Units lag 1, 3, 6, 12.
- Rolling mean 3 và 6 tháng.
- Average selling price.
- Discount rate.
- Category.
- Territory.
- Product age.
- Months since last sale.
- Seasonality.
- CPI và lãi suất nếu có.

## 5.4. Đầu ra

- Forecast Month.
- Product.
- Category.
- Territory.
- Predicted Revenue.
- Predicted Units.
- Revenue Change.
- Revenue Change Percentage.
- Contribution Percentage.
- Trend.

Xếp hạng product theo:

- Mức tăng doanh thu dự báo.
- Mức giảm doanh thu dự báo.
- Tỷ trọng đóng góp.
- Mức doanh thu tối thiểu để tránh sản phẩm quá nhỏ đứng đầu.

---

# 6. Forecast Reconciliation

Mục tiêu:

```text
Tổng Product Forecast
= Tổng Category Forecast
= Total Revenue Forecast
```

## 6.1. Điều chỉnh Category

```text
Adjusted Category Forecast
= Raw Category Forecast
× Total Forecast
/ Tổng Raw Category Forecast
```

## 6.2. Điều chỉnh Product

```text
Adjusted Product Forecast
= Raw Product Forecast
× Adjusted Category Forecast
/ Tổng Raw Product Forecast trong Category
```

Sau bước này có thể kể câu chuyện:

> Doanh thu kỳ tới được dự báo tăng 12%, chủ yếu đến từ Bikes và Components. Các product đóng góp tăng trưởng lớn nhất là A, B và C.

---

# 7. Nhánh 2 – Customer Churn Prediction

## 7.1. Grain

```text
Customer × Snapshot Month
```

## 7.2. Feature

- Recency.
- Frequency.
- Monetary.
- Average Order Value.
- Customer Tenure.
- Number of Categories.
- Promotion Usage.
- Discount Usage.
- Gross Profit Contribution.
- Recent Order Decline.
- Last Purchased Category.
- Territory.
- Previous Segment.

## 7.3. Tạo nhãn churn

Ví dụ:

```text
Khách hàng được xem là churn
nếu không phát sinh giao dịch trong 3 hoặc 6 tháng tiếp theo.
```

Feature chỉ dùng dữ liệu trước snapshot.

Label dùng dữ liệu sau snapshot.

## 7.4. Chia dữ liệu

Không dùng random split.

Dùng:

```text
Train: snapshot cũ
Validation: snapshot tiếp theo
Test: snapshot mới nhất có đủ thời gian quan sát nhãn
```

## 7.5. Mô hình cần thử

- Logistic Regression baseline.
- Random Forest.
- Gradient Boosting.
- XGBoost.
- LightGBM.

## 7.6. Metric

- PR-AUC.
- ROC-AUC.
- Recall.
- F1-score.
- Recall@Top-K.
- Lift@Top-K.

Không mặc định threshold 0.5.

Có thể:

- Chọn threshold đạt Recall mục tiêu.
- Hoặc chọn Top 10%–20% khách hàng có rủi ro cao nhất.

## 7.7. Scoring

Chỉ score snapshot mới nhất chưa có label.

Đầu ra:

- Snapshot Month.
- Customer Key.
- VIP Flag.
- Churn Probability.
- Risk Level.
- Main Risk Factor.
- Model Version.
- Predicted At.

---

# 8. Các bảng đầu ra

## 8.1. Tổng doanh thu

```text
ml.revenue_forecast_predictions
```

Grain:

```text
Forecast Month × Territory
```

## 8.2. Category

```text
ml.category_revenue_forecast
```

Grain:

```text
Forecast Month × Territory × Category
```

## 8.3. Product

```text
ml.product_revenue_forecast
```

Grain:

```text
Forecast Month × Territory × Product
```

## 8.4. Churn

```text
ml.customer_churn_predictions
```

Grain:

```text
Snapshot Month × Customer
```

Các bảng forecast nên chứa:

- Raw Prediction.
- Adjusted Prediction.
- Change Amount.
- Change Percentage.
- Contribution Percentage.
- Trend.
- Model Version.
- Forecast Created At.

---

# 9. Dashboard Superset

## 9.1. Revenue Forecast

- Actual vs Forecast.
- Forecast theo Territory.
- Forecast Growth.
- Forecast Interval.
- Khu vực tăng hoặc giảm mạnh.

## 9.2. Category Contribution

- Category Revenue Forecast.
- Category Contribution Percentage.
- Category tăng hoặc giảm mạnh.
- Category share theo thời gian.

## 9.3. Product Contribution

- Top product đóng góp tăng trưởng.
- Top product suy giảm.
- Product forecast theo territory.
- Product contribution waterfall.

## 9.4. Customer Churn

- Tổng số khách hàng churn risk cao.
- VIP churn risk.
- Churn risk theo territory.
- Danh sách khách hàng cần can thiệp.
- Main risk factor.

---

# 10. Thứ tự triển khai

1. Chuẩn hóa dataset doanh thu.
2. Xây rolling backtest.
3. So sánh các model doanh thu.
4. Chọn và refit model tốt nhất.
5. Forecast doanh thu 1–3 tháng.
6. Xây dataset category revenue.
7. Forecast category.
8. Xây dataset product revenue.
9. Forecast product.
10. Reconcile Total–Category–Product.
11. Xây Customer Snapshot.
12. Tạo nhãn churn.
13. Train và đánh giá churn model.
14. Score snapshot mới nhất.
15. Ghi kết quả vào PostgreSQL.
16. Xây dashboard Superset.

---

# 11. Những phần cần sửa trong notebook hiện tại

- Không hard-code ARDL hoặc GBC là model cuối cùng.
- Không dùng một train/test split để chọn model.
- Không dùng test vừa chọn model vừa báo cáo kết quả cuối.
- Không dùng category units để giải thích revenue forecast.
- Không dùng slope product làm forecast.
- Không để Total, Category và Product forecast độc lập.
- Không random split dữ liệu churn.
- Không predict churn trên toàn bộ lịch sử.
- Không dùng `if_exists="replace"` khi ghi bảng production.
- Cần lưu model, preprocessor, feature list, metric và model version.

---

# 12. Kết quả cuối cùng cần đạt

Chương 6 phải trả lời được:

1. Doanh thu 1–3 tháng tới tăng hay giảm?
2. Territory nào đóng góp chính vào biến động đó?
3. Category nào tạo ra mức tăng hoặc giảm doanh thu?
4. Product nào đóng góp nhiều nhất?
5. Khách hàng nào có nguy cơ rời bỏ?
6. Doanh nghiệp cần chuẩn bị và hành động như thế nào?

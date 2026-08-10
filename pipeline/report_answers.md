# Báo cáo Phân tích Dữ liệu Log (Phần A — Data Pipeline)

Báo cáo chi tiết trả lời 4 câu hỏi nghiệp vụ từ Phòng CNTT — Công ty Tài chính Sao Đỏ dựa trên kết quả chạy pipeline xử lý log 7 ngày.

---

## 📊 Câu hỏi 1: Service nào có nhiều lỗi (level=ERROR) nhất trong 7 ngày?
- **Kết quả**: *[Sẽ được điền sau khi chạy pipeline]*
- **Bảng tổng hợp**:
| Service | Tổng số lỗi (ERROR) | Tỷ lệ (%) |
| :--- | :---: | :---: |
| ... | ... | ... |
- **Nhận xét & Phân tích**: ...

---

## 📊 Câu hỏi 2: Số lượng lỗi theo ngày của toàn hệ thống — ngày nào bất thường?
- **Kết quả**: *[Sẽ được điền sau khi chạy pipeline]*
- **Bảng thống kê theo ngày**:
| Ngày | Số lượng ERROR | Số lượng WARN | Tổng số log | Ghi chú |
| :---: | :---: | :---: | :---: | :--- |
| ... | ... | ... | ... | ... |
- **Ngày bất thường (Spike / Anomaly)**: ...
- **Nguyên nhân nghi vấn**: ...

---

## 📊 Câu hỏi 3: Top 3 loại lỗi (message / error code) phổ biến nhất, thuộc service nào?
- **Kết quả**: *[Sẽ được điền sau khi chạy pipeline]*
- **Bảng Top 3 lỗi**:
| Hạng | Loại lỗi / Error Message pattern | Service liên quan | Số lần xuất hiện | Tỷ lệ trong tổng ERROR |
| :---: | :--- | :--- | :---: | :---: |
| 1 | ... | ... | ... | ... |
| 2 | ... | ... | ... | ... |
| 3 | ... | ... | ... | ... |

---

## 📊 Câu hỏi 4: Thống kê bản ghi bị loại/sửa trong bước làm sạch dữ liệu
- **Tổng số bản ghi ban đầu**: ...
- **Số bản ghi hợp lệ (Cleaned)**: ...
- **Số bản ghi bị loại (Quarantine / Discarded)**: ...
- **Phân loại các vấn đề dữ liệu phát hiện**:
| STT | Loại vấn đề dữ liệu | Số lượng bản ghi | Hành động xử lý (Sửa / Loại bỏ) | Lý do xử lý |
| :---: | :--- | :---: | :---: | :--- |
| 1 | Malformed JSON (dòng log không đúng cú pháp JSON) | ... | Loại bỏ | Không thể khôi phục dữ liệu tin cậy |
| 2 | Missing timestamp / Invalid format | ... | Sửa/Loại | ... |
| 3 | Null hoặc Invalid log level | ... | Sửa/Loại | ... |
| 4 | Trùng lặp (Duplicate log lines) | ... | Khử trùng lặp | ... |

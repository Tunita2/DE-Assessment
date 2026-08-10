# AI Work Log — Data Engineer Assessment (Xbrain / TechX)

Nhật ký sử dụng AI có kiểm chứng trong quá trình thực hiện POC Data Engineer & Mini Knowledge Base.

> **Nguyên tắc**: 
> - Chọn lọc 8–15 entry có ý nghĩa nhất về mặt kỹ thuật và ra quyết định.
> - Trung thực ghi lại các trường hợp AI đề xuất sai/chưa tối ưu và quá trình kiểm chứng, sửa đổi.
> - Tất cả code/tài liệu đưa vào bài nộp đều được hiểu rõ và kiểm chứng thực tế.

---

## 📋 Bảng Nhật ký AI (AI Work Log)

| STT | Việc (Task) | Prompt | Output & đánh giá | Verify & sửa |
| :---: | :--- | :--- | :--- | :--- |
| **01** | Khởi tạo cấu trúc repository & tài liệu dự án | *"Tạo cấu trúc thư mục repo cho bài POC DE theo đúng tài liệu mô tả Xbrain_Assessment_DE_01_Domain_POC và Bài 2 AI Proficiency"* | **AI trả về:** Đầy đủ các thư mục `pipeline/`, `kb/`, `design/`, `sop/`, `ai_proficiency/`, `README.md`, `AI_WORKLOG.md`.<br>**Đánh giá:** Đúng cấu trúc yêu cầu của đề bài, phân tách rõ ràng giữa code pipeline, KB và báo cáo. | **Cách kiểm chứng:** Đối chiếu với bảng thư mục mục *Nộp bài* trong file đề bài Bài 1 và yêu cầu nộp chung Bài 2.<br>**Đã sửa:** Bổ sung thêm `.gitignore` chuẩn Python và `requirements.txt`. |


---

## 🔍 Ghi chú & Đúc kết kinh nghiệm sử dụng AI
- **Verification First**: Luôn đối chiếu code được sinh với dữ liệu thực tế (`data/app_logs_7days.jsonl` và `data/docs/`) trước khi chấp nhận.
- **Edge cases**: AI thường giả định dữ liệu sạch hoàn hảo; cần chủ động yêu cầu xử lý malformed JSON, missing fields, timestamp parsing errors.

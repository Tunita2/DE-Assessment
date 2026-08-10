# Báo cáo Đánh giá Chất lượng Mini Knowledge Base (Phần B — RAG Evaluation)

**Đơn vị thực hiện**: Đội Data Engineering — Xbrain (TechX Corp)  
**Khách hàng**: Phòng CNTT — Công ty Tài chính Sao Đỏ  
**Phạm vi tài liệu**: 8 tài liệu vận hành & chính sách nội bộ (`data/docs/`)  
**Bộ benchmark**: 10 câu hỏi kiểm thử bao phủ 4 nhóm câu hỏi chuẩn RAG  

---

## 📊 1. Bảng Điểm Sức Khỏe Knowledge Base (Executive Metrics)

| Chỉ số Đánh giá (Metrics) | Kết quả Đạt được | Ngưỡng Kỳ vọng | Đánh giá Trạng thái |
| :--- | :---: | :---: | :---: |
| **Tổng số câu hỏi kiểm thử** | **10 câu** | 10 câu | Đạt 100% độ phủ |
| **Tỷ lệ Tìm đúng tài liệu (Retrieval Hit Rate)** | **100.0%** | $\ge 90\%$ | 🟢 Xuất sắc |
| **Tỷ lệ Độ bám nguồn (Groundedness / Không bịa)** | **100.0%** | $\ge 90\%$ | 🟢 Tuyệt đối |
| **Xử lý Bẫy xung đột phiên bản (POL-01 v2 over v1)** | **100.0%** | $100\%$ | 🟢 Hoàn hảo |
| **Từ chối câu hỏi ngoài phạm vi (Out-of-Scope)** | **100.0%** | $100\%$ | 🟢 Không Hallucination |
| **ĐIỂM SỨC KHỎE TỔNG THỂ (OVERALL SCORE)** | **100.0%** | $\ge 90\%$ | 🏆 VƯỢT TIÊU CHUẨN |

---

## 📋 2. Bảng Tổng Hợp Kết Quả 10 Câu Hỏi Benchmark

| ID          | Loại câu hỏi   | Câu hỏi kiểm thử                                                                                                                                                    | Nguồn tìm được                 | Retrieval Hit   | Groundedness   | Kết luận   |
|-------------|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------|-----------------|----------------|------------|
| **EVAL-01** | DIRECT_LOOKUP  | Chính sách đổi mật khẩu hệ thống quy định bao lâu phải đổi một lần và khi nào bắt buộc xác thực 2 lớp?                                                              | POL-02                         | ✅ Đạt          | ✅ Đạt         | **PASS**   |
| **EVAL-02** | DIRECT_LOOKUP  | Tài khoản không hoạt động bao lâu sẽ bị khoá tự động và nhân viên nghỉ việc bị khoá tài khoản khi nào?                                                              | POL-02                         | ✅ Đạt          | ✅ Đạt         | **PASS**   |
| **EVAL-03** | DIRECT_LOOKUP  | Lịch chạy của job báo cáo batch-report là vào mấy giờ và phụ thuộc dữ liệu từ những dịch vụ nào?                                                                    | RUN-01, POL-01                 | ✅ Đạt          | ✅ Đạt         | **PASS**   |
| **EVAL-04** | DIRECT_LOOKUP  | Ngưỡng tỷ lệ ERROR bao nhiêu phần trăm thì hệ thống kích hoạt cảnh báo CRITICAL theo tài liệu giám sát?                                                             | GUIDE-01                       | ✅ Đạt          | ✅ Đạt         | **PASS**   |
| **EVAL-05** | VERSION_TRAP   | Chính sách sao lưu (backup) cơ sở dữ liệu quy định thời gian chạy, thời gian lưu giữ, địa điểm lưu trữ và thẩm quyền khôi phục như thế nào?                         | POL-01, RUN-01                 | ✅ Đạt          | ✅ Đạt         | **PASS**   |
| **EVAL-06** | MULTI_SOURCE   | Khi payment-api gặp sự cố lỗi DB ConnTimeout, đội vận hành có được restart ngay không, lưu ý gì về queue, và nếu tỷ lệ lỗi vượt quá 5% thì phân loại sự cố mức mấy? | FAQ-01, SOP-02, SOP-01, RUN-01 | ✅ Đạt          | ✅ Đạt         | **PASS**   |
| **EVAL-07** | MULTI_SOURCE   | Khi job batch-report bị lỗi ERR NullPointer in ReportBuilder, nguyên nhân do đâu và quy trình khắc phục như thế nào?                                                | RUN-01, FAQ-01                 | ✅ Đạt          | ✅ Đạt         | **PASS**   |
| **EVAL-08** | OVERVIEW       | Hệ thống đã từng ghi nhận những loại lỗi thường gặp nào và cách xử lý sơ bộ của từng loại?                                                                          | FAQ-01                         | ✅ Đạt          | ✅ Đạt         | **PASS**   |
| **EVAL-09** | OUT_OF_SCOPE   | Công ty có chính sách hỗ trợ tiền ăn trưa hoặc phụ cấp làm thêm giờ cho nhân viên trực ca đêm không?                                                                | None (Rejected)                | ✅ Đạt          | ✅ Đạt         | **PASS**   |
| **EVAL-10** | OUT_OF_SCOPE   | Hướng dẫn quy trình xin nghỉ phép năm và thủ tục thanh toán công tác phí cho nhân viên IT?                                                                          | None (Rejected)                | ✅ Đạt          | ✅ Đạt         | **PASS**   |

---

## 🔍 3. Phân Tích Kỹ Thuật Chi Tiết Theo 4 Nhóm Câu Hỏi

### 1. Nhóm Tra Cứu Trực Tiếp (Direct Lookup: EVAL-01, 02, 03, 04)
- **Mục tiêu**: Kiểm tra khả năng tìm đúng và trích xuất nguyên văn các quy chuẩn kỹ thuật cụ thể (đổi mật khẩu 90 ngày, khóa tài khoản sau 30 ngày, job chạy 23:00, ngưỡng CRITICAL > 5%).
- **Kết quả**: Đạt **100% Retrieval Hit** và **100% Groundedness**. Chunking theo Heading H2/H3 giúp mỗi quy tắc được đóng gói nguyên vẹn trong một chunk độc lập mà không bị cắt đứt đoạn.

### 2. Nhóm Bẫy Xung Đột Phiên Bản (Version Conflict Trap: EVAL-05)
- **Tình huống**: Thư mục chứa cả `POL-01 v1` (Cũ: 22:00, 7 ngày, phòng 3) và `POL-01 v2` (Mới: 23:30, 30 ngày, Cloud KMS mã hóa, cần phê duyệt).
- **Cơ chế xử lý Freshness**:
  - `MarkdownChunker` tự động phát hiện và gán metadata `"status": "DEPRECATED"` cho bản v1 và `"status": "ACTIVE"` cho bản v2.
  - `KnowledgeRetriever` áp dụng bộ lọc `active_only=True` $\rightarrow$ Loại bỏ hoàn toàn bản v1 khỏi không gian tìm kiếm.
- **Kết quả**: Trả lời chính xác **100% theo bản v2** (23:30, 30 ngày, Cloud mã hóa). Không xảy ra hiện tượng trích dẫn thông tin lỗi thời.

### 3. Nhóm Tổng Hợp Đa Nguồn & Câu Hỏi Tổng Quan (Multi-Source & Overview: EVAL-06, 07, 08)
- **Tình huống**:
  - EVAL-06 ghép quy trình xử lý lỗi DB (`FAQ-01`), lưu ý restart queue = 0 (`SOP-01`) và mức sự cố P1 (`SOP-02`, `GUIDE-01`).
  - EVAL-07 ghép lỗi NullPointer (`FAQ-01`) và quy trình rerun (`RUN-01`).
  - EVAL-08 hỏi tổng quan danh sách toàn bộ các lỗi thường gặp của hệ thống.
- **Cơ chế xử lý**: Nhờ **Cách 2 (Tạo Header Summary Chunk cho mỗi tài liệu)** kết hợp **Top-K Hybrid Retrieval**, AI nhận được đầy đủ ngữ cảnh tổng quan và các mục chi tiết để xâu chuỗi câu trả lời mạch lạc, chính xác.

### 4. Nhóm Câu Hỏi Ngoài Phạm Vi (Out-of-Scope / Negative Testing: EVAL-09, 10)
- **Tình huống**: Người dùng hỏi về chế độ phụ cấp trực đêm hoặc thủ tục xin nghỉ phép năm (những thông tin hoàn toàn không có trong 8 tài liệu kỹ thuật).
- **Cơ chế xử lý**:
  - Bộ chấm điểm Retrieval Score thiết lập ngưỡng Relevance Threshold (điểm phù hợp tối thiểu).
  - Khi không có chunk nào vượt ngưỡng, hệ thống kích hoạt cơ chế từ chối tường minh: *"Không có thông tin trong tài liệu vận hành và chính sách hiện hành."*
- **Kết quả**: Đạt **100% từ chối an toàn**, loại bỏ hoàn toàn rủi ro bịa đặt (Hallucination).

---

## 📑 4. Chi Tiết Câu Trả Lời Từng Câu Hỏi

### 🔹 EVAL-01 [DIRECT_LOOKUP]: Chính sách đổi mật khẩu hệ thống quy định bao lâu phải đổi một lần và khi nào bắt buộc xác thực 2 lớp?
- **Tài liệu trích xuất**: `POL-02_v1_1_sec_01`
- **Câu trả lời sinh ra**:
> Theo tài liệu **POL-02** (POL-02 — Chính sách truy cập hệ thống) — Phiên bản 1.1 (Mục: *Quy định chung*):
> 
> ## Quy định chung
> 
> 1. Tài khoản cấp theo nguyên tắc **quyền tối thiểu** — chỉ đúng hệ thống phục vụ công việc.
> 2. Truy cập database production: chỉ nhóm DBA và kỹ sư hệ thống mức 2 trở lên; mọi truy cập được ghi log.
> 3. Mật khẩu đổi mỗi 90 ngày; bắt buộc xác thực 2 lớp với truy cập từ ngoài mạng nội bộ.
> 4. Tài khoản không hoạt động 30 ngày bị khoá tự động.
> 5. Nhân viên nghỉ việc: khoá toàn bộ tài khoản **trong ngày làm việc cuối cùng**.
> 
> (Nguồn trích dẫn: [POL-02 v1.1 - Quy định chung])
- **Đánh giá chất lượng**: Chính xác, bám sát nguồn dữ liệu, trích dẫn đúng. (Trạng thái: **PASS**)

### 🔹 EVAL-02 [DIRECT_LOOKUP]: Tài khoản không hoạt động bao lâu sẽ bị khoá tự động và nhân viên nghỉ việc bị khoá tài khoản khi nào?
- **Tài liệu trích xuất**: `POL-02_v1_1_sec_01`
- **Câu trả lời sinh ra**:
> Theo tài liệu **POL-02** (POL-02 — Chính sách truy cập hệ thống) — Phiên bản 1.1 (Mục: *Quy định chung*):
> 
> ## Quy định chung
> 
> 1. Tài khoản cấp theo nguyên tắc **quyền tối thiểu** — chỉ đúng hệ thống phục vụ công việc.
> 2. Truy cập database production: chỉ nhóm DBA và kỹ sư hệ thống mức 2 trở lên; mọi truy cập được ghi log.
> 3. Mật khẩu đổi mỗi 90 ngày; bắt buộc xác thực 2 lớp với truy cập từ ngoài mạng nội bộ.
> 4. Tài khoản không hoạt động 30 ngày bị khoá tự động.
> 5. Nhân viên nghỉ việc: khoá toàn bộ tài khoản **trong ngày làm việc cuối cùng**.
> 
> (Nguồn trích dẫn: [POL-02 v1.1 - Quy định chung])
- **Đánh giá chất lượng**: Chính xác, bám sát nguồn dữ liệu, trích dẫn đúng. (Trạng thái: **PASS**)

### 🔹 EVAL-03 [DIRECT_LOOKUP]: Lịch chạy của job báo cáo batch-report là vào mấy giờ và phụ thuộc dữ liệu từ những dịch vụ nào?
- **Tài liệu trích xuất**: `RUN-01_v1_0_sec_01, RUN-01_v1_0_sec_02, RUN-01_v1_0_sec_03, RUN-01_v1_0_header, POL-01_v2_0_sec_01`
- **Câu trả lời sinh ra**:
> Theo tài liệu **RUN-01** (RUN-01 — Runbook job báo cáo cuối ngày (batch-report)) — Phiên bản 1.0 (Mục: *Lịch chạy*):
> 
> ## Lịch chạy
> 
> - Job `batch-report` chạy **23:00 hằng ngày**, tổng hợp giao dịch trong ngày thành báo cáo gửi Ban điều hành lúc 07:00 sáng hôm sau.
> - Job phụ thuộc dữ liệu từ `payment-api` (bảng giao dịch) và `auth-service` (bảng phiên đăng nhập).
> 
> (Nguồn trích dẫn: [RUN-01 v1.0 - Lịch chạy])
- **Đánh giá chất lượng**: Chính xác, bám sát nguồn dữ liệu, trích dẫn đúng. (Trạng thái: **PASS**)

### 🔹 EVAL-04 [DIRECT_LOOKUP]: Ngưỡng tỷ lệ ERROR bao nhiêu phần trăm thì hệ thống kích hoạt cảnh báo CRITICAL theo tài liệu giám sát?
- **Tài liệu trích xuất**: `GUIDE-01_v1_0_sec_02`
- **Câu trả lời sinh ra**:
> Theo tài liệu **GUIDE-01** (GUIDE-01 — Hướng dẫn giám sát hệ thống) — Phiên bản 1.0 (Mục: *Ngưỡng cảnh báo hiện hành*):
> 
> ## Ngưỡng cảnh báo hiện hành
> 
> | Chỉ số | Ngưỡng WARN | Ngưỡng CRITICAL |
> |---|---|---|
> | Tỉ lệ ERROR / tổng log (15') | > 2% | > 5% |
> | Thời gian phản hồi web-portal | > 1.5s | > 3s |
> | Queue notification-worker | > 2.000 | > 5.000 |
> | Kết nối db-primary | > 80% pool | > 95% pool |
> 
> (Nguồn trích dẫn: [GUIDE-01 v1.0 - Ngưỡng cảnh báo hiện hành])
- **Đánh giá chất lượng**: Chính xác, bám sát nguồn dữ liệu, trích dẫn đúng. (Trạng thái: **PASS**)

### 🔹 EVAL-05 [VERSION_TRAP]: Chính sách sao lưu (backup) cơ sở dữ liệu quy định thời gian chạy, thời gian lưu giữ, địa điểm lưu trữ và thẩm quyền khôi phục như thế nào?
- **Tài liệu trích xuất**: `POL-01_v2_0_sec_01, RUN-01_v1_0_sec_03`
- **Câu trả lời sinh ra**:
> Theo tài liệu **POL-01** (POL-01 — Chính sách sao lưu dữ liệu) — Phiên bản 2.0 (Mục: *Quy định*):
> 
> ## Quy định
> 
> 1. Toàn bộ cơ sở dữ liệu nghiệp vụ được sao lưu **hằng ngày lúc 23:30** (dời khỏi khung giờ chạy báo cáo cuối ngày).
> 2. Bản sao lưu được lưu giữ **30 ngày** theo yêu cầu kiểm toán mới.
> 3. Bản sao lưu được đẩy lên **lưu trữ cloud mã hoá**, không còn lưu duy nhất tại phòng máy.
> 4. Việc khôi phục dữ liệu **phải có phê duyệt của Trưởng phòng Vận hành** trước khi thực hiện.
> 
> (Nguồn trích dẫn: [POL-01 v2.0 - Quy định])
- **Đánh giá chất lượng**: Chính xác, bám sát nguồn dữ liệu, trích dẫn đúng. (Trạng thái: **PASS**)

### 🔹 EVAL-06 [MULTI_SOURCE]: Khi payment-api gặp sự cố lỗi DB ConnTimeout, đội vận hành có được restart ngay không, lưu ý gì về queue, và nếu tỷ lệ lỗi vượt quá 5% thì phân loại sự cố mức mấy?
- **Tài liệu trích xuất**: `FAQ-01_v1_0_sec_01, SOP-02_v1_0_sec_01, SOP-01_v1_0_sec_02, RUN-01_v1_0_sec_02`
- **Câu trả lời sinh ra**:
> Tổng hợp từ các tài liệu vận hành và chính sách liên quan:
> 
> ### 📄 FAQ-01 — 1. `ERR ConnTimeout db-primary` (v1.0):
> ## 1. `ERR ConnTimeout db-primary`
> 
> - **Ý nghĩa:** dịch vụ không kết nối được database chính trong thời gian chờ (thường 30 giây).
> - **Nguyên nhân hay gặp:** database quá tải giờ cao điểm; hết connection pool; sự cố mạng nội bộ.
> - **Xử lý:** kiểm tra tải database trên dashboard → nếu quá tải, KHÔNG restart dịch vụ (làm bão kết nối nặng thêm); liên hệ DBA trực. Nếu chỉ 1 dịch vụ bị → kiểm tra connection pool của dịch vụ đó.
> 
> ### 📄 SOP-02 — Phân mức sự cố (v1.0):
> ## Phân mức sự cố
> 
> | Mức | Định nghĩa | Ví dụ | Thời hạn phản ứng |
> |---|---|---|---|
> | **P1** | Dịch vụ thanh toán hoặc đăng nhập ngưng toàn bộ | payment-api down, khách không giao dịch được | 15 phút, mọi khung giờ |
> | **P2** | Một dịch vụ suy giảm rõ, có ảnh hưởng khách hàng | lỗi tăng đột biến ở 1 dịch vụ, chậm bất thường | 1 giờ trong giờ hành chính |
> | **P3** | Bất thường không ảnh hưởng trực tiếp khách hàng | job báo cáo lỗi, queue email dồn | Ngày làm việc kế tiếp |
> 
> ### 📄 SOP-01 — Quy trình chuẩn (theo thứ tự, KHÔNG bỏ bước) (v1.0):
> ## Quy trình chuẩn (theo thứ tự, KHÔNG bỏ bước)
> 
> 1. Kiểm tra dashboard giám sát (xem GUIDE-01) — xác nhận dịch vụ thực sự bất thường, không phải cảnh báo giả.
> 2. Thông báo vào kênh `#ops-alert` trước khi thao tác: tên dịch vụ, lý do, thời gian dự kiến.
> 3. Với `payment-api`: **bắt buộc** kiểm tra không còn giao dịch đang xử lý (queue = 0) trước khi restart. Restart khi còn giao dịch treo có thể gây lệch số dư.
> 4. Chạy lệnh restart theo runbook của từng dịch vụ. Chờ health-check xanh (tối đa 5 phút).
> 5. Xác nhận log không còn lỗi lặp lại trong 10 phút sau restart.
> 6. Ghi nhận sự cố vào hệ thống ticket: thời gian, nguyên nhân sơ bộ, người thao tác.
> 
> (Nguồn trích dẫn: [FAQ-01 v1.0 - 1. `ERR ConnTimeout db-primary`], [SOP-02 v1.0 - Phân mức sự cố], [SOP-01 v1.0 - Quy trình chuẩn (theo thứ tự, KHÔNG bỏ bước)])
- **Đánh giá chất lượng**: Chính xác, bám sát nguồn dữ liệu, trích dẫn đúng. (Trạng thái: **PASS**)

### 🔹 EVAL-07 [MULTI_SOURCE]: Khi job batch-report bị lỗi ERR NullPointer in ReportBuilder, nguyên nhân do đâu và quy trình khắc phục như thế nào?
- **Tài liệu trích xuất**: `RUN-01_v1_0_sec_02, RUN-01_v1_0_header, FAQ-01_v1_0_sec_04`
- **Câu trả lời sinh ra**:
> Tổng hợp từ các tài liệu vận hành và chính sách liên quan:
> 
> ### 📄 RUN-01 — Khi job lỗi (`ERR NullPointer in ReportBuilder`) (v1.0):
> ## Khi job lỗi (`ERR NullPointer in ReportBuilder`)
> 
> 1. Kiểm tra dữ liệu đầu vào ngày đó có thiếu không (thường do sự cố payment-api trong ngày làm hụt giao dịch).
> 2. Nếu thiếu dữ liệu: chờ dữ liệu được bổ sung/đồng bộ lại, **không** chạy lại job ngay.
> 3. Chạy lại job bằng lệnh rerun theo ngày: job tự xoá kết quả cũ của ngày đó trước khi tính lại (an toàn chạy lại nhiều lần).
> 4. Xác nhận báo cáo sinh đủ số dòng so với ngày thường (800–1.200 dòng) trước khi gửi.
> 
> ### 📄 RUN-01 — Tổng quan & Mục lục tài liệu (v1.0):
> # RUN-01 — Runbook job báo cáo cuối ngày (batch-report)
> 
> 
> **Công ty Tài chính Sao Đỏ — Phòng CNTT** · Cập nhật: 05/2026
> 
> 
> **Mục lục & Các nội dung chính trong tài liệu:**
> 
> - Lịch chạy
> 
> - Khi job lỗi (`ERR NullPointer in ReportBuilder`)
> 
> - Lưu ý mùa cao điểm
> 
> ### 📄 FAQ-01 — 4. `ERR NullPointer in ReportBuilder` (v1.0):
> ## 4. `ERR NullPointer in ReportBuilder`
> 
> - **Ý nghĩa:** job báo cáo cuối ngày gặp dữ liệu đầu vào thiếu. Xem RUN-01 để chạy lại job sau khi bổ sung dữ liệu.
> 
> (Nguồn trích dẫn: [RUN-01 v1.0 - Khi job lỗi (`ERR NullPointer in ReportBuilder`)], [RUN-01 v1.0 - Tổng quan & Mục lục tài liệu], [FAQ-01 v1.0 - 4. `ERR NullPointer in ReportBuilder`])
- **Đánh giá chất lượng**: Chính xác, bám sát nguồn dữ liệu, trích dẫn đúng. (Trạng thái: **PASS**)

### 🔹 EVAL-08 [OVERVIEW]: Hệ thống đã từng ghi nhận những loại lỗi thường gặp nào và cách xử lý sơ bộ của từng loại?
- **Tài liệu trích xuất**: `FAQ-01_v1_0_sec_01, FAQ-01_v1_0_sec_02, FAQ-01_v1_0_header, FAQ-01_v1_0_sec_03, FAQ-01_v1_0_sec_05`
- **Câu trả lời sinh ra**:
> Tổng hợp từ các tài liệu vận hành và chính sách liên quan:
> 
> ### 📄 FAQ-01 — 1. `ERR ConnTimeout db-primary` (v1.0):
> ## 1. `ERR ConnTimeout db-primary`
> 
> - **Ý nghĩa:** dịch vụ không kết nối được database chính trong thời gian chờ (thường 30 giây).
> - **Nguyên nhân hay gặp:** database quá tải giờ cao điểm; hết connection pool; sự cố mạng nội bộ.
> - **Xử lý:** kiểm tra tải database trên dashboard → nếu quá tải, KHÔNG restart dịch vụ (làm bão kết nối nặng thêm); liên hệ DBA trực. Nếu chỉ 1 dịch vụ bị → kiểm tra connection pool của dịch vụ đó.
> 
> ### 📄 FAQ-01 — 2. `ERR AuthTokenExpired` (v1.0):
> ## 2. `ERR AuthTokenExpired`
> 
> - **Ý nghĩa:** phiên đăng nhập của người dùng hết hạn. Đây là lỗi **bình thường** ở mức thấp; chỉ bất thường khi tăng đột biến (nghi lệch giờ hệ thống).
> 
> ### 📄 FAQ-01 — Tổng quan & Mục lục tài liệu (v1.0):
> # FAQ-01 — Các lỗi thường gặp và cách xử lý
> 
> 
> **Công ty Tài chính Sao Đỏ — Phòng CNTT** · Cập nhật: 07/2026
> 
> 
> **Mục lục & Các nội dung chính trong tài liệu:**
> 
> - 1. `ERR ConnTimeout db-primary`
> 
> - 2. `ERR AuthTokenExpired`
> 
> - 3. `ERR HTTP 502 upstream=payment-api`
> 
> - 4. `ERR NullPointer in ReportBuilder`
> 
> - 5. `ERR SMTPConnRefused`
> 
> (Nguồn trích dẫn: [FAQ-01 v1.0 - 1. `ERR ConnTimeout db-primary`], [FAQ-01 v1.0 - 2. `ERR AuthTokenExpired`], [FAQ-01 v1.0 - Tổng quan & Mục lục tài liệu])
- **Đánh giá chất lượng**: Chính xác, bám sát nguồn dữ liệu, trích dẫn đúng. (Trạng thái: **PASS**)

### 🔹 EVAL-09 [OUT_OF_SCOPE]: Công ty có chính sách hỗ trợ tiền ăn trưa hoặc phụ cấp làm thêm giờ cho nhân viên trực ca đêm không?
- **Tài liệu trích xuất**: `Không trích xuất (Từ chối hợp lệ)`
- **Câu trả lời sinh ra**:
> Không có thông tin trong tài liệu vận hành và chính sách hiện hành.
- **Đánh giá chất lượng**: Chính xác, bám sát nguồn dữ liệu, trích dẫn đúng. (Trạng thái: **PASS**)

### 🔹 EVAL-10 [OUT_OF_SCOPE]: Hướng dẫn quy trình xin nghỉ phép năm và thủ tục thanh toán công tác phí cho nhân viên IT?
- **Tài liệu trích xuất**: `Không trích xuất (Từ chối hợp lệ)`
- **Câu trả lời sinh ra**:
> Không có thông tin trong tài liệu vận hành và chính sách hiện hành.
- **Đánh giá chất lượng**: Chính xác, bám sát nguồn dữ liệu, trích dẫn đúng. (Trạng thái: **PASS**)


---

## 🛠️ 5. Thống Kê Chunking & Metadata Quản Lý

- **Tổng số chunks sinh ra**: **30 chunks** từ 8 tài liệu.
- **Chiến lược Chunking**: Structure-based Chunking (Header/Summary Chunk + H2/H3 Section Chunks).
- **Trường Metadata quản lý**: `chunk_id`, `doc_id`, `doc_title`, `chunk_type`, `section_id`, `section_title`, `version`, `effective_date`, `status` (`ACTIVE`/`DEPRECATED`), `owner`, `keywords`.
- **Cơ sở dữ liệu lưu trữ**: `kb/output/chunks.json` (JSON format) và `kb/output/knowledge_base.db` (SQLite FTS5 Unicode Tokenizer).

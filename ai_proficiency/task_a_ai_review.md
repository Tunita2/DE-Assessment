# Review: Thiết kế pipeline AWS + Knowledge Base cho RAG

**Người review:** Bùi Lê Tuấn

**Vai trò:** Data Engineer (AI / Knowledge Engineering) — ứng viên chương trình
AWS x Xbrain Accelerator

**Ngày review:** 11/08/2026

**Đối tượng được review:** Câu trả lời do AI (đề bài cung cấp) sinh ra cho prompt bên dưới

**Phạm vi review:** Câu trả lời của AI cho prompt "Thiết kế pipeline trên AWS thu
log hằng ngày từ hệ thống của khách vào data lake, và tổ chức knowledge base cho RAG"

---

## 📜 Đoạn văn bản AI cần Review
> *"Bạn nên lưu toàn bộ log vào S3 Standard-IA vì đây là lựa chọn mặc định rẻ nhất cho data lake. Để thu dữ liệu, cấu hình một Glue job đọc trực tiếp từ database RDS production của khách mỗi 5 phút — đây là pattern chuẩn cho near-real-time. Dữ liệu nên chuyển sang Parquet, một format lưu theo hàng (row-based) nên ghi rất nhanh, phù hợp cho analytics. Với các bước transform nặng chạy khoảng 30–45 phút, dùng AWS Lambda là phù hợp nhất vì không phải quản lý server. Về knowledge base cho RAG, hãy chia tài liệu thành các chunk cố định 4.000 token — kích thước này luôn tốt nhất cho mọi loại tài liệu. Cuối cùng, không cần đánh version cho knowledge base, vì bản mới nhất luôn là bản đúng — cứ ghi đè là được."*

---

## Bối cảnh & Đánh giá tổng quan

Câu trả lời trên chứa 7 vấn đề, trải từ lỗi kiến thức nền tảng đơn thuần (Parquet)
đến rủi ro vận hành/bảo mật nghiêm trọng (truy cập trực tiếp RDS production của
khách hàng BFSI). Vấn đề nghiêm trọng nhất — và cũng là gốc rễ kéo theo nhiều lỗi
khác — là việc AI **tự mở rộng scope của đề bài** (từ "hằng ngày" thành "mỗi 5
phút") mà không hỏi lại hay nêu rõ giả định. Các điểm dưới đây được sắp xếp theo
mức độ nghiêm trọng, không theo thứ tự xuất hiện trong đoạn văn gốc.

---

## Chi tiết từng điểm sai

### Điểm 1 — Tự mở rộng scope ngoài prompt (mức độ: cao nhất, gốc rễ của các lỗi khác)

❌ "Cấu hình một Glue job đọc trực tiếp từ RDS production mỗi 5 phút — pattern
chuẩn cho near-real-time"

**Sai ở đâu:** Prompt chỉ yêu cầu thu log **hằng ngày** (daily batch), không hề
nhắc đến near-real-time hay tần suất bao nhiêu phút.

**Vì sao sai:** Đây là giả định tự thêm vào, không có căn cứ trong prompt. Khi
leo thang độ phức tạp không cần thiết, các lựa chọn kỹ thuật phía sau (Glue
polling liên tục, Lambda cho job nặng) đều bị kéo theo sai hướng — giải quyết
một bài toán không được hỏi.

**Sửa lại:** Với yêu cầu "hằng ngày", nên thiết kế batch pipeline đơn giản: log
được đẩy (push) định kỳ 1 lần/ngày vào S3 raw zone, xử lý bằng 1 Glue job chạy
theo lịch (schedule) 1 lần/ngày — không cần cơ chế polling liên tục.

🔎 Nguồn kiểm chứng: Tự suy luận dựa trên prompt, xác định scope của bài toán.

---

### Điểm 2 — Vấn đề bảo mật & tải khi query RDS production trực tiếp

❌ "cấu hình một Glue job đọc trực tiếp từ database RDS production của khách"

**Sai ở đâu:**
(a) Query liên tục từ Glue sẽ làm tăng tải I/O/CPU/connection lên RDS của khách,
cạnh tranh tài nguyên trực tiếp với các giao dịch thật của khách hàng đang chạy
trên cùng database.
(b) Về nghiệp vụ, không phải lúc nào RDS production cũng cho phép kết nối từ bên
ngoài — vi phạm ranh giới bảo mật, đặc biệt với khách hàng tài chính (BFSI).

**Sửa lại:** Khách tự đẩy log qua CloudWatch Logs về S3 để lấy log từ đây. Nếu
bắt buộc phải đọc từ DB, dùng Read Replica hoặc DMS/CDC để không tạo thêm tải
lên DB gốc.

🔎 Nguồn kiểm chứng:
- Thực hành thu thập logs RDS → CloudWatch → S3 ở Phase 1.
- AWS DMS User Guide — "Creating tasks for ongoing replication using AWS DMS"
  (docs.aws.amazon.com/dms/latest/userguide/CHAP_Task.CDC.html): xác nhận CDC
  hoạt động bằng cách đọc thay đổi từ transaction log/binlog của database
  engine, không phải query trực tiếp vào bảng — nên tải lên nguồn thấp hơn
  nhiều so với cách polling SQL lặp lại. Tài liệu cũng lưu ý CDC không phải
  real-time tuyệt đối, độ trễ phụ thuộc nhiều yếu tố và không có SLA cam kết.
- AWS re:Post — "Will DMS task have any impact on the source database?"
  (repost.aws/questions/QUO8sEedbZQpyFTFFxgHtKDQ): xác nhận DMS vẫn có tác động
  nhất định lên source (I/O, CPU, đặc biệt trong giai đoạn full-load ban đầu),
  nhưng thấp hơn đáng kể so với việc tự viết job query trực tiếp mỗi vài phút —
  có thể giảm thêm bằng cách giới hạn số task/bảng chạy song song.

---

### Điểm 3 — S3 Standard-IA làm nơi lưu log mới, gọi là "mặc định rẻ nhất" (mức độ: sai use-case)

❌ "Nên lưu toàn bộ log vào S3 Standard-IA vì đây là lựa chọn mặc định rẻ nhất
cho data lake"

**Sai ở đâu:** Standard-IA không phải "mặc định" đúng cho log mới ghi vào.

**Vì sao sai:** Standard-IA được thiết kế cho dữ liệu ít truy cập nhưng cần lấy
nhanh khi cần — có phí phụ trội khi đọc (retrieval fee) và ràng buộc lưu tối
thiểu 30 ngày. Log vận hành mới thường được truy vấn ngay (dashboard, alert,
phân tích gần thời gian thực) — dùng Standard-IA ngay từ đầu vừa tốn phí đọc
không cần thiết vừa đi ngược mục đích thiết kế của storage class này. "Rẻ nhất"
không đồng nghĩa "đúng nhất" — phải xét theo access pattern.

**Sửa lại:** Dùng S3 Standard cho log mới/gần đây, gắn Lifecycle policy để tự
động chuyển sang Standard-IA/Glacier sau khoảng thời gian không còn truy cập
thường xuyên (VD: 30-90 ngày).

🔎 Nguồn kiểm chứng: AWS S3 Documentation — mục "Amazon S3 storage classes".
https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html

---

### Điểm 4 — Định nghĩa sai Parquet là row-based (mức độ: lỗi kiến thức nền)

❌ "Parquet là format lưu theo hàng (row-based), ghi rất nhanh, phù hợp cho
analytics"

**Sai ở đâu:** Parquet là **columnar** (lưu theo cột), không phải row-based.

**Vì sao sai:** Đây là lỗi định nghĩa ngược hoàn toàn. Điểm mạnh của Parquet đến
từ việc lưu theo cột: khi truy vấn analytics chỉ cần đọc đúng cột liên quan
(không quét cả dòng), nén hiệu quả hơn vì dữ liệu cùng cột thường đồng kiểu.
Row-based (như CSV) mới là dạng ghi nhanh nhưng đọc chậm hơn cho truy vấn phân
tích theo cột.

**Sửa lại:** "Parquet là format lưu theo cột (columnar storage), giúp truy vấn
analytics nhanh hơn vì chỉ đọc đúng cột cần thiết, đồng thời nén dữ liệu hiệu
quả hơn."

🔎 Nguồn kiểm chứng:
https://docs.aws.amazon.com/glue/latest/dg/aws-glue-programming-etl-format-parquet-home.html

---

### Điểm 5 — Vượt ngoài khả năng của Lambda

❌ "Với các bước transform nặng chạy khoảng 30-45 phút, dùng AWS Lambda là phù
hợp nhất vì không phải quản lý server"

**Sai ở đâu:** AWS Lambda có giới hạn thời gian chạy tối đa **15 phút (900
giây)** — đây là hard limit không thể cấu hình vượt qua, không phải vấn đề
"phù hợp hay không".

**Vì sao sai:** Một job cần 30-45 phút về mặt kỹ thuật **không thể chạy** trên
Lambda — vượt quá 2-3 lần giới hạn cho phép.

**Sửa lại:** Dùng AWS Glue ETL job (đã được nhắc ở bước trước nhưng dùng sai
chỗ) cho các bước transform nặng, dài hơi — Glue được thiết kế đúng cho khối
lượng công việc ETL kéo dài, không giới hạn 15 phút như Lambda. Vẫn có thể dùng
Lambda cho các bước transform nhẹ, chạy dưới 15 phút.

🔎 Nguồn kiểm chứng: AWS Lambda Documentation — mục "Lambda quotas" (nêu rõ
maximum execution timeout = 900 seconds).
https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html

---

### Điểm 6 — Không có chunking nào "tốt nhất", chỉ có phù hợp hơn (mức độ: tuyệt đối hoá sai)

❌ "Chia tài liệu thành các chunk cố định 4.000 token — kích thước này luôn tốt
nhất cho mọi loại tài liệu"

**Sai ở đâu:** Không tồn tại 1 kích thước chunk đúng cho mọi loại tài liệu.

**Vì sao sai:** Kích thước chunk tối ưu phụ thuộc vào cấu trúc và mục đích của
tài liệu: tài liệu FAQ ngắn nên chunk theo từng câu hỏi-đáp; tài liệu có cấu
trúc mục/điều (như chính sách) nên chunk theo section; nếu ép tất cả về 4.000
token cố định, chunk sẽ dễ gộp nhiều chủ đề không liên quan (với tài liệu ngắn)
hoặc cắt đứt giữa chừng 1 ý (với tài liệu dài có cấu trúc chặt), làm giảm độ
chính xác retrieval.

**Sửa lại:** Chọn chiến lược chunk theo cấu trúc tài liệu (structure-based
chunking — theo heading/section) thay vì kích thước cố định tuyệt đối; kích
thước chỉ nên là giới hạn trên (upper bound), không phải mục tiêu cố định. Cách
chunk phù hợp còn tuỳ vào nguồn tài liệu và dạng câu hỏi người dùng thường hỏi.

🔎 Nguồn kiểm chứng: Pinecone Learning Center — bài "Chunking Strategies"; tài
liệu reading/ trong đề assessment (M5) về chunking cơ bản.

---

### Điểm 7 — "Không cần version, ghi đè là được" (mức độ: sai nghiêm trọng, phủ định bài toán đang giải)

❌ "Không cần đánh version cho knowledge base, vì bản mới nhất luôn là bản đúng
— cứ ghi đè là được"

**Sai ở đâu:** Giả định "bản mới luôn đúng" là sai, và việc ghi đè xoá mất khả
năng biết tài liệu nào đã cũ/deprecated.

**Vì sao sai:** Không có version, hệ thống mất 3 khả năng quan trọng: (a) biết
tài liệu nào đã lỗi thời để tránh trích dẫn nhầm quy định cũ; (b) audit/truy
vết "tại thời điểm X, chính sách nói gì" — quan trọng với khách hàng BFSI cần
tuân thủ kiểm toán; (c) rollback nếu bản cập nhật mới bị lỗi nhập liệu.

**Sửa lại:** Mỗi tài liệu cần gắn ít nhất các trường version, status; khi có
bản mới, giữ lại bản cũ với status DEPRECATED thay vì xoá/ghi đè, để hệ thống
retrieval có thể lọc đúng bản đang hiệu lực.

🔎 Nguồn kiểm chứng:
- Tự lập luận dựa trên chính case POL-01 v1/v2 trong bài assessment.
- Amazon Bedrock Knowledge Bases (sản phẩm managed KB của AWS — khác với hệ
  thống tự xây trong bài này, nhưng cho thấy nguyên tắc chung của ngành):
  - "Modify an Amazon Bedrock knowledge base" xác nhận thao tác
    `UpdateKnowledgeBase` sẽ ghi đè toàn bộ field nếu không chỉ định rõ field
    cần giữ nguyên — cho thấy "ghi đè không kiểm soát" là rủi ro được chính
    AWS cảnh báo, không phải lo ngại thừa.
  - "Resource policies for managed knowledge bases" mô tả cơ chế
    `policyRevisionId` (optimistic locking) giúp tránh 2 admin cùng ghi đè lên
    nhau mà không biết. Lưu ý: đây là version hoá cho **resource policy/quyền
    truy cập**, không phải version hoá **nội dung tài liệu** trong KB — nhưng
    cùng chung nguyên tắc rằng hệ thống production-grade cần cơ chế theo dõi
    thay đổi để tránh ghi đè ngoài ý muốn, đúng tinh thần ACTIVE/DEPRECATED
    mà hệ thống trong bài đang áp dụng cho nội dung tài liệu.

---

## Bài học rút ra

Lỗi nghiêm trọng nhất không nằm ở từng chi tiết kỹ thuật riêng lẻ, mà ở việc AI
đã **mở rộng scope của đề bài mà không hỏi lại hoặc nêu rõ giả định** (từ "hằng
ngày" thành "mỗi 5 phút", từ "hệ thống của khách" thành "database production").
Khi verify output của AI, bước đầu tiên nên là đối chiếu ngược lại: câu trả lời
có đúng đang giải bài toán được hỏi hay không — trước khi đi vào kiểm tra từng
chi tiết kỹ thuật. Đây là loại lỗi dễ bị bỏ sót nếu chỉ đọc lướt thấy "nghe có
vẻ đúng logic".

## Ghi chú thêm: về độ rõ ràng của prompt

Prompt gốc dùng cụm "hệ thống của khách" mà không làm rõ "khách" là tổ chức nội
bộ hay đối tác bên ngoài. Đây là điểm mơ hồ hợp lý có thể góp phần khiến AI tự
đưa ra giả định sai (truy cập trực tiếp RDS production). Bài học: khi prompt
còn mơ hồ ở chi tiết ảnh hưởng lớn đến thiết kế (như quyền truy cập hệ thống),
nên yêu cầu AI hỏi lại hoặc nêu rõ giả định trước khi thiết kế, thay vì để AI
tự chọn 1 hướng và trình bày như thể chắc chắn.
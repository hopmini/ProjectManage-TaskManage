# TÀI LIỆU KHỞI TẠO DỰ ÁN (PROJECT CHARTER)

## 1. THÔNG TIN CHUNG

- **Tên dự án**: Triển khai Hệ thống ERP FaceWorks AI 2026
- **Mã dự án**: FW-AI-2026
- **Tổng ngân sách dự kiến**: 2,500,000,000 VND
- **Mục tiêu**: Xây dựng nền tảng quản trị tổng thể doanh nghiệp tích hợp trí tuệ nhân tạo (AI), tự động hóa quy trình quản lý dự án, báo cáo và tương tác với người dùng thông qua trợ lý ảo.

## 2. DANH SÁCH HẠNG MỤC CÔNG VIỆC (TASKS)

1. **Khảo sát và Phân tích Nghiệp vụ (BA)**
   - Mô tả: Thu thập yêu cầu từ các phòng ban, chốt quy trình luồng dữ liệu chuẩn.
   - Thời lượng dự kiến: 80 giờ.

2. **Thiết kế Kiến trúc Hệ thống và UI/UX**
   - Mô tả: Xây dựng Wireframe, Mockup Kanban cao cấp và kiến trúc cơ sở dữ liệu.
   - Thời lượng dự kiến: 120 giờ.

3. **Phát triển Module Quản lý Dự án cốt lõi**
   - Mô tả: Lập trình các màn hình Kanban, Form View, Chart và Widget Chat.
   - Thời lượng dự kiến: 200 giờ.

4. **Tích hợp Trợ lý Ảo AI (Groq/Llama3)**
   - Mô tả: Kết nối bộ não AI, huấn luyện đọc file PDF, trích xuất dữ liệu thông minh.
   - Thời lượng dự kiến: 100 giờ.

5. **Kiểm thử Hệ thống (UAT & Security)**
   - Mô tả: Test hiệu năng, bảo mật và khả năng chịu tải của các API.
   - Thời lượng dự kiến: 80 giờ.

6. **Đào tạo Người dùng và Go-live**
   - Mô tả: Tổ chức các buổi Training cho End-user và chuyển giao công nghệ.
   - Thời lượng dự kiến: 60 giờ.

## 3. DANH SÁCH RỦI RO TIỀM ẨN (RISKS)

1. **Thay đổi phạm vi yêu cầu (Scope Creep)**
   - Mức độ: 3 (Nghiêm trọng)
   - Phương án xử lý: Ràng buộc chặt chẽ trong hợp đồng, mọi thay đổi phải qua Change Request và tính thêm chi phí.

2. **API của bên thứ 3 (AI) phản hồi chậm hoặc lỗi mạng**
   - Mức độ: 2 (Trung bình)
   - Phương án xử lý: Triển khai cơ chế Retry, Timeout và Cache dữ liệu để đảm bảo trải nghiệm người dùng không bị gián đoạn.

3. **Thiếu hụt kỹ sư Senior AI trong giai đoạn tích hợp**
   - Mức độ: 2 (Trung bình)
   - Phương án xử lý: Liên hệ các đối tác outsouce dự phòng hoặc đẩy nhanh tiến độ đào tạo nội bộ.

4. **Nút thắt cổ chai về Performance khi dữ liệu lớn (Datalake)**
   - Mức độ: 3 (Nghiêm trọng)
   - Phương án xử lý: Tối ưu hóa truy vấn SQL ngay từ đầu, thiết lập index chuẩn và cân nhắc dùng Elasticsearch.

5. **Người dùng cuối phản kháng với hệ thống mới**
   - Mức độ: 2 (Trung bình)
   - Phương án xử lý: Giao diện (UI) thiết kế thân thiện, bắt mắt. Có các video hướng dẫn trực quan dạng Tiktok/Short ngắn gọn.

---
*Tài liệu này được tạo tự động để phục vụ việc kiểm thử tính năng Extract JSON qua AI của hệ thống FaceWorks ERP.*

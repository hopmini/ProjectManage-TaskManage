![Ubuntu](https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)
![GitLab](https://img.shields.io/badge/gitlab-%23181717.svg?style=for-the-badge&logo=gitlab&logoColor=white)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

HỆ THỐNG QUẢN TRỊ DỰ ÁN CHIẾN LƯỢC (DNU-PROJECT ENTERPRISE)

#📝 Giới thiệu dự án

Hệ thống được xây dựng để quản trị dự án. Dựa trên nền tảng Odoo, hệ thống cung cấp các công cụ điều hành chuyên sâu, tích hợp đa module giữa Nhân sự (HRM) và Thư viện công việc.

Các chức năng cốt lõi:

Dashboard tổng quan: Theo dõi thời gian thực các chỉ số tiến độ, ngân sách và trạng thái dự án.

Quản lý Cột mốc (Milestones): Theo dõi các giai đoạn sống còn của dự án.

Quản trị Rủi ro (Risk Management): Phân tích mức độ ảnh hưởng và lập phương án dự phòng rủi ro.

Điều phối Công việc: "Bốc" đầu việc từ thư viện mẫu và gán trực tiếp cho nhân sự thực hiện.

Theo dõi KPI tự động: Hệ thống tự động tính toán % hoàn thành và cảnh báo trễ hạn.

Báo cáo BI đa chiều: Phân tích dữ liệu qua các góc nhìn Pivot, Graph, Kanban và Calendar.

#🚀 Hướng dẫn cài đặt và khởi tạo môi trường

##1. Cài đặt công cụ và thư viện hệ thống

Người sử dụng thực thi lệnh sau trên Ubuntu để cài đặt các thư viện cần thiết:

```sudo apt-get update
sudo apt-get install libxml2-dev libxslt-dev libldap2-dev libsasl2-dev libssl-dev \
python3.10-distutils python3.10-dev build-essential libffi-dev zlib1g-dev \
python3.10-venv libpq-dev```


##2. Tải mã nguồn dự án

Thực hiện clone mã nguồn từ GitHub:

git clone [https://github.com/hopmini/ProjectManage-TaskManage.git](https://github.com/hopmini/ProjectManage-TaskManage.git)
`cd ProjectManage-TaskManage`


##3. Khởi tạo môi trường ảo (Virtual Environment)

```python3.10 -m venv ./venv
source venv/bin/activate
pip3 install -r requirements.txt```


##4. Thiết lập Cơ sở dữ liệu (Docker)

Khởi tạo PostgreSQL server bằng Docker Compose:

`docker-compose up -d`


#⚙️ Cấu hình vận hành

##1. Khởi tạo tệp odoo.conf

Tạo tệp cấu hình để hệ thống nhận diện các phân hệ:

```[options]
addons_path = addons, odoo/addons
db_host = localhost
db_password = odoo
db_user = odoo
db_port = 5432
xmlrpc_port = 8069```


##2. Lệnh khởi chạy và cập nhật

Sử dụng lệnh sau để nâng cấp module và chạy hệ thống:

python3 odoo-bin.py -c odoo.conf -u all 


#🛠 Kiến trúc hệ thống

Hệ thống tuân thủ kiến trúc Enterprise 4 tầng:

Lớp hiển thị (XML/JS): Kanban, Form điều hành trung tâm.

Lớp nghiệp vụ (Python/ORM): Xử lý logic tự động hóa tiến độ và ngân sách.

Lớp tích hợp (Cross-module): Kết nối module quan_ly_nhan_su và quan_ly_cong_viec.

Lớp dữ liệu (PostgreSQL): Lưu trữ và bảo mật dữ liệu cấp doanh nghiệp.

#🔗 Thông tin mã nguồn

GitHub Repository: ProjectManage-TaskManage

Tác giả: hopmini

Giấy phép: LGPL-3

Dự án thực hiện trong khuôn khổ Học phần Thực tập CNTT7 - FIT - Đại học Đại Nam.
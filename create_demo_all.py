# -*- coding: utf-8 -*-
# --- Master Demo Data Script for Odoo Project Management ---
# Run via: python3 odoo-bin.py shell -c odoo.conf -d odoo < create_demo_all.py

import random
from datetime import date, timedelta

# 1. PERSONNEL (15 Records)
emp_names = [
    "Lê Hoàng Anh", "Trần Minh Đức", "Nguyễn Thu Thủy", "Phạm Hải Đăng", "Vũ Kim Ngân",
    "Đặng Quốc Bảo", "Bùi Hồng Liên", "Lý Thanh Tùng", "Hoàng Thùy Dương", "Đỗ Văn Hùng",
    "Ngô Mỹ Linh", "Phan Anh Tuấn", "Trịnh Xuân Vinh", "Lương Gia Bảo", "Mai Tuyết Nhung"
]
job_titles = ["Project Manager", "Architect", "Lead Developer", "QA Manager", "Business Analyst", "Security Expert", "DevOps Engineer"]

employees = []
for i, name in enumerate(emp_names):
    emp = self.env['quan_ly.nhan_vien'].search([('name', '=', name)], limit=1)
    if not emp:
        emp = self.env['quan_ly.nhan_vien'].create({
            'name': name,
            'ma_nv': f"NV{100 + i}"
        })
    employees.append(emp)

# 2. PROJECTS (15 Records)
project_templates = [
    ("Hệ thống Giao thông Thông minh i-Traffic", "khach_hang", 5000000000),
    ("Trung tâm Dữ liệu Edge Computing DNU", "noi_bo", 8500000000),
    ("Nền tảng Blockchain Truy xuất Nguồn gốc", "nghien_cuu", 3200000000),
    ("Hệ thống ERP VinGroup Phase 2", "khach_hang", 12000000000),
    ("Ứng dụng AI Nhận diện Khuôn mặt BV", "bao_tri", 1500000000),
    ("Hạ tầng 5G Campus Thông minh", "noi_bo", 4200000000),
    ("Cổng Dịch vụ công Trực tuyến Tỉnh X", "khach_hang", 2800000000),
    ("Phần mềm Quản lý Bệnh viện Med-Core", "khach_hang", 6700000000),
    ("Nghiên cứu Vật liệu Nano linh kiện", "nghien_cuu", 1800000000),
    ("Số hóa Hồ sơ Lưu trữ Quốc gia", "khach_hang", 9500000000),
    ("Hệ thống Learning Management (LMS)", "noi_bo", 2100000000),
    ("Tự động hóa Kho vận Logistics", "khach_hang", 5400000000),
    ("Bảo trì Hệ thống Core Banking", "bao_tri", 3800000000),
    ("Phân tích Big Data Thị trường BĐS", "nghien_cuu", 2500000000),
    ("Ứng dụng Fintech Ví điện tử mới", "khach_hang", 11000000000)
]

for i, (name, ptype, budget) in enumerate(project_templates):
    p = self.env['quan_ly.du_an'].search([('ten_du_an', '=', name)], limit=1)
    if not p:
        p = self.env['quan_ly.du_an'].create({
            'ten_du_an': name,
            'loai_du_an': ptype,
            'ngan_sach_du_kien': budget,
            'truong_du_an_id': employees[i % len(employees)].id,
            'ngay_bat_dau': date.today() - timedelta(days=random.randint(30, 90)),
            'ngay_ket_thuc': date.today() + timedelta(days=random.randint(180, 500)),
            'trang_thai': random.choice(['nhap', 'trien_khai', 'tam_dung', 'tre_han']),
            'do_uu_tien': random.choice(['1', '2', '3'])
        })
        print(f"Created project: {name}")
    else:
        # Just update the basic info and trigger children creation if needed
        p.write({
            'loai_du_an': ptype,
            'ngan_sach_du_kien': budget,
            'truong_du_an_id': employees[i % len(employees)].id,
        })
        print(f"Updating existing project: {name}")

    # Clear children to rebuild cleanly
    print(f"Refreshing child records for {name}...")
    p.milestone_ids.unlink()
    p.dong_cong_viec_ids.unlink()
    p.risk_ids.unlink()
    self.env['quan_ly.du_an.issue'].search([('du_an_id', '=', p.id)]).unlink()
    self.env['quan_ly.du_an.quality'].search([('du_an_id', '=', p.id)]).unlink()
    self.env['quan_ly.du_an.resource'].search([('du_an_id', '=', p.id)]).unlink()
    self.env['quan_ly.du_an.stakeholder'].search([('du_an_id', '=', p.id)]).unlink()
    # Milestones (3 per project)
    for m in range(3):
        self.env['quan_ly.du_an.milestone'].create({
            'du_an_id': p.id,
            'ten_cot_moc': f"Cột mốc Giai đoạn {m+1}: {name}",
            'ngay_du_kien': date.today() + timedelta(days=(m+1)*60),
            'da_dat_duoc': random.choice([True, False]),
            'ngan_sach': budget * 0.2
        })
        
    # Tasks (5 per project)
    task_pool = ["Khởi động", "Khảo sát", "Thiết kế", "Lập trình", "Kiểm thử", "Triển khai", "Đào tạo", "Bàn giao"]
    for t in range(5):
        t_name = random.choice(task_pool) + f" - {name}"
        task_rec = self.env['quan_ly.cong_viec'].search([('ten_cong_viec', '=', t_name)], limit=1)
        if not task_rec: task_rec = self.env['quan_ly.cong_viec'].create({'ten_cong_viec': t_name})
        self.env['quan_ly.du_an.line'].create({
            'du_an_id': p.id,
            'cong_viec_id': task_rec.id,
            'nhan_vien_id': random.choice(employees).id,
            'ngay_deadline': date.today() + timedelta(days=random.randint(10, 100)),
            'trang_thai_viec': random.choice(['todo', 'doing', 'done']),
            'so_gio_du_kien': random.randint(20, 80),
            'so_gio_thuc_te': random.randint(5, 30),
            'tien_do_cong_viec': random.randint(0, 100)
        })

    # Issues (2 per project)
    issue_pool = ["Lỗi API", "Chậm tiến độ nhân sự", "Thiếu thiết bị", "Yêu cầu thay đổi", "Lỗi UI", "Database overload"]
    for iss in range(2):
        self.env['quan_ly.du_an.issue'].create({
            'du_an_id': p.id,
            'name': random.choice(issue_pool) + f" - {name}",
            'priority': random.choice(['0', '1', '2']),
            'severity': random.choice(['low', 'medium', 'high']),
            'status': random.choice(['new', 'in_progress', 'resolved']),
            'assignee_id': random.choice(employees).id
        })

    # Risks (2 per project)
    risk_pool = ["Biến động tỉ giá", "Nhân sự nghỉ việc", "Thay đổi pháp lý", "Mất mát dữ liệu", "Thiếu hụt vốn"]
    for rk in range(2):
        self.env['quan_ly.du_an.risk'].create({
            'du_an_id': p.id,
            'ten_rui_ro': random.choice(risk_pool),
            'muc_do': random.choice(['1', '2', '3']),
            'trang_thai': random.choice(['dang_theo_doi', 'da_xay_ra', 'da_xu_ly'])
        })

    # Quality (2 per project)
    quality_pool = ["Kiểm tra Bảo mật", "Đánh giá Performance", "Kiểm tra Tính năng", "Audit Mã nguồn"]
    for qt in range(2):
        self.env['quan_ly.du_an.quality'].create({
            'du_an_id': p.id,
            'name': random.choice(quality_pool),
            'is_passed': random.choice([True, False]),
            'quality_score': random.randint(40, 100),
            'inspector_id': random.choice(employees).id
        })

    # Resources (2 per project)
    res_pool = ["Server Dell PowerEdge", "AWS Cloud Credit", "Macbook Pro M2", "License JetBrains", "Thuê ngoài Dev"]
    for res in range(2):
        self.env['quan_ly.du_an.resource'].create({
            'du_an_id': p.id,
            'name': random.choice(res_pool),
            'type': random.choice(['hardware', 'software', 'human']),
            'quantity': random.randint(1, 10),
            'unit_price': random.randint(100, 5000) * 10000
        })

    # Stakeholders (2 per project)
    org_pool = ["Bộ Công thương", "VinGroup", "FPT Software", "Đại học DNU", "Ngân hàng Techcombak"]
    for sh in range(2):
        self.env['quan_ly.du_an.stakeholder'].create({
            'du_an_id': p.id,
            'name': f"Ông/Bà {random.choice(emp_names)}",
            'organization': random.choice(org_pool),
            'role': "Giám đốc / Đại diện",
            'influence_score': random.randint(50, 100)
        })
        
    # Trigger AI Analysis to populate the first tab
    p.action_ai_analyze()

self.env.cr.commit()
print("Success: Generated full 15-project demo ecosystem with child records.")

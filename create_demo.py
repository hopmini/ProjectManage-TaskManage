# --- Script tạo dữ liệu mẫu Odoo (Chạy qua Odoo Shell) ---
# Cách chạy: python3 odoo-bin.py shell -c odoo.conf -d odoo < create_demo.py

projects_data = [
    {
        'ten_du_an': 'Hệ thống Thành phố Thông minh DNU (SmartCity 2026)',
        'loai_du_an': 'khach_hang',
        'trang_thai': 'trien_khai',
        'ngan_sach_du_kien': 5000000000.0,
        'tien_do_tong_the': 45.0,
        'do_uu_tien': '3',
        'mo_ta_du_an': '<p>Tích hợp IoT và AI điều phối giao thông toàn khu vực.</p>'
    },
    {
        'ten_du_an': 'Tối ưu Hạ tầng Trình diễn AI (AI Ops Infrastructure)',
        'loai_du_an': 'noi_bo',
        'trang_thai': 'nhap',
        'ngan_sach_du_kien': 1200000000.0,
        'tien_do_tong_the': 10.0,
        'do_uu_tien': '2',
        'mo_ta_du_an': '<p>Nâng cấp Server GPU hỗ trợ chatbot và xử lý dữ liệu lớn.</p>'
    },
    {
        'ten_du_an': 'Bảo trì Hệ thống Quản trị Doanh nghiệp (ERP Upgrade)',
        'loai_du_an': 'bao_tri',
        'trang_thai': 'hoan_thanh',
        'ngan_sach_du_kien': 450000000.0,
        'tien_do_tong_the': 100.0,
        'do_uu_tien': '1',
        'mo_ta_du_an': '<p>Nâng cấp Odoo 15 lên bản Enterprise ổn định.</p>'
    },
    {
        'ten_du_an': 'Nghiên cứu Ứng dụng Blockchain trong Logistics',
        'loai_du_an': 'nghien_cuu',
        'trang_thai': 'tam_dung',
        'ngan_sach_du_kien': 2800000000.0,
        'tien_do_tong_the': 30.5,
        'do_uu_tien': '1',
        'mo_ta_du_an': '<p>Theo dõi luồng hàng hóa minh bạch bằng Ledger công nghệ cao.</p>'
    },
    {
        'ten_du_an': 'Tự động hóa Quy trình Báo cáo Tài chính',
        'loai_du_an': 'khach_hang',
        'trang_thai': 'trien_khai',
        'ngan_sach_du_kien': 850000000.0,
        'tien_do_tong_the': 68.0,
        'do_uu_tien': '2',
        'mo_ta_du_an': '<p>Robot hóa (RPA) việc lấy dữ liệu từ ngân hàng và kế toán.</p>'
    }
]

# Tạo dữ liệu
admin_user = self.env.ref('base.user_admin', raise_if_not_found=False) or self.env['res.users'].search([('login', '=', 'admin')], limit=1)
manager = self.env['quan_ly.nhan_vien'].search([], limit=1)

for p_vals in projects_data:
    # Check if exists
    exists = self.env['quan_ly.du_an'].search([('ten_du_an', '=', p_vals['ten_du_an'])], limit=1)
    if not exists:
        vals = p_vals.copy()
        if manager: vals['truong_du_an_id'] = manager.id
        self.env['quan_ly.du_an'].create(vals)
        print(f"Created project: {p_vals['ten_du_an']}")

self.env.cr.commit()
print("Successfully generated elite portfolio data.")

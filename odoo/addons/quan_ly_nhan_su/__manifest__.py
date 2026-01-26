# -*- coding: utf-8 -*-
{
    'name': "Quản Lý Nhân Sự",
    'summary': "Quản lý nhân viên, chấm công và tính lương",
    'description': """
        Module quản lý nhân sự bao gồm:
        - Quản lý hồ sơ nhân viên, đơn vị.
        - Chấm công: Giờ vào/ra, đi muộn, về sớm, tăng ca.
        - Tính lương: Tự động tính dựa trên công và thưởng/phạt.
    """,
    'author': "Your Name",
    'category': 'Human Resources',
    'version': '1.0',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/don_vi.xml',
        'views/nhan_vien.xml',
        'views/cham_cong.xml',
        'views/tinh_luong.xml',
        'views/menu.xml',
        'wizard/import_excel.xml',
        'reports/phieu_luong.xml',
    ],
    'installable': True,
    'application': True,
}
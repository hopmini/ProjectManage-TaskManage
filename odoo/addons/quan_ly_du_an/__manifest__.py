# -*- coding: utf-8 -*-
{
    'name': "Quản lý Dự án (Professor Edition)",
    'version': '1.0.0',
    'category': 'Project Management',
    'summary': "Quản lý dự án 1000 tỷ",
    'author': "Giáo sư IT - FIT DNU",
    'depends': ['base', 'quan_ly_nhan_su', 'quan_ly_cong_viec', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/du_an_view.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
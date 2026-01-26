# -*- coding: utf-8 -*-
{
    'name': "Quản lý Công việc (BTL)",
    'version': '1.5.1',
    'depends': ['base', 'quan_ly_nhan_su'],
    'data': [
        'security/ir.model.access.csv',
        'views/cong_viec_view.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
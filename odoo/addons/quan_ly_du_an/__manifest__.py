# -*- coding: utf-8 -*-
{
    'name': "Quản lý Dự án",
    'version': '1.0.0',
    'category': 'Project',
    'summary': "Hệ thống Quản lý Dự án & Tự động hóa",
    'author': "DNU IT",
    'depends': ['base', 'quan_ly_nhan_su', 'quan_ly_cong_viec', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/du_an_view.xml',
        'views/reports.xml',
        'views/cron_job.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'quan_ly_du_an/static/src/css/du_an_style.css',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
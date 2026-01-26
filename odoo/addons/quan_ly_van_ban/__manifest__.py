# -*- coding: utf-8 -*-
{
    'name': "Quản lý Văn bản",

    'summary': """
        Hệ thống quản lý văn bản đến, văn bản đi và phân loại văn bản
    """,

    'description': """
        Module quản lý văn bản dành cho các cơ quan công tác. Cung cấp các tính năng:
        - Quản lý văn bản đến (nhận, xử lý, ký duyệt)
        - Quản lý văn bản đi (soạn thảo, phát hành, theo dõi)
        - Phân loại và quản lý loại văn bản
        - Gắn kèm tệp tin cho mỗi văn bản
    """,

    'author': "FIT-DNU",
    'website': "https://ttdn1501.aiotlabdnu.xyz/web",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/van_ban_den.xml',
        'views/van_ban_di.xml',
        'views/loai_van_ban.xml',
        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

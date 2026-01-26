# -*- coding: utf-8 -*-
from odoo import models, fields

class DonVi(models.Model):
    _name = 'quan_ly.don_vi'
    _description = 'Đơn vị / Phòng ban'

    name = fields.Char(string='Tên đơn vị', required=True)
    ma_don_vi = fields.Char(string='Mã đơn vị')
    mo_ta = fields.Text(string='Mô tả')
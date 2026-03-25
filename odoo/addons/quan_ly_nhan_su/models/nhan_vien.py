# -*- coding: utf-8 -*-
from odoo import models, fields

class NhanVien(models.Model):
    _name = 'quan_ly.nhan_vien'
    _description = 'Hồ sơ nhân viên'

    name = fields.Char(string='Họ và tên', required=True)
    ma_nv = fields.Char(string='Mã nhân viên', required=True)
    don_vi_id = fields.Many2one('quan_ly.don_vi', string='Phòng ban')
    
    # ===> THÊM DÒNG NÀY ĐỂ SỬA LỖI <===
    user_id = fields.Many2one('res.users', string='Tài khoản hệ thống') 
    hinh_anh = fields.Binary(string='Hình ảnh')
    # ==================================

    luong_co_ban = fields.Float(string='Lương cơ bản', default=5000000)
    ngay_cong_chuan = fields.Integer(string='Công chuẩn/tháng', default=26)
    phu_cap_mac_dinh = fields.Float(string='Phụ cấp cố định', default=0)
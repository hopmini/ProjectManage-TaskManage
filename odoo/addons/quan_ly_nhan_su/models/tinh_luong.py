# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime # <--- Thư viện để lấy năm hiện tại
import calendar 

class TinhLuong(models.Model):
    _name = 'quan_ly.tinh_luong'
    _description = 'Phiếu tính lương'

    # 1. FIELD NAME (Quan trọng: Phải có để không bị lỗi view XML)
    name = fields.Char(string='Mã phiếu', default='PL/New', readonly=True)

    nhan_vien_id = fields.Many2one('quan_ly.nhan_vien', string='Nhân viên', required=True)
    
    thang = fields.Selection([
        ('1', 'Tháng 1'), ('2', 'Tháng 2'), ('3', 'Tháng 3'),
        ('4', 'Tháng 4'), ('5', 'Tháng 5'), ('6', 'Tháng 6'),
        ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'),
        ('10', 'Tháng 10'), ('11', 'Tháng 11'), ('12', 'Tháng 12')
    ], string='Tháng', required=True)
    
    # 2. DEFAULT NĂM: Tự động lấy năm hiện tại (2026)
    nam = fields.Integer(string='Năm', default=lambda self: datetime.now().year, required=True)

    # --- CÁC TRƯỜNG HIỂN THỊ CHI TIẾT ---
    luong_co_ban = fields.Float(string='Lương cơ bản', related='nhan_vien_id.luong_co_ban', store=True)
    ngay_cong_chuan = fields.Integer(string='Công chuẩn', related='nhan_vien_id.ngay_cong_chuan', store=True)
    
    luong_mot_ngay = fields.Float(string='Lương 1 ngày', compute='_compute_luong', store=True)
    so_cong_thuc_te = fields.Integer(string='Số công đi làm', compute='_compute_luong', store=True)
    
    tong_thuong = fields.Float(string='Tổng thưởng', compute='_compute_luong', store=True)
    tong_phat = fields.Float(string='Tổng phạt', compute='_compute_luong', store=True)
    phu_cap = fields.Float(string='Phụ cấp', default=0)
    
    # 3. DANH SÁCH CHI TIẾT (Dùng Many2many + compute để hiển thị)
    chi_tiet_cong_ids = fields.Many2many('quan_ly.cham_cong', 
                                         string='Chi tiết ngày công', 
                                         compute='_compute_luong')

    thuc_linh = fields.Float(string='THỰC LĨNH', compute='_compute_luong', store=True)

    @api.depends('nhan_vien_id', 'thang', 'nam', 'phu_cap')
    def _compute_luong(self):
        for r in self:
            if not r.nhan_vien_id or not r.thang:
                r.thuc_linh = 0
                r.chi_tiet_cong_ids = False
                continue
            
            # Tính lương 1 ngày
            cong_chuan = r.ngay_cong_chuan if r.ngay_cong_chuan > 0 else 26
            r.luong_mot_ngay = r.luong_co_ban / cong_chuan
            
            # Xác định ngày đầu/cuối tháng
            year = r.nam
            month = int(r.thang)
            last_day = calendar.monthrange(year, month)[1]
            start_date = f'{year}-{month:02d}-01'
            end_date = f'{year}-{month:02d}-{last_day}'

            # Tìm chấm công
            cham_cong_recs = self.env['quan_ly.cham_cong'].search([
                ('nhan_vien_id', '=', r.nhan_vien_id.id),
                ('ngay_cham', '>=', start_date),
                ('ngay_cham', '<=', end_date)
            ])
            
            # Gán dữ liệu vào bảng chi tiết
            r.chi_tiet_cong_ids = cham_cong_recs

            # Tính toán tổng hợp
            r.so_cong_thuc_te = len(cham_cong_recs)
            r.tong_thuong = sum(rec.tien_thuong for rec in cham_cong_recs)
            r.tong_phat = sum(rec.tien_phat for rec in cham_cong_recs)
            
            # ===> CÔNG THỨC TÍNH LƯƠNG <===
            luong_theo_cong = r.luong_mot_ngay * r.so_cong_thuc_te
            r.thuc_linh = luong_theo_cong + r.tong_thuong + r.phu_cap - r.tong_phat

    @api.model
    def create(self, vals):
        # Tự sinh tên phiếu: PL/Tháng-Năm
        if vals.get('name', 'PL/New') == 'PL/New':
            vals['name'] = 'PL/' + str(vals.get('thang')) + '-' + str(vals.get('nam'))
        return super(TinhLuong, self).create(vals)
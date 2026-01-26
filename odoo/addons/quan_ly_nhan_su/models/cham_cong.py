# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ChamCong(models.Model):
    _name = 'quan_ly.cham_cong'
    _description = 'Quản lý chấm công'

    name = fields.Char(string='Mã', default='New', readonly=True)
    nhan_vien_id = fields.Many2one('quan_ly.nhan_vien', string='Nhân viên', required=True)
    ngay_cham = fields.Date(string='Ngày chấm', default=fields.Date.today, required=True)
    
    # Giờ nhập theo số thập phân (Ví dụ: 8h30 = 8.5)
    gio_vao = fields.Float(string='Giờ vào', default=8.0)
    gio_ra = fields.Float(string='Giờ ra', default=17.0)
    
    # Các trường tính toán
    tong_gio_lam = fields.Float(string='Tổng giờ làm', compute='_compute_cong', store=True)
    tien_phat = fields.Float(string='Tiền phạt (Đi muộn/Về sớm)', compute='_compute_cong', store=True)
    tien_thuong = fields.Float(string='Tiền thưởng (Tăng ca)', compute='_compute_cong', store=True)
    trang_thai = fields.Selection([
        ('du_cong', 'Đủ công'),
        ('di_muon', 'Đi muộn/Về sớm'),
        ('tang_ca', 'Có tăng ca')
    ], string='Trạng thái', compute='_compute_cong', store=True)

    @api.depends('gio_vao', 'gio_ra')
    def _compute_cong(self):
        for r in self:
            # 1. Tính tổng giờ làm
            if r.gio_ra > r.gio_vao:
                gio_lam = r.gio_ra - r.gio_vao
                # Trừ 1 tiếng nghỉ trưa nếu làm quá 5 tiếng
                r.tong_gio_lam = gio_lam - 1 if gio_lam > 5 else gio_lam
            else:
                r.tong_gio_lam = 0

            # 2. Logic Phạt/Thưởng
            phat = 0
            thuong = 0
            status = 'du_cong'

            # Quy định: Vào sau 8h15 (8.25) là muộn, Ra trước 17h (17.0) là sớm
            if r.gio_vao > 8.25: 
                phat += 50000  # Phạt 50k đi muộn
                status = 'di_muon'
            
            if r.gio_ra < 17.0:
                phat += 50000  # Phạt 50k về sớm
                status = 'di_muon'

            # Quy định: Làm trên 9 tiếng tính là tăng ca
            if r.tong_gio_lam > 9:
                so_gio_tang = r.tong_gio_lam - 8 # Giả sử chuẩn 8 tiếng
                thuong = so_gio_tang * 100000    # Thưởng 100k/giờ
                status = 'tang_ca'

            r.tien_phat = phat
            r.tien_thuong = thuong
            r.trang_thai = status

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('quan_ly.cham_cong') or 'New'
        return super(ChamCong, self).create(vals)
    
    # ĐÃ XÓA DÒNG tinh_luong_id VÌ KHÔNG CẦN THIẾT NỮA
# -*- coding: utf-8 -*-
# *******************************************************************************
# * Học phần: Thực tập CNTT7 - Khoa CNTT - DNU                                 *
# * Đề tài: Kiến trúc ERP điều hành dự án 1000 tỷ (DNU-Golden Project)          *
# * File: Business Logic Layer (Python Models)                                  *
# *******************************************************************************

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, datetime

class QuanLyDuAn(models.Model):
    _name = 'quan_ly.du_an'
    _description = 'Hệ thống Quản lý Dự án Enterprise'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ten_du_an'
    _order = 'do_uu_tien desc, ngay_bat_dau desc'

    # --- KHỐI 1: THÔNG TIN ĐỊNH DANH ---
    ten_du_an = fields.Char(string='Tên dự án chủ trì', required=True, tracking=True)
    ma_du_an = fields.Char(string='Mã dự án', required=True, copy=False, readonly=True, default=lambda self: _('NEW'))
    loai_du_an = fields.Selection([
        ('noi_bo', 'Dự án nội bộ (DNU-HQ)'),
        ('khach_hang', 'Triển khai cho đối tác'),
        ('nghien_cuu', 'Nghiên cứu & Phát triển'),
        ('bao_tri', 'Bảo trì hạ tầng')
    ], string='Phân loại hình', default='khach_hang', tracking=True)
    color = fields.Integer(string='Mã màu thẻ', default=0)
    active = fields.Boolean(string='Còn hoạt động', default=True)

    # --- KHỐI 2: NHÂN SỰ ---
    truong_du_an_id = fields.Many2one('quan_ly.nhan_vien', string='Trưởng dự án (PM)', required=True, tracking=True)
    thanh_vien_ids = fields.Many2many('quan_ly.nhan_vien', 'du_an_nhan_vien_rel', 'du_an_id', 'nhan_vien_id', string='Đội ngũ chuyên gia')
    so_luong_thanh_vien = fields.Integer(string='Tổng số nhân sự', compute='_compute_member_count', store=True)

    # --- KHỐI 3: VÒNG ĐỜI & TRẠNG THÁI ---
    ngay_bat_dau = fields.Date(string='Ngày khởi công', default=fields.Date.today, required=True, tracking=True)
    ngay_ket_thuc = fields.Date(string='Hạn bàn giao', required=True, tracking=True)
    ngay_nghiem_thu = fields.Date(string='Ngày hoàn thành thực tế', readonly=True)
    trang_thai = fields.Selection([
        ('nhap', 'Bản thảo'),
        ('trien_khai', 'Đang thực hiện'),
        ('tam_dung', 'Tạm dừng'),
        ('tre_han', 'Cảnh báo trễ hạn'),
        ('hoan_thanh', 'Đã hoàn thành'),
        ('huy', 'Đã hủy bỏ')
    ], string='Trạng thái vận hành', default='nhap', compute='_compute_trang_thai_logic', store=True, tracking=True)
    do_uu_tien = fields.Selection([('0', 'Thấp'), ('1', 'Bình thường'), ('2', 'Ưu tiên cao'), ('3', 'Rất khẩn cấp')], string='Mức độ ưu tiên', default='1', index=True)

    # --- KHỐI 4: TÀI CHÍNH & KPI ---
    ngan_sach_du_kien = fields.Float(string='Ngân sách phê duyệt', default=0.0)
    chi_phi_thuc_te = fields.Float(string='Vốn đã giải ngân', default=0.0)
    ty_le_ngan_sach = fields.Float(string='% Ngân sách đã dùng', compute='_compute_financial_stats')
    tien_do_tong_the = fields.Float(string='Tiến độ (%)', compute='_compute_progress_stats', store=True)
    tong_so_viec = fields.Integer(string='Tổng số việc', compute='_compute_progress_stats', store=True)
    so_viec_hoan_thanh = fields.Integer(string='Số đầu việc xong', compute='_compute_progress_stats', store=True)

    # --- KHỐI 5: QUAN HỆ ---
    dong_cong_viec_ids = fields.One2many('quan_ly.du_an.line', 'du_an_id', string='Bảng phân công')
    milestone_ids = fields.One2many('quan_ly.du_an.milestone', 'du_an_id', string='Cột mốc chiến lược')
    risk_ids = fields.One2many('quan_ly.du_an.risk', 'du_an_id', string='Danh mục rủi ro')
    mo_ta_du_an = fields.Html(string='Thuyết minh dự án')
    ghi_chu_quan_tri = fields.Text(string='Chỉ thị nội bộ')
    danh_gia_sau_du_an = fields.Selection([('xuat_sac', 'Xuất sắc'), ('tot', 'Tốt'), ('dat', 'Trung bình'), ('kem', 'Kém')], string='Kết quả nghiệm thu', readonly=True)

    @api.depends('thanh_vien_ids')
    def _compute_member_count(self):
        for r in self: r.so_luong_thanh_vien = len(r.thanh_vien_ids)

    @api.depends('ngan_sach_du_kien', 'chi_phi_thuc_te')
    def _compute_financial_stats(self):
        for r in self: r.ty_le_ngan_sach = (r.chi_phi_thuc_te / r.ngan_sach_du_kien * 100) if r.ngan_sach_du_kien > 0 else 0

    @api.depends('dong_cong_viec_ids.trang_thai_viec')
    def _compute_progress_stats(self):
        for r in self:
            lines = r.dong_cong_viec_ids
            r.tong_so_viec = len(lines)
            done = len(lines.filtered(lambda x: x.trang_thai_viec == 'done'))
            r.so_viec_hoan_thanh = done
            r.tien_do_tong_the = (done / r.tong_so_viec * 100) if r.tong_so_viec > 0 else 0

    @api.depends('tien_do_tong_the', 'ngay_ket_thuc')
    def _compute_trang_thai_logic(self):
        today = date.today()
        for r in self:
            if r.trang_thai == 'huy': continue
            if r.tien_do_tong_the == 100:
                r.trang_thai = 'hoan_thanh'
                if not r.ngay_nghiem_thu: r.ngay_nghiem_thu = today
            elif r.ngay_ket_thuc and r.ngay_ket_thuc < today and r.tien_do_tong_the < 100:
                r.trang_thai = 'tre_han'
            elif r.tien_do_tong_the > 0: r.trang_thai = 'trien_khai'
            else: r.trang_thai = 'nhap'

    def action_start_project(self):
        for r in self:
            if not r.dong_cong_viec_ids: raise ValidationError(_("Chưa có danh sách công việc!"))
            r.write({'trang_thai': 'trien_khai'})

    def action_finish_project(self):
        for r in self:
            if r.tien_do_tong_the < 100: raise ValidationError(_("Chưa hoàn thành 100% công việc!"))
            r.write({'trang_thai': 'hoan_thanh', 'ngay_nghiem_thu': date.today(), 'danh_gia_sau_du_an': 'tot'})

    def action_reset_to_draft(self):
        self.write({'trang_thai': 'nhap', 'ngay_nghiem_thu': False, 'danh_gia_sau_du_an': False})

    def action_cancel_project(self):
        self.write({'trang_thai': 'huy'})

    def action_view_tasks(self):
        return {
            'name': _('Công việc Dự án'),
            'type': 'ir.actions.act_window',
            'res_model': 'quan_ly.du_an.line',
            'view_mode': 'tree,form',
            'domain': [('du_an_id', '=', self.id)],
            'target': 'current',
        }

    @api.model
    def create(self, vals):
        if vals.get('ma_du_an', _('NEW')) == _('NEW'):
            vals['ma_du_an'] = 'DA-' + datetime.now().strftime('%Y%m%d-%H%M')
        return super(QuanLyDuAn, self).create(vals)

class QuanLyDuAnLine(models.Model):
    _name = 'quan_ly.du_an.line'
    _description = 'Chi tiết phân công dự án'
    du_an_id = fields.Many2one('quan_ly.du_an', ondelete='cascade', required=True)
    cong_viec_id = fields.Many2one('quan_ly.cong_viec', string='Đầu việc mẫu', required=True)
    nhan_vien_id = fields.Many2one('quan_ly.nhan_vien', string='Chuyên gia thực hiện', required=True)
    ngay_deadline = fields.Date(string='Hạn hoàn thành', required=True)
    trang_thai_viec = fields.Selection([('todo', 'Chờ làm'), ('doing', 'Đang làm'), ('done', 'Hoàn tất')], string='Tình trạng', default='todo')
    ghi_chu_rieng = fields.Char(string='Chỉ thị')
    is_late = fields.Boolean(string='Trễ', compute='_compute_is_late')

    @api.depends('ngay_deadline', 'trang_thai_viec')
    def _compute_is_late(self):
        today = date.today()
        for line in self: line.is_late = bool(line.ngay_deadline and line.ngay_deadline < today and line.trang_thai_viec != 'done')

    @api.onchange('cong_viec_id')
    def _onchange_task(self):
        if self.cong_viec_id and self.cong_viec_id.nguoi_thuc_hien_id: self.nhan_vien_id = self.cong_viec_id.nguoi_thuc_hien_id

class QuanLyDuAnMilestone(models.Model):
    _name = 'quan_ly.du_an.milestone'
    _description = 'Cột mốc dự án'
    du_an_id = fields.Many2one('quan_ly.du_an', ondelete='cascade')
    ten_cot_moc = fields.Char(string='Tên mốc chiến lược', required=True)
    ngay_du_kien = fields.Date(string='Ngày dự kiến đạt', required=True)
    da_dat_duoc = fields.Boolean(string='Đã hoàn thành', default=False)
    ghi_chu = fields.Text(string='Mô tả mốc')

class QuanLyDuAnRisk(models.Model):
    _name = 'quan_ly.du_an.risk'
    _description = 'Quản trị rủi ro'
    du_an_id = fields.Many2one('quan_ly.du_an', ondelete='cascade')
    ten_rui_ro = fields.Char(string='Tên rủi ro tiềm ẩn', required=True)
    muc_do = fields.Selection([('1', 'Thấp'), ('2', 'Trung bình'), ('3', 'Nghiêm trọng')], string='Mức độ', default='1')
    phuong_an_xu_ly = fields.Text(string='Phương án dự phòng')
    trang_thai = fields.Selection([('dang_theo_doi', 'Đang theo dõi'), ('da_xay_ra', 'Đã xảy ra'), ('da_xu_ly', 'Đã khắc phục')], string='Tình trạng rủi ro', default='dang_theo_doi')
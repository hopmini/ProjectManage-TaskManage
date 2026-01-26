# -*- coding: utf-8 -*-
# *******************************************************************************
# * Học phần: Thực tập CNTT7 - FIT - DNU                                       *
# * Đề tài: Module Quản lý Công việc (Phiên bản mã tự động ngẫu nhiên)          *
# * Giải pháp: Sử dụng Python Logic để tạo mã, không phụ thuộc file XML Data    *
# *******************************************************************************

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import random
import string
from datetime import datetime

class QuanLyCongViec(models.Model):
    """
    Model quản lý danh mục công việc.
    Mã định danh sẽ được hệ thống tự tính toán ngẫu nhiên khi khởi tạo.
    """
    _name = 'quan_ly.cong_viec'
    _description = 'Hệ thống Quản lý Danh mục Công việc (Auto-Random ID)'
    _rec_name = 'ten_cong_viec'
    _order = 'do_uu_tien desc, id'

    # --- HÀM TỰ TẠO MÃ NGẪU NHIÊN (KHÔNG CẦN FILE NGOÀI) ---
    def _get_default_code(self):
        """Tạo mã có định dạng CV + 4 ký tự ngẫu nhiên (Ví dụ: CV9G2X)"""
        size = 4
        chars = string.ascii_uppercase + string.digits
        random_str = ''.join(random.choice(chars) for _ in range(size))
        return "CV" + random_str

    # --- THÔNG TIN ĐỊNH DANH ---
    ten_cong_viec = fields.Char(
        string='Tên đầu việc cụ thể', 
        required=True, 
        help="Nhập tên công việc thật (Ví dụ: Lập trình giao diện Login)"
    )
    
    ma_cong_viec = fields.Char(
        string='Mã định danh công việc', 
        required=True,
        readonly=True, # Khóa lại không cho sửa để đảm bảo tính duy nhất
        default=_get_default_code,
        help="Mã số này được hệ thống tự động tạo ngẫu nhiên."
    )

    mo_ta_chi_tiet = fields.Html(
        string='Yêu cầu & Hướng dẫn thực hiện',
        help="Ghi chú chi tiết cách thức thực hiện công việc này cho nhân viên."
    )

    # --- TÍCH HỢP NHÂN SỰ (DỮ LIỆU TỪ MODULE HRM) ---
    nguoi_thuc_hien_id = fields.Many2one(
        'quan_ly.nhan_vien', 
        string='Nhân sự phụ trách mặc định',
        help="Nhân viên này được bốc trực tiếp từ danh sách của module Nhân sự."
    )

    # --- QUẢN LÝ TRẠNG THÁI & PHÂN LOẠI ---
    trang_thai = fields.Selection([
        ('moi', 'Mới tiếp nhận'),
        ('dang_lam', 'Đang triển khai'),
        ('hoan_thanh', 'Đã hoàn tất'),
        ('huy', 'Đã hủy bỏ')
    ], string='Trạng thái hiện tại', default='moi')

    do_uu_tien = fields.Selection([
        ('0', 'Thấp'),
        ('1', 'Bình thường'),
        ('2', 'Cao'),
        ('3', 'Rất khẩn cấp')
    ], string='Mức độ ưu tiên', default='1')

    do_kho = fields.Selection([
        ('de', 'Dễ (1đ)'),
        ('tb', 'Trung bình (3đ)'),
        ('kho', 'Khó (5đ)'),
        ('v_kho', 'Rất khó (10đ)')
    ], string='Độ phức tạp', default='tb')

    # --- THEO DÕI THỜI GIAN ---
    ngay_tao = fields.Datetime(
        string='Thời điểm tạo', 
        default=fields.Datetime.now, 
        readonly=True
    )
    
    ngay_bat_dau = fields.Date(string='Ngày bắt đầu dự kiến', default=fields.Date.today)
    
    han_hoan_thanh = fields.Date(string='Hạn cuối (Deadline)')
    
    so_gio_du_kien = fields.Float(
        string='Thời gian thực hiện (Giờ)', 
        default=8.0,
        help="Ước tính tổng số giờ làm việc cần thiết."
    )

    # --- CÁC HÀM XỬ LÝ LOGIC & KIỂM TRA ---

    @api.constrains('ma_cong_viec')
    def _check_unique_code(self):
        """Đảm bảo mã ngẫu nhiên không bị trùng (dù xác suất rất thấp)"""
        for record in self:
            duplicate = self.search([
                ('ma_cong_viec', '=', record.ma_cong_viec),
                ('id', '!=', record.id)
            ])
            if duplicate:
                # Nếu trùng thì tự đổi mã khác luôn
                record.ma_cong_viec = self._get_default_code()

    @api.constrains('ngay_bat_dau', 'han_hoan_thanh')
    def _check_date_validity(self):
        """Kiểm tra logic ngày tháng của BTL"""
        for record in self:
            if record.ngay_bat_dau and record.han_hoan_thanh:
                if record.ngay_bat_dau > record.han_hoan_thanh:
                    raise ValidationError(_("Lỗi: Ngày bắt đầu không được lớn hơn ngày hoàn thành!"))

    def action_set_doing(self):
        """Nút bấm UI chuyển trạng thái sang Đang làm"""
        for record in self:
            record.trang_thai = 'dang_lam'

    def action_set_done(self):
        """Nút bấm UI chuyển trạng thái sang Hoàn thành"""
        for record in self:
            if not record.nguoi_thuc_hien_id:
                raise ValidationError(_("Yêu cầu gán nhân sự trước khi xác nhận hoàn thành!"))
            record.trang_thai = 'hoan_thanh'

    # --- KẾT THÚC CLASS QUANLYCONGVIEC ---
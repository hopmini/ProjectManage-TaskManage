from odoo import models, fields, api
from datetime import date

from odoo.exceptions import ValidationError

class VanBanDen(models.Model):
    _name = "van_ban_den"
    _description = 'Bảng chứa thông tin văn bản đến'
    _rec_name = 'ten_van_ban'

    so_van_ban_den = fields.Char("Số hiệu văn bản", required=True)
    ten_van_ban = fields.Char("Tên văn bản", required=True)
    loai_van_ban_id = fields.Many2one('loai_van_ban', string="Loại văn bản")
    handler_employee_id = fields.Many2one("hr.employee", string="Cán bộ xử lý")
    signer_employee_id = fields.Many2one("hr.employee", string="Người ký")
    noi_gui_den = fields.Char("Nơi gửi đến")
    ngay_nhan = fields.Date("Ngày nhận")
    state = fields.Selection([
        ("draft", "Mới"),
        ("confirmed", "Đã xác nhận"),
        ("done", "Hoàn tất"),
    ], string="Trạng thái", default="draft")
    file = fields.Binary("File đính kèm")
    file_name = fields.Char("Tên file")


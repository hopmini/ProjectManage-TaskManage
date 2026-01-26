from odoo import models, fields, api
from datetime import date

from odoo.exceptions import ValidationError

class VanBanDi(models.Model):
    _name = 'van_ban_di'
    _description = 'Bảng chứa thông tin văn bản đi'
    _rec_name = 'ten_van_ban'

    so_van_ban_di = fields.Char("Số hiệu văn bản", required=True)
    ten_van_ban = fields.Char("Tên văn bản", required=True)
    loai_van_ban_id = fields.Many2one('loai_van_ban', string="Loại văn bản")
    noi_nhan = fields.Char("Nơi nhận")
    ngay_phat_hanh = fields.Date("Ngày phát hành")
    state = fields.Selection([
        ("draft", "Mới"),
        ("confirmed", "Đã xác nhận"),
        ("done", "Hoàn tất"),
    ], string="Trạng thái", default="draft")
    file = fields.Binary("File đính kèm")
    file_name = fields.Char("Tên file")


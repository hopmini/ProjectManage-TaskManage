# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DuAnTaiLieu(models.Model):
    _name = 'quan_ly.du_an.document'
    _description = 'Tài liệu / Wiki dự án'

    du_an_id = fields.Many2one('quan_ly.du_an', string='Dự án', ondelete='cascade')
    name = fields.Char(string='Tên tài liệu', required=True)
    link = fields.Char(string='Đường dẫn / URL')
    category = fields.Selection([
        ('technical', 'Kỹ thuật'),
        ('legal', 'Pháp lý'),
        ('meeting', 'Biên bản họp'),
        ('other', 'Khác')
    ], string='Phân loại', default='technical')
    version = fields.Char(string='Phiên bản', default='1.0')
    description = fields.Text(string='Tóm tắt nội dung')
    
    approval_status = fields.Selection([
        ('draft', 'Bản nháp'),
        ('review', 'Chờ duyệt'),
        ('approved', 'Đã phê duyệt')
    ], string='Trạng thái Duyệt', default='draft')
    importance_level = fields.Selection([('normal', 'Bình thường'), ('high', 'Quan trọng')], string='Mức độ', default='normal')
    
    document_status_html = fields.Html(compute="_compute_status_html")

    @api.depends('name', 'approval_status', 'importance_level', 'version', 'category')
    def _compute_status_html(self):
        for r in self:
            if r.approval_status == 'approved':
                stamp_color = "#ca8a04"
                stamp_bg = "#fef08a"
                stamp_text = "PASSED"
                icon = "fa-check-circle"
            elif r.approval_status == 'review':
                stamp_color = "#eab308"
                stamp_bg = "#fef9c3"
                stamp_text = "REVIEW"
                icon = "fa-eye"
            else:
                stamp_color = "#a16207"
                stamp_bg = "#fffdf5"
                stamp_text = "DRAFT"
                icon = "fa-pencil"

            imp_badge = f'<span style="background: #ef4444; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; margin-left: 10px;">QUAN TRỌNG</span>' if r.importance_level == 'high' else ''
                
            html = f"""
            <div style="font-family: 'Outfit', sans-serif; background: #fffdf5; padding: 0; border-radius: 12px; border: 1px solid #fde047; color: #422006; display: flex; overflow: hidden; box-shadow: 0 4px 10px rgba(202, 138, 4, 0.05);">
                <!-- Document Icon Side -->
                <div style="background: #fef08a; width: 100px; display: flex; flex-direction: column; align-items: center; justify-content: center; border-right: 1px dashed #facc15;">
                    <i class="fa fa-file-pdf-o" style="font-size: 36px; color: #ca8a04; margin-bottom: 8px;"></i>
                    <div style="font-size: 12px; font-weight: 800; color: #a16207;">v{r.version or '1.0'}</div>
                </div>
                
                <!-- Main Info -->
                <div style="padding: 20px; flex-grow: 1; position: relative;">
                    <div style="font-size: 11px; font-weight: 700; color: #a16207; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">HỒ SƠ TÀI LIỆU DỰ ÁN {imp_badge}</div>
                    <h3 style="margin: 0 0 5px 0; font-size: 20px; font-weight: 800; color: #713f12;">{r.name or 'Chưa rõ tên'}</h3>
                    <div style="font-size: 13px; color: #854d0e;"><i class="fa fa-folder-open-o"></i> Phân loại: {dict(self._fields['category'].selection).get(r.category, 'Khác') if r.category else 'Khác'}</div>
                    
                    <!-- Watermark Stamp -->
                    <div style="position: absolute; right: 20px; top: 15px; border: 4px solid {stamp_color}; border-radius: 8px; padding: 5px 15px; transform: rotate(15deg); background: {stamp_bg}; opacity: 0.9; box-shadow: 0 0 10px rgba(0,0,0,0.05);">
                        <div style="font-size: 20px; font-weight: 900; color: {stamp_color}; letter-spacing: 2px;">
                            <i class="fa {icon}"></i> {stamp_text}
                        </div>
                    </div>
                </div>
            </div>
            """
            r.document_status_html = html
